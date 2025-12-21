import os
import requests
from django.conf import settings

def classify_state(
    temp_c: float,
    *,
    min_temp: float,
    max_temp: float,
    margin: float = 5.0,
):
    if temp_c < min_temp - margin or temp_c > max_temp + margin:
        return "CRITICAL"

    if temp_c < min_temp or temp_c > max_temp:
        return "SEVERE"

    return "NORMAL"


def _role_chat_map():
    """
    ROLE_CHAT_IDS env format:
    ROLE_A:12345,ROLE_B:-100998877,ROLE_C:5555
    """
    raw = os.getenv("ROLE_CHAT_IDS", "")
    res = {}
    for part in [p.strip() for p in raw.split(",") if p.strip()]:
        if ":" in part:
            k, v = part.split(":", 1)
            k = k.strip()
            try:
                res[k] = int(v.strip())
            except ValueError:
                # ignore malformed ids
                pass
    return res

def notify_role(role_index: int, ticket):
    """
    Sends a Telegram message to the chat mapped to the role at role_index.
    Safe no-op if disabled or misconfigured.
    """
    if os.getenv("TELEGRAM_ENABLED", "false").lower() not in ("1", "true", "yes"):
        return

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return

    roles = getattr(settings, "ESCALATION_ROLES", [])
    if not roles:
        return

    role_index = max(0, min(role_index, len(roles) - 1))
    role_name = roles[role_index]

    chat_map = _role_chat_map()
    chat_id = chat_map.get(role_name)
    if not chat_id:
        return  # no chat configured for this role

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    device = ticket.device.code
    text = (
        "🚨 *ColdChain Alert*\n"
        f"Device: `{device}`\n"
        f"Severity: *{ticket.severity}*\n"
        f"Role: *{role_name}*\n"
        f"Attempts since last escalation: {ticket.attempt_count}\n"
        f"Ticket ID: `{ticket.id}`\n"
        "Ack in app or reply later when webhook is enabled."
    )

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }

    try:
        r = requests.post(url, json=payload, timeout=8)
        r.raise_for_status()
    except requests.RequestException:
        # For MVP we stay silent; later add logging if you like
        pass

def send_telegram_message(chat_id: int, text: str, markdown: bool = True) -> dict:
    token = settings.TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if markdown:
        payload["parse_mode"] = "Markdown"
    r = requests.post(url, json=payload, timeout=15)
    try:
        return r.json()
    except Exception:
        return {"ok": False, "status": r.status_code, "text": r.text}