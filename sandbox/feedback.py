#!/usr/bin/env python3
"""
Test the AIFeedbackService directly.
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.services.ai_feedback import AIFeedbackService
from ui.services.config import Config
from engine.evaluator import evaluate

# Sample session log (from a real run)
SAMPLE_SESSION_LOG = {
    "challenge_id": "hello-clice",
    "started_at": "2026-07-02T13:36:18.590414",
    "submitted_at": "2026-07-02T13:37:18.403892",
    "goal_reached": True,
    "commands": [
        {"command": "echo \"Hello clice\" > output.txt", "exit_code": 0, "output": "", "elapsed_seconds": 0.07},
        {"command": "cat output.txt", "exit_code": 0, "output": "Hello clice", "elapsed_seconds": 0.06},
        {"command": ":submit", "exit_code": 0, "output": "", "elapsed_seconds": 0.01}
    ]
}

# Sample challenge
SAMPLE_CHALLENGE = {
    "id": "05d63620-db71-4bf4-bdbd-48b89ce0debb",
    "code": "hello-clice",
    "title": "Hello CLICE Challenge",
    "description": "Create a file called output.txt containing exactly 'Hello clice'",
    "difficulty": "BEGINNER[#--]",
    "category": "FILE_MANIPULATION",
    "markdown": "## Hello CLICE Challenge\n\nCreate a file called output.txt...",
    "objectives": [
        "Create a file named `output.txt` in the `/workspace` directory",
        "The file must contain the exact string 'Hello clice'"
    ]
}

def test_service():
    print("="*60)
    print("Testing AIFeedbackService")
    print("="*60)
    
    # Load config
    config = Config()
    print(f"\n📋 Config loaded:")
    print(f"  API Key present: {bool(config.openrouter_api_key)}")
    print(f"  Model: {config.openrouter_model}")
    print(f"  API Key (first 10 chars): {config.openrouter_api_key[:10]}...")
    
    if not config.openrouter_api_key:
        print("\n❌ No API key found! Check .env file.")
        return
    
    # Compute metrics
    print("\n📊 Computing metrics...")
    metrics = evaluate(SAMPLE_SESSION_LOG)
    print(f"  Commands: {metrics['command_count']}")
    print(f"  Time: {metrics['time_seconds']:.1f}s")
    print(f"  Error rate: {metrics['error_rate']:.1f}%")
    print(f"  Correctness: {metrics['correctness'] * 100:.1f}%")
    
    # Generate feedback
    print("\n🤖 Generating AI feedback...")
    service = AIFeedbackService(config)
    
    try:
        feedback = service.generate_feedback(SAMPLE_CHALLENGE, SAMPLE_SESSION_LOG, metrics)
        
        print("\n" + "="*60)
        print("AI FEEDBACK")
        print("="*60)
        
        print(f"\nType: {type(feedback)}")
        print(f"Length: {len(feedback)} characters")
        print(f"Content:\n{feedback}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_service()