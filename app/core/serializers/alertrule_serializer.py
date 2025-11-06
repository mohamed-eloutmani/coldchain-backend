from rest_framework import serializers
from core.models import AlertRule

class AlertRuleSerializer(serializers.ModelSerializer):
    deviceCode = serializers.CharField(source="device.code", read_only=True)

    class Meta:
        model = AlertRule
        fields = (
            "id", "device", "deviceCode",
            "low_warn", "high_warn",
            "low_crit", "high_crit",
            "hysteresis",
        )
