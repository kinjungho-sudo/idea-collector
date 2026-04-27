---
name: notion-sync
description: 스크리닝 결과(top + watchlist)를 Notion DB에 한 아이디어 한 행씩 업서트
---

# notion-sync

## 역할
- `ideas/source/YYYY-MM-DD_scored.json`을 읽어 Notion DB에 각 아이디어를 한 페이지로 생성
- 동일 `id`가 이미 존재하면 업데이트 (Notion DB 검색 후 patch)

## Notion DB
- DB URL: https://www.notion.so/bf511b94aec84d25a4a6283f491d1a6a
- DB ID: `bf511b94aec84d25a4a6283f491d1a6a`
- 환경 변수: `NOTION_TOKEN`, `NOTION_DATABASE_ID`

## 필드 매핑
| Notion 필드 | 타입 | 스코어 JSON 매핑 |
|---|---|---|
| 아이디어 제목 | title | `title` |
| 날짜 | date | `date` |
| 총점 | number | `total` |
| 등급 | select | 70+: 심층분석 / 50~69: 관심목록 / 그 외: 필터링 |
| 출처 | select | `source` → Reddit/HN/ProductHunt/X/Trends |
| 문제 선명도 | number | `scores.problem_clarity` |
| 타겟 명확도 | number | `scores.target_clarity` |
| 사업 기회 | number | `scores.market_opportunity` |
| 초기 비용 | number | `scores.entry_cost` |
| 국내 가능성 | number | `scores.domestic_feasibility` |
| 국내 적용 각도 | rich_text | `deep.domestic_angle` |
| MVP 제안 | rich_text | `deep.mvp` |
| 첫 수익 경로 | rich_text | `deep.first_revenue_path` |
| AI 활용 가능 | checkbox | `ai_applicable` |
| 보안 연계 가능 | checkbox | `security_linkable` |
| 상태 | select | 기본 "검토대기" |
| 주간 리포트 포함 | checkbox | 기본 false |
| 원본 링크 | url | `source_url` |
| External ID | rich_text | `id` (업서트 키) |
