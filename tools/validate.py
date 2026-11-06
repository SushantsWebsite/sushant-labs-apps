#!/usr/bin/env python3
"""Validate apps.json against the apps/ folder. Exit code 1 on any problem."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ("slug", "name", "tagline", "status")
STATUSES = {"live", "ready", "planned"}
SLUG_RE = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
SEMVER_RE = re.compile(r"\d+\.\d+\.\d+")


def check(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    data = json.loads((root / "apps.json").read_text(encoding="utf-8"))
    seen: set[str] = set()
    for app in data["apps"]:
        slug = app.get("slug", "?")
        for key in REQUIRED:
            if not app.get(key):
                errors.append(f"{slug}: missing '{key}'")
        if not SLUG_RE.fullmatch(slug):
            errors.append(f"{slug}: slug must be lowercase letters, digits and dashes")
        if slug in seen:
            errors.append(f"{slug}: duplicate slug")
        seen.add(slug)

        status = app.get("status")
        if status not in STATUSES:
            errors.append(f"{slug}: status must be one of {sorted(STATUSES)}")
        if status in ("live", "ready"):
            for name in ("main.py", "README.md"):
                if not (root / "apps" / slug / name).exists():
                    errors.append(f"{slug}: apps/{slug}/{name} is missing")
            if not app.get("description"):
                errors.append(f"{slug}: needs a 'description' for its page")
        if status == "live" and not SEMVER_RE.fullmatch(app.get("version", "")):
            errors.append(f"{slug}: live apps need a version like 1.0.0")
    return errors


def main() -> int:
    errors = check()
    for line in errors:
        print("ERROR:", line)
    if not errors:
        print("apps.json OK")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
