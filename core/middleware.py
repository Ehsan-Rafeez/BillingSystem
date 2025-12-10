from django.conf import settings
from django.shortcuts import redirect


class LoginRequiredMiddleware:
    """
    Redirects unauthenticated users to LOGIN_URL except for allowlisted paths.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.allow_prefixes = [
            "/accounts/login",
            "/admin",
            "/static/",
            "/media/",
        ]

    def __call__(self, request):
        path = request.path
        if not request.user.is_authenticated and not self._is_allowed(path):
            return redirect(f"{settings.LOGIN_URL}?next={path}")
        return self.get_response(request)

    def _is_allowed(self, path: str) -> bool:
        return any(path.startswith(prefix) for prefix in self.allow_prefixes)
