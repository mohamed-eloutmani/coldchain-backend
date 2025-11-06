from django.db import models

class Measurement(models.Model):
    STATE_CHOICES = [
        ("NORMAL", "NORMAL"),
        ("SEVERE", "SEVERE"),
        ("CRITICAL", "CRITICAL")
    ]
    device = models.ForeignKey("core.Device", on_delete=models.CASCADE, related_name="measurements")
    ts = models.DateTimeField()
    temp_c = models.FloatField()
    humidity = models.FloatField(null=True, blank=True)
    state = models.CharField(max_length=10, choices=STATE_CHOICES)

    class Meta:
        indexes = [
            models.Index(fields=["device", "ts"]),
            models.Index(fields=["state", "ts"]),
        ]
