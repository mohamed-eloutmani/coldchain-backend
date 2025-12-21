from rest_framework import serializers
from django.utils import timezone
from django.conf import settings

from core.models import Measurement, Device, Ticket
from core.utils import notify_role, classify_state


class MeasurementSerializer(serializers.ModelSerializer):
    deviceCode = serializers.CharField(source="device.code", read_only=True)

    class Meta:
        model = Measurement
        fields = ("id", "deviceCode", "ts", "temp_c", "humidity", "state")


class IngestMeasurementSerializer(serializers.Serializer):
    deviceId = serializers.CharField(max_length=64)
    ts = serializers.DateTimeField()
    tempC = serializers.FloatField()
    humidity = serializers.FloatField(required=False, allow_null=True)

    def create(self, validated_data):
        code = validated_data["deviceId"]
        device, _ = Device.objects.get_or_create(code=code)
        temp = validated_data["tempC"]
        hum = validated_data.get("humidity")
        ts = validated_data["ts"]

        state = classify_state(
            temp,
            min_temp=device.min_temp,
            max_temp=device.max_temp,
        )

        m = Measurement.objects.create(
            device=device, ts=ts, temp_c=temp, humidity=hum, state=state
        )

        if state == "NORMAL":
            Ticket.objects.filter(device=device, status="OPEN").update(
                status="CLOSED", closed_at=timezone.now(), attempt_count=0
            )
        else:
            t, created = Ticket.objects.get_or_create(
                device=device,
                status="OPEN",
                defaults={"severity": ("CRITICAL" if state == "CRITICAL" else "SEVERE")},
            )
            if created:
                t.last_notified_role_index = 0
                t.attempt_count = 1
                t.save()
                notify_role(t.last_notified_role_index, t)
            else:
                if state == "CRITICAL" and t.severity != "CRITICAL":
                    t.severity = "CRITICAL"
                if t.acked_at is None:
                    t.attempt_count += 1
                    roles = getattr(settings, "ESCALATION_ROLES", [])
                    if t.attempt_count >= 4 and roles:
                        max_idx = max(0, len(roles) - 1)
                        new_idx = min(t.last_notified_role_index + 1, max_idx)
                        if new_idx != t.last_notified_role_index:
                            t.last_notified_role_index = new_idx
                            t.attempt_count = 0
                            t.save()
                            notify_role(t.last_notified_role_index, t)
                        else:
                            t.attempt_count = 0
                t.save()

        return m
