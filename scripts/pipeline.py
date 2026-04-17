"""전체 파이프라인 엔드투엔드 실행.

사용: python -m scripts.pipeline [--date YYYY-MM-DD] [--skip-alert]
순서: collect_all → screen_ideas → daily_report → save_to_notion → send_telegram
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLLECT = ROOT / ".claude/skills/idea-collector/scripts/collect_all.py"
SCREEN = ROOT / ".claude/skills/idea-screener/scripts/screen_ideas.py"
DAILY = ROOT / ".claude/skills/report-generator/scripts/daily_report.py"
NOTION = ROOT / ".claude/skills/notion-sync/scripts/save_to_notion.py"
TG = ROOT / ".claude/skills/alert-sender/scripts/send_telegram.py"


def _run(args: list[str], *, critical: bool) -> int:
    print(f"\n▶ {' '.join(args)}")
    rc = subprocess.call(args, cwd=ROOT)
    if rc != 0 and critical:
        print(f"✖ 크리티컬 단계 실패 (rc={rc}) — 중단", file=sys.stderr)
        sys.exit(rc)
    if rc != 0:
        print(f"⚠ 단계 실패 (rc={rc}) — 계속 진행", file=sys.stderr)
    return rc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )
    parser.add_argument("--skip-alert", action="store_true")
    parser.add_argument("--skip-notion", action="store_true")
    args = parser.parse_args()

    py = sys.executable
    _run([py, str(COLLECT)], critical=True)
    _run([py, str(SCREEN), "--date", args.date], critical=True)
    _run([py, str(DAILY), "--date", args.date], critical=True)
    if not args.skip_notion:
        _run([py, str(NOTION), "--date", args.date], critical=False)
    if not args.skip_alert:
        _run([py, str(TG), "--date", args.date], critical=False)
    print("\n✔ 파이프라인 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
