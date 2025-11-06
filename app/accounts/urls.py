from django.urls import path
from .views import RegisterStaffView

urlpatterns = [
    path("register-staff", RegisterStaffView.as_view(), name="register_staff"),
]
