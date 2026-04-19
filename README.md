# idea-collector

창업 아이디어 수집 자동화 에이전트 v1.0 — 외부 소스에서 매일 아이디어를 수집하고, 정호의 5가지 검증 기준으로 필터링해 MVP 후보 DB를 축적하는 시스템.

## 구성
- `CLAUDE.md` — 오케스트레이터 (5기준 + 가치관 필터 고정)
- `.claude/skills/idea-collector/` — RSS/크롤링 수집
- `.claude/skills/idea-evaluator/` — Claude 평가 + 통과/탈락 분류
- `.claude/skills/idea-reporter/` — 주간 Top 3 리포트
- `.claude/skills/git-sync/` — 자동 커밋/푸시
- `scripts/pipeline.py` — E2E 드라이버
- `n8n/idea_collector_workflow.json` — n8n 일일 08:00 / 주간 월요일 09:00
- `ideas/{raw,candidates,reports}` + `ideas/index.md` + `ideas/log.md`

## 빠른 시작
```bash
cp .env.example .env    # 키 입력
pip install -r requirements.txt

# 전체 파이프라인
python -m scripts.pipeline

# 수동 아이디어 1건
python .claude/skills/idea-evaluator/scripts/evaluate_idea.py --text "AI 자동화 아이디어 내용..."

# 단계별
python .claude/skills/idea-collector/scripts/crawl_sources.py --limit 15
python .claude/skills/idea-evaluator/scripts/evaluate_all_raw.py
python .claude/skills/idea-evaluator/scripts/notify_new_candidates.py --since 180
bash .claude/skills/git-sync/scripts/git_commit_push.sh

# 주간
python .claude/skills/idea-reporter/scripts/weekly_report.py
```

## 검증 기준 (5개 전부 6점 이상 + 가치관 필터 통과)
- 기획 속도 / MVP 속도 / 고객 확보 / 수익 가능성 / 반복 수익 (각 0~10)
- 가치관 필터: 단순 노동 대체, 사기, 관심 도메인 밖 → 즉시 탈락

자세한 내용은 `CLAUDE.md`.

## 비용
아이디어 1건 평가 ~$0.003, 하루 50건 기준 월 ~$4.5.
