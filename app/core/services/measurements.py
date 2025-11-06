from django.db.models import Avg, Min, Max
from core.models import Measurement, Device

class MeasurementService:
    @staticmethod
    def ingest_from_serializer(serializer):
        """Serializer already validated. Use its create() to persist and return Measurement."""
        return serializer.save()

    @staticmethod
    def series(*, device: Device, frm=None, to=None):
        qs = Measurement.objects.filter(device=device)
        if frm:
            qs = qs.filter(ts__gte=frm)
        if to:
            qs = qs.filter(ts__lte=to)
        return qs.order_by("ts")

    @staticmethod
    def aggregate(qs):
        return qs.aggregate(
            avg_temp=Avg("temp_c"),
            min_temp=Min("temp_c"),
            max_temp=Max("temp_c"),
        )

    @staticmethod
    def recent_for_device(device: Device, *, limit: int = 100):
        return Measurement.objects.filter(device=device).order_by("-ts")[:limit]

    @staticmethod
    def recent_all(*, limit: int = 100):
        return Measurement.objects.all().order_by("-ts")[:limit]
