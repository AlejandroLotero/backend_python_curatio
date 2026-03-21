from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import (
    Medicamento,
    FormaFarmaceutica,
    Presentacion,
    ViaAdministracion,
    Laboratorio,
    EstadoMedicamento,
    Proveedor,
    MedicamentoHistorial,
)
from .forms import CrearMedicamentoForm, ActualizarMedicamentoForm


def _is_admin(user):
    return getattr(user, "rol", None) == "Administrador"


def _serialize_medication(m):
    return {
        "id": m.id,
        "name": m.nombre,
        "pharmaceutical_form": {
            "id": m.forma.id,
            "name": m.forma.nombre,
        } if m.forma else None,
        "presentation": {
            "id": m.presentacion.id,
            "name": m.presentacion.nombre,
        } if m.presentacion else None,
        "concentration": m.concentracion,
        "description": m.descripcion,
        "administration_route": {
            "id": m.via_administracion.id,
            "name": m.via_administracion.nombre,
        } if m.via_administracion else None,
        "laboratory": {
            "id": m.laboratorio.id,
            "name": m.laboratorio.nombre,
        } if m.laboratorio else None,
        "batch": m.lote,
        "manufacturing_date": m.fecha_fabricacion.isoformat() if m.fecha_fabricacion else None,
        "expiration_date": m.fecha_vencimiento.isoformat() if m.fecha_vencimiento else None,
        "stock": m.stock,
        "purchase_price": str(m.precio_compra),
        "sale_price": str(m.precio_venta),
        "supplier": {
            "id": m.proveedor.nit,
            "name": m.proveedor.nombre,
            "nit": m.proveedor.nit,
        } if m.proveedor else None,
        "requires_prescription": m.requiere_formula,
        "status": {
            "id": m.estado.id,
            "name": m.estado.nombre,
        } if m.estado else None,
        "can_be_sold": m.puede_venderse,
        "responsible": {
            "id": m.responsable.id,
            "name": m.responsable.nombre,
            "email": m.responsable.email,
        } if m.responsable else None,
        "created_by": {
            "id": m.creado_por.id,
            "name": m.creado_por.nombre,
            "email": m.creado_por.email,
        } if m.creado_por else None,
        "created_at": m.creado_en.isoformat() if m.creado_en else None,
        "updated_at": m.actualizado_en.isoformat() if m.actualizado_en else None,
    }


def _serialize_catalog_item(item):
    return {
        "id": getattr(item, "id", None),
        "name": getattr(item, "nombre", None),
    }


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def medications_resource(request):
    if not _is_admin(request.user):
        return Response(
            {"error": {"code": "FORBIDDEN", "message": "You do not have permission."}},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == "GET":
        queryset = Medicamento.objects.select_related(
            "forma",
            "presentacion",
            "via_administracion",
            "laboratorio",
            "proveedor",
            "estado",
            "responsable",
            "creado_por",
        ).order_by("nombre")

        search = (request.GET.get("search") or "").strip()
        administration_route = (request.GET.get("administration_route") or "").strip()
        laboratory = (request.GET.get("laboratory") or "").strip()
        medication_status = (request.GET.get("status") or "").strip()
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 10))

        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(concentracion__icontains=search) |
                Q(lote__icontains=search) |
                Q(proveedor__nombre__icontains=search)
            )

        if administration_route:
            queryset = queryset.filter(via_administracion_id=administration_route)

        if laboratory:
            queryset = queryset.filter(laboratorio_id=laboratory)

        if medication_status:
            queryset = queryset.filter(estado_id=medication_status)

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        return Response({
            "data": {
                "results": [_serialize_medication(item) for item in page_obj],
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
                    "administration_route": administration_route,
                    "laboratory": laboratory,
                    "status": medication_status,
                }
            },
            "message": "Medications retrieved successfully."
        })

    form = CrearMedicamentoForm(request.data)
    if form.is_valid():
        medication = form.save(commit=False)
        medication.creado_por = request.user
        medication.requiere_formula = False
        medication.laboratorio_texto = medication.laboratorio.nombre if medication.laboratorio else None
        medication.save()

        MedicamentoHistorial.objects.create(
            medicamento=medication,
            accion="CREADO",
            usuario=request.user,
            detalle="Medication created from SPA integration."
        )

        return Response(
            {
                "data": {
                    "medication": _serialize_medication(medication)
                },
                "message": "Medication created successfully."
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(
        {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Please correct the highlighted fields.",
                "fields": form.errors,
            }
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def medication_detail_resource(request, medication_id):
    if not _is_admin(request.user):
        return Response(
            {"error": {"code": "FORBIDDEN", "message": "You do not have permission."}},
            status=status.HTTP_403_FORBIDDEN,
        )

    medication = get_object_or_404(
        Medicamento.objects.select_related(
            "forma",
            "presentacion",
            "via_administracion",
            "laboratorio",
            "proveedor",
            "estado",
            "responsable",
            "creado_por",
        ),
        pk=medication_id
    )

    if request.method == "GET":
        return Response({
            "data": {
                "medication": _serialize_medication(medication)
            },
            "message": "Medication retrieved successfully."
        })

    form = ActualizarMedicamentoForm(request.data, instance=medication)
    if form.is_valid():
        updated = form.save(commit=False)
        updated.laboratorio_texto = updated.laboratorio.nombre if updated.laboratorio else None
        updated.save()

        MedicamentoHistorial.objects.create(
            medicamento=updated,
            accion="ACTUALIZADO",
            usuario=request.user,
            detalle="Medication updated from SPA integration."
        )

        return Response({
            "data": {
                "medication": _serialize_medication(updated)
            },
            "message": "Medication updated successfully."
        })

    return Response(
        {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Please correct the highlighted fields.",
                "fields": form.errors,
            }
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def medication_status_resource(request, medication_id):
    if not _is_admin(request.user):
        return Response(
            {"error": {"code": "FORBIDDEN", "message": "You do not have permission."}},
            status=status.HTTP_403_FORBIDDEN,
        )

    medication = get_object_or_404(Medicamento.objects.select_related("estado"), pk=medication_id)
    status_id = request.data.get("status_id")

    if not status_id:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Status is required.",
                    "fields": {"status_id": ["This field is required."]},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    new_status = EstadoMedicamento.objects.filter(pk=status_id, activo=True).first()
    if not new_status:
        return Response(
            {
                "error": {
                    "code": "INVALID_STATUS",
                    "message": "Invalid status.",
                    "fields": {"status_id": ["Invalid status."]},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    old_status = medication.estado.nombre if medication.estado else None
    medication.estado = new_status
    medication.save(update_fields=["estado", "actualizado_en"])

    MedicamentoHistorial.objects.create(
        medicamento=medication,
        accion="CAMBIO_ESTADO",
        usuario=request.user,
        detalle=f"Status changed: {old_status} -> {new_status.nombre}",
    )

    return Response({
        "data": {
            "medication": _serialize_medication(medication)
        },
        "message": "Medication status updated successfully."
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def pharmaceutical_forms_catalog(request):
    items = FormaFarmaceutica.objects.filter(activo=True).order_by("nombre")
    return Response({
        "data": {
            "results": [_serialize_catalog_item(item) for item in items]
        },
        "message": "Pharmaceutical forms retrieved successfully."
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def presentations_catalog(request):
    form_id = request.GET.get("pharmaceutical_form_id")
    queryset = Presentacion.objects.filter(activo=True)

    if form_id:
        queryset = queryset.filter(forma_id=form_id)

    queryset = queryset.order_by("nombre")

    results = [
        {
            "id": item.id,
            "name": item.nombre,
            "pharmaceutical_form_id": item.forma_id,
        }
        for item in queryset
    ]

    return Response({
        "data": {
            "results": results
        },
        "message": "Presentations retrieved successfully."
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def administration_routes_catalog(request):
    items = ViaAdministracion.objects.filter(activo=True).order_by("nombre")
    return Response({
        "data": {
            "results": [_serialize_catalog_item(item) for item in items]
        },
        "message": "Administration routes retrieved successfully."
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def laboratories_catalog(request):
    items = Laboratorio.objects.filter(activo=True).order_by("nombre")
    return Response({
        "data": {
            "results": [_serialize_catalog_item(item) for item in items]
        },
        "message": "Laboratories retrieved successfully."
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def medication_statuses_catalog(request):
    items = EstadoMedicamento.objects.filter(activo=True).order_by("nombre")
    return Response({
        "data": {
            "results": [_serialize_catalog_item(item) for item in items]
        },
        "message": "Medication statuses retrieved successfully."
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def suppliers_catalog(request):
    queryset = Proveedor.objects.all().order_by("nombre")
    supplier_status = (request.GET.get("status") or "").strip()

    if supplier_status:
        queryset = queryset.filter(estado=supplier_status)

    results = [
        {
            "id": item.nit,
            "name": item.nombre,
            "nit": item.nit,
            "status": item.estado,
        }
        for item in queryset
    ]

    return Response({
        "data": {
            "results": results
        },
        "message": "Suppliers retrieved successfully."
    })