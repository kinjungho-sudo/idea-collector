"""ideas/raw/*.md 중 status=raw 항목을 전부 평가.

- 통과한 아이디어는 ideas/candidates/로 복사, raw frontmatter도 갱신
- 탈락 항목은 raw만 유지 + fail_reason 기록
- ideas/index.md 재생성, ideas/log.md 이력 추가
- 텔레그램 알림은 별도 스크립트에서 처리 (notify_new_candidates.py)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
RAW_DIR = ROOT / "ideas" / "raw"
CAND_DIR = ROOT / "ideas" / "candidates"
INDEX_PATH = ROOT / "ideas" / "index.md"
LOG_PATH = ROOT / "ideas" / "log.md"

EVAL_SCRIPT = Path(__file__).parent / "evaluate_idea.py"


def _parse_frontmatter(path: Path) -> tuple[dict, str]:
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


def _rebuild_index() -> None:
    cand_files = sorted(CAND_DIR.glob("*.md"))
    raw_files = sorted(RAW_DIR.glob("*.md"))
    failed: list[tuple[str, str, str]] = []
    for rf in raw_files:
        fm, _ = _parse_frontmatter(rf)
        if fm.get("status") == "failed":
            failed.append((fm.get("title", rf.stem), fm.get("fail_reason", ""), rf.name))

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# 창업 아이디어 후보 목록",
        f"_마지막 업데이트: {now} | 후보: {len(cand_files)}개 | 탈락: {len(failed)}개_",
        "",
        "## 🟢 실험중",
        "_없음_",
        "",
        "## 🟡 검토중",
        "_없음_",
        "",
        "## ✅ 후보 등록",
    ]
    if not cand_files:
        lines.append("_없음_")
    else:
        lines.append("| 제목 | 카테고리 | 총점 | 파일 |")
        lines.append("|---|---|---|---|")
        for cf in cand_files:
            fm, _ = _parse_frontmatter(cf)
            lines.append(
                "| {t} | {c} | {s}/50 | [{f}](candidates/{f}) |".format(
                    t=fm.get("title", cf.stem).replace("|", "｜"),
                    c=fm.get("category", ""),
                    s=fm.get("total_score", 0),
                    f=cf.name,
                )
            )
    lines.extend(["", "## ❌ 탈락"])
    if not failed:
        lines.append("_없음_")
    else:
        lines.append("| 제목 | 사유 | 파일 |")
        lines.append("|---|---|---|")
        for t, reason, fname in failed:
            lines.append(
                f"| {t.replace('|', '｜')} | {reason.replace('|', '｜')} | [{fname}](raw/{fname}) |"
            )
    lines.append("")
    INDEX_PATH.write_text("\n".join(lines), encoding="utf-8")


def _log(msg: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"- {ts} — {msg}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--model", default=os.environ.get("EVAL_MODEL", "claude-sonnet-4-6"))
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CAND_DIR.mkdir(parents=True, exist_ok=True)

    targets: list[Path] = []
    for path in sorted(RAW_DIR.glob("*.md")):
        fm, _ = _parse_frontmatter(path)
        if fm.get("status", "raw") == "raw":
            targets.append(path)
    if not targets:
        print("[batch] 평가 대상 raw 없음")
        _rebuild_index()
        return 0

    passed = 0
    failed = 0
    new_candidates: list[str] = []
    for path in targets:
        print(f"[batch] 평가: {path.name}")
        if args.dry_run:
            continue
        rc = subprocess.call(
            [sys.executable, str(EVAL_SCRIPT), "--file", str(path), "--model", args.model],
            cwd=ROOT,
        )
        if rc != 0:
            _log(f"[eval] 실패: {path.name}")
            continue
        fm_after, _ = _parse_frontmatter(path)
        if fm_after.get("status") == "passed":
            passed += 1
            new_candidates.append(fm_after.get("title", path.stem))
        else:
            failed += 1

    _rebuild_index()
    _log(f"[batch] 평가 완료 — 통과 {passed}, 탈락 {failed}")

    summary = {"passed": passed, "failed": failed, "new_candidates": new_candidates}
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
