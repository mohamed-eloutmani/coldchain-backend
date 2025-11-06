# core/notify.py
import os, requests

def _resolve_chat_id(explicit: str | None = None) -> str | None:
    if explicit:
        return explicit
    chat = os.getenv("TELEGRAM_CHAT_ID")
    if chat and chat != "0":
        return chat
    chat = os.getenv("TG_SITE_PHARMA_MANAGER")
    if chat and chat != "0":
        return chat
    mapping = os.getenv("ROLE_CHAT_IDS", "")
    for part in mapping.split(","):
        if ":" in part:
            _, cid = part.split(":", 1)
            cid = cid.strip()
            if cid and cid != "0":
                return cid
    return None

def telegram_send(text: str, chat_id: str | None = None, markdown: bool = False) -> bool:
    if os.getenv("TELEGRAM_ENABLED", "false").lower() != "true":
        print("[notify] skipped: TELEGRAM_ENABLED!=true")
        return False

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat  = _resolve_chat_id(chat_id)

    if not token or not chat:
        print("[notify] skipped: TELEGRAM_BOT_TOKEN or chat id missing")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat, "text": text}
    if markdown:
        data["parse_mode"] = "Markdown"

    try:
        resp = requests.post(url, data=data, timeout=10)
        ok = resp.ok and resp.json().get("ok") is True
        print(f"[notify] POST {url} -> {resp.status_code} ok={ok} body={resp.text[:200]}")
        return ok
    except Exception as e:
        print(f"[notify] error sending: {e}")
        return False
