#!/usr/bin/env python3
import sys
import json
from pathlib import Path
from ui.services.registry import RegistryService
from ui.services.config import Config
from loader.challenge_loader import ChallengeLoader
from logger.session import ShellSession
from engine.evaluator import evaluate
from logger.debug import trace

def main():
    trace("cli_main_begin", argv=sys.argv[1:])
    if len(sys.argv) < 2:
        print("Usage: clice list")
        print("       clice run <challenge-id>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    config = Config()
    registry = RegistryService(config)
    
    if command == "list":
        challenges = registry.get_challenges()
        print("\nAvailable challenges:")
        for c in challenges:
            display_id = c.get("code", c.get("id", "???")[:8])
            print(f"  {display_id} - {c.get('title', 'Unknown')} ({c.get('difficulty', 'N/A')})")
        return
    
    if command == "run":
        trace("cli_run_begin", challenge_id=sys.argv[2] if len(sys.argv) > 2 else None)
        if len(sys.argv) < 3:
            print("Usage: clice run <challenge-id>")
            sys.exit(1)
        
        
        user_input = sys.argv[2]
        mode = 'container'
        if len(sys.argv) > 3: 
            mode = sys.argv[3]
        challenges = registry.get_challenges()
        # challenges = []
        challenge_info = None
        for c in challenges:
            code = c.get("code", "")
            uuid_full = c.get("id", "")  # id is the UUID
            
            # 1. Exact match on code
            if code == user_input:
                challenge_info = c
                break
            
            # 2. Exact match on full UUID
            if uuid_full == user_input:
                challenge_info = c
                break
            
            # 3. Match on first 8 characters of UUID
            if len(user_input) >= 8 and uuid_full.startswith(user_input):
                challenge_info = c
                break
        
        if not challenge_info:
            print(f"Challenge '{user_input}' not found")
            print("\nAvailable challenges:")
            for c in challenges:
                display_id = c.get("code", c.get("id", "???")[:8])
                print(f"  {display_id} - {c.get('title', 'Unknown')}")
            sys.exit(1)
        
        # Get primary identifier (code) for display and internal use
        
        
        
        print(f"\n== {challenge_info.get('title', challenge_info.get('code'))} ==")
        print(f"{challenge_info.get('description', 'No description')}\n")
        
        loader = ChallengeLoader()
        container = None if mode == 'raw' else loader.load_challenge(challenge_info)
        print("✓ Environment ready\n")
        
        session = ShellSession(challenge_info.get("id"), container_name=None)
        session.start()
        
        print("Type commands. Type ':submit' when done.\n")
        
        while True:
            cmd = input("$ ").strip()
            if not cmd:
                continue
            if cmd == ":submit":
                break
            if cmd == ":quit":
                print("Session cancelled")
                loader.cleanup(container)
                return
            
            output, exit_code, elapsed, prompt = session.execute(cmd)
            if exit_code == 0:
                print(f"[{elapsed:.2f}s]")
            else:
                print(f"[{elapsed:.2f}s] (exit {exit_code})")
            if output:
                print(output)
            print(f"\n======\n {prompt} \n======\n")
        
        log = session.submit()
        
        print("\nVerifying...")
        passed = loader.verify(challenge_info.get("id"), container)
        
        # log["goal_reached"] = passed
        metrics = evaluate(log)
        
        safe_timestamp = log['started_at'].replace(":", "-")
        log_path = Path("assets") / f"{challenge_info.get('id')}_{safe_timestamp}.json"
        log_path.parent.mkdir(exist_ok=True)
        with open(log_path, "w") as f:
            json.dump(log, f, indent=2)
        
        print("\n" + "="*50)
        print("RESULTS")
        print("="*50)
        print(f"Challenge: {passed and '✓ PASSED' or '✗ FAILED'}")
        print(f"Commands: {metrics['command_count']}")
        print(f"Time: {metrics['time_seconds']:.1f}s")
        print(f"Error rate: {metrics['error_rate']:.0f}%")
        print(f"Log saved: {log_path}")
        
        # loader.cleanup(container)

if __name__ == "__main__":
    main()