"""Typing Speed Test - 30 seconds, WPM, accuracy, best score. Sushant Labs."""
import math
import time
import tkinter as tk

from logic import SCORES_PATH, accuracy, best_wpm, correct_chars, load_scores, make_text, save_score, wpm

DURATION = 30
BG, PANEL, FG, MUTED = "#12141a", "#1b1f29", "#f2f4f8", "#8b93a7"
OK, BAD = "#3ddc97", "#ff6b5e"
FONT, MONO = "Helvetica", "Courier"


class TypingTest:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("Typing Speed Test")
        root.configure(bg=BG)
        root.geometry("760x470")
        root.minsize(640, 430)

        self.target = ""
        self.started_at = None
        self.finished = False
        self._job = None

        self.timer = tk.Label(root, text=f"{DURATION}s", bg=BG, fg=FG, font=(FONT, 34, "bold"))
        self.timer.pack(pady=(22, 4))
        self.hint = tk.Label(root, text="", bg=BG, fg=MUTED, font=(FONT, 12))
        self.hint.pack()

        self.text = tk.Text(
            root, height=7, wrap="word", bg=PANEL, fg=MUTED, relief="flat", font=(MONO, 17),
            padx=18, pady=14, cursor="arrow", highlightthickness=0,
        )
        self.text.pack(fill="x", padx=28, pady=16)
        self.text.tag_configure("ok", foreground=OK)
        self.text.tag_configure("bad", foreground="#ffffff", background=BAD)
        self.text.tag_configure("cur", background="#323949", foreground=FG)

        self.var = tk.StringVar()
        self.entry = tk.Entry(
            root, textvariable=self.var, bg=PANEL, fg=FG, insertbackground=FG, relief="flat",
            font=(MONO, 17), highlightthickness=1, highlightbackground="#323949", highlightcolor=OK,
        )
        self.entry.pack(fill="x", padx=28, ipady=8)
        self.entry.bind("<KeyRelease>", self.on_key)
        root.bind("<Escape>", lambda _event: self.restart())

        self.result = tk.Label(root, text="", bg=BG, fg=FG, font=(FONT, 15))
        self.result.pack(pady=(18, 4))
        self.best = tk.Label(root, text="", bg=BG, fg=MUTED, font=(FONT, 12))
        self.best.pack()

        self.restart()

    def restart(self) -> None:
        if self._job is not None:
            self.root.after_cancel(self._job)
            self._job = None
        self.target = make_text(60)
        self.started_at = None
        self.finished = False
        self.entry.config(state="normal")
        self.var.set("")
        self.entry.focus_set()
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", self.target)
        self.paint("")
        self.timer.config(text=f"{DURATION}s")
        self.hint.config(text="Timer starts on your first keystroke  |  Esc to restart")
        self.result.config(text="", fg=FG)
        best = best_wpm(load_scores(SCORES_PATH))
        self.best.config(text=f"Best: {best} WPM" if best else "No score yet - set the first one")

    def paint(self, typed: str) -> None:
        text = self.text
        text.config(state="normal")
        for tag in ("ok", "bad", "cur"):
            text.tag_remove(tag, "1.0", "end")
        for i, char in enumerate(typed[: len(self.target)]):
            text.tag_add("ok" if char == self.target[i] else "bad", f"1.0+{i}c", f"1.0+{i + 1}c")
        if len(typed) < len(self.target):
            text.tag_add("cur", f"1.0+{len(typed)}c", f"1.0+{len(typed) + 1}c")
        text.config(state="disabled")

    def on_key(self, _event) -> None:
        if self.finished:
            return
        typed = self.var.get()
        if not typed:
            self.paint("")
            return
        if self.started_at is None:
            self.started_at = time.monotonic()
            self.tick()
        self.paint(typed)
        if len(typed) >= len(self.target):
            self.finish()

    def tick(self) -> None:
        if self.finished or self.started_at is None:
            return
        left = DURATION - (time.monotonic() - self.started_at)
        if left <= 0:
            self.finish()
            return
        self.timer.config(text=f"{math.ceil(left)}s")
        self._job = self.root.after(100, self.tick)

    def finish(self) -> None:
        if self.finished:
            return
        self.finished = True
        if self._job is not None:
            self.root.after_cancel(self._job)
            self._job = None
        elapsed = min(DURATION, time.monotonic() - self.started_at)
        typed = self.var.get()[: len(self.target)]
        speed = wpm(correct_chars(typed, self.target), elapsed)
        acc = accuracy(typed, self.target)

        previous = best_wpm(load_scores(SCORES_PATH))
        save_score(SCORES_PATH, speed, acc)
        record = previous is None or speed > previous

        self.entry.config(state="disabled")
        self.timer.config(text="Done")
        self.result.config(text=f"{speed} WPM  |  {acc}% accuracy" + ("  |  new best!" if record else ""),
                           fg=OK if record else FG)
        self.best.config(text=f"Best: {max(speed, previous or 0)} WPM")
        self.hint.config(text="Press Esc to try again")


def main() -> None:
    root = tk.Tk()
    TypingTest(root)
    root.mainloop()


if __name__ == "__main__":
    main()
