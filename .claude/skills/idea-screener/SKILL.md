---
name: idea-screener
description: Claude Sonnet API로 원시 아이디어 리스트를 오너 맥락 기반 5항목 스코어링하고 TOP 10 + 관심 목록을 JSON으로 산출
---

# idea-screener

## 역할
`ideas/source/YYYY-MM-DD_raw.json`을 읽어 Claude Sonnet로 전 항목을 일괄 스코어링.
총점 70+ 아이디어는 심층 분석(타겟, MVP, 첫 수익 경로)을 추가로 받음.

## 평가 기준
- 문제 선명도 (25)
- 타겟 명확도 (25)
- 사업 기회 크기 (20)
- 초기 비용 / 진입 난이도 (20)
- 국내 시장 실현 가능성 (10)

배점 외 참고: AI 활용 가능 / 보안 연계 가능 (checkbox).

## 출력 (ideas/source/YYYY-MM-DD_scored.json)
```json
{
  "date": "2026-04-18",
  "collected": 87,
  "screened": 35,
  "top": [ { "id": "...", "title": "...", "total": 92, "scores": {...}, "deep": {...}, "source_url": "..." } ],
  "watchlist": [ { ... } ]
}
```

## 스크립트
- `scripts/scoring_prompt.md` — 시스템/사용자 프롬프트 템플릿 (수정 시 로직 영향)
- `scripts/screen_ideas.py` — 호출 엔트리포인트 (`python screen_ideas.py --date YYYY-MM-DD`)

## 주의
- 모델: `claude-sonnet-4-6` (기본), `--model`로 오버라이드
- 비용 절감: raw 입력은 제목 + 요약(최대 500자)으로 압축해 주입
- 상한: raw 100개 × ~300 토큰 + 응답 → 요청당 ~$0.01 예상
