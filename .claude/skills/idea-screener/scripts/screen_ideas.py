"""Claude Sonnet로 raw 아이디어를 일괄 스코어링.

사용: python screen_ideas.py --date 2026-04-18 [--model claude-sonnet-4-6]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROMPT_TEMPLATE = Path(__file__).parent / "scoring_prompt.md"
DEFAULT_MODEL = "claude-sonnet-4-6"


def _compact(items: list[dict]) -> list[dict]:
    compact = []
    for it in items:
        compact.append(
            {
                "id": it["id"],
                "title": it.get("title", "")[:200],
                "text": (it.get("text") or "")[:500],
                "source": it.get("source"),
                "url": it.get("url"),
                "signals": {
                    "score": it.get("score", 0),
                    "comments": it.get("comments", 0),
                    "tag": it.get("subreddit_or_tag"),
                },
            }
        )
    return compact


def _build_messages(raw_items: list[dict]) -> tuple[str, list[dict]]:
    template = PROMPT_TEMPLATE.read_text(encoding="utf-8")
    system_part, user_part = template.split("## [USER]", 1)
    system = system_part.replace("## [SYSTEM]", "").strip()
    user = user_part.strip().replace(
        "<<IDEAS_JSON>>",
        json.dumps(_compact(raw_items), ensure_ascii=False, indent=2),
    )
    return system, [{"role": "user", "content": user}]


def _call_claude(system: str, messages: list[dict], model: str) -> dict:
    from anthropic import Anthropic  # type: ignore

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=model,
        max_tokens=16000,
        system=system,
        messages=messages,
    )
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text[:-3]
    return json.loads(text)


def _partition(results: list[dict]) -> tuple[list[dict], list[dict]]:
    top = [r for r in results if r.get("tier") == "top" or r.get("total", 0) >= 70]
    watch = [
        r
        for r in results
        if r.get("tier") == "watchlist" or 50 <= r.get("total", 0) < 70
    ]
    top.sort(key=lambda r: r.get("total", 0), reverse=True)
    watch.sort(key=lambda r: r.get("total", 0), reverse=True)
    return top[:10], watch


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )
    parser.add_argument("--model", default=os.environ.get("SCREEN_MODEL", DEFAULT_MODEL))
    args = parser.parse_args()

    src = Path(f"ideas/source/{args.date}_raw.json")
    if not src.exists():
        print(f"[screen] {src} 없음", file=sys.stderr)
        return 1
    raw = json.loads(src.read_text(encoding="utf-8"))
    if not raw:
        print("[screen] raw 비어있음", file=sys.stderr)
        return 1

    system, messages = _build_messages(raw)
    data = _call_claude(system, messages, args.model)
    results = data.get("results", [])
    top, watch = _partition(results)

    url_by_id = {it["id"]: it.get("url") for it in raw}
    for r in top + watch:
        r.setdefault("source_url", url_by_id.get(r.get("id"), ""))

    out = {
        "date": args.date,
        "model": args.model,
        "collected": len(raw),
        "screened": len(results),
        "top": top,
        "watchlist": watch,
    }
    out_path = Path(f"ideas/source/{args.date}_scored.json")
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"[screen] {len(raw)} 입력 → 평가 {len(results)} / TOP {len(top)} / 관심 {len(watch)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
