# from django.conf import settings
# from django.contrib.auth import logout
# from django.utils import timezone


# class SessionInactivityMiddleware:
#     """
#     Middleware que expira la sesión por inactividad.

#     - Usa SESSION_CONFIG como fuente central de configuración.
#     - Marca la request con `session_expired` para que la vista pueda responder correctamente.
#     """

#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         # Por defecto, la sesión NO está expirada
#         request.session_expired = False

#         if request.user.is_authenticated:
#             timeout = settings.SESSION_CONFIG["INACTIVITY_TIMEOUT"]

#             last_activity = request.session.get("last_activity_ts")
#             now_ts = int(timezone.now().timestamp())

#             if last_activity:
#                 elapsed = now_ts - last_activity

#                 # Si supera el tiempo permitido, cerrar sesión
#                 if elapsed > timeout:
#                     logout(request)
#                     request.session.flush()

#                     # Marcamos que la sesión expiró por inactividad
#                     request.session_expired = True

#                     # No actualizamos last_activity 
#                     return self.get_response(request)

#             # Solo actualizamos actividad si la sesión sigue activa
#             request.session["last_activity_ts"] = now_ts

#         return self.get_response(request)
from django.conf import settings
from django.contrib.auth import logout
from django.utils import timezone


class SessionInactivityMiddleware:
    """
    Middleware que expira la sesión por inactividad.

    Reglas:
    - Usa SESSION_CONFIG como fuente central de configuración.
    - Marca la request con `session_expired` para que la vista de sesión
      pueda responder con un código específico.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Por defecto, asumimos que la sesión no expiró por inactividad.
        request.session_expired = False

        if request.user.is_authenticated:
            timeout = settings.SESSION_CONFIG["INACTIVITY_TIMEOUT"]

            last_activity = request.session.get("last_activity_ts")
            now_ts = int(timezone.now().timestamp())

            if last_activity:
                elapsed = now_ts - last_activity

                # Si superó el umbral de inactividad, se cierra la sesión.
                if elapsed > timeout:
                    logout(request)
                    request.session.flush()

                    # Marcamos la request para que la vista responda
                    # con SESSION_EXPIRED.
                    request.session_expired = True

                    return self.get_response(request)

            # Solo si la sesión sigue activa actualizamos el último timestamp.
            request.session["last_activity_ts"] = now_ts

        return self.get_response(request)