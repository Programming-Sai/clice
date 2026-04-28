# sandbox/playground_fixed.py
import pexpect
import time
import re

print("="*60)
print("FIXED PLAYGROUND - Forced Buffer Reset")
print("="*60)

child = pexpect.spawn('docker run --rm -it ubuntu:22.04 /bin/bash', timeout=30)
child.expect(['\\$', '\\#'], timeout=10)
print("✓ Ready\n")

def flush_buffer():
    """Discard anything currently in the buffer"""
    try:
        # Try to read everything available without blocking
        child.read_nonblocking(10000, timeout=0.1)
    except:
        pass

def execute(cmd):
    """Execute command and return clean output"""
    flush_buffer()  # Clear any leftover data
    
    child.sendline(cmd)
    
    try:
        child.expect(['\\$', '\\#'], timeout=30)
    except pexpect.TIMEOUT:
        # On timeout, force reset
        flush_buffer()
        return "[TIMEOUT - command took >30s]", -1
    
    # Get output
    raw = child.before.decode()
    
    # Clean
    clean = re.sub(r'\x1b\[[0-9;]*[mK]', '', raw)
    
    # Remove command echo
    if clean.startswith(cmd):
        clean = clean[len(cmd):].lstrip()
    
    # Remove trailing prompt
    clean = re.sub(r'root@[a-f0-9]+:/[#$]?\s*$', '', clean)
    clean = clean.strip()
    
    # Get exit code separately
    child.sendline('echo $?')
    child.expect(['\\$', '\\#'], timeout=5)
    exit_raw = child.before.decode()
    exit_match = re.search(r'(\d+)\s*$', exit_raw)
    exit_code = int(exit_match.group(1)) if exit_match else -1
    
    return clean, exit_code

while True:
    cmd = input(">>> ").strip()
    if cmd == ":quit":
        break
    
    output, exit_code = execute(cmd)
    print(f"\n[exit: {exit_code}]\n{output}\n")

child.sendline('exit')
child.expect(pexpect.EOF)
print("✓ Done")