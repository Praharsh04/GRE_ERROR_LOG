"""
GRE Pace Trainer — Session Storage

Persists Question Tracker session data as JSON files in a local
sessions/ directory for historical review.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

_SESSIONS_DIR = Path(__file__).resolve().parent.parent / "sessions"


class SessionStorage:
    """Save and load tracker session data."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self._dir = base_dir or _SESSIONS_DIR
        self._dir.mkdir(parents=True, exist_ok=True)

    def save_session(self, session_data: dict) -> Path:
        """Save a session and return the file path."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"session_{ts}.json"
        path = self._dir / filename

        # Add metadata
        session_data["saved_at"] = datetime.now().isoformat()

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, default=str)
        except OSError:
            pass
        return path

    def load_sessions(self) -> list[dict]:
        """Load all saved sessions, newest first."""
        sessions: list[dict] = []
        if not self._dir.exists():
            return sessions

        for path in sorted(self._dir.glob("session_*.json"), reverse=True):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    sessions.append(json.load(f))
            except (json.JSONDecodeError, OSError):
                continue
        return sessions

    def session_to_dict(self, stats: Any) -> dict:
        """Convert a SessionStats object into a serialisable dict."""
        questions = []
        for q in stats.questions:
            questions.append({
                "number": q.number,
                "time_ms": q.time_ms,
                "target_ms": q.target_ms,
                "pace": q.pace,
                "diff_ms": q.diff_ms,
                "timestamp": q.timestamp,
                "status": q.status,
            })

        return {
            "total_questions": stats.total_questions,
            "total_time_ms": stats.total_time_ms,
            "target_time_ms": stats.target_time_ms,
            "average_ms": stats.average_ms,
            "median_ms": stats.median_ms,
            "fastest_ms": stats.fastest_ms,
            "fastest_q": stats.fastest_q,
            "slowest_ms": stats.slowest_ms,
            "slowest_q": stats.slowest_q,
            "fast_count": stats.fast_count,
            "on_target_count": stats.on_target_count,
            "slow_count": stats.slow_count,
            "on_target_pct": round(stats.on_target_pct, 1),
            "questions": questions,
        }
