# Revenue map

Honest expectation: free desktop utilities rarely earn much from direct sales or tips. The compounding assets are the audience and the lead funnel. Streams are ordered by expected value for someone who sells services.

## 1. Custom builds (the main engine)

Every app page and the home page end with a "Request a custom build" box that opens the GitHub issue form (`custom-build.yml`) plus your direct contact link. The apps are your portfolio; the CTA turns visitors into scoped jobs for the drop-servicing business.

Offer ladder (my suggested starting points, not market data; test and adjust):

| Offer | Starting price |
|---|---|
| Rebrand an existing app (logo, colours, name) | $49 to $99 |
| Add a feature to an existing app | $149 to $299 |
| New custom tool from scratch | $499 and up |

Reply within a day, confirm scope in writing, take a deposit before starting.

Make the pages findable by AI answer engines: the site already ships `llms.txt`, `sitemap.xml`, canonical URLs and `SoftwareApplication` structured data. Use your own apps as the proof case for your AEO work.

## 2. Pay-what-you-want bundles

Sell a convenience pack on Gumroad, Lemon Squeezy or Ko-fi Shop: source code, a short build guide and the packaged installers. Set the price to "pay what you want" with a small suggested amount. The code stays MIT-licensed and free on GitHub; people pay for convenience and to say thanks.

- Per app: put the product link in that app's `buy_url` in `apps.json`.
- Store-wide: pass `--store URL` to `tools/setup.py`.
- Check that the platform supports payouts to your country before you commit to one.

## 3. Sponsors and tips

- GitHub Sponsors: apply on GitHub, then rerun `tools/setup.py ... --sponsors`. It needs approval and is not available everywhere, so check your region first.
- Ko-fi: `--kofi YOURHANDLE`. Needs no approval.

Buttons only render when the link is set, so there are never dead buttons.

## 4. Audience (feeds everything above)

Post every release with a 15-second screen recording. Templates and a 5-day cadence are in `launch/post-templates.md`. Put the storefront link in every bio.

## 5. Later: a Pro tier

Only when one app proves demand (suggested trigger: 100+ downloads in a week, or three unprompted feature requests). Then sell a Pro build through Gumroad or Lemon Squeezy license keys and put the link in that app's `buy_url`. Do not build licensing before demand exists.

## Tracking

Release downloads per app:

    gh api repos/OWNER/REPO/releases --jq '.[] | {tag: .tag_name, downloads: ([.assets[].download_count] | add)}'

Also watch GitHub **Insights > Traffic** for views and clones, and set `plausible_domain` in `config.json` if you want page analytics. Count custom-build issues and direct messages as your real conversion number.

## Weekly loop

| Day | Move |
|---|---|
| Mon | Pick the app (`new_app.py`), build it in 25 to 60 minutes |
| Tue | Polish, write description and features, `ship.py --push` |
| Wed | Post the launch with the recording |
| Thu | Answer comments and issues, reply to every custom-build request |
| Fri | Check downloads and leads, choose next week's app |
