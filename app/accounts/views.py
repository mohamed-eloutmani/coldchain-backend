from rest_framework import generics, permissions
from .serializers import RegisterStaffSerializer

class RegisterStaffView(generics.CreateAPIView):
    serializer_class = RegisterStaffSerializer
    permission_classes = [permissions.IsAdminUser]  # only admin can create staff