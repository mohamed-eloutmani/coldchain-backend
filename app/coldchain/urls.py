from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from core.views import LoginView

urlpatterns = [
    path("admin/", admin.site.urls),

    # JWT endpoints (UPDATED LOGIN)
    path("api/auth/login", LoginView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh", TokenRefreshView.as_view(), name="token_refresh"),

    # Main ColdChain IoT API
    path("api/", include("core.urls")),
    path("api/accounts/", include("accounts.urls")),
]
