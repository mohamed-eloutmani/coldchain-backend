from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "is_active", "is_staff", "date_joined"]
        read_only_fields = ["id", "date_joined"]

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=4,
        trim_whitespace=False
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "password",
            "is_active",
            "is_staff",
        ]
        read_only_fields = ["id"]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")

        # ✅ FIX: username is required by Django User model
        if not validated_data.get("username"):
            validated_data["username"] = validated_data["email"]

        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    # Optional password change on update
    password = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=False, min_length=4)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "password", "is_active", "is_staff"]

    def update(self, instance, validated_data):
        pwd = validated_data.pop("password", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if pwd:
            instance.set_password(pwd)
        instance.save()
        return instance
