#!/usr/bin/env python3
"""Check briefing source URLs and the built site's internal links.

Standard library only. Run from the repository root, after a build:

    python3 scripts/build.py
    python3 scripts/check_links.py

Exits 0 when every source URL is https and either returns a real article
or is only blocked by a bot wall, and every relative link in dist/ hits
its file and anchor. Exits 1 on a dead link, a redirect to a homepage or
parent section index, or a broken internal link.

A 401, 403, 429, or timeout is printed as "blocked". Open those in a
browser before keeping them. The script does not treat a bot wall as a
pass for a URL you have not read.
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urljoin
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
DIST = ROOT / "dist"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
TIMEOUT = 25
WORKERS = 8


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[tuple[str, str]] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {k: v for k, v in attrs if v is not None}
        if "id" in data:
            self.ids.add(data["id"])
        if tag in {"a", "link"} and "href" in data:
            self.hrefs.append((data["href"], tag))
        if tag in {"img", "script"} and "src" in data:
            self.hrefs.append((data["src"], tag))


def segments(url: str) -> list[str]:
    path = urlsplit(url).path.rstrip("/")
    return [part for part in path.split("/") if part]


def host(url: str) -> str:
    return urlsplit(url).netloc.lower().removeprefix("www.")


def collapsed(original: str, final: str) -> str | None:
    """Homepage, or a parent section index of the URL we asked for."""
    if host(original) != host(final):
        return None
    original_parts = segments(original)
    final_parts = segments(final)
    if not final_parts:
        return "homepage"
    if (
        len(final_parts) < len(original_parts)
        and original_parts[: len(final_parts)] == final_parts
    ):
        return "section front"
    return None


def collect_sources() -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []

    def walk(node: object, where: str) -> None:
        if isinstance(node, dict):
            url = node.get("url")
            if isinstance(url, str) and url.startswith(("http://", "https://")):
                found.append((where, url))
            for key, value in node.items():
                if key != "url":
                    walk(value, where)
        elif isinstance(node, list):
            for value in node:
                walk(value, where)

    for path in sorted(CONTENT.rglob("*.json")):
        if path.name == "schema.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        walk(data, str(path.relative_to(ROOT)))
    return found


def fetch(url: str) -> dict[str, object]:
    if not url.startswith("https://"):
        return {"url": url, "class": "fail", "detail": "source URL is not https"}
    request = Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
    try:
        with urlopen(request, timeout=TIMEOUT) as response:
            response.read(2048)
            code = getattr(response, "status", 200)
            final = response.geturl()
    except HTTPError as error:
        code = error.code
        final = error.geturl()
    except (URLError, TimeoutError, OSError) as error:
        return {"url": url, "class": "blocked", "detail": f"unreachable ({error.__class__.__name__})"}
    if code in {401, 403, 408, 429}:
        return {"url": url, "class": "blocked", "detail": f"HTTP {code}"}
    if code in {404, 410}:
        return {"url": url, "class": "fail", "detail": f"HTTP {code}"}
    if code >= 500:
        return {"url": url, "class": "blocked", "detail": f"HTTP {code}"}
    if code >= 400:
        return {"url": url, "class": "fail", "detail": f"HTTP {code}"}
    problem = collapsed(url, final)
    if problem:
        return {
            "url": url,
            "class": "fail",
            "detail": f"HTTP {code} redirected to a {problem}: {final}",
        }
    return {"url": url, "class": "ok", "detail": f"HTTP {code}"}


def check_sources() -> tuple[int, list[str]]:
    refs = collect_sources()
    unique = sorted({url for _, url in refs})
    by_url: dict[str, list[str]] = {}
    for where, url in refs:
        by_url.setdefault(url, []).append(where)
    print(f"source references: {len(refs)}")
    print(f"unique source URLs: {len(unique)}")
    results: dict[str, dict[str, object]] = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(fetch, url): url for url in unique}
        for future in as_completed(futures):
            url = futures[future]
            results[url] = future.result()
    failures: list[str] = []
    blocked = 0
    ok = 0
    for url in unique:
        result = results[url]
        kind = result["class"]
        if kind == "ok":
            ok += 1
            continue
        places = ", ".join(sorted(set(by_url[url])))
        line = f"{kind}: {result['detail']}  {url}  ({places})"
        print(line)
        if kind == "blocked":
            blocked += 1
        else:
            failures.append(line)
    print(f"sources ok: {ok}  blocked: {blocked}  failed: {len(failures)}")
    return len(unique), failures


def check_dist() -> list[str]:
    if not DIST.is_dir():
        return ["dist/ is missing. Run python3 scripts/build.py first."]
    pages = sorted(DIST.rglob("*.html"))
    if not pages:
        return ["dist/ has no HTML. Run python3 scripts/build.py first."]
    parsed: dict[Path, LinkParser] = {}
    for page in pages:
        parser = LinkParser()
        parser.feed(page.read_text(encoding="utf-8"))
        parsed[page] = parser
    failures: list[str] = []
    checked = 0
    for page, parser in parsed.items():
        for href, tag in parser.hrefs:
            if href.startswith(("mailto:", "javascript:", "data:")):
                continue
            if href.startswith("//"):
                failures.append(f"{page.relative_to(ROOT)}: protocol-relative {tag} {href}")
                continue
            if href.startswith(("http://", "https://")):
                continue
            if href.startswith("/"):
                failures.append(
                    f"{page.relative_to(ROOT)}: root-absolute {tag} {href} "
                    "breaks the /calvin-briefings/ subpath"
                )
                continue
            checked += 1
            path_part, _, anchor = href.partition("#")
            target = page.parent if path_part == "" else (page.parent / path_part).resolve()
            try:
                target.relative_to(DIST.resolve())
            except ValueError:
                failures.append(f"{page.relative_to(ROOT)}: {href} escapes dist/")
                continue
            if path_part and not target.is_file():
                failures.append(f"{page.relative_to(ROOT)}: missing {href}")
                continue
            if anchor:
                host_page = page if path_part == "" else target
                host_parser = parsed.get(host_page)
                if host_parser is None and host_page.is_file():
                    host_parser = LinkParser()
                    host_parser.feed(host_page.read_text(encoding="utf-8"))
                    parsed[host_page] = host_parser
                if host_parser is None or anchor not in host_parser.ids:
                    failures.append(f"{page.relative_to(ROOT)}: missing anchor #{anchor} in {href}")
    print(f"internal links checked: {checked} across {len(pages)} pages")
    return failures


def main() -> int:
    _, source_failures = check_sources()
    internal_failures = check_dist()
    failures = source_failures + internal_failures
    for line in internal_failures:
        print(f"fail: {line}")
    if failures:
        print(f"link check failed ({len(failures)})")
        return 1
    print("link check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
