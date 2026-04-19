"""E2E 파이프라인: 수집 → 평가 → 알림 → Git 커밋.

사용:
    python -m scripts.pipeline                  # 전체
    python -m scripts.pipeline --skip-notify    # 텔레그램 알림 생략
    python -m scripts.pipeline --skip-git       # git 커밋 생략
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CRAWL = ROOT / ".claude/skills/idea-collector/scripts/crawl_sources.py"
EVAL_ALL = ROOT / ".claude/skills/idea-evaluator/scripts/evaluate_all_raw.py"
NOTIFY = ROOT / ".claude/skills/idea-evaluator/scripts/notify_new_candidates.py"
GIT_SYNC = ROOT / ".claude/skills/git-sync/scripts/git_commit_push.sh"


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
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--skip-notify", action="store_true")
    parser.add_argument("--skip-git", action="store_true")
    args = parser.parse_args()

    py = sys.executable
    _run([py, str(CRAWL), "--limit", str(args.limit)], critical=False)
    _run([py, str(EVAL_ALL)], critical=False)
    if not args.skip_notify:
        _run([py, str(NOTIFY), "--since", "180"], critical=False)
    if not args.skip_git:
        _run(["bash", str(GIT_SYNC)], critical=False)
    print("\n✔ 파이프라인 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
