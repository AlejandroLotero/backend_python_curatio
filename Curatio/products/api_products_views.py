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
    ProveedorHistorial,
)
from .forms import CrearMedicamentoForm, ActualizarMedicamentoForm, CrearProveedorForm


def _is_admin(user):
    return getattr(user, "rol", None) == "Administrador"


def _is_cliente(user):
    """RFCLI03 / RFCLI04: recursos de consulta de medicamentos para rol Cliente."""
    return getattr(user, "rol", None) == "Cliente"


def _normalize_medication_name(value):
    """Normaliza nombre para comparar (minúsculas, espacios colapsados)."""
    return " ".join((value or "").strip().lower().split())


def _edit_distance_at_most(s1, s2, max_dist=2):
    """
    Distancia de Levenshtein; devuelve el entero si es <= max_dist, si no None.
    Corta filas temprano si ya no puede mejorar (ahorro con muchos registros).
    """
    len1, len2 = len(s1), len(s2)
    if abs(len1 - len2) > max_dist:
        return None

    previous = list(range(len2 + 1))
    for i in range(1, len1 + 1):
        current = [i]
        row_min = i
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            v = min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost)
            current.append(v)
            row_min = min(row_min, v)
        if row_min > max_dist:
            return None
        previous = current

    d = previous[-1]
    return d if d <= max_dist else None


def _serialize_medication_cliente(m):
    """
    RFCLI03: vista solo lectura para cliente (sin datos internos de compra/proveedor).
    """
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
        "sale_price": str(m.precio_venta),
        "requires_prescription": m.requiere_formula,
        "status": {
            "id": m.estado.id,
            "name": m.estado.nombre,
        } if m.estado else None,
        "can_be_sold": m.puede_venderse,
    }


def _medication_queryset_cliente():
    return Medicamento.objects.select_related(
        "forma",
        "presentacion",
        "via_administracion",
        "laboratorio",
        "estado",
    )


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
def medication_client_view_resource(request):
    """
    RFCLI03 — Cliente: ver medicamento en solo lectura por ID exacto o por nombre.
    Si el nombre no coincide exactamente, se devuelven sugerencias (1–2 letras de diferencia).
    """
    if not _is_cliente(request.user):
        return Response(
            {
                "error": {
                    "code": "FORBIDDEN",
                    "message": "Solo el rol Cliente puede consultar medicamentos en este recurso.",
                    "fields": {},
                }
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    raw_id = (request.GET.get("medication_id") or request.GET.get("id") or "").strip()
    raw_name = (request.GET.get("name") or "").strip()

    # Sin parámetros útiles
    if not raw_id and not raw_name:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Indique medication_id (o id) o nombre en la consulta.",
                    "fields": {
                        "medication_id": ["Obligatorio si no envía name."],
                        "name": ["Obligatorio si no envía medication_id o id."],
                    },
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Prioridad: ID si viene informado (coincidencia exacta en PK)
    if raw_id:
        try:
            pk = int(raw_id)
        except (TypeError, ValueError):
            return Response(
                {
                    "error": {
                        "code": "INVALID_MEDICATION_ID",
                        "message": "El ID del medicamento no es válido.",
                        "fields": {"medication_id": ["Debe ser un número entero."]},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if pk <= 0:
            return Response(
                {
                    "error": {
                        "code": "INVALID_MEDICATION_ID",
                        "message": "El ID del medicamento no es válido.",
                        "fields": {"medication_id": ["El ID debe ser mayor que cero."]},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        med = _medication_queryset_cliente().filter(pk=pk).first()
        if not med:
            return Response(
                {
                    "error": {
                        "code": "MEDICATION_NOT_FOUND",
                        "message": "No se encontró un medicamento con el ID indicado.",
                        "fields": {},
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "data": {
                    "medication": _serialize_medication_cliente(med),
                    "suggestions": [],
                },
                "message": "Medicamento encontrado.",
            },
            status=status.HTTP_200_OK,
        )

    # Búsqueda por nombre exacto (insensible a mayúsculas en BD)
    normed_query = _normalize_medication_name(raw_name)
    if not normed_query:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "El nombre del medicamento no es válido.",
                    "fields": {"name": ["Indique un nombre no vacío."]},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    med = _medication_queryset_cliente().filter(nombre__iexact=raw_name.strip()).first()
    if med:
        return Response(
            {
                "data": {
                    "medication": _serialize_medication_cliente(med),
                    "suggestions": [],
                },
                "message": "Medicamento encontrado.",
            },
            status=status.HTTP_200_OK,
        )

    # Sin coincidencia exacta: sugerencias con distancia de edición 1 o 2
    scored = []
    for mid, nombre in Medicamento.objects.values_list("id", "nombre"):
        nn = _normalize_medication_name(nombre)
        if nn == normed_query:
            continue
        dist = _edit_distance_at_most(normed_query, nn, max_dist=2)
        if dist is not None and dist >= 1:
            scored.append((dist, mid, nombre))

    scored.sort(key=lambda t: (t[0], t[2].lower()))
    suggestions = [{"id": m_id, "name": nom} for _d, m_id, nom in scored[:15]]

    return Response(
        {
            "error": {
                "code": "MEDICATION_NOT_FOUND",
                "message": "No se encontró un medicamento con ese nombre exacto.",
                "suggestions": suggestions,
                "fields": {},
            }
        },
        status=status.HTTP_404_NOT_FOUND,
    )


def _parse_optional_positive_int(value, field_name):
    """Valida entero de filtro opcional; None si viene vacío."""
    raw = (value or "").strip()
    if raw == "":
        return None, None
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return None, {
            "code": "VALIDATION_ERROR",
            "message": f"El parámetro {field_name} debe ser un número entero válido.",
            "fields": {field_name: ["Valor no numérico."]},
        }
    if n <= 0:
        return None, {
            "code": "VALIDATION_ERROR",
            "message": f"El parámetro {field_name} debe ser mayor que cero.",
            "fields": {field_name: ["Valor inválido."]},
        }
    return n, None


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def medications_client_list_resource(request):
    """
    RFCLI04 — Cliente: listado de medicamentos (solo lectura).
    Filtros opcionales; orden por nombre. Sin paginación en servidor: el front pagina.
    """
    if not _is_cliente(request.user):
        return Response(
            {
                "error": {
                    "code": "FORBIDDEN",
                    "message": "Solo el rol Cliente puede listar medicamentos en este recurso.",
                    "fields": {},
                }
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    name = (request.GET.get("name") or request.GET.get("search") or "").strip()

    route_id, err = _parse_optional_positive_int(
        request.GET.get("administration_route"), "administration_route"
    )
    if err:
        return Response({"error": err}, status=status.HTTP_400_BAD_REQUEST)

    lab_id, err = _parse_optional_positive_int(request.GET.get("laboratory"), "laboratory")
    if err:
        return Response({"error": err}, status=status.HTTP_400_BAD_REQUEST)

    status_id, err = _parse_optional_positive_int(request.GET.get("status"), "status")
    if err:
        return Response({"error": err}, status=status.HTTP_400_BAD_REQUEST)

    queryset = _medication_queryset_cliente().order_by("nombre")

    if name:
        queryset = queryset.filter(nombre__icontains=name)

    if route_id is not None:
        queryset = queryset.filter(via_administracion_id=route_id)

    if lab_id is not None:
        queryset = queryset.filter(laboratorio_id=lab_id)

    if status_id is not None:
        queryset = queryset.filter(estado_id=status_id)

    results = [_serialize_medication_cliente(m) for m in queryset]

    return Response(
        {
            "data": {
                "results": results,
                "count": len(results),
                "filters": {
                    "name": name,
                    "administration_route": str(route_id) if route_id is not None else "",
                    "laboratory": str(lab_id) if lab_id is not None else "",
                    "status": str(status_id) if status_id is not None else "",
                },
            },
            "message": "Medicamentos obtenidos correctamente.",
        },
        status=status.HTTP_200_OK,
    )


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

#Funcion para serializar los datos del proveedor
def _serialize_supplier_row(item):
    """
    Serialización alineada al modelo Proveedor (products/models.py).
    Se mantienen id/name/nit/status para compatibilidad con selects de medicamentos
    y catálogos existentes; el resto alimenta el módulo SPA de proveedores.
    """
    return {
        "id": item.nit,
        "name": item.nombre,
        "nit": item.nit,
        "status": item.estado,
        "razon_social": item.razon_social or "",
        "nombre_contacto": item.nombre_contacto or "",
        "telefono_contacto": item.telefono_contacto or "",
        "correo_contacto": item.correo_contacto or "",
        "direccion": item.direccion or "",
        "ciudad": item.ciudad or "",
    }


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def suppliers_catalog(request):
    """
    GET: listado para la tabla SPA y para ?status=Activo (medicamentos).
    POST: alta de proveedor (solo Administrador), misma validación que CrearProveedorForm.
    """
    if request.method == "GET":
        queryset = Proveedor.objects.all().order_by("nombre")
        supplier_status = (request.GET.get("status") or "").strip()

        if supplier_status:
            queryset = queryset.filter(estado=supplier_status)

        results = [_serialize_supplier_row(item) for item in queryset]

        return Response({
            "data": {
                "results": results
            },
            "message": "Suppliers retrieved successfully."
        })

    if not _is_admin(request.user):
        return Response(
            {"error": {"code": "FORBIDDEN", "message": "You do not have permission."}},
            status=status.HTTP_403_FORBIDDEN,
        )

    form = CrearProveedorForm(request.data)
    if form.is_valid():
        proveedor = form.save(commit=False)
        proveedor.creado_por = request.user
        proveedor.full_clean()
        proveedor.save()

        ProveedorHistorial.objects.create(
            proveedor=proveedor,
            accion="CREADO",
            usuario=request.user,
            detalle="Proveedor creado desde API (SPA).",
        )

        return Response(
            {
                "data": {
                    "supplier": _serialize_supplier_row(proveedor),
                },
                "message": "Supplier created successfully.",
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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def supplier_detail_resource(request, supplier_nit):
    """Detalle por NIT (PK de Proveedor) para la vista SPA de proveedor."""
    proveedor = Proveedor.objects.filter(pk=supplier_nit).first()
    if not proveedor:
        return Response(
            {
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Supplier not found.",
                    "fields": {},
                }
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response({
        "data": {
            "supplier": _serialize_supplier_row(proveedor),
        },
        "message": "Supplier retrieved successfully.",
    })


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def supplier_status_resource(request, supplier_nit):
    """Cambio de estado Activo/Inactivo (paridad con cambiar_estado_proveedor en views.py)."""
    if not _is_admin(request.user):
        return Response(
            {"error": {"code": "FORBIDDEN", "message": "You do not have permission."}},
            status=status.HTTP_403_FORBIDDEN,
        )

    proveedor = Proveedor.objects.filter(pk=supplier_nit).first()
    if not proveedor:
        return Response(
            {
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Supplier not found.",
                    "fields": {},
                }
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    nuevo_estado = (request.data.get("estado") or "").strip()
    if nuevo_estado not in ["Activo", "Inactivo"]:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid status.",
                    "fields": {"estado": ['Debe ser "Activo" o "Inactivo".']},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    estado_anterior = proveedor.estado
    if estado_anterior == nuevo_estado:
        return Response({
            "data": {
                "supplier": _serialize_supplier_row(proveedor),
            },
            "message": "Supplier status unchanged.",
        })

    proveedor.estado = nuevo_estado
    proveedor.save(update_fields=["estado", "actualizado_en"])

    ProveedorHistorial.objects.create(
        proveedor=proveedor,
        accion="CAMBIO_ESTADO",
        usuario=request.user,
        detalle=f"Estado: {estado_anterior} → {nuevo_estado}",
    )

    return Response({
        "data": {
            "supplier": _serialize_supplier_row(proveedor),
        },
        "message": "Supplier status updated successfully.",
    })