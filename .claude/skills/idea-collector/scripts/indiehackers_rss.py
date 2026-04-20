"""DEV.to API 수집기 (Indie Hackers 대체).

https://dev.to/api/articles 에서 startup/saas/indiehacker 태그 최신 글 수집.
공개 API, 인증 불필요.
"""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = "https://dev.to/api/articles"
TAGS = ["startup", "saas", "indiehacker"]
PER_TAG = 7
LIMIT = 20


def _make_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


def fetch_all() -> list[dict]:
    seen: set[str] = set()
    items: list[dict] = []

    for tag in TAGS:
        url = f"{BASE_URL}?tag={tag}&per_page={PER_TAG}&top=1"
        req = urllib.request.Request(url, headers={"User-Agent": "idea-collector/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                articles = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            print(f"[devto] tag={tag} 실패: {exc}", file=sys.stderr)
            continue

        for a in articles:
            link = a.get("url", "")
            if not link or link in seen:
                continue
            seen.add(link)
            items.append({
                "id": f"devto_{_make_id(link)}",
                "source": "indiehackers",
                "title": a.get("title", "").strip(),
                "url": link,
                "text": (a.get("description") or "")[:2000],
                "author": a.get("user", {}).get("username", ""),
                "score": a.get("positive_reactions_count", 0),
                "comments": a.get("comments_count", 0),
                "created_at": a.get("published_at", ""),
                "subreddit_or_tag": f"devto:{tag}",
            })
            if len(items) >= LIMIT:
                return items

    return items


def main() -> int:
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir = Path("ideas/source")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{date}_indiehackers.json"
    try:
        items = fetch_all()
    except Exception as exc:
        print(f"[devto] 실패: {exc}", file=sys.stderr)
        items = []
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[devto] {len(items)}개 수집 → {path}")
    return 0 if items else 1


if __name__ == "__main__":
    sys.exit(main())
