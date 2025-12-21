from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class TokenObtainPairWithUserSerializer(TokenObtainPairSerializer):
    username_field = "email"  

    def validate(self, attrs):
        data = super().validate(attrs)

        data["user"] = {
            "id": self.user.id,
            "email": self.user.email,
            "is_staff": self.user.is_staff,
        }
        return data
