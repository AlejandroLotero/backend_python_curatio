# from django.contrib.auth import logout
# from django.utils import timezone
# from django.contrib.sessions.models import Session

# from .models import ExclusiveSession


# class ExclusiveSessionMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         request.session_replaced = False

#         if request.user.is_authenticated:
#             current_session_key = request.session.session_key

#             lock = ExclusiveSession.objects.filter(user=request.user).first()

#             # Si no hay lock, no cierres la sesión aquí.
#             # Deja que el flujo de login la reconstruya cuando corresponda.
#             if lock is None:
#                 return self.get_response(request)

#             # Si el lock existe pero está inactivo, tampoco cierres aquí.
#             if not lock.is_active:
#                 return self.get_response(request)

#             # Si el lock apunta a una sesión que ya no existe en django_session,
#             # considéralo huérfano y no expulses esta sesión.
#             lock_session_exists = Session.objects.filter(
#                 session_key=lock.session_key
#             ).exists()

#             if not lock_session_exists:
#                 lock.is_active = False
#                 lock.replaced_at = timezone.now()
#                 lock.save(update_fields=["is_active", "replaced_at"])
#                 return self.get_response(request)

#             # Si esta sesión es la dueña legítima, permitir.
#             if lock.session_key == current_session_key:
#                 lock.last_seen_at = timezone.now()
#                 lock.save(update_fields=["last_seen_at"])
#                 return self.get_response(request)

#             # Solo aquí sí se considera reemplazada por otra sesión real.
#             logout(request)
#             request.session.flush()
#             request.session_replaced = True

#         return self.get_response(request)

from django.contrib.auth import logout
from django.db import DatabaseError
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.sessions.models import Session

from .models import ExclusiveSession


class ExclusiveSessionMiddleware:
    """
    Garantiza que la request autenticada corresponda a la sesión exclusiva vigente.
    También limpia locks huérfanos para evitar falsos conflictos.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.session_replaced = False

        if request.user.is_authenticated:
            try:
                current_session_key = request.session.session_key

                active_lock = (
                    ExclusiveSession.objects.filter(
                        user=request.user,
                        is_active=True,
                    ).first()
                )

                # Si no hay lock activo, no se expulsa al usuario.
                if not active_lock:
                    return self.get_response(request)

                # Si el lock apunta a una sesión que ya no existe,
                # se considera huérfano y se desactiva.
                lock_session_exists = Session.objects.filter(
                    session_key=active_lock.session_key
                ).exists()

                if not lock_session_exists:
                    active_lock.is_active = False
                    active_lock.replaced_at = timezone.now()
                    active_lock.save(update_fields=["is_active", "replaced_at"])
                    return self.get_response(request)

                # Si esta request pertenece a la sesión dueña, se actualiza actividad.
                if active_lock.session_key == current_session_key:
                    active_lock.touch()
                    return self.get_response(request)

                # Solo aquí se considera que realmente hubo reemplazo.
                logout(request)
                request.session.flush()
                request.session_replaced = True

                return JsonResponse(
                    {
                        "error": {
                            "code": "SESSION_REPLACED",
                            "message": "Your session was replaced by another tab or device.",
                            "fields": {},
                        }
                    },
                    status=401,
                )
            except DatabaseError:
                # Tabla accounts_exclusive_session ausente u otro fallo DB: no bloquear la API.
                return self.get_response(request)

        return self.get_response(request)