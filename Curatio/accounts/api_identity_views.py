from django.conf import settings
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.middleware.csrf import get_token
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

User = get_user_model()

# Generador estándar de tokens de reseteo de Django
password_reset_token_generator = PasswordResetTokenGenerator()


def _serialize_user(user):
    """
    Serializa el usuario autenticado al formato esperado por el frontend.
    """
    return {
        "id": user.id,
        "name": user.nombre,
        "email": user.email,
        "role": user.rol,
        "is_active": user.estado,
        "email_confirmed": user.email_confirmed,
        "document_type": user.tipo_documento,
        "document_number": user.numero_documento,
        "phone": user.telefono,
        "secondary_phone": user.telefono_secundario,
        "address": user.direccion,
        "photo": user.foto.url if user.foto else None,
        "start_date": user.fecha_inicio.isoformat() if user.fecha_inicio else None,
        "end_date": user.fecha_fin.isoformat() if user.fecha_fin else None,
    }


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
    Incluye:
    - link directo
    - token visible
    """
    reset_link = _build_password_reset_link(uidb64, token)

    subject = "Restablecimiento de contraseña - Curatio"
    message = (
        f"Hola {user.nombre},\n\n"
        "Recibimos una solicitud para restablecer tu contraseña.\n\n"
        f"Link de restablecimiento:\n{reset_link}\n\n"
        f"Si necesitas ingresar el token manualmente, usa este token:\n{token}\n\n"
        "Si no solicitaste este cambio, puedes ignorar este correo.\n"
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


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
                "csrfToken": token
            },
            "message": "CSRF token generated successfully."
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
            # Si la sesión expiró por inactividad, informar código específico
            if getattr(request, "session_expired", False):
                return Response(
                    {
                        "error": {
                            "code": "SESSION_EXPIRED",
                            "message": "Session expired due to inactivity.",
                            "fields": {},
                        }
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            return Response(
                {
                    "error": {
                        "code": "UNAUTHENTICATED",
                        "message": "Authentication required.",
                        "fields": {},
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(
            {
                "data": {
                    "user": _serialize_user(request.user)
                },
                "message": "Session retrieved successfully."
            },
            status=status.HTTP_200_OK,
        )

    # =========================
    # POST / login
    # =========================
    if request.method == "POST":
        email = (request.data.get("email") or "").strip().lower()
        password = request.data.get("password") or ""

        if not email or not password:
            return Response(
                {
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "Email and password are required.",
                        "fields": {
                            "email": ["This field is required."] if not email else [],
                            "password": ["This field is required."] if not password else [],
                        },
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
                        "message": "Invalid email or password.",
                        "fields": {},
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Cuenta deshabilitada
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

        # Correo no confirmado
        if not user.email_confirmed:
            return Response(
                {
                    "error": {
                        "code": "EMAIL_NOT_CONFIRMED",
                        "message": "Your email address is not confirmed.",
                        "fields": {},
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        login(request, user)

        # Reinicia marca de actividad
        import time
        request.session["last_activity_ts"] = int(time.time())

        return Response(
            {
                "data": {
                    "user": _serialize_user(user)
                },
                "message": "Session created successfully."
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
                        "message": "Authentication required.",
                        "fields": {},
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        logout(request)
        request.session.flush()

        return Response(
            {
                "data": None,
                "message": "Session deleted successfully."
            },
            status=status.HTTP_200_OK,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def password_recovery_request_view(request):
    """
    Solicita recuperación de contraseña.

    Reglas:
    - Si el correo existe y es elegible, se envía email
    - Si no existe, se responde éxito genérico
    - Si existe, también devolvemos recovery_uid para soportar
      el flujo actual TokenPasswordPage del frontend
    """
    email = (request.data.get("email") or "").strip().lower()

    if not email:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Email is required.",
                    "fields": {
                        "email": ["This field is required."]
                    },
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = User.objects.filter(email=email).first()
    recovery_uid = None

    # Solo enviar si el usuario existe, está activo y tiene correo confirmado
    if user and user.is_active and user.estado and user.email_confirmed:
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = password_reset_token_generator.make_token(user)

        _send_password_reset_email(user, uidb64, token)

        # Se devuelve para soportar el flujo manual del frontend actual
        recovery_uid = uidb64

    return Response(
        {
            "data": {
                "recovery_uid": recovery_uid
            },
            "message": "If the email exists, a password reset message has been sent."
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
                    "message": "UID and token are required.",
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
                    "message": "Invalid recovery context.",
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
                    "message": "The token is invalid or expired.",
                    "fields": {},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {
            "data": {
                "valid": True
            },
            "message": "Token validated successfully."
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
                    "message": "Please correct the highlighted fields.",
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

    user = _get_user_from_uid(uid)

    if user is None:
        return Response(
            {
                "error": {
                    "code": "INVALID_TOKEN",
                    "message": "Invalid recovery context.",
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
                    "message": "The token is invalid or expired.",
                    "fields": {},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Valida contraseña con las reglas globales del proyecto
    try:
        validate_password(password, user=user)
    except DjangoValidationError as exc:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Password does not meet security policy.",
                    "fields": {
                        "password": list(exc.messages)
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
            "message": "Password updated successfully."
        },
        status=status.HTTP_200_OK,
    )