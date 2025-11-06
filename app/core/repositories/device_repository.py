from typing import Optional, List, Dict
from django.utils import timezone
from django.db.models import QuerySet
from ..models import Device, Measurement


class DeviceRepository:
    # -------- Basics --------
    @staticmethod
    def get_by_code(code: str) -> Device:
        return Device.objects.get(code=code)

    @staticmethod
    def get_or_none_by_code(code: str) -> Optional[Device]:
        try:
            return Device.objects.get(code=code)
        except Device.DoesNotExist:
            return None

    @staticmethod
    def list_all(order_by: str = "code") -> QuerySet[Device]:
        return Device.objects.all().order_by(order_by)

    @staticmethod
    def count() -> int:
        return Device.objects.count()

    # -------- Mutations --------
    @staticmethod
    def create(code: str, **fields) -> Device:
        return Device.objects.create(code=code, **fields)

    @staticmethod
    def create_or_activate(code: str, **fields) -> Device:
        obj, _created = Device.objects.get_or_create(code=code, defaults=fields)
        # If it existed but was inactive, revive it
        changed = False
        if fields.get("is_active") is not None and obj.is_active != fields["is_active"]:
            obj.is_active = fields["is_active"]
            changed = True
        # Upsert other fields (label/site, etc.) if provided
        for k, v in fields.items():
            if hasattr(obj, k) and getattr(obj, k) != v:
                setattr(obj, k, v)
                changed = True
        if changed:
            obj.save(update_fields=[*fields.keys(), "is_active"] if "is_active" in fields else [*fields.keys()])
        return obj

    @staticmethod
    def update(device: Device, **fields) -> Device:
        for k, v in fields.items():
            if hasattr(device, k):
                setattr(device, k, v)
        device.save(update_fields=list(fields.keys()))
        return device

    # -------- Convenience helpers --------
    @staticmethod
    def latest_measurement(device: Device) -> Optional[Measurement]:
        return Measurement.objects.filter(device=device).order_by("-ts").first()

    @staticmethod
    def with_latest() -> List[Dict]:
        """
        Lightweight list of all devices and their latest reading (if any).
        """
        items: List[Dict] = []
        for d in DeviceRepository.list_all():
            latest = Measurement.objects.filter(device=d).order_by("-ts").first()
            items.append({
                "code": d.code,
                "name": getattr(d, "label", d.code) or d.code,
                "site": getattr(d, "site", "") or "",
                "isActive": d.is_active,
                "createdAt": d.created_at,
                "latest": {
                    "ts": getattr(latest, "ts", None),
                    "tempC": getattr(latest, "temp_c", None),
                    "humidity": getattr(latest, "humidity", None),
                },
            })
        return items
