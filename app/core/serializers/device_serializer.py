from rest_framework import serializers
from core.models import Device

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ("id", "code", "site", "label", "is_active", "created_at")
        read_only_fields = ("id", "created_at")
