from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),

    # JWT endpoints
    path("api/auth/login", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh", TokenRefreshView.as_view(), name="token_refresh"),

    # Main ColdChain IoT API
    path("api/", include("core.urls")),
    path("api/accounts/", include("accounts.urls")),  # if you keep your user endpoints
]
