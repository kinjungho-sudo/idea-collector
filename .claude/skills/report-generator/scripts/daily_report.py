"""스크리닝 결과 → 일일 Markdown 리포트.

사용: python daily_report.py --date 2026-04-18
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SOURCE_LABEL = {
    "reddit": "Reddit",
    "hn": "Hacker News",
    "producthunt": "ProductHunt",
    "trends": "Google Trends",
    "x": "X (Twitter)",
}


def _score_line(name: str, val: int, max_val: int, reason: str) -> str:
    return f"- {name}: {val}/{max_val} ({reason})"


def _render_top(idx: int, item: dict) -> str:
    total = item.get("total", 0)
    title = item.get("title") or "(제목 없음)"
    scores = item.get("scores", {})
    reasons = item.get("reasons", {})
    deep = item.get("deep") or {}
    source = SOURCE_LABEL.get(item.get("source", ""), item.get("source", ""))
    url = item.get("source_url", "")
    tag = item.get("subreddit_or_tag", "")

    ai = "✓" if item.get("ai_applicable") else "△"
    sec = "✓" if item.get("security_linkable") else "△"

    lines = [
        f"### {idx}위 ({total}점) — {title}",
        f"**출처**: {source} {tag}  ",
        f"**링크**: {url}  ",
        f"**요약**: {item.get('summary', '')}",
        "",
        "**점수 상세**:",
        _score_line(
            "문제 선명도",
            scores.get("problem_clarity", 0),
            25,
            reasons.get("problem_clarity", ""),
        ),
        _score_line(
            "타겟 명확도",
            scores.get("target_clarity", 0),
            25,
            reasons.get("target_clarity", ""),
        ),
        _score_line(
            "사업 기회",
            scores.get("market_opportunity", 0),
            20,
            reasons.get("market_opportunity", ""),
        ),
        _score_line(
            "초기 비용",
            scores.get("entry_cost", 0),
            20,
            reasons.get("entry_cost", ""),
        ),
        _score_line(
            "국내 가능성",
            scores.get("domestic_feasibility", 0),
            10,
            reasons.get("domestic_feasibility", ""),
        ),
        "",
        f"**참고 메모**: AI 자동화 {ai} / 보안 도메인 연계 {sec}  ",
    ]
    if deep.get("target_customer"):
        lines.extend(
            [
                "",
                f"**타겟 고객**: {deep.get('target_customer', '')}",
                f"**국내 적용 각도**: {deep.get('domestic_angle', '')}",
                f"**MVP 제안**: {deep.get('mvp', '')}",
                f"**첫 수익 경로**: {deep.get('first_revenue_path', '')}",
                f"**해외 유사 사례**: {deep.get('overseas_reference', '')}",
            ]
        )
    lines.append("\n---\n")
    return "\n".join(lines)


def _render_watchlist(items: list[dict]) -> str:
    if not items:
        return "_관심 목록 없음_\n"
    rows = ["| 점수 | 제목 | 출처 | 링크 |", "|---|---|---|---|"]
    for it in items:
        rows.append(
            "| {total} | {title} | {src} | [열기]({url}) |".format(
                total=it.get("total", 0),
                title=(it.get("title") or "").replace("|", "｜")[:80],
                src=SOURCE_LABEL.get(it.get("source", ""), it.get("source", "")),
                url=it.get("source_url", ""),
            )
        )
    return "\n".join(rows) + "\n"


def render(scored: dict) -> str:
    date = scored.get("date")
    top = scored.get("top", [])
    watch = scored.get("watchlist", [])
    collected = scored.get("collected", 0)
    screened = scored.get("screened", 0)

    out = [
        f"# 창업 아이디어 일일 리포트 — {date}",
        "",
        "## 📊 오늘의 수집 현황",
        f"- 총 수집: {collected}개",
        f"- 스크리닝 대상: {screened}개",
        f"- **TOP 선정: {len(top)}개**",
        f"- 관심 목록: {len(watch)}개",
        "",
        "---",
        "",
        "## 🏆 TOP 아이디어",
        "",
    ]
    if not top:
        out.append("_오늘은 70점 이상 아이디어가 없습니다._\n")
    else:
        for i, it in enumerate(top, 1):
            out.append(_render_top(i, it))

    out.extend(["## 📋 관심 목록 (50~69점)", "", _render_watchlist(watch)])
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )
    args = parser.parse_args()

    src = Path(f"ideas/source/{args.date}_scored.json")
    if not src.exists():
        print(f"[daily_report] {src} 없음", file=sys.stderr)
        return 1
    scored = json.loads(src.read_text(encoding="utf-8"))
    out_dir = Path("ideas/reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"idea_report_{args.date}.md"
    out_path.write_text(render(scored), encoding="utf-8")
    print(f"[daily_report] → {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
