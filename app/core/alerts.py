# core/alerts.py
from datetime import timedelta
from django.utils import timezone
from core.models import Ticket, Measurement
from core.notify import telegram_send

CLEARANCE_MIN = 10  # normal-for-X minutes before auto-close


def on_violation(device, severity: str):
    now = timezone.now()
    t = Ticket.objects.filter(device=device, status="OPEN").first()

    if not t:
        t = Ticket.objects.create(
            device=device,
            status="OPEN",
            severity=severity,
            opened_at=now,
            last_notified_at=now,
        )
        print(f"[alerts] OPEN ticket #{t.id} {device.code} {severity}", flush=True)
        telegram_send(f"🚨 {device.code} {severity}\nOpened at {now:%Y-%m-%d %H:%M UTC}")
        return

    # Escalate SEVERE -> CRITICAL once
    if t.severity != severity and severity == "CRITICAL":
        t.severity = "CRITICAL"
        t.last_notified_at = now
        t.save(update_fields=["severity", "last_notified_at"])
        print(f"[alerts] ESCALATE ticket #{t.id} -> CRITICAL", flush=True)
        telegram_send(f"⏫ {device.code} escalated to CRITICAL at {now:%H:%M} UTC")

    # Still violating: reminders handle periodic pings


def on_recovery(device):
    t = Ticket.objects.filter(device=device, status="OPEN").first()
    if not t:
        return

    now = timezone.now()
    since = now - timedelta(minutes=CLEARANCE_MIN)
    recent_states = list(
        Measurement.objects.filter(device=device, ts__gte=since).values_list("state", flat=True)
    )

    if recent_states and all(s == "NORMAL" for s in recent_states):
        t.status = "CLOSED"
        t.closed_at = now
        t.save(update_fields=["status", "closed_at"])
        print(f"[alerts] RESOLVE ticket #{t.id}", flush=True)
        telegram_send(f"✅ {device.code} back to normal\nClosed at {now:%Y-%m-%d %H:%M UTC}")
