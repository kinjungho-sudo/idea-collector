"""
Startup idea collection from:
- Reddit: r/entrepreneur, r/SaaS, r/smallbusiness (RSS)
- HN: Show HN, Ask HN (Algolia API)
- ProductHunt RSS
- DEV.to: startup, saas, indiehacker tags (RSS)
"""

from __future__ import annotations

import hashlib
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterator
from xml.etree import ElementTree as ET

USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "idea-collector/1.0 (startup-screening)")

RSS_SOURCES = [
    {"source": "reddit", "tag": "r/entrepreneur",   "url": "https://www.reddit.com/r/entrepreneur/.rss"},
    {"source": "reddit", "tag": "r/SaaS",           "url": "https://www.reddit.com/r/SaaS/.rss"},
    {"source": "reddit", "tag": "r/smallbusiness",  "url": "https://www.reddit.com/r/smallbusiness/.rss"},
    {"source": "producthunt", "tag": "today",       "url": "https://www.producthunt.com/feed"},
    {"source": "devto", "tag": "startup",           "url": "https://dev.to/feed/tag/startup"},
    {"source": "devto", "tag": "saas",              "url": "https://dev.to/feed/tag/saas"},
    {"source": "devto", "tag": "indiehacker",       "url": "https://dev.to/feed/tag/indiehacker"},
]

HN_SOURCES = [
    {"tag": "Show HN", "query_tag": "show_hn"},
    {"tag": "Ask HN",  "query_tag": "ask_hn"},
]


@dataclass
class Item:
    source: str
    tag: str
    title: str
    body: str
    url: str
    author: str = ""
    published: str = ""
    uid: str = field(init=False)

    def __post_init__(self):
        self.uid = hashlib.sha1(self.url.encode()).hexdigest()[:12]


def _fetch(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/atom+xml, application/json, text/xml, */*",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _text(el: ET.Element | None, *tags: str) -> str:
    if el is None:
        return ""
    for t in tags:
        found = el.find(t)
        if found is not None:
            raw = "".join(found.itertext()) or (found.text or "")
            if raw.strip():
                return raw.strip()
    return ""


def _parse_rss(xml: str, source: str, tag: str) -> list[Item]:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return []

    items: list[Item] = []
    ns_content = "{http://purl.org/rss/1.0/modules/content/}encoded"
    ns_dc = "{http://purl.org/dc/elements/1.1/}"
    ns_atom = "{http://www.w3.org/2005/Atom}"

    channel = root.find("channel")
    if channel is not None:
        for it in channel.findall("item"):
            title = _text(it, "title")
            link = _text(it, "link")
            desc = _text(it, "description", ns_content)
            author = _text(it, f"{ns_dc}creator", "author")
            pub = _text(it, "pubDate", f"{ns_dc}date")
            if not title or not link:
                continue
            items.append(Item(source, tag, title, _strip_html(desc), link, author, pub))
        return items

    for entry in root.findall(f"{ns_atom}entry"):
        title = _text(entry, f"{ns_atom}title")
        link_el = entry.find(f"{ns_atom}link")
        link = link_el.get("href", "") if link_el is not None else ""
        body = _text(entry, f"{ns_atom}summary", f"{ns_atom}content")
        author = _text(entry, f"{ns_atom}author/{ns_atom}name")
        pub = _text(entry, f"{ns_atom}updated", f"{ns_atom}published")
        if not title or not link:
            continue
        items.append(Item(source, tag, title, _strip_html(body), link, author, pub))
    return items


def _fetch_hn(query_tag: str, limit: int = 15) -> list[Item]:
    import json
    url = (
        f"https://hn.algolia.com/api/v1/search_by_date"
        f"?tags={query_tag}&hitsPerPage={limit}"
    )
    try:
        raw = _fetch(url, timeout=15)
        data = json.loads(raw)
    except Exception:
        return []

    items: list[Item] = []
    for hit in data.get("hits", []):
        title = hit.get("title", "").strip()
        story_url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
        body = (hit.get("story_text") or "").strip()
        author = hit.get("author", "")
        ts = hit.get("created_at", "")
        if not title:
            continue
        items.append(Item("hackernews", query_tag, title, _strip_html(body), story_url, author, ts))
    return items


def collect_all(limit_per_source: int = 15) -> list[Item]:
    seen_urls: set[str] = set()
    results: list[Item] = []

    for feed in RSS_SOURCES:
        try:
            xml = _fetch(feed["url"])
            batch = _parse_rss(xml, feed["source"], feed["tag"])[:limit_per_source * 2]
        except Exception as e:
            print(f"  [skip] {feed['tag']}: {e}")
            continue

        added = 0
        for it in batch:
            if it.url in seen_urls or not it.title:
                continue
            seen_urls.add(it.url)
            results.append(it)
            added += 1
            if added >= limit_per_source:
                break
        print(f"  [rss] {feed['tag']}: {added}건")
        time.sleep(0.5)

    for hn in HN_SOURCES:
        batch = _fetch_hn(hn["query_tag"], limit_per_source)
        added = 0
        for it in batch:
            if it.url in seen_urls or not it.title:
                continue
            seen_urls.add(it.url)
            results.append(it)
            added += 1
        print(f"  [hn] {hn['tag']}: {added}건")

    return results
