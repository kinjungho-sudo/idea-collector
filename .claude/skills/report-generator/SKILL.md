---
name: report-generator
description: 스크리닝 결과를 일일/주간 Markdown 리포트로 렌더링해 ideas/reports에 저장
---

# report-generator

## 역할
- `ideas/source/YYYY-MM-DD_scored.json` → `ideas/reports/idea_report_YYYY-MM-DD.md`
- 매주 일요일 7일치를 Claude로 재분석해 반복 패턴 감지 후 `weekly_summary_YYYY-WW.md`

## 일일 리포트 포맷
- 수집 현황 요약
- TOP 10 (점수 상세, 참고 메모, 국내 적용 각도, MVP, 첫 수익 경로)
- 관심 목록 50~69점 테이블

## 주간 리포트 포맷
- 주간 TOP 5 (중복 등장 아이디어 가중)
- 반복 패턴 (Claude가 감지한 주제)
- 신규 시그널 / 식어버린 시그널

## 스크립트
- `scripts/daily_report.py`
- `scripts/weekly_summary.py`
