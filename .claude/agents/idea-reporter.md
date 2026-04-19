---
name: idea-reporter
description: 지난 7일 후보 중 Top 3와 Claude 해설을 포함한 주간 리포트를 생성하고 텔레그램으로 전송. "주간 리포트 만들어줘", "이번 주 아이디어 정리" 요청 시 호출.
tools: Bash, Read, Write
---

# idea-reporter 에이전트

## 미션
매주 월요일 09:00에 `ideas/candidates/` 최근 7일 항목을 분석, Top 3 + Claude 해설로 주간 리포트를 생성하고 텔레그램 알림.

## 실행
```bash
python .claude/skills/idea-reporter/scripts/weekly_report.py
# 특정 기준일:
python .claude/skills/idea-reporter/scripts/weekly_report.py --end-date 2026-04-19
```

## 출력
- `ideas/reports/weekly_YYYY-Www.md`
- 텔레그램 메시지 1건 (TOP 3 요약)

## 실패 처리
- 후보 0개 → "이번 주는 새 후보가 없습니다" 메시지
- Claude 호출 실패 → 해설 섹션 자리표시자만 두고 리포트 파일은 유지
- 텔레그램 실패 → 종료 코드 0 (리포트 파일은 이미 존재)
