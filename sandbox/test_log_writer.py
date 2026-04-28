# sandbox/test_log_writer.py
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger.session import ShellSession

session = ShellSession(challenge_id="test_01")
session.start()
print("✓ Ready. Type commands, then :submit\n")

while True:
    cmd = input("$ ").strip()
    if not cmd:
        continue
    if cmd == ":submit":
        break
    
    output, exit_code, elapsed = session.execute(cmd)
    
    if exit_code == 0:
        print(f"[{elapsed:.2f}s] ✓")
    else:
        print(f"[{elapsed:.2f}s] ✗ (exit {exit_code})")
    
    if output:
        print(output)

log = session.submit()
with open("assets/log.json", "w") as f:
    json.dump(log, f, indent=2)

print(f"\n✓ Log saved. Commands: {len(log['commands'])}")