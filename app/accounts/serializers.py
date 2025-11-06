from rest_framework import serializers
from django.contrib.auth import get_user_model
User = get_user_model()

class RegisterStaffSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    class Meta:
        model = User
        fields = ["email", "username", "password"]
    def create(self, data):
        user = User(email=data["email"], username=data["username"])
        user.set_password(data["password"])
        user.save()
        return user