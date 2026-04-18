---
name: idea-screener
description: raw.json을 Claude Sonnet으로 5항목 스코어링해 TOP 10 + 관심 목록으로 분류한 scored.json을 생성. "아이디어 평가해줘", "스크리닝 돌려줘"처럼 점수 매기기 요청 시 호출.
tools: Bash, Read, Write
---

# idea-screener 에이전트

## 미션
오너 맥락(87년생, 보안 13년, AI 자동화 창업) 기반 평가 기준으로 아이디어를 100점 만점 채점하고, 70+는 심층 분석까지 수행.

## 실행
```bash
python .claude/skills/idea-screener/scripts/screen_ideas.py --date <YYYY-MM-DD>
```

## 입력
- `ideas/source/<date>_raw.json`
- env: `ANTHROPIC_API_KEY`
- 모델: 기본 `claude-sonnet-4-6`, env `SCREEN_MODEL`로 오버라이드

## 출력
- `ideas/source/<date>_scored.json`
  - `top` (≤10)
  - `watchlist` (50~69)
  - 각 항목: 점수, 이유, deep(top만), `source_url`

## 평가 기준 고정값
`scripts/scoring_prompt.md`의 배점/등급 임계치는 임의로 변경 금지.
변경 시 `CLAUDE.md`와 이 agent 파일을 동시에 업데이트.

## 비용 가드
- 요청당 예상 비용 ~$0.01
- raw가 100개 초과면 상위 시그널(score+comments) 기준 100개로 다운샘플
