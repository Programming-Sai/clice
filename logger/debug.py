from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import os
import threading


_TRACE_PATH = Path(__file__).resolve().parents[1] / "logs" / "shell-trace.log"


def trace(stage: str, **fields) -> None:
    """Append a small structured trace line to the session debug log."""
    try:
        _TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        pid = os.getpid()
        thread = threading.current_thread().name
        extras = " ".join(f"{key}={value!r}" for key, value in fields.items())
        line = f"{timestamp} pid={pid} thread={thread} stage={stage}"
        if extras:
            line = f"{line} {extras}"
        with _TRACE_PATH.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        # Tracing must never interfere with the UI or shell startup path.
        pass
