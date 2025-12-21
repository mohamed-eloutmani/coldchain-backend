from django.db import models
from django.utils import timezone

class Device(models.Model):
    code = models.CharField(max_length=64, unique=True)
    site = models.CharField(max_length=128, blank=True, default="")
    label = models.CharField(max_length=128, blank=True, default="")
    is_active = models.BooleanField(default=True)

    min_temp = models.FloatField(default=5.0)
    max_temp = models.FloatField(default=25.0)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.code
