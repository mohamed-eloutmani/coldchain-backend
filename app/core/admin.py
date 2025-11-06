from django.contrib import admin
from .models import Device, Measurement, AlertRule, Ticket

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("code","site","label","is_active","created_at")
    search_fields = ("code","site","label")

@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = ("device","ts","temp_c","humidity","state")
    list_filter = ("state", "device")
    search_fields = ("device__code",)

@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ("device","low_warn","high_warn","low_crit","high_crit","hysteresis")

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("device","status","severity","opened_at","closed_at","last_notified_role_index","attempt_count")
    list_filter = ("status","severity")
