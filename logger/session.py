# logger/session.py - Final Production Version
import pexpect
import time
import re
from datetime import datetime
from logger.debug import trace


def _strip_control_sequences(text: str) -> str:
    """Remove common ANSI/terminal control sequences from shell output."""
    return re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', text)

class ShellSession:
    def __init__(self, challenge_id, container_name=None):
        self.challenge_id = challenge_id
        self.container_name = container_name
        self.commands = []
        self.start_time = None
        self.child = None
        trace("shell_init", challenge_id=challenge_id, container_name=container_name)
    
    def start(self):
        self.start_time = datetime.now()
        trace("shell_start_begin", challenge_id=self.challenge_id, container_name=self.container_name)
        if not hasattr(pexpect, "spawn"):
            raise RuntimeError(
                "pexpect.spawn is unavailable in this Python environment; "
                "run the TUI under a POSIX Python (WSL/Linux) or install a "
                "Windows-compatible shell backend."
            )
        
        if self.container_name:
            docker_cmd = f'docker exec -it {self.container_name} /bin/bash'
        else:
            docker_cmd = 'docker run --rm -it ubuntu:22.04 /bin/bash'
        
        trace("shell_spawn", docker_cmd=docker_cmd)
        self.child = pexpect.spawn(docker_cmd, timeout=30)
        trace("shell_spawn_ok")
        self.child.expect(['\\$', '\\#'], timeout=15)
        trace("shell_initial_prompt")
        
        # Set a unique prompt to avoid false matches
        self.child.sendline('PS1="CLICE_PROMPT> "')
        trace("shell_prompt_sent")
        self.child.expect("CLICE_PROMPT> ", timeout=5)
        trace("shell_prompt_seen_once")
        self.child.expect("CLICE_PROMPT> ", timeout=5)
        trace("shell_prompt_seen_twice")
        self._flush_buffer() 
        trace("shell_buffer_flushed_after_prompt")
        # One extra sync cycle to clear any startup residue before the
        # first user command is captured.
        self.child.sendline('')
        trace("shell_blank_line_sent")
        self.child.expect("CLICE_PROMPT> ", timeout=2)
        trace("shell_blank_line_prompt_seen")
        self._flush_buffer()
        trace("shell_start_done")
        
        return self
    
    def _flush_buffer(self):
        """Completely clear the pexpect buffer using proven method"""
        try:
            trace("shell_flush_begin")
            # Read everything available without blocking
            while True:
                self.child.read_nonblocking(4096, timeout=0.1)
        except pexpect.TIMEOUT:
            trace("shell_flush_empty")
            pass  # Buffer is empty
    
    def _clear_and_reset(self):
        """Emergency reset when prompt detection fails"""
        self._flush_buffer()
        # Try to get back to a known state
        self.child.sendline('')
        try:
            self.child.expect("CLICE_PROMPT> ", timeout=2)
            return True
        except:
            return False
    
    def execute(self, command: str) -> tuple:
        """Execute a command and return (output, exit_code, elapsed)"""
        trace("shell_execute_begin", command=command)
        # BLOCK dangerous interactive programs
        blocked = ['nano', 'vim', 'vi', 'crontab', 'top', 'htop', 'less', 'more']
        if any(command.strip().startswith(b) for b in blocked):
            trace("shell_execute_blocked", command=command)
            return f"[BLOCKED] {command} not allowed", 1, 0.0
        
        # Clear any leftover data from previous command
        self._flush_buffer()
        
        start = time.time()
        
        # Send command
        self.child.sendline(command)
        trace("shell_execute_sent", command=command)
        
        # Wait for prompt with timeout
        try:
            self.child.expect("CLICE_PROMPT> ", timeout=30)
            trace("shell_execute_prompt_seen", command=command)
        except pexpect.TIMEOUT:
            # Emergency recovery
            trace("shell_execute_timeout", command=command)
            self._clear_and_reset()
            return "[TIMEOUT] Command exceeded 30 seconds", -1, 30.0
        
        elapsed = time.time() - start
        
        # Get raw output (everything before the prompt)
        raw_output = self.child.before.decode()
        
        # Clean: remove command echo and terminal control codes
        clean = _strip_control_sequences(raw_output)
        if not self.commands:
            clean = clean.lstrip('\r\n"\' ')
        if clean.startswith(command):
            clean = clean[len(command):].lstrip()
        clean = clean.strip()
        
        # Capture exit code (in a separate transaction)
        self._flush_buffer()
        self.child.sendline('echo $?')
        trace("shell_exit_code_sent", command=command)
        self.child.expect("CLICE_PROMPT> ", timeout=5)
        trace("shell_exit_code_prompt_seen", command=command)
        exit_raw = _strip_control_sequences(self.child.before.decode())
        exit_matches = re.findall(r'\b\d+\b', exit_raw)
        exit_code = int(exit_matches[-1]) if exit_matches else -1
        
        # Log it
        self.commands.append({
            "index": len(self.commands) + 1,
            "command": command,
            "output": clean,
            "exit_code": exit_code,
            "elapsed_seconds": round(elapsed, 3)
        })
        trace("shell_execute_done", command=command, exit_code=exit_code, elapsed=round(elapsed, 3))
        
        return clean, exit_code, elapsed
    
    def submit(self):
        trace("shell_submit_begin", challenge_id=self.challenge_id)
        self.child.sendline('exit')
        try:
            self.child.expect(pexpect.EOF, timeout=5)
        except:
            self.child.terminate(force=True)
            trace("shell_submit_force_terminated")
        
        trace("shell_submit_done")
        return {
            "challenge_id": self.challenge_id,
            "started_at": self.start_time.isoformat(),
            "submitted_at": datetime.now().isoformat(),
            "goal_reached": False,
            "commands": self.commands
        }

    def terminate(self):
        """Forcefully close the shell without waiting for a prompt."""
        trace("shell_terminate_begin", challenge_id=self.challenge_id)
        if not self.child:
            return
        try:
            if self.child.isalive():
                self.child.sendline('exit')
                try:
                    self.child.expect(pexpect.EOF, timeout=3)
                except Exception:
                    pass
        finally:
            try:
                if self.child.isalive():
                    self.child.terminate(force=True)
            except Exception as e:
                trace("shell_terminate_error", error=repr(e))
            trace("shell_terminate_done")
            