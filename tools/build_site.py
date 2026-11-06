#!/usr/bin/env python3
"""Build the static storefront (./site) from apps.json + config.json.

    python tools/build_site.py            # build, warn about placeholders
    python tools/build_site.py --strict   # fail while config.json has YOUR_* placeholders (CI)
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site"
e = html.escape

STATUS_LABEL = {"live": "Live", "ready": "Releasing soon", "planned": "Up next"}
DOWNLOADS = [("Windows", "Windows.exe"), ("macOS", "macOS.zip"), ("Linux", "Linux")]

CSS = """
:root{--bg:#fafaf9;--fg:#1c1917;--muted:#78716c;--card:#fff;--line:#e7e5e4;--accent:#0f766e;--accent-fg:#fff;--soft:#f0fdfa}
@media (prefers-color-scheme:dark){:root{--bg:#0c0a09;--fg:#f5f5f4;--muted:#a8a29e;--card:#1c1917;--line:#292524;--accent:#2dd4bf;--accent-fg:#042f2e;--soft:#042f2e}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:var(--accent)}
.wrap{max-width:960px;margin:0 auto;padding:0 20px}
header{padding:56px 0 8px}
h1{font-size:clamp(2rem,5vw,3rem);line-height:1.1;margin:0 0 12px;letter-spacing:-.02em}
.muted{color:var(--muted)}
.lead{color:var(--muted);font-size:1.15rem;max-width:620px;margin:0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px;margin:32px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px;display:flex;flex-direction:column;gap:8px;text-decoration:none;color:inherit}
a.card:hover{border-color:var(--accent)}
.card h3{margin:0;font-size:1.1rem}
.card p{margin:0;color:var(--muted);font-size:.95rem}
.card.planned{opacity:.7}
.badge{align-self:flex-start;font-size:.75rem;padding:2px 10px;border-radius:99px;border:1px solid var(--line);color:var(--muted)}
.badge.live{background:var(--accent);color:var(--accent-fg);border-color:var(--accent)}
.badge.ready{border-color:var(--accent);color:var(--accent)}
.btns{display:flex;flex-wrap:wrap;gap:10px;margin:20px 0}
.btn{display:inline-block;padding:10px 18px;border-radius:10px;border:1px solid var(--line);text-decoration:none;font-weight:600;color:var(--fg);background:var(--card)}
.btn.primary{background:var(--accent);color:var(--accent-fg);border-color:var(--accent)}
.cta{background:var(--soft);border:1px solid var(--line);border-radius:14px;padding:24px;margin:32px 0}
.cta h2{margin-top:0}
pre{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;overflow:auto;font-size:.9rem}
ul.feat{padding-left:20px}
footer{border-top:1px solid var(--line);padding:8px 0 48px;color:var(--muted);font-size:.9rem;margin-top:48px}
"""


def base_url(cfg: dict) -> str:
    return f"https://{cfg['github_user']}.github.io/{cfg['repo']}"


def repo_url(cfg: dict) -> str:
    return f"https://github.com/{cfg['github_user']}/{cfg['repo']}"


def asset_url(cfg: dict, app: dict, suffix: str) -> str:
    tag = f"{app['slug']}-v{app['version']}"
    return f"{repo_url(cfg)}/releases/download/{tag}/{app['slug']}-{suffix}"


def placeholders(cfg: dict) -> list[str]:
    return [k for k, v in cfg.items() if isinstance(v, str) and "YOUR_" in v]


def requirements(root: Path, slug: str) -> list[str]:
    path = root / "apps" / slug / "requirements.txt"
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]


def btn(label: str, url: str, kind: str = "") -> str:
    cls = "btn primary" if kind == "primary" else "btn"
    return f'<a class="{cls}" href="{e(url, quote=True)}" rel="noopener">{e(label)}</a>'


def support_buttons(cfg: dict, app: dict | None = None) -> str:
    out = []
    if app and app.get("buy_url"):
        out.append(btn("Get the Pro pack", app["buy_url"], "primary"))
    elif cfg.get("store_url"):
        out.append(btn("Get the app bundle", cfg["store_url"], "primary"))
    if cfg.get("sponsor_url"):
        out.append(btn("Sponsor on GitHub", cfg["sponsor_url"]))
    if cfg.get("kofi_url"):
        out.append(btn("Buy me a coffee", cfg["kofi_url"]))
    return "".join(out)


def cta(cfg: dict, app: dict | None = None) -> str:
    issue = f"{repo_url(cfg)}/issues/new?template=custom-build.yml"
    links = btn("Request a custom build", issue, "primary")
    if cfg.get("contact_url"):
        links += btn("Message me directly", cfg["contact_url"])
    what = f"a custom version of {e(app['name'])}" if app else "one of these tools"
    return (
        '<section class="cta"><h2>Need this built for your business?</h2>'
        f"<p>I tailor {what} to your branding and workflow, or build something new from scratch. "
        f"Tell me what you need and I will scope it.</p><div class=\"btns\">{links}</div></section>"
    )


def card(app: dict, prefix: str) -> str:
    status = app["status"]
    inner = (
        f'<span class="badge {status}">{STATUS_LABEL[status]}</span>'
        f"<h3>{e(app['name'])}</h3><p>{e(app['tagline'])}</p>"
    )
    if status in ("live", "ready"):
        return f'<a class="card" href="{prefix}apps/{e(app["slug"], quote=True)}.html">{inner}</a>'
    return f'<div class="card planned">{inner}</div>'


def jsonld_for(cfg: dict, app: dict) -> dict:
    data = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": app["name"],
        "description": app.get("description") or app["tagline"],
        "applicationCategory": "GameApplication" if app.get("category") == "Games" else "UtilitiesApplication",
        "operatingSystem": "Windows, macOS, Linux",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "author": {"@type": "Organization", "name": cfg["brand"]},
        "url": f"{base_url(cfg)}/apps/{app['slug']}.html",
    }
    if app.get("version"):
        data["softwareVersion"] = app["version"]
    return data


def page(cfg: dict, title: str, desc: str, body: str, rel_path: str, prefix: str,
         support: str = "", jsonld: dict | None = None) -> str:
    canonical = f"{base_url(cfg)}/{rel_path}"
    ld = ""
    if jsonld:
        safe = json.dumps(jsonld).replace("<", "\\u003c").replace(">", "\\u003e")
        ld = '<script type="application/ld+json">' + safe + "</script>"
    analytics = ""
    if cfg.get("plausible_domain"):
        analytics = (f'<script defer data-domain="{e(cfg["plausible_domain"], quote=True)}" '
                     'src="https://plausible.io/js/script.js"></script>')
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc, quote=True)}">
<link rel="canonical" href="{e(canonical, quote=True)}">
<meta property="og:title" content="{e(title, quote=True)}">
<meta property="og:description" content="{e(desc, quote=True)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{e(canonical, quote=True)}">
<style>{CSS}</style>
{ld}
{analytics}
</head>
<body>
<div class="wrap">
{body}
<footer>
<div class="btns">{support}</div>
<p>&copy; {e(cfg["brand"])} &middot; MIT licensed &middot; <a href="{e(repo_url(cfg), quote=True)}" rel="noopener">Source on GitHub</a> &middot; <a href="{prefix}index.html">All apps</a></p>
</footer>
</div>
</body>
</html>
"""


def index_page(cfg: dict, apps: list[dict]) -> str:
    cards = "".join(card(a, "") for a in apps)
    live = sum(a["status"] == "live" for a in apps)
    body = (
        f'<header><p class="muted">{e(cfg["brand"])}</p><h1>{e(cfg["tagline"])}</h1>'
        f'<p class="lead">{live} live, {len(apps)} in the pipeline. Star the repo to follow new releases.</p>'
        f'<div class="btns">{btn("Star on GitHub", repo_url(cfg), "primary")}</div></header>'
        f'<div class="grid">{cards}</div>{cta(cfg)}'
    )
    desc = f"{cfg['brand']}: free, open-source Python desktop apps. {live} live, {len(apps)} planned."
    return page(cfg, cfg["brand"], desc, body, "", "", support_buttons(cfg))


def app_page(cfg: dict, app: dict, root: Path) -> str:
    slug = app["slug"]
    if app["status"] == "live" and app.get("version"):
        dl = "".join(
            btn(f"Download for {label}", asset_url(cfg, app, suffix), "primary" if i == 0 else "")
            for i, (label, suffix) in enumerate(DOWNLOADS)
        )
        note = f'<p class="muted">Version {e(app["version"])} &middot; free &middot; no account needed</p>'
    else:
        dl = ""
        note = ('<p class="muted">Installers are on the way. You can run it from source right now '
                "(below) or star the repo to be notified of the release.</p>")
    dl += btn("View source", f"{repo_url(cfg)}/tree/main/apps/{slug}")

    feats = "".join(f"<li>{e(f)}</li>" for f in app.get("features", []))
    feats_html = f'<h2>Features</h2><ul class="feat">{feats}</ul>' if feats else ""
    stack = " &middot; ".join(e(s) for s in app.get("stack", []))

    reqs = requirements(root, slug)
    pip = f"pip install -r apps/{slug}/requirements.txt\n" if reqs else ""
    run = (f"git clone {repo_url(cfg)}.git\ncd {cfg['repo']}\n{pip}python apps/{slug}/main.py")

    body = (
        f'<header><p class="muted"><a href="index.html">&larr; All apps</a></p>'
        f'<h1>{e(app["name"])}</h1><p class="lead">{e(app["tagline"])}</p></header>'
        f'<div class="btns">{dl}</div>{note}'
        f'<p>{e(app.get("description", ""))}</p>{feats_html}'
        f'<h2>Run from source</h2><pre>{e(run)}</pre>'
        f'<p class="muted">Requires Python 3.10+. Built with {stack}.</p>'
        f'{cta(cfg, app)}'
    )
    body = body.replace('href="index.html"', 'href="../index.html"')
    title = f"{app['name']} - free Python desktop app | {cfg['brand']}"
    desc = app.get("description") or app["tagline"]
    return page(cfg, title, desc, body, f"apps/{slug}.html", "../",
                support_buttons(cfg, app), jsonld_for(cfg, app))


def build(apps: list[dict], cfg: dict, out: Path = OUT, root: Path = ROOT) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    (out / "apps").mkdir(exist_ok=True)
    written: list[Path] = []

    def emit(rel: str, text: str) -> None:
        path = out / rel
        path.write_text(text, encoding="utf-8")
        written.append(path)

    emit("index.html", index_page(cfg, apps))
    pages = [a for a in apps if a["status"] in ("live", "ready")]
    for app in pages:
        emit(f"apps/{app['slug']}.html", app_page(cfg, app, root))

    urls = [f"{base_url(cfg)}/"] + [f"{base_url(cfg)}/apps/{a['slug']}.html" for a in pages]
    sitemap = "".join(f"<url><loc>{e(u)}</loc></url>" for u in urls)
    emit("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>'
         f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sitemap}</urlset>')
    emit("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {base_url(cfg)}/sitemap.xml\n")

    lines = [f"# {cfg['brand']}", f"> {cfg['tagline']}", "", "## Apps"]
    for a in pages:
        lines.append(f"- [{a['name']}]({base_url(cfg)}/apps/{a['slug']}.html): {a['tagline']}")
    lines += ["", "## Source", f"- [GitHub repository]({repo_url(cfg)}): MIT licensed, issues welcome"]
    emit("llms.txt", "\n".join(lines) + "\n")
    emit(".nojekyll", "")
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="fail on YOUR_* placeholders in config.json")
    args = parser.parse_args()

    apps = json.loads((ROOT / "apps.json").read_text(encoding="utf-8"))["apps"]
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

    missing = placeholders(cfg)
    if missing:
        msg = "config.json still has placeholders: " + ", ".join(missing) + "  (run tools/setup.py)"
        if args.strict:
            print("ERROR:", msg)
            return 1
        print("WARNING:", msg)

    files = build(apps, cfg)
    print(f"Built {len(files)} files into {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
