"""
GRE Pace Trainer — Settings Persistence

Saves and restores user preferences to a JSON file alongside the
application executable / script.
"""

import json
from pathlib import Path

# Resolve settings path relative to the project root
_SETTINGS_DIR = Path(__file__).resolve().parent.parent
_SETTINGS_FILE = _SETTINGS_DIR / "settings.json"

DEFAULTS: dict = {
    "interval_minutes": 3,
    "interval_seconds": 0,
    "question_count": 20,
    "always_on_top": True,
    "sound_enabled": True,
    "notifications_enabled": True,
    "volume": 80,
    "notification_sound": "Classic Beep",
    "muted": False,
    "window_x": -1,
    "window_y": -1,
}


class SettingsManager:
    """Load and save application settings to a JSON file."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or _SETTINGS_FILE

    @property
    def settings_path(self) -> Path:
        return self._path

    def load(self) -> dict:
        """Load settings from disk, falling back to defaults for missing keys."""
        settings = dict(DEFAULTS)
        try:
            if self._path.exists():
                with open(self._path, "r", encoding="utf-8") as f:
                    stored = json.load(f)
                if isinstance(stored, dict):
                    settings.update(stored)
        except (json.JSONDecodeError, OSError, ValueError):
            pass  # Corrupt file — use defaults
        return settings

    def save(self, settings: dict) -> None:
        """Write settings to disk."""
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
        except OSError:
            pass  # Non-critical — silently ignore write failures
