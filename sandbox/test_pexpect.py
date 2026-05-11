# sandbox/comprehensive_test.py
import pexpect
import time
import sys
import re

def run_test(name, commands, expect_pattern='\\#', timeout=10, needs_python=False):
    print(f"\n{'='*50}")
    print(f"TEST: {name}")
    print('='*50)
    
    # Skip Python test since python3 isn't installed
    if needs_python:
        print(f"SKIPPED: {name} requires python3 which is not in base container")
        return
    
    child = pexpect.spawn('docker run --rm -it ubuntu:22.04 /bin/bash', timeout=30)
    
    try:
        child.expect(['\\$', '\\#'], timeout=15)
    except pexpect.TIMEOUT:
        print("FAILED: Could not get initial prompt")
        return
    
    for cmd, expected in commands:
        print(f"\n> {cmd}")
        child.sendline(cmd)
        
        try:
            child.expect(expected, timeout=timeout)
            output = child.before.decode()
            # Truncate long output for readability
            if len(output) > 500:
                print(f"Output (first 500 chars): {repr(output[:500])}...")
            else:
                print(f"Output: {repr(output)}")
        except pexpect.TIMEOUT:
            print(f"TIMEOUT after {timeout}s")
            print(f"Buffer: {repr(child.before.decode()[:200])}")
        except Exception as e:
            print(f"ERROR: {e}")
    
    try:
        child.sendline('exit')
        child.expect(pexpect.EOF, timeout=5)
        print("✓ Clean exit")
    except:
        print("Exit failed, but continuing")
        child.terminate(force=True)

def strip_ansi(text):
    """Remove ANSI escape codes from text"""
    return re.sub(r'\x1b\[[0-9;]*[mK]', '', text)

def test_state_persistence():
    print(f"\n{'='*50}")
    print(f"TEST: State Persistence (cd, vars, files)")
    print('='*50)
    
    child = pexpect.spawn('docker run --rm -it ubuntu:22.04 /bin/bash', timeout=30)
    
    try:
        child.expect(['\\$', '\\#'], timeout=15)
    except pexpect.TIMEOUT:
        print("FAILED: Could not get initial prompt")
        return False
    
    results = []
    
    # Change directory
    child.sendline('cd /tmp')
    child.expect('\\#')
    results.append(("Changed to /tmp", True))
    
    # Create a file
    child.sendline('echo "persistent data" > testfile.txt')
    child.expect('\\#')
    results.append(("Created testfile.txt", True))
    
    # Set a variable
    child.sendline('MYVAR="hello from variable"')
    child.expect('\\#')
    results.append(("Set MYVAR", True))
    
    # Export it
    child.sendline('export MYVAR')
    child.expect('\\#')
    results.append(("Exported MYVAR", True))
    
    # View all
    child.sendline('ls')
    child.expect('\\#')
    results.append(("View files", True))

    # Verify we're STILL in /tmp
    child.sendline('pwd')
    child.expect('\\#')
    output = child.before.decode()
    output_clean = strip_ansi(output)
    # Extract the actual pwd output (everything after the command)
    lines = output_clean.split('\n')
    pwd_value = None
    for line in lines:
        if line and not line.startswith('pwd') and 'pwd' not in line:
            pwd_value = line.strip()
            break
    if pwd_value and '/tmp' in pwd_value:
        results.append((f"Current directory: '{pwd_value}'", True))
    else:
        results.append((f"Current directory: '{pwd_value}' (expected /tmp)", False))
    
    # Verify file exists
    child.sendline('cat testfile.txt')
    child.expect('\\#')
    output = child.before.decode()
    output_clean = strip_ansi(output)
    lines = output_clean.split('\n')
    file_content = None
    for line in lines:
        if line and 'cat testfile.txt' not in line:
            file_content = line.strip()
            if file_content:
                break
    if file_content and 'persistent data' in file_content:
        results.append((f"File content: '{file_content}'", True))
    else:
        results.append((f"File content: '{file_content}' (expected 'persistent data')", False))
    
    # Verify variable persists
    child.sendline('echo $MYVAR')
    child.expect('\\#')
    output = child.before.decode()
    output_clean = strip_ansi(output)
    lines = output_clean.split('\n')
    var_value = None
    for line in lines:
        if line and 'echo $MYVAR' not in line:
            var_value = line.strip()
            if var_value:
                break
    if var_value and 'hello from variable' in var_value:
        results.append((f"Variable value: '{var_value}'", True))
    else:
        results.append((f"Variable value: '{var_value}' (expected 'hello from variable')", False))
    
    child.sendline('exit')
    try:
        child.expect(pexpect.EOF, timeout=5)
        results.append(("Container exit", True))
    except:
        results.append(("Container exit", False))
        child.terminate(force=True)
    
    # Print summary
    print("\n--- State Persistence Results ---")
    all_passed = True
    for msg, passed in results:
        status = "✓" if passed else "✗"
        print(f"  {status} {msg}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n✓✓✓ State persistence CONFIRMED - terminal remembers everything ✓✓✓")
    else:
        print("\n✗ Some state persistence checks failed")
    
    return all_passed

# Test suite
tests = [
    ("Long running command", [("sleep 2 && echo done", '\\#')], '\\#', 5, False),
    ("No output command", [("cd /tmp", '\\#')], '\\#', 5, False),
    ("Stderr command", [("ls /nonexistent", '\\#')], '\\#', 5, False),
    ("Exit code capture", [
        ("ls /nonexistent", '\\#'),
        ("echo $?", '\\#')
    ], '\\#', 5, False),
    ("Python interactive", [
        ("python3", '>>>'),
        ("print('hi')", '>>>'),
        ("exit()", '\\#')
    ], '>>>', 5, True),
    ("No newline", [("printf 'no newline'", '\\#')], '\\#', 5, False),
]

print("\n" + "="*60)
print("C.L.I.C.E. - Comprehensive Pexpect Test Suite")
print("="*60)

# Run all tests
for test in tests:
    try:
        run_test(*test)
    except Exception as e:
        print(f"TEST CRASHED: {e}")
        continue

# Run state persistence test
test_state_persistence()

print("\n" + "="*60)
print("All tests completed")
print("="*60) 