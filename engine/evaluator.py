# engine/evaluator.py
import json
from datetime import datetime

def compute_correctness(log):
    """
    Correctness is binary: did they reach the goal?
    goal_reached comes from check.sh exit code (0 = True, 1 = False)
    """
    return 1.0 if log.get("goal_reached", False) else 0.0

def compute_command_count(log):
    """Total number of commands executed"""
    return len(log.get("commands", []))

def compute_time_seconds(log):
    """Time between started_at and submitted_at"""
    start = datetime.fromisoformat(log.get("started_at", ""))
    end = datetime.fromisoformat(log.get("submitted_at", ""))
    return (end - start).total_seconds()

def compute_error_rate(log):
    """Percentage of commands with non-zero exit code"""
    commands = log.get("commands", [])
    if not commands:
        return 0.0
    failed = sum(1 for cmd in commands if cmd.get("exit_code", 0) != 0)
    return (failed / len(commands)) * 100

def evaluate(log_data):
    """
    Main entry point. Accepts dict or file path.
    """
    if isinstance(log_data, str):
        with open(log_data, 'r') as f:
            log = json.load(f)
    else:
        log = log_data
    
    return {
        "correctness": compute_correctness(log),
        "command_count": compute_command_count(log),
        "time_seconds": compute_time_seconds(log),
        "error_rate": compute_error_rate(log),
        "goal_reached": log.get("goal_reached", False)
    } 