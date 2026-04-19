"""RSS 기반 창업 아이디어 수집기.

소스: Reddit r/SideProject, r/Entrepreneur, Product Hunt, Indie Hackers.
각 피드에서 최신 글을 가져와 중복을 제거한 뒤 `ideas/raw/YYYY-MM-DD_<slug>.md`로 저장.

사용:
    python crawl_sources.py [--limit 20]
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_text import slugify, strip_html  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]
RAW_DIR = ROOT / "ideas" / "raw"
INDEX_PATH = ROOT / "ideas" / "index.md"
LOG_PATH = ROOT / "ideas" / "log.md"

USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "idea-collector/1.0")

FEEDS: list[dict[str, str]] = [
    {"source": "reddit", "tag": "r/SideProject", "url": "https://www.reddit.com/r/SideProject/.rss"},
    {"source": "reddit", "tag": "r/Entrepreneur", "url": "https://www.reddit.com/r/Entrepreneur/.rss"},
    {"source": "producthunt", "tag": "today", "url": "https://www.producthunt.com/feed"},
    {"source": "indiehackers", "tag": "community", "url": "https://www.indiehackers.com/feed.xml"},
]


@dataclass
class RawItem:
    source: str
    tag: str
    url: str
    title: str
    author: str
    body: str
    published: str

    @property
    def ext_id(self) -> str:
        h = hashlib.sha1(self.url.encode("utf-8")).hexdigest()[:10]
        return f"{self.source}_{h}"


def _fetch(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _first_text(el: ET.Element | None, *paths: str) -> str:
    if el is None:
        return ""
    for p in paths:
        found = el.find(p)
        if found is not None:
            text = "".join(found.itertext()) or found.text or ""
            if text.strip():
                return text.strip()
    return ""


def _parse_feed(raw: str, source: str, tag: str) -> list[RawItem]:
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return []

    items: list[RawItem] = []
    # RSS 2.0
    channel = root.find("channel")
    if channel is not None:
        for it in channel.findall("item"):
            title = _first_text(it, "title")
            link = _first_text(it, "link")
            desc = _first_text(it, "description", "{http://purl.org/rss/1.0/modules/content/}encoded")
            author = _first_text(it, "{http://purl.org/dc/elements/1.1/}creator", "author")
            pub = _first_text(it, "pubDate", "{http://purl.org/dc/elements/1.1/}date")
            if not link or not title:
                continue
            items.append(
                RawItem(source, tag, link, title, author, strip_html(desc), pub)
            )
        return items

    # Atom
    ns = "{http://www.w3.org/2005/Atom}"
    for entry in root.findall(f"{ns}entry"):
        title = _first_text(entry, f"{ns}title")
        link_el = entry.find(f"{ns}link")
        link = link_el.get("href") if link_el is not None else ""
        summary = _first_text(entry, f"{ns}summary", f"{ns}content")
        author = _first_text(entry, f"{ns}author/{ns}name")
        pub = _first_text(entry, f"{ns}updated", f"{ns}published")
        if not link or not title:
            continue
        items.append(RawItem(source, tag, link, title, author, strip_html(summary), pub))
    return items


def _load_existing_urls() -> set[str]:
    seen: set[str] = set()
    if not INDEX_PATH.exists():
        return seen
    text = INDEX_PATH.read_text(encoding="utf-8")
    for m in re.finditer(r"https?://\S+", text):
        seen.add(m.group(0).rstrip(")]."))
    # raw 파일의 url: 도 수집
    for raw in RAW_DIR.glob("*.md"):
        head = raw.read_text(encoding="utf-8").split("---", 2)
        if len(head) >= 2:
            for line in head[1].splitlines():
                if line.strip().startswith("url:"):
                    seen.add(line.split(":", 1)[1].strip())
    return seen


def _write_raw(item: RawItem) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = slugify(item.title)
    path = RAW_DIR / f"{date}_{slug}_{item.ext_id}.md"
    frontmatter = (
        "---\n"
        f"id: {item.ext_id}\n"
        f"source: {item.source}\n"
        f"tag: {item.tag}\n"
        f"url: {item.url}\n"
        f"title: {item.title.replace(chr(10), ' ')[:200]!r}\n"
        f"author: {(item.author or '').replace(chr(10), ' ')!r}\n"
        f"collected_at: {datetime.now(timezone.utc).isoformat()}\n"
        f"published: {item.published}\n"
        "status: raw\n"
        "---\n\n"
    )
    path.write_text(frontmatter + (item.body or "").strip() + "\n", encoding="utf-8")
    return path


def _log(line: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"- {ts} — {line}\n")


def collect(limit_per_source: int) -> Iterable[Path]:
    seen = _load_existing_urls()
    created: list[Path] = []
    for feed in FEEDS:
        try:
            raw = _fetch(feed["url"])
            items = _parse_feed(raw, feed["source"], feed["tag"])[: limit_per_source * 2]
        except (urllib.error.URLError, TimeoutError) as exc:
            _log(f"[collect] {feed['source']}/{feed['tag']} 실패: {exc}")
            continue

        added = 0
        for item in items:
            if item.url in seen:
                continue
            path = _write_raw(item)
            created.append(path)
            seen.add(item.url)
            added += 1
            if added >= limit_per_source:
                break
        _log(f"[collect] {feed['source']}/{feed['tag']} — 신규 {added}건")
    return created


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=10, help="소스당 최대 신규 건수")
    args = parser.parse_args()
    created = list(collect(args.limit))
    print(f"[collect] 총 신규 {len(created)}건 저장 → {RAW_DIR}")
    return 0 if created else 1


if __name__ == "__main__":
    sys.exit(main())
