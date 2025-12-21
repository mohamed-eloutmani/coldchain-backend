import csv
from io import TextIOWrapper
from django.utils.dateparse import parse_datetime
from django.db import transaction

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.http import HttpResponse

from core.models import Measurement
from .services.devices import DeviceService
from .services.measurements import MeasurementService
from .serializers import MeasurementSerializer


# =========================
# RANGE
# =========================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def measurements_range(request):
    code = request.GET.get("device")
    frm = parse_datetime(request.GET.get("from")) if request.GET.get("from") else None
    to = parse_datetime(request.GET.get("to")) if request.GET.get("to") else None
    limit = int(request.GET.get("limit") or 1000)

    if code:
        device = DeviceService.get_by_code_or_404(code)
        qs = MeasurementService.series(device=device, frm=frm, to=to)[:limit]
    else:
        qs = MeasurementService.recent_all(limit=limit)

    return Response(MeasurementSerializer(qs, many=True).data)


# =========================
# EXPORT CSV
# =========================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def measurements_export_csv(request):
    code = request.GET.get("device")
    frm = parse_datetime(request.GET.get("from")) if request.GET.get("from") else None
    to = parse_datetime(request.GET.get("to")) if request.GET.get("to") else None

    if code:
        device = DeviceService.get_by_code_or_404(code)
        qs = MeasurementService.series(device=device, frm=frm, to=to)
        filename = f"measurements_{device.code}.csv"
    else:
        qs = MeasurementService.recent_all(limit=10000)
        filename = "measurements_all.csv"

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(["device", "timestamp", "temp_c", "humidity", "state"])

    for m in qs:
        writer.writerow([
            m.device.code,
            m.ts.isoformat(),
            m.temp_c,
            m.humidity,
            m.state,
        ])

    return response


# =========================
# IMPORT CSV (ADMIN ONLY)
# =========================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])  # 🔥 REQUIRED
def measurements_import_csv(request):

    if not request.user.is_staff:
        return Response(
            {"detail": "Only admins can import measurements."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if "file" not in request.FILES:
        return Response(
            {"detail": "CSV file is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    file = request.FILES["file"]
    reader = csv.DictReader(TextIOWrapper(file, encoding="utf-8"))

    inserted = 0
    skipped = 0
    errors = []

    with transaction.atomic():
        for line_no, row in enumerate(reader, start=2):
            try:
                device_code = row["device"].strip()
                ts = parse_datetime(row["timestamp"])

                if not ts:
                    raise ValueError("Invalid timestamp")

                temp = float(row["temp_c"]) if row.get("temp_c") else None
                hum = float(row["humidity"]) if row.get("humidity") else None

                device = DeviceService.get_by_code_or_404(device_code)

                if Measurement.objects.filter(device=device, ts=ts).exists():
                    skipped += 1
                    continue

                Measurement.objects.create(
                    device=device,
                    ts=ts,
                    temp_c=temp,
                    humidity=hum,
                )

                inserted += 1

            except Exception as e:
                errors.append({
                    "line": line_no,
                    "error": str(e),
                    "row": row,
                })

    return Response(
        {
            "inserted": inserted,
            "skipped_duplicates": skipped,
            "errors": errors,
        },
        status=status.HTTP_200_OK,
    )
