from rest_framework import serializers

class DeviceCreateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    location = serializers.CharField(max_length=200, required=False, allow_blank=True)
    active = serializers.BooleanField(required=False, default=True)
    thresholds = serializers.DictField(child=serializers.FloatField(), required=False)

class DeviceUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    location = serializers.CharField(max_length=200, required=False, allow_blank=True)
    active = serializers.BooleanField(required=False)
    thresholds = serializers.DictField(child=serializers.FloatField(), required=False)
