from rest_framework.response import Response
from rest_framework.views import APIView

from cti_api.auth import clear_auth_cookie, issue_token, set_auth_cookie, verify_password
from cti_api.db.mongo import users
from cti_api.serializers import LoginSerializer


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"].strip()
        password = serializer.validated_data["password"]
        user = users().find_one({"username": username})
        if not user or not verify_password(password, user.get("password_hash", "")):
            return Response({"detail": "Invalid username or password"}, status=401)
        token = issue_token(user["user_id"], user["role"])
        response = Response({"user_id": user["user_id"], "role": user["role"]})
        set_auth_cookie(response, token)
        return response


class LogoutView(APIView):
    def post(self, request):
        response = Response({"detail": "Logged out"})
        clear_auth_cookie(response)
        return response


class MeView(APIView):
    def get(self, request):
        payload = getattr(request, "jwt_user", {})
        return Response({"user_id": payload.get("user_id"), "role": payload.get("role")})
