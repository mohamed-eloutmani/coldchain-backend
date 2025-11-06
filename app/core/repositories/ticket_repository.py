from typing import Optional, List, Dict
from django.utils import timezone
from django.db.models import QuerySet, Count
from ..models import Ticket, Device, Measurement


class TicketRepository:
    # -------- Basics --------
    @staticmethod
    def get_open_by_id(ticket_id: int) -> Ticket:
        return Ticket.objects.get(id=ticket_id, status="OPEN")

    @staticmethod
    def open_tickets() -> QuerySet[Ticket]:
        return Ticket.objects.filter(status="OPEN").select_related("device").order_by("-opened_at")

    @staticmethod
    def open_for_device(device: Device) -> QuerySet[Ticket]:
        return Ticket.objects.filter(device=device, status="OPEN").order_by("-opened_at")

    @staticmethod
    def count_open() -> int:
        return Ticket.objects.filter(status="OPEN").count()

    # -------- Create --------
    @staticmethod
    def create_open(
        device: Device,
        severity: str,
        reminder_interval_min: int = 30,
        opened_at=None,
    ) -> Ticket:
        return Ticket.objects.create(
            device=device,
            status="OPEN",
            severity=severity,
            opened_at=opened_at or timezone.now(),
            reminder_interval_min=reminder_interval_min,
            last_notified_role_index=0,
            attempt_count=0,
        )

    # -------- Mutations --------
    @staticmethod
    def ack(ticket: Ticket, by: str, when=None) -> Ticket:
        ticket.acked_by = by
        ticket.acked_at = when or timezone.now()
        ticket.attempt_count = 0
        ticket.save(update_fields=["acked_by", "acked_at", "attempt_count"])
        return ticket

    @staticmethod
    def close(ticket: Ticket, when=None) -> Ticket:
        ticket.status = "CLOSED"
        ticket.closed_at = when or timezone.now()
        ticket.save(update_fields=["status", "closed_at"])
        return ticket

    @staticmethod
    def bump_attempt(ticket: Ticket, when=None, role_index: Optional[int] = None) -> Ticket:
        ticket.attempt_count = (ticket.attempt_count or 0) + 1
        ticket.last_notified_at = when or timezone.now()
        if role_index is not None:
            ticket.last_notified_role_index = role_index
        fields = ["attempt_count", "last_notified_at"]
        if role_index is not None:
            fields.append("last_notified_role_index")
        ticket.save(update_fields=fields)
        return ticket

    # -------- Helpers --------
    @staticmethod
    def latest_measurement_text(device: Device) -> str:
        latest = Measurement.objects.filter(device=device).order_by("-ts").first()
        if not latest:
            return "—"
        temp = f"{latest.temp_c:.1f}°C" if latest.temp_c is not None else "—"
        hum = f"{latest.humidity:.0f}%" if latest.humidity is not None else "—"
        return f"{temp} / {hum}"
