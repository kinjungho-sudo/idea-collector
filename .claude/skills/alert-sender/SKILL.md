---
name: alert-sender
description: 일일 TOP 3 아이디어를 텔레그램으로 요약 전송 (이메일 폴백 옵션)
---

# alert-sender

## 역할
- `ideas/source/YYYY-MM-DD_scored.json`의 `top` 상위 3개를 Markdown으로 포맷해 전송
- 기본 채널: 텔레그램 (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`)
- 폴백: `--channel=email` 옵션 + `ALERT_EMAIL_*` env (SMTP)

## 메시지 예시
```
📬 2026-04-18 창업 아이디어 TOP 3

1. (92점) <제목>
   🔗 <url>
   💡 <2줄 요약>

2. (88점) ...
3. (85점) ...
```

## 스크립트
- `scripts/send_telegram.py`
