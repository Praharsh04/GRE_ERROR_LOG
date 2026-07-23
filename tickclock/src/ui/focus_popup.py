"""
GRE Pace Trainer — Focus Timer Popup

A floating window inspired by the Windows Clock timer popup.
Draggable, borderless, dark mode, always-on-top.
Supports real-time resizing from all edges and corners with
dynamic font scaling.
"""

import os
from PySide6.QtCore import Qt, Signal, QSize, QRect, QPoint
from PySide6.QtGui import QMouseEvent, QWheelEvent, QIcon, QCursor, QPainter, QColor, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QProgressBar,
)


ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets")

def _get_icon(name: str) -> QIcon:
    return QIcon(os.path.join(ASSETS_DIR, name))


def _fmt_ms(ms: int, show_hours: bool = False) -> str:
    total_s = max(0, ms) // 1000
    h, r = divmod(total_s, 3600)
    m, s = divmod(r, 60)
    if show_hours or h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


# Edge zones for resize hit-testing
_EDGE_MARGIN = 8

_EDGE_NONE   = 0
_EDGE_LEFT   = 1
_EDGE_RIGHT  = 2
_EDGE_TOP    = 4
_EDGE_BOTTOM = 8

_CURSOR_MAP = {
    _EDGE_LEFT:                  Qt.SizeHorCursor,
    _EDGE_RIGHT:                 Qt.SizeHorCursor,
    _EDGE_TOP:                   Qt.SizeVerCursor,
    _EDGE_BOTTOM:                Qt.SizeVerCursor,
    _EDGE_LEFT  | _EDGE_TOP:     Qt.SizeFDiagCursor,
    _EDGE_RIGHT | _EDGE_BOTTOM:  Qt.SizeFDiagCursor,
    _EDGE_LEFT  | _EDGE_BOTTOM:  Qt.SizeBDiagCursor,
    _EDGE_RIGHT | _EDGE_TOP:     Qt.SizeBDiagCursor,
}


class FocusPopup(QWidget):
    """Floating horizontal timer dashboard with real-time edge resizing."""

    request_play = Signal()
    request_pause = Signal()
    request_reset = Signal()
    request_close = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)

        self.setMinimumSize(340, 90)
        self.resize(520, 130)

        self._drag_pos = None
        self._resize_edge = _EDGE_NONE
        self._resize_origin_rect = QRect()
        self._resize_origin_pos = QPoint()
        self._current_opacity = 1.0
        self.setWindowOpacity(self._current_opacity)

        self._build_ui()

    # ══════════════════════════════════════════════════════════
    # UI BUILD
    # ══════════════════════════════════════════════════════════

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)

        self._bg_frame = QFrame()
        self._bg_frame.setStyleSheet(
            """
            QFrame#popupBg {
                background-color: #121212;
                border-radius: 16px;
                border: 1px solid #333;
            }
            """
        )
        self._bg_frame.setObjectName("popupBg")
        self._bg_frame.setMouseTracking(True)
        root.addWidget(self._bg_frame)

        bg_layout = QHBoxLayout(self._bg_frame)
        bg_layout.setContentsMargins(20, 12, 16, 12)
        bg_layout.setSpacing(12)

        # ── Left: Main Timer ──
        self._lbl_timer = QLabel("00:00")
        self._lbl_timer.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._lbl_timer.setMouseTracking(True)
        bg_layout.addWidget(self._lbl_timer)

        # ── Middle: Stats ──
        stats_widget = QWidget()
        stats_widget.setMouseTracking(True)
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setContentsMargins(0, 2, 0, 2)
        stats_layout.setAlignment(Qt.AlignVCenter)
        
        self._lbl_mode = QLabel("Session Mode")
        stats_layout.addWidget(self._lbl_mode)

        self._lbl_line1 = QLabel("Question 0 / 0")
        stats_layout.addWidget(self._lbl_line1)
        stats_layout.addSpacing(3)

        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedHeight(6)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setStyleSheet(
            """
            QProgressBar {
                background-color: #333333;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #2563eb;
                border-radius: 3px;
            }
            """
        )
        stats_layout.addWidget(self._progress_bar)
        stats_layout.addSpacing(2)

        self._lbl_line2 = QLabel("")
        stats_layout.addWidget(self._lbl_line2)

        bg_layout.addWidget(stats_widget, 1)

        # ── Right: Controls ──
        self._controls_widget = QWidget()
        self._controls_widget.setMouseTracking(True)
        self._controls_widget.setStyleSheet(
            """
            QPushButton {
                background: #222222; color: #ffffff; border: 1px solid #444;
                border-radius: 18px; font-size: 16px; font-weight: bold;
            }
            QPushButton:hover { background: #3b82f6; border: 1px solid #3b82f6; }
            QPushButton:pressed { background: #1d4ed8; }
            QPushButton#closeBtn:hover { background: #ef4444; border: 1px solid #ef4444; }
            """
        )
        cw_layout = QHBoxLayout(self._controls_widget)
        cw_layout.setContentsMargins(0, 0, 0, 0)
        cw_layout.setSpacing(8)
        cw_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self._btn_play = QPushButton()
        self._btn_play.setIcon(_get_icon("play.svg"))
        self._btn_play.setIconSize(QSize(18, 18))
        self._btn_play.setFixedSize(36, 36)
        self._btn_play.setCursor(Qt.PointingHandCursor)
        self._btn_play.clicked.connect(self.request_play.emit)
        
        self._btn_pause = QPushButton()
        self._btn_pause.setIcon(_get_icon("pause.svg"))
        self._btn_pause.setIconSize(QSize(18, 18))
        self._btn_pause.setFixedSize(36, 36)
        self._btn_pause.setCursor(Qt.PointingHandCursor)
        self._btn_pause.clicked.connect(self.request_pause.emit)
        
        self._btn_reset = QPushButton()
        self._btn_reset.setIcon(_get_icon("reset.svg"))
        self._btn_reset.setIconSize(QSize(18, 18))
        self._btn_reset.setFixedSize(36, 36)
        self._btn_reset.setCursor(Qt.PointingHandCursor)
        self._btn_reset.clicked.connect(self.request_reset.emit)

        self._btn_close = QPushButton()
        self._btn_close.setIcon(_get_icon("close.svg"))
        self._btn_close.setIconSize(QSize(18, 18))
        self._btn_close.setObjectName("closeBtn")
        self._btn_close.setFixedSize(36, 36)
        self._btn_close.setCursor(Qt.PointingHandCursor)
        self._btn_close.clicked.connect(self.request_close.emit)
        
        cw_layout.addWidget(self._btn_play)
        cw_layout.addWidget(self._btn_pause)
        cw_layout.addWidget(self._btn_reset)
        cw_layout.addWidget(self._btn_close)
        
        bg_layout.addWidget(self._controls_widget)

        # Apply initial scaled styles
        self._apply_scaled_styles()

    # ══════════════════════════════════════════════════════════
    # DYNAMIC FONT SCALING
    # ══════════════════════════════════════════════════════════

    def _apply_scaled_styles(self):
        """Recalculate font sizes and styles based on current widget height."""
        h = self.height()
        
        # Scale timer font: base 56px at height 130, min 28px, max 96px
        timer_size = max(28, min(96, int(h * 0.43)))
        # Scale info fonts proportionally
        mode_size = max(9, min(16, int(h * 0.09)))
        line1_size = max(11, min(22, int(h * 0.13)))
        line2_size = max(9, min(16, int(h * 0.09)))

        font_family = "'Segoe UI Variable Display', 'Segoe UI', sans-serif"

        # Timer — color is set by update methods, so only set size/weight/font here
        # We preserve existing color by reading current stylesheet
        current_style = self._lbl_timer.styleSheet()
        # Extract color if present
        color = "#ffffff"
        if "color:" in current_style:
            import re
            m = re.search(r'color:\s*(#[0-9a-fA-F]+)', current_style)
            if m:
                color = m.group(1)
        self._lbl_timer.setStyleSheet(
            f"color: {color}; font-size: {timer_size}px; font-weight: 700; "
            f"font-family: {font_family};"
        )
        
        self._lbl_mode.setStyleSheet(
            f"color: #b0b0b0; font-size: {mode_size}px; font-weight: bold;"
        )
        self._lbl_line1.setStyleSheet(
            f"color: #ffffff; font-size: {line1_size}px; font-weight: 600;"
        )
        self._lbl_line2.setStyleSheet(
            f"color: #aaaaaa; font-size: {line2_size}px;"
        )

    # ══════════════════════════════════════════════════════════
    # DATA BINDING
    # ══════════════════════════════════════════════════════════

    def update_pace_trainer(self, elapsed_ms: int, remaining_ms: int,
                            count: int, total: int, state: str):
        self._lbl_mode.setText("PACE TRAINER")
        self._lbl_timer.setText(_fmt_ms(remaining_ms))
        
        # Preserve current scaling, just reset color to white
        h = self.height()
        timer_size = max(28, min(96, int(h * 0.43)))
        font_family = "'Segoe UI Variable Display', 'Segoe UI', sans-serif"
        self._lbl_timer.setStyleSheet(
            f"color: #ffffff; font-size: {timer_size}px; font-weight: 700; "
            f"font-family: {font_family};"
        )
        
        self._lbl_line1.setText(f"Question {count} / {total}")
        self._lbl_line2.setText(f"Elapsed: {_fmt_ms(elapsed_ms)}")
        
        total_time = elapsed_ms + remaining_ms
        if total_time > 0:
            self._progress_bar.setRange(0, total_time)
            self._progress_bar.setValue(elapsed_ms)
        else:
            self._progress_bar.setRange(0, 100)
            self._progress_bar.setValue(0)
            
        self._btn_play.setVisible(state != "running")
        self._btn_pause.setVisible(state == "running")

    def update_question_tracker(self, elapsed_ms: int, current_q: int,
                                avg_ms: int, target_ms: int, state: str):
        self._lbl_mode.setText("QUESTION TRACKER")
        self._lbl_timer.setText(_fmt_ms(elapsed_ms))
        
        if target_ms > 0:
            ratio = elapsed_ms / target_ms
            if ratio < 0.8: color = "#ffffff"
            elif ratio < 1.0: color = "#fbbf24"
            elif ratio < 1.2: color = "#fb923c"
            else: color = "#f87171"
            
            self._progress_bar.setRange(0, target_ms)
            self._progress_bar.setValue(min(elapsed_ms, target_ms))
        else:
            color = "#ffffff"
            self._progress_bar.setRange(0, 100)
            self._progress_bar.setValue(0)
        
        h = self.height()
        timer_size = max(28, min(96, int(h * 0.43)))
        font_family = "'Segoe UI Variable Display', 'Segoe UI', sans-serif"
        self._lbl_timer.setStyleSheet(
            f"color: {color}; font-size: {timer_size}px; font-weight: 700; "
            f"font-family: {font_family};"
        )
        
        self._lbl_line1.setText(f"Question #{current_q}")
        avg_str = _fmt_ms(avg_ms) if avg_ms > 0 else "--:--"
        tgt_str = _fmt_ms(target_ms) if target_ms > 0 else "--:--"
        self._lbl_line2.setText(f"Avg: {avg_str}  •  Target: {tgt_str}")
        
        self._btn_play.setVisible(state != "running")
        self._btn_pause.setVisible(state == "running")

    # ══════════════════════════════════════════════════════════
    # EDGE HIT TESTING
    # ══════════════════════════════════════════════════════════

    def _edge_at(self, pos: QPoint) -> int:
        """Determine which resize edge(s) a local position falls on."""
        rect = self.rect()
        edge = _EDGE_NONE
        if pos.x() <= _EDGE_MARGIN:
            edge |= _EDGE_LEFT
        elif pos.x() >= rect.width() - _EDGE_MARGIN:
            edge |= _EDGE_RIGHT
        if pos.y() <= _EDGE_MARGIN:
            edge |= _EDGE_TOP
        elif pos.y() >= rect.height() - _EDGE_MARGIN:
            edge |= _EDGE_BOTTOM
        return edge

    # ══════════════════════════════════════════════════════════
    # INTERACTION
    # ══════════════════════════════════════════════════════════

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            # Let button clicks through
            child = self.childAt(event.position().toPoint())
            if isinstance(child, QPushButton):
                super().mousePressEvent(event)
                return

            local = event.position().toPoint()
            edge = self._edge_at(local)
            if edge != _EDGE_NONE:
                # Start edge resize
                self._resize_edge = edge
                self._resize_origin_rect = self.geometry()
                self._resize_origin_pos = event.globalPosition().toPoint()
            else:
                # Start drag
                self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._resize_edge != _EDGE_NONE:
            # Active resize
            delta = event.globalPosition().toPoint() - self._resize_origin_pos
            new_geo = QRect(self._resize_origin_rect)

            if self._resize_edge & _EDGE_LEFT:
                new_geo.setLeft(new_geo.left() + delta.x())
            if self._resize_edge & _EDGE_RIGHT:
                new_geo.setRight(new_geo.right() + delta.x())
            if self._resize_edge & _EDGE_TOP:
                new_geo.setTop(new_geo.top() + delta.y())
            if self._resize_edge & _EDGE_BOTTOM:
                new_geo.setBottom(new_geo.bottom() + delta.y())

            # Enforce minimum size
            min_w, min_h = self.minimumWidth(), self.minimumHeight()
            if new_geo.width() < min_w:
                if self._resize_edge & _EDGE_LEFT:
                    new_geo.setLeft(new_geo.right() - min_w)
                else:
                    new_geo.setRight(new_geo.left() + min_w)
            if new_geo.height() < min_h:
                if self._resize_edge & _EDGE_TOP:
                    new_geo.setTop(new_geo.bottom() - min_h)
                else:
                    new_geo.setBottom(new_geo.top() + min_h)

            self.setGeometry(new_geo)
            return

        if self._drag_pos is not None:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()
            return

        # Hover — update cursor based on edge proximity
        edge = self._edge_at(event.position().toPoint())
        if edge in _CURSOR_MAP:
            self.setCursor(_CURSOR_MAP[edge])
        else:
            self.unsetCursor()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        self._resize_edge = _EDGE_NONE

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        if delta > 0:
            self._current_opacity = min(1.0, self._current_opacity + 0.05)
        elif delta < 0:
            self._current_opacity = max(0.2, self._current_opacity - 0.05)
        self.setWindowOpacity(self._current_opacity)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_scaled_styles()

    def paintEvent(self, event):
        """Draw subtle resize grip dots in the bottom-right corner."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 60))
        
        # Draw 3 small dots in a diagonal pattern
        bx = self.width() - 18
        by = self.height() - 18
        for i in range(3):
            for j in range(3):
                if i + j >= 2:  # Only lower-right triangle
                    painter.drawEllipse(bx + j * 5, by + i * 5, 3, 3)
        painter.end()

    def cleanup_and_close(self):
        """Properly close the popup and clean up resources."""
        self.hide()
