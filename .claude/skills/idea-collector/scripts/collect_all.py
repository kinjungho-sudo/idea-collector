"""모든 소스를 병렬 수집 + 1차 필터링 + 단일 raw.json 병합.

1차 필터링 기준:
- 중복 제거 (id, 제목 정규화 비교)
- 키워드 필터: 창업/자동화/AI/SaaS/문제/불편/startup/problem/automation/pain
  (ProductHunt, Trends는 키워드 필터 면제 — 원본 자체가 시그널)
- 최소 반응: Reddit/HN은 score+comments ≥ 10
"""

from __future__ import annotations

import concurrent.futures
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from hn_fetcher import fetch_all as fetch_hn
from producthunt_rss import fetch_all as fetch_ph
from reddit_scraper import fetch_all as fetch_reddit
from trends_fetcher import fetch_all as fetch_trends

KEYWORDS = re.compile(
    r"창업|자동화|불편|문제|사업|부업|SaaS|saas|"
    r"startup|problem|pain|automat|AI|agent|workflow|prod",
    re.IGNORECASE,
)
MAX_TOTAL = 100


def _normalize_title(t: str) -> str:
    return re.sub(r"\W+", "", t or "").lower()


def _filter(items: list[dict]) -> list[dict]:
    seen_ids: set[str] = set()
    seen_titles: set[str] = set()
    out: list[dict] = []
    for it in items:
        if it["id"] in seen_ids:
            continue
        norm = _normalize_title(it.get("title", ""))
        if norm and norm in seen_titles:
            continue
        # 키워드 필터 (Reddit/HN만)
        if it["source"] in ("reddit", "hn"):
            haystack = f"{it.get('title', '')} {it.get('text', '')}"
            if not KEYWORDS.search(haystack):
                continue
            if (it.get("score", 0) + it.get("comments", 0)) < 10:
                continue
        seen_ids.add(it["id"])
        if norm:
            seen_titles.add(norm)
        out.append(it)
    return out[:MAX_TOTAL]


def main() -> int:
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir = Path("ideas/source")
    out_dir.mkdir(parents=True, exist_ok=True)

    tasks = {
        "reddit": fetch_reddit,
        "hn": fetch_hn,
        "producthunt": fetch_ph,
        "trends": fetch_trends,
    }
    gathered: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(fn): name for name, fn in tasks.items()}
        for fut in concurrent.futures.as_completed(futures):
            name = futures[fut]
            try:
                items = fut.result()
                gathered.extend(items)
                print(f"[collect] {name}: {len(items)}")
            except Exception as exc:  # noqa: BLE001
                print(f"[collect] {name} 실패: {exc}", file=sys.stderr)

    filtered = _filter(gathered)
    raw_path = out_dir / f"{date}_raw.json"
    raw_path.write_text(
        json.dumps(filtered, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[collect] 총 {len(gathered)} → 필터 후 {len(filtered)} → {raw_path}")
    return 0 if filtered else 1


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    sys.exit(main())
