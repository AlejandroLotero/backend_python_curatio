from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import User, BitacoraUsuario
from .forms import CrearUsuarioForm, EditarUsuarioAdminForm
from .utils import generar_password


def _request_has_field(request, *names):
    try:
        data = request.data
        return any(name in data for name in names)
    except TypeError:
        return False


def _empty_to_none(val):
    if val is None:
        return None
    if isinstance(val, str) and val.strip() == "":
        return None
    return val


def _merge_admin_update_payload(request, user):
    """
    Combina el usuario actual con los campos enviados (PATCH/PUT parcial o completo).
    """
    merged = {
        "nombre": user.nombre,
        "tipo_documento": user.tipo_documento,
        "numero_documento": user.numero_documento,
        "rol": user.rol,
        "fecha_inicio": user.fecha_inicio,
        "fecha_fin": user.fecha_fin,
        "email": user.email,
        "telefono": user.telefono,
        "telefono_secundario": user.telefono_secundario,
        "direccion": user.direccion,
        "estado": user.estado,
    }
    d = request.data

    if _request_has_field(request, "fullNames", "name", "nombre"):
        merged["nombre"] = d.get("fullNames") or d.get("name") or d.get("nombre") or ""

    if _request_has_field(request, "documentTypes", "document_type", "tipo_documento"):
        merged["tipo_documento"] = (
            d.get("documentTypes") or d.get("document_type") or d.get("tipo_documento") or ""
        )

    if _request_has_field(request, "documentNumber", "document_number", "numero_documento"):
        merged["numero_documento"] = (
            d.get("documentNumber") or d.get("document_number") or d.get("numero_documento") or ""
        )

    if _request_has_field(request, "roles", "role", "rol"):
        merged["rol"] = d.get("roles") or d.get("role") or d.get("rol") or user.rol

    if _request_has_field(request, "startDate", "start_date", "fecha_inicio"):
        merged["fecha_inicio"] = _empty_to_none(
            d.get("startDate") or d.get("start_date") or d.get("fecha_inicio")
        )

    if _request_has_field(request, "endDate", "end_date", "fecha_fin"):
        merged["fecha_fin"] = _empty_to_none(
            d.get("endDate") or d.get("end_date") or d.get("fecha_fin")
        )

    if _request_has_field(request, "email"):
        merged["email"] = d.get("email") or ""

    if _request_has_field(request, "phoneNumber", "phone", "telefono"):
        merged["telefono"] = (
            d.get("phoneNumber") or d.get("phone") or d.get("telefono") or ""
        )

    if _request_has_field(request, "secondaryPhone", "secondary_phone", "telefono_secundario"):
        merged["telefono_secundario"] = _empty_to_none(
            d.get("secondaryPhone") or d.get("secondary_phone") or d.get("telefono_secundario")
        )

    if _request_has_field(request, "address", "direccion"):
        merged["direccion"] = d.get("address") or d.get("direccion") or ""

    if _request_has_field(request, "estado", "is_active", "status"):
        raw = None
        if "estado" in d:
            raw = d.get("estado")
        elif "is_active" in d:
            raw = d.get("is_active")
        else:
            st = d.get("status")
            if isinstance(st, str):
                low = st.strip().lower()
                if low in ("activo", "active", "1", "true"):
                    raw = True
                elif low in ("inactivo", "inactive", "0", "false"):
                    raw = False
                else:
                    raw = st
            else:
                raw = st
        merged["estado"] = bool(raw)

    return merged


def _inactivation_reason_from_request(request):
    return (
        (request.data.get("reason") or "").strip()
        or (request.data.get("inactivation_reason") or "").strip()
        or (request.data.get("justification") or "").strip()
        or (request.data.get("motivo") or "").strip()
    )


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


def _flatten_model_validation_error(exc):
    field_errors = {}
    for field_name, errors in exc.error_dict.items():
        field_errors[field_name] = [str(err) for err in errors]
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
                    "message": "Please correct the highlighted fields.",
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
    send_mail(
        subject="Cuenta creada - Curatio",
        message=(
            f"Hola {user.nombre},\n\n"
            "Tu cuenta ha sido creada correctamente.\n"
            f"Correo: {user.email}\n"
            f"Contraseña temporal: {generated_password}\n\n"
            "Te recomendamos cambiarla cuando ingreses al sistema."
        ),
        from_email=None,
        recipient_list=[user.email],
        fail_silently=False,
    )

    return Response(
        {
            "data": {
                "user": _serialize_user(user)
            },
            "message": "User created successfully."
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "PATCH", "PUT"])
@permission_classes([IsAuthenticated])
def user_detail_resource(request, user_id):
    """
    Recurso detalle de usuario.

    GET: administrador o el mismo usuario dueño del perfil.

    PATCH/PUT (RFADMIN04): solo ADMIN. Actualiza datos de la cuenta; requiere
    justificación visible al pasar a Inactivo; registra bitácora.
    """
    target_user = get_object_or_404(User, pk=user_id)

    if request.method == "GET":
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

    # ---------- PATCH / PUT: actualización por administrador ----------
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

    was_active = bool(target_user.estado)
    merged = _merge_admin_update_payload(request, target_user)

    effective_rol = merged.get("rol") or target_user.rol
    if effective_rol == "Administrador" and merged.get("estado") is False:
        return Response(
            {
                "error": {
                    "code": "INVALID_OPERATION",
                    "message": "No se puede desactivar una cuenta de administrador.",
                    "fields": {},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    proposed_inactive = was_active and not bool(merged.get("estado"))
    if proposed_inactive:
        reason = _inactivation_reason_from_request(request)
        if not reason:
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": (
                            "Para cambiar el estado a Inactivo se requiere una justificación "
                            "(campos: reason, inactivation_reason, justification o motivo)."
                        ),
                        "fields": {
                            "reason": [
                                "Este campo es obligatorio al desactivar la cuenta."
                            ],
                        },
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    photo_file = (
        request.FILES.get("photo")
        or request.FILES.get("foto")
        or request.FILES.get("photoFile")
    )
    form_kwargs = {"data": merged, "instance": target_user}
    if photo_file:
        form_kwargs["files"] = request.FILES

    form = EditarUsuarioAdminForm(**form_kwargs)

    if not form.is_valid():
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Por favor corrija los campos indicados.",
                    "fields": _flatten_form_errors(form),
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = form.save(commit=False)
    if user.rol == "Administrador":
        user.is_staff = True
    else:
        user.is_staff = False
    if photo_file:
        user.foto = photo_file
        try:
            user.full_clean()
        except DjangoValidationError as exc:
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Por favor corrija los campos indicados.",
                        "fields": _flatten_model_validation_error(exc),
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
    user.save()

    bitacora_motivo = (
        _inactivation_reason_from_request(request)
        if proposed_inactive
        else "Cuenta actualizada desde el módulo de gestión de usuarios."
    )
    BitacoraUsuario.objects.create(
        admin=request.user,
        usuario=user,
        accion="ACTUALIZADO",
        motivo=bitacora_motivo,
    )

    return Response(
        {
            "data": {
                "user": _serialize_user(user)
            },
            "message": "Cuenta actualizada exitosamente",
        },
        status=status.HTTP_200_OK,
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