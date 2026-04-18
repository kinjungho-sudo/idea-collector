# idea-collector

창업 아이디어 스크리닝 에이전트 v1.0 — 매일 07:00 해외 + 국내 창업 신호를 자동 수집하고, 오너 맥락 기반 5항목 채점으로 TOP 10을 리포트로 받는 시스템.

## 구성
- `CLAUDE.md` — 오케스트레이터 (평가 기준, 파이프라인, 환경)
- `.claude/skills/` — 수집·스크리닝·리포트·Notion·알림 스킬
- `.claude/agents/` — 작업별 에이전트 정의
- `scripts/pipeline.py` — 엔드투엔드 드라이버
- `n8n/idea_screener_workflow.json` — n8n 일일/주간 워크플로우
- `ideas/source/` — 소스별 원시 + 병합 + 스코어 JSON
- `ideas/reports/` — 일일/주간 Markdown 리포트

## 빠른 시작
```bash
cp .env.example .env   # 키 입력
pip install -r requirements.txt
python -m scripts.pipeline            # 전체 실행
# 또는 단계별:
python .claude/skills/idea-collector/scripts/collect_all.py
python .claude/skills/idea-screener/scripts/screen_ideas.py
python .claude/skills/report-generator/scripts/daily_report.py
python .claude/skills/notion-sync/scripts/save_to_notion.py
python .claude/skills/alert-sender/scripts/send_telegram.py
```

## 평가 기준
상세는 `CLAUDE.md` 참고. 100점 만점: 문제 선명도(25) / 타겟 명확도(25) / 사업 기회(20) / 초기 비용(20) / 국내 가능성(10). AI 활용도·보안 연계는 참고 정보(배점 제외).

- 70+ → 심층 분석 TOP 10
- 50~69 → 관심 목록
- 49 이하 → 자동 필터링

## 비용
Claude API는 스크리닝 단계에서만 호출. 일일 ~$0.01, 월 ~$0.30 예상.
