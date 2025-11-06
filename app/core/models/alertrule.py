from django.db import models

class AlertRule(models.Model):
    device = models.OneToOneField("core.Device", on_delete=models.CASCADE, related_name="alert_rule", null=True, blank=True)
    low_warn = models.FloatField(default=2.0)
    high_warn = models.FloatField(default=8.0)
    low_crit = models.FloatField(default=0.0)
    high_crit = models.FloatField(default=10.0)
    hysteresis = models.FloatField(default=0.3)
