"""Password Generator - secure random passwords, one-click copy. Sushant Labs."""
import tkinter as tk

from logic import entropy_bits, generate, pool_size, strength_label

BG, PANEL, FG, MUTED = "#12141a", "#1b1f29", "#f2f4f8", "#8b93a7"
COLORS = {"Weak": "#ff6b5e", "Fair": "#ffb454", "Strong": "#3ddc97", "Excellent": "#2dd4bf"}
FONT, MONO = "Helvetica", "Courier"
CLEAR_AFTER_MS = 30_000


class PasswordApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("Password Generator")
        root.configure(bg=BG)
        root.resizable(False, False)

        self.length = tk.IntVar(value=16)
        self.opts = {name: tk.BooleanVar(value=True) for name in ("upper", "lower", "digits", "symbols")}
        self.avoid = tk.BooleanVar(value=False)
        self.password = tk.StringVar()

        box = tk.Frame(root, bg=BG)
        box.pack(padx=28, pady=24)

        entry = tk.Entry(
            box, textvariable=self.password, state="readonly", readonlybackground=PANEL, fg=FG,
            relief="flat", font=(MONO, 18), width=34, justify="center",
        )
        entry.pack(ipady=12, fill="x")

        self.strength = tk.Label(box, text="", bg=BG, fg=MUTED, font=(FONT, 12))
        self.strength.pack(pady=(8, 12))

        buttons = tk.Frame(box, bg=BG)
        buttons.pack()
        self._button(buttons, "Generate", self.refresh, "#3ddc97", "#0b1f17")
        self.copy_btn = self._button(buttons, "Copy", self.copy, "#252a36", FG)

        tk.Label(box, text="Length", bg=BG, fg=MUTED, font=(FONT, 11)).pack(pady=(18, 0))
        tk.Scale(
            box, from_=8, to=64, orient="horizontal", variable=self.length, length=360,
            bg=BG, fg=FG, troughcolor=PANEL, highlightthickness=0, command=lambda _v: self.refresh(),
        ).pack()

        checks = tk.Frame(box, bg=BG)
        checks.pack(pady=(6, 0))
        labels = {"upper": "A-Z", "lower": "a-z", "digits": "0-9", "symbols": "!@#"}
        for key, text in labels.items():
            tk.Checkbutton(
                checks, text=text, variable=self.opts[key], command=self.refresh, bg=BG, fg=FG,
                selectcolor=PANEL, activebackground=BG, activeforeground=FG, font=(FONT, 12),
            ).pack(side="left", padx=6)
        tk.Checkbutton(
            box, text="Avoid look-alike characters (I l 1 O 0 o)", variable=self.avoid, command=self.refresh,
            bg=BG, fg=MUTED, selectcolor=PANEL, activebackground=BG, activeforeground=FG, font=(FONT, 11),
        ).pack(pady=(8, 0))

        self.refresh()

    def _button(self, parent, text, command, bg, fg) -> tk.Button:
        button = tk.Button(
            parent, text=text, command=command, width=11, relief="flat", bd=0, pady=8,
            bg=bg, fg=fg, activebackground=bg, activeforeground=fg, font=(FONT, 12, "bold"),
        )
        button.pack(side="left", padx=5)
        return button

    def settings(self) -> dict:
        return dict(
            upper=self.opts["upper"].get(), lower=self.opts["lower"].get(),
            digits=self.opts["digits"].get(), symbols=self.opts["symbols"].get(),
            avoid_ambiguous=self.avoid.get(),
        )

    def refresh(self) -> None:
        try:
            value = generate(self.length.get(), **self.settings())
        except ValueError as error:
            self.password.set("")
            self.strength.config(text=str(error), fg=COLORS["Weak"])
            return
        self.password.set(value)
        bits = entropy_bits(len(value), pool_size(**self.settings()))
        label = strength_label(bits)
        self.strength.config(text=f"{label} - about {bits:.0f} bits of entropy", fg=COLORS[label])

    def copy(self) -> None:
        value = self.password.get()
        if not value:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(value)
        self.copy_btn.config(text="Copied")
        self.root.after(1500, lambda: self.copy_btn.config(text="Copy"))
        self.root.after(CLEAR_AFTER_MS, lambda: self._clear_clipboard(value))

    def _clear_clipboard(self, value: str) -> None:
        try:
            if self.root.clipboard_get() == value:
                self.root.clipboard_clear()
        except tk.TclError:
            pass


def main() -> None:
    root = tk.Tk()
    PasswordApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
