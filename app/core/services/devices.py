from django.utils import timezone
from django.http import Http404
from core.models import Device

# Map public API keys -> real model fields
_FIELD_ALIASES = {
    "name": "label",
    "location": "site",
    "active": "is_active",
}

def _device_field_names():
    return {
        f.name
        for f in Device._meta.get_fields()
        if getattr(f, "concrete", False)
        and not getattr(f, "many_to_many", False)
        and not getattr(f, "one_to_many", False)
    }

_DEVICE_FIELDS = _device_field_names()

def _apply_aliases(data: dict) -> dict:
    """Map external keys (name/location/active) to real model fields (label/site/is_active)."""
    mapped = {}
    for k, v in data.items():
        real = _FIELD_ALIASES.get(k, k)   # e.g. 'location' -> 'site'
        mapped[real] = v
    return mapped


class DeviceService:
    @staticmethod
    def get_by_code_or_404(code: str):
        try:
            return Device.objects.get(code=code)
        except Device.DoesNotExist:
            raise Http404("Device not found")

    @staticmethod
    def create_device(**data):
        # map aliases then keep only real model fields
        data = _apply_aliases(data)
        payload = {k: v for k, v in data.items() if k in _DEVICE_FIELDS}

        if "code" not in payload:
            return None, {"detail": "Field 'code' is required."}

        # sensible defaults if those columns exist
        if "label" in _DEVICE_FIELDS and "label" not in payload:
            payload["label"] = payload["code"]
        if "created_at" in _DEVICE_FIELDS and "created_at" not in payload:
            payload["created_at"] = timezone.now()
        if "is_active" in _DEVICE_FIELDS and "is_active" not in payload:
            payload["is_active"] = True

        if Device.objects.filter(code=payload["code"]).exists():
            return None, {"detail": "Device code already exists."}

        dev = Device.objects.create(**payload)
        return dev, None

    @staticmethod
    def detail_as_dict(device):
        # latest reading if you have related name "measurements"
        latest = device.measurements.order_by("-ts").first() if hasattr(device, "measurements") else None

        return {
            "code": device.code,
            # expose friendly keys, read from real fields
            "name": getattr(device, "label", None) if "label" in _DEVICE_FIELDS else None,
            "location": getattr(device, "site", None) if "site" in _DEVICE_FIELDS else None,
            "active": getattr(device, "is_active", None) if "is_active" in _DEVICE_FIELDS else None,
            "last_temp": getattr(latest, "temp_c", None) if latest else None,
            "last_state": getattr(latest, "state", None) if latest else None,
            "last_ts": getattr(latest, "ts", None) if latest else None,
        }

    @staticmethod
    def update_device(device, data: dict):
        # map aliases and update only real fields
        data = _apply_aliases(data)
        changed = False
        for k, v in data.items():
            if k in _DEVICE_FIELDS:
                setattr(device, k, v)
                changed = True
        if changed:
            device.save()
        return device

    @staticmethod
    def deactivate_or_delete(device, hard=False):
        if hard:
            device.delete()
            return True
        if "is_active" in _DEVICE_FIELDS and getattr(device, "is_active", True):
            device.is_active = False
            device.save(update_fields=["is_active"])
        return True

    @staticmethod
    def list_with_latest():
        items = []
        for d in Device.objects.all():
            items.append(DeviceService.detail_as_dict(d))
        # (optionally sort by code or latest ts)
        return items
