#!/usr/bin/env python3
"""One-time setup: fills config.json, .github/FUNDING.yml and the issue-form contact link.

    python tools/setup.py --user YOUR_GITHUB_NAME --contact https://your-booking-or-contact-page
        [--repo sushant-labs-apps] [--sponsors] [--kofi HANDLE] [--store https://you.gumroad.com]
        [--plausible yourdomain.com]

Only pass --sponsors once GitHub Sponsors is approved for your account, and only pass
--kofi / --store for pages that exist. Anything you leave out simply does not appear on the site.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--user", required=True, help="GitHub username")
    parser.add_argument("--contact", required=True, help="URL where people can hire/contact you")
    parser.add_argument("--repo")
    parser.add_argument("--sponsors", action="store_true")
    parser.add_argument("--kofi")
    parser.add_argument("--store")
    parser.add_argument("--plausible")
    args = parser.parse_args()

    cfg_path = ROOT / "config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg["github_user"] = args.user
    cfg["contact_url"] = args.contact
    if args.repo:
        cfg["repo"] = args.repo
    if args.sponsors:
        cfg["sponsor_url"] = f"https://github.com/sponsors/{args.user}"
    if args.kofi:
        cfg["kofi_url"] = f"https://ko-fi.com/{args.kofi}"
    if args.store:
        cfg["store_url"] = args.store
    if args.plausible:
        cfg["plausible_domain"] = args.plausible
    cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

    funding = []
    if cfg.get("sponsor_url"):
        funding.append(f"github: [{args.user}]")
    if cfg.get("kofi_url"):
        funding.append(f"ko_fi: {cfg['kofi_url'].rstrip('/').split('/')[-1]}")
    if cfg.get("store_url"):
        funding.append(f'custom: ["{cfg["store_url"]}"]')
    body = "\n".join(funding) if funding else "# Run tools/setup.py with --sponsors / --kofi / --store to enable the Sponsor button."
    (ROOT / ".github" / "FUNDING.yml").write_text(body + "\n", encoding="utf-8")

    issue_cfg = "blank_issues_enabled: false\n"
    if args.contact.startswith("http"):
        issue_cfg += (
            "contact_links:\n"
            "  - name: Private enquiry (budget, NDA, anything not for a public issue)\n"
            f"    url: {args.contact}\n"
            "    about: Issues are public. Use this for anything sensitive.\n"
        )
    else:
        print("Note: GitHub issue forms only accept http(s) contact links, so the private-enquiry link was skipped.")
    (ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml").write_text(issue_cfg, encoding="utf-8")

    print("config.json, FUNDING.yml and issue-form config updated.")
    print("Next: python tools/build_site.py --strict && open site/index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
