"""HTML/문자열에서 순수 텍스트만 뽑는 공용 헬퍼.

외부 의존성 없이 표준 라이브러리만 사용.
"""

from __future__ import annotations

import html
import re

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t]+")
_NL_RE = re.compile(r"\n{3,}")


def strip_html(src: str) -> str:
    if not src:
        return ""
    # script/style 덩어리 제거
    src = re.sub(r"<script[\s\S]*?</script>", "", src, flags=re.IGNORECASE)
    src = re.sub(r"<style[\s\S]*?</style>", "", src, flags=re.IGNORECASE)
    # <br>, </p>, </div>를 개행으로 치환
    src = re.sub(r"<(br|/p|/div|/li|/h[1-6])\s*/?>", "\n", src, flags=re.IGNORECASE)
    src = _TAG_RE.sub("", src)
    src = html.unescape(src)
    src = _WS_RE.sub(" ", src)
    src = _NL_RE.sub("\n\n", src)
    return src.strip()


def slugify(title: str, max_len: int = 60) -> str:
    s = re.sub(r"[^\w가-힣\s-]", "", title or "").strip().lower()
    s = re.sub(r"[\s_-]+", "-", s)
    return s[:max_len] or "untitled"
