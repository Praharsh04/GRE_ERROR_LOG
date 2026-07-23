"""
GRE Pace Trainer — Custom Chart Widgets

QPainter-based chart widgets for the Question Tracker analytics.
Fully offline — no external plotting library required.
"""

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

# ── Palette ────────────────────────────────────────────────

COLOR_FAST = QColor("#4ade80")
COLOR_ON_TARGET = QColor("#ffffff")
COLOR_SLOW = QColor("#f87171")
COLOR_BG = QColor("#121212")
COLOR_GRID = QColor("#333333")
COLOR_TEXT = QColor("#888888")
COLOR_TARGET_LINE = QColor("#aaaaaa")
COLOR_SURFACE = QColor("#1e1e1e")


def _pace_color(time_ms: int, target_ms: int) -> QColor:
    if target_ms <= 0:
        return COLOR_ON_TARGET
    ratio = time_ms / target_ms
    if ratio < 0.80:
        return COLOR_FAST
    elif ratio <= 1.20:
        return COLOR_ON_TARGET
    else:
        return COLOR_SLOW


def _format_sec(ms: int) -> str:
    s = max(0, ms) / 1000
    m, s = divmod(int(s), 60)
    if m > 0:
        return f"{m}:{s:02d}"
    return f"{s}s"


class BarChartWidget(QWidget):
    """Bar chart showing time per question with a target line overlay."""

    def __init__(
        self,
        question_times_ms: list[int],
        target_ms: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._times = question_times_ms
        self._target = target_ms
        self.setMinimumHeight(220)
        min_width = max(350, len(question_times_ms) * 36 + 80)
        self.setMinimumWidth(min_width)

    def paintEvent(self, event) -> None:
        if not self._times:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Margins
        left = 52
        right = 16
        top = 16
        bottom = 32

        chart_w = w - left - right
        chart_h = h - top - bottom

        if chart_w <= 0 or chart_h <= 0:
            painter.end()
            return

        n = len(self._times)
        max_val = max(max(self._times), self._target) * 1.15

        if max_val <= 0:
            painter.end()
            return

        # ── Background ────────────────────────────────
        painter.fillRect(self.rect(), COLOR_SURFACE)

        # ── Y-axis grid lines ─────────────────────────
        painter.setPen(QPen(COLOR_GRID, 1, Qt.DashLine))
        label_font = QFont("Segoe UI", 8)
        painter.setFont(label_font)

        num_grid = 5
        for i in range(num_grid + 1):
            y = top + chart_h - (i / num_grid) * chart_h
            val = int((i / num_grid) * max_val)
            painter.setPen(QPen(COLOR_GRID, 1, Qt.DashLine))
            painter.drawLine(int(left), int(y), int(w - right), int(y))
            painter.setPen(COLOR_TEXT)
            painter.drawText(
                QRectF(0, y - 8, left - 6, 16),
                Qt.AlignRight | Qt.AlignVCenter,
                _format_sec(val),
            )

        # ── Bars ──────────────────────────────────────
        bar_spacing = 3
        bar_total_w = chart_w / n
        bar_w = max(6, bar_total_w - bar_spacing * 2)
        bar_w = min(bar_w, 40)

        for i, t in enumerate(self._times):
            bar_h = (t / max_val) * chart_h
            x = left + i * bar_total_w + (bar_total_w - bar_w) / 2
            y = top + chart_h - bar_h

            color = _pace_color(t, self._target)

            # Draw rounded bar
            path = QPainterPath()
            radius = min(3, bar_w / 2)
            path.addRoundedRect(QRectF(x, y, bar_w, bar_h), radius, radius)
            painter.fillPath(path, color)

            # Question number label below
            painter.setPen(COLOR_TEXT)
            painter.setFont(QFont("Segoe UI", 7))
            label_rect = QRectF(x - 4, top + chart_h + 4, bar_w + 8, 20)
            painter.drawText(label_rect, Qt.AlignCenter, f"Q{i + 1}")

        # ── Target line ───────────────────────────────
        target_y = top + chart_h - (self._target / max_val) * chart_h
        pen = QPen(COLOR_TARGET_LINE, 2, Qt.DashLine)
        painter.setPen(pen)
        painter.drawLine(int(left), int(target_y), int(w - right), int(target_y))

        # Target label
        painter.setPen(COLOR_TARGET_LINE)
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        painter.drawText(
            QRectF(left + 4, target_y - 18, 100, 16),
            Qt.AlignLeft | Qt.AlignVCenter,
            f"Target: {_format_sec(self._target)}",
        )

        painter.end()


class PaceBreakdownWidget(QWidget):
    """Horizontal stacked bar showing fast/on-target/slow breakdown."""

    def __init__(
        self,
        fast: int,
        on_target: int,
        slow: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._fast = fast
        self._on_target = on_target
        self._slow = slow
        self.setFixedHeight(40)
        self.setMinimumWidth(280)

    def paintEvent(self, event) -> None:
        total = self._fast + self._on_target + self._slow
        if total <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width() - 2
        h = 20
        y = 2
        x = 1
        radius = 6

        segments = [
            (self._fast, COLOR_FAST, "Fast"),
            (self._on_target, COLOR_ON_TARGET, "On Target"),
            (self._slow, COLOR_SLOW, "Slow"),
        ]

        # Draw background
        bg_path = QPainterPath()
        bg_path.addRoundedRect(QRectF(x, y, w, h), radius, radius)
        painter.fillPath(bg_path, COLOR_BG)

        # Draw segments using clipping
        painter.setClipPath(bg_path)
        cx = float(x)
        for count, color, _ in segments:
            if count <= 0:
                continue
            seg_w = (count / total) * w
            painter.fillRect(QRectF(cx, y, seg_w, h), color)
            cx += seg_w
        painter.setClipping(False)

        # Legend below
        painter.setFont(QFont("Segoe UI", 9))
        lx = x
        ly = y + h + 4
        for count, color, label in segments:
            if count <= 0:
                continue
            # Dot
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(lx), int(ly + 2), 8, 8)
            # Text
            painter.setPen(QColor("#8888a0"))
            text = f"{label}: {count}"
            painter.drawText(int(lx + 12), int(ly + 11), text)
            lx += len(text) * 7 + 28

        painter.end()
