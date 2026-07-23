"""
GRE Pace Trainer — Timestamp-based Timer Engine

Uses time.perf_counter() for drift-free timing. A QTimer polls at 50ms
intervals and derives elapsed time from wall-clock deltas, ensuring the
timer stays accurate across long sessions, window minimisation, and
pause/resume cycles.
"""

import time
from PySide6.QtCore import QObject, QTimer, Qt, Signal


class TimerEngine(QObject):
    """Core timing engine for the GRE Pace Trainer."""

    # Signals
    tick = Signal(int)                # remaining_ms for current interval
    interval_completed = Signal(int)  # completed question count
    session_completed = Signal()
    state_changed = Signal(str)       # 'idle' | 'running' | 'paused' | 'completed'

    POLL_INTERVAL_MS = 50

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

        # Configuration
        self._interval_duration_ms: int = 0
        self._total_questions: int = 0

        # Runtime state
        self._state: str = "idle"
        self._completed_questions: int = 0

        # Timestamp tracking
        self._start_timestamp: float = 0.0
        self._pause_timestamp: float = 0.0
        self._accumulated_pause_ms: float = 0.0

        # Poll timer
        self._poll_timer = QTimer(self)
        self._poll_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._poll_timer.setInterval(self.POLL_INTERVAL_MS)
        self._poll_timer.timeout.connect(self._on_poll)

    # ── Properties ────────────────────────────────────────────

    @property
    def state(self) -> str:
        return self._state

    @property
    def completed_questions(self) -> int:
        return self._completed_questions

    @property
    def total_questions(self) -> int:
        return self._total_questions

    @property
    def interval_duration_ms(self) -> int:
        return self._interval_duration_ms

    @property
    def session_total_ms(self) -> int:
        return self._interval_duration_ms * self._total_questions

    # ── Public Methods ────────────────────────────────────────

    def configure(self, interval_ms: int, total_questions: int) -> None:
        """Set up a new session. Must be called before start()."""
        self._interval_duration_ms = interval_ms
        self._total_questions = total_questions
        self._completed_questions = 0
        self._accumulated_pause_ms = 0.0
        self._set_state("idle")

    def start(self) -> None:
        """Begin the session."""
        if self._state != "idle":
            return
        self._start_timestamp = time.perf_counter()
        self._accumulated_pause_ms = 0.0
        self._completed_questions = 0
        self._poll_timer.start()
        self._set_state("running")

    def pause(self) -> None:
        """Pause the session, preserving exact position."""
        if self._state != "running":
            return
        self._pause_timestamp = time.perf_counter()
        self._poll_timer.stop()
        self._set_state("paused")

    def resume(self) -> None:
        """Resume from the exact paused position."""
        if self._state != "paused":
            return
        pause_duration = (time.perf_counter() - self._pause_timestamp) * 1000.0
        self._accumulated_pause_ms += pause_duration
        self._poll_timer.start()
        self._set_state("running")

    def reset(self) -> None:
        """Stop and restore to initial idle state."""
        self._poll_timer.stop()
        self._completed_questions = 0
        self._accumulated_pause_ms = 0.0
        self._set_state("idle")

    def get_elapsed_ms(self) -> int:
        """Total net elapsed time (excluding pauses)."""
        if self._state == "idle":
            return 0
        if self._state == "completed":
            return self.session_total_ms
        return int(self._net_elapsed_ms())

    def get_remaining_session_ms(self) -> int:
        """Time remaining until session end."""
        return max(0, self.session_total_ms - self.get_elapsed_ms())

    def get_current_interval_remaining_ms(self) -> int:
        """Time remaining in the current question interval."""
        if self._state in ("idle", "completed"):
            return self._interval_duration_ms if self._state == "idle" else 0
        net = self._net_elapsed_ms()
        elapsed_in_interval = net % self._interval_duration_ms
        return max(0, int(self._interval_duration_ms - elapsed_in_interval))

    # ── Internal ──────────────────────────────────────────────

    def _net_elapsed_ms(self) -> float:
        """Calculate net elapsed time in ms, excluding pauses."""
        if self._state == "paused":
            raw = (self._pause_timestamp - self._start_timestamp) * 1000.0
        else:
            raw = (time.perf_counter() - self._start_timestamp) * 1000.0
        return max(0.0, raw - self._accumulated_pause_ms)

    def _on_poll(self) -> None:
        """Called every POLL_INTERVAL_MS while running."""
        if self._interval_duration_ms <= 0 or self._total_questions <= 0:
            return

        net = self._net_elapsed_ms()

        # How many intervals should be complete by now?
        intervals_done = int(net // self._interval_duration_ms)
        intervals_done = min(intervals_done, self._total_questions)

        # Emit interval_completed for each newly completed interval
        while self._completed_questions < intervals_done:
            self._completed_questions += 1
            self.interval_completed.emit(self._completed_questions)

        # Check for session completion
        if self._completed_questions >= self._total_questions:
            self._poll_timer.stop()
            self._set_state("completed")
            self.session_completed.emit()
            return

        # Emit tick with remaining ms in current interval
        elapsed_in_interval = net - (self._completed_questions * self._interval_duration_ms)
        remaining = max(0, int(self._interval_duration_ms - elapsed_in_interval))
        self.tick.emit(remaining)

    def _set_state(self, new_state: str) -> None:
        """Update state and emit signal."""
        if self._state != new_state:
            self._state = new_state
            self.state_changed.emit(new_state)
