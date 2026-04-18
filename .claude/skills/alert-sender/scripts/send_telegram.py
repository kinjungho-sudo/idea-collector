"""TOP 3 아이디어 텔레그램 요약 전송.

사용: python send_telegram.py --date 2026-04-18
필요 env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def _format(date: str, top: list[dict]) -> str:
    header = f"📬 {date} 창업 아이디어 TOP {min(3, len(top))}\n"
    if not top:
        return header + "\n_오늘은 70점 이상 아이디어가 없습니다._"
    lines = [header]
    for i, it in enumerate(top[:3], 1):
        lines.append(
            "{i}. ({total}점) {title}\n   🔗 {url}\n   💡 {summary}".format(
                i=i,
                total=it.get("total", 0),
                title=(it.get("title") or "")[:120],
                url=it.get("source_url") or "",
                summary=(it.get("summary") or "")[:160],
            )
        )
    return "\n\n".join(lines)


def send(text: str) -> dict:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    payload = urllib.parse.urlencode(
        {"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"}
    ).encode("utf-8")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    req = urllib.request.Request(url, data=payload, method="POST")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )
    args = parser.parse_args()

    src = Path(f"ideas/source/{args.date}_scored.json")
    if not src.exists():
        print(f"[alert] {src} 없음", file=sys.stderr)
        return 1
    data = json.loads(src.read_text(encoding="utf-8"))
    text = _format(args.date, data.get("top") or [])
    try:
        send(text)
        print("[alert] 텔레그램 전송 완료")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"[alert] 실패: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
