from django.conf import settings
from django.contrib.auth import logout
from django.utils import timezone
from .session_exclusivity_service import SessionExclusivityService

class SessionInactivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.session_expired = False

        if request.user.is_authenticated:
            timeout = settings.SESSION_CONFIG["INACTIVITY_TIMEOUT"]
            last_activity = request.session.get("last_activity_ts")
            now_ts = int(timezone.now().timestamp())

            if last_activity:
                elapsed = now_ts - last_activity

                if elapsed > timeout:
                    current_session_key = request.session.session_key

                    SessionExclusivityService.release_if_owner(
                        user=request.user,
                        session_key=current_session_key,
                    )

                    logout(request)
                    request.session.flush()
                    request.session_expired = True
                    return self.get_response(request)

            request.session["last_activity_ts"] = now_ts

        return self.get_response(request)