from rest_framework import serializers

class TicketCommentSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000)

class TicketResolveSerializer(serializers.Serializer):
    resolution = serializers.CharField(max_length=1000)
