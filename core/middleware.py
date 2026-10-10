from django.conf import settings
from django.shortcuts import redirect
from django.utils import timezone

from .tenancy import get_current_shop
from .models import ApiToken


class LoginRequiredMiddleware:
    """
    Redirects unauthenticated users to LOGIN_URL except for allowlisted paths.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.allow_prefixes = [
            "/accounts/login",
            "/admin",
            "/api/",
            "/static/",
            "/media/",
        ]

    def __call__(self, request):
        path = request.path
        if not request.user.is_authenticated and not self._is_allowed(path):
            return redirect(f"{settings.LOGIN_URL}?next={path}")
        self._authenticate_api_token(request)
        request.shop = get_current_shop(request)
        return self.get_response(request)

    def _is_allowed(self, path: str) -> bool:
        return any(path.startswith(prefix) for prefix in self.allow_prefixes)

    def _authenticate_api_token(self, request):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return
        token_value = header.removeprefix("Bearer ").strip()
        token = ApiToken.objects.select_related("user").filter(token=token_value).first()
        if not token:
            return
        request.user = token.user
        request.api_token = token
        ApiToken.objects.filter(id=token.id).update(last_used_at=timezone.now())
