# from django.conf import settings
# from django.contrib.auth import authenticate, login, logout, get_user_model
# from django.contrib.auth.password_validation import validate_password
# from django.contrib.auth.tokens import PasswordResetTokenGenerator
# from django.core.exceptions import ValidationError as DjangoValidationError
# from .email_utils import send_password_reset_email
# from django.middleware.csrf import get_token
# from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
# from django.utils.encoding import force_bytes, force_str

# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import AllowAny
# from rest_framework.response import Response
# from rest_framework import status

# from .user_serializers import serialize_user_for_profile
# from .session_exclusivity_service import SessionExclusivityService

# import time

# User = get_user_model()

# # Generador estándar de tokens de reseteo de Django
# password_reset_token_generator = PasswordResetTokenGenerator()


# def _serialize_session_user(request, user):
#     """
#     Serializa el usuario autenticado al formato esperado por el frontend.
#     """
#     admin = getattr(user, "rol", None) == "Administrador"
#     return serialize_user_for_profile(user, viewer_is_admin=admin, request=request)


# def _get_user_from_uid(uidb64):
#     """
#     Intenta recuperar un usuario a partir del uid codificado.
#     Si falla, retorna None.
#     """
#     try:
#         user_id = force_str(urlsafe_base64_decode(uidb64))
#         return User.objects.filter(pk=user_id).first()
#     except Exception:
#         return None


# def _build_password_reset_link(uidb64, token):
#     """
#     Construye el link que se enviará al correo.
#     Apunta al frontend React.
#     """
#     return f"{settings.FRONTEND_BASE_URL}/reset-password?uid={uidb64}&token={token}"


# def _send_password_reset_email(user, uidb64, token):
#     """
#     Envía el correo de recuperación de contraseña.
#     """
#     send_password_reset_email(user, uidb64, token)


# @api_view(["GET"])
# @permission_classes([AllowAny])
# def csrf_token_view(request):
#     """
#     Genera y devuelve el token CSRF para el frontend.
#     """
#     token = get_token(request)

#     return Response(
#         {
#             "data": {
#                 "csrfToken": token
#             },
#             "message": "CSRF token generated successfully."
#         },
#         status=status.HTTP_200_OK,
#     )


# @api_view(["GET", "POST", "DELETE"])
# @permission_classes([AllowAny])
# def session_resource_view(request):
#     """
#     Recurso de sesión:
#     - GET: obtiene sesión actual
#     - POST: login
#     - DELETE: logout
#     """

#     # =========================
#     # GET / current session
#     # =========================
#     if request.method == "GET":
#     if not request.user.is_authenticated:
#         if getattr(request, "session_expired", False):
#             return Response(
#                 {
#                     "error": {
#                         "code": "SESSION_EXPIRED",
#                         "message": "Session expired due to inactivity.",
#                         "fields": {},
#                     }
#                 },
#                 status=status.HTTP_401_UNAUTHORIZED,
#             )

#         if getattr(request, "session_replaced", False):
#             return Response(
#                 {
#                     "error": {
#                         "code": "SESSION_REPLACED",
#                         "message": "Your session was replaced by another tab or device.",
#                         "fields": {},
#                     }
#                 },
#                 status=status.HTTP_401_UNAUTHORIZED,
#             )

#         return Response(
#             {
#                 "error": {
#                     "code": "UNAUTHENTICATED",
#                     "message": "Authentication required.",
#                     "fields": {},
#                 }
#             },
#             status=status.HTTP_401_UNAUTHORIZED,
#         )
#     )

#     # =========================
#     # POST / login
#     # =========================
#     if request.method == "POST":
#         # Se leen las credenciales como ya lo hacías
#         email = (request.data.get("email") or "").strip().lower()
#         password = request.data.get("password") or ""

#         # Nuevo campo enviado por frontend para identificar la instancia
#         # actual del navegador/pestaña/dispositivo.
#         client_instance_id = (request.data.get("client_instance_id") or "").strip()

#         # Se arma un diccionario de errores por campo para no romper
#         # tu estilo actual de respuestas del backend.
#         field_errors = {}

#         if not email:
#             field_errors["email"] = ["This field is required."]

#         if not password:
#             field_errors["password"] = ["This field is required."]

#         if not client_instance_id:
#             field_errors["client_instance_id"] = ["This field is required."]

#         if field_errors:
#             return Response(
#                 {
#                     "error": {
#                         "code": "VALIDATION_ERROR",
#                         "message": "Email, password and client instance are required.",
#                         "fields": field_errors,
#                     }
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         # Autenticación estándar contra Django usando email como username.
#         user = authenticate(request, username=email, password=password)

#         if user is None:
#             return Response(
#                 {
#                     "error": {
#                         "code": "INVALID_CREDENTIALS",
#                         "message": "Invalid email or password.",
#                         "fields": {},
#                     }
#                 },
#                 status=status.HTTP_401_UNAUTHORIZED,
#             )

#         # Cuenta deshabilitada
#         if not user.is_active or not user.estado:
#             return Response(
#                 {
#                     "error": {
#                         "code": "ACCOUNT_DISABLED",
#                         "message": "This account is disabled.",
#                         "fields": {},
#                     }
#                 },
#                 status=status.HTTP_403_FORBIDDEN,
#             )

#         # Correo no confirmado
#         if not user.email_confirmed:
#             return Response(
#                 {
#                     "error": {
#                         "code": "EMAIL_NOT_CONFIRMED",
#                         "message": "Your email address is not confirmed.",
#                         "fields": {},
#                     }
#                 },
#                 status=status.HTTP_403_FORBIDDEN,
#             )

#         # Se autentica la sesión exactamente como ya lo hacías.
#         login(request, user)

#         # Se fuerza el guardado para garantizar que Django ya tenga
#         # una session_key materializada en base de datos.
#         request.session.save()

#         # Tomamos la clave real de esta sesión para registrarla
#         # como posible dueña de la cuenta.
#         session_key = request.session.session_key

#         # Se intenta adquirir la exclusividad.
#         # Si ya existe otra sesión activa para este usuario,
#         # el servicio no rompe el flujo: devuelve conflicto controlado.
#         exclusivity_result = SessionExclusivityService.acquire_or_detect_conflict(
#             user=user,
#             session_key=session_key,
#             client_instance_id=client_instance_id,
#         )

#         # Si no se pudo adquirir porque ya hay otra sesión distinta,
#         # cerramos esta autenticación provisional para no dejar una sesión
#         # huérfana y respondemos con código específico para que el frontend
#         # muestre el modal de decisión.
#         if not exclusivity_result["success"]:
#             logout(request)
#             request.session.flush()

#             return Response(
#                 {
#                     "error": {
#                         "code": "SESSION_CONFLICT",
#                         "message": "This account is already active in another tab or device.",
#                         "fields": {},
#                     },
#                     "data": {
#                         "can_takeover": True,
#                     }
#                 },
#                 status=status.HTTP_409_CONFLICT,
#             )

#         # Reinicia marca de actividad del middleware de inactividad.
#         request.session["last_activity_ts"] = int(time.time())

#         return Response(
#             {
#                 "data": {
#                     "user": _serialize_session_user(request, user)
#                 },
#                 "message": "Session created successfully."
#             },
#             status=status.HTTP_200_OK,
#         )

#     # =========================
#     # DELETE / logout
#     # =========================
#     if request.method == "DELETE":
#         if not request.user.is_authenticated:
#             return Response(
#                 {
#                     "error": {
#                         "code": "UNAUTHENTICATED",
#                         "message": "Authentication required.",
#                         "fields": {},
#                     }
#                 },
#                 status=status.HTTP_401_UNAUTHORIZED,
#             )

#         # Antes de destruir la sesión de Django, liberamos el lock exclusivo
#         # únicamente si esta sesión era la sesión dueña actual.
#         current_session_key = request.session.session_key

#         SessionExclusivityService.release_if_owner(
#             user=request.user,
#             session_key=current_session_key,
#         )

#         logout(request)
#         request.session.flush()

#         return Response(
#             {
#                 "data": None,
#                 "message": "Session deleted successfully."
#             },
#             status=status.HTTP_200_OK,
#         )


# @api_view(["POST"])
# @permission_classes([AllowAny])
# def password_recovery_request_view(request):
#     """
#     Solicita recuperación de contraseña.
#     """
#     email = (request.data.get("email") or "").strip().lower()

#     if not email:
#         return Response(
#             {
#                 "error": {
#                     "code": "VALIDATION_ERROR",
#                     "message": "Email is required.",
#                     "fields": {
#                         "email": ["This field is required."]
#                     },
#                 }
#             },
#             status=status.HTTP_400_BAD_REQUEST,
#         )

#     user = User.objects.filter(email=email).first()
#     recovery_uid = None

#     if user and user.is_active and user.estado and user.email_confirmed:
#         uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
#         token = password_reset_token_generator.make_token(user)

#         _send_password_reset_email(user, uidb64, token)
#         recovery_uid = uidb64

#     return Response(
#         {
#             "data": {
#                 "recovery_uid": recovery_uid
#             },
#             "message": "If the email exists, a password reset message has been sent."
#         },
#         status=status.HTTP_200_OK,
#     )


# @api_view(["POST"])
# @permission_classes([AllowAny])
# def password_recovery_validate_view(request):
#     """
#     Valida uid + token antes del cambio de contraseña.
#     """
#     uid = (request.data.get("uid") or "").strip()
#     token = (request.data.get("token") or "").strip()

#     if not uid or not token:
#         return Response(
#             {
#                 "error": {
#                     "code": "VALIDATION_ERROR",
#                     "message": "UID and token are required.",
#                     "fields": {
#                         "uid": ["This field is required."] if not uid else [],
#                         "token": ["This field is required."] if not token else [],
#                     },
#                 }
#             },
#             status=status.HTTP_400_BAD_REQUEST,
#         )

#     user = _get_user_from_uid(uid)

#     if user is None:
#         return Response(
#             {
#                 "error": {
#                     "code": "INVALID_TOKEN",
#                     "message": "Invalid recovery context.",
#                     "fields": {},
#                 }
#             },
#             status=status.HTTP_400_BAD_REQUEST,
#         )

#     if not password_reset_token_generator.check_token(user, token):
#         return Response(
#             {
#                 "error": {
#                     "code": "INVALID_TOKEN",
#                     "message": "The token is invalid or expired.",
#                     "fields": {},
#                 }
#             },
#             status=status.HTTP_400_BAD_REQUEST,
#         )

#     return Response(
#         {
#             "data": {
#                 "valid": True
#             },
#             "message": "Token validated successfully."
#         },
#         status=status.HTTP_200_OK,
#     )


# @api_view(["POST"])
# @permission_classes([AllowAny])
# def password_recovery_confirm_view(request):
#     """
#     Confirma el cambio de contraseña usando uid + token + nueva contraseña.
#     """
#     uid = (request.data.get("uid") or "").strip()
#     token = (request.data.get("token") or "").strip()
#     password = request.data.get("password") or ""
#     confirm_password = request.data.get("confirm_password") or ""

#     field_errors = {}

#     if not uid:
#         field_errors["uid"] = ["This field is required."]
#     if not token:
#         field_errors["token"] = ["This field is required."]
#     if not password:
#         field_errors["password"] = ["This field is required."]
#     if not confirm_password:
#         field_errors["confirm_password"] = ["This field is required."]

#     if field_errors:
#         return Response(
#             {
#                 "error": {
#                     "code": "VALIDATION_ERROR",
#                     "message": "No estás cumpliendo con las reglas de negocio",
#                     "fields": field_errors,
#                 }
#             },
#             status=status.HTTP_400_BAD_REQUEST,
#         )

#     if password != confirm_password:
#         return Response(
#             {
#                 "error": {
#                     "code": "VALIDATION_ERROR",
#                     "message": "Passwords do not match.",
#                     "fields": {
#                         "confirm_password": ["Passwords do not match."]
#                     },
#                 }
#             },
#             status=status.HTTP_400_BAD_REQUEST,
#         )

#     user = _get_user_from_uid(uid)

#     if user is None:
#         return Response(
#             {
#                 "error": {
#                     "code": "INVALID_TOKEN",
#                     "message": "Invalid recovery context.",
#                     "fields": {},
#                 }
#             },
#             status=status.HTTP_400_BAD_REQUEST,
#         )

#     if not password_reset_token_generator.check_token(user, token):
#         return Response(
#             {
#                 "error": {
#                     "code": "INVALID_TOKEN",
#                     "message": "The token is invalid or expired.",
#                     "fields": {},
#                 }
#             },
#             status=status.HTTP_400_BAD_REQUEST,
#         )

#     try:
#         validate_password(password, user=user)
#     except DjangoValidationError as exc:
#         return Response(
#             {
#                 "error": {
#                     "code": "VALIDATION_ERROR",
#                     "message": "Password does not meet security policy.",
#                     "fields": {
#                         "password": list(exc.messages)
#                     },
#                 }
#             },
#             status=status.HTTP_400_BAD_REQUEST,
#         )

#     user.set_password(password)
#     user.save(update_fields=["password"])

#     return Response(
#         {
#             "data": None,
#             "message": "Password updated successfully."
#         },
#         status=status.HTTP_200_OK,
#     )


# @api_view(["POST"])
# @permission_classes([AllowAny])
# def session_takeover_view(request):
#     """
#     Crea una nueva sesión autenticada y fuerza la transferencia de posesión.

#     Se usa cuando el usuario decide quedarse en la pestaña o dispositivo actual.
#     """
#     email = (request.data.get("email") or "").strip().lower()
#     password = request.data.get("password") or ""
#     client_instance_id = (request.data.get("client_instance_id") or "").strip()

#     field_errors = {}

#     if not email:
#         field_errors["email"] = ["This field is required."]
#     if not password:
#         field_errors["password"] = ["This field is required."]
#     if not client_instance_id:
#         field_errors["client_instance_id"] = ["This field is required."]

#     if field_errors:
#         return Response(
#             {
#                 "error": {
#                     "code": "VALIDATION_ERROR",
#                     "message": "Email, password and client instance are required.",
#                     "fields": field_errors,
#                 }
#             },
#             status=status.HTTP_400_BAD_REQUEST,
#         )

#     user = authenticate(request, username=email, password=password)

#     if user is None:
#         return Response(
#             {
#                 "error": {
#                     "code": "INVALID_CREDENTIALS",
#                     "message": "Invalid email or password.",
#                     "fields": {},
#                 }
#             },
#             status=status.HTTP_401_UNAUTHORIZED,
#         )

#     if not user.is_active or not user.estado:
#         return Response(
#             {
#                 "error": {
#                     "code": "ACCOUNT_DISABLED",
#                     "message": "This account is disabled.",
#                     "fields": {},
#                 }
#             },
#             status=status.HTTP_403_FORBIDDEN,
#         )

#     if not user.email_confirmed:
#         return Response(
#             {
#                 "error": {
#                     "code": "EMAIL_NOT_CONFIRMED",
#                     "message": "Your email address is not confirmed.",
#                     "fields": {},
#                 }
#             },
#             status=status.HTTP_403_FORBIDDEN,
#         )

#     login(request, user)
#     request.session.save()

#     SessionExclusivityService.force_takeover(
#         user=user,
#         new_session_key=request.session.session_key,
#         new_client_instance_id=client_instance_id,
#     )

#     request.session["last_activity_ts"] = int(time.time())

#     return Response(
#         {
#             "data": {
#                 "user": _serialize_session_user(request, user),
#             },
#             "message": "Session takeover completed successfully.",
#         },
#         status=status.HTTP_200_OK,
#     )

from django.conf import settings
#Tras guardar la nueva contraseña se llama a update_session_auth_hash(request, user), que alinea la sesión actual con el nuevo hash, 
#para que puedas seguir navegando (perfil, etc.) sin tener que iniciar sesión otra vez.
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.middleware.csrf import get_token
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .email_utils import send_password_reset_email
from .user_serializers import serialize_user_for_profile
from .session_exclusivity_service import SessionExclusivityService

import time

User = get_user_model()

password_reset_token_generator = PasswordResetTokenGenerator()


def _serialize_session_user(request, user):
    """
    Serializa el usuario autenticado al formato esperado por el frontend.
    """
    admin = getattr(user, "rol", None) == "Administrador"
    return serialize_user_for_profile(user, viewer_is_admin=admin, request=request)


def _get_user_from_uid(uidb64):
    """
    Intenta recuperar un usuario a partir del uid codificado.
    Si falla, retorna None.
    """
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        return User.objects.filter(pk=user_id).first()
    except Exception:
        return None


def _build_password_reset_link(uidb64, token):
    """
    Construye el link que se enviará al correo.
    Apunta al frontend React.
    """
    return f"{settings.FRONTEND_BASE_URL}/reset-password?uid={uidb64}&token={token}"


def _send_password_reset_email(user, uidb64, token):
    """
    Envía el correo de recuperación de contraseña.
    """
    send_password_reset_email(user, uidb64, token)


@api_view(["GET"])
@permission_classes([AllowAny])
def csrf_token_view(request):
    """
    Genera y devuelve el token CSRF para el frontend.
    """
    token = get_token(request)

    return Response(
        {
            "data": {
                "csrfToken": token,
            },
            "message": "CSRF token se ha genarado correctamente.",
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET", "POST", "DELETE"])
@permission_classes([AllowAny])
def session_resource_view(request):
    """
    Recurso de sesión:
    - GET: obtiene sesión actual
    - POST: login
    - DELETE: logout
    """

    # =========================
    # GET / current session
    # =========================
    if request.method == "GET":
        if not request.user.is_authenticated:
            if getattr(request, "session_expired", False):
                return Response(
                    {
                        "error": {
                            "code": "SESSION_EXPIRED",
                            "message": "Su sesion ha expirado por inactividad.",
                            "fields": {},
                        }
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            if getattr(request, "session_replaced", False):
                return Response(
                    {
                        "error": {
                            "code": "SESSION_REPLACED",
                            "message": "Su sesion fue reemplazada por otra pestaña o dispositivo.",
                            "fields": {},
                        }
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            return Response(
                {
                    "error": {
                        "code": "UNAUTHENTICATED",
                        "message": "Autenticación requerida.",
                        "fields": {},
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(
            {
                "data": {
                    "user": _serialize_session_user(request, request.user),
                },
                "message": "Sesión obtenida correctamente.",
            },
            status=status.HTTP_200_OK,
        )

    # =========================
    # POST / login
    # =========================
    if request.method == "POST":
        email = (request.data.get("email") or "").strip().lower()
        password = request.data.get("password") or ""
        client_instance_id = (request.data.get("client_instance_id") or "").strip()

        field_errors = {}

        if not email:
            field_errors["email"] = ["This field is required."]

        if not password:
            field_errors["password"] = ["This field is required."]

        if not client_instance_id:
            field_errors["client_instance_id"] = ["This field is required."]

        if field_errors:
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Email, password and client instance are required.",
                        "fields": field_errors,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=email, password=password)

        if user is None:
            return Response(
                {
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "Email o contraseña inválidos.",
                        "fields": {},
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active or not user.estado:
            return Response(
                {
                    "error": {
                        "code": "ACCOUNT_DISABLED",
                        "message": "This account is disabled.",
                        "fields": {},
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user.email_confirmed:
            return Response(
                {
                    "error": {
                        "code": "EMAIL_NOT_CONFIRMED",
                        "message": "Su dirección de correo electrónico no está confirmada.",
                        "fields": {},
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        login(request, user)
        request.session.save()

        session_key = request.session.session_key

        exclusivity_result = SessionExclusivityService.acquire_or_detect_conflict(
            user=user,
            session_key=session_key,
            client_instance_id=client_instance_id,
        )

        if not exclusivity_result["success"]:
            logout(request)
            request.session.flush()

            return Response(
                {
                    "error": {
                        "code": "SESSION_CONFLICT",
                        "message": "Esta cuenta ya está activa en otra pestaña o dispositivo.",
                        "fields": {},
                    },
                    "data": {
                        "can_takeover": True,
                    },
                },
                status=status.HTTP_409_CONFLICT,
            )

        # Reinicia marca de actividad
        login(request, user)
        request.session.save()

        client_instance_id = request.data.get("client_instance_id")

        result = SessionExclusivityService.acquire_or_detect_conflict(
            user=user,
            session_key=request.session.session_key,
            client_instance_id=client_instance_id,
        )

        if not result["success"]:
            return Response(
                {
                    "error": {
                        "code": "SESSION_CONFLICT",
                        "message": "Ya existe una sesión activa.",
                        "fields": {},
                        "meta": {
                            "requires_takeover": True
                        }
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )

        # OK → sesión válida
        import time
        request.session["last_activity_ts"] = int(time.time())

        return Response(
            {
                "data": {
                    "user": _serialize_session_user(request, user),
                },
                "message": "Sesión creada correctamente.",
            },
            status=status.HTTP_200_OK,
        )

    # =========================
    # DELETE / logout
    # =========================
    if request.method == "DELETE":
        if not request.user.is_authenticated:
            return Response(
                {
                    "error": {
                        "code": "UNAUTHENTICATED",
                        "message": "Autenticación requerida.",
                        "fields": {},
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        current_session_key = request.session.session_key

        SessionExclusivityService.release_if_owner(
            user=request.user,
            session_key=current_session_key,
        )

        logout(request)
        request.session.flush()

        return Response(
            {
                "data": None,
                "message": "Sesión eliminada correctamente.",
            },
            status=status.HTTP_200_OK,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def password_recovery_request_view(request):
    """
    Solicita recuperación de contraseña.
    """
    email = (request.data.get("email") or "").strip().lower()

    if not email:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "El email es requerido.",
                    "fields": {
                        "email": ["This field is required."],
                    },
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = User.objects.filter(email=email).first()
    recovery_uid = None

    if user and user.is_active and user.estado and user.email_confirmed:
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = password_reset_token_generator.make_token(user)

        _send_password_reset_email(user, uidb64, token)
        recovery_uid = uidb64

    return Response(
        {
            "data": {
                "recovery_uid": recovery_uid,
            },
            "message": "Si el email existe, se ha enviado un mensaje de recuperación de contraseña.",
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def password_recovery_validate_view(request):
    """
    Valida uid + token antes del cambio de contraseña.
    """
    uid = (request.data.get("uid") or "").strip()
    token = (request.data.get("token") or "").strip()

    if not uid or not token:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "UID y token son requeridos.",
                    "fields": {
                        "uid": ["This field is required."] if not uid else [],
                        "token": ["This field is required."] if not token else [],
                    },
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = _get_user_from_uid(uid)

    if user is None:
        return Response(
            {
                "error": {
                    "code": "INVALID_TOKEN",
                    "message": "Contexto de recuperación inválido.",
                    "fields": {},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not password_reset_token_generator.check_token(user, token):
        return Response(
            {
                "error": {
                    "code": "INVALID_TOKEN",
                    "message": "El token es inválido o ha expirado.",
                    "fields": {},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {
            "data": {
                "valid": True,
            },
            "message": "Token validado correctamente.",
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def password_recovery_confirm_view(request):
    """
    Confirma el cambio de contraseña usando uid + token + nueva contraseña.
    """
    uid = (request.data.get("uid") or "").strip()
    token = (request.data.get("token") or "").strip()
    password = request.data.get("password") or ""
    confirm_password = request.data.get("confirm_password") or ""

    field_errors = {}

    if not uid:
        field_errors["uid"] = ["This field is required."]
    if not token:
        field_errors["token"] = ["This field is required."]
    if not password:
        field_errors["password"] = ["This field is required."]
    if not confirm_password:
        field_errors["confirm_password"] = ["This field is required."]

    if field_errors:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "No estás cumpliendo con las reglas de negocio",
                    "fields": field_errors,
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if password != confirm_password:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Las contraseñas no coinciden.",
                    "fields": {
                        "confirm_password": ["Las contraseñas no coinciden."],
                    },
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = _get_user_from_uid(uid)

    if user is None:
        return Response(
            {
                "error": {
                    "code": "INVALID_TOKEN",
                    "message": "Contexto de recuperación inválido.",
                    "fields": {},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not password_reset_token_generator.check_token(user, token):
        return Response(
            {
                "error": {
                    "code": "INVALID_TOKEN",
                    "message": "El token es inválido o ha expirado.",
                    "fields": {},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        validate_password(password, user=user)
    except DjangoValidationError as exc:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "La contraseña no cumple con la política de seguridad.",
                    "fields": {
                        "password": list(exc.messages),
                    },
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.set_password(password)
    user.save(update_fields=["password"])

    return Response(
        {
            "data": None,
            "message": "Contraseña actualizada correctamente.",
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def session_takeover_view(request):
    """
    Crea una nueva sesión autenticada y fuerza la transferencia de posesión.

    Se usa cuando el usuario decide quedarse en la pestaña o dispositivo actual.
    """
    email = (request.data.get("email") or "").strip().lower()
    password = request.data.get("password") or ""
    client_instance_id = (request.data.get("client_instance_id") or "").strip()

    field_errors = {}

    if not email:
        field_errors["email"] = ["This field is required."]
    if not password:
        field_errors["password"] = ["This field is required."]
    if not client_instance_id:
        field_errors["client_instance_id"] = ["This field is required."]

    if field_errors:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Email, contraseña y cliente son requeridos.",
                    "fields": field_errors,
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(request, username=email, password=password)

    if user is None:
        return Response(
            {
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Email o contraseña inválidos.",
                    "fields": {},
                }
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active or not user.estado:
        return Response(
            {
                "error": {
                    "code": "ACCOUNT_DISABLED",
                    "message": "Esta cuenta está deshabilitada.",
                    "fields": {},
                }
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    if not user.email_confirmed:
        return Response(
            {
                "error": {
                    "code": "EMAIL_NOT_CONFIRMED",
                    "message": "Su dirección de correo electrónico no está confirmada.",
                    "fields": {},
                }
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    login(request, user)
    request.session.save()

    SessionExclusivityService.force_takeover(
        user=user,
        new_session_key=request.session.session_key,
        new_client_instance_id=client_instance_id,
    )

    request.session["last_activity_ts"] = int(time.time())

    return Response(
        {
            "data": {
                "user": _serialize_session_user(request, user),
            },
            "message": "Transferencia de sesión completada correctamente.",
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def password_change_session_view(request):
    """
    Cambio de contraseña para el usuario autenticado (sesión activa).
    No requiere token de correo; valida política con validate_password.
    """
    password = request.data.get("password") or ""
    confirm_password = request.data.get("confirm_password") or ""

    field_errors = {}
    if not password:
        field_errors["password"] = ["This field is required."]
    if not confirm_password:
        field_errors["confirm_password"] = ["This field is required."]

    if field_errors:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "No estás cumpliendo con las reglas de negocio",
                    "fields": field_errors,
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if password != confirm_password:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Passwords do not match.",
                    "fields": {
                        "confirm_password": ["Passwords do not match."]
                    },
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = request.user
    try:
        validate_password(password, user=user)
    except DjangoValidationError as exc:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "La contraseña no cumple con la política de seguridad.",
                    "fields": {
                        "password": list(exc.messages)
                    },
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.set_password(password)
    user.save(update_fields=["password"])
    update_session_auth_hash(request, user) # Alinea la sesión actual con el nuevo hash, para que puedas seguir navegando (perfil, etc.) sin tener que iniciar sesión otra vez.

    return Response(
        {
            "data": None,
            "message": "Contraseña actualizada correctamente."
        },
        status=status.HTTP_200_OK,
    )