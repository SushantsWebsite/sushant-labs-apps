#!/usr/bin/env python3
"""Scaffold a new app (or fill in a planned one) in apps/<slug>/.

    python tools/new_app.py file-organizer
    python tools/new_app.py "Brand New Idea" --tagline "One line pitch"
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MAIN = '''"""{name} - Sushant Labs."""
import tkinter as tk

from logic import greet


def main() -> None:
    root = tk.Tk()
    root.title("{name}")
    root.geometry("420x260")
    tk.Label(root, text=greet("{name}"), font=("Helvetica", 18)).pack(expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()
'''

LOGIC = '''"""Pure logic for {name}. Keep it free of tkinter so it can be unit-tested."""


def greet(name: str) -> str:
    return f"{{name}} is ready to build."
'''

README = """# {name}

{tagline}

## Run

    python main.py

## Build a standalone app

    pip install pyinstaller
    pyinstaller --onefile --windowed main.py
"""


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="slug of a planned app, or a new app name")
    parser.add_argument("--tagline", default="")
    args = parser.parse_args()

    slug = slugify(args.name)
    path = ROOT / "apps.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    entry = next((a for a in data["apps"] if a["slug"] == slug), None)

    if entry is None:
        entry = {
            "slug": slug,
            "name": args.name.strip(),
            "tagline": args.tagline or "Describe this app in one line.",
            "status": "planned",
            "category": "Utilities",
            "stack": ["Python", "Tkinter"],
        }
        data["apps"].append(entry)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Added '{slug}' to apps.json")

    folder = ROOT / "apps" / slug
    if (folder / "main.py").exists():
        print(f"ERROR: apps/{slug}/main.py already exists")
        return 1
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "main.py").write_text(MAIN.format(name=entry["name"]), encoding="utf-8")
    (folder / "logic.py").write_text(LOGIC.format(name=entry["name"]), encoding="utf-8")
    (folder / "README.md").write_text(README.format(name=entry["name"], tagline=entry["tagline"]), encoding="utf-8")

    print(f"Scaffolded apps/{slug}/  ->  build it, add 'description' + 'features' to apps.json,")
    print(f"then: python tools/ship.py {slug} 1.0.0 --push")
    return 0


if __name__ == "__main__":
    sys.exit(main())
