import time
import requests
from django.conf import settings
from django.utils import timezone
from django.core.management.base import BaseCommand
from core.models import Ticket, Measurement
from core.utils import send_telegram_message

API = "https://api.telegram.org/bot{token}/{method}"


def _ack_ticket(ticket_id: int, by: str) -> dict:
    try:
        t = Ticket.objects.get(id=ticket_id, status="OPEN")
        t.acked_by = by
        t.acked_at = timezone.now()
        t.attempt_count = 0
        t.save()
        return {"ok": True, "ticketId": t.id, "acked_by": t.acked_by, "acked_at": t.acked_at}
    except Ticket.DoesNotExist:
        return {"ok": False, "error": f"OPEN ticket {ticket_id} not found"}


def _process_update(update):
    msg = (update.get("message") or update.get("edited_message")) or {}
    chat = msg.get("chat") or {}
    text = (msg.get("text") or "").strip()
    user = msg.get("from") or {}
    sender_name = (user.get("username") or user.get("first_name") or "telegram-user")
    chat_id = chat.get("id")
    if not text or not chat_id:
        return

    if text.lower() == "/start":
        send_telegram_message(
            chat_id,
            "✅ *ColdChain Bot Ready!*\nUse `/status` to see open alerts or `/ack <ticketId>` to acknowledge.",
            markdown=True,
        )
        return

    if text.lower().startswith("/status"):
        parts = text.split(maxsplit=1)
        filter_code = parts[1].strip() if len(parts) == 2 else None
        qs = Ticket.objects.filter(status="OPEN").select_related("device").order_by("-opened_at")
        if filter_code:
            qs = qs.filter(device__code__iexact=filter_code)

        if not qs.exists():
            txt = "📊 *Open tickets:* none."
            if filter_code:
                txt += f" (device `{filter_code}`)"
            send_telegram_message(chat_id, txt, markdown=True)
            return

        lines = ["📊 *Open tickets:*"]
        now_dt = timezone.now()
        for t in qs[:10]:
            latest = Measurement.objects.filter(device=t.device).order_by("-ts").first()
            temp = f"{latest.temp_c:.1f}°C" if latest and latest.temp_c is not None else "—"
            hum  = f"{latest.humidity:.0f}%" if latest and latest.humidity is not None else "—"
            age_minutes = int((now_dt - t.opened_at).total_seconds() // 60)
            emoji = "🔴" if t.severity == "CRITICAL" else "🟠"
            lines.append(
                f"{emoji} *#{t.id}* – `{t.device.code}` *{t.severity}* "
                f"({temp} / {hum})  age: {age_minutes}m  attempts: {t.attempt_count}"
            )
        send_telegram_message(chat_id, "\n".join(lines), markdown=True)
        return

    if text.lower().startswith("/ack"):
        parts = text.split()
        if len(parts) == 2 and parts[1].isdigit():
            res = _ack_ticket(int(parts[1]), sender_name)
            if res.get("ok"):
                t = Ticket.objects.get(id=res["ticketId"])
                latest = Measurement.objects.filter(device=t.device).order_by("-ts").first()
                temp_txt = f"{latest.temp_c:.1f}°C" if latest and latest.temp_c is not None else "—"
                send_telegram_message(
                    chat_id,
                    f"✅ Ticket *#{t.id}* for `{t.device.code}` acknowledged by *{sender_name}*.\n"
                    f"Severity: *{t.severity}* | Temp: {temp_txt}",
                    markdown=True,
                )
            else:
                send_telegram_message(chat_id, f"⚠️ {res.get('error')}", markdown=True)
            return
        send_telegram_message(chat_id, "Usage: `/ack <ticketId>`", markdown=True)
        return

    send_telegram_message(chat_id, "🤖 Unknown command. Try `/status` or `/ack <id>`.", markdown=True)


class Command(BaseCommand):
    help = "Telegram bot polling (no webhook)."

    def handle(self, *args, **kwargs):
        token = settings.TELEGRAM_BOT_TOKEN.strip()
        if not token:
            self.stderr.write(self.style.ERROR("[telegram_bot] TELEGRAM_BOT_TOKEN missing"))
            raise SystemExit(1)

        # Ensure webhook is disabled so polling works
        try:
            del_resp = requests.post(API.format(token=token, method="deleteWebhook"),
                                     data={"drop_pending_updates": "false"}, timeout=15)
            self.stdout.write(self.style.SUCCESS(f"[telegram_bot] deleteWebhook: {del_resp.status_code}"))
        except Exception as e:
            self.stderr.write(self.style.WARNING(f"[telegram_bot] deleteWebhook failed: {e} (continuing)"))

        # Simple health log
        self.stdout.write(self.style.SUCCESS("[telegram_bot] polling started; waiting for messages…"))

        offset = 0
        while True:
            try:
                url = API.format(token=token, method="getUpdates")
                resp = requests.get(url, params={"timeout": 50, "offset": offset + 1}, timeout=60)
                data = resp.json()
                if not data.get("ok"):
                    self.stderr.write(self.style.WARNING(f"[telegram_bot] getUpdates not ok: {data}"))
                    time.sleep(3)
                    continue
                for upd in data.get("result", []):
                    offset = upd["update_id"]
                    _process_update(upd)
            except KeyboardInterrupt:
                self.stdout.write("[telegram_bot] stopping…")
                break
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"[telegram_bot] error: {e}"))
                time.sleep(3)
