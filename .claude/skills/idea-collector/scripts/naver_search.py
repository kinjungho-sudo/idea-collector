"""네이버 검색 API 수집기.

창업/자동화/불편함 관련 국내 블로그·카페 글을 네이버 검색 API로 수집.
환경 변수: NAVER_CLIENT_ID, NAVER_CLIENT_SECRET
없으면 스킵 (0개 반환).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SEARCH_URL = "https://openapi.naver.com/v1/search/blog.json"
LIMIT = 20
QUERIES = [
    "창업 아이디어 불편",
    "자동화 SaaS 문제",
    "1인 창업 AI 도구",
    "스타트업 페인포인트",
]


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _make_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


def _search(query: str, client_id: str, client_secret: str, display: int = 5) -> list[dict]:
    params = urllib.parse.urlencode({"query": query, "display": display, "sort": "date"})
    req = urllib.request.Request(
        f"{SEARCH_URL}?{params}",
        headers={
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret,
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("items", [])


def fetch_all() -> list[dict]:
    client_id = os.environ.get("NAVER_CLIENT_ID", "")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        print("[naver] NAVER_CLIENT_ID/SECRET 없음 — 스킵", file=sys.stderr)
        return []

    items: list[dict] = []
    seen: set[str] = set()

    for query in QUERIES:
        try:
            results = _search(query, client_id, client_secret, display=5)
            for r in results:
                link = r.get("link") or r.get("bloggerlink", "")
                if not link or link in seen:
                    continue
                seen.add(link)
                title = _strip_html(r.get("title", ""))
                desc = _strip_html(r.get("description", ""))
                items.append({
                    "id": f"naver_{_make_id(link)}",
                    "source": "naver",
                    "title": title,
                    "url": link,
                    "text": desc[:2000],
                    "author": r.get("bloggername", ""),
                    "score": 0,
                    "comments": 0,
                    "created_at": r.get("postdate", ""),
                    "subreddit_or_tag": f"naver:{query}",
                })
                if len(items) >= LIMIT:
                    return items
        except Exception as exc:
            print(f"[naver] 쿼리 '{query}' 실패: {exc}", file=sys.stderr)

    return items


def main() -> int:
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir = Path("ideas/source")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{date}_naver.json"
    try:
        items = fetch_all()
    except Exception as exc:
        print(f"[naver] 실패: {exc}", file=sys.stderr)
        items = []
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[naver] {len(items)}개 수집 → {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
