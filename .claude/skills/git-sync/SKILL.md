---
name: git-sync
description: ideas/ 폴더 변경사항을 커밋하고 원격으로 푸시. 파이프라인 마지막 단계에서 호출.
---

# git-sync

## 역할
평가 후 `ideas/candidates/`, `ideas/raw/`, `ideas/index.md`, `ideas/log.md` 변경분을 커밋·푸시.

## 스크립트
- `scripts/git_commit_push.sh`
  - 변경 없으면 no-op
  - 커밋 메시지: `chore(ideas): auto-update YYYY-MM-DD HH:MMZ (N candidates)`
  - 푸시 실패 시 최대 4회 지수 백오프 재시도
