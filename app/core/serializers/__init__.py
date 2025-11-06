"""
app/core/serializers
Central export hub for all serializers.
This lets other modules safely do:  from app.core.serializers import <SerializerName>
"""

# Core measurement serializers
from .measurement_serializer import MeasurementSerializer, IngestMeasurementSerializer

# Device serializers (support both naming styles)
try:
    from .devices import DeviceCreateSerializer, DeviceUpdateSerializer
except ImportError:
    try:
        from .device_serializer import DeviceSerializer
    except ImportError:
        DeviceCreateSerializer = DeviceUpdateSerializer = DeviceSerializer = None

# Ticket serializers
try:
    from .tickets import TicketCommentSerializer, TicketResolveSerializer
except ImportError:
    try:
        from .ticket_serializer import TicketSerializer
    except ImportError:
        TicketCommentSerializer = TicketResolveSerializer = TicketSerializer = None

# User serializers
try:
    from .users import UserListSerializer, UserCreateSerializer, UserUpdateSerializer
except ImportError:
    UserListSerializer = UserCreateSerializer = UserUpdateSerializer = None

# Alert rule serializers (if file exists)
try:
    from .alertrule_serializer import AlertRuleSerializer
except ImportError:
    AlertRuleSerializer = None


__all__ = [
    # Measurements
    "MeasurementSerializer",
    "IngestMeasurementSerializer",

    # Devices
    "DeviceCreateSerializer",
    "DeviceUpdateSerializer",
    "DeviceSerializer",

    # Tickets
    "TicketCommentSerializer",
    "TicketResolveSerializer",
    "TicketSerializer",

    # Users
    "UserListSerializer",
    "UserCreateSerializer",
    "UserUpdateSerializer",

    # Alerts (optional)
    "AlertRuleSerializer",
]
