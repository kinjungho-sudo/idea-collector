"""Google Trends 수집기.

pytrends로 KR + US 일간 트렌딩 키워드 상위 20개 수집.
실패 시 빈 결과 반환 (pytrends가 구글 변경에 민감하므로 파이프라인 중단 금지).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

LIMIT_PER_REGION = 10


def _fetch_region(region: str) -> list[dict]:
    from pytrends.request import TrendReq  # type: ignore

    pytrends = TrendReq(hl="ko" if region == "KR" else "en-US", tz=540)
    df = pytrends.trending_searches(pn="south_korea" if region == "KR" else "united_states")
    items: list[dict] = []
    for idx, row in df.head(LIMIT_PER_REGION).iterrows():
        keyword = str(row[0])
        items.append(
            {
                "id": f"trend_{region}_{idx}",
                "source": "trends",
                "title": keyword,
                "url": f"https://trends.google.com/trends/explore?q={keyword}&geo={region}",
                "text": f"Google Trends {region} daily trending: {keyword}",
                "author": "",
                "score": LIMIT_PER_REGION - idx,
                "comments": 0,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "subreddit_or_tag": f"trends:{region}",
            }
        )
    return items


def fetch_all() -> list[dict]:
    results: list[dict] = []
    for region in ("KR", "US"):
        try:
            results.extend(_fetch_region(region))
        except Exception as exc:  # noqa: BLE001
            print(f"[trends] {region} 실패: {exc}", file=sys.stderr)
    return results[:20]


def main() -> int:
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir = Path("ideas/source")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{date}_trends.json"
    items = fetch_all()
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[trends] {len(items)}개 수집 → {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
