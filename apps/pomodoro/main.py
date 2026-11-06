"""Focus Timer - a Pomodoro timer with a progress ring. Sushant Labs."""
import math
import time
import tkinter as tk

from logic import DURATIONS, LABELS, WORK, format_time, next_phase

BG, FG, MUTED, TRACK = "#12141a", "#f2f4f8", "#8b93a7", "#252a36"
ACCENTS = {"work": "#ff6b5e", "short": "#3ddc97", "long": "#5eb0ff"}
FONT = "Helvetica"


class FocusTimer:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("Focus Timer")
        root.configure(bg=BG)
        root.resizable(False, False)

        self.phase = WORK
        self.total = DURATIONS[WORK]
        self.remaining = float(self.total)
        self.end_at = 0.0
        self.running = False
        self.sessions = 0
        self._job = None

        self.canvas = tk.Canvas(root, width=300, height=300, bg=BG, highlightthickness=0)
        self.canvas.pack(padx=28, pady=(28, 8))
        self.canvas.create_oval(20, 20, 280, 280, outline=TRACK, width=14)
        self.arc = self.canvas.create_arc(
            20, 20, 280, 280, start=90, extent=-359.9, style="arc", outline=ACCENTS[WORK], width=14
        )
        self.clock = self.canvas.create_text(150, 138, text="25:00", fill=FG, font=(FONT, 46, "bold"))
        self.label = self.canvas.create_text(150, 188, text="Focus", fill=MUTED, font=(FONT, 15))

        row = tk.Frame(root, bg=BG)
        row.pack(pady=8)
        self.start_btn = self._button(row, "Start", self.toggle)
        self._button(row, "Reset", self.reset)
        self._button(row, "Skip", self.skip)

        self.count = tk.Label(root, text="Sessions: 0", bg=BG, fg=MUTED, font=(FONT, 12))
        self.count.pack(pady=(4, 24))

        root.bind("<space>", lambda _event: self.toggle())
        self.render()

    def _button(self, parent: tk.Frame, text: str, command) -> tk.Button:
        button = tk.Button(
            parent, text=text, command=command, width=8, relief="flat", bd=0, pady=6,
            bg=TRACK, fg=FG, activebackground="#323949", activeforeground=FG, font=(FONT, 12),
        )
        button.pack(side="left", padx=5)
        return button

    def _cancel(self) -> None:
        if self._job is not None:
            self.root.after_cancel(self._job)
            self._job = None

    def toggle(self) -> None:
        if self.running:
            self._cancel()
            self.running = False
            self.start_btn.config(text="Resume")
        else:
            self._cancel()
            self.running = True
            self.end_at = time.monotonic() + self.remaining
            self.start_btn.config(text="Pause")
            self.tick()
        self.render()

    def tick(self) -> None:
        if not self.running:
            return
        self.remaining = max(0.0, self.end_at - time.monotonic())
        self.render()
        if self.remaining <= 0:
            self.advance(completed=True)
        else:
            self._job = self.root.after(200, self.tick)

    def reset(self) -> None:
        self._cancel()
        self.running = False
        self.remaining = float(self.total)
        self.start_btn.config(text="Start")
        self.render()

    def skip(self) -> None:
        self.advance(completed=False)

    def advance(self, completed: bool) -> None:
        self._cancel()
        self.running = False
        if self.phase == WORK and completed:
            self.sessions += 1
            self.count.config(text=f"Sessions: {self.sessions}")
        self.phase = next_phase(self.phase, self.sessions)
        self.total = DURATIONS[self.phase]
        self.remaining = float(self.total)
        self.start_btn.config(text="Start")
        self.render()
        if completed:
            self.root.bell()
            self.root.after(250, self.root.bell)

    def render(self) -> None:
        fraction = self.remaining / self.total if self.total else 0.0
        self.canvas.itemconfigure(
            self.arc, extent=-max(0.01, 359.99 * fraction), outline=ACCENTS[self.phase]
        )
        shown = format_time(math.ceil(self.remaining))
        self.canvas.itemconfigure(self.clock, text=shown)
        self.canvas.itemconfigure(self.label, text=LABELS[self.phase])
        self.root.title(f"{shown} - {LABELS[self.phase]}" if self.running else "Focus Timer")


def main() -> None:
    root = tk.Tk()
    FocusTimer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
