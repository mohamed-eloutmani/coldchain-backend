from typing import Optional
from django.db.models import Avg, Min, Max, QuerySet
from ..models import Measurement, Device


class MeasurementRepository:
    # -------- Create --------
    @staticmethod
    def create(
        device: Device,
        ts,
        temp_c: float,
        humidity: Optional[float] = None,
        state: str = "NORMAL",
    ) -> Measurement:
        return Measurement.objects.create(
            device=device, ts=ts, temp_c=temp_c, humidity=humidity, state=state
        )

    # -------- Queries --------
    @staticmethod
    def for_device(device: Device, frm=None, to=None, ascending: bool = True) -> QuerySet[Measurement]:
        qs = Measurement.objects.filter(device=device)
        if frm is not None:
            qs = qs.filter(ts__gte=frm)
        if to is not None:
            qs = qs.filter(ts__lte=to)
        return qs.order_by("ts" if ascending else "-ts")

    @staticmethod
    def last_for_device(device: Device) -> Optional[Measurement]:
        return Measurement.objects.filter(device=device).order_by("-ts").first()

    @staticmethod
    def recent_for_device(device: Device, limit: int = 100) -> QuerySet[Measurement]:
        return Measurement.objects.filter(device=device).order_by("-ts")[:limit]

    @staticmethod
    def recent_all(limit: int = 100) -> QuerySet[Measurement]:
        return Measurement.objects.order_by("-ts")[:limit]

    # -------- Aggregates --------
    @staticmethod
    def aggregate(qs: QuerySet[Measurement]) -> dict:
        return qs.aggregate(
            avg_temp=Avg("temp_c"),
            min_temp=Min("temp_c"),
            max_temp=Max("temp_c"),
        )
