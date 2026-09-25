from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from django.conf import settings
from django.http import JsonResponse


def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password, password_hash):
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def issue_token(user_id, role):
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user_id,
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=settings.JWT_HOURS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def decode_token(token):
    return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])


def set_auth_cookie(response, token):
    response.set_cookie(
        settings.JWT_COOKIE,
        token,
        httponly=True,
        samesite="Lax",
        secure=False,
        path="/",
        max_age=settings.JWT_HOURS * 3600,
    )


def clear_auth_cookie(response):
    response.delete_cookie(settings.JWT_COOKIE, path="/")


class JWTAuthMiddleware:
    """Validate the httpOnly JWT cookie on /api/ routes other than login and logout."""

    OPEN_PATHS = {"/api/auth/login", "/api/auth/logout"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if not path.startswith("/api/") or request.method == "OPTIONS":
            return self.get_response(request)
        if path.rstrip("/") in self.OPEN_PATHS:
            return self.get_response(request)

        token = request.COOKIES.get(settings.JWT_COOKIE)
        if not token:
            return JsonResponse({"detail": "Authentication required"}, status=401)
        try:
            request.jwt_user = decode_token(token)
        except jwt.PyJWTError:
            return JsonResponse({"detail": "Invalid or expired token"}, status=401)
        return self.get_response(request)
