from django.utils import timezone
from core.models import Ticket

class TicketService:
    @staticmethod
    def list_open_as_dict(*, roles):
        qs = Ticket.objects.filter(status="OPEN").order_by("-opened_at").select_related("device")
        data = []
        for t in qs:
            role_name = None
            if roles and 0 <= t.last_notified_role_index < len(roles):
                role_name = roles[t.last_notified_role_index]
            data.append({
                "id": t.id,
                "deviceCode": t.device.code,
                "severity": t.severity,
                "opened_at": t.opened_at,
                "attempt_count": t.attempt_count,
                "last_notified_role_index": t.last_notified_role_index,
                "current_role": role_name,
                "acked_by": t.acked_by,
                "acked_at": t.acked_at,
            })
        return data

    @staticmethod
    def ack(*, ticket_id: int, by: str):
        try:
            t = Ticket.objects.get(id=ticket_id, status="OPEN")
        except Ticket.DoesNotExist:
            return {"ok": False, "error": "ticket not found or already closed"}

        t.acked_by = by
        t.acked_at = timezone.now()
        t.attempt_count = 0
        t.save()
        return {"ok": True, "ticketId": t.id, "acked_by": t.acked_by, "acked_at": t.acked_at}
    @staticmethod
    def get_one_as_dict(ticket_id: int):
        try:
            t = Ticket.objects.select_related("device").get(id=ticket_id)
        except Ticket.DoesNotExist:
            raise Http404("Ticket not found")
        return {
            "id": t.id,
            "device": getattr(t.device, "code", None),
            "created_at": t.created_at,
            "state": t.state,
            "last_temp": getattr(t, "last_temp", None),
            "ack_by": t.ack_by,
            "ack_at": t.ack_at,
            "resolution": getattr(t, "resolution", None),
            "resolved_at": getattr(t, "resolved_at", None),
        }

    @staticmethod
    def add_comment(ticket_id: int, message: str, author: str):
        try:
            t = Ticket.objects.get(id=ticket_id)
        except Ticket.DoesNotExist:
            return {"ok": False, "detail": "Not found"}
        # If you have a TicketComment model, create it here; otherwise store in a log list.
        # Example (pseudo):
        # TicketComment.objects.create(ticket=t, author=author, message=message)
        return {"ok": True, "ticket_id": t.id, "message": message, "author": author}

    @staticmethod
    def resolve(ticket_id: int, resolution: str, by: str):
        try:
            t = Ticket.objects.get(id=ticket_id)
        except Ticket.DoesNotExist:
            return {"ok": False, "detail": "Not found"}
        if hasattr(t, "resolve"):
            # If your model has a .resolve() domain method:
            t.resolve(resolution=resolution, by=by)
        else:
            from django.utils import timezone
            t.resolution = resolution
            t.resolved_at = timezone.now()
            t.state = "RESOLVED"
            t.save(update_fields=["resolution", "resolved_at", "state"])
        return {"ok": True, "ticket_id": t.id, "resolution": resolution}
