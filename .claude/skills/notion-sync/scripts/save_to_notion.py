"""스크리닝 결과를 Notion DB에 업서트.

사용: python save_to_notion.py --date 2026-04-18
필요 env: NOTION_TOKEN, NOTION_DATABASE_ID
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

NOTION_VERSION = "2022-06-28"
API = "https://api.notion.com/v1"

SOURCE_MAP = {
    "reddit": "Reddit",
    "hn": "HN",
    "producthunt": "ProductHunt",
    "trends": "Trends",
    "x": "X",
}


def _request(method: str, path: str, body: dict | None = None) -> dict:
    token = os.environ["NOTION_TOKEN"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(f"{API}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Notion {method} {path} {e.code}: {detail}") from e


def _text(val: str) -> list[dict]:
    val = (val or "")[:1900]
    return [{"type": "text", "text": {"content": val}}] if val else []


def _tier(total: int) -> str:
    if total >= 70:
        return "심층분석"
    if total >= 50:
        return "관심목록"
    return "필터링"


def _props(item: dict, date: str) -> dict:
    scores = item.get("scores", {})
    deep = item.get("deep") or {}
    source = SOURCE_MAP.get(item.get("source", ""), item.get("source") or "기타")
    return {
        "아이디어 제목": {"title": _text(item.get("title") or "(제목 없음)")},
        "날짜": {"date": {"start": date}},
        "총점": {"number": int(item.get("total", 0))},
        "등급": {"select": {"name": _tier(int(item.get("total", 0)))}},
        "출처": {"select": {"name": source}},
        "문제 선명도": {"number": int(scores.get("problem_clarity", 0))},
        "타겟 명확도": {"number": int(scores.get("target_clarity", 0))},
        "사업 기회": {"number": int(scores.get("market_opportunity", 0))},
        "초기 비용": {"number": int(scores.get("entry_cost", 0))},
        "국내 가능성": {"number": int(scores.get("domestic_feasibility", 0))},
        "국내 적용 각도": {"rich_text": _text(deep.get("domestic_angle", ""))},
        "MVP 제안": {"rich_text": _text(deep.get("mvp", ""))},
        "첫 수익 경로": {"rich_text": _text(deep.get("first_revenue_path", ""))},
        "AI 활용 가능": {"checkbox": bool(item.get("ai_applicable"))},
        "보안 연계 가능": {"checkbox": bool(item.get("security_linkable"))},
        "상태": {"select": {"name": "검토대기"}},
        "주간 리포트 포함": {"checkbox": False},
        "원본 링크": {"url": item.get("source_url") or None},
        "External ID": {"rich_text": _text(item.get("id", ""))},
    }


def _find_existing(db_id: str, ext_id: str) -> str | None:
    res = _request(
        "POST",
        f"/databases/{db_id}/query",
        {
            "filter": {
                "property": "External ID",
                "rich_text": {"equals": ext_id},
            },
            "page_size": 1,
        },
    )
    pages = res.get("results") or []
    return pages[0]["id"] if pages else None


def upsert(item: dict, date: str, db_id: str) -> str:
    ext_id = item.get("id") or ""
    props = _props(item, date)
    existing = _find_existing(db_id, ext_id) if ext_id else None
    if existing:
        _request("PATCH", f"/pages/{existing}", {"properties": props})
        return f"updated:{existing}"
    res = _request(
        "POST",
        "/pages",
        {"parent": {"database_id": db_id}, "properties": props},
    )
    return f"created:{res['id']}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )
    args = parser.parse_args()

    src = Path(f"ideas/source/{args.date}_scored.json")
    if not src.exists():
        print(f"[notion] {src} 없음", file=sys.stderr)
        return 1
    data = json.loads(src.read_text(encoding="utf-8"))
    db_id = os.environ["NOTION_DATABASE_ID"]

    targets = (data.get("top") or []) + (data.get("watchlist") or [])
    ok = 0
    for it in targets:
        try:
            status = upsert(it, args.date, db_id)
            ok += 1
            print(f"[notion] {status} — {it.get('title','')[:60]}")
        except Exception as exc:  # noqa: BLE001
            print(f"[notion] 실패 {it.get('id')}: {exc}", file=sys.stderr)
    print(f"[notion] {ok}/{len(targets)} 저장 완료")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
