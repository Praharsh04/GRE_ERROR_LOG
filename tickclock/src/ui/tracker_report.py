"""
GRE Pace Trainer — Tracker Report Dialog

Detailed analytics dialog shown after a Question Tracker session ends.
Contains summary stats, question log table, bar chart, and pace breakdown.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.ui.chart_widgets import BarChartWidget, PaceBreakdownWidget


def _fmt(ms: int) -> str:
    """Format milliseconds as Xm Ys or Xs."""
    total_s = max(0, ms) / 1000
    m, s = divmod(int(total_s), 60)
    if m > 0:
        return f"{m}m {s:02d}s"
    return f"{s}s"


def _fmt_diff(diff_ms: int) -> str:
    """Format a time difference with sign."""
    sign = "+" if diff_ms >= 0 else "−"
    abs_s = abs(diff_ms) / 1000
    m, s = divmod(int(abs_s), 60)
    if m > 0:
        return f"{sign}{m}m {s:02d}s"
    return f"{sign}{s}s"


def _pace_label(pace: str) -> tuple[str, str]:
    """Return display text and color for a pace classification."""
    if pace == "fast":
        return "✓ Fast", "#4ade80"
    elif pace == "on_target":
        return "● On Target", "#7c6ff5"
    else:
        return "✗ Slow", "#f87171"


class TrackerReportDialog(QDialog):
    """Full analytics report for a completed tracker session."""

    def __init__(self, parent, stats) -> None:
        super().__init__(parent)
        self.setWindowTitle("Session Analysis")
        self.setMinimumWidth(480)
        self.setMinimumHeight(600)
        self.setWindowFlags(
            Qt.Dialog | Qt.WindowCloseButtonHint
        )
        self.setModal(True)
        self._stats = stats
        self._build_ui()

    def _build_ui(self) -> None:
        # Scroll area wrapping everything
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: #1e1e2e; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        stats = self._stats

        # ── Title ──────────────────────────────────────
        title = QLabel("📊  Session Analysis")
        title.setObjectName("summaryTitle")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #7c6ff5;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # ── Summary Stats Card ─────────────────────────
        card = QFrame()
        card.setObjectName("summaryCard")
        card_layout = QGridLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(12)

        stat_items = [
            ("Total Questions", str(stats.total_questions)),
            ("Total Time", _fmt(stats.total_time_ms)),
            ("Average", _fmt(stats.average_ms)),
            ("Median", _fmt(stats.median_ms)),
            ("Fastest", f"Q{stats.fastest_q} — {_fmt(stats.fastest_ms)}"),
            ("Slowest", f"Q{stats.slowest_q} — {_fmt(stats.slowest_ms)}"),
            ("Target", _fmt(stats.target_time_ms)),
            ("Avg vs Target", _fmt_diff(stats.average_ms - stats.target_time_ms)),
            ("Within Pace", f"{stats.on_target_pct:.0f}%"),
        ]

        for i, (label, value) in enumerate(stat_items):
            row, col = divmod(i, 3)
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 10px; color: #5c5c78; font-weight: 600;")
            val = QLabel(value)
            val.setStyleSheet("font-size: 14px; color: #e0e0e8; font-weight: 700;")

            cell = QVBoxLayout()
            cell.setSpacing(2)
            cell.addWidget(lbl)
            cell.addWidget(val)
            card_layout.addLayout(cell, row, col)

        layout.addWidget(card)

        # ── Pace Breakdown ─────────────────────────────
        breakdown_label = QLabel("PACE BREAKDOWN")
        breakdown_label.setObjectName("sectionTitle")
        layout.addWidget(breakdown_label)

        breakdown = PaceBreakdownWidget(
            stats.fast_count, stats.on_target_count, stats.slow_count
        )
        layout.addWidget(breakdown)

        # ── Bar Chart ──────────────────────────────────
        chart_label = QLabel("TIME PER QUESTION")
        chart_label.setObjectName("sectionTitle")
        layout.addWidget(chart_label)

        times = [q.time_ms for q in stats.questions]
        chart = BarChartWidget(times, stats.target_time_ms)
        chart.setMinimumHeight(240)
        layout.addWidget(chart)

        # ── Question Log ───────────────────────────────
        log_label = QLabel("QUESTION LOG")
        log_label.setObjectName("sectionTitle")
        layout.addWidget(log_label)

        # Header row
        header = QHBoxLayout()
        header.setSpacing(0)
        for text, width in [("#", 36), ("Time", 80), ("Diff", 80), ("Status", 100)]:
            h = QLabel(text)
            h.setFixedWidth(width)
            h.setStyleSheet(
                "font-size: 10px; font-weight: 700; color: #5c5c78; padding: 4px 0;"
            )
            header.addWidget(h)
        header.addStretch()
        layout.addLayout(header)

        # Divider
        div = QFrame()
        div.setObjectName("divider")
        div.setFrameShape(QFrame.HLine)
        layout.addWidget(div)

        # Question rows
        for q in stats.questions:
            row = QHBoxLayout()
            row.setSpacing(0)

            num_lbl = QLabel(f"Q{q.number}")
            num_lbl.setFixedWidth(36)
            num_lbl.setStyleSheet("font-size: 12px; color: #8888a0; font-weight: 600;")
            row.addWidget(num_lbl)

            time_lbl = QLabel(_fmt(q.time_ms))
            time_lbl.setFixedWidth(80)
            time_lbl.setStyleSheet("font-size: 12px; color: #e0e0e8; font-weight: 600;")
            row.addWidget(time_lbl)

            diff_lbl = QLabel(_fmt_diff(q.diff_ms))
            diff_lbl.setFixedWidth(80)
            diff_color = "#4ade80" if q.diff_ms <= 0 else "#f87171"
            diff_lbl.setStyleSheet(
                f"font-size: 12px; color: {diff_color}; font-weight: 500;"
            )
            row.addWidget(diff_lbl)

            pace_text, pace_color = _pace_label(q.pace)
            pace_lbl = QLabel(pace_text)
            pace_lbl.setFixedWidth(100)
            pace_lbl.setStyleSheet(
                f"font-size: 12px; color: {pace_color}; font-weight: 600;"
            )
            row.addWidget(pace_lbl)

            row.addStretch()
            layout.addLayout(row)

        layout.addSpacing(12)

        # ── Close Button ───────────────────────────────
        close_btn = QPushButton("Close")
        close_btn.setObjectName("summaryCloseBtn")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)
