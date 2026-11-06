# Password Generator

Random passwords from Python's `secrets` module (OS-level secure randomness). Standard library only.

## Run

    python main.py

Nothing is stored or sent anywhere. After you copy a password, the clipboard is cleared 30 seconds
later if it still holds that password.

## Build a standalone app

    pip install pyinstaller
    pyinstaller --onefile --windowed main.py
