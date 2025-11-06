from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from .serializers.users import (
    UserListSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
)

User = get_user_model()

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdminUser])
def users_list_create(request):
    """
    GET  /api/users           -> list all users (admin only)
    POST /api/users           -> create user (admin only)
    """
    if request.method == "GET":
        qs = User.objects.all().order_by("-date_joined")
        return Response(UserListSerializer(qs, many=True).data)

    # POST
    ser = UserCreateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    user = ser.save()
    return Response(UserListSerializer(user).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated, IsAdminUser])
def users_detail(request, user_id: int):
    """
    GET    /api/users/{id}     -> retrieve user
    PUT    /api/users/{id}     -> full update
    PATCH  /api/users/{id}     -> partial update
    DELETE /api/users/{id}     -> deactivate (soft-delete); add ?hard=1 to hard delete
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(UserListSerializer(user).data)

    if request.method in ("PUT", "PATCH"):
        partial = (request.method == "PATCH")
        ser = UserUpdateSerializer(user, data=request.data, partial=partial)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(UserListSerializer(user).data)

    # DELETE -> default = soft delete (deactivate)
    hard = request.GET.get("hard") in ("1", "true", "True")
    if hard:
        user.delete()
    else:
        if user.is_active:
            user.is_active = False
            user.save(update_fields=["is_active"])
    return Response(status=status.HTTP_204_NO_CONTENT)
