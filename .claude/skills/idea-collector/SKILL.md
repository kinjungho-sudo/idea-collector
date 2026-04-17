---
name: idea-collector
description: Reddit, Hacker News, ProductHunt, Google Trends에서 창업 신호를 일 단위로 수집해 ideas/source/*.json으로 저장
---

# idea-collector

## 역할
- 소스별 스크립트를 병렬 실행해 원시 아이디어 리스트를 확보
- 1차 필터링: 중복 제거, 키워드 매칭 (창업/자동화/AI/SaaS/문제/불편), 최소 반응 임계치
- 결과를 `ideas/source/YYYY-MM-DD_raw.json`에 저장

## 소스별 상한
| 소스 | 상한 | 엔드포인트 |
|------|------|-----------|
| Reddit | 20 | PRAW (r/entrepreneur, r/SaaS, r/smallbusiness) |
| Hacker News | 20 | Algolia API `/search` (Show HN, Ask HN, 48h) |
| ProductHunt | 20 | RSS https://www.producthunt.com/feed |
| Google Trends | 20 | pytrends (daily trending KR + US) |

총합 100개 이하로 제한.

## 출력 스키마 (ideas/source/*.json)
```json
[
  {
    "id": "reddit_abc123",
    "source": "reddit",
    "title": "...",
    "url": "...",
    "text": "...",
    "author": "...",
    "score": 42,
    "comments": 15,
    "created_at": "2026-04-18T06:21:00Z",
    "subreddit_or_tag": "r/SaaS"
  }
]
```

## 실패 처리
- 한 소스가 실패하면 해당 소스만 스킵하고 로그 (`ideas/source/collect.log`)
- 모든 소스 실패 시 종료 코드 1 반환 (n8n이 에스컬레이션)

## 스크립트
- `scripts/reddit_scraper.py`
- `scripts/hn_fetcher.py`
- `scripts/producthunt_rss.py`
- `scripts/trends_fetcher.py`
- `scripts/collect_all.py` — 4개 병렬 호출 + 병합 + 1차 필터링
