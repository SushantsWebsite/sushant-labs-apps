#!/usr/bin/env python3
"""Make an app live: mark it live in apps.json, commit, tag, and (optionally) push.

    python tools/ship.py pomodoro 1.0.0              # commit + tag locally
    python tools/ship.py pomodoro 1.0.0 --push       # ...and push, which triggers the Release workflow
    python tools/ship.py pomodoro 1.0.0 --dry-run    # show what would happen

Pushing the tag `pomodoro-v1.0.0` builds Windows/macOS/Linux binaries on GitHub and
attaches them to a Release. The storefront redeploys itself once the assets exist.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str], dry: bool) -> None:
    print("$", " ".join(cmd))
    if not dry:
        subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("slug")
    parser.add_argument("version", help="semantic version, e.g. 1.0.0")
    parser.add_argument("--push", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not re.fullmatch(r"\d+\.\d+\.\d+", args.version):
        print("ERROR: version must look like 1.0.0")
        return 1

    path = ROOT / "apps.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    app = next((a for a in data["apps"] if a["slug"] == args.slug), None)
    if app is None:
        print(f"ERROR: '{args.slug}' is not in apps.json")
        return 1
    if not (ROOT / "apps" / args.slug / "main.py").exists():
        print(f"ERROR: apps/{args.slug}/main.py does not exist")
        return 1
    if not app.get("description"):
        print(f"ERROR: add a 'description' (and 'features') for {args.slug} in apps.json first")
        return 1

    app["status"], app["version"] = "live", args.version
    if not args.dry_run:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    tag = f"{args.slug}-v{args.version}"
    try:
        run(["git", "add", "-A"], args.dry_run)
        run(["git", "commit", "-m", f"Release {args.slug} v{args.version}"], args.dry_run)
        run(["git", "tag", tag], args.dry_run)
        if args.push:
            run(["git", "push", "origin", "HEAD"], args.dry_run)
            run(["git", "push", "origin", tag], args.dry_run)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"ERROR: git step failed ({exc}). apps.json was updated; fix git and rerun the failed command.")
        return 1

    if not args.push:
        print(f"\nNext: git push origin HEAD && git push origin {tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
