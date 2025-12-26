import os
from pathlib import Path
from datetime import timedelta
from corsheaders.defaults import default_headers

BASE_DIR = Path(__file__).resolve().parent.parent

# ======================================================
# Basic Configuration
# ======================================================
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-key")
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"

# Render uses dynamic hostnames
ALLOWED_HOSTS = ["*"]

# ======================================================
# Telegram Bot
# ======================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# ======================================================
# Installed Apps
# ======================================================
INSTALLED_APPS = [
    "corsheaders",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "rest_framework_simplejwt",

    "core",
    "accounts",
]

# ======================================================
# Middleware (ORDER MATTERS)
# ======================================================
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Render static files
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ======================================================
# URLs & WSGI
# ======================================================
ROOT_URLCONF = "coldchain.urls"
WSGI_APPLICATION = "coldchain.wsgi.application"

# ======================================================
# Templates
# ======================================================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

# ======================================================
# Database (PostgreSQL / Render-ready)
# ======================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.getenv("POSTGRES_HOST", "db"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "NAME": os.getenv("POSTGRES_DB", "coldchain"),
        "USER": os.getenv("POSTGRES_USER", "coldchain"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "coldchain"),
        "CONN_MAX_AGE": 60,
    }
}

# ======================================================
# Localization
# ======================================================
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ======================================================
# Static Files (WhiteNoise + Render)
# ======================================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ======================================================
# Django REST Framework & JWT
# ======================================================
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "SIGNING_KEY": os.getenv("JWT_SECRET", "super-secret-key"),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ======================================================
# Custom User Model
# ======================================================
AUTH_USER_MODEL = "accounts.User"

# ======================================================
# Escalation policy (unchanged)
# ======================================================
ESCALATION_ROLES = [
    "SITE_PHARMA_MANAGER",
    "TECHNICAL_MANAGER",
    "PROCUREMENT_MANAGER",
]

TG_SITE_PHARMA_MANAGER = int(os.getenv("TG_SITE_PHARMA_MANAGER", "0"))
TG_TECHNICAL_MANAGER = int(os.getenv("TG_TECHNICAL_MANAGER", "0"))
TG_PROCUREMENT_MANAGER = int(os.getenv("TG_PROCUREMENT_MANAGER", "0"))

TELEGRAM_ROLE_CHAT_MAP = {
    "SITE_PHARMA_MANAGER": TG_SITE_PHARMA_MANAGER,
    "TECHNICAL_MANAGER": TG_TECHNICAL_MANAGER,
    "PROCUREMENT_MANAGER": TG_PROCUREMENT_MANAGER,
}

# ======================================================
# CORS (Netlify → Render)
# ======================================================
CORS_ALLOW_ALL_ORIGINS = True  # OK for now (restrict later)

CORS_ALLOW_HEADERS = list(default_headers) + [
    "authorization",
]

CORS_ALLOW_CREDENTIALS = True

# ======================================================
# CSRF (required for Render + Netlify)
# ======================================================
CSRF_TRUSTED_ORIGINS = [
    "https://*.onrender.com",
    "https://*.netlify.app",
]
