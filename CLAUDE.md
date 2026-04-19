# 창업 아이디어 수집 자동화 에이전트 — 오케스트레이터

외부에서 아이디어를 자동 수집하고, 정호의 검증 기준 5가지로 필터링해서 MVP 후보 리스트를 만드는 에이전트.

## 오너 프로필 / 목표 맥락
- 정호 (코마인드웍스)
- 목표: 월 MRR 300만원, 1~2달에 MVP 1개씩 출시
- 관심 도메인: AI 에이전트 / 업무 자동화 / 1인창업 / 교육 / 콘텐츠
- 파이프라인 정의: Raw 수집 → Claude 평가 → 후보 DB → 텔레그램 알림

## 검증 기준 (Must 조건 — 5가지 전부 통과해야 후보 등록)

| # | 기준 | 조건 | 점수 범위 |
|---|------|------|----------|
| 1 | 기획 속도 | 1주일 내 기획/설계 완성 가능한가? | 0~10 |
| 2 | MVP 속도 | 4주 내 MVP 완성 가능한가? | 0~10 |
| 3 | 고객 확보 | 5주 내 테스트 고객 확보 가능한가? | 0~10 |
| 4 | 수익 가능성 | 2달 내 MRR 30만원 달성 가능한가? | 0~10 |
| 5 | 반복 수익 | 구독/재계약/반복 구매 구조를 만들 수 있는가? | 0~10 |

**통과 기준**: 5개 항목 모두 6점 이상 → `candidates/` 등록. 한 항목이라도 5점 이하면 Raw만 보관 + 탈락 사유 기록.

## 가치관 필터 (즉시 탈락)
- 단순 노동 대체 (사람을 해고하기 위한 자동화)
- 사기/기만적 요소 포함 비즈니스
- 관심 도메인 밖 (에너지 / 제조 / 금융 / 정치 등)

## 데이터 소스

### 국내
| 소스 | 유형 | 수집 방식 |
|------|------|----------|
| 디시인사이드 창업갤 | 커뮤니티 | 크롤링 |
| 에펨코리아 자유게시판 | 커뮤니티 | 크롤링 |
| 네이버 블로그 (1인창업 태그) | 블로그 | RSS |
| 유튜브 (AI솔로프래너, 1인창업) | 영상 | 자막 추출 (v1.1) |

### 해외
| 소스 | 유형 | 수집 방식 |
|------|------|----------|
| Reddit r/SideProject | 커뮤니티 | RSS |
| Reddit r/Entrepreneur | 커뮤니티 | RSS |
| Product Hunt | 제품 런칭 | RSS |
| Indie Hackers | 커뮤니티 | RSS |

## 파이프라인

```
[n8n 스케줄 08:00] → [소스별 수집 + 중복 URL 제거 + 본문 추출]
  → [ideas/raw/YYYY-MM-DD_<slug>.md] 저장
  → [Claude 평가 (5기준 + 가치관 필터)]
    ├─ 통과 → [ideas/candidates/<slug>.md] 저장
    └─ 탈락 → Raw만 유지 + 탈락 사유 기록
  → [ideas/index.md 업데이트] → [ideas/log.md 이력 기록]
  → [Git commit + push] → [텔레그램 "✅ 새 아이디어 후보: ..."]
```

주간 리뷰: 매주 월요일 09:00, 지난 7일치 후보 분석 → Top 3 추천 + 텔레그램 발송.

## 스킬 구성
- `.claude/skills/idea-collector/` — 소스별 수집 + 본문 추출 + raw 저장
- `.claude/skills/idea-evaluator/` — Claude 5기준 평가 + 가치관 필터
- `.claude/skills/idea-reporter/` — 주간 Top 3 리포트
- `.claude/skills/git-sync/` — Git 커밋/푸시

## 데이터 위치
- Raw: `ideas/raw/YYYY-MM-DD_<slug>.md`
- 후보: `ideas/candidates/<slug>.md`
- 목록: `ideas/index.md` (상태: 실험중/검토중/후보/탈락)
- 이력: `ideas/log.md`

## 환경 변수 (.env)
```
ANTHROPIC_API_KEY=
EVAL_MODEL=claude-sonnet-4-6
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
REDDIT_USER_AGENT=idea-collector/1.0
GIT_AUTHOR_NAME=idea-bot
[email protected]
```

## 실행 방법 (로컬)
```bash
# 전체 파이프라인
python -m scripts.pipeline

# 수동 아이디어 평가
python .claude/skills/idea-evaluator/scripts/evaluate_idea.py --text "아이디어 내용"
python .claude/skills/idea-evaluator/scripts/evaluate_idea.py --file ideas/raw/2026-04-19_xyz.md

# 단계별
python .claude/skills/idea-collector/scripts/crawl_sources.py
python .claude/skills/idea-evaluator/scripts/evaluate_all_raw.py
python .claude/skills/idea-reporter/scripts/weekly_report.py
bash .claude/skills/git-sync/scripts/git_commit_push.sh
```

n8n 워크플로우: `n8n/idea_collector_workflow.json`.

## 비용
아이디어 1건 평가 ~$0.003, 하루 50건 기준 월 ~$4.5.

## 로드맵
- v1.0: RSS 수집 + Claude 평가 + 텔레그램 알림 (현재)
- v1.1: 유튜브 자막 수집
- v1.2: 주간 Top 3 자동 리포트
- v2.0: 후보 → MVP 설계서 자동 생성
- v3.0: 실험 결과 피드백 루프 (수익 데이터 연동)
