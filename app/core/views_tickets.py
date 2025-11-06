from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .services.tickets import TicketService
from .serializers.tickets import TicketCommentSerializer, TicketResolveSerializer

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ticket_get(request, ticket_id: int):
    data = TicketService.get_one_as_dict(ticket_id)
    return Response(data)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ticket_comment(request, ticket_id: int):
    ser = TicketCommentSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    name = getattr(request.user, "username", None) or getattr(request.user, "email", "operator")
    res = TicketService.add_comment(ticket_id, ser.validated_data["message"], name)
    return Response(res, status=200 if res.get("ok") else 404)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ticket_resolve(request, ticket_id: int):
    ser = TicketResolveSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    name = getattr(request.user, "username", None) or getattr(request.user, "email", "operator")
    res = TicketService.resolve(ticket_id, ser.validated_data["resolution"], name)
    return Response(res, status=200 if res.get("ok") else 404)
