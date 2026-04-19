"""evaluate_all_raw.py 실행 결과를 읽고 새 후보를 텔레그램으로 알림.

stdin에 `{"passed": N, "failed": N, "new_candidates": [...]}` JSON을 받거나,
candidates/의 최신 mtime 파일(--since 분) 기준으로 조회.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CAND_DIR = ROOT / "ideas" / "candidates"


def _send(text: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("[notify] 텔레그램 env 없음, 스킵", file=sys.stderr)
        return
    data = urllib.parse.urlencode(
        {"chat_id": chat, "text": text[:4000], "disable_web_page_preview": "true"}
    ).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage", data=data, method="POST"
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        resp.read()


def _recent_candidates(since_min: int) -> list[str]:
    cutoff = time.time() - since_min * 60
    titles: list[str] = []
    for path in CAND_DIR.glob("*.md"):
        if path.stat().st_mtime < cutoff:
            continue
        text = path.read_text(encoding="utf-8").split("---\n", 2)
        if len(text) >= 2:
            for line in text[1].splitlines():
                if line.startswith("title:"):
                    titles.append(line.split(":", 1)[1].strip().strip("'\""))
                    break
    return titles


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", type=int, default=120, help="분 단위, 최근 mtime 기준")
    parser.add_argument(
        "--from-stdin",
        action="store_true",
        help="evaluate_all_raw.py의 JSON을 stdin으로 받음",
    )
    args = parser.parse_args()

    if args.from_stdin:
        try:
            payload = json.load(sys.stdin)
            titles = payload.get("new_candidates") or []
        except Exception:  # noqa: BLE001
            titles = []
    else:
        titles = _recent_candidates(args.since)

    if not titles:
        print("[notify] 새 후보 없음")
        return 0

    text = "✅ 새 아이디어 후보\n\n" + "\n".join(f"• {t}" for t in titles[:10])
    try:
        _send(text)
        print(f"[notify] {len(titles)}건 알림 전송")
    except Exception as exc:  # noqa: BLE001
        print(f"[notify] 실패: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
