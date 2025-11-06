from core.models import AlertRule

class AlertService:
    @staticmethod
    def get_for_device(device):
        try:
            return device.alert_rule
        except AlertRule.DoesNotExist:
            return None

    @staticmethod
    def upsert_for_device(device, *, low_warn, high_warn, low_crit, high_crit, hysteresis):
        obj, _ = AlertRule.objects.update_or_create(
            device=device,
            defaults=dict(
                low_warn=low_warn,
                high_warn=high_warn,
                low_crit=low_crit,
                high_crit=high_crit,
                hysteresis=hysteresis,
            ),
        )
        return obj
