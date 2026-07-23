"""
GRE Pace Trainer — Question Tracker Widget

The main UI for the Question Time Tracker mode. Provides configuration,
a live dashboard with real-time pacing feedback, a scrollable question
log, and keyboard-driven workflow (Space → Next, Escape → End).
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.tracker_engine import TrackerEngine
from src.session_storage import SessionStorage
from src.sound_manager import SoundManager
from src.ui.tracker_report import TrackerReportDialog


def _fmt_timer(ms: int) -> str:
    """Format ms as MM:SS for the live countdown."""
    total_s = max(0, ms) // 1000
    m, s = divmod(total_s, 60)
    return f"{m:02d}:{s:02d}"


def _fmt_short(ms: int) -> str:
    """Format ms as Xm Ys or Xs."""
    total_s = max(0, ms) / 1000
    m, s = divmod(int(total_s), 60)
    if m > 0:
        return f"{m}m {s:02d}s"
    return f"{s}s"


class TrackerWidget(QWidget):
    """Question Time Tracker tab content."""

    # Emitted so MainWindow can play sounds
    play_beep = Signal()
    play_completion = Signal()
    show_notification = Signal(str, str)  # title, message

    def __init__(self, sound: SoundManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sound = sound
        self._engine = TrackerEngine(self)
        self._storage = SessionStorage()

        self._build_ui()
        self._connect_signals()

    # ══════════════════════════════════════════════════════════
    # UI BUILD
    # ══════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 20)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────
        title = QLabel("Question Time Tracker")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        subtitle = QLabel("Track Your Actual Pacing Per Question")
        subtitle.setObjectName("appSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        root.addWidget(subtitle)
        root.addSpacing(18)

        # ── CONFIG SECTION (visible when idle) ────────
        self._config_section = QWidget()
        cs = QVBoxLayout(self._config_section)
        cs.setContentsMargins(0, 0, 0, 0)
        cs.setSpacing(0)

        # Presets
        presets_label = QLabel("PRESETS")
        presets_label.setObjectName("sectionTitle")
        cs.addWidget(presets_label)
        cs.addSpacing(8)

        presets_row = QHBoxLayout()
        presets_row.setSpacing(8)

        for name, obj, mins, secs in [
            ("Quant\n1m 45s", "presetQuant", 1, 45),
            ("Verbal\n1m 30s", "presetVerbal", 1, 30),
            ("RC\n4m 00s", "presetRC", 4, 0),
        ]:
            btn = QPushButton(name)
            btn.setObjectName(obj)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, m=mins, s=secs: self._apply_preset(m, s))
            presets_row.addWidget(btn)

        cs.addLayout(presets_row)
        cs.addSpacing(18)

        # Target time config
        cfg_label = QLabel("TARGET TIME PER QUESTION")
        cfg_label.setObjectName("sectionTitle")
        cs.addWidget(cfg_label)
        cs.addSpacing(8)

        time_row = QHBoxLayout()
        time_row.setSpacing(10)

        self._spin_min = QSpinBox()
        self._spin_min.setRange(0, 60)
        self._spin_min.setSuffix(" min")
        self._spin_min.setValue(1)

        self._spin_sec = QSpinBox()
        self._spin_sec.setRange(0, 59)
        self._spin_sec.setSuffix(" sec")
        self._spin_sec.setValue(45)

        time_row.addWidget(self._spin_min, 1)
        time_row.addWidget(self._spin_sec, 1)
        cs.addLayout(time_row)

        cs.addSpacing(20)

        # Start button
        self._btn_start = QPushButton("Start Session")
        self._btn_start.setCursor(Qt.PointingHandCursor)
        self._btn_start.setFocusPolicy(Qt.NoFocus)
        self._btn_start.clicked.connect(self._start_session)
        cs.addWidget(self._btn_start)

        root.addWidget(self._config_section)

        # ── LIVE DASHBOARD (visible when running) ─────
        self._dashboard = QWidget()
        ds = QVBoxLayout(self._dashboard)
        ds.setContentsMargins(0, 0, 0, 0)
        ds.setSpacing(0)

        # Current question label
        self._lbl_question_num = QLabel("Question 1")
        self._lbl_question_num.setAlignment(Qt.AlignCenter)
        self._lbl_question_num.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #8888a0;"
        )
        ds.addWidget(self._lbl_question_num)
        ds.addSpacing(4)

        # Big timer
        self._lbl_timer = QLabel("00:00")
        self._lbl_timer.setObjectName("timerDisplay")
        self._lbl_timer.setAlignment(Qt.AlignCenter)
        ds.addWidget(self._lbl_timer)
        ds.addSpacing(4)

        # Pace indicator
        self._lbl_pace = QLabel("● On Pace")
        self._lbl_pace.setAlignment(Qt.AlignCenter)
        self._lbl_pace.setStyleSheet(
            "font-size: 13px; font-weight: 700; color: #4ade80;"
        )
        ds.addWidget(self._lbl_pace)
        ds.addSpacing(16)

        # Stats row
        stats_card = QFrame()
        stats_card.setObjectName("card")
        stats_grid = QHBoxLayout(stats_card)
        stats_grid.setContentsMargins(16, 12, 16, 12)
        stats_grid.setSpacing(0)

        # Completed
        col1 = QVBoxLayout()
        col1.setSpacing(2)
        col1.setAlignment(Qt.AlignCenter)
        lbl = QLabel("COMPLETED")
        lbl.setObjectName("statLabel")
        lbl.setAlignment(Qt.AlignCenter)
        self._lbl_completed = QLabel("0")
        self._lbl_completed.setObjectName("statValue")
        self._lbl_completed.setAlignment(Qt.AlignCenter)
        col1.addWidget(lbl)
        col1.addWidget(self._lbl_completed)
        stats_grid.addLayout(col1)

        # Avg Time
        col2 = QVBoxLayout()
        col2.setSpacing(2)
        col2.setAlignment(Qt.AlignCenter)
        lbl2 = QLabel("AVG TIME")
        lbl2.setObjectName("statLabel")
        lbl2.setAlignment(Qt.AlignCenter)
        self._lbl_avg = QLabel("--")
        self._lbl_avg.setObjectName("statValue")
        self._lbl_avg.setAlignment(Qt.AlignCenter)
        col2.addWidget(lbl2)
        col2.addWidget(self._lbl_avg)
        stats_grid.addLayout(col2)

        # Target
        col3 = QVBoxLayout()
        col3.setSpacing(2)
        col3.setAlignment(Qt.AlignCenter)
        lbl3 = QLabel("TARGET")
        lbl3.setObjectName("statLabel")
        lbl3.setAlignment(Qt.AlignCenter)
        self._lbl_target = QLabel("--")
        self._lbl_target.setObjectName("statValue")
        self._lbl_target.setAlignment(Qt.AlignCenter)
        col3.addWidget(lbl3)
        col3.addWidget(self._lbl_target)
        stats_grid.addLayout(col3)

        ds.addWidget(stats_card)
        ds.addSpacing(14)

        # Keyboard hints
        hints_frame = QFrame()
        hints_layout = QHBoxLayout(hints_frame)
        hints_layout.setContentsMargins(0, 0, 0, 0)
        hints_layout.setSpacing(16)

        for key, action in [("SPACE", "Next Question"), ("ESC", "End Session")]:
            h = QHBoxLayout()
            h.setSpacing(6)
            kbd = QLabel(key)
            kbd.setStyleSheet(
                "background: #3a3a50; color: #e0e0e8; padding: 3px 10px;"
                "border-radius: 4px; font-size: 11px; font-weight: 700;"
                "font-family: 'Cascadia Mono', 'Consolas', monospace;"
            )
            kbd.setAlignment(Qt.AlignCenter)
            act = QLabel(action)
            act.setStyleSheet("font-size: 11px; color: #5c5c78;")
            h.addWidget(kbd)
            h.addWidget(act)
            hints_layout.addLayout(h)

        hints_layout.addStretch()
        ds.addWidget(hints_frame)
        ds.addSpacing(12)

        # Question log header
        log_header_lbl = QLabel("QUESTION LOG")
        log_header_lbl.setObjectName("sectionTitle")
        ds.addWidget(log_header_lbl)
        ds.addSpacing(6)

        # Scrollable question log
        self._log_scroll = QScrollArea()
        self._log_scroll.setWidgetResizable(True)
        self._log_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._log_scroll.setStyleSheet(
            "QScrollArea { border: 1px solid #3a3a50; border-radius: 6px;"
            " background: #252538; }"
        )
        self._log_scroll.setMinimumHeight(120)
        self._log_scroll.setMaximumHeight(200)

        self._log_container = QWidget()
        self._log_layout = QVBoxLayout(self._log_container)
        self._log_layout.setContentsMargins(10, 8, 10, 8)
        self._log_layout.setSpacing(4)
        self._log_layout.addStretch()
        self._log_scroll.setWidget(self._log_container)

        ds.addWidget(self._log_scroll)
        ds.addSpacing(16)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._btn_next = QPushButton("Next Question  (Space)")
        self._btn_next.setCursor(Qt.PointingHandCursor)
        self._btn_next.setFocusPolicy(Qt.NoFocus)
        self._btn_next.clicked.connect(self._next_question)
        btn_row.addWidget(self._btn_next, 2)

        self._btn_end = QPushButton("End Session")
        self._btn_end.setObjectName("resetBtn")
        self._btn_end.setCursor(Qt.PointingHandCursor)
        self._btn_end.setFocusPolicy(Qt.NoFocus)
        self._btn_end.clicked.connect(self._end_session)
        btn_row.addWidget(self._btn_end, 1)

        ds.addLayout(btn_row)

        self._dashboard.setVisible(False)
        root.addWidget(self._dashboard)

        root.addStretch()

    # ══════════════════════════════════════════════════════════
    # SIGNAL CONNECTIONS
    # ══════════════════════════════════════════════════════════

    def _connect_signals(self) -> None:
        self._engine.tick.connect(self._on_tick)
        self._engine.question_recorded.connect(self._on_question_recorded)
        self._engine.session_ended.connect(self._on_session_ended)
        self._engine.over_time.connect(self._on_over_time)

    def _on_over_time(self) -> None:
        self._sound.play_over_time_beep()

    # ══════════════════════════════════════════════════════════
    # ACTIONS
    # ══════════════════════════════════════════════════════════

    def _start_session(self) -> None:
        total_sec = self._spin_min.value() * 60 + self._spin_sec.value()
        if total_sec <= 0:
            return

        target_ms = total_sec * 1000

        # Clear old log entries
        while self._log_layout.count() > 1:
            item = self._log_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Update UI
        self._lbl_target.setText(_fmt_short(target_ms))
        self._lbl_completed.setText("0")
        self._lbl_avg.setText("--")
        self._lbl_timer.setText("00:00")
        self._lbl_timer.setStyleSheet("")
        self._lbl_question_num.setText("Question 1")
        self._lbl_pace.setText("● On Pace")
        self._lbl_pace.setStyleSheet(
            "font-size: 13px; font-weight: 700; color: #4ade80;"
        )

        self._config_section.setVisible(False)
        self._dashboard.setVisible(True)

        self._engine.start_session(target_ms)

    def _next_question(self) -> None:
        if self._engine.state != "running":
            return
        self._engine.next_question()

    def _end_session(self) -> None:
        if self._engine.state != "running":
            return
        self._engine.end_session()

    def _apply_preset(self, mins: int, secs: int) -> None:
        self._spin_min.setValue(mins)
        self._spin_sec.setValue(secs)

    # ══════════════════════════════════════════════════════════
    # KEY HANDLING (called by MainWindow)
    # ══════════════════════════════════════════════════════════

    def handle_space(self) -> bool:
        """Handle Space key. Returns True if consumed."""
        if self._engine.state == "running":
            self._next_question()
            return True
        return False

    def handle_escape(self) -> bool:
        """Handle Escape key. Returns True if consumed."""
        if self._engine.state == "running":
            self._end_session()
            return True
        return False

    # ══════════════════════════════════════════════════════════
    # ENGINE CALLBACKS
    # ══════════════════════════════════════════════════════════

    def _on_tick(self, elapsed_ms: int) -> None:
        """Update the live timer display and pace indicator."""
        self._lbl_timer.setText(_fmt_timer(elapsed_ms))

        target = self._engine.target_ms
        if target <= 0:
            return

        ratio = elapsed_ms / target

        # Color the timer based on how close to target
        if ratio < 0.80:
            color = "#e0e0e8"  # Default — plenty of time
            pace_text = "● On Pace"
            pace_color = "#4ade80"
        elif ratio < 1.0:
            color = "#fbbf24"  # Warning — approaching target
            pace_text = "● Approaching Target"
            pace_color = "#fbbf24"
        elif ratio < 1.20:
            color = "#fb923c"  # Over target but within tolerance
            pace_text = "⚠ Over Target"
            pace_color = "#fb923c"
        else:
            color = "#f87171"  # Significantly over
            pace_text = "✗ Behind Pace"
            pace_color = "#f87171"

        self._lbl_timer.setStyleSheet(
            f"font-size: 42px; font-weight: 700; color: {color};"
            f" font-family: 'Cascadia Mono', 'Consolas', monospace;"
        )
        self._lbl_pace.setText(pace_text)
        self._lbl_pace.setStyleSheet(
            f"font-size: 13px; font-weight: 700; color: {pace_color};"
        )

    def _on_question_recorded(self, q_num: int, time_ms: int) -> None:
        """Add a completed question to the log and update stats."""
        self._sound.play_interval_beep()

        target = self._engine.target_ms
        diff_ms = time_ms - target

        # Pace classification
        ratio = time_ms / target if target > 0 else 1.0
        if ratio < 0.80:
            pace_text = "✓ Fast"
            pace_color = "#4ade80"
        elif ratio <= 1.20:
            pace_text = "● On Target"
            pace_color = "#ffffff"
        else:
            pace_text = "✗ Slow"
            pace_color = "#f87171"

        # Diff formatting
        sign = "+" if diff_ms >= 0 else "−"
        abs_s = abs(diff_ms) / 1000
        dm, ds = divmod(int(abs_s), 60)
        diff_str = f"{sign}{dm}m {ds:02d}s" if dm > 0 else f"{sign}{ds}s"
        diff_color = "#4ade80" if diff_ms <= 0 else "#f87171"

        # Build log row
        row = QHBoxLayout()
        row.setSpacing(0)

        num_lbl = QLabel(f"Q{q_num}")
        num_lbl.setFixedWidth(40)
        num_lbl.setStyleSheet("font-size: 12px; color: #8888a0; font-weight: 600;")

        time_lbl = QLabel(_fmt_short(time_ms))
        time_lbl.setFixedWidth(72)
        time_lbl.setStyleSheet("font-size: 12px; color: #e0e0e8; font-weight: 600;")

        diff_lbl = QLabel(diff_str)
        diff_lbl.setFixedWidth(72)
        diff_lbl.setStyleSheet(
            f"font-size: 12px; color: {diff_color}; font-weight: 500;"
        )

        pace_lbl = QLabel(pace_text)
        pace_lbl.setStyleSheet(
            f"font-size: 12px; color: {pace_color}; font-weight: 600;"
        )

        row.addWidget(num_lbl)
        row.addWidget(time_lbl)
        row.addWidget(diff_lbl)
        row.addWidget(pace_lbl)
        row.addStretch()

        row_widget = QWidget()
        row_widget.setLayout(row)

        # Insert before the stretch at the end
        self._log_layout.insertWidget(self._log_layout.count() - 1, row_widget)

        # Auto-scroll to bottom
        self._log_scroll.verticalScrollBar().setValue(
            self._log_scroll.verticalScrollBar().maximum()
        )

        # Update dashboard stats
        completed = self._engine.completed_count
        self._lbl_completed.setText(str(completed))
        avg = self._engine.get_live_average_ms()
        self._lbl_avg.setText(_fmt_short(avg))

        # Update question number
        self._lbl_question_num.setText(f"Question {self._engine.current_question}")
        self._lbl_timer.setText("00:00")
        self._lbl_timer.setStyleSheet("")

        # Notification
        self.show_notification.emit(
            "Question Recorded",
            f"Q{q_num}: {_fmt_short(time_ms)} ({pace_text})",
        )

    def _on_session_ended(self) -> None:
        """Show the analytics report and return to config view."""
        self._sound.play_completion_beep()

        stats = self._engine.get_stats()

        # Persist session
        self._storage.save_session(self._storage.session_to_dict(stats))

        self.show_notification.emit(
            "Tracker Session Complete",
            f"{stats.total_questions} questions · Avg {_fmt_short(stats.average_ms)}",
        )

        # Show report
        if stats.total_questions > 0:
            report = TrackerReportDialog(self.window(), stats)
            report.exec()

        # Return to config
        self._engine.reset()
        self._dashboard.setVisible(False)
        self._config_section.setVisible(True)
