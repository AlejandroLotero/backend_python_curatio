from django.conf import settings
from django.contrib.auth import logout
from django.utils import timezone


class SessionInactivityMiddleware:
    """
    Cierra la sesión si el usuario supera el tiempo máximo de inactividad.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            timeout = getattr(settings, "SESSION_INACTIVITY_TIMEOUT", 60)
            last_activity = request.session.get("last_activity_ts")

            now_ts = int(timezone.now().timestamp())

            if last_activity:
                elapsed = now_ts - last_activity
                if elapsed > timeout:
                    logout(request)
                    request.session.flush()

            request.session["last_activity_ts"] = now_ts

        response = self.get_response(request)
        return response