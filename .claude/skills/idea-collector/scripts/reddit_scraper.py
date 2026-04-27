"""Reddit 창업 신호 수집기.

r/entrepreneur, r/SaaS, r/smallbusiness의 최신 + 인기 글을 소스당 20개 이하로 수집.
PRAW(Reddit API) 우선, 실패 시 .json 공개 엔드포인트 폴백.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import urllib.request
import urllib.error

SUBREDDITS = ["entrepreneur", "SaaS", "smallbusiness"]
PER_SUB_LIMIT = 7  # 3 * 7 = 21 (상한 20 근접)
MIN_UPVOTES = 5
MIN_COMMENTS = 2
USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "idea-collector/1.0")


def _fetch_praw(sub: str, limit: int) -> list[dict]:
    import praw  # type: ignore

    client_id = os.environ["REDDIT_CLIENT_ID"]
    client_secret = os.environ["REDDIT_CLIENT_SECRET"]
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=USER_AGENT,
    )
    out: list[dict] = []
    for post in reddit.subreddit(sub).hot(limit=limit * 2):
        if post.stickied or post.score < MIN_UPVOTES or post.num_comments < MIN_COMMENTS:
            continue
        out.append(
            {
                "id": f"reddit_{post.id}",
                "source": "reddit",
                "title": post.title,
                "url": f"https://reddit.com{post.permalink}",
                "text": (post.selftext or "")[:2000],
                "author": str(post.author) if post.author else "unknown",
                "score": int(post.score),
                "comments": int(post.num_comments),
                "created_at": datetime.fromtimestamp(post.created_utc, tz=timezone.utc).isoformat(),
                "subreddit_or_tag": f"r/{sub}",
            }
        )
        if len(out) >= limit:
            break
    return out


def _fetch_public_json(sub: str, limit: int) -> list[dict]:
    url = f"https://www.reddit.com/r/{sub}/hot.json?limit={limit * 2}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    out: list[dict] = []
    for child in data.get("data", {}).get("children", []):
        p = child.get("data", {})
        if p.get("stickied") or p.get("score", 0) < MIN_UPVOTES or p.get("num_comments", 0) < MIN_COMMENTS:
            continue
        out.append(
            {
                "id": f"reddit_{p['id']}",
                "source": "reddit",
                "title": p.get("title", ""),
                "url": f"https://reddit.com{p.get('permalink', '')}",
                "text": (p.get("selftext") or "")[:2000],
                "author": p.get("author") or "unknown",
                "score": int(p.get("score", 0)),
                "comments": int(p.get("num_comments", 0)),
                "created_at": datetime.fromtimestamp(
                    p.get("created_utc", 0), tz=timezone.utc
                ).isoformat(),
                "subreddit_or_tag": f"r/{sub}",
            }
        )
        if len(out) >= limit:
            break
    return out


def fetch_all() -> list[dict]:
    results: list[dict] = []
    for sub in SUBREDDITS:
        try:
            if os.environ.get("REDDIT_CLIENT_ID") and os.environ.get("REDDIT_CLIENT_SECRET"):
                items = _fetch_praw(sub, PER_SUB_LIMIT)
            else:
                items = _fetch_public_json(sub, PER_SUB_LIMIT)
            results.extend(items)
            time.sleep(1)
        except Exception as exc:  # noqa: BLE001
            print(f"[reddit] {sub} 실패: {exc}", file=sys.stderr)
    return results[:20]


def main() -> int:
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir = Path("ideas/source")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{date}_reddit.json"
    items = fetch_all()
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[reddit] {len(items)}개 수집 → {path}")
    return 0 if items else 1


if __name__ == "__main__":
    sys.exit(main())
