# Calvin's Army & Tech Briefings

A static weekday briefing for Army, defense, AI, cyber, and infrastructure news. It replaces the earlier site at [calvin-briefings.pplx.app](https://calvin-briefings.pplx.app/), which stopped updating on 13 October 2026.

The pages are the same nine sections, with the same anchors: Army, Department of War, AI, Cyber, WWT, Budget, Tech, Partners, and Data Center & Networking. Content lives in JSON. Layout is generated.

Intended address after GitHub Pages is turned on: `https://deebogem504-dev.github.io/calvin-briefings/`

## Preview locally

Python 3.11 or newer. No packages to install.

```bash
python3 scripts/build.py
python3 -m http.server 4173 -d dist
```

Open `http://127.0.0.1:4173/`.

Links are relative, so the same files work at the site root or under `/calvin-briefings/`.

## How a weekday update works

Edit the JSON in `content/`, then rebuild. The procedure, item counts, and retirement rules are in [UPDATING.md](UPDATING.md). The field contract is [content/schema.json](content/schema.json).

`content/site.json` field `updated` is the "Last updated" date on the site.

## Turn on GitHub Pages (one time, after this is merged to `main`)

The workflow `.github/workflows/pages.yml` builds `dist/` and deploys it on every push to `main`. It does not run on pull requests.

1. Merge the approved pull request to `main`.
2. In the repository on GitHub, open **Settings → Pages**.
3. Under **Build and deployment**, set **Source** to **GitHub Actions**.
4. If the first Actions run failed on the "Configure GitHub Pages" step, re-run it after step 3.

`actions/configure-pages` is called with `enablement: true`, which tries to create the Pages site if it does not exist. GitHub does not let the default workflow token create a Pages site. Turning the source to GitHub Actions once is the step that unblocks deploy. Later pushes only need the workflow, which already has `pages: write` and `id-token: write`.

Do not add a personal access token unless you specifically want the workflow itself to create the Pages site. A normal deploy does not need one.

The published URL is `https://deebogem504-dev.github.io/calvin-briefings/`.
