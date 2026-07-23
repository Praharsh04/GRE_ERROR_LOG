"""
GRE Pace Trainer — Session Summary Dialog

Displayed after a session completes, showing a recap of the practice run.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)


class SummaryDialog(QDialog):
    """Modal dialog showing the completed session summary."""

    def __init__(
        self,
        parent,
        questions: int,
        interval_minutes: int,
        interval_seconds: int,
        total_time_ms: int,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Session Complete")
        self.setFixedWidth(400)
        self.setWindowFlags(
            Qt.Dialog | Qt.WindowCloseButtonHint | Qt.MSWindowsFixedSizeDialogHint
        )
        self.setModal(True)

        self._build_ui(questions, interval_minutes, interval_seconds, total_time_ms)

    def _build_ui(
        self,
        questions: int,
        interval_minutes: int,
        interval_seconds: int,
        total_time_ms: int,
    ) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(0)

        # Card container
        card = QFrame()
        card.setObjectName("summaryCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 28, 24, 24)
        card_layout.setSpacing(20)

        # ── Title ────────────────────────────────────────
        title = QLabel("✓  Session Complete")
        title.setObjectName("summaryTitle")
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)

        # ── Stats ────────────────────────────────────────
        stats_frame = QFrame()
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(14)

        # Format time per question
        time_parts = []
        if interval_minutes > 0:
            time_parts.append(f"{interval_minutes}m")
        if interval_seconds > 0:
            time_parts.append(f"{interval_seconds}s")
        time_str = " ".join(time_parts) if time_parts else "0s"

        # Format total session time
        total_seconds = total_time_ms // 1000
        total_min, total_sec = divmod(total_seconds, 60)
        total_hr, total_min = divmod(total_min, 60)
        if total_hr > 0:
            total_str = f"{total_hr}h {total_min}m {total_sec}s"
        elif total_min > 0:
            total_str = f"{total_min}m {total_sec}s"
        else:
            total_str = f"{total_sec}s"

        stats = [
            ("Questions", str(questions)),
            ("Time Per Question", time_str),
            ("Total Session Time", total_str),
            ("Completed", f"{questions} / {questions}"),
        ]

        for label_text, value_text in stats:
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setObjectName("summaryStatLabel")
            val = QLabel(value_text)
            val.setObjectName("summaryStatValue")
            val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val)
            stats_layout.addLayout(row)

        card_layout.addWidget(stats_frame)

        # ── Divider ──────────────────────────────────────
        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFrameShape(QFrame.HLine)
        card_layout.addWidget(divider)

        # ── Status ───────────────────────────────────────
        status = QLabel("Completed Successfully")
        status.setObjectName("summaryStatus")
        status.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(status)

        # ── Close button ─────────────────────────────────
        close_btn = QPushButton("Close")
        close_btn.setObjectName("summaryCloseBtn")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        card_layout.addWidget(close_btn, alignment=Qt.AlignCenter)

        outer.addWidget(card)
