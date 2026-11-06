# Typing Speed Test

A 30-second typing test with live per-letter feedback. Standard library only.

## Run

    python main.py

The timer starts on your first keystroke. Press **Esc** to restart. Your best score is saved to
`~/.sushant_labs/typing_scores.json` (local only).

## Build a standalone app

    pip install pyinstaller
    pyinstaller --onefile --windowed main.py
