# 창업 아이디어 스크리닝 에이전트 — 오케스트레이터

매일 해외 + 국내 창업 신호를 자동 수집하고, 오너 맥락에 맞는 아이디어만 골라 점수 매겨 리포트로 받는 시스템.

## 오너 프로필 (평가 기준 맥락)
- 87년생 남성
- 네트워크 보안 13년 경력
- AI 에이전트 기반 업무 자동화 1인 창업 준비 중
- 위 프로필은 Claude 스크리닝 프롬프트의 시스템 컨텍스트에 고정 주입

## 평가 기준 (100점 만점)

| 항목 | 배점 | 평가 기준 |
|------|------|----------|
| 문제 선명도 | 25 | 해결하는 문제가 구체적이고 반복적으로 발생하는가? |
| 타겟 명확도 | 25 | 돈을 낼 고객이 누구인지 즉시 특정 가능한가? |
| 사업 기회 크기 | 20 | 시장 규모와 성장성이 충분한가? 해외 검증 사례가 있는가? |
| 초기 비용 / 진입 난이도 | 20 | 1인 창업자가 3개월 내 MVP 가능한가? |
| 국내 시장 실현 가능성 | 10 | 한국 고객이 지금 당장 돈을 낼 이유가 있는가? |

**AI 활용도 / 보안 도메인 연계는 참고 정보로만 표시 (배점 제외).**

- 총점 70+ → 심층 분석 대상 (TOP 10)
- 총점 50~69 → 관심 목록 보관
- 총점 49 이하 → 자동 필터링

## 데이터 소스 (하루 수집량: 소스당 최대 20개, 총 100개 이하)
- Reddit (r/entrepreneur, r/SaaS, r/smallbusiness)
- Hacker News (Show HN, Ask HN)
- ProductHunt (오늘의 런칭 제품)
- X(트위터) 트렌딩 키워드 (창업/자동화/AI 관련, v1.1)
- Google Trends (국내 + 글로벌)

## 파이프라인

```
[수집 소스] → [n8n 스케줄 07:00] → [소스별 수집]
  → [1차 필터링 (n8n, 무료)] → [/ideas/source/*.json 저장]
  → [Claude 스크리닝 (Sonnet, 비용 발생)] → [리포트 생성]
  → [/ideas/reports/*.md 저장] → [Notion DB] → [텔레그램 TOP 3]
```

주간 집계는 매주 일요일 09:00에 7일치 리포트를 Claude에 재분석, `weekly_summary_*.md` 저장.

## 스킬 구성
- `.claude/skills/idea-collector/` — 소스별 수집 (Python 스크립트)
- `.claude/skills/idea-screener/` — Claude API 스크리닝 + 평가 기준 프롬프트
- `.claude/skills/report-generator/` — Markdown 리포트 (일일 + 주간)
- `.claude/skills/notion-sync/` — Notion DB 저장
- `.claude/skills/alert-sender/` — 텔레그램 TOP 3 알림

## 데이터 위치
- Raw: `ideas/source/YYYY-MM-DD_raw.json`
- Daily: `ideas/reports/idea_report_YYYY-MM-DD.md`
- Weekly: `ideas/reports/weekly_summary_YYYY-WW.md`
- Notion DB: https://www.notion.so/bf511b94aec84d25a4a6283f491d1a6a

## 환경 변수 (.env)
```
ANTHROPIC_API_KEY=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=idea-collector/1.0
PRODUCTHUNT_TOKEN=          # optional; RSS로도 동작
NOTION_TOKEN=
NOTION_DATABASE_ID=bf511b94aec84d25a4a6283f491d1a6a
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

## 실행 방법 (로컬)
```bash
# 전체 파이프라인
python -m scripts.pipeline                  # collect → screen → report → sync → alert

# 단계별
python .claude/skills/idea-collector/scripts/reddit_scraper.py
python .claude/skills/idea-collector/scripts/hn_fetcher.py
python .claude/skills/idea-collector/scripts/producthunt_rss.py
python .claude/skills/idea-screener/scripts/screen_ideas.py --date 2026-04-18
python .claude/skills/report-generator/scripts/daily_report.py --date 2026-04-18
python .claude/skills/notion-sync/scripts/save_to_notion.py --date 2026-04-18
python .claude/skills/alert-sender/scripts/send_telegram.py --date 2026-04-18
```

n8n 워크플로우는 `n8n/idea_screener_workflow.json` 참고.
