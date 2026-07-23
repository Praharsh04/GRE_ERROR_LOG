"""
GRE Pace Trainer — Main Window

Central hub with two tabs:
  1. Pace Trainer — interval-based pacing alerts
  2. Question Tracker — per-question timing analytics

Wires together the timer engine, tracker engine, sound manager,
settings persistence, and tray integration.
"""

from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.settings_manager import SettingsManager
from src.sound_manager import SoundManager
from src.timer_engine import TimerEngine
from src.ui.styles import get_stylesheet
from src.ui.summary_dialog import SummaryDialog
from src.ui.tracker_widget import TrackerWidget
from src.ui.tray_manager import TrayManager
from src.ui.focus_popup import FocusPopup


def _create_app_icon() -> QIcon:
    """Generate the window icon: purple circle with white 'P'."""
    size = 64
    pix = QPixmap(size, size)
    pix.fill(QColor(0, 0, 0, 0))
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor("#2d2d2d"))
    p.setPen(Qt.NoPen)
    p.drawEllipse(2, 2, size - 4, size - 4)
    p.setPen(QColor("#ffffff"))
    f = QFont("Segoe UI", 26, QFont.Bold)
    p.setFont(f)
    p.drawText(pix.rect(), Qt.AlignCenter, "P")
    p.end()
    return QIcon(pix)


class MainWindow(QMainWindow):
    """GRE Pace Trainer main application window."""

    def __init__(self) -> None:
        super().__init__()

        # ── Core services ─────────────────────────────────
        self._timer = TimerEngine(self)
        self._sound = SoundManager()
        self._settings = SettingsManager()
        self._closing_for_real = False

        # ── Window setup ──────────────────────────────────
        self.setWindowTitle("GRE Pace Trainer")
        self.setWindowIcon(_create_app_icon())
        self.setFixedWidth(420)
        self.setMinimumHeight(580)
        self.setStyleSheet(get_stylesheet())

        # ── Build UI ──────────────────────────────────────
        self._build_ui()

        # ── Tray ──────────────────────────────────────────
        self._tray = TrayManager(self)
        self._tray.show()
        self._tray.restore_requested.connect(self._restore_from_tray)
        self._tray.start_pause_requested.connect(self._on_start_pause)
        self._tray.reset_requested.connect(self._on_reset)
        self._tray.exit_requested.connect(self._do_exit)

        # ── Timer connections ─────────────────────────────
        self._timer.tick.connect(self._on_tick)
        self._timer.interval_completed.connect(self._on_interval_completed)
        self._timer.session_completed.connect(self._on_session_completed)
        self._timer.state_changed.connect(self._on_state_changed)

        # ── Focus Popup ───────────────────────────────────
        self._popup = FocusPopup()
        self._popup.request_play.connect(self._on_popup_play)
        self._popup.request_pause.connect(self._on_popup_pause)
        self._popup.request_reset.connect(self._on_popup_reset)
        self._popup.request_close.connect(self._on_popup_close)

        # ── Tracker notifications ─────────────────────────
        self._tracker.show_notification.connect(self._show_notification)

        # ── Elapsed time updater ──────────────────────────
        self._display_timer = QTimer(self)
        self._display_timer.setInterval(200)
        self._display_timer.timeout.connect(self._update_elapsed_display)

        # ── Global key event filter ───────────────────────
        # Install event filter on the application to capture key presses
        # even when child widgets (SpinBox, buttons, etc.) have focus.
        QApplication.instance().installEventFilter(self)

        # ── Load settings ─────────────────────────────────
        self._load_settings()

    # ══════════════════════════════════════════════════════════
    # UI CONSTRUCTION
    # ══════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Tab widget ────────────────────────────────────
        self._tabs = QTabWidget()
        self._tabs.setObjectName("mainTabs")

        # Tab 1: Pace Trainer
        pace_tab = self._build_pace_tab()
        self._tabs.addTab(pace_tab, "⏱  Pace Trainer")

        # Tab 2: Question Tracker
        self._tracker = TrackerWidget(self._sound, self)
        self._tabs.addTab(self._tracker, "📊  Question Tracker")

        root.addWidget(self._tabs)

        # ── Options bar (shared across tabs) ──────────────
        options_widget = QWidget()
        options_widget.setStyleSheet("background: #1a1a2a;")
        opts = QVBoxLayout(options_widget)
        opts.setContentsMargins(20, 10, 20, 10)
        opts.setSpacing(6)

        row1 = QHBoxLayout()
        row1.setSpacing(10)
        self._chk_on_top = QCheckBox("Always On Top")
        self._chk_on_top.setChecked(True)
        self._chk_on_top.toggled.connect(self._toggle_always_on_top)
        row1.addWidget(self._chk_on_top)

        self._chk_sound = QCheckBox("Sound Alerts")
        self._chk_sound.setChecked(True)
        self._chk_sound.toggled.connect(self._sound.set_enabled)
        row1.addWidget(self._chk_sound)

        self._chk_notifications = QCheckBox("Desktop Alerts")
        self._chk_notifications.setChecked(True)
        row1.addWidget(self._chk_notifications)
        opts.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(10)
        self._btn_popup = QPushButton("🕒 Pop-Out Timer")
        self._btn_popup.setObjectName("resetBtn")
        self._btn_popup.setCursor(Qt.PointingHandCursor)
        self._btn_popup.clicked.connect(self._toggle_popup)
        row2.addWidget(self._btn_popup)

        vol_label = QLabel("Vol")
        vol_label.setObjectName("volumeLabel")
        row2.addWidget(vol_label)

        self._slider_volume = QSlider(Qt.Horizontal)
        self._slider_volume.setRange(0, 100)
        self._slider_volume.setValue(80)
        self._slider_volume.valueChanged.connect(self._sound.set_volume)
        row2.addWidget(self._slider_volume, 1)

        self._lbl_volume = QLabel("80")
        self._lbl_volume.setObjectName("volumeLabel")
        self._lbl_volume.setFixedWidth(24)
        self._slider_volume.valueChanged.connect(
            lambda v: self._lbl_volume.setText(str(v))
        )
        row2.addWidget(self._lbl_volume)
        opts.addLayout(row2)

        # ── Sound Settings Row ─────────────────────────
        row3 = QHBoxLayout()
        row3.setSpacing(8)

        sound_label = QLabel("Alert Sound")
        sound_label.setObjectName("volumeLabel")
        row3.addWidget(sound_label)

        self._combo_sound = QComboBox()
        self._combo_sound.setStyleSheet(
            """
            QComboBox {
                background: #1e1e1e; color: #e0e0e0; border: 1px solid #333;
                border-radius: 6px; padding: 5px 10px; font-size: 12px;
                min-width: 120px;
            }
            QComboBox:hover { border-color: #fff; }
            QComboBox::drop-down {
                border: none; width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #aaa;
                width: 0; height: 0;
            }
            QComboBox QAbstractItemView {
                background: #1e1e1e; color: #e0e0e0;
                border: 1px solid #333; selection-background-color: #2d2d2d;
            }
            """
        )
        for name in self._sound.get_sound_names():
            self._combo_sound.addItem(name)
        self._combo_sound.currentTextChanged.connect(self._on_sound_changed)
        row3.addWidget(self._combo_sound, 1)

        self._btn_preview = QPushButton("▶")
        self._btn_preview.setToolTip("Preview sound")
        self._btn_preview.setFixedSize(30, 30)
        self._btn_preview.setCursor(Qt.PointingHandCursor)
        self._btn_preview.setStyleSheet(
            "QPushButton { background: #222; border: 1px solid #444; border-radius: 6px;"
            " color: #fff; font-size: 12px; padding: 0; }"
            "QPushButton:hover { background: #3b82f6; border-color: #3b82f6; }"
        )
        self._btn_preview.clicked.connect(self._preview_sound)
        row3.addWidget(self._btn_preview)

        self._chk_mute = QCheckBox("Mute")
        self._chk_mute.toggled.connect(self._sound.set_muted)
        row3.addWidget(self._chk_mute)

        opts.addLayout(row3)

        root.addWidget(options_widget)

    def _build_pace_tab(self) -> QWidget:
        """Build the Pace Trainer tab content."""
        tab = QWidget()
        root = QVBoxLayout(tab)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sticky Top Section ────────────────────────
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(24, 20, 24, 10)
        top_layout.setSpacing(0)

        title = QLabel("GRE Pace Trainer")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignCenter)
        top_layout.addWidget(title)

        subtitle = QLabel("Develop Your Question Pacing")
        subtitle.setObjectName("appSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        top_layout.addWidget(subtitle)
        
        # Timer display section (hidden when idle)
        self._timer_section = QWidget()
        ts = QVBoxLayout(self._timer_section)
        ts.setContentsMargins(0, 16, 0, 0)
        ts.setSpacing(0)

        alert_label = QLabel("NEXT ALERT IN")
        alert_label.setObjectName("sectionTitle")
        alert_label.setAlignment(Qt.AlignCenter)
        ts.addWidget(alert_label)
        ts.addSpacing(4)

        self._lbl_countdown = QLabel("00:00")
        self._lbl_countdown.setObjectName("timerDisplay")
        self._lbl_countdown.setAlignment(Qt.AlignCenter)
        ts.addWidget(self._lbl_countdown)
        ts.addSpacing(16)

        prog_label = QLabel("PROGRESS")
        prog_label.setObjectName("sectionTitle")
        ts.addWidget(prog_label)
        ts.addSpacing(6)

        prog_row = QHBoxLayout()
        self._lbl_progress = QLabel("0 / 0")
        self._lbl_progress.setObjectName("progressFraction")
        self._lbl_percent = QLabel("0%")
        self._lbl_percent.setObjectName("progressPercent")
        self._lbl_percent.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        prog_row.addWidget(self._lbl_progress)
        prog_row.addStretch()
        prog_row.addWidget(self._lbl_percent)
        ts.addLayout(prog_row)
        ts.addSpacing(6)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        ts.addWidget(self._progress_bar)
        ts.addSpacing(14)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        elapsed_col = QVBoxLayout()
        elapsed_col.setSpacing(2)
        el_label = QLabel("ELAPSED")
        el_label.setObjectName("statLabel")
        self._lbl_elapsed = QLabel("00:00")
        self._lbl_elapsed.setObjectName("statValue")
        elapsed_col.addWidget(el_label)
        elapsed_col.addWidget(self._lbl_elapsed)
        stats_row.addLayout(elapsed_col)
        stats_row.addStretch()

        remaining_col = QVBoxLayout()
        remaining_col.setSpacing(2)
        remaining_col.setAlignment(Qt.AlignRight)
        rem_label = QLabel("REMAINING")
        rem_label.setObjectName("statLabel")
        rem_label.setAlignment(Qt.AlignRight)
        self._lbl_remaining = QLabel("00:00")
        self._lbl_remaining.setObjectName("statValue")
        self._lbl_remaining.setAlignment(Qt.AlignRight)
        remaining_col.addWidget(rem_label)
        remaining_col.addWidget(self._lbl_remaining)
        stats_row.addLayout(remaining_col)
        ts.addLayout(stats_row)
        ts.addSpacing(16)

        divider2 = QFrame()
        divider2.setObjectName("divider")
        divider2.setFrameShape(QFrame.HLine)
        ts.addWidget(divider2)
        
        self._timer_section.setVisible(False)
        top_layout.addWidget(self._timer_section)
        
        root.addWidget(top_widget)

        # ── Scrollable Config Section ─────────────────
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        scroll_widget = QWidget()
        sw = QVBoxLayout(scroll_widget)
        sw.setContentsMargins(24, 10, 24, 10)
        sw.setSpacing(0)

        presets_label = QLabel("PRESETS")
        presets_label.setObjectName("sectionTitle")
        sw.addWidget(presets_label)
        sw.addSpacing(8)

        presets_row = QHBoxLayout()
        presets_row.setSpacing(8)

        btn_quant = QPushButton("Quant\n1m 45s · 20Q")
        btn_quant.setObjectName("presetQuant")
        btn_quant.setCursor(Qt.PointingHandCursor)
        btn_quant.clicked.connect(lambda: self._apply_preset(1, 45, 20))

        btn_verbal = QPushButton("Verbal\n1m 30s · 20Q")
        btn_verbal.setObjectName("presetVerbal")
        btn_verbal.setCursor(Qt.PointingHandCursor)
        btn_verbal.clicked.connect(lambda: self._apply_preset(1, 30, 20))

        btn_rc = QPushButton("RC\n4m 00s · 10Q")
        btn_rc.setObjectName("presetRC")
        btn_rc.setCursor(Qt.PointingHandCursor)
        btn_rc.clicked.connect(lambda: self._apply_preset(4, 0, 10))

        presets_row.addWidget(btn_quant)
        presets_row.addWidget(btn_verbal)
        presets_row.addWidget(btn_rc)
        sw.addLayout(presets_row)

        sw.addSpacing(18)

        config_label = QLabel("CONFIGURATION")
        config_label.setObjectName("sectionTitle")
        sw.addWidget(config_label)
        sw.addSpacing(10)

        time_label = QLabel("Time Per Question")
        time_label.setObjectName("inputLabel")
        sw.addWidget(time_label)
        sw.addSpacing(4)

        time_row = QHBoxLayout()
        time_row.setSpacing(10)

        self._spin_min = QSpinBox()
        self._spin_min.setRange(0, 60)
        self._spin_min.setSuffix(" min")
        self._spin_min.setValue(3)

        self._spin_sec = QSpinBox()
        self._spin_sec.setRange(0, 59)
        self._spin_sec.setSuffix(" sec")
        self._spin_sec.setValue(0)

        time_row.addWidget(self._spin_min, 1)
        time_row.addWidget(self._spin_sec, 1)
        sw.addLayout(time_row)

        sw.addSpacing(10)

        q_label = QLabel("Number of Questions")
        q_label.setObjectName("inputLabel")
        sw.addWidget(q_label)
        sw.addSpacing(4)

        self._spin_questions = QSpinBox()
        self._spin_questions.setRange(1, 200)
        self._spin_questions.setValue(20)
        sw.addWidget(self._spin_questions)

        sw.addStretch()
        scroll_area.setWidget(scroll_widget)
        root.addWidget(scroll_area, 1)

        # ── Sticky Bottom Section ─────────────────────
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(24, 10, 24, 20)
        
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._btn_start = QPushButton("Start")
        self._btn_start.setCursor(Qt.PointingHandCursor)
        self._btn_start.setFocusPolicy(Qt.NoFocus)
        self._btn_start.clicked.connect(self._on_start_pause)

        self._btn_reset = QPushButton("Reset")
        self._btn_reset.setObjectName("resetBtn")
        self._btn_reset.setCursor(Qt.PointingHandCursor)
        self._btn_reset.setFocusPolicy(Qt.NoFocus)
        self._btn_reset.clicked.connect(self._on_reset)
        self._btn_reset.setEnabled(False)

        btn_row.addWidget(self._btn_start, 2)
        btn_row.addWidget(self._btn_reset, 1)
        bottom_layout.addLayout(btn_row)
        
        root.addWidget(bottom_widget)

        return tab

    # ══════════════════════════════════════════════════════════
    # KEY HANDLING
    # ══════════════════════════════════════════════════════════

    def eventFilter(self, obj, event) -> bool:
        """Global event filter to capture key presses regardless of focus.
        
        This ensures Space/Escape work for the Question Tracker even when
        child widgets (SpinBox, buttons) hold keyboard focus.
        """
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_P and event.modifiers() == Qt.ControlModifier:
                if not event.isAutoRepeat():
                    self._toggle_popup()
                    return True

            # Only route shortcuts when the Question Tracker tab is active
            if self._tabs.currentWidget() is self._tracker:
                if event.key() == Qt.Key_Space:
                    # Ignore auto-repeat (key held down) to prevent
                    # accidental rapid-fire question advancement
                    if event.isAutoRepeat():
                        return True
                    if self._tracker.handle_space():
                        return True
                elif event.key() == Qt.Key_Escape:
                    if event.isAutoRepeat():
                        return True
                    if self._tracker.handle_escape():
                        return True

        return super().eventFilter(obj, event)

    def keyPressEvent(self, event) -> None:
        """Fallback key handler (most keys caught by eventFilter above)."""
        super().keyPressEvent(event)

    # ══════════════════════════════════════════════════════════
    # PACE TRAINER CALLBACKS
    # ══════════════════════════════════════════════════════════

    def _on_tick(self, remaining_ms: int) -> None:
        self._lbl_countdown.setText(self._format_time(remaining_ms))

    def _on_interval_completed(self, count: int) -> None:
        total = self._timer.total_questions
        self._lbl_progress.setText(f"{count} / {total}")
        pct = int((count / total) * 100) if total > 0 else 0
        self._lbl_percent.setText(f"{pct}%")
        self._progress_bar.setValue(pct)

        if count < total:
            self._sound.play_interval_beep()

        if self._chk_notifications.isChecked():
            self._tray.show_notification(
                "Interval Complete", f"Progress: {count} / {total}"
            )

    def _on_session_completed(self) -> None:
        self._display_timer.stop()
        self._sound.play_completion_beep()
        total = self._timer.total_questions
        self._lbl_progress.setText(f"{total} / {total}")
        self._lbl_percent.setText("100%")
        self._progress_bar.setValue(100)
        self._lbl_countdown.setText("00:00")
        self._lbl_remaining.setText("00:00")
        self._lbl_elapsed.setText(self._format_time(self._timer.session_total_ms))

        if self._chk_notifications.isChecked():
            self._tray.show_notification(
                "GRE Session Complete",
                f"{total} / {total} Intervals Finished",
                5000,
            )

        SummaryDialog(
            self,
            questions=total,
            interval_minutes=self._spin_min.value(),
            interval_seconds=self._spin_sec.value(),
            total_time_ms=self._timer.session_total_ms,
        ).exec()

    def _on_state_changed(self, state: str) -> None:
        is_idle = state == "idle"
        is_running = state == "running"
        is_paused = state == "paused"

        self._timer_section.setVisible(not is_idle)
        self._spin_min.setEnabled(is_idle)
        self._spin_sec.setEnabled(is_idle)
        self._spin_questions.setEnabled(is_idle)

        if is_idle:
            self._btn_start.setText("Start")
            self._tray.update_start_pause_text("Start")
        elif is_running:
            self._btn_start.setText("Pause")
            self._tray.update_start_pause_text("Pause")
        elif is_paused:
            self._btn_start.setText("Resume")
            self._tray.update_start_pause_text("Resume")
        else:
            self._btn_start.setText("Start")
            self._tray.update_start_pause_text("Start")

        self._btn_reset.setEnabled(not is_idle)

        if is_running:
            self._display_timer.start()
        else:
            self._display_timer.stop()
            
        self._update_elapsed_display()

    def _update_elapsed_display(self) -> None:
        elapsed = self._timer.get_elapsed_ms()
        remaining = self._timer.get_remaining_session_ms()
        self._lbl_elapsed.setText(self._format_time(elapsed))
        self._lbl_remaining.setText(self._format_time(remaining))
        
        if self._popup.isVisible():
            if self._tabs.currentWidget() is self._tracker:
                eng = self._tracker._engine
                self._popup.update_question_tracker(
                    elapsed_ms=eng.get_current_elapsed_ms(),
                    current_q=max(1, eng.current_question),
                    avg_ms=eng.get_live_average_ms(),
                    target_ms=eng.target_ms,
                    state=eng.state
                )
            else:
                self._popup.update_pace_trainer(
                    elapsed_ms=elapsed,
                    remaining_ms=self._timer.get_current_interval_remaining_ms(),
                    count=self._timer.completed_questions,
                    total=self._timer.total_questions,
                    state=self._timer.state
                )

    # ══════════════════════════════════════════════════════════
    # POPUP HANDLERS
    # ══════════════════════════════════════════════════════════

    def _toggle_popup(self) -> None:
        if self._popup.isVisible():
            self._popup.hide()
        else:
            self._popup.show()
            self._update_elapsed_display()

    def _on_popup_play(self) -> None:
        if self._tabs.currentWidget() is self._tracker:
            if self._tracker._engine.state == "idle":
                self._tracker._start_session()
        else:
            if self._timer.state in ("idle", "completed"):
                self._on_start_pause() # This handles start and resets nicely
            elif self._timer.state == "paused":
                self._timer.resume()
                self._update_elapsed_display()

    def _on_popup_pause(self) -> None:
        if self._tabs.currentWidget() is self._tracker:
            # Tracker doesn't really have a pause, it's continuous until ended.
            pass
        else:
            if self._timer.state == "running":
                self._timer.pause()
                self._update_elapsed_display()

    def _on_popup_reset(self) -> None:
        if self._tabs.currentWidget() is self._tracker:
            self._tracker._end_session()
        else:
            self._on_reset()

    def _on_popup_close(self) -> None:
        self._popup.cleanup_and_close()

    # ══════════════════════════════════════════════════════════
    # BUTTON HANDLERS
    # ══════════════════════════════════════════════════════════

    def _on_start_pause(self) -> None:
        state = self._timer.state

        if state in ("idle", "completed"):
            total_sec = self._spin_min.value() * 60 + self._spin_sec.value()
            if total_sec <= 0:
                return
            questions = self._spin_questions.value()
            if questions <= 0:
                return

            interval_ms = total_sec * 1000
            self._timer.configure(interval_ms, questions)

            self._lbl_progress.setText(f"0 / {questions}")
            self._lbl_percent.setText("0%")
            self._progress_bar.setValue(0)
            self._lbl_countdown.setText(self._format_time(interval_ms))
            self._lbl_elapsed.setText("00:00")
            self._lbl_remaining.setText(self._format_time(interval_ms * questions))

            self._timer.start()

        elif state == "running":
            self._timer.pause()
            self._update_elapsed_display()

        elif state == "paused":
            self._timer.resume()

    def _on_reset(self) -> None:
        self._timer.reset()
        self._display_timer.stop()
        self._lbl_countdown.setText("00:00")
        self._lbl_elapsed.setText("00:00")
        self._lbl_remaining.setText("00:00")
        self._lbl_progress.setText("0 / 0")
        self._lbl_percent.setText("0%")
        self._progress_bar.setValue(0)

    def _apply_preset(self, minutes: int, seconds: int, questions: int) -> None:
        if self._timer.state != "idle":
            return
        self._spin_min.setValue(minutes)
        self._spin_sec.setValue(seconds)
        self._spin_questions.setValue(questions)

    # ══════════════════════════════════════════════════════════
    # NOTIFICATIONS
    # ══════════════════════════════════════════════════════════

    def _show_notification(self, title: str, message: str) -> None:
        """Route notification requests to the tray (used by both tabs)."""
        if self._chk_notifications.isChecked():
            self._tray.show_notification(title, message)

    # ══════════════════════════════════════════════════════════
    # OPTIONS
    # ══════════════════════════════════════════════════════════

    def _toggle_always_on_top(self, checked: bool) -> None:
        flags = self.windowFlags()
        if checked:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    def _on_sound_changed(self, name: str) -> None:
        """Handle notification sound selection change."""
        if name and name in self._sound.get_sound_names():
            self._sound.set_notification_sound(name)

    def _preview_sound(self) -> None:
        """Play a preview of the currently selected notification sound."""
        name = self._combo_sound.currentText()
        if name:
            self._sound.preview_sound(name)

    # ══════════════════════════════════════════════════════════
    # WINDOW EVENTS
    # ══════════════════════════════════════════════════════════

    def closeEvent(self, event) -> None:
        if self._closing_for_real:
            self._save_settings()
            self._tray.hide()
            event.accept()
        else:
            event.ignore()
            self.hide()
            self._tray.show_notification(
                "GRE Pace Trainer",
                "Running in the background. Double-click tray icon to restore.",
            )

    def _restore_from_tray(self) -> None:
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _do_exit(self) -> None:
        self._closing_for_real = True
        self._save_settings()
        self._tray.hide()
        self._popup.close()
        QApplication.quit()

    # ══════════════════════════════════════════════════════════
    # SETTINGS
    # ══════════════════════════════════════════════════════════

    def _load_settings(self) -> None:
        s = self._settings.load()
        self._spin_min.setValue(s.get("interval_minutes", 3))
        self._spin_sec.setValue(s.get("interval_seconds", 0))
        self._spin_questions.setValue(s.get("question_count", 20))
        self._chk_on_top.setChecked(s.get("always_on_top", True))
        self._chk_sound.setChecked(s.get("sound_enabled", True))
        self._chk_notifications.setChecked(s.get("notifications_enabled", True))
        self._slider_volume.setValue(s.get("volume", 80))

        x, y = s.get("window_x", -1), s.get("window_y", -1)
        if x >= 0 and y >= 0:
            self.move(x, y)
            
        px, py = s.get("popup_x", -1), s.get("popup_y", -1)
        if px >= 0 and py >= 0:
            self._popup.move(px, py)

        if s.get("always_on_top", True):
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        # Restore sound settings
        saved_sound = s.get("notification_sound", "Classic Beep")
        if saved_sound in self._sound.get_sound_names():
            self._sound.set_notification_sound(saved_sound)
            idx = self._combo_sound.findText(saved_sound)
            if idx >= 0:
                self._combo_sound.setCurrentIndex(idx)

        is_muted = s.get("muted", False)
        self._sound.set_muted(is_muted)
        self._chk_mute.setChecked(is_muted)

    def _save_settings(self) -> None:
        pos = self.pos()
        ppos = self._popup.pos()
        self._settings.save({
            "interval_minutes": self._spin_min.value(),
            "interval_seconds": self._spin_sec.value(),
            "question_count": self._spin_questions.value(),
            "always_on_top": self._chk_on_top.isChecked(),
            "sound_enabled": self._chk_sound.isChecked(),
            "notifications_enabled": self._chk_notifications.isChecked(),
            "volume": self._slider_volume.value(),
            "notification_sound": self._sound.get_notification_sound(),
            "muted": self._sound.muted,
            "window_x": pos.x(),
            "window_y": pos.y(),
            "popup_x": ppos.x(),
            "popup_y": ppos.y(),
        })

    # ══════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════

    @staticmethod
    def _format_time(ms: int) -> str:
        total_sec = max(0, ms) // 1000
        hours, remainder = divmod(total_sec, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
