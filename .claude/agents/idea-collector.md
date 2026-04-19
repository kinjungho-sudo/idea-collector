---
name: idea-collector
description: Reddit/Product Hunt/Indie Hackers 등 창업 아이디어 소스에서 새 글을 수집해 ideas/raw/*.md로 저장. "아이디어 수집해줘", "오늘 트렌드 모아봐" 같은 요청 시 자동 호출.
tools: Bash, Read, Write
---

# idea-collector 에이전트

## 미션
외부 창업 아이디어 소스를 매일 스캔하고 중복을 걸러낸 뒤 `ideas/raw/YYYY-MM-DD_<slug>.md`로 저장.

## 실행
```bash
python .claude/skills/idea-collector/scripts/crawl_sources.py --limit 10
```

## 입력
- 환경 변수: `REDDIT_USER_AGENT` (권장)

## 출력
- `ideas/raw/*.md` 신규 파일 (frontmatter + 본문)
- `ideas/log.md` 이력 한 줄 추가

## 성공 조건
- 최소 1건 이상 새 raw 생성 (종료 코드 0)
- 전 소스 실패 → 종료 코드 1

## 수동 입력 모드
"아이디어 수집: <내용>" 같이 전달받으면 raw 파일을 수동으로 생성:
```bash
cat <<EOF > ideas/raw/$(date -u +%F)_manual_<slug>.md
---
id: manual_<hash>
source: manual
url: ""
title: "<제목>"
author: jungho
collected_at: $(date -u +%FT%TZ)
status: raw
---
<내용 본문>
EOF
```
