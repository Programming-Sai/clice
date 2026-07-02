from logger.debug import trace

import docker
import tempfile
import requests
from pathlib import Path

class ChallengeLoader:
    def __init__(self):
        self.docker = docker.from_env()
        self.checker_images = {}
        self.volume_name = None
    
    def load_challenge(self, challenge_info):
        """Pull challenge image, build checker image, return container"""
        
        # 1. Pull challenge image
        image_name = challenge_info["image"]
        print(f"Pulling {image_name}...")
        self.docker.images.pull(image_name)
        
        # 2. Build checker image
        self._build_checker_image(challenge_info)
        
        # 3. Create shared volume
        volume_name = f"clice-workspace-{challenge_info['id']}"
        try:
            # Remove old volume if exists
            old_volume = self.docker.volumes.get(volume_name)
            old_volume.remove()
        except:
            pass
        self.docker.volumes.create(name=volume_name)
        self.volume_name = volume_name
        
        container_name = f"clice-{challenge_info['id']}"
        try:
            existing = self.docker.containers.get(container_name)
            existing.remove(force=True)
            print(f"Removed existing container: {container_name}")
        except docker.errors.NotFound:
            pass
        
        # 4. Start user container
        container = self.docker.containers.run(
            challenge_info["image"],
            command=["tail", "-f", "/dev/null"],
            detach=True,
            stdin_open=True,
            tty=True,
            volumes={volume_name: {"bind": "/workspace", "mode": "rw"}},
            name=container_name
        )
        
        # Verify container is running
        import time
        time.sleep(1)
        container.reload()
        if container.status != 'running':
            raise RuntimeError(f"Container {container.id} failed to start: {container.status}")
        
        return container
    
    def _build_checker_image(self, challenge_info):
        """Build isolated checker image for this challenge (cached)"""
        challenge_id = challenge_info["id"].lower()
        check_url = challenge_info["check_url"]
        image_tag = f"clice-checker-{challenge_id}:latest"
        
        # Check if already built
        try:
            self.docker.images.get(image_tag)
            self.checker_images[challenge_id] = image_tag
            print(f"Checker image already cached for {challenge_id}")
            return
        except docker.errors.ImageNotFound:
            pass
        
        # Download check.py
        print(f"Downloading check script for {challenge_id}...")
        response = requests.get(check_url, timeout=15)
        response.raise_for_status()
        check_script = response.text
        
        # Build checker image
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "check.py"
            script_path.write_text(check_script)
            
            dockerfile = """
FROM python:3.10-slim
COPY check.py /check.py
WORKDIR /
ENTRYPOINT ["python", "/check.py"]
"""
            (Path(tmpdir) / "Dockerfile").write_text(dockerfile)
            
            print(f"Building checker image for {challenge_id}...")
            self.docker.images.build(
                path=tmpdir,
                tag=image_tag,
                rm=True
            )
            self.checker_images[challenge_id] = image_tag
            print(f"Checker image built: {image_tag}")
    
    def verify(self, challenge_id, user_container):
        """Run verification using pre-built checker image"""
        image_tag = self.checker_images.get(challenge_id)
        

        container = None
        try:
            if not image_tag:
                raise ValueError(f"No checker image for {challenge_id}")
            container = self.docker.containers.create(
                image_tag,
                volumes={self.volume_name: {"bind": "/workspace", "mode": "ro"}},
                network_disabled=True,
                mem_limit="50m",
                nano_cpus=500000000,
                read_only=True,
                tmpfs={"/tmp": ""},   # writable scratch space, still isolatedz
            )

            container.start()
            trace("verify_container_wait_begin", challenge_id=challenge_id)

            try:
                trace("verify_wait_start")
                result = container.wait(timeout=20)
                trace("verify_wait_done", status=result)
                exit_code = result["StatusCode"]
            except requests.exceptions.ReadTimeout as e:
                print(f"Checker timed out for {challenge_id}")
                trace("verify_wait_timeout", error=repr(e))
                exit_code = -1

            logs = container.logs().decode().strip()
            trace("loader_verify_checker_output", logs=logs, exit_code=exit_code)
            print("Checker output:" if logs else "NO Logs", logs)

            return exit_code == 0

        except Exception as e:
            trace("loader_verify_outer_exception", error=repr(e), error_type=type(e).__name__)
            print(f"Verification error: {e}")
            return False
        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass


    def cleanup(self, container):
        """Stop and remove user container and volume"""
        try:
            container.stop()
            container.remove()
        except:
            pass
        
        try:
            if hasattr(self, 'volume_name') and self.volume_name:
                volume = self.docker.volumes.get(self.volume_name)
                volume.remove()
        except:
            pass