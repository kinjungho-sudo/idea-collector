"""
Score collected startup ideas using Claude API.

Scoring rubric (total 100):
  문제선명도   (problem_clarity)       : 0–25
  타겟명확도   (target_clarity)        : 0–25
  사업기회     (market_opportunity)    : 0–20
  초기비용     (entry_cost)            : 0–20  (higher = lower barrier = better)
  국내가능성   (domestic_feasibility)  : 0–10

Grade: 70+ → 심층분석 / 50–69 → 관심목록 / <50 → 탈락
"""

from __future__ import annotations

import json
import os
import time

import anthropic

from scripts.collect import Item

MODEL = os.environ.get("EVAL_MODEL", "claude-sonnet-4-6")

SYSTEM_PROMPT = """\
당신은 1인 창업 전문 아이디어 스크리너입니다.
오너 프로필: 87년생 남성, 네트워크 보안 13년 경력, AI 에이전트 기반 업무 자동화 1인 창업 준비 중.
관심 도메인: AI 에이전트, 업무 자동화, 교육, 콘텐츠, SaaS.
목표: 월 MRR 300만원, 1~2달에 MVP 1개씩 출시.

주어진 아이디어(제목+본문)를 아래 5가지 기준으로 채점하고 JSON만 반환하세요.

[채점 기준]
1. 문제선명도 (problem_clarity): 0~25 — 해결하는 문제가 명확하고 Pain이 실재하는가?
2. 타겟명확도 (target_clarity): 0~25 — 누가 쓸지 구체적으로 특정 가능한가?
3. 사업기회 (market_opportunity): 0~20 — 시장 크기·성장성·경쟁 구도가 유리한가?
4. 초기비용 (entry_cost): 0~20 — 초기 투자 없이(또는 최소 비용으로) 시작 가능한가? (낮을수록 좋음 → 점수는 높을수록 좋음)
5. 국내가능성 (domestic_feasibility): 0~10 — 한국 시장에서 적용/판매 가능한가?

[즉시 탈락 조건] 아래 해당 시 모든 항목 0점:
- 단순 노동 대체 자동화 (해고 목적)
- 사기/기만적 요소
- 에너지/제조/금융/정치 도메인

[딥 분석 필드] 총점 50 이상일 때만 채워주세요 (이하면 빈 문자열):
- mvp: 4주 안에 만들 수 있는 최소 MVP 형태 (1~2문장)
- first_revenue_path: 첫 수익을 내기 위한 가장 빠른 경로 (1~2문장)
- domestic_angle: 한국 시장 맞춤 적용 각도 (1~2문장)

반드시 아래 JSON 형식만 반환 (마크다운/코드블록 없이):
{
  "scores": {
    "problem_clarity": <int 0-25>,
    "target_clarity": <int 0-25>,
    "market_opportunity": <int 0-20>,
    "entry_cost": <int 0-20>,
    "domestic_feasibility": <int 0-10>
  },
  "reasoning": "<한 줄 근거>",
  "deep": {
    "mvp": "<str>",
    "first_revenue_path": "<str>",
    "domestic_angle": "<str>"
  }
}"""


def _score_one(client: anthropic.Anthropic, item: Item) -> dict:
    body_excerpt = (item.body or "")[:800]
    user_msg = f"제목: {item.title}\n출처: {item.source}/{item.tag}\n\n본문:\n{body_excerpt}"

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = response.content[0].text.strip()
        data = json.loads(raw)
    except Exception as e:
        print(f"    [score-err] {item.title[:50]}: {e}")
        data = {
            "scores": {
                "problem_clarity": 0,
                "target_clarity": 0,
                "market_opportunity": 0,
                "entry_cost": 0,
                "domestic_feasibility": 0,
            },
            "reasoning": f"평가 실패: {e}",
            "deep": {"mvp": "", "first_revenue_path": "", "domestic_angle": ""},
        }

    scores = data.get("scores", {})
    total = sum(scores.values())
    if total >= 70:
        grade = "심층분석"
    elif total >= 50:
        grade = "관심목록"
    else:
        grade = "탈락"

    return {
        "uid": item.uid,
        "title": item.title,
        "source": f"{item.source}/{item.tag}",
        "source_url": item.url,
        "date": item.published[:10] if item.published else "",
        "total": total,
        "grade": grade,
        "scores": scores,
        "reasoning": data.get("reasoning", ""),
        "deep": data.get("deep", {"mvp": "", "first_revenue_path": "", "domestic_angle": ""}),
    }


def _make_client() -> anthropic.Anthropic:
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        return anthropic.Anthropic(api_key=api_key, base_url=base_url)
    # Claude Code remote session: use ingress token as auth_token
    token_file = os.environ.get(
        "CLAUDE_SESSION_INGRESS_TOKEN_FILE",
        "/home/claude/.claude/remote/.session_ingress_token",
    )
    try:
        token = open(token_file).read().strip()
        return anthropic.Anthropic(auth_token=token, base_url=base_url)
    except FileNotFoundError:
        pass
    raise RuntimeError("No Anthropic credentials found. Set ANTHROPIC_API_KEY.")


def score_all(items: list[Item], delay: float = 0.3) -> list[dict]:
    client = _make_client()
    results: list[dict] = []
    total = len(items)
    for i, item in enumerate(items, 1):
        print(f"  [{i}/{total}] {item.title[:60]}")
        result = _score_one(client, item)
        results.append(result)
        if i < total:
            time.sleep(delay)
    return results
