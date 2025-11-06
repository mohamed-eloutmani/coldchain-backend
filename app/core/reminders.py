# core/reminders.py
from django.utils import timezone
from datetime import timedelta
from core.models import Ticket
from core.notify import telegram_send

def send_open_ticket_reminders():
    now = timezone.now()
    open_tickets = Ticket.objects.filter(status="OPEN")

    for t in open_tickets:
        interval = timedelta(minutes=t.reminder_interval_min)
        if not t.last_notified_at or (now - t.last_notified_at) >= interval:
            telegram_send(f"⏰ {t.device.code} still {t.severity}. Incident open since {t.opened_at:%Y-%m-%d %H:%M UTC}.")
            t.last_notified_at = now
            t.attempt_count = (t.attempt_count or 0) + 1
            t.save(update_fields=["last_notified_at","attempt_count"])
