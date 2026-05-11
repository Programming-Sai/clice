# logger/session.py - Final Production Version
import pexpect
import time
import re
from datetime import datetime


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
    
    def start(self):
        self.start_time = datetime.now()
        
        if self.container_name:
            docker_cmd = f'docker exec -it {self.container_name} /bin/bash'
        else:
            docker_cmd = 'docker run --rm -it ubuntu:22.04 /bin/bash'
        
        self.child = pexpect.spawn(docker_cmd, timeout=30)
        self.child.expect(['\\$', '\\#'], timeout=15)
        
        # Set a unique prompt to avoid false matches
        self.child.sendline('PS1="CLICE_PROMPT> "')
        self.child.expect("CLICE_PROMPT> ", timeout=5)
        self._flush_buffer() 
        # One extra sync cycle to clear any startup residue before the
        # first user command is captured.
        self.child.sendline('')
        self.child.expect("CLICE_PROMPT> ", timeout=2)
        self._flush_buffer()
        
        return self
    
    def _flush_buffer(self):
        """Completely clear the pexpect buffer using proven method"""
        try:
            # Read everything available without blocking
            while True:
                self.child.read_nonblocking(4096, timeout=0.1)
        except pexpect.TIMEOUT:
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
        # BLOCK dangerous interactive programs
        blocked = ['nano', 'vim', 'vi', 'crontab', 'top', 'htop', 'less', 'more']
        if any(command.strip().startswith(b) for b in blocked):
            return f"[BLOCKED] {command} not allowed", 1, 0.0
        
        # Clear any leftover data from previous command
        self._flush_buffer()
        
        start = time.time()
        
        # Send command
        self.child.sendline(command)
        
        # Wait for prompt with timeout
        try:
            self.child.expect("CLICE_PROMPT> ", timeout=30)
        except pexpect.TIMEOUT:
            # Emergency recovery
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
        self.child.expect("CLICE_PROMPT> ", timeout=5)
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
        
        return clean, exit_code, elapsed
    
    def submit(self):
        self.child.sendline('exit')
        try:
            self.child.expect(pexpect.EOF, timeout=5)
        except:
            self.child.terminate(force=True)
        
        return {
            "challenge_id": self.challenge_id,
            "started_at": self.start_time.isoformat(),
            "submitted_at": datetime.now().isoformat(),
            "goal_reached": False,
            "commands": self.commands
        }
