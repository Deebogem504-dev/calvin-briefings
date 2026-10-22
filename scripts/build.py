#!/usr/bin/env python3
"""Build the static briefings site from content/*.json into dist/.

No third-party packages. Run from the repository root:

    python3 scripts/build.py
"""

from __future__ import annotations

import html
import json
import shutil
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
SECTIONS_DIR = CONTENT / "sections"
ARCHIVE_DIR = CONTENT / "archive"
SRC = ROOT / "src"
DIST = ROOT / "dist"

TAGS = {None, "context", "inference"}
WEEKDAYS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)
MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


class BuildError(Exception):
    pass


def load_json(path: Path):
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise BuildError(f"{path}: invalid JSON ({exc})") from exc


def require(obj, key, path, kind=None):
    if not isinstance(obj, dict) or key not in obj:
        raise BuildError(f"{path}: missing {key}")
    value = obj[key]
    if kind is str and (not isinstance(value, str) or not value.strip()):
        raise BuildError(f"{path}: {key} must be a non-empty string")
    if kind is list and not isinstance(value, list):
        raise BuildError(f"{path}: {key} must be a list")
    return value


def parse_iso(value: str, path: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise BuildError(f"{path}: {value} is not YYYY-MM-DD") from exc


def long_date(value: date) -> str:
    return f"{WEEKDAYS[value.weekday()]}, {MONTHS[value.month - 1]} {value.day}, {value.year}"


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def check_url(url: str, path: str) -> None:
    if not isinstance(url, str) or not url.startswith("https://"):
        raise BuildError(f"{path}: source url must be an absolute https URL")


def logo_svg() -> str:
    return """<svg class="logo" viewBox="0 0 48 48" fill="none" aria-hidden="true">
<path d="M24 3 L42 10 V24 C42 34 34 41.5 24 45 C14 41.5 6 34 6 24 V10 Z" stroke="currentColor" stroke-width="2.5" stroke-linejoin="round"/>
<path d="M14 21 L24 15 L34 21" stroke="var(--accent)" stroke-width="3" stroke-linecap="square"/>
<path d="M14 29 L24 23 L34 29" stroke="var(--accent)" stroke-width="3" stroke-linecap="square"/>
<circle cx="24" cy="35.5" r="2.4" fill="currentColor"/></svg>"""


def asset(depth: int, name: str) -> str:
    return f"{'../' * depth}assets/{name}"


def page_href(depth: int, filename: str) -> str:
    return f"{'../' * depth}{filename}"


def shell(title: str, description: str, body: str, depth: int, current: str | None) -> str:
    nav_links = []
    for section in SECTIONS:
        href = page_href(depth, section["file"])
        cls = "on" if section["file"] == current else ""
        nav_links.append(
            f'<a href="{esc(href)}" class="{cls}">{esc(section["nav"])}</a>'
        )
    home = page_href(depth, "index.html")
    desc = esc(description)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{desc}">
<link rel="icon" href="{esc(asset(depth, 'favicon.svg'))}">
<link rel="stylesheet" href="{esc(asset(depth, 'site.css'))}">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="bar">
<div class="bar-inner">
<a class="brand" href="{esc(home)}">{logo_svg()}<span>{esc(SITE['shortName'])}<small>Army &amp; tech briefings</small></span></a>
<button class="theme" type="button" id="theme-toggle">Dark</button>
</div>
<nav class="nav wrap" aria-label="Briefings">{''.join(nav_links)}</nav>
</header>
<main id="main" class="wrap">
{body}
</main>
<footer class="foot">
<div class="wrap">
<p>Static briefing. Every reported item links to a public source. Context is a standing fact still in force. Inference, used on the WWT page, is analysis tied to those sources, not a new report.</p>
<p>Last updated {esc(UPDATED_LABEL)}. Built from the files in <code>content/</code>.</p>
</div>
</footer>
<script src="{esc(asset(depth, 'theme.js'))}"></script>
</body>
</html>
"""


def render_sources(sources: list) -> str:
    parts = []
    for source in sources:
        parts.append(
            f'<a href="{esc(source["url"])}">{esc(source["name"])}</a>'
        )
    return '<div class="src">' + " · ".join(parts) + "</div>"


def render_item(item: dict) -> str:
    tag = item.get("tag")
    tag_html = f'<span class="tag">{esc(tag.upper())}</span>' if tag else ""
    return f"""<article class="item">
<div class="idate">{esc(item["dateLabel"])}</div>
<div>
<h3>{esc(item["headline"])}{tag_html}</h3>
<p>{esc(item["summary"])}</p>
{render_sources(item["sources"])}
</div>
</article>"""


def render_section_page(section: dict) -> str:
    chips = []
    blocks = []
    by_sub = {sub["id"]: [] for sub in section["subsections"]}
    for item in section["items"]:
        by_sub[item["subsection"]].append(item)
    for sub in section["subsections"]:
        chips.append(
            f'<a class="chip" href="#{esc(sub["id"])}">{esc(sub["title"])}</a>'
        )
        rows = "".join(render_item(item) for item in by_sub[sub["id"]])
        if not rows:
            rows = '<p class="empty">No items this edition.</p>'
        blocks.append(
            f'<section class="sec" id="{esc(sub["id"])}"><h2><span class="pip"></span>{esc(sub["title"])}</h2>{rows}</section>'
        )
    compiled = long_date(parse_iso(section["compiled"], section["file"]))
    body = f"""<a class="back" href="index.html">All briefings</a>
<p class="kicker"><span class="lbl">{esc(section["kicker"])}</span><span>{esc(section["cadence"])}</span></p>
<h1>{esc(section["title"])}</h1>
<p class="meta">Compiled {esc(compiled)}. Covers {esc(section["covers"])}. {esc(section["description"])}</p>
<div class="chips">{''.join(chips)}</div>
<aside class="note"><b>READ FIRST</b> {esc(section["readFirst"])}</aside>
{''.join(blocks)}
"""
    title = f"{section['title']} · {SITE['shortName']}"
    return shell(title, section["description"], body, 0, section["file"])


def render_home() -> str:
    signals = []
    for signal in TOP["signals"]:
        signals.append(
            f'''<a class="sig" href="{esc(signal["href"])}"><span class="slbl">{esc(signal["label"])}</span><span class="sdate">{esc(signal["dateLabel"])}</span><span class="shl">{esc(signal["headline"])}</span></a>'''
        )
    cards = []
    for section in SECTIONS:
        count = len(section["items"])
        noun = "item" if count == 1 else "items"
        cards.append(
            f'''<a class="card" href="{esc(section["file"])}"><span class="navlabel">{esc(section["nav"])}</span><strong>{esc(section["title"])}</strong><p>{esc(section["description"])}</p><span class="cad">{esc(section["cadence"])} · {count} {noun}</span></a>'''
        )
    body = f"""<p class="stamp">Last updated {esc(UPDATED_LABEL)}</p>
<p class="kicker"><span class="lbl">Weekday briefing</span></p>
<h1>{esc(SITE["name"])}</h1>
<p class="lede">{esc(SITE["tagline"])} {esc(SITE["audience"])}</p>
<section class="sec" id="signals"><h2><span class="pip"></span>Top signals</h2>
<div class="sigs">{''.join(signals)}</div></section>
<section class="sec" id="briefings"><h2><span class="pip"></span>Briefings</h2>
<div class="cards">{''.join(cards)}</div></section>
<p class="meta"><a href="archive/index.html">Earlier editions</a></p>
"""
    return shell(SITE["name"], SITE["tagline"], body, 0, None)


def render_archive_index(editions: list[dict]) -> str:
    rows = []
    for edition in editions:
        rows.append(
            f'''<a class="sig" href="{esc(edition["slug"])}"><span class="slbl">ARCHIVE</span><span class="sdate">{esc(edition["dateLabel"])}</span><span class="shl">{esc(edition["title"])}</span></a>'''
        )
    if not rows:
        rows.append('<p class="empty">No earlier editions yet.</p>')
    body = f"""<a class="back" href="../index.html">All briefings</a>
<p class="kicker"><span class="lbl">Archive</span></p>
<h1>Earlier editions</h1>
<p class="lede">Each weekday run files the previous edition here before replacing the live pages. The October 13 entry is the last compilation of the previous site.</p>
<div class="sigs">{''.join(rows)}</div>
"""
    return shell(f"Archive · {SITE['shortName']}", "Earlier briefing editions.", body, 1, None)


def render_archive_edition(edition: dict) -> str:
    rows = []
    for signal in edition["signals"]:
        sources = render_sources(signal["sources"])
        rows.append(
            f'''<article class="item"><div class="idate">{esc(signal["dateLabel"])}</div><div><h3><span class="slbl">{esc(signal["label"])}</span> {esc(signal["headline"])}</h3>{sources}</div></article>'''
        )
    body = f"""<a class="back" href="index.html">All earlier editions</a>
<p class="stamp">{esc(edition["dateLabel"])}</p>
<h1>{esc(edition["title"])}</h1>
<p class="lede">{esc(edition["note"])}</p>
{''.join(rows)}
"""
    return shell(
        f"{edition['title']} · {SITE['shortName']}",
        edition["note"],
        body,
        1,
        None,
    )


def validate_sources(sources, path: str) -> None:
    if not isinstance(sources, list) or not sources:
        raise BuildError(f"{path}: at least one source is required")
    for index, source in enumerate(sources):
        where = f"{path} source {index + 1}"
        if not isinstance(source, dict):
            raise BuildError(f"{where}: must be an object")
        require(source, "name", where, str)
        check_url(require(source, "url", where, str), where)


def validate_section(section: dict, path: Path) -> None:
    for key in (
        "id",
        "file",
        "nav",
        "kicker",
        "cadence",
        "title",
        "description",
        "compiled",
        "covers",
        "readFirst",
    ):
        require(section, key, path, str)
    if section["id"] != path.stem:
        raise BuildError(f"{path}: id must match filename")
    if section["file"] != f"{section['id']}.html":
        raise BuildError(f"{path}: file must be {section['id']}.html")
    parse_iso(section["compiled"], str(path))
    if section["compiled"] != SITE["updated"]:
        raise BuildError(
            f"{path}: compiled is {section['compiled']} but site.updated is {SITE['updated']}. Set them to the same edition date."
        )
    subsections = require(section, "subsections", path, list)
    if not subsections:
        raise BuildError(f"{path}: subsections must not be empty")
    seen_subs = set()
    for sub in subsections:
        sid = require(sub, "id", path, str)
        require(sub, "title", path, str)
        if sid in seen_subs:
            raise BuildError(f"{path}: duplicate subsection {sid}")
        if not sid.replace("-", "").isalnum():
            raise BuildError(f"{path}: subsection id {sid} must be a slug")
        seen_subs.add(sid)
    items = require(section, "items", path, list)
    seen_items = set()
    context_count = 0
    inference_count = 0
    for item in items:
        iid = require(item, "id", path, str)
        if iid in seen_items:
            raise BuildError(f"{path}: duplicate item {iid}")
        seen_items.add(iid)
        sub = require(item, "subsection", path, str)
        if sub not in seen_subs:
            raise BuildError(f"{path}: item {iid} uses unknown subsection {sub}")
        parse_iso(require(item, "date", path, str), f"{path} item {iid}")
        require(item, "dateLabel", path, str)
        require(item, "headline", path, str)
        require(item, "summary", path, str)
        tag = item.get("tag")
        if tag not in TAGS:
            raise BuildError(f"{path}: item {iid} tag must be context, inference, or omitted")
        if tag == "inference" and section["id"] != "wwt":
            raise BuildError(f"{path}: inference is only allowed on wwt")
        if tag == "context":
            context_count += 1
        if tag == "inference":
            inference_count += 1
        validate_sources(item.get("sources"), f"{path} item {iid}")
    if context_count > 2:
        raise BuildError(f"{path}: at most 2 context items, found {context_count}")
    if inference_count > 2:
        raise BuildError(f"{path}: at most 2 inference items, found {inference_count}")
    section["_subs"] = seen_subs
    section["_items"] = {item["id"]: item for item in items}


def validate_top() -> None:
    signals = require(TOP, "signals", "top-signals.json", list)
    if len(signals) != 6:
        raise BuildError("top-signals.json: exactly 6 signals are required")
    by_file = {section["file"]: section for section in SECTIONS}
    for signal in signals:
        require(signal, "label", "top-signals.json", str)
        require(signal, "dateLabel", "top-signals.json", str)
        require(signal, "headline", "top-signals.json", str)
        section_id = require(signal, "section", "top-signals.json", str)
        item_id = require(signal, "item", "top-signals.json", str)
        href = require(signal, "href", "top-signals.json", str)
        match = next((section for section in SECTIONS if section["id"] == section_id), None)
        if match is None:
            raise BuildError(f"top signal {item_id}: unknown section {section_id}")
        if href != f"{match['file']}#{signal_anchor(match, item_id)}":
            raise BuildError(
                f"top signal {item_id}: href must be {match['file']}#{signal_anchor(match, item_id)}"
            )
        if item_id not in match["_items"]:
            raise BuildError(f"top signal {item_id}: no such item in {section_id}")
        if match["file"] not in by_file:
            raise BuildError(f"top signal {item_id}: missing page")


def signal_anchor(section: dict, item_id: str) -> str:
    item = section["_items"].get(item_id)
    if item is None:
        raise BuildError(f"missing item {item_id}")
    return item["subsection"]


def validate_archive(edition: dict, path: Path) -> None:
    require(edition, "date", path, str)
    parse_iso(edition["date"], str(path))
    if path.stem != edition["date"]:
        raise BuildError(f"{path}: filename must match date")
    require(edition, "title", path, str)
    require(edition, "note", path, str)
    signals = require(edition, "signals", path, list)
    if not signals:
        raise BuildError(f"{path}: signals must not be empty")
    for signal in signals:
        require(signal, "label", path, str)
        require(signal, "dateLabel", path, str)
        require(signal, "headline", path, str)
        validate_sources(signal.get("sources"), str(path))


def favicon() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
<rect width="48" height="48" rx="8" fill="#1c1915"/>
<path d="M24 6 L40 12 V23 C40 32 33 38.5 24 42 C15 38.5 8 32 8 23 V12 Z" fill="none" stroke="#f3efe6" stroke-width="2.5"/>
<path d="M15 21 L24 15 L33 21" stroke="#f0b429" stroke-width="3" fill="none"/>
<path d="M15 29 L24 23 L33 29" stroke="#f0b429" stroke-width="3" fill="none"/>
<circle cx="24" cy="35" r="2.2" fill="#f3efe6"/>
</svg>
"""


def main() -> int:
    global SITE, SECTIONS, TOP, UPDATED_LABEL
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    (DIST / "assets").mkdir()
    (DIST / "archive").mkdir()

    site_path = CONTENT / "site.json"
    SITE = load_json(site_path)
    require(SITE, "name", site_path, str)
    require(SITE, "shortName", site_path, str)
    require(SITE, "tagline", site_path, str)
    require(SITE, "audience", site_path, str)
    updated = parse_iso(require(SITE, "updated", site_path, str), str(site_path))
    UPDATED_LABEL = long_date(updated)
    order = require(SITE, "sections", site_path, list)
    if order != [
        "army",
        "dow",
        "ai",
        "cyber",
        "wwt",
        "budget",
        "tech",
        "partners",
        "datacenter",
    ]:
        raise BuildError("site.json sections must stay in the original nine-page order")

    SECTIONS = []
    for section_id in order:
        path = SECTIONS_DIR / f"{section_id}.json"
        if not path.exists():
            raise BuildError(f"missing {path}")
        section = load_json(path)
        validate_section(section, path)
        SECTIONS.append(section)

    top_path = CONTENT / "top-signals.json"
    TOP = load_json(top_path)
    validate_top()

    editions = []
    if ARCHIVE_DIR.exists():
        for path in sorted(ARCHIVE_DIR.glob("*.json")):
            edition = load_json(path)
            validate_archive(edition, path)
            edition["slug"] = f"{edition['date']}.html"
            edition["dateLabel"] = long_date(parse_iso(edition["date"], str(path)))
            editions.append(edition)
    editions.sort(key=lambda edition: edition["date"], reverse=True)

    shutil.copy(SRC / "site.css", DIST / "assets" / "site.css")
    shutil.copy(SRC / "theme.js", DIST / "assets" / "theme.js")
    (DIST / "assets" / "favicon.svg").write_text(favicon(), encoding="utf-8")
    (DIST / ".nojekyll").write_text("", encoding="utf-8")
    (DIST / "index.html").write_text(render_home(), encoding="utf-8")
    for section in SECTIONS:
        (DIST / section["file"]).write_text(render_section_page(section), encoding="utf-8")
    (DIST / "archive" / "index.html").write_text(render_archive_index(editions), encoding="utf-8")
    for edition in editions:
        (DIST / "archive" / edition["slug"]).write_text(
            render_archive_edition(edition), encoding="utf-8"
        )

    print(f"Built {DIST} · {UPDATED_LABEL}")
    for section in SECTIONS:
        print(f"  {section['file']}: {len(section['items'])} items")
    print(f"  archive: {len(editions)} edition(s)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BuildError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
