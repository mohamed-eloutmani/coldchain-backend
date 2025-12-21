from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from .services.devices import DeviceService
from .serializers.devices import DeviceCreateSerializer, DeviceUpdateSerializer
# app/core/views.py (adjust device_metrics)
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncMinute, TruncHour, TruncDay, TruncWeek, TruncMonth
from django.db.models import Avg, Min, Max
from .services.measurements import MeasurementService


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def devices_list_create(request):
    """
    GET  /api/devices               -> list all devices with latest reading
    POST /api/devices               -> create a device (admin only)
    """
    if request.method == "GET":
        items = DeviceService.list_with_latest()
        return Response(items)

    # POST (admin only)
    if not request.user.is_staff:
        return Response({"detail": "Only admins can create devices."}, status=403)

    ser = DeviceCreateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    dev, err = DeviceService.create_device(**ser.validated_data)
    if err:
        return Response(err, status=status.HTTP_400_BAD_REQUEST)
    return Response(DeviceService.detail_as_dict(dev), status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def devices_detail_update_delete(request, code: str):
    """
    GET    /api/devices/{code}       -> get one
    PUT    /api/devices/{code}       -> full update (admin only)
    PATCH  /api/devices/{code}       -> partial update (admin only)
    DELETE /api/devices/{code}?hard=1 -> deactivate or hard delete (admin only)
    """
    device = DeviceService.get_by_code_or_404(code)

    if request.method == "GET":
        return Response(DeviceService.detail_as_dict(device))

    # Admin-only mutations
    if not request.user.is_staff:
        return Response({"detail": "Only admins can modify devices."}, status=403)

    if request.method in ("PUT", "PATCH"):
        ser = DeviceUpdateSerializer(data=request.data, partial=(request.method == "PATCH"))
        ser.is_valid(raise_exception=True)
        device = DeviceService.update_device(device, ser.validated_data)
        return Response(DeviceService.detail_as_dict(device))

    # DELETE
    hard = request.GET.get("hard") in ("1", "true", "True")
    DeviceService.deactivate_or_delete(device, hard=hard)
    return Response(status=status.HTTP_204_NO_CONTENT)





BUCKET_MAP = {
    "minute": TruncMinute,
    "hour": TruncHour,
    "day": TruncDay,
    "week": TruncWeek,
    "month": TruncMonth,
}

def _resolve_range_and_bucket(req):
    """
    Accepts either:
      - from/to (ISO 8601)
      - or range=day|week|month|year
    And optional bucket=minute|hour|day|week|month (defaults smartly by range)
    """
    now = timezone.now()

    # range preset
    rng = (req.GET.get("range") or "").lower()
    frm = parse_datetime(req.GET.get("from")) if req.GET.get("from") else None
    to  = parse_datetime(req.GET.get("to")) if req.GET.get("to") else None

    if rng and (frm or to):
        # if both are provided, explicit wins (ignore range)
        rng = ""

    if not (frm and to):
        if rng == "day":
            to = now; frm = now - timedelta(days=1)
            default_bucket = "minute"
        elif rng == "week":
            to = now; frm = now - timedelta(days=7)
            default_bucket = "hour"
        elif rng == "month":
            to = now; frm = now - timedelta(days=30)
            default_bucket = "day"
        elif rng == "year":
            to = now; frm = now - timedelta(days=365)
            default_bucket = "week"
        else:
            # fallback: 24h window
            to = now; frm = now - timedelta(days=1)
            default_bucket = "minute"
    else:
        # explicit range → choose bucket based on length
        span = (to - frm).total_seconds()
        if span <= 2*24*3600: default_bucket = "minute"
        elif span <= 14*24*3600: default_bucket = "hour"
        elif span <= 90*24*3600: default_bucket = "day"
        elif span <= 365*24*3600: default_bucket = "week"
        else: default_bucket = "month"

    bucket = (req.GET.get("bucket") or default_bucket).lower()
    if bucket not in BUCKET_MAP:
        bucket = default_bucket

    return frm, to, bucket


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def device_metrics(request, code):
    """
    KPI & time series for a device.
    Supports:
      - ?from=ISO&to=ISO
      - or ?range=day|week|month|year
      - optional ?bucket=minute|hour|day|week|month
    Returns bucketed series with avg/min/max per bucket.
    """
    device = DeviceService.get_by_code_or_404(code)
    frm, to, bucket = _resolve_range_and_bucket(request)

    # Raw queryset in range
    qs = MeasurementService.series(device=device, frm=frm, to=to)

    # Aggregate by bucket using PostgreSQL date_trunc via ORM
    trunc = BUCKET_MAP[bucket]("ts")
    agg = (
        qs.annotate(bucket_ts=trunc)
          .values("bucket_ts")
          .order_by("bucket_ts")
          .annotate(
              temp_avg=Avg("temp_c"),
              temp_min=Min("temp_c"),
              temp_max=Max("temp_c"),
              hum_avg=Avg("humidity"),
              hum_min=Min("humidity"),
              hum_max=Max("humidity"),
          )
    )

    # Build series payload
    series = [
        {
            "t": r["bucket_ts"].isoformat(),
            "temp": round(r["temp_avg"], 2) if r["temp_avg"] is not None else None,
            "temp_min": r["temp_min"],
            "temp_max": r["temp_max"],
            "humidity": round(r["hum_avg"], 2) if r["hum_avg"] is not None else None,
            "hum_min": r["hum_min"],
            "hum_max": r["hum_max"],
        }
        for r in agg
    ]

    # Quick global agg (last window)
    global_agg = {
        "from": frm.isoformat(),
        "to": to.isoformat(),
        "points": len(series),
        "bucket": bucket,
    }

    return Response({"series": series, "agg": global_agg})
