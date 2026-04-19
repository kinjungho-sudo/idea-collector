#!/usr/bin/env bash
# ideas/ 하위 변경분을 자동 커밋·푸시.
# 사용: bash git_commit_push.sh [branch]
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

BRANCH="${1:-$(git rev-parse --abbrev-ref HEAD)}"

git add ideas/raw ideas/candidates ideas/index.md ideas/log.md ideas/reports 2>/dev/null || true

if git diff --cached --quiet; then
  echo "[git-sync] 변경 없음 — 스킵"
  exit 0
fi

CAND_COUNT=$(find ideas/candidates -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
STAMP=$(date -u +"%Y-%m-%d %H:%MZ")
MSG="chore(ideas): auto-update ${STAMP} (${CAND_COUNT} candidates)"

git commit -m "$MSG"

DELAY=2
for attempt in 1 2 3 4; do
  if git push -u origin "$BRANCH"; then
    echo "[git-sync] 푸시 성공"
    exit 0
  fi
  echo "[git-sync] 푸시 실패 attempt=${attempt}, ${DELAY}s 후 재시도" >&2
  sleep "$DELAY"
  DELAY=$((DELAY * 2))
done

echo "[git-sync] 최종 푸시 실패" >&2
exit 1
