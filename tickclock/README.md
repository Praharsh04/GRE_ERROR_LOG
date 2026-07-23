# GRE Pace Trainer

A Windows desktop pacing coach that repeatedly alerts you at fixed question intervals, helping GRE students develop a strong sense of timing.

## Features

- **Drift-free timer** — timestamp-based timing that stays accurate across hours-long sessions
- **GRE presets** — Quant, Verbal, and Reading Comprehension presets
- **Custom timing** — set any interval from seconds to minutes
- **Sound alerts** — short beep per interval, ascending completion tone
- **Desktop notifications** — optional toast notifications for each interval
- **System tray** — minimize to tray and keep timing in the background
- **Always on top** — stays visible during practice sessions
- **Settings persistence** — remembers your last configuration
- **Session summary** — detailed recap after completing a session

## Requirements

- Python 3.10+
- Windows 10/11

## Setup

```bash
# Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Build Standalone Executable

```bash
# Install PyInstaller (included in requirements.txt)
pip install -r requirements.txt

# Build the exe
pyinstaller --noconfirm --onefile --windowed ^
    --name "GRE Pace Trainer" ^
    --icon NONE ^
    main.py
```

The standalone `.exe` will be in the `dist/` folder.

> **Tip:** To add a custom `.ico` file, replace `--icon NONE` with `--icon your_icon.ico`.

## Project Structure

```
tickclock/
├── main.py                     # Entry point
├── requirements.txt            # Dependencies
├── README.md                   # This file
├── settings.json               # Auto-generated user settings
└── src/
    ├── __init__.py
    ├── timer_engine.py         # Drift-free timestamp timer
    ├── sound_manager.py        # winsound-based beep manager
    ├── settings_manager.py     # JSON settings persistence
    └── ui/
        ├── __init__.py
        ├── main_window.py      # Main application window
        ├── styles.py           # QSS dark mode stylesheet
        ├── summary_dialog.py   # Session summary dialog
        └── tray_manager.py     # System tray integration
```

## License

MIT
