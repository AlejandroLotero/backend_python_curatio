from django.contrib.auth import logout
from django.http import JsonResponse

from .models import ExclusiveSession


class ExclusiveSessionMiddleware:
    """
    Garantiza que la request autenticada corresponda a la sesión exclusiva vigente.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            active_lock = ExclusiveSession.objects.filter(
                user=request.user,
                is_active=True,
            ).first()

            current_session_key = request.session.session_key

            if active_lock and active_lock.session_key != current_session_key:
                logout(request)
                request.session.flush()

                return JsonResponse(
                    {
                        "error": {
                            "code": "SESSION_REPLACED",
                            "message": "Your session was replaced by another tab or device.",
                            "fields": {},
                        }
                    },
                    status=409,
                )

            if active_lock and active_lock.session_key == current_session_key:
                active_lock.touch()

        return self.get_response(request)