# sandbox/playground_fixed.py
import pexpect
import re

print("=" * 60)
print("FIXED PLAYGROUND - Forced Buffer Reset")
print("=" * 60)

child = pexpect.spawn("docker run --rm -it ubuntu:22.04 /bin/bash", timeout=30)
child.expect(["\\$", "\\#"], timeout=10)
print("✓ Ready\n")


def strip_control_sequences(text):
    """Remove ANSI and terminal control sequences from shell output."""
    return re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)


def flush_buffer():
    """Discard anything currently in the buffer."""
    try:
        child.read_nonblocking(10000, timeout=0.1)
    except Exception:
        pass


def execute(cmd):
    """Execute command and return clean output."""
    flush_buffer()

    child.sendline(cmd)

    try:
        child.expect(["\\$", "\\#"], timeout=30)
    except pexpect.TIMEOUT:
        flush_buffer()
        return "[TIMEOUT - command took >30s]", -1

    raw = child.before.decode()
    clean = strip_control_sequences(raw)

    if clean.startswith(cmd):
        clean = clean[len(cmd):].lstrip()

    clean = re.sub(r"root@[a-f0-9]+:/[#$]?\s*$", "", clean).strip()

    child.sendline("echo $?")
    child.expect(["\\$", "\\#"], timeout=5)
    exit_raw = strip_control_sequences(child.before.decode())
    exit_matches = re.findall(r"\b\d+\b", exit_raw)
    exit_code = int(exit_matches[-1]) if exit_matches else -1

    return clean, exit_code


while True:
    cmd = input(">>> ").strip()
    if cmd == ":quit":
        break

    output, exit_code = execute(cmd)
    print(f"\n[exit: {exit_code}]\n{output}\n")

child.sendline("exit")
child.expect(pexpect.EOF)
print("✓ Done")
 