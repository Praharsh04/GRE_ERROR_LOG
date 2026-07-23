"""
GRE Pace Trainer — Sound Manager

Manages notification sounds using PySide6.QtMultimedia to ensure proper
audio routing (e.g., to Bluetooth headphones) and reliable volume control.

Supports selectable notification sounds from assets/sounds/ and a mute toggle.
"""

import os
from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")

SOUND_OPTIONS = {
    "Classic Beep": "classic_beep.wav",
    "Bell": "bell.wav",
    "Chime": "chime.wav",
    "Digital Alarm": "digital_alarm.wav",
    "Soft Ding": "soft_ding.wav",
    "Short Buzzer": "short_buzzer.wav",
}


class SoundManager:
    """Non-blocking sound notification manager using QSoundEffect."""

    def __init__(self) -> None:
        self._enabled: bool = True
        self._muted: bool = False
        self._volume: int = 80  # 0-100
        self._notification_sound: str = "Classic Beep"

        # ── Interval & over-time effects (loaded from sounds/) ──
        self._interval_sfx = QSoundEffect()
        self._over_time_sfx = QSoundEffect()
        self._over_time_sfx.setLoopCount(3)

        self._load_notification_sound()

        # ── Completion effect (always uses assets/completion.wav) ──
        self._completion_sfx = QSoundEffect()
        self._completion_sfx.setSource(QUrl.fromLocalFile(os.path.join(ASSETS_DIR, "completion.wav")))

        # ── Preview effect (reusable single-shot player) ──
        self._preview_sfx = QSoundEffect()

        self._update_volumes()

    # ── Properties ────────────────────────────────────────────

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def volume(self) -> int:
        return self._volume

    @property
    def muted(self) -> bool:
        return self._muted

    # ── Configuration ─────────────────────────────────────────

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def set_volume(self, volume: int) -> None:
        self._volume = max(0, min(100, volume))
        self._update_volumes()

    def set_muted(self, muted: bool) -> None:
        self._muted = muted

    def set_notification_sound(self, name: str) -> None:
        """Change the notification sound used for interval and over-time alerts.

        Args:
            name: A key from SOUND_OPTIONS (e.g. "Classic Beep").
        """
        if name not in SOUND_OPTIONS:
            return
        self._notification_sound = name
        self._load_notification_sound()

    def get_notification_sound(self) -> str:
        """Return the display name of the currently selected notification sound."""
        return self._notification_sound

    def get_sound_names(self) -> list[str]:
        """Return a list of available notification sound display names."""
        return list(SOUND_OPTIONS.keys())

    # ── Playback ──────────────────────────────────────────────

    def play_interval_beep(self) -> None:
        """Short, clean beep for interval completion."""
        if not self._should_play():
            return
        self._interval_sfx.play()

    def play_completion_beep(self) -> None:
        """Distinctive tone pattern for session completion."""
        if not self._should_play():
            return
        self._completion_sfx.play()

    def play_over_time_beep(self) -> None:
        """Urgent beep for exceeding target time."""
        if not self._should_play():
            return
        self._over_time_sfx.play()

    def preview_sound(self, name: str) -> None:
        """Play a single preview of the given sound.

        Args:
            name: A key from SOUND_OPTIONS.
        """
        if name not in SOUND_OPTIONS:
            return
        filepath = os.path.join(SOUNDS_DIR, SOUND_OPTIONS[name])
        self._preview_sfx.setSource(QUrl.fromLocalFile(filepath))
        self._preview_sfx.setVolume(self._volume / 100.0)
        self._preview_sfx.play()

    # ── Internal ──────────────────────────────────────────────

    def _should_play(self) -> bool:
        return self._enabled and not self._muted and self._volume > 0

    def _load_notification_sound(self) -> None:
        """(Re)load interval & over-time sources from the selected sound file."""
        filepath = os.path.join(SOUNDS_DIR, SOUND_OPTIONS[self._notification_sound])
        url = QUrl.fromLocalFile(filepath)
        self._interval_sfx.setSource(url)
        self._over_time_sfx.setSource(url)

    def _update_volumes(self) -> None:
        # QSoundEffect expects a volume between 0.0 and 1.0
        v = self._volume / 100.0
        self._interval_sfx.setVolume(v)
        self._over_time_sfx.setVolume(v)
        self._completion_sfx.setVolume(v)
        self._preview_sfx.setVolume(v)
