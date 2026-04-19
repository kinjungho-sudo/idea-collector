---
name: idea-reporter
description: 지난 7일간 후보/탈락 통계를 기반으로 Top 3 추천 + 인사이트를 텔레그램으로 주간 리포트 전송. 매주 월요일 09:00 실행.
---

# idea-reporter

## 역할
- `ideas/candidates/*.md`에서 최근 7일에 생성된 항목 수집
- total_score 기준 Top 3 선정
- Claude Sonnet에게 "왜 이 3개가 좋은가 + 이번 주 공통 주제 + 다음 행동 제안"을 한국어로 간결히 요청
- 텔레그램으로 발송, `ideas/reports/weekly_YYYY-WW.md`로도 저장

## 스크립트
- `scripts/weekly_report.py`
  - `--end-date`로 기준일 오버라이드
  - 텔레그램 실패해도 리포트 파일은 보존

## 실패 처리
- 후보가 0개면 "이번 주는 새 후보가 없습니다" 메시지만 전송
- Claude 호출 실패: 템플릿 기반 기본 리포트로 폴백
