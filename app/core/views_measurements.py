import csv
from io import StringIO
from django.utils.dateparse import parse_datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .services.devices import DeviceService
from .services.measurements import MeasurementService
from .serializers import MeasurementSerializer

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def measurements_range(request):
    """
    GET /api/measurements/range?device=<code>&from=ISO8601&to=ISO8601&limit=1000
    """
    code = request.GET.get("device")
    frm = parse_datetime(request.GET.get("from")) if request.GET.get("from") else None
    to  = parse_datetime(request.GET.get("to")) if request.GET.get("to") else None
    limit = int(request.GET.get("limit") or 1000)

    if code:
        device = DeviceService.get_by_code_or_404(code)
        qs = MeasurementService.series(device=device, frm=frm, to=to)[:limit]
    else:
        qs = MeasurementService.recent_all(limit=limit)  # fallback: last N overall

    return Response(MeasurementSerializer(qs, many=True).data)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def measurements_export_csv(request):
    """
    GET /api/measurements/export.csv?device=<code>&from=ISO&to=ISO
    """
    code = request.GET.get("device")
    frm = parse_datetime(request.GET.get("from")) if request.GET.get("from") else None
    to  = parse_datetime(request.GET.get("to")) if request.GET.get("to") else None

    if code:
        device = DeviceService.get_by_code_or_404(code)
        qs = MeasurementService.series(device=device, frm=frm, to=to)
    else:
        qs = MeasurementService.recent_all(limit=10000)

    # Build CSV in-memory
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["device", "ts", "temp_c", "humidity", "state"])
    for m in qs:
        writer.writerow([getattr(m.device, "code", None), m.ts, m.temp_c, m.humidity, m.state])

    csv_data = buf.getvalue()
    # DRF Response with text/csv
    return Response(csv_data, content_type="text/csv")
