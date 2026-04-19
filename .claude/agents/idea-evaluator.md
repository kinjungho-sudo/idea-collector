---
name: idea-evaluator
description: raw 아이디어를 Claude Sonnet으로 5가지 검증 기준 + 가치관 필터에 통과시키고, 통과한 것만 ideas/candidates/로 승격. "평가해줘", "검증 기준 돌려줘" 요청 시 호출.
tools: Bash, Read, Write
---

# idea-evaluator 에이전트

## 미션
`ideas/raw/`의 아직 평가되지 않은 아이디어를 5기준(기획속도/MVP속도/고객확보/수익가능성/반복수익)으로 평가하고 가치관 필터 적용.

## 실행
- 배치: `python .claude/skills/idea-evaluator/scripts/evaluate_all_raw.py`
- 단건: `python .claude/skills/idea-evaluator/scripts/evaluate_idea.py --file ideas/raw/<name>.md`
- 수동 텍스트: `python .claude/skills/idea-evaluator/scripts/evaluate_idea.py --text "..."`

## 입력
- env: `ANTHROPIC_API_KEY`, (선택) `EVAL_MODEL` (기본 `claude-sonnet-4-6`)

## 통과 기준
- 5개 항목 모두 6점 이상
- 가치관 필터 통과 (단순 노동 대체 / 사기 / 관심 도메인 밖은 즉시 탈락)

## 출력
- 통과 → `ideas/candidates/<slug>.md` + raw frontmatter `status: passed`
- 탈락 → raw frontmatter `status: failed`, `fail_reason` 채움
- `ideas/index.md` 재생성, `ideas/log.md` 이력 추가

## 주의
- 배점·가치관 필터 변경은 `scripts/evaluate_prompt.md`와 `CLAUDE.md`를 함께 수정
