# Updating the briefings

This is the runbook for a weekday refresh. Follow it literally. The site has no backend, no API keys, and no paid services. A refresh is a content edit plus `python3 scripts/build.py`.

The audience is a Consulting Systems Engineer at World Wide Technology who supports the U.S. Army tactical team at Aberdeen Proving Ground. Prefer items that change what that person would brief: Army leadership and networks, defense operations, the budget, exploited vulnerabilities, and the OEMs WWT sells.

## When to run

- Run on weekday mornings, U.S. Eastern time. Do not publish a weekend edition unless a person asks.
- Cover roughly the previous weekday through the morning you run. On Monday, cover Friday through Monday morning.
- On Monday, or on the first update of a week when Monday was skipped, run the weekly cleanup under "Retiring items" before you add new items. That pass leaves only the past week of articles in every section file.
- Set `content/site.json` field `updated` to that morning's date (`YYYY-MM-DD`). Set `compiled` in every file under `content/sections/` to the same date. The build fails if they differ.
- The "Last updated" line on the site is that date. Do not bump it unless the content changed.

## Files you may edit

| File | What it is |
| --- | --- |
| `content/site.json` | Site name, tagline, audience, edition date, section order |
| `content/top-signals.json` | The six home-page signals |
| `content/sections/*.json` | One file per section page |
| `content/archive/YYYY-MM-DD.json` | A frozen prior edition |
| `content/schema.json` | The field contract. Change it only when the field rules change |
| `UPDATING.md` | This runbook |

Do not edit `dist/`. The build deletes and recreates it. Do not add a backend, a CMS, an API key, or a paid font host.

Do not rename these section ids, files, or subsection ids. Old links and the home-page anchors depend on them.

| File | Page | Cadence | Subsection ids (do not rename) |
| --- | --- | --- | --- |
| `army.json` | `army.html` | Weekly, Mondays | `leadership`, `modernization`, `contracts`, `network`, `ahead` |
| `dow.json` | `dow.html` | Weekdays | `secwar`, `acquisition`, `goldendome`, `ops` |
| `ai.json` | `ai.html` | Weekdays | `anthropic`, `openai`, `google`, `nvidia`, `local`, `policy`, `defense-ai` |
| `cyber.json` | `cyber.html` | Weekdays | `kev`, `incidents`, `trends` |
| `wwt.json` | `wwt.html` | Weekly, Mondays | `content`, `leaders`, `conferences`, `mapping` |
| `budget.json` | `budget.html` | Weekly, Mondays | `approps`, `ndaa`, `reconciliation` |
| `tech.json` | `tech.html` | Weekly, Mondays | `quantum`, `autonomy`, `compute`, `space` |
| `partners.json` | `partners.html` | Weekly, Mondays | `cisco`, `dell`, `hpe`, `netapp`, `nvidia`, `microsoft`, `paloalto`, `aws`, `google`, `quiet`, `other` |
| `datacenter.json` | `datacenter.html` | Weekdays | `networking`, `capacity`, `power`, `storage` |

`partners.json` subsection `quiet` is the heading "F5 · Intel · VMware". Put a VMware, F5, or Intel item there. If only one of the three had news, write that item and say in `readFirst` which of the three were quiet.

On a weekday that is not the weekly day, still refresh the daily sections (`dow`, `ai`, `cyber`, `datacenter`) and top signals. Leave weekly sections alone unless a fact in them is now wrong, or the daily research checklist has a new qualifying item for that section. Add that item only. On Monday, refresh every section and run the weekly cleanup.

## What an item looks like

Match `content/schema.json` definition `item`. Example:

```json
{
  "id": "safepay-2026-10-20",
  "subsection": "trends",
  "date": "2026-10-20",
  "dateLabel": "Oct 20–21",
  "headline": "SafePay advisory: about 600 victims, initial access through edge devices",
  "summary": "Two to four sentences. Only facts you read in the sources. Name the organization, the date, and the number as the source stated it.",
  "sources": [
    {
      "name": "CISA advisory",
      "url": "https://www.cisa.gov/news-events/cybersecurity-advisories/aa26-293a"
    }
  ]
}
```

Rules:

- `id` is a stable slug, unique inside the file. Reuse the same id if you keep an item. Do not invent a second id for the same story.
- `subsection` must be one of that file's subsection ids.
- `date` is the publication date, `YYYY-MM-DD`. If a story spans days, use the latest day and put the span in `dateLabel` (`Oct 20–21`).
- `headline` is one sentence a reader can scan. No clickbait, no all caps.
- `summary` is two to four sentences. Attribute claims ("CISA said", "Dell announced"). Do not add a number, a name, a date, or a cause that you did not read in a source you opened.
- `sources` is one to four objects. `url` must be `https://`. `name` is the publisher (`Army.mil`, `CISA`, `WWT`), not the headline.
- `tag` is optional. Omit it for ordinary news. Use `"context"` for a standing fact that is still true, whose `date` is inside the past 7 days, and that is older than this edition's shorter window (acting leaders, the CR end date, an award that is still the current vehicle). The weekly cleanup removes a `context` item once its `date` is older than 7 days. Use `"inference"` only in `wwt.json`, only in subsection `mapping`. The build rejects `inference` anywhere else.
- Order items inside a subsection with the most important first, not strictly by date. The build keeps file order.
- A subsection with no items is valid. The page prints "No items this edition." Do not write a fake item that says nothing happened.

## How many items

Count items in the file, including context and inference.

| Section | Keep |
| --- | --- |
| `dow`, `ai`, `cyber`, `datacenter` | 6 to 12 |
| `army`, `wwt`, `budget`, `tech`, `partners` | 4 to 12 |
| Each subsection | 0 to 4 |
| `content/top-signals.json` | exactly 6 |

Do not pad to the maximum. An empty HPE or Space subsection is correct when you found nothing. Prefer one sourced item over two weak ones. The weekly cleanup can leave a section under the low end of its range. Leave it short. Do not add a filler item to climb back to 4 or 6.

Context cap: at most 2 items tagged `context` per section. Inference cap: at most 2, and only on `wwt` mapping.

## Daily research checklist

These three sites are additional sources only. On every weekday run, keep searching the web broadly and keep searching every existing source for every section (Army, DOW, AI, Cyber, WWT, Budget, Tech, Partners, and DC/NET). Never limit research to these three sites. A section with nothing from these three sites still gets the same broad search it had before.

Scrape the three sites in addition to that search. Monday's scrape covers Friday through Monday morning, so the weekend is included then. Do not publish a weekend edition only to scrape them.

- https://www.federalnewsnetwork.com
- https://www.einnews.com
- https://www.tomshardware.com

From these three sites, keep a hit only when it ties into the Army or DoW/DoD, or when it is a new AI topic. Place it in the best-fitting section: Army (`army.json`), DOW (`dow.json`), AI (`ai.json`), Cyber (`cyber.json`), WWT (`wwt.json`), Budget (`budget.json`), Tech (`tech.json`), Partners (`partners.json`), or DC/NET (`datacenter.json`). Use one of that file's existing subsection ids. Items found in the broad search follow the same placement rules and are not filtered down to what these three sites cover.

Each item's link must be the original article. `sources[].url` is the `https://` URL of that article. It must pass `python3 scripts/check_links.py`. A homepage, a section front, or a search results page is not a source.

`einnews.com` is an aggregator. When the lead came from there, open the EIN page, follow it to the original publisher's article, and cite that publisher's name and URL. If you cannot open the original article, skip the item. Do not cite the EIN News wrapper, and do not invent a publisher, an item, or a link.

Never invent an item, a quote, a dollar figure, or a URL. A scrape hit you did not open and read is not a source.

## Sourcing

Never invent an item, a quote, a dollar figure, or a URL.

1. Search the web broadly for every section. Start with primary sources: `army.mil`, `war.gov`, `cisa.gov`, `congress.gov`, company newsrooms (`wwt.com`, `nvidia.com`, vendor blogs), then `Breaking Defense`, `DefenseScoop`, `Stars and Stripes`, Reuters, and the major tech press, then whatever else the day's story requires. The three sites in the daily research checklist are additional sources only. Scrape them too, on every run. Never limit research to those three sites, and never skip a section because they had nothing on it.
2. Open the URL and read it before you cite it. A search snippet is not a source.
3. If the page does not load, do not cite it. A bot wall (HTTP 403) is acceptable only when a normal fetch of the article body succeeded and the URL is the canonical article URL, not a search redirect.
4. Every factual clause in `summary` must be supported by one of that item's sources. If you are connecting two stories, tag the item `inference` and only do that on the WWT mapping subsection.
5. Do not cite this repository, the old Perplexity site, or another briefing item as a source. Cite the underlying article.
6. Skip rumors, unsourced social posts, and pages that are only a headline.

## Retiring items

Before adding the new edition:

1. Read `content/site.json` `updated`. Call that date PREV.
2. If `content/archive/PREV.json` does not exist, create it from the current top signals. Shape:

```json
{
  "date": "PREV",
  "title": "October 22, 2026",
  "note": "Top signals from the edition replaced on the next weekday.",
  "signals": [
    {
      "label": "DOW",
      "dateLabel": "Oct 21",
      "headline": "Same headline as the live signal",
      "sources": [{ "name": "The National", "url": "https://..." }]
    }
  ]
}
```

Copy the six live signals. For each, look up `item` in the section file and copy that item's `sources` onto the archive signal. Archive signals link to publishers, not to `dow.html#ops`, because those anchors will move.

3. Then edit the live files. On Monday, or on the first update of the week, run the weekly cleanup below before you add items.

### Weekly cleanup

On Monday, or on the first update of a week when Monday was skipped, remove every item older than 7 days from all section data files (`content/sections/*.json`). Leave `content/archive/` as it is. Those editions stay frozen. After this pass, the live site shows only the past week of articles.

Age is the item's published date. `content/schema.json` definition `item` requires `date` (`YYYY-MM-DD`), and `scripts/build.py` rejects an item that omits it. Every current item already has `date`, so leave the schema unchanged. Do not age an item from `compiled`, `covers`, `dateLabel`, or the archive edition where the story first appeared.

Compare `date` with the new `content/site.json` `updated` you are about to publish. Remove the item when `date` is earlier than 7 days before `updated`. An item dated exactly 7 days before `updated` stays. Example: an `updated` of `2026-10-26` removes `date` on or before `2026-10-18` and keeps `2026-10-19` through `2026-10-26`. When `dateLabel` is a span, `date` is the latest day, and that is the day you age.

This replaces the old rule that dropped an item only after 14 days, and the exception that kept a re-checked `context` item past that window. `context` and `inference` items older than 7 days come out on this pass, including a standing fact that is still true. Inside the 7-day window, keep a `context` item only while it is still the standing fact. When a secretary is confirmed, delete the "acting" context item instead of leaving both.

The count ranges in "How many items" do not keep an older item on the page. If the cleanup leaves a section under its usual minimum, leave it short. After the deletions, point `content/top-signals.json` only at items that remain, and change `readFirst` so it does not describe a removed story.

On a later weekday in the same week, do not repeat the full-file purge. Still drop an item early when one of the rules below applies.

Also drop a live item when any of these is true:

- A newer item in the same subsection supersedes it (a nomination was confirmed, a bill passed, a patch shipped and the KEV due date passed with no new exploitation news).
- You would otherwise exceed the counts above. Drop the oldest untagged item first.

Kev and incident items: remove a vulnerability item once it is no longer the current patching priority, usually after the next edition unless exploitation is still the day's news. Do not let the cyber page become a backlog of old CVEs. The weekly cleanup is the backstop: a KEV item older than 7 days does not stay.

## Top signals

`content/top-signals.json` has exactly six objects. Each object:

- `section` is a section id.
- `item` is an `id` that exists in that section file.
- `href` is `{file}.html#{subsection}` for that item. Example: item `safepay-2026-10-20` in subsection `trends` of `cyber.json` has `"href": "cyber.html#trends"`.
- `label` is the short nav label (`ARMY`, `DOW`, `AI`, `CYBER`, `WWT`, `BUDGET`, `TECH`, `PARTNERS`, `DC/NET`).
- `headline` matches the story. It can be shorter than the item headline. It must not claim something the item does not.

Choose the six a reader should see before anything else. Spread them across sections when the news supports it. Do not use six signals from one section. The build checks that `href` and `item` agree.

## Read-first note

Each section has `readFirst`, one short paragraph. Say the date window, what is new, and what you looked for and did not find ("No new NETCOM release"). Do not hide an empty search.

`covers` is the human date window, for example `Oct 14–22, 2026`.

## Rebuild

From the repository root, with Python 3.11 or newer (the standard library only):

```bash
python3 scripts/build.py
```

The script writes `dist/` and exits non-zero on a contract violation. Fix the JSON. Do not hand-edit HTML in `dist/`.

Check links. This step is required before you finish. It uses only the Python standard library:

```bash
python3 scripts/check_links.py
```

Run it after `scripts/build.py`. It fetches every `https` source URL in `content/` (including the archive) and checks every relative link and anchor in `dist/`. It exits non-zero on a 404 or 410, on a redirect to a site homepage or a parent section index, on a non-https source, and on an internal link that misses its file or anchor. Publisher bot-walls (401, 403, or a timeout) are printed as `blocked` and do not fail the run; open each of those in a browser and confirm the article before you keep the URL. A homepage or section-front URL is not a source. If you cannot find the exact article, delete the item.

Preview:

```bash
python3 -m http.server 4173 -d dist
```

Open `http://127.0.0.1:4173/`. Click every nav item, one top signal, one source link, and the archive. Check a phone-width window. Internal links are relative (`army.html`, `assets/site.css`, `archive/index.html`) so the site works at `https://deebogem504-dev.github.io/calvin-briefings/` without a base tag.

## Deploy

GitHub Actions deploys on a push to `main` only. The workflow is `.github/workflows/pages.yml`. It checks out the repo, runs `actions/configure-pages@v5` with `enablement: true`, runs `python3 scripts/build.py`, uploads `dist/` with `actions/upload-pages-artifact@v4`, and deploys with `actions/deploy-pages@v4`.

Do not push to `main` from an unattended refresh unless the repository owner has said this branch is approved to publish. Open a pull request instead.

`enablement: true` cannot create the Pages site with the default `GITHUB_TOKEN`. The owner turns Pages on once, in the repo settings, source "GitHub Actions". After that, the configure step only reads the existing site and the deploy job publishes. See `README.md`.

## Checklist before you finish

- [ ] Searched the web broadly and every existing source for every section. Also scraped the three additional sites (`federalnewsnetwork.com`, `einnews.com`, `tomshardware.com`) and did not limit research to them. Army, DoW/DoD, and new AI items from those sites are in the best-fitting section. EIN leads cite the original publisher article. No invented items or links
- [ ] On Monday, or the first update of the week, every section item whose `date` is more than 7 days before `updated` was removed. Archive files were left in place
- [ ] `updated` and every `compiled` are the same date
- [ ] Previous edition copied to `content/archive/YYYY-MM-DD.json` if it was not already there
- [ ] Counts are inside the ranges above, or an empty subsection is explicit
- [ ] Every new URL was opened and matches the summary
- [ ] No `inference` outside `wwt.json` mapping
- [ ] At most two `context` items per section
- [ ] Six top signals, each `href` pointing at a real item
- [ ] Subsection ids unchanged
- [ ] `python3 scripts/build.py` exits 0
- [ ] `python3 scripts/check_links.py` exits 0, and every `blocked` URL was opened and matches the item
- [ ] Home, one section, and the archive render, including on a narrow viewport
