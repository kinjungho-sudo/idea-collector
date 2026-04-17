"""ProductHunt RSS 수집기.

https://www.producthunt.com/feed 에서 당일 런칭 제품 최대 20개 파싱.
표준 라이브러리 xml.etree만 사용 (외부 의존성 없음).
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

FEED_URL = "https://www.producthunt.com/feed"
LIMIT = 20


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def fetch_all() -> list[dict]:
    req = urllib.request.Request(FEED_URL, headers={"User-Agent": "idea-collector/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    root = ET.fromstring(raw)
    channel = root.find("channel")
    items: list[dict] = []
    if channel is None:
        return items
    for it in channel.findall("item")[: LIMIT * 2]:
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        desc = _strip_html(it.findtext("description") or "")
        pub = it.findtext("pubDate") or ""
        guid = (it.findtext("guid") or link).strip()
        item_id = re.sub(r"[^a-zA-Z0-9]", "", guid)[-12:] or str(abs(hash(link)))[:12]
        items.append(
            {
                "id": f"ph_{item_id}",
                "source": "producthunt",
                "title": title,
                "url": link,
                "text": desc[:2000],
                "author": "",
                "score": 0,
                "comments": 0,
                "created_at": pub,
                "subreddit_or_tag": "producthunt",
            }
        )
        if len(items) >= LIMIT:
            break
    return items


def main() -> int:
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir = Path("ideas/source")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{date}_producthunt.json"
    try:
        items = fetch_all()
    except Exception as exc:  # noqa: BLE001
        print(f"[producthunt] 실패: {exc}", file=sys.stderr)
        items = []
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[producthunt] {len(items)}개 수집 → {path}")
    return 0 if items else 1


if __name__ == "__main__":
    sys.exit(main())
