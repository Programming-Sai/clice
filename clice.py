#!/usr/bin/env python3
import sys
import json
from pathlib import Path
from loader.registry import ChallengeRegistry
from loader.challenge_loader import ChallengeLoader
from logger.session import ShellSession
from engine.evaluator import evaluate

def main():
    if len(sys.argv) < 2:
        print("Usage: clice list")
        print("       clice run <challenge-id>")
        sys.exit(1)
    
    command = sys.argv[1]
    registry = ChallengeRegistry()
    
    if command == "list":
        challenges = registry.fetch()
        print("\nAvailable challenges:")
        for c in challenges:
            print(f"  {c['id']} - {c['name']} ({c['difficulty']})")
        return
    
    if command == "run":
        if len(sys.argv) < 3:
            print("Usage: clice run <challenge-id>")
            sys.exit(1)
        
        challenge_id = sys.argv[2]
        challenge_info = registry.get_challenge(challenge_id)
        
        if not challenge_info:
            print(f"Challenge '{challenge_id}' not found")
            sys.exit(1)
        
        print(f"\n== {challenge_info['name']} == ")
        print(f"{challenge_info['description']}\n")
        
        # Load challenge (pulls image + builds checker)
        loader = ChallengeLoader()
        container = loader.load_challenge(challenge_info)
        print("✓ Environment ready\n")
        
        # Start shell session
        session = ShellSession(challenge_id, container_name=container.id)
        session.start()
        
        print("Type commands. Type ':submit' when done.\n")
        
        # Interactive loop
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
            
            output, exit_code, elapsed = session.execute(cmd)
            if exit_code == 0:
                print(f"[{elapsed:.2f}s]")
            else:
                print(f"[{elapsed:.2f}s] (exit {exit_code})")
            if output:
                print(output)
        
        # Submit, verify, evaluate
        log = session.submit()
        
        print("\nVerifying...")
        passed = loader.verify(challenge_id, container)
        
        log["goal_reached"] = passed
        metrics = evaluate(log)
        
        # Save log
        safe_timestamp = log['started_at'].replace(":", "-")
        log_path = Path("assets") / f"{challenge_id}_{safe_timestamp}.json"
        log_path.parent.mkdir(exist_ok=True)
        with open(log_path, "w") as f:
            json.dump(log, f, indent=2)
        
        # Report
        print("\n" + "="*50)
        print("RESULTS")
        print("="*50)
        print(f"Challenge: {passed and '✓ PASSED' or '✗ FAILED'}")
        print(f"Commands: {metrics['command_count']}")
        print(f"Time: {metrics['time_seconds']:.1f}s")
        print(f"Error rate: {metrics['error_rate']:.0f}%")
        print(f"Log saved: {log_path}")
        
        # Cleanup
        loader.cleanup(container)

if __name__ == "__main__":
    main()