"""
GRE Pace Trainer — Question Tracker Engine

Tracks the actual time spent per question using perf_counter timestamps.
Produces per-question timing data and real-time analytics.
"""

import time
import statistics
from datetime import datetime
from dataclasses import dataclass, field
from PySide6.QtCore import QObject, QTimer, Qt, Signal


@dataclass
class QuestionRecord:
    """A single recorded question timing."""
    number: int
    time_ms: int
    target_ms: int
    timestamp: str = ""      # ISO format timestamp when question was completed
    status: str = "completed" # 'completed' or 'skipped'

    @property
    def diff_ms(self) -> int:
        return self.time_ms - self.target_ms

    @property
    def pace(self) -> str:
        ratio = self.time_ms / self.target_ms if self.target_ms > 0 else 1.0
        if ratio < 0.80:
            return "fast"
        elif ratio <= 1.20:
            return "on_target"
        else:
            return "slow"


@dataclass
class SessionStats:
    """Aggregate analytics for a completed or in-progress session."""
    total_questions: int = 0
    total_time_ms: int = 0
    target_time_ms: int = 0
    average_ms: int = 0
    median_ms: int = 0
    fastest_ms: int = 0
    fastest_q: int = 0
    slowest_ms: int = 0
    slowest_q: int = 0
    on_target_count: int = 0
    fast_count: int = 0
    slow_count: int = 0
    on_target_pct: float = 0.0
    questions: list = field(default_factory=list)


class TrackerEngine(QObject):
    """Tracks per-question timing with timestamp precision."""

    # Signals
    tick = Signal(int)                      # current question elapsed_ms
    question_recorded = Signal(int, int)    # question_number, time_ms
    session_ended = Signal()
    stats_updated = Signal()
    over_time = Signal()

    POLL_MS = 50

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

        self._target_ms: int = 0
        self._state: str = "idle"  # idle | running | finished
        self._current_question: int = 0
        self._question_start: float = 0.0
        self._records: list[QuestionRecord] = []
        self._beeped_for_current: bool = False

        self._poll_timer = QTimer(self)
        self._poll_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._poll_timer.setInterval(self.POLL_MS)
        self._poll_timer.timeout.connect(self._on_poll)

    # ── Properties ────────────────────────────────────────

    @property
    def state(self) -> str:
        return self._state

    @property
    def current_question(self) -> int:
        return self._current_question

    @property
    def completed_count(self) -> int:
        return len(self._records)

    @property
    def records(self) -> list[QuestionRecord]:
        return list(self._records)

    @property
    def target_ms(self) -> int:
        return self._target_ms

    # ── Public API ────────────────────────────────────────

    def start_session(self, target_ms: int) -> None:
        """Begin a new tracking session."""
        self._target_ms = target_ms
        self._records.clear()
        self._current_question = 1
        self._question_start = time.perf_counter()
        self._state = "running"
        self._beeped_for_current = False
        self._poll_timer.start()
        self.stats_updated.emit()

    def next_question(self) -> None:
        """Record current question time and advance to the next."""
        if self._state != "running":
            return

        elapsed_ms = int((time.perf_counter() - self._question_start) * 1000)
        record = QuestionRecord(
            number=self._current_question,
            time_ms=elapsed_ms,
            target_ms=self._target_ms,
            timestamp=datetime.now().isoformat(),
            status="completed",
        )
        self._records.append(record)
        self.question_recorded.emit(self._current_question, elapsed_ms)

        self._current_question += 1
        self._question_start = time.perf_counter()
        self._beeped_for_current = False
        self.stats_updated.emit()

    def end_session(self) -> None:
        """End the session. Records the current question if any time elapsed."""
        if self._state != "running":
            return

        # Record the in-progress question if user spent any time on it
        elapsed_ms = int((time.perf_counter() - self._question_start) * 1000)
        if elapsed_ms > 500:  # Only record if at least 0.5s spent
            record = QuestionRecord(
                number=self._current_question,
                time_ms=elapsed_ms,
                target_ms=self._target_ms,
                timestamp=datetime.now().isoformat(),
                status="completed",
            )
            self._records.append(record)

        self._poll_timer.stop()
        self._state = "finished"
        self.stats_updated.emit()
        self.session_ended.emit()

    def reset(self) -> None:
        """Clear all data and return to idle."""
        self._poll_timer.stop()
        self._records.clear()
        self._current_question = 0
        self._state = "idle"

    def get_current_elapsed_ms(self) -> int:
        """Elapsed time on the current question."""
        if self._state != "running":
            return 0
        return int((time.perf_counter() - self._question_start) * 1000)

    def get_stats(self) -> SessionStats:
        """Compute aggregate session analytics."""
        stats = SessionStats()
        if not self._records:
            stats.target_time_ms = self._target_ms
            return stats

        times = [r.time_ms for r in self._records]
        stats.total_questions = len(self._records)
        stats.total_time_ms = sum(times)
        stats.target_time_ms = self._target_ms
        stats.average_ms = int(statistics.mean(times))
        stats.median_ms = int(statistics.median(times))

        fastest_idx = times.index(min(times))
        slowest_idx = times.index(max(times))
        stats.fastest_ms = times[fastest_idx]
        stats.fastest_q = self._records[fastest_idx].number
        stats.slowest_ms = times[slowest_idx]
        stats.slowest_q = self._records[slowest_idx].number

        stats.fast_count = sum(1 for r in self._records if r.pace == "fast")
        stats.on_target_count = sum(1 for r in self._records if r.pace == "on_target")
        stats.slow_count = sum(1 for r in self._records if r.pace == "slow")
        stats.on_target_pct = (
            (stats.fast_count + stats.on_target_count) / stats.total_questions * 100
        )
        stats.questions = list(self._records)
        return stats

    def get_live_average_ms(self) -> int:
        """Average time of completed questions."""
        if not self._records:
            return 0
        return int(statistics.mean(r.time_ms for r in self._records))

    # ── Internal ──────────────────────────────────────────

    def _on_poll(self) -> None:
        elapsed = int((time.perf_counter() - self._question_start) * 1000)
        self.tick.emit(elapsed)
        
        if not self._beeped_for_current and elapsed >= self._target_ms > 0:
            self._beeped_for_current = True
            self.over_time.emit()
