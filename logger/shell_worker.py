# logger/shell_worker.py
"""
Runs ShellSession in an isolated OS process so pexpect's fork() never
races against Textual's asyncio loop / driver threads.
"""
import multiprocessing as mp
from logger.session import ShellSession
from logger.debug import trace

_ctx = mp.get_context("spawn")



def _worker(challenge_id, container_name, conn):
    trace("worker_start", challenge_id=challenge_id, container_name=container_name)
    try:
        shell = ShellSession(challenge_id, container_name=container_name)
        trace("worker_shell_created")
        shell.start()
        trace("worker_shell_ready")
        conn.send(("ready", None))
        trace("worker_ready_sent")
    except Exception as e:
        trace("worker_start_error", error=repr(e))
        conn.send(("error", str(e)))
        return

    while True:
        try:
            trace("worker_waiting_for_message")
            msg = conn.recv()
            trace("worker_received_message", message=msg)
        except EOFError:
            trace("worker_eof")
            break

        if msg == "__exit__":
            try:
                result = shell.submit()
                conn.send(("submitted", result))
                trace("worker_submitted")
            except Exception as e:
                trace("worker_submit_error", error=repr(e))
                conn.send(("error", str(e)))
            break

        try:
            output, exit_code, elapsed = shell.execute(msg)
            conn.send(("result", (output, exit_code, elapsed)))
            trace("worker_result_sent", exit_code=exit_code, elapsed=elapsed)
        except Exception as e:
            trace("worker_execute_error", error=repr(e))
            conn.send(("error", str(e)))


class IPCShellSession:
    """
    Drop-in replacement for ShellSession, but backed by a subprocess.
    Same execute()/submit() surface so SessionScreen barely changes.
    """

    def __init__(self, challenge_id, container_name=None):
        self.challenge_id = challenge_id
        self.container_name = container_name
        self._parent_conn, self._child_conn = _ctx.Pipe()
        self._proc = None
        trace("ipc_init", challenge_id=challenge_id, container_name=container_name)

    def start(self, ready_timeout=30):
        trace("ipc_start_begin", challenge_id=self.challenge_id, ready_timeout=ready_timeout)
        self._proc = _ctx.Process(
            target=_worker,
            args=(self.challenge_id, self.container_name, self._child_conn),
            daemon=True,
        )
        self._proc.start()
        trace("ipc_process_started", pid=self._proc.pid)

        if not self._parent_conn.poll(timeout=ready_timeout):
            trace("ipc_start_timeout", alive=self._proc.is_alive(), exitcode=self._proc.exitcode)
            raise TimeoutError("Shell process did not respond in time")

        status, payload = self._parent_conn.recv()
        trace("ipc_start_response", status=status, payload_type=type(payload).__name__)
        if status == "error":
            raise RuntimeError(payload)
        return self

    def execute(self, command, timeout=35):
        trace("ipc_execute_begin", command=command, timeout=timeout)
        self._parent_conn.send(command)
        if not self._parent_conn.poll(timeout=timeout):
            trace("ipc_execute_timeout", command=command)
            return "[TIMEOUT] No response from shell process", -1, float(timeout)

        status, payload = self._parent_conn.recv()
        trace("ipc_execute_response", command=command, status=status)
        if status == "error":
            return f"[ERROR] {payload}", -1, 0.0
        return payload  # (output, exit_code, elapsed)

    def submit(self, timeout=10):
        trace("ipc_submit_begin", timeout=timeout)
        self._parent_conn.send("__exit__")
        if self._parent_conn.poll(timeout=timeout):
            status, payload = self._parent_conn.recv()
            trace("ipc_submit_response", status=status)
            if status == "submitted":
                return payload
        if self._proc:
            self._proc.terminate()
            trace("ipc_submit_terminated", exitcode=self._proc.exitcode)
        return {
            "challenge_id": self.challenge_id,
            "goal_reached": False,
            "commands": [],
        }

    def terminate(self):
        if self._proc and self._proc.is_alive():
            self._proc.terminate()
            trace("ipc_terminated")
