"""
GRE Pace Trainer — System Tray Manager

Provides system-tray icon, context menu, and balloon notifications.
"""

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap, QFont
from PySide6.QtWidgets import QMenu, QSystemTrayIcon, QWidget


def _create_tray_icon() -> QIcon:
    """Generate a simple purple circle icon with 'P' letter."""
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # Purple circle
    painter.setBrush(QColor("#7c6ff5"))
    painter.setPen(QColor("#7c6ff5"))
    painter.drawEllipse(4, 4, size - 8, size - 8)

    # White "P" letter
    painter.setPen(QColor("#ffffff"))
    font = QFont("Segoe UI", 28, QFont.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), 0x0084, "P")  # AlignCenter

    painter.end()
    return QIcon(pixmap)


class TrayManager(QObject):
    """System tray icon with context menu."""

    restore_requested = Signal()
    start_pause_requested = Signal()
    reset_requested = Signal()
    exit_requested = Signal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self._tray = QSystemTrayIcon(_create_tray_icon(), parent)
        self._tray.setToolTip("GRE Pace Trainer")
        self._tray.activated.connect(self._on_activated)

        # Context menu
        menu = QMenu(parent)

        self._restore_action = QAction("Restore", menu)
        self._restore_action.triggered.connect(self.restore_requested.emit)
        menu.addAction(self._restore_action)

        menu.addSeparator()

        self._start_pause_action = QAction("Start", menu)
        self._start_pause_action.triggered.connect(self.start_pause_requested.emit)
        menu.addAction(self._start_pause_action)

        self._reset_action = QAction("Reset", menu)
        self._reset_action.triggered.connect(self.reset_requested.emit)
        menu.addAction(self._reset_action)

        menu.addSeparator()

        exit_action = QAction("Exit", menu)
        exit_action.triggered.connect(self.exit_requested.emit)
        menu.addAction(exit_action)

        self._tray.setContextMenu(menu)

    # ── Public ────────────────────────────────────────────────

    def show(self) -> None:
        self._tray.show()

    def hide(self) -> None:
        self._tray.hide()

    def show_notification(
        self, title: str, message: str, duration_ms: int = 3000
    ) -> None:
        """Show a balloon notification from the tray icon."""
        if self._tray.supportsMessages():
            self._tray.showMessage(title, message, QSystemTrayIcon.Information, duration_ms)

    def update_start_pause_text(self, text: str) -> None:
        """Update the Start/Pause menu item label."""
        self._start_pause_action.setText(text)

    # ── Internal ──────────────────────────────────────────────

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.DoubleClick:
            self.restore_requested.emit()
