"""주간 Top 3 후보 리포트 생성 + 텔레그램 발송.

사용: python weekly_report.py [--end-date 2026-04-19]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CAND_DIR = ROOT / "ideas" / "candidates"
REPORT_DIR = ROOT / "ideas" / "reports"


def _parse_frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    fm: dict = {}
    body = text
    if text.startswith("---\n"):
        parts = text.split("---\n", 2)
        if len(parts) >= 3:
            for line in parts[1].splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    fm[k.strip()] = v.strip().strip("'\"")
            body = parts[2]
    return fm, body.strip()


def _recent_candidates(end: datetime, days: int = 7) -> list[dict]:
    since = end - timedelta(days=days)
    out: list[dict] = []
    for path in CAND_DIR.glob("*.md"):
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        if mtime < since or mtime > end:
            continue
        fm, body = _parse_frontmatter(path)
        out.append(
            {
                "path": path,
                "title": fm.get("title", path.stem),
                "category": fm.get("category", ""),
                "total_score": int(fm.get("total_score", 0) or 0),
                "body": body,
            }
        )
    out.sort(key=lambda x: x["total_score"], reverse=True)
    return out


def _claude_commentary(top: list[dict], model: str) -> str:
    try:
        from anthropic import Anthropic  # type: ignore
    except ImportError:
        return "_(anthropic SDK 미설치, 해설 생략)_"
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return "_(ANTHROPIC_API_KEY 없음, 해설 생략)_"
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    payload = [
        {
            "title": c["title"],
            "category": c["category"],
            "total_score": c["total_score"],
            "excerpt": c["body"][:500],
        }
        for c in top
    ]
    resp = client.messages.create(
        model=model,
        max_tokens=1200,
        system=(
            "너는 창업 코치다. 아래 Top 3 후보를 읽고 한국어로 3섹션을 써라: "
            "(1) 공통 주제 (2) 정호가 다음 주에 취해야 할 행동 1개 (3) 주의할 함정 1개. "
            "각 섹션은 2~3줄. 마크다운 헤더 사용."
        ),
        messages=[
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False, indent=2)}
        ],
    )
    return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")


def _send_telegram(text: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("[weekly] 텔레그램 env 없음, 전송 스킵", file=sys.stderr)
        return
    payload = urllib.parse.urlencode(
        {"chat_id": chat_id, "text": text[:4000], "disable_web_page_preview": "true"}
    ).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        resp.read()


def render(end: str, top: list[dict], commentary: str) -> str:
    lines = [
        f"# 주간 아이디어 리포트 — {end}",
        "",
        f"_후보 {len(top)}개 중 Top 3_",
        "",
        "## 🏆 Top 3",
        "",
    ]
    for i, c in enumerate(top[:3], 1):
        lines.extend(
            [
                f"### {i}. {c['title']} ({c['total_score']}/50)",
                f"- 카테고리: {c['category']}",
                f"- 파일: `{c['path'].relative_to(ROOT)}`",
                "",
            ]
        )
    if len(top) < 3:
        lines.append("_(이번 주 후보 < 3개)_\n")
    lines.extend(["## 🧭 해설", commentary.strip() or "_(해설 없음)_", ""])
    return "\n".join(lines)


def _render_telegram(end: str, top: list[dict]) -> str:
    if not top:
        return f"📬 {end} 주간 리포트\n\n이번 주는 새 후보가 없습니다."
    lines = [f"📬 {end} 주간 TOP 3"]
    for i, c in enumerate(top[:3], 1):
        lines.append(f"{i}. ({c['total_score']}/50) {c['title']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--end-date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )
    parser.add_argument(
        "--model", default=os.environ.get("EVAL_MODEL", "claude-sonnet-4-6")
    )
    args = parser.parse_args()

    end_dt = datetime.strptime(args.end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    top = _recent_candidates(end_dt)
    commentary = _claude_commentary(top[:3], args.model) if top else ""
    report = render(args.end_date, top, commentary)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    iso_y, iso_w, _ = end_dt.isocalendar()
    out_path = REPORT_DIR / f"weekly_{iso_y}-W{iso_w:02d}.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"[weekly] → {out_path}")

    try:
        _send_telegram(_render_telegram(args.end_date, top))
        print("[weekly] 텔레그램 전송 완료")
    except Exception as exc:  # noqa: BLE001
        print(f"[weekly] 텔레그램 실패: {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
