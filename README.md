# Sushant Labs Apps

One repo that turns 25-minute Python builds into live products:

    build app  ->  ship.py  ->  GitHub Release (Win/macOS/Linux)  ->  storefront site  ->  revenue
                                                                          ^                    |
                                                          build-in-public posts <---------------

| Piece | What it does |
|---|---|
| `apps/<slug>/` | One folder per app: `main.py` (UI), `logic.py` (testable logic), `README.md` |
| `apps.json` | The catalog. Drives the site, validation and releases |
| `tools/new_app.py` | Scaffolds a new app folder in one command |
| `tools/ship.py` | Marks an app live, commits, tags, pushes |
| `.github/workflows/release.yml` | On tag: builds Windows, macOS and Linux binaries and publishes a Release |
| `.github/workflows/pages.yml` | Builds and deploys the storefront to GitHub Pages |
| `.github/workflows/ci.yml` | Compiles, validates the catalog and runs the tests on every push |
| `streamlit_app.py` | Read-only browser for exploring this repository's files |
| `.github/ISSUE_TEMPLATE/custom-build.yml` | Turns visitors into custom-build leads |
| `REVENUE.md` | The money map and a weekly loop |
| `launch/post-templates.md` | Ready-to-paste build-in-public posts |

Included and working: **Focus Timer**, **Password Generator**, **Typing Speed Test**. The other 12 ideas are in the catalog as "Up next".

## Browse this repository with Streamlit

Run locally from the repository root:

    pip install -r requirements.txt
    streamlit run streamlit_app.py

The browser shows a navigable file tree, supports filename/path search and an apps-only filter, renders README files as Markdown, and displays other text files with syntax highlighting. It reads from the public GitHub repository and does not execute repository files.

To host it on Streamlit Community Cloud, create an app from this repository and set `streamlit_app.py` as the entry point.

## Go live in about 10 minutes

1. Create an empty GitHub repo named `sushant-labs-apps` (public, no README).
2. Fill the config, from this folder:

       python tools/setup.py --user YOUR_GITHUB_NAME --contact https://your-booking-or-contact-page

   Add `--sponsors` only after GitHub Sponsors is approved, `--kofi HANDLE` and `--store URL` when those pages exist.
3. Add a description and features to any app you ship (the three starters already have them), then check locally:

       python tools/build_site.py --strict
       python -m unittest discover -s tests

4. Push:

       git init && git add -A && git commit -m "Launch Sushant Labs apps"
       git branch -M main
       git remote add origin https://github.com/YOUR_GITHUB_NAME/sushant-labs-apps.git
       git push -u origin main

5. On GitHub: **Settings > Pages > Source: GitHub Actions**. Your storefront appears at `https://YOUR_GITHUB_NAME.github.io/sushant-labs-apps/`.
6. Ship the first app:

       python tools/ship.py pomodoro 1.0.0 --push

   About five minutes later the Release has Windows, macOS and Linux downloads and the site shows the buttons.

## The weekly loop

    python tools/new_app.py file-organizer      # scaffold (or fill in a planned app)
    # build it in Visual Studio, record a 15-second clip
    # add "description" + "features" to its entry in apps.json
    python tools/ship.py file-organizer 1.0.0 --push
    # post using launch/post-templates.md

## Notes

- Each app's `logic.py` stays free of tkinter so it can be unit-tested. Put new logic there.
- If an app needs packages, add `apps/<slug>/requirements.txt`; the release workflow and the site pick it up.
- Downloaded installers are unsigned, so Windows SmartScreen and macOS Gatekeeper will warn first-time users. Say so in your launch post ("More info > Run anyway"), or add code signing later.
- Money setup lives in [REVENUE.md](REVENUE.md).
