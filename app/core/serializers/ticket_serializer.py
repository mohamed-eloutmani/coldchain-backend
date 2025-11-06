from rest_framework import serializers
from core.models import Ticket

class TicketSerializer(serializers.ModelSerializer):
    deviceCode = serializers.CharField(source="device.code", read_only=True)

    class Meta:
        model = Ticket
        fields = (
            "id", "device", "deviceCode",
            "status", "severity",
            "opened_at", "closed_at",
            "last_notified_role_index", "attempt_count",
            "acked_by", "acked_at",
        )
        read_only_fields = ("id", "opened_at", "closed_at")
