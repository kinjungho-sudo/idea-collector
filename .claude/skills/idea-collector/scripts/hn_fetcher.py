"""Hacker News 창업 신호 수집기.

Algolia HN Search API로 Show HN / Ask HN 최근 48시간 게시물을 최대 20개 수집.
"""

from __future__ import annotations

import json
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path

LIMIT = 20
MIN_POINTS = 10
MIN_COMMENTS = 3
TAGS = ["show_hn", "ask_hn"]


def _fetch_tag(tag: str, since: int, per_tag: int) -> list[dict]:
    params = urllib.parse.urlencode(
        {
            "tags": f"story,{tag}",
            "numericFilters": f"created_at_i>={since},points>={MIN_POINTS}",
            "hitsPerPage": per_tag,
        }
    )
    url = f"https://hn.algolia.com/api/v1/search_by_date?{params}"
    with urllib.request.urlopen(url, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    out: list[dict] = []
    for hit in data.get("hits", []):
        if (hit.get("num_comments") or 0) < MIN_COMMENTS:
            continue
        out.append(
            {
                "id": f"hn_{hit['objectID']}",
                "source": "hn",
                "title": hit.get("title") or hit.get("story_title") or "",
                "url": hit.get("url")
                or f"https://news.ycombinator.com/item?id={hit['objectID']}",
                "text": (hit.get("story_text") or "")[:2000],
                "author": hit.get("author") or "unknown",
                "score": int(hit.get("points") or 0),
                "comments": int(hit.get("num_comments") or 0),
                "created_at": hit.get("created_at"),
                "subreddit_or_tag": tag,
            }
        )
    return out


def fetch_all() -> list[dict]:
    since = int((datetime.now(timezone.utc) - timedelta(hours=48)).timestamp())
    results: list[dict] = []
    per_tag = LIMIT // len(TAGS) + 2
    for tag in TAGS:
        try:
            results.extend(_fetch_tag(tag, since, per_tag))
        except Exception as exc:  # noqa: BLE001
            print(f"[hn] {tag} 실패: {exc}", file=sys.stderr)
    # 중복 id 제거
    seen: set[str] = set()
    dedup: list[dict] = []
    for item in results:
        if item["id"] in seen:
            continue
        seen.add(item["id"])
        dedup.append(item)
    dedup.sort(key=lambda x: x["score"], reverse=True)
    return dedup[:LIMIT]


def main() -> int:
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir = Path("ideas/source")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{date}_hn.json"
    items = fetch_all()
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[hn] {len(items)}개 수집 → {path}")
    return 0 if items else 1


if __name__ == "__main__":
    sys.exit(main())
