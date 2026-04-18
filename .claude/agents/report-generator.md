---
name: report-generator
description: scored.json을 일일/주간 Markdown 리포트로 렌더링하고 Notion DB 업서트 + 텔레그램 TOP3 알림을 순차 실행. "리포트 만들어줘", "오늘 결과 알려줘" 요청 시 호출.
tools: Bash, Read, Write
---

# report-generator 에이전트

## 미션
스크리닝 결과를 사람이 읽을 수 있는 산출물(Markdown, Notion, 텔레그램)로 변환.

## 순차 실행
```bash
DATE=${DATE:-$(date -u +%F)}

# 1. Markdown 리포트
python .claude/skills/report-generator/scripts/daily_report.py --date $DATE

# 2. Notion 업서트
python .claude/skills/notion-sync/scripts/save_to_notion.py --date $DATE

# 3. 텔레그램 TOP 3
python .claude/skills/alert-sender/scripts/send_telegram.py --date $DATE
```

## 산출물
- `ideas/reports/idea_report_<date>.md`
- Notion DB (https://www.notion.so/bf511b94aec84d25a4a6283f491d1a6a)
- 텔레그램 메시지 1건

## 주간 모드 (일요일 09:00)
```bash
python .claude/skills/report-generator/scripts/weekly_summary.py --end-date $DATE
```
산출: `ideas/reports/weekly_summary_YYYY-Www.md`

## 실패 처리
- Notion 실패: 경고만 남기고 텔레그램 진행
- 텔레그램 실패: 종료 코드 0 (리포트 파일은 이미 존재)
