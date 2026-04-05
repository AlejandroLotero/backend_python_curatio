from .email_utils import send_account_created_email
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import User, BitacoraUsuario
from .forms import CrearUsuarioForm
from .utils import generar_password


def _is_admin(user):
    """
    Determina si el usuario autenticado tiene rol de administrador.
    """
    return getattr(user, "rol", None) == "Administrador"


def _serialize_user(user):
    """
    Serializa un usuario al formato esperado por el frontend.
    """
    return {
        "id": user.id,
        "name": user.nombre,
        "email": user.email,
        "role": user.rol,
        "is_active": user.estado,
        "email_confirmed": getattr(user, "email_confirmed", True),
        "document_type": user.tipo_documento,
        "document_number": user.numero_documento,
        "phone": user.telefono,
        "secondary_phone": user.telefono_secundario,
        "address": user.direccion,
        "photo": user.foto.url if user.foto else None,
        "start_date": user.fecha_inicio.isoformat() if user.fecha_inicio else None,
        "end_date": user.fecha_fin.isoformat() if user.fecha_fin else None,
        "created_at": user.creado_en.isoformat() if user.creado_en else None,
        "updated_at": user.actualizado_en.isoformat() if user.actualizado_en else None,
    }


def _normalize_create_user_payload(request):
    """
    Normaliza el payload que llega desde el frontend para que encaje con
    el formulario/modelo de Django.

    Acepta nombres del frontend actual y los transforma a nombres del backend.
    También incorpora la foto si llega por multipart/form-data.
    """
    data = request.data.copy()

    normalized = {
        # ===== equivalencias frontend -> backend =====
        "nombre": data.get("fullNames") or data.get("name") or data.get("nombre") or "",
        "tipo_documento": data.get("documentTypes") or data.get("document_type") or data.get("tipo_documento") or "",
        "numero_documento": data.get("documentNumber") or data.get("document_number") or data.get("numero_documento") or "",
        "direccion": data.get("address") or data.get("direccion") or "",
        "telefono": data.get("phoneNumber") or data.get("phone") or data.get("telefono") or "",
        "telefono_secundario": data.get("secondaryPhone") or data.get("secondary_phone") or data.get("telefono_secundario") or "",
        "email": data.get("email") or "",
        "confirmar_email": data.get("confirmEmail") or data.get("confirmar_email") or "",
        "rol": data.get("roles") or data.get("role") or data.get("rol") or "",
        "fecha_inicio": data.get("startDate") or data.get("start_date") or data.get("fecha_inicio") or "",
        "fecha_fin": data.get("endDate") or data.get("end_date") or data.get("fecha_fin") or "",
    }

    # ===== foto / avatar =====
    # DRF puede recibir multipart y exponerlo en request.FILES.
    photo_file = request.FILES.get("photo") or request.FILES.get("foto") or request.FILES.get("photoFile")
    if photo_file:
        normalized["foto"] = photo_file

    return normalized


def _flatten_form_errors(form):
    """
    Convierte errores de Django Forms a un shape simple para frontend.
    """
    field_errors = {}

    for field_name, errors in form.errors.items():
        field_errors[field_name] = [str(error) for error in errors]

    return field_errors


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def users_resource(request):
    """
    Recurso colección de usuarios.

    Métodos:
    - GET: listado paginado y filtrado
    - POST: creación real de usuario por parte de un administrador
    """
    if not _is_admin(request.user):
        return Response(
            {
                "error": {
                    "code": "FORBIDDEN",
                    "message": "You do not have permission.",
                    "fields": {},
                }
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    # =========================
    # GET / listado de usuarios
    # =========================
    if request.method == "GET":
        queryset = User.objects.all().order_by("nombre")

        search = (request.GET.get("search") or "").strip()
        role = (request.GET.get("role") or "").strip()
        status_filter = (request.GET.get("status") or "").strip()
        document = (request.GET.get("document") or "").strip()
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 10))

        if search:
            queryset = queryset.filter(nombre__icontains=search)

        if role:
            queryset = queryset.filter(rol=role)

        if status_filter != "":
            if status_filter.lower() in ["true", "1", "active", "activo"]:
                queryset = queryset.filter(estado=True)
            elif status_filter.lower() in ["false", "0", "inactive", "inactivo"]:
                queryset = queryset.filter(estado=False)

        if document:
            queryset = queryset.filter(
                Q(numero_documento__icontains=document) |
                Q(tipo_documento__icontains=document)
            )

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        return Response({
            "data": {
                "results": [_serialize_user(item) for item in page_obj],
                "pagination": {
                    "count": paginator.count,
                    "num_pages": paginator.num_pages,
                    "page": page_obj.number,
                    "page_size": page_size,
                    "has_next": page_obj.has_next(),
                    "has_previous": page_obj.has_previous(),
                },
                "filters": {
                    "search": search,
                    "role": role,
                    "status": status_filter,
                    "document": document,
                }
            },
            "message": "Users retrieved successfully."
        })

    # =========================
    # POST / crear usuario real
    # =========================
    normalized_payload = _normalize_create_user_payload(request)
    form = CrearUsuarioForm(normalized_payload, request.FILES)

    if not form.is_valid():
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Por favor validar los campos resaltados en rojo ",
                    "fields": _flatten_form_errors(form),
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Creamos usuario sin guardar todavía para setear flags y contraseña
    user = form.save(commit=False)

    # Estado de negocio y estado técnico
    user.estado = True
    user.is_active = True

    # Por flujo administrativo, el correo queda confirmado
    if hasattr(user, "email_confirmed"):
        user.email_confirmed = True

    # Si el nuevo usuario es administrador, habilitar acceso staff
    if user.rol == "Administrador":
        user.is_staff = True

    # Contraseña automática según requerimiento actual
    generated_password = generar_password()
    user.set_password(generated_password)

    # Guardar usuario
    user.save()

    # Registrar en bitácora
    BitacoraUsuario.objects.create(
        admin=request.user,
        usuario=user,
        accion="CREADO",
        motivo="Usuario creado desde el módulo de gestión de usuarios."
    )

    # Enviar correo con la contraseña generada
    # Enviar correo con diseño profesional
    send_account_created_email(user, generated_password)

    return Response(
        {
            "data": {
                "user": _serialize_user(user)
            },
            "message": "User created successfully."
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_detail_resource(request, user_id):
    """
    Recurso detalle de usuario.
    Puede verlo:
    - un administrador
    - el mismo usuario dueño del perfil
    """
    target_user = get_object_or_404(User, pk=user_id)

    if _is_admin(request.user) or request.user.id == target_user.id:
        return Response({
            "data": {
                "user": _serialize_user(target_user)
            },
            "message": "User retrieved successfully."
        })

    return Response(
        {
            "error": {
                "code": "FORBIDDEN",
                "message": "You do not have permission.",
                "fields": {},
            }
        },
        status=status.HTTP_403_FORBIDDEN,
    )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def user_status_resource(request, user_id):
    """
    Actualiza estado activo/inactivo de un usuario.
    Solo un administrador puede hacerlo.
    """
    if not _is_admin(request.user):
        return Response(
            {
                "error": {
                    "code": "FORBIDDEN",
                    "message": "You do not have permission.",
                    "fields": {},
                }
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    target_user = get_object_or_404(User, pk=user_id)

    # Regla de negocio: no desactivar administradores
    if target_user.rol == "Administrador":
        return Response(
            {
                "error": {
                    "code": "INVALID_OPERATION",
                    "message": "Administrator accounts cannot be disabled.",
                    "fields": {},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    next_status = request.data.get("is_active", None)
    reason = (request.data.get("reason") or "").strip()

    if next_status is None:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "is_active is required.",
                    "fields": {
                        "is_active": ["This field is required."]
                    },
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    next_status = bool(next_status)

    target_user.estado = next_status
    target_user.is_active = next_status
    target_user.save(update_fields=["estado", "is_active", "actualizado_en"])

    BitacoraUsuario.objects.create(
        admin=request.user,
        usuario=target_user,
        accion="ACTIVADO" if next_status else "DESACTIVADO",
        motivo=reason,
    )

    return Response({
        "data": {
            "user": _serialize_user(target_user)
        },
        "message": "User status updated successfully."
    })