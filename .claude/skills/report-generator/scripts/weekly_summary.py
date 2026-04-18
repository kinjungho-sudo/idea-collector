"""지난 7일치 스코어 데이터를 Claude로 재분석해 주간 요약 생성.

사용: python weekly_summary.py [--end-date 2026-04-18]
- end-date 기준으로 7일치 ideas/source/*_scored.json 로드
- 반복 등장 아이디어에 가중 → 주간 TOP 5
- Claude가 주제 클러스터링 + 시그널 추세 해설
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _load_week(end_date: datetime) -> list[dict]:
    items: list[dict] = []
    for i in range(7):
        d = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
        p = Path(f"ideas/source/{d}_scored.json")
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            for entry in (data.get("top") or []) + (data.get("watchlist") or []):
                entry["_date"] = d
                items.append(entry)
    return items


def _weighted_rank(items: list[dict]) -> list[dict]:
    by_title: dict[str, list[dict]] = defaultdict(list)
    for it in items:
        key = (it.get("title") or "").strip().lower()[:80]
        if key:
            by_title[key].append(it)
    clusters = []
    for key, group in by_title.items():
        avg = sum(g.get("total", 0) for g in group) / len(group)
        weighted = avg + (len(group) - 1) * 5  # 반복 등장 가중
        clusters.append(
            {
                "title": group[0].get("title"),
                "appearances": len(group),
                "avg_total": round(avg, 1),
                "weighted": round(weighted, 1),
                "dates": sorted({g["_date"] for g in group}),
                "sample_url": group[0].get("source_url"),
            }
        )
    clusters.sort(key=lambda c: c["weighted"], reverse=True)
    return clusters[:5]


def _call_claude_overview(clusters: list[dict], model: str) -> str:
    try:
        from anthropic import Anthropic  # type: ignore
    except ImportError:
        return "_(anthropic SDK 미설치: Claude 해설 생략)_"
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return "_(ANTHROPIC_API_KEY 없음: Claude 해설 생략)_"
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=model,
        max_tokens=2000,
        system=(
            "너는 창업 트렌드 분석가다. 아래 주간 TOP 5 아이디어 클러스터를 읽고 "
            "1) 공통 주제 2) 반복 신호 3) 식어버린 신호 4) 87년생 보안 13년차 "
            "1인 창업자에게 주는 행동 제안을 한국어 Markdown으로 써라."
        ),
        messages=[
            {
                "role": "user",
                "content": json.dumps(clusters, ensure_ascii=False, indent=2),
            }
        ],
    )
    return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")


def render(end_date: str, clusters: list[dict], overview: str) -> str:
    lines = [
        f"# 창업 아이디어 주간 리포트 — {end_date} 기준",
        "",
        "## 🏆 주간 TOP 5 (반복 등장 가중)",
        "",
        "| 순위 | 제목 | 가중점수 | 평균점수 | 등장 횟수 | 등장 날짜 |",
        "|---|---|---|---|---|---|",
    ]
    for i, c in enumerate(clusters, 1):
        lines.append(
            "| {i} | {t} | {w} | {a} | {n} | {d} |".format(
                i=i,
                t=(c["title"] or "").replace("|", "｜")[:80],
                w=c["weighted"],
                a=c["avg_total"],
                n=c["appearances"],
                d=", ".join(c["dates"]),
            )
        )
    lines.extend(["", "## 🧭 Claude 주간 해설", "", overview, ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--end-date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )
    parser.add_argument(
        "--model", default=os.environ.get("WEEKLY_MODEL", "claude-sonnet-4-6")
    )
    args = parser.parse_args()

    end = datetime.strptime(args.end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    items = _load_week(end)
    if not items:
        print("[weekly] 지난 7일 scored 데이터 없음", file=sys.stderr)
        return 1
    clusters = _weighted_rank(items)
    overview = _call_claude_overview(clusters, args.model)

    iso_year, iso_week, _ = end.isocalendar()
    out_dir = Path("ideas/reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"weekly_summary_{iso_year}-W{iso_week:02d}.md"
    out_path.write_text(render(args.end_date, clusters, overview), encoding="utf-8")
    print(f"[weekly] → {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
