from django.db import models
from django.utils import timezone

class Ticket(models.Model):
    STATUS_CHOICES = [("OPEN", "OPEN"), ("CLOSED", "CLOSED")]
    SEVERITY_CHOICES = [("SEVERE", "SEVERE"), ("CRITICAL", "CRITICAL")]

    device = models.ForeignKey("core.Device", on_delete=models.CASCADE, related_name="tickets")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="OPEN")
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    opened_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)

    last_notified_role_index = models.IntegerField(default=0)
    attempt_count = models.IntegerField(default=0)
    acked_by = models.CharField(max_length=128, null=True, blank=True)
    acked_at = models.DateTimeField(null=True, blank=True)
    last_notified_at = models.DateTimeField(null=True, blank=True)
    reminder_interval_min = models.IntegerField(default=30)

    class Meta:
        indexes = [models.Index(fields=["device", "status", "opened_at"])]
