import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _required(name):
    value = os.getenv(name, "").strip()
    if not value or value.startswith("replace-me"):
        raise RuntimeError(
            f"{name} is missing. Copy backend/.env.example to backend/.env and set it."
        )
    return value


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-cti-platform-secret")
DEBUG = os.getenv("DEBUG", "true").lower() in {"1", "true", "yes"}
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "corsheaders",
    "rest_framework",
    "cti_api",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "cti_api.auth.JWTAuthMiddleware",
]

ROOT_URLCONF = "cti_project.urls"
WSGI_APPLICATION = "cti_project.wsgi.application"
ASGI_APPLICATION = "cti_project.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    }
]

# Django still expects a default database entry. Application data lives in
# MongoDB and Neo4j, accessed through cti_api/db — not the ORM.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
APPEND_SLASH = True

MONGO_URI = _required("MONGO_URI")
NEO4J_URI = _required("NEO4J_URI")
NEO4J_USER = _required("NEO4J_USER")
NEO4J_PASSWORD = _required("NEO4J_PASSWORD")
JWT_SECRET = _required("JWT_SECRET")
JWT_COOKIE = "cti_jwt"
JWT_HOURS = 12

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
    "EXCEPTION_HANDLER": "cti_api.exceptions.api_exception_handler",
}
