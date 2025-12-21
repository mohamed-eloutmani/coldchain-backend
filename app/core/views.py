# app/core/views.py

from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.views import TokenObtainPairView

# ✅ CORRECT SERIALIZER IMPORTS (NO DUPLICATES)
from core.serializers.jwt import TokenObtainPairWithUserSerializer
from core.serializers.auth import LoginUserSerializer
from core.serializers import IngestMeasurementSerializer, MeasurementSerializer

from core.services.measurements import MeasurementService
from core.services.tickets import TicketService
from core.services.devices import DeviceService
from core.services.telegram_bot import TelegramBotService


# ----------------------------
#  Public API (JWT-protected)
# ----------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ingest_measurement(request):
    ser = IngestMeasurementSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    m = MeasurementService.ingest_from_serializer(ser)
    return Response(MeasurementSerializer(m).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def device_metrics(request, code):
    device = DeviceService.get_by_code_or_404(code)
    frm = parse_datetime(request.GET.get("from")) if request.GET.get("from") else None
    to = parse_datetime(request.GET.get("to")) if request.GET.get("to") else None
    qs = MeasurementService.series(device=device, frm=frm, to=to)
    agg = MeasurementService.aggregate(qs)
    return Response(
        {"series": MeasurementSerializer(qs, many=True).data, "agg": agg}
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def devices_list(request):
    return Response(DeviceService.list_with_latest())


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def measurements_recent(request):
    code = request.GET.get("device")
    limit = int(request.GET.get("limit") or 100)

    if code:
        device = DeviceService.get_by_code_or_404(code)
        qs = MeasurementService.recent_for_device(device, limit=limit)
    else:
        qs = MeasurementService.recent_all(limit=limit)

    return Response(MeasurementSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    return Response(DeviceService.dashboard_summary())


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def tickets_open(request):
    roles = getattr(settings, "ESCALATION_ROLES", [])
    return Response(TicketService.list_open_as_dict(roles=roles))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ticket_ack(request, ticket_id: int):
    name = request.data.get("name") or request.user.email
    res = TicketService.ack(ticket_id=ticket_id, by=name)
    return Response(res, status=200 if res.get("ok") else 404)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def escalation_roles(request):
    roles = getattr(settings, "ESCALATION_ROLES", [])
    return Response({"roles": roles, "count": len(roles)})


# ----------------------------
#  Telegram webhook (optional)
# ----------------------------

@csrf_exempt
@api_view(["POST"])
def telegram_webhook(request):
    update = TelegramBotService.safe_parse_update(request)
    chat_id, text, sender_name = TelegramBotService.extract_message(update)

    if not chat_id or not text:
        return Response({"ok": True})

    if text.lower() == "/start":
        TelegramBotService.reply_start(chat_id)
        return Response({"ok": True})

    if text.lower().startswith("/status"):
        parts = text.split(maxsplit=1)
        code = parts[1].strip() if len(parts) == 2 else None
        msg = TelegramBotService.compose_status_message(code)
        TelegramBotService.send_md(chat_id, msg)
        return Response({"ok": True})

    if text.lower().startswith("/ack"):
        parts = text.split()
        if len(parts) == 2 and parts[1].isdigit():
            res = TicketService.ack(ticket_id=int(parts[1]), by=sender_name)
            TelegramBotService.reply_ack(chat_id, res, sender_name)
            return Response(res, status=200 if res.get("ok") else 404)

        TelegramBotService.send_md(chat_id, "Usage: `/ack <ticketId>`")
        return Response({"ok": False}, status=400)

    TelegramBotService.send_md(chat_id, "🤖 Unknown command.")
    return Response({"ok": True})


# ----------------------------
#  Tiny authenticated sanity view
# ----------------------------

class HelloView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {"message": f"Hello {request.user.email}, your token is valid!"}
        )


# ----------------------------
#  Auth - Login (JWT + user)
# ----------------------------

class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login
    Body: { "email": "...", "password": "..." }
    """
    serializer_class = TokenObtainPairWithUserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user

        return Response(
            {
                "access": serializer.validated_data["access"],
                "refresh": serializer.validated_data["refresh"],
                "user": LoginUserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_devices_stats(request):
    """
    GET /api/dashboard/devices-stats
    Returns counts by last known state: NORMAL / WARNING / CRITICAL / UNKNOWN
    """
    items = DeviceService.list_with_latest()

    counts = {
        "NORMAL": 0,
        "WARNING": 0,
        "CRITICAL": 0,
        "UNKNOWN": 0,
    }

    for d in items:
        state = d.get("last_state") or "UNKNOWN"
        if state not in counts:
            state = "UNKNOWN"
        counts[state] += 1

    return Response(counts)
