"""
GRE Pace Trainer — Entry Point

A Windows desktop pacing coach that repeatedly alerts at fixed question
intervals, helping GRE students develop a strong sense of timing.
"""

import sys
from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("GRE Pace Trainer")
    app.setOrganizationName("TickClock")
    app.setQuitOnLastWindowClosed(False)  # Keep running in tray

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
