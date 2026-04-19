---
name: idea-evaluator
description: raw 아이디어를 정호의 5가지 검증 기준 + 가치관 필터로 평가해 통과 시 ideas/candidates/*.md로 승격, 탈락 시 raw frontmatter에 사유 기록
---

# idea-evaluator

## 역할
`ideas/raw/*.md` 또는 직접 입력된 텍스트를 Claude Sonnet으로 평가.
5기준 전부 6점 이상 + 가치관 필터 통과 → `ideas/candidates/<slug>.md` 승격.
그 외 → raw의 frontmatter `status` 갱신(`failed`) + `fail_reason` 기록.

## 평가 프롬프트 고정값
`scripts/evaluate_prompt.md` 에 시스템+사용자 템플릿 보관.
배점 변경 시 `CLAUDE.md`와 이 SKILL.md를 동시에 수정.

## 통과 조건
- 5개 항목 모두 ≥ 6
- 가치관 필터 통과 (단순 노동 대체, 사기/기만, 관심 도메인 밖 → 즉시 탈락)
- 탈락 시 `pass=false`, `fail_reason` 명시

## 출력 스키마 (Claude JSON)
```json
{
  "title": "...",
  "category": "AI에이전트|자동화|교육|콘텐츠|기타",
  "scores": {
    "기획속도": 0,
    "MVP속도": 0,
    "고객확보": 0,
    "수익가능성": 0,
    "반복수익": 0
  },
  "total_score": 0,
  "pass": true,
  "fail_reason": null,
  "summary": "3줄 요약",
  "mvp_idea": "가장 작은 MVP 제안",
  "tags": ["..."]
}
```

## 스크립트
- `scripts/evaluate_prompt.md` — 시스템/사용자 프롬프트 템플릿
- `scripts/evaluate_idea.py` — 단건 평가 (`--file` 또는 `--text`)
- `scripts/evaluate_all_raw.py` — `ideas/raw/` 배치 평가 + index/log 갱신

## 실패 처리
- Claude API 실패 → 재시도 1회 → raw만 유지, log 기록
- JSON 파싱 실패 → raw 상태 `needs-retry`로 표시
