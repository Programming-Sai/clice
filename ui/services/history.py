# ui/services/history.py
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from ui.services.config import Config

class HistoryService:
    """Handles saving, loading, and deleting session logs."""

    def __init__(self, config: Config = None):
        config = config or Config()
        # CLICE_LOGS_DIR (via Config.logs_dir) previously wasn't wired to
        # anything - sessions always went to a hardcoded "assets/sessions"
        # regardless of that setting. Now it actually controls where
        # session logs live.
        self.SESSIONS_DIR = config.logs_dir / "sessions"
        self.INDEX_FILE = self.SESSIONS_DIR / "index.json"
        self.SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        self._ensure_index()
    
    def _ensure_index(self) -> None:
        if not self.INDEX_FILE.exists():
            self._write_index([])
    
    def _write_index(self, index: List[Dict]) -> None:
        with open(self.INDEX_FILE, "w") as f:
            json.dump(index, f, indent=2)
    
    def _read_index(self) -> List[Dict]:
        with open(self.INDEX_FILE, "r") as f:
            return json.load(f)
    
    def save_session(self, session_log: Dict, challenge: Dict) -> str:
        """Save initial session log (before metrics/AI feedback are computed)."""
        session_id = str(uuid.uuid4())[:8]
        
        full_log = {
            "session_id": session_id,
            "challenge_id": challenge.get("id"),
            "challenge_code": challenge.get("code", challenge.get("id")),
            "challenge_title": challenge.get("title"),
            "category": challenge.get("category", "CLI"),
            "difficulty": challenge.get("difficulty", "intermediate"),
            "tags": challenge.get("tags", []),
            "objectives": challenge.get("objectives", []),
            "started_at": session_log.get("started_at"),
            "submitted_at": session_log.get("submitted_at"),
            "goal_reached": session_log.get("goal_reached", False),
            "commands": session_log.get("commands", []),
            "checker_output": session_log.get("checker_output", ""),
            "checker_exit_code": session_log.get("checker_exit_code"),
            "checker_error": session_log.get("checker_error"),
            "metrics": {},  # Will be filled later
            "ai_feedback": ""  # Will be filled later
        }
        
        # Save full log
        log_path = self.SESSIONS_DIR / f"{session_id}.json"
        with open(log_path, "w") as f:
            json.dump(full_log, f, indent=2)
        
        # Update index
        index = self._read_index()
        index.append({
            "session_id": session_id,
            "challenge_code": challenge.get("code", challenge.get("id")),
            "challenge_title": challenge.get("title"),
            "started_at": session_log.get("started_at"),
            "submitted_at": session_log.get("submitted_at"),
            "duration_seconds": self._calculate_duration(session_log),
            "command_count": len(session_log.get("commands", [])),
            "goal_reached": session_log.get("goal_reached", False),
            "status": "PASS" if session_log.get("goal_reached", False) else "FAIL",
            "log_path": str(log_path)
        })
        self._write_index(index)
        
        return session_id
    
    def update_session(self, session_id: str, metrics: Dict, ai_feedback: str) -> bool:
        """Update a session with computed metrics and AI feedback."""
        log_path = self.SESSIONS_DIR / f"{session_id}.json"
        if not log_path.exists():
            return False
        
        with open(log_path, "r") as f:
            log = json.load(f)
        
        log["metrics"] = metrics
        log["ai_feedback"] = ai_feedback
        
        with open(log_path, "w") as f:
            json.dump(log, f, indent=2)
        
        return True
    
    def get_sessions(self) -> List[Dict]:
        """Get all session summaries (for the history table)."""
        index = self._read_index()
        
        # Sort by started_at (newest first)
        return sorted(index, key=lambda x: x.get("started_at", ""), reverse=True)
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get a full session log by ID."""
        log_path = self.SESSIONS_DIR / f"{session_id}.json"
        if not log_path.exists():
            return None
        with open(log_path, "r") as f:
            return json.load(f)
    
    def delete_session(self, session_id: str) -> bool:
        index = self._read_index()
        new_index = [s for s in index if s["session_id"] != session_id]
        if len(new_index) == len(index):
            return False
        
        log_path = self.SESSIONS_DIR / f"{session_id}.json"
        if log_path.exists():
            log_path.unlink()
        
        self._write_index(new_index)
        return True
    
    def clear_all(self) -> None:
        for f in self.SESSIONS_DIR.glob("*.json"):
            if f.name != "index.json":
                f.unlink()
        self._write_index([])
    
    def _calculate_duration(self, session_log: Dict) -> float:
        try:
            start = datetime.fromisoformat(session_log.get("started_at", ""))
            end = datetime.fromisoformat(session_log.get("submitted_at", ""))
            return (end - start).total_seconds()
        except:
            return 0.0