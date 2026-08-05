from logger.debug import trace

import docker
import io
import tarfile
import threading
import requests

from ui.services.config import Config


class ChallengeLoader:
    def __init__(self, config: Config = None):
        self.docker = docker.from_env()
        self.config = config or Config()
        # challenge_id (lowercased) -> raw checker script text
        self.check_scripts = {}

    def load_challenge(self, challenge_info):
        """Pull challenge image, start the challenge container. No volume:
        the container's own writable layer is the workspace, and the
        checker later execs directly into this same container, so nothing
        else needs to share storage with it."""

        image_name = challenge_info["image"]
        print(f"Pulling {image_name}...")
        self._pull_with_timeout(image_name)

        # Cache the checker script now so verify() has it ready later.
        self._fetch_check_script(challenge_info)

        container_name = f"clice-{challenge_info['id']}"
        try:
            existing = self.docker.containers.get(container_name)
            existing.remove(force=True)
            print(f"Removed existing container: {container_name}")
        except docker.errors.NotFound:
            pass

        container = self.docker.containers.run(
            challenge_info["image"],
            command=["tail", "-f", "/dev/null"],
            detach=True,
            stdin_open=True,
            tty=True,
            name=container_name,
            mem_limit=self.config.challenge_mem_limit,
            nano_cpus=self.config.challenge_nano_cpus,
            network_disabled=not self.config.network_enabled,
        )

        # Verify container is running
        import time
        time.sleep(1)
        container.reload()
        if container.status != 'running':
            raise RuntimeError(f"Container {container.id} failed to start: {container.status}")

        return container

    def _pull_with_timeout(self, image_name):
        """Pull an image with a hard timeout. docker-py's images.pull() has
        no per-call timeout of its own, so a stalled/unreachable registry
        (bad DNS, dead TLS handshake, etc.) can otherwise hang far longer
        than any reasonable app-level wait - the error the loading-screen
        timeout is meant to prevent."""
        result = {"error": None}

        def do_pull():
            try:
                self.docker.images.pull(image_name)
            except Exception as e:
                result["error"] = e

        thread = threading.Thread(target=do_pull, daemon=True)
        thread.start()
        thread.join(timeout=self.config.docker_timeout)

        if thread.is_alive():
            trace("pull_timeout", image=image_name, timeout=self.config.docker_timeout)
            raise TimeoutError(
                f"Pulling {image_name} took longer than {self.config.docker_timeout}s "
                f"(registry unreachable or very slow) - check your connection or the "
                f"CLICE_DOCKER_TIMEOUT setting."
            )

        if result["error"] is not None:
            raise result["error"]

    def _fetch_check_script(self, challenge_info):
        """Download this challenge's checker script (cached, any language -
        the shebang line decides what runs it, not us)."""
        challenge_id = challenge_info["id"].lower()
        check_url = challenge_info["check_url"]

        if challenge_id in self.check_scripts:
            print(f"Checker script already cached for {challenge_id}")
            return

        print(f"Downloading check script for {challenge_id}...")
        response = requests.get(check_url, timeout=15)
        response.raise_for_status()
        self.check_scripts[challenge_id] = response.text
        print(f"Checker script cached for {challenge_id}")

    def verify(self, challenge_id, user_container):
        """Run the checker script directly inside the live challenge
        container. The script is written in with its shebang intact and
        made executable, so any interpreter the author's image provides
        (bash, python3, node, whatever) works - we never assume one.

        Returns a dict, not a bare bool, so callers can see *why*:
            {
                "passed": bool,
                "exit_code": int | None,   # None if it never completed (timeout/staging error)
                "output": str,             # combined stdout+stderr from the checker
                "error": str | None,       # set on staging/timeout/exec-level failures
            }
        """

        challenge_id = challenge_id.lower()
        script = self.check_scripts.get(challenge_id)

        if not script:
            msg = f"No checker script cached for {challenge_id}"
            print(f"Verification error: {msg}")
            return {"passed": False, "exit_code": None, "output": "", "error": msg}

        if not user_container:
            msg = "No running challenge container to verify against"
            print(f"Verification error: {msg}")
            return {"passed": False, "exit_code": None, "output": "", "error": msg}

        remote_path = "/tmp/.clice_check"

        try:
            self._write_script(user_container, script, remote_path)
        except Exception as e:
            trace("verify_write_script_failed", error=repr(e), error_type=type(e).__name__)
            msg = f"Couldn't stage checker: {e}"
            print(f"Verification error: {msg}")
            return {"passed": False, "exit_code": None, "output": "", "error": msg}

        result = {"exit_code": None, "output": "", "error": None}

        def run_exec():
            try:
                trace("verify_exec_begin", challenge_id=challenge_id)
                exit_code, output = user_container.exec_run([remote_path], demux=True)
                stdout, stderr = output if isinstance(output, tuple) else (output, None)
                combined = b"".join(x for x in (stdout, stderr) if x)
                result["exit_code"] = exit_code
                result["output"] = combined.decode(errors="replace").strip()
            except Exception as e:
                result["error"] = str(e)

        thread = threading.Thread(target=run_exec, daemon=True)
        thread.start()
        thread.join(timeout=self.config.checker_timeout)

        # Best-effort tidy up regardless of outcome (not a security measure -
        # the container already had full user access all session; this is
        # just not leaving clutter behind).
        try:
            user_container.exec_run(["rm", "-f", remote_path])
        except Exception:
            pass

        if thread.is_alive():
            msg = f"Checker timed out after {self.config.checker_timeout}s"
            print(msg)
            trace("verify_exec_timeout", challenge_id=challenge_id, timeout=self.config.checker_timeout)
            return {"passed": False, "exit_code": None, "output": result["output"], "error": msg}

        if result["error"] is not None:
            trace("verify_exec_exception", error=result["error"])
            print(f"Verification error: {result['error']}")
            return {"passed": False, "exit_code": None, "output": result["output"], "error": result["error"]}

        trace("verify_exec_output", output=result["output"], exit_code=result["exit_code"])
        print("Checker output:" if result["output"] else "NO Logs", result["output"])

        # Exit codes 126/127 are POSIX shell conventions meaning the process
        # never actually ran - "command not found" (127, e.g. the checker's
        # interpreter doesn't exist on this image) or "found but not
        # executable" (126). Both mean the checker produced no real verdict
        # on the user's work at all, so this is an environment error, not a
        # legitimate fail - distinct from "the checker ran and said no".
        if result["exit_code"] in (126, 127):
            msg = f"Checker process could not start (exit {result['exit_code']}): {result['output']}"
            trace("verify_exec_infra_failure", exit_code=result["exit_code"], output=result["output"])
            return {"passed": False, "exit_code": result["exit_code"], "output": result["output"], "error": msg}

        return {
            "passed": result["exit_code"] == 0,
            "exit_code": result["exit_code"],
            "output": result["output"],
            "error": None,
        }

    def _write_script(self, container, script_text, remote_path):
        """Write the checker script into the container as an executable
        file at remote_path, without shelling out or touching the host
        filesystem."""
        data = script_text.encode()
        tarbuf = io.BytesIO()
        with tarfile.TarFile(fileobj=tarbuf, mode="w") as tar:
            info = tarfile.TarInfo(name=remote_path.lstrip("/").split("/")[-1])
            info.size = len(data)
            info.mode = 0o755  # executable
            tar.addfile(info, io.BytesIO(data))
        tarbuf.seek(0)

        target_dir = "/" + "/".join(remote_path.lstrip("/").split("/")[:-1])
        container.put_archive(target_dir or "/", tarbuf)

    def cleanup(self, container):
        """Stop and remove the challenge container, if auto-cleanup is on."""
        if not self.config.auto_cleanup:
            return
        try:
            container.stop()
            container.remove()
        except Exception:
            pass