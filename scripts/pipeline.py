"""
E2E 스타트업 아이디어 스크리닝 파이프라인.

단계:
  1. 수집: Reddit / HN / ProductHunt / DEV.to
  2. 스코어링: Claude API 5기준 평가
  3. 저장: ideas/source/YYYY-MM-DD_scored.json
  4. (선택) 텔레그램 알림
  5. (선택) Notion 저장

사용:
    python -m scripts.pipeline                        # 전체
    python -m scripts.pipeline --skip-notion          # Notion 저장 생략
    python -m scripts.pipeline --skip-alert           # 알림 생략
    python -m scripts.pipeline --skip-notion --skip-alert
    python -m scripts.pipeline --limit 10             # 소스당 최대 건수
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "ideas" / "source"

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass


def _send_telegram(bot_token: str, chat_id: str, text: str) -> None:
    import urllib.request, urllib.parse
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10):
            pass
    except Exception as e:
        print(f"  [telegram-err] {e}")


def main() -> int:
    parser = argparse.ArgumentParser(description="창업 아이디어 스크리닝 파이프라인")
    parser.add_argument("--limit", type=int, default=15, help="소스당 최대 수집 건수")
    parser.add_argument("--skip-notion", action="store_true", help="Notion 저장 생략")
    parser.add_argument("--skip-alert", action="store_true", help="텔레그램 알림 생략")
    args = parser.parse_args()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # ── STEP 1: 수집 ──────────────────────────────────────────────
    print(f"\n▶ [1/3] 소스 수집 (소스당 최대 {args.limit}건)")
    from scripts.collect import collect_all
    items = collect_all(limit_per_source=args.limit)
    print(f"  총 수집: {len(items)}건")

    if not items:
        print("수집된 아이디어 없음. 종료.", file=sys.stderr)
        return 1

    # ── STEP 2: 스코어링 ──────────────────────────────────────────
    print(f"\n▶ [2/3] Claude 스코어링 ({len(items)}건)")
    from scripts.score import score_all
    scored = score_all(items)

    top       = [r for r in scored if r["grade"] == "심층분석"]
    watchlist = [r for r in scored if r["grade"] == "관심목록"]
    rejected  = [r for r in scored if r["grade"] == "탈락"]

    top.sort(key=lambda x: x["total"], reverse=True)
    watchlist.sort(key=lambda x: x["total"], reverse=True)

    # ── STEP 3: JSON 저장 ─────────────────────────────────────────
    print(f"\n▶ [3/3] JSON 저장")
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = SOURCE_DIR / f"{today}_scored.json"

    output = {
        "date": today,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_collected": len(scored),
            "top_count": len(top),
            "watchlist_count": len(watchlist),
            "rejected_count": len(rejected),
        },
        "top": top,
        "watchlist": watchlist,
        "rejected": rejected,
    }
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  저장: {out_path}")

    # ── 알림 ──────────────────────────────────────────────────────
    if not args.skip_alert:
        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        if bot_token and chat_id:
            lines = [f"*[아이디어 스크리닝 완료]* {today}"]
            lines.append(f"수집: {len(scored)}건 | 심층분석: {len(top)}건 | 관심목록: {len(watchlist)}건")
            if top:
                lines.append("\n*TOP 아이디어:*")
                for r in top[:3]:
                    lines.append(f"• {r['title'][:50]} ({r['total']}점)")
            _send_telegram(bot_token, chat_id, "\n".join(lines))
            print("  텔레그램 알림 전송 완료")
        else:
            print("  [skip] 텔레그램 미설정")

    # ── 결과 요약 ─────────────────────────────────────────────────
    print(f"""
╔══════════════════════════════╗
  파이프라인 완료 — {today}
  수집 총계  : {len(scored):>4}건
  심층분석   : {len(top):>4}건  (70점↑)
  관심목록   : {len(watchlist):>4}건  (50–69점)
  탈락       : {len(rejected):>4}건  (<50점)
  출력 파일  : ideas/source/{today}_scored.json
╚══════════════════════════════╝""")

    return 0


if __name__ == "__main__":
    sys.exit(main())
