from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status


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
        "document_type": user.tipo_documento,
        "document_number": user.numero_documento,
        "phone": user.telefono,
        "secondary_phone": user.telefono_secundario,
        "address": user.direccion,
        "photo": user.foto.url if user.foto else None,
        "start_date": user.fecha_inicio.isoformat() if user.fecha_inicio else None,
        "end_date": user.fecha_fin.isoformat() if user.fecha_fin else None,
    }


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

        login(request, user)

        # Reinicia la marca de actividad
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