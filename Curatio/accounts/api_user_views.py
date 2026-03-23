from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import User, BitacoraUsuario


def _is_admin(user):
    return getattr(user, "rol", None) == "Administrador"


def _serialize_user(user):
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
        "created_at": user.creado_en.isoformat() if user.creado_en else None,
        "updated_at": user.actualizado_en.isoformat() if user.actualizado_en else None,
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def users_resource(request):
    if not _is_admin(request.user):
        return Response(
            {"error": {"code": "FORBIDDEN", "message": "You do not have permission."}},
            status=status.HTTP_403_FORBIDDEN,
        )

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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_detail_resource(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)

    if _is_admin(request.user) or request.user.id == target_user.id:
        return Response({
            "data": {
                "user": _serialize_user(target_user)
            },
            "message": "User retrieved successfully."
        })

    return Response(
        {"error": {"code": "FORBIDDEN", "message": "You do not have permission."}},
        status=status.HTTP_403_FORBIDDEN,
    )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def user_status_resource(request, user_id):
    if not _is_admin(request.user):
        return Response(
            {"error": {"code": "FORBIDDEN", "message": "You do not have permission."}},
            status=status.HTTP_403_FORBIDDEN,
        )

    target_user = get_object_or_404(User, pk=user_id)

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