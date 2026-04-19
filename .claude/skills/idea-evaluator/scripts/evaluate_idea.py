"""단일 아이디어 평가.

사용:
    python evaluate_idea.py --file ideas/raw/2026-04-19_xxx.md
    python evaluate_idea.py --text "짧은 설명 문자열"
    python evaluate_idea.py --stdin

평가 결과는 stdout에 JSON으로 출력. --file 모드에선 raw frontmatter도 갱신.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path


def slugify(title: str, max_len: int = 60) -> str:
    s = re.sub(r"[^\w가-힣\s-]", "", title or "").strip().lower()
    s = re.sub(r"[\s_-]+", "-", s)
    return s[:max_len] or "untitled"

PROMPT_TEMPLATE = Path(__file__).parent / "evaluate_prompt.md"
DEFAULT_MODEL = os.environ.get("EVAL_MODEL", "claude-sonnet-4-6")

REQUIRED_KEYS = {"기획속도", "MVP속도", "고객확보", "수익가능성", "반복수익"}
MIN_PASS = 6


def _load_template() -> tuple[str, str]:
    text = PROMPT_TEMPLATE.read_text(encoding="utf-8")
    system_part, user_part = text.split("## [USER]", 1)
    system = system_part.replace("## [SYSTEM]", "", 1).strip()
    user = user_part.strip()
    return system, user


def _read_raw(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    fm: dict = {}
    body = text
    if text.startswith("---\n"):
        parts = text.split("---\n", 2)
        if len(parts) >= 3:
            for line in parts[1].splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    fm[k.strip()] = v.strip().strip("'\"")
            body = parts[2]
    return fm, body.strip()


def _call_claude(system: str, user: str, model: str) -> str:
    try:
        from anthropic import Anthropic  # type: ignore
    except ImportError as exc:  # noqa: BLE001
        raise RuntimeError("anthropic SDK 미설치: pip install anthropic") from exc

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=model,
        max_tokens=1500,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()


def _extract_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\n", "", raw)
        if raw.endswith("```"):
            raw = raw[:-3]
    return json.loads(raw)


def _recompute_pass(result: dict) -> dict:
    scores = result.get("scores") or {}
    if not REQUIRED_KEYS.issubset(scores.keys()):
        result.setdefault("fail_reason", "invalid_scores_schema")
        result["pass"] = False
        return result
    total = sum(int(scores[k]) for k in REQUIRED_KEYS)
    result["total_score"] = total
    all_pass = all(int(scores[k]) >= MIN_PASS for k in REQUIRED_KEYS)
    if not all_pass and result.get("pass"):
        result["pass"] = False
        result["fail_reason"] = result.get("fail_reason") or (
            f"항목별 최소 {MIN_PASS}점 미달"
        )
    return result


def evaluate(text: str, model: str = DEFAULT_MODEL) -> dict:
    system, user_tpl = _load_template()
    user = user_tpl.replace("<<IDEA_TEXT>>", text.strip())
    raw = _call_claude(system, user, model)
    result = _extract_json(raw)
    return _recompute_pass(result)


def _update_raw_frontmatter(path: Path, result: dict) -> None:
    fm, body = _read_raw(path)
    fm["status"] = "passed" if result.get("pass") else "failed"
    fm["total_score"] = str(result.get("total_score", 0))
    fm["category"] = result.get("category", "")
    if not result.get("pass"):
        fm["fail_reason"] = (result.get("fail_reason") or "").replace("\n", " ")
    rendered = ["---"]
    for k, v in fm.items():
        rendered.append(f"{k}: {v}")
    rendered.append("---\n")
    path.write_text("\n".join(rendered) + "\n" + body + "\n", encoding="utf-8")


def _write_candidate(src: Path | None, result: dict, body: str) -> Path:
    cand_dir = Path("ideas/candidates")
    cand_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(result.get("title") or (src.stem if src else "manual"))
    path = cand_dir / f"{slug}.md"
    scores = result.get("scores", {})
    lines = [
        "---",
        f"title: {result.get('title', '')!r}",
        f"category: {result.get('category', '')}",
        f"total_score: {result.get('total_score', 0)}",
        f"source_file: {src.as_posix() if src else 'manual'}",
        "status: candidate",
        "tags: " + ",".join(result.get("tags") or []),
        "---",
        "",
        f"# {result.get('title', '')}",
        "",
        "## 점수",
        "| 기준 | 점수 |",
        "|---|---|",
        f"| 기획 속도 | {scores.get('기획속도', 0)}/10 |",
        f"| MVP 속도 | {scores.get('MVP속도', 0)}/10 |",
        f"| 고객 확보 | {scores.get('고객확보', 0)}/10 |",
        f"| 수익 가능성 | {scores.get('수익가능성', 0)}/10 |",
        f"| 반복 수익 | {scores.get('반복수익', 0)}/10 |",
        f"| **합계** | **{result.get('total_score', 0)}/50** |",
        "",
        "## 요약",
        result.get("summary", ""),
        "",
        "## MVP 제안",
        result.get("mvp_idea", ""),
        "",
        "## 원문",
        body.strip(),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--file", help="raw markdown 경로")
    grp.add_argument("--text", help="평가할 텍스트 문자열")
    grp.add_argument("--stdin", action="store_true", help="stdin에서 텍스트 읽기")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="candidates/raw를 변경하지 않고 JSON만 출력",
    )
    args = parser.parse_args()

    src: Path | None = None
    if args.file:
        src = Path(args.file)
        fm, body = _read_raw(src)
        text = f"제목: {fm.get('title', '')}\n출처: {fm.get('url', '')}\n\n{body}"
    elif args.stdin:
        text = sys.stdin.read()
        body = text
    else:
        text = args.text or ""
        body = text

    result = evaluate(text, model=args.model)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if args.no_write:
        return 0
    if src is not None:
        _update_raw_frontmatter(src, result)
    if result.get("pass"):
        cand_path = _write_candidate(src, result, body)
        print(f"[eval] PASS → {cand_path}", file=sys.stderr)
    else:
        print(f"[eval] FAIL — {result.get('fail_reason')}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
