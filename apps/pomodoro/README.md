# Focus Timer

A Pomodoro timer with a progress ring and session counter. Python standard library only (Tkinter).

## Run

    python main.py

Press **Space** to start or pause. After every fourth focus session you get a long break.

## Build a standalone app

    pip install pyinstaller
    pyinstaller --onefile --windowed main.py
