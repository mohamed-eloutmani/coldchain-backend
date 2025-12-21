from django.urls import path
from . import views
from . import views_users
from . import views_measurements
from . import views_tickets
from . import views_devices

urlpatterns = [
    # ----------------------------------
    # Measurements & Devices (main data)
    # ----------------------------------
    path("measurements/ingest", views.ingest_measurement, name="ingest_measurement"),
    path("measurements/recent", views.measurements_recent, name="measurements_recent"),
    path("devices", views_devices.devices_list_create, name="devices_list_create"),   # GET + POST
    path("devices/<str:code>/metrics", views_devices.device_metrics, name="device_metrics"),
    path("devices/<str:code>", views_devices.devices_detail_update_delete, name="devices_detail_update_delete"),  # GET/PUT/PATCH/DELETE

    # ----------------------------------
    # Tickets & Escalations
    # ----------------------------------
    path("tickets/open", views.tickets_open, name="tickets_open"),
    path("tickets/<int:ticket_id>/ack", views.ticket_ack, name="ticket_ack"),
    path("escalation/roles", views.escalation_roles, name="escalation_roles"),

    # Ticket extra endpoints
    path("tickets/<int:ticket_id>", views_tickets.ticket_get, name="ticket_get"),
    path("tickets/<int:ticket_id>/comment", views_tickets.ticket_comment, name="ticket_comment"),
    path("tickets/<int:ticket_id>/resolve", views_tickets.ticket_resolve, name="ticket_resolve"),

    # ----------------------------------
    # Telegram webhook (optional)
    # ----------------------------------
    path("telegram/webhook", views.telegram_webhook, name="telegram_webhook"),

    # ----------------------------------
    # Health check / sanity endpoint
    # ----------------------------------
    path("hello", views.HelloView.as_view(), name="hello_view"),

    # --- Users CRUD (admin only) ---
    path("users", views_users.users_list_create, name="users_list_create"),          # GET, POST
    path("users/<int:user_id>", views_users.users_detail, name="users_detail"),

    # Measurements range/export (if you added them)
    path("measurements/range", views_measurements.measurements_range, name="measurements_range"),
    path("measurements/export.csv", views_measurements.measurements_export_csv, name="measurements_export_csv"),
    path("measurements/import.csv", views_measurements.measurements_import_csv),
    # Dashboard stats (if you added it)
    path("dashboard/devices-stats", views.dashboard_devices_stats, name="dashboard_devices_stats"),
]
