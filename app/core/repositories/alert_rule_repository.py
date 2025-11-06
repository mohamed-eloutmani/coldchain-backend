from typing import Optional
from ..models import AlertRule, Device


class AlertRuleRepository:
    @staticmethod
    def get_for_device(device: Device) -> Optional[AlertRule]:
        try:
            return AlertRule.objects.get(device=device)
        except AlertRule.DoesNotExist:
            return None

    @staticmethod
    def upsert_for_device(
        device: Device,
        low_warn: float,
        high_warn: float,
        low_crit: float,
        high_crit: float,
        hysteresis: float = 0.3,
    ) -> AlertRule:
        obj, created = AlertRule.objects.get_or_create(device=device, defaults={
            "low_warn": low_warn,
            "high_warn": high_warn,
            "low_crit": low_crit,
            "high_crit": high_crit,
            "hysteresis": hysteresis,
        })
        if not created:
            changed = False
            for field, value in {
                "low_warn": low_warn,
                "high_warn": high_warn,
                "low_crit": low_crit,
                "high_crit": high_crit,
                "hysteresis": hysteresis,
            }.items():
                if getattr(obj, field) != value:
                    setattr(obj, field, value)
                    changed = True
            if changed:
                obj.save(update_fields=["low_warn", "high_warn", "low_crit", "high_crit", "hysteresis"])
        return obj

    @staticmethod
    def all() -> list[AlertRule]:
        return list(AlertRule.objects.select_related("device").all())
