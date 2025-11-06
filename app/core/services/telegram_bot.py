import json
from django.utils import timezone
from django.conf import settings
from core.models import Ticket, Measurement
from core.utils import send_telegram_message  # you already have this

class TelegramBotService:
    @staticmethod
    def safe_parse_update(request):
        try:
            if isinstance(request.data, dict):
                return request.data
            return json.loads(request.body.decode("utf-8"))
        except Exception:
            return {}

    @staticmethod
    def extract_message(update):
        msg = (update.get("message") or update.get("edited_message")) or {}
        chat = msg.get("chat") or {}
        text = (msg.get("text") or "").strip()
        user = msg.get("from") or {}
        sender = (user.get("username") or user.get("first_name") or "telegram-user")
        return chat.get("id"), text, sender

    @staticmethod
    def send_md(chat_id, text):
        send_telegram_message(chat_id, text, markdown=True)

    @staticmethod
    def reply_start(chat_id):
        TelegramBotService.send_md(
            chat_id,
            "✅ *ColdChain Bot Ready!*\nUse `/status` to see open alerts or `/ack <ticketId>` to acknowledge."
        )

    @staticmethod
    def compose_status_message(filter_code=None):
        roles = getattr(settings, "ESCALATION_ROLES", [])
        qs = Ticket.objects.filter(status="OPEN").select_related("device").order_by("-opened_at")
        if filter_code:
            qs = qs.filter(device__code__iexact=filter_code)
        if not qs.exists():
            base = "📊 *Open tickets:* none."
            return base + (f" (device `{filter_code}`)" if filter_code else "")

        lines = ["📊 *Open tickets:*"]
        now_dt = timezone.now()
        for t in qs[:10]:
            latest = Measurement.objects.filter(device=t.device).order_by("-ts").first()
            temp = f"{latest.temp_c:.1f}°C" if latest and latest.temp_c is not None else "—"
            hum = f"{latest.humidity:.0f}%" if latest and latest.humidity is not None else "—"
            age = int((now_dt - t.opened_at).total_seconds() // 60)
            role = roles[t.last_notified_role_index] if roles and 0 <= t.last_notified_role_index < len(roles) else "N/A"
            emoji = "🔴" if t.severity == "CRITICAL" else "🟠"
            lines.append(
                f"{emoji} *#{t.id}* – `{t.device.code}` *{t.severity}* "
                f"({temp} / {hum}) age: {age}m role: `{role}` attempts: {t.attempt_count}"
            )
        return "\n".join(lines)

    @staticmethod
    def reply_ack(chat_id, res, sender_name):
        if res.get("ok"):
            t = Ticket.objects.get(id=res["ticketId"])
            latest = Measurement.objects.filter(device=t.device).order_by("-ts").first()
            temp_txt = f"{latest.temp_c:.1f}°C" if latest and latest.temp_c is not None else "—"
            TelegramBotService.send_md(
                chat_id,
                f"✅ Ticket *#{t.id}* for `{t.device.code}` acknowledged by *{sender_name}*.\n"
                f"Severity: *{t.severity}* | Temp: {temp_txt}"
            )
        else:
            TelegramBotService.send_md(chat_id, f"⚠️ {res.get('error')}")
