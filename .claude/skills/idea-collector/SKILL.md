---
name: idea-collector
description: Reddit(r/SideProject, r/Entrepreneur), Product Hunt, Indie Hackers RSS와 국내 커뮤니티 크롤링으로 창업 아이디어 원천을 수집해 ideas/raw/*.md로 저장
---

# idea-collector

## 역할
외부 소스에서 창업 아이디어 원천을 자동 수집해 `ideas/raw/YYYY-MM-DD_<slug>.md`로 저장.
중복 URL은 `ideas/index.md`와 비교해 스킵. 본문은 텍스트 추출해서 저장.

## 소스 (v1.0)

### RSS 기반 (우선 구현)
| 소스 | URL |
|------|-----|
| Reddit r/SideProject | https://www.reddit.com/r/SideProject/.rss |
| Reddit r/Entrepreneur | https://www.reddit.com/r/Entrepreneur/.rss |
| Product Hunt | https://www.producthunt.com/feed |
| Indie Hackers | https://www.indiehackers.com/feed.xml |

### 크롤링 기반 (국내)
| 소스 | URL | 주의사항 |
|------|-----|---------|
| 디시인사이드 창업갤 | https://gall.dcinside.com/board/lists/?id=entrepreneur | robots.txt + 요청 간격 ≥3s |
| 에펨코리아 자유게시판 | https://www.fmkorea.com/index.php?mid=free | 동일 |
| 네이버 블로그 (1인창업 태그) | https://rss.blog.naver.com/<blogId>.xml | RSS 가능 |

## 출력 스키마

Raw 파일(`ideas/raw/YYYY-MM-DD_<slug>.md`) 구조:
```markdown
---
id: <source>_<hash>
source: reddit|producthunt|indiehackers|dc|fmkorea|naverblog|youtube|manual
url: https://...
title: "..."
author: "..."
collected_at: 2026-04-19T08:00:00Z
status: raw
---

<본문 텍스트>
```

## 스크립트
- `scripts/crawl_sources.py` — 소스별 병렬 수집 + 본문 추출 + raw 저장 + 중복 제거
- `scripts/extract_text.py` — HTML → 순수 텍스트 헬퍼 (크롤링 소스 공용)

## 실패 처리
- 크롤링 실패: 재시도 2회 → 해당 소스만 스킵 + `ideas/log.md` 기록
- 본문 추출 실패: 제목만 저장
- 모든 소스 실패 시 종료 코드 1

## 환경 변수
- `REDDIT_USER_AGENT` — 필수
- (옵션) 유튜브 자막은 v1.1 추가 예정
