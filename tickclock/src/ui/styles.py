"""
GRE Pace Trainer — QSS Stylesheet

Minimal Dark theme using deep greys and white accents.
All design tokens are defined here for consistency.
"""


def get_stylesheet() -> str:
    """Return the complete application stylesheet."""
    return """
    /* ── Global ─────────────────────────────────────────── */

    QMainWindow {
        background-color: #121212;
    }

    QWidget {
        background-color: transparent;
        color: #e0e0e0;
        font-family: "Segoe UI", sans-serif;
        font-size: 13px;
    }

    /* ── Buttons ────────────────────────────────────────── */

    QPushButton {
        background-color: #ffffff;
        color: #000000;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        font-size: 13px;
        min-height: 18px;
    }

    QPushButton:hover {
        background-color: #e0e0e0;
    }

    QPushButton:pressed {
        background-color: #cccccc;
    }

    QPushButton:disabled {
        background-color: #2d2d2d;
        color: #666666;
    }

    QPushButton#resetBtn {
        background-color: transparent;
        border: 1px solid #333333;
        color: #aaaaaa;
    }

    QPushButton#resetBtn:hover {
        border-color: #ffffff;
        color: #ffffff;
    }

    QPushButton#resetBtn:pressed {
        background-color: #1e1e1e;
    }

    /* Preset buttons */
    QPushButton#presetQuant,
    QPushButton#presetVerbal,
    QPushButton#presetRC {
        background-color: #1e1e1e;
        border: 1px solid #333333;
        border-radius: 6px;
        padding: 8px 14px;
        font-size: 12px;
        color: #aaaaaa;
        font-weight: 500;
    }

    QPushButton#presetQuant:hover,
    QPushButton#presetVerbal:hover,
    QPushButton#presetRC:hover {
        border-color: #ffffff;
        color: #ffffff;
        background-color: #2d2d2d;
    }

    /* ── SpinBox ────────────────────────────────────────── */

    QSpinBox {
        background-color: #1e1e1e;
        border: 1px solid #333333;
        border-radius: 6px;
        padding: 8px 12px;
        color: #ffffff;
        font-size: 15px;
        font-weight: 600;
        min-width: 70px;
        selection-background-color: #555555;
    }

    QSpinBox:focus {
        border-color: #ffffff;
    }

    QSpinBox:disabled {
        background-color: #121212;
        color: #666666;
        border-color: #1e1e1e;
    }

    QSpinBox::up-button, QSpinBox::down-button {
        width: 20px;
        border: none;
        background: transparent;
    }

    QSpinBox::up-arrow {
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-bottom: 5px solid #aaaaaa;
        width: 0px;
        height: 0px;
    }

    QSpinBox::down-arrow {
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid #aaaaaa;
        width: 0px;
        height: 0px;
    }

    QSpinBox::up-arrow:hover { border-bottom-color: #ffffff; }
    QSpinBox::down-arrow:hover { border-top-color: #ffffff; }

    /* ── ProgressBar ────────────────────────────────────── */

    QProgressBar {
        background-color: #1e1e1e;
        border: none;
        border-radius: 4px;
        min-height: 8px;
        max-height: 8px;
        text-align: center;
    }

    QProgressBar::chunk {
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 #888888, stop:1 #ffffff
        );
        border-radius: 4px;
    }

    /* ── CheckBox ───────────────────────────────────────── */

    QCheckBox {
        color: #aaaaaa;
        font-size: 12px;
        spacing: 8px;
    }

    QCheckBox:hover {
        color: #ffffff;
    }

    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 1px solid #333333;
        background-color: #1e1e1e;
    }

    QCheckBox::indicator:checked {
        background-color: #ffffff;
        border-color: #ffffff;
        image: none; /* Can add custom checkmark if desired */
    }

    QCheckBox::indicator:hover {
        border-color: #ffffff;
    }

    /* ── Slider ─────────────────────────────────────────── */

    QSlider::groove:horizontal {
        height: 4px;
        background: #333333;
        border-radius: 2px;
    }

    QSlider::handle:horizontal {
        width: 16px;
        height: 16px;
        margin: -6px 0;
        background: #ffffff;
        border-radius: 8px;
    }

    QSlider::handle:horizontal:hover {
        background: #e0e0e0;
    }

    QSlider::sub-page:horizontal {
        background: #aaaaaa;
        border-radius: 2px;
    }

    /* ── Divider ────────────────────────────────────────── */

    QFrame#divider {
        background-color: #333333;
        max-height: 1px;
        min-height: 1px;
    }

    /* ── Labels ─────────────────────────────────────────── */

    QLabel {
        color: #e0e0e0;
        background: transparent;
    }

    QLabel#appTitle {
        font-size: 18px;
        font-weight: 700;
        color: #ffffff;
    }

    QLabel#appSubtitle {
        font-size: 11px;
        color: #888888;
        font-weight: 400;
    }

    QLabel#sectionTitle {
        font-size: 10px;
        font-weight: 700;
        color: #888888;
        padding-top: 4px;
    }

    QLabel#timerDisplay {
        font-size: 42px;
        font-weight: 700;
        color: #ffffff;
        font-family: "Cascadia Mono", "Consolas", monospace;
    }

    QLabel#statValue {
        font-size: 14px;
        font-weight: 600;
        color: #ffffff;
    }

    QLabel#statLabel {
        font-size: 11px;
        color: #888888;
        font-weight: 400;
    }

    QLabel#progressFraction {
        font-size: 15px;
        font-weight: 700;
        color: #ffffff;
    }

    QLabel#progressPercent {
        font-size: 13px;
        font-weight: 600;
        color: #aaaaaa;
    }

    QLabel#inputLabel {
        font-size: 12px;
        color: #aaaaaa;
        font-weight: 500;
    }

    QLabel#volumeLabel {
        font-size: 11px;
        color: #888888;
    }

    /* ── Card container ─────────────────────────────────── */

    QFrame#card {
        background-color: #1e1e1e;
        border-radius: 10px;
        border: 1px solid #333333;
    }

    /* ── Menu (tray) ────────────────────────────────────── */

    QMenu {
        background-color: #1e1e1e;
        border: 1px solid #333333;
        border-radius: 8px;
        padding: 4px;
    }

    QMenu::item {
        padding: 8px 24px;
        color: #e0e0e0;
        border-radius: 4px;
    }

    QMenu::item:selected {
        background-color: #2d2d2d;
    }

    QMenu::separator {
        height: 1px;
        background: #333333;
        margin: 4px 8px;
    }

    /* ── Summary Dialog ─────────────────────────────────── */

    QDialog {
        background-color: #121212;
    }

    QFrame#summaryCard {
        background-color: #1e1e1e;
        border-radius: 12px;
        border: 1px solid #333333;
    }

    QLabel#summaryTitle {
        font-size: 20px;
        font-weight: 700;
        color: #ffffff;
    }

    QLabel#summaryStatLabel {
        font-size: 12px;
        color: #888888;
    }

    QLabel#summaryStatValue {
        font-size: 14px;
        font-weight: 600;
        color: #ffffff;
    }

    QLabel#summaryStatus {
        font-size: 14px;
        font-weight: 700;
        color: #ffffff;
    }

    QPushButton#summaryCloseBtn {
        background-color: #ffffff;
        color: #000000;
        border: none;
        border-radius: 8px;
        padding: 10px 32px;
        font-weight: 600;
        font-size: 13px;
    }

    QPushButton#summaryCloseBtn:hover {
        background-color: #e0e0e0;
    }

    /* ── Tab Widget ─────────────────────────────────────── */

    QTabWidget::pane {
        border: none;
        background: transparent;
    }

    QTabBar::tab {
        background: transparent;
        color: #aaaaaa;
        padding: 10px 16px;
        font-weight: 600;
        font-size: 14px;
        border-bottom: 2px solid transparent;
    }

    QTabBar::tab:hover {
        color: #ffffff;
    }

    QTabBar::tab:selected {
        color: #ffffff;
        border-bottom: 2px solid #ffffff;
    }
    """
