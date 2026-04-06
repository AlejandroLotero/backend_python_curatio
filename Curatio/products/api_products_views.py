# # from django.core.paginator import Paginator
# # from django.db.models import Q
# # from django.shortcuts import get_object_or_404
# # from rest_framework.decorators import api_view, permission_classes
# # from rest_framework.permissions import IsAuthenticated
# # from rest_framework.response import Response
# # from rest_framework import status

# # from .models import (
# #     Medicamento,
# #     FormaFarmaceutica,
# #     Presentacion,
# #     ViaAdministracion,
# #     Laboratorio,
# #     EstadoMedicamento,
# #     Proveedor,
# #     MedicamentoHistorial,
# # )
# # from .forms import CrearMedicamentoForm, ActualizarMedicamentoForm


# # def _is_admin(user):
# #     return getattr(user, "rol", None) == "Administrador"


# # def _is_cliente(user):
# #     """RFCLI03 / RFCLI04: recursos de consulta de medicamentos para rol Cliente."""
# #     return getattr(user, "rol", None) == "Cliente"


# # def _normalize_medication_name(value):
# #     """Normaliza nombre para comparar (minúsculas, espacios colapsados)."""
# #     return " ".join((value or "").strip().lower().split())


# # def _edit_distance_at_most(s1, s2, max_dist=2):
# #     """
# #     Distancia de Levenshtein; devuelve el entero si es <= max_dist, si no None.
# #     Corta filas temprano si ya no puede mejorar (ahorro con muchos registros).
# #     """
# #     len1, len2 = len(s1), len(s2)
# #     if abs(len1 - len2) > max_dist:
# #         return None

# #     previous = list(range(len2 + 1))
# #     for i in range(1, len1 + 1):
# #         current = [i]
# #         row_min = i
# #         for j in range(1, len2 + 1):
# #             cost = 0 if s1[i - 1] == s2[j - 1] else 1
# #             v = min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost)
# #             current.append(v)
# #             row_min = min(row_min, v)
# #         if row_min > max_dist:
# #             return None
# #         previous = current

# #     d = previous[-1]
# #     return d if d <= max_dist else None


# # def _serialize_medication_cliente(m):
# #     """
# #     RFCLI03: vista solo lectura para cliente (sin datos internos de compra/proveedor).
# #     """
# #     return {
# #         "id": m.id,
# #         "name": m.nombre,
# #         "pharmaceutical_form": {
# #             "id": m.forma.id,
# #             "name": m.forma.nombre,
# #         } if m.forma else None,
# #         "presentation": {
# #             "id": m.presentacion.id,
# #             "name": m.presentacion.nombre,
# #         } if m.presentacion else None,
# #         "concentration": m.concentracion,
# #         "description": m.descripcion,
# #         "administration_route": {
# #             "id": m.via_administracion.id,
# #             "name": m.via_administracion.nombre,
# #         } if m.via_administracion else None,
# #         "laboratory": {
# #             "id": m.laboratorio.id,
# #             "name": m.laboratorio.nombre,
# #         } if m.laboratorio else None,
# #         "batch": m.lote,
# #         "manufacturing_date": m.fecha_fabricacion.isoformat() if m.fecha_fabricacion else None,
# #         "expiration_date": m.fecha_vencimiento.isoformat() if m.fecha_vencimiento else None,
# #         "stock": m.stock,
# #         "sale_price": str(m.precio_venta),
# #         "requires_prescription": m.requiere_formula,
# #         "status": {
# #             "id": m.estado.id,
# #             "name": m.estado.nombre,
# #         } if m.estado else None,
# #         "can_be_sold": m.puede_venderse,
# #     }


# # def _medication_queryset_cliente():
# #     return Medicamento.objects.select_related(
# #         "forma",
# #         "presentacion",
# #         "via_administracion",
# #         "laboratorio",
# #         "estado",
# #     )


# # def _serialize_medication(m):
# #     return {
# #         "id": m.id,
# #         "name": m.nombre,
# #         "pharmaceutical_form": {
# #             "id": m.forma.id,
# #             "name": m.forma.nombre,
# #         } if m.forma else None,
# #         "presentation": {
# #             "id": m.presentacion.id,
# #             "name": m.presentacion.nombre,
# #         } if m.presentacion else None,
# #         "concentration": m.concentracion,
# #         "description": m.descripcion,
# #         "administration_route": {
# #             "id": m.via_administracion.id,
# #             "name": m.via_administracion.nombre,
# #         } if m.via_administracion else None,
# #         "laboratory": {
# #             "id": m.laboratorio.id,
# #             "name": m.laboratorio.nombre,
# #         } if m.laboratorio else None,
# #         "batch": m.lote,
# #         "manufacturing_date": m.fecha_fabricacion.isoformat() if m.fecha_fabricacion else None,
# #         "expiration_date": m.fecha_vencimiento.isoformat() if m.fecha_vencimiento else None,
# #         "stock": m.stock,
# #         "purchase_price": str(m.precio_compra),
# #         "sale_price": str(m.precio_venta),
# #         "supplier": {
# #             "id": m.proveedor.nit,
# #             "name": m.proveedor.nombre,
# #             "nit": m.proveedor.nit,
# #         } if m.proveedor else None,
# #         "requires_prescription": m.requiere_formula,
# #         "status": {
# #             "id": m.estado.id,
# #             "name": m.estado.nombre,
# #         } if m.estado else None,
# #         "can_be_sold": m.puede_venderse,
# #         "responsible": {
# #             "id": m.responsable.id,
# #             "name": m.responsable.nombre,
# #             "email": m.responsable.email,
# #         } if m.responsable else None,
# #         "created_by": {
# #             "id": m.creado_por.id,
# #             "name": m.creado_por.nombre,
# #             "email": m.creado_por.email,
# #         } if m.creado_por else None,
# #         "created_at": m.creado_en.isoformat() if m.creado_en else None,
# #         "updated_at": m.actualizado_en.isoformat() if m.actualizado_en else None,
# #     }


# # def _serialize_catalog_item(item):
# #     return {
# #         "id": getattr(item, "id", None),
# #         "name": getattr(item, "nombre", None),
# #     }


# # @api_view(["GET", "POST"])
# # @permission_classes([IsAuthenticated])
# # def medications_resource(request):
# #     if not _is_admin(request.user):
# #         return Response(
# #             {"error": {"code": "FORBIDDEN", "message": "You do not have permission."}},
# #             status=status.HTTP_403_FORBIDDEN,
# #         )

# #     if request.method == "GET":
# #         queryset = Medicamento.objects.select_related(
# #             "forma",
# #             "presentacion",
# #             "via_administracion",
# #             "laboratorio",
# #             "proveedor",
# #             "estado",
# #             "responsable",
# #             "creado_por",
# #         ).order_by("nombre")

# #         search = (request.GET.get("search") or "").strip()
# #         administration_route = (request.GET.get("administration_route") or "").strip()
# #         laboratory = (request.GET.get("laboratory") or "").strip()
# #         medication_status = (request.GET.get("status") or "").strip()
# #         page = int(request.GET.get("page", 1))
# #         page_size = int(request.GET.get("page_size", 10))

# #         if search:
# #             queryset = queryset.filter(
# #                 Q(nombre__icontains=search) |
# #                 Q(concentracion__icontains=search) |
# #                 Q(lote__icontains=search) |
# #                 Q(proveedor__nombre__icontains=search)
# #             )

# #         if administration_route:
# #             queryset = queryset.filter(via_administracion_id=administration_route)

# #         if laboratory:
# #             queryset = queryset.filter(laboratorio_id=laboratory)

# #         if medication_status:
# #             queryset = queryset.filter(estado_id=medication_status)

# #         paginator = Paginator(queryset, page_size)
# #         page_obj = paginator.get_page(page)

# #         return Response({
# #             "data": {
# #                 "results": [_serialize_medication(item) for item in page_obj],
# #                 "pagination": {
# #                     "count": paginator.count,
# #                     "num_pages": paginator.num_pages,
# #                     "page": page_obj.number,
# #                     "page_size": page_size,
# #                     "has_next": page_obj.has_next(),
# #                     "has_previous": page_obj.has_previous(),
# #                 },
# #                 "filters": {
# #                     "search": search,
# #                     "administration_route": administration_route,
# #                     "laboratory": laboratory,
# #                     "status": medication_status,
# #                 }
# #             },
# #             "message": "Medications retrieved successfully."
# #         })

# #     form = CrearMedicamentoForm(request.data)
# #     if form.is_valid():
# #         medication = form.save(commit=False)
# #         medication.creado_por = request.user
# #         medication.requiere_formula = False
# #         medication.laboratorio_texto = medication.laboratorio.nombre if medication.laboratorio else None
# #         medication.save()

# #         MedicamentoHistorial.objects.create(
# #             medicamento=medication,
# #             accion="CREADO",
# #             usuario=request.user,
# #             detalle="Medication created from SPA integration."
# #         )

# #         return Response(
# #             {
# #                 "data": {
# #                     "medication": _serialize_medication(medication)
# #                 },
# #                 "message": "Medication created successfully."
# #             },
# #             status=status.HTTP_201_CREATED,
# #         )

# #     return Response(
# #         {
# #             "error": {
# #                 "code": "VALIDATION_ERROR",
# #                 "message": "Please correct the highlighted fields.",
# #                 "fields": form.errors,
# #             }
# #         },
# #         status=status.HTTP_400_BAD_REQUEST,
# #     )


# # @api_view(["GET", "PUT"])
# # @permission_classes([IsAuthenticated])
# # def medication_detail_resource(request, medication_id):
# #     if not _is_admin(request.user):
# #         return Response(
# #             {"error": {"code": "FORBIDDEN", "message": "You do not have permission."}},
# #             status=status.HTTP_403_FORBIDDEN,
# #         )

# #     medication = get_object_or_404(
# #         Medicamento.objects.select_related(
# #             "forma",
# #             "presentacion",
# #             "via_administracion",
# #             "laboratorio",
# #             "proveedor",
# #             "estado",
# #             "responsable",
# #             "creado_por",
# #         ),
# #         pk=medication_id
# #     )

# #     if request.method == "GET":
# #         return Response({
# #             "data": {
# #                 "medication": _serialize_medication(medication)
# #             },
# #             "message": "Medication retrieved successfully."
# #         })

# #     form = ActualizarMedicamentoForm(request.data, instance=medication)
# #     if form.is_valid():
# #         updated = form.save(commit=False)
# #         updated.laboratorio_texto = updated.laboratorio.nombre if updated.laboratorio else None
# #         updated.save()

# #         MedicamentoHistorial.objects.create(
# #             medicamento=updated,
# #             accion="ACTUALIZADO",
# #             usuario=request.user,
# #             detalle="Medication updated from SPA integration."
# #         )

# #         return Response({
# #             "data": {
# #                 "medication": _serialize_medication(updated)
# #             },
# #             "message": "Medication updated successfully."
# #         })

# #     return Response(
# #         {
# #             "error": {
# #                 "code": "VALIDATION_ERROR",
# #                 "message": "Please correct the highlighted fields.",
# #                 "fields": form.errors,
# #             }
# #         },
# #         status=status.HTTP_400_BAD_REQUEST,
# #     )


# # @api_view(["PATCH"])
# # @permission_classes([IsAuthenticated])
# # def medication_status_resource(request, medication_id):
# #     if not _is_admin(request.user):
# #         return Response(
# #             {"error": {"code": "FORBIDDEN", "message": "You do not have permission."}},
# #             status=status.HTTP_403_FORBIDDEN,
# #         )

# #     medication = get_object_or_404(Medicamento.objects.select_related("estado"), pk=medication_id)
# #     status_id = request.data.get("status_id")

# #     if not status_id:
# #         return Response(
# #             {
# #                 "error": {
# #                     "code": "VALIDATION_ERROR",
# #                     "message": "Status is required.",
# #                     "fields": {"status_id": ["This field is required."]},
# #                 }
# #             },
# #             status=status.HTTP_400_BAD_REQUEST,
# #         )

# #     new_status = EstadoMedicamento.objects.filter(pk=status_id, activo=True).first()
# #     if not new_status:
# #         return Response(
# #             {
# #                 "error": {
# #                     "code": "INVALID_STATUS",
# #                     "message": "Invalid status.",
# #                     "fields": {"status_id": ["Invalid status."]},
# #                 }
# #             },
# #             status=status.HTTP_400_BAD_REQUEST,
# #         )

# #     old_status = medication.estado.nombre if medication.estado else None
# #     medication.estado = new_status
# #     medication.save(update_fields=["estado", "actualizado_en"])

# #     MedicamentoHistorial.objects.create(
# #         medicamento=medication,
# #         accion="CAMBIO_ESTADO",
# #         usuario=request.user,
# #         detalle=f"Status changed: {old_status} -> {new_status.nombre}",
# #     )

# #     return Response({
# #         "data": {
# #             "medication": _serialize_medication(medication)
# #         },
# #         "message": "Medication status updated successfully."
# #     })


# # @api_view(["GET"])
# # @permission_classes([IsAuthenticated])
# # def medication_client_view_resource(request):
# #     """
# #     RFCLI03 — Cliente: ver medicamento en solo lectura por ID exacto o por nombre.
# #     Si el nombre no coincide exactamente, se devuelven sugerencias (1–2 letras de diferencia).
# #     """
# #     if not _is_cliente(request.user):
# #         return Response(
# #             {
# #                 "error": {
# #                     "code": "FORBIDDEN",
# #                     "message": "Solo el rol Cliente puede consultar medicamentos en este recurso.",
# #                     "fields": {},
# #                 }
# #             },
# #             status=status.HTTP_403_FORBIDDEN,
# #         )

# #     raw_id = (request.GET.get("medication_id") or request.GET.get("id") or "").strip()
# #     raw_name = (request.GET.get("name") or "").strip()

# #     # Sin parámetros útiles
# #     if not raw_id and not raw_name:
# #         return Response(
# #             {
# #                 "error": {
# #                     "code": "VALIDATION_ERROR",
# #                     "message": "Indique medication_id (o id) o nombre en la consulta.",
# #                     "fields": {
# #                         "medication_id": ["Obligatorio si no envía name."],
# #                         "name": ["Obligatorio si no envía medication_id o id."],
# #                     },
# #                 }
# #             },
# #             status=status.HTTP_400_BAD_REQUEST,
# #         )

# #     # Prioridad: ID si viene informado (coincidencia exacta en PK)
# #     if raw_id:
# #         try:
# #             pk = int(raw_id)
# #         except (TypeError, ValueError):
# #             return Response(
# #                 {
# #                     "error": {
# #                         "code": "INVALID_MEDICATION_ID",
# #                         "message": "El ID del medicamento no es válido.",
# #                         "fields": {"medication_id": ["Debe ser un número entero."]},
# #                     }
# #                 },
# #                 status=status.HTTP_400_BAD_REQUEST,
# #             )

# #         if pk <= 0:
# #             return Response(
# #                 {
# #                     "error": {
# #                         "code": "INVALID_MEDICATION_ID",
# #                         "message": "El ID del medicamento no es válido.",
# #                         "fields": {"medication_id": ["El ID debe ser mayor que cero."]},
# #                     }
# #                 },
# #                 status=status.HTTP_400_BAD_REQUEST,
# #             )

# #         med = _medication_queryset_cliente().filter(pk=pk).first()
# #         if not med:
# #             return Response(
# #                 {
# #                     "error": {
# #                         "code": "MEDICATION_NOT_FOUND",
# #                         "message": "No se encontró un medicamento con el ID indicado.",
# #                         "fields": {},
# #                     }
# #                 },
# #                 status=status.HTTP_404_NOT_FOUND,
# #             )

# #         return Response(
# #             {
# #                 "data": {
# #                     "medication": _serialize_medication_cliente(med),
# #                     "suggestions": [],
# #                 },
# #                 "message": "Medicamento encontrado.",
# #             },
# #             status=status.HTTP_200_OK,
# #         )

# #     # Búsqueda por nombre exacto (insensible a mayúsculas en BD)
# #     normed_query = _normalize_medication_name(raw_name)
# #     if not normed_query:
# #         return Response(
# #             {
# #                 "error": {
# #                     "code": "VALIDATION_ERROR",
# #                     "message": "El nombre del medicamento no es válido.",
# #                     "fields": {"name": ["Indique un nombre no vacío."]},
# #                 }
# #             },
# #             status=status.HTTP_400_BAD_REQUEST,
# #         )

# #     med = _medication_queryset_cliente().filter(nombre__iexact=raw_name.strip()).first()
# #     if med:
# #         return Response(
# #             {
# #                 "data": {
# #                     "medication": _serialize_medication_cliente(med),
# #                     "suggestions": [],
# #                 },
# #                 "message": "Medicamento encontrado.",
# #             },
# #             status=status.HTTP_200_OK,
# #         )

# #     # Sin coincidencia exacta: sugerencias con distancia de edición 1 o 2
# #     scored = []
# #     for mid, nombre in Medicamento.objects.values_list("id", "nombre"):
# #         nn = _normalize_medication_name(nombre)
# #         if nn == normed_query:
# #             continue
# #         dist = _edit_distance_at_most(normed_query, nn, max_dist=2)
# #         if dist is not None and dist >= 1:
# #             scored.append((dist, mid, nombre))

# #     scored.sort(key=lambda t: (t[0], t[2].lower()))
# #     suggestions = [{"id": m_id, "name": nom} for _d, m_id, nom in scored[:15]]

# #     return Response(
# #         {
# #             "error": {
# #                 "code": "MEDICATION_NOT_FOUND",
# #                 "message": "No se encontró un medicamento con ese nombre exacto.",
# #                 "suggestions": suggestions,
# #                 "fields": {},
# #             }
# #         },
# #         status=status.HTTP_404_NOT_FOUND,
# #     )


# # def _parse_optional_positive_int(value, field_name):
# #     """Valida entero de filtro opcional; None si viene vacío."""
# #     raw = (value or "").strip()
# #     if raw == "":
# #         return None, None
# #     try:
# #         n = int(raw)
# #     except (TypeError, ValueError):
# #         return None, {
# #             "code": "VALIDATION_ERROR",
# #             "message": f"El parámetro {field_name} debe ser un número entero válido.",
# #             "fields": {field_name: ["Valor no numérico."]},
# #         }
# #     if n <= 0:
# #         return None, {
# #             "code": "VALIDATION_ERROR",
# #             "message": f"El parámetro {field_name} debe ser mayor que cero.",
# #             "fields": {field_name: ["Valor inválido."]},
# #         }
# #     return n, None


# # @api_view(["GET"])
# # @permission_classes([IsAuthenticated])
# # def medications_client_list_resource(request):
# #     """
# #     RFCLI04 — Cliente: listado de medicamentos (solo lectura).
# #     Filtros opcionales; orden por nombre. Sin paginación en servidor: el front pagina.
# #     """
# #     if not _is_cliente(request.user):
# #         return Response(
# #             {
# #                 "error": {
# #                     "code": "FORBIDDEN",
# #                     "message": "Solo el rol Cliente puede listar medicamentos en este recurso.",
# #                     "fields": {},
# #                 }
# #             },
# #             status=status.HTTP_403_FORBIDDEN,
# #         )

# #     name = (request.GET.get("name") or request.GET.get("search") or "").strip()

# #     route_id, err = _parse_optional_positive_int(
# #         request.GET.get("administration_route"), "administration_route"
# #     )
# #     if err:
# #         return Response({"error": err}, status=status.HTTP_400_BAD_REQUEST)

# #     lab_id, err = _parse_optional_positive_int(request.GET.get("laboratory"), "laboratory")
# #     if err:
# #         return Response({"error": err}, status=status.HTTP_400_BAD_REQUEST)

# #     status_id, err = _parse_optional_positive_int(request.GET.get("status"), "status")
# #     if err:
# #         return Response({"error": err}, status=status.HTTP_400_BAD_REQUEST)

# #     queryset = _medication_queryset_cliente().order_by("nombre")

# #     if name:
# #         queryset = queryset.filter(nombre__icontains=name)

# #     if route_id is not None:
# #         queryset = queryset.filter(via_administracion_id=route_id)

# #     if lab_id is not None:
# #         queryset = queryset.filter(laboratorio_id=lab_id)

# #     if status_id is not None:
# #         queryset = queryset.filter(estado_id=status_id)

# #     results = [_serialize_medication_cliente(m) for m in queryset]

# #     return Response(
# #         {
# #             "data": {
# #                 "results": results,
# #                 "count": len(results),
# #                 "filters": {
# #                     "name": name,
# #                     "administration_route": str(route_id) if route_id is not None else "",
# #                     "laboratory": str(lab_id) if lab_id is not None else "",
# #                     "status": str(status_id) if status_id is not None else "",
# #                 },
# #             },
# #             "message": "Medicamentos obtenidos correctamente.",
# #         },
# #         status=status.HTTP_200_OK,
# #     )


# # @api_view(["GET"])
# # @permission_classes([IsAuthenticated])
# # def pharmaceutical_forms_catalog(request):
# #     items = FormaFarmaceutica.objects.filter(activo=True).order_by("nombre")
# #     return Response({
# #         "data": {
# #             "results": [_serialize_catalog_item(item) for item in items]
# #         },
# #         "message": "Pharmaceutical forms retrieved successfully."
# #     })


# # @api_view(["GET"])
# # @permission_classes([IsAuthenticated])
# # def presentations_catalog(request):
# #     form_id = request.GET.get("pharmaceutical_form_id")
# #     queryset = Presentacion.objects.filter(activo=True)

# #     if form_id:
# #         queryset = queryset.filter(forma_id=form_id)

# #     queryset = queryset.order_by("nombre")

# #     results = [
# #         {
# #             "id": item.id,
# #             "name": item.nombre,
# #             "pharmaceutical_form_id": item.forma_id,
# #         }
# #         for item in queryset
# #     ]

# #     return Response({
# #         "data": {
# #             "results": results
# #         },
# #         "message": "Presentations retrieved successfully."
# #     })


# # @api_view(["GET"])
# # @permission_classes([IsAuthenticated])
# # def administration_routes_catalog(request):
# #     items = ViaAdministracion.objects.filter(activo=True).order_by("nombre")
# #     return Response({
# #         "data": {
# #             "results": [_serialize_catalog_item(item) for item in items]
# #         },
# #         "message": "Administration routes retrieved successfully."
# #     })


# # @api_view(["GET"])
# # @permission_classes([IsAuthenticated])
# # def laboratories_catalog(request):
# #     items = Laboratorio.objects.filter(activo=True).order_by("nombre")
# #     return Response({
# #         "data": {
# #             "results": [_serialize_catalog_item(item) for item in items]
# #         },
# #         "message": "Laboratories retrieved successfully."
# #     })


# # @api_view(["GET"])
# # @permission_classes([IsAuthenticated])
# # def medication_statuses_catalog(request):
# #     items = EstadoMedicamento.objects.filter(activo=True).order_by("nombre")
# #     return Response({
# #         "data": {
# #             "results": [_serialize_catalog_item(item) for item in items]
# #         },
# #         "message": "Medication statuses retrieved successfully."
# #     })


# # @api_view(["GET"])
# # @permission_classes([IsAuthenticated])
# # def suppliers_catalog(request):
# #     queryset = Proveedor.objects.all().order_by("nombre")
# #     supplier_status = (request.GET.get("status") or "").strip()

# #     if supplier_status:
# #         queryset = queryset.filter(estado=supplier_status)

# #     results = [
# #         {
# #             "id": item.nit,
# #             "name": item.nombre,
# #             "nit": item.nit,
# #             "status": item.estado,
# #         }
# #         for item in queryset
# #     ]

# #     return Response({
# #         "data": {
# #             "results": results
# #         },
# #         "message": "Suppliers retrieved successfully."
# #     })

# # from django.core.paginator import Paginator
# # from django.db.models import Q
# # from django.shortcuts import get_object_or_404
# # from rest_framework.decorators import api_view, permission_classes
# # from rest_framework.permissions import IsAuthenticated
# # from rest_framework.response import Response
# # from rest_framework import status
# # from difflib import SequenceMatcher
# # from rest_framework.permissions import AllowAny

# # from .models import (
# #     Medicamento,
# #     FormaFarmaceutica,
# #     Presentacion,
# #     ViaAdministracion,
# #     Laboratorio,
# #     EstadoMedicamento,
# #     Proveedor,
# #     MedicamentoHistorial,
# # )
# # from .forms import CrearMedicamentoForm, ActualizarMedicamentoForm


# # def _is_admin(user):
# #     return getattr(user, "rol", None) == "Administrador"


# # def _serialize_medication(m):
# #     return {
# #         "id": m.id,
# #         "name": m.nombre,
# #         "pharmaceutical_form": {
# #             "id": m.forma.id,
# #             "name": m.forma.nombre,
# #         } if m.forma else None,
# #         "presentation": {
# #             "id": m.presentacion.id,
# #             "name": m.presentacion.nombre,
# #         } if m.presentacion else None,
# #         "concentration": m.concentracion,
# #         "description": m.descripcion,
# #         "administration_route": {
# #             "id": m.via_administracion.id,
# #             "name": m.via_administracion.nombre,
# #         } if m.via_administracion else None,
# #         "laboratory": {
# #             "id": m.laboratorio.id,
# #             "name": m.laboratorio.nombre,
# #         } if m.laboratorio else None,
# #         "batch": m.lote,
# #         "manufacturing_date": m.fecha_fabricacion.isoformat() if m.fecha_fabricacion else None,
# #         "expiration_date": m.fecha_vencimiento.isoformat() if m.fecha_vencimiento else None,
# #         "stock": m.stock,
# #         "purchase_price": str(m.precio_compra),
# #         "sale_price": str(m.precio_venta),
# #         "supplier": {
# #             "id": m.proveedor.nit,
# #             "name": m.proveedor.nombre,
# #             "nit": m.proveedor.nit,
# #         } if m.proveedor else None,
# #         "requires_prescription": m.requiere_formula,
# #         "status": {
# #             "id": m.estado.id,
# #             "name": m.estado.nombre,
# #         } if m.estado else None,
# #         "can_be_sold": m.puede_venderse,
# #         "responsible": {
# #             "id": m.responsable.id,
# #             "name": m.responsable.nombre,
# #             "email": m.responsable.email,
# #         } if m.responsable else None,
# #         "created_by": {
# #             "id": m.creado_por.id,
# #             "name": m.creado_por.nombre,
# #             "email": m.creado_por.email,
# #         } if m.creado_por else None,
# #         "created_at": m.creado_en.isoformat() if m.creado_en else None,
# #         "updated_at": m.actualizado_en.isoformat() if m.actualizado_en else None,
# #     }

# # def _serialize_catalog_medication(m):
# #     """
# #     Serialización read-only para consulta comercial/pública.
# #     Esta respuesta la consumen:
# #     - buscador del cliente
# #     - buscador de admin/farmaceuta
# #     - ProductShowPage
# #     """
# #     return {
# #         "id": m.id,
# #         "name": m.nombre,
# #         "pharmaceutical_form": {
# #             "id": m.forma.id,
# #             "name": m.forma.nombre,
# #         } if m.forma else None,
# #         "presentation": {
# #             "id": m.presentacion.id,
# #             "name": m.presentacion.nombre,
# #         } if m.presentacion else None,
# #         "concentration": m.concentracion,
# #         "description": m.descripcion,
# #         "administration_route": {
# #             "id": m.via_administracion.id,
# #             "name": m.via_administracion.nombre,
# #         } if m.via_administracion else None,
# #         "laboratory": {
# #             "id": m.laboratorio.id,
# #             "name": m.laboratorio.nombre,
# #         } if m.laboratorio else None,
# #         "batch": m.lote,
# #         "manufacturing_date": m.fecha_fabricacion.isoformat() if m.fecha_fabricacion else None,
# #         "expiration_date": m.fecha_vencimiento.isoformat() if m.fecha_vencimiento else None,
# #         "stock": m.stock,
# #         "purchase_price": str(m.precio_compra),
# #         "sale_price": str(m.precio_venta),
# #         "supplier": {
# #             "id": m.proveedor.nit,
# #             "name": m.proveedor.nombre,
# #             "nit": m.proveedor.nit,
# #         } if m.proveedor else None,
# #         "requires_prescription": m.requiere_formula,
# #         "status": {
# #             "id": m.estado.id,
# #             "name": m.estado.nombre,
# #         } if m.estado else None,
# #         "can_be_sold": m.puede_venderse,
# #         "created_at": m.creado_en.isoformat() if m.creado_en else None,
# #         "updated_at": m.actualizado_en.isoformat() if m.actualizado_en else None,
# #     }


# # def _build_name_suggestions(queryset, raw_query, limit=5):
# #     """
# #     Construye sugerencias cuando no existe coincidencia exacta.
# #     Regla del RQ:
# #     - si el nombre difiere en 1 o 2 letras
# #     - mostrar sugerencias
# #     """
# #     normalized_query = (raw_query or "").strip().lower()

# #     if not normalized_query:
# #         return []

# #     suggestions = []

# #     for item in queryset:
# #         candidate_name = (item.nombre or "").strip().lower()

# #         # Diferencia aproximada por longitud
# #         length_diff = abs(len(candidate_name) - len(normalized_query))

# #         # Ratio de similitud
# #         similarity = SequenceMatcher(None, normalized_query, candidate_name).ratio()

# #         # Regla flexible:
# #         # - diferencia corta o
# #         # - alta similitud textual
# #         if length_diff <= 2 or similarity >= 0.75:
# #             suggestions.append((similarity, item))

# #     # Ordenamos por mayor similitud
# #     suggestions.sort(key=lambda pair: pair[0], reverse=True)

# #     # Retornamos solo los medicamentos serializados
# #     return [_serialize_catalog_medication(item) for _, item in suggestions[:limit]]

# # def _serialize_catalog_item(item):
# #     return {
# #         "id": getattr(item, "id", None),
# #         "name": getattr(item, "nombre", None),
# #     }

# # def _serialize_public_medication_search_item(medication):
# #     """
# #     Serializa un medicamento para resultados de búsqueda pública/comercial.
# #     Este formato es más liviano que el administrativo y sirve para:
# #     - autocompletado del navbar
# #     - resultados públicos
# #     - detalle comercial
# #     """
# #     return {
# #         "id": medication.id,
# #         "name": medication.nombre,
# #         "presentation": medication.presentacion.nombre if medication.presentacion else "",
# #         "concentration": medication.concentracion or "",
# #         "laboratory": medication.laboratorio.nombre if medication.laboratorio else "",
# #         "description": medication.descripcion or "",
# #         "sale_price": str(medication.precio_venta or 0),
# #         "stock": medication.stock or 0,
# #         "status": medication.estado.nombre if medication.estado else "",
# #         "can_be_sold": medication.puede_venderse,
# #     }


# # def _build_medication_suggestions(query, queryset, limit=5):
# #     """
# #     Construye sugerencias por similitud de nombre.
# #     Regla funcional:
# #     - si el nombre difiere por 1 o 2 letras aproximadamente,
# #       se devuelve como sugerencia
# #     """
# #     query_normalized = (query or "").strip().lower()
# #     suggestions = []

# #     if not query_normalized:
# #         return suggestions

# #     for medication in queryset:
# #         medication_name = (medication.nombre or "").strip().lower()

# #         # Similitud textual simple
# #         similarity_ratio = SequenceMatcher(
# #             None,
# #             query_normalized,
# #             medication_name
# #         ).ratio()

# #         # Heurística práctica:
# #         # - ratio alto
# #         # - y diferencia de longitud razonable
# #         if similarity_ratio >= 0.75:
# #             suggestions.append({
# #                 "id": medication.id,
# #                 "name": medication.nombre,
# #             })

# #         if len(suggestions) >= limit:
# #             break

# #     return suggestions


# # @api_view(["GET", "POST"])
# # @permission_classes([IsAuthenticated])
# # def medications_resource(request):
# #     if not _is_admin(request.user):
# #         return Response(
# #             {"error": {"code": "FORBIDDEN", "message": "You do not have permission."}},
# #             status=status.HTTP_403_FORBIDDEN,
# #         )

# #     if request.method == "GET":
# #         queryset = Medicamento.objects.select_related(
# #             "forma",
# #             "presentacion",
# #             "via_administracion",
# #             "laboratorio",
# #             "proveedor",
# #             "estado",
# #             "responsable",
# #             "creado_por",
# #         ).order_by("nombre")

# #         search = (request.GET.get("search") or "").strip()
# #         administration_route = (request.GET.get("administration_route") or "").strip()
# #         laboratory = (request.GET.get("laboratory") or "").strip()
# #         medication_status = (request.GET.get("status") or "").strip()
# #         page = int(request.GET.get("page", 1))
# #         page_size = int(request.GET.get("page_size", 10))

# #         if search:
# #             queryset = queryset.filter(
# #                 Q(nombre__icontains=search) |
# #                 Q(concentracion__icontains=search) |
# #                 Q(lote__icontains=search) |
# #                 Q(proveedor__nombre__icontains=search)
# #             )

# #         if administration_route:
# #             queryset = queryset.filter(via_administracion_id=administration_route)

# #         if laboratory:
# #             queryset = queryset.filter(laboratorio_id=laboratory)

# #         if medication_status:
# #             queryset = queryset.filter(estado_id=medication_status)

# #         paginator = Paginator(queryset, page_size)
# #         page_obj = paginator.get_page(page)

# #         return Response({
# #             "data": {
# #                 "results": [_serialize_medication(item) for item in page_obj],
# #                 "pagination": {
# #                     "count": paginator.count,
# #                     "num_pages": paginator.num_pages,
# #                     "page": page_obj.number,
# #                     "page_size": page_size,
# #                     "has_next": page_obj.has_next(),
# #                     "has_previous": page_obj.has_previous(),
# #                 },
# #                 "filters": {
# #                     "search": search,
# #                     "administration_route": administration_route,
# #                     "laboratory": laboratory,
# #                     "status": medication_status,
# #                 }
# #             },
# #             "message": "Medications retrieved successfully."
# #         })

# #     form = CrearMedicamentoForm(request.data)
# #     if form.is_valid():
# #         medication = form.save(commit=False)
# #         medication.creado_por = request.user
# #         medication.requiere_formula = False
# #         medication.laboratorio_texto = medication.laboratorio.nombre if medication.laboratorio else None
# #         medication.save()

# #         MedicamentoHistorial.objects.create(
# #             medicamento=medication,
# #             accion="CREADO",
# #             usuario=request.user,
# #             detalle="Medication created from SPA integration."
# #         )

# #         return Response(
# #             {
# #                 "data": {
# #                     "medication": _serialize_medication(medication)
# #                 },
# #                 "message": "Medication created successfully."
# #             },
# #             status=status.HTTP_201_CREATED,
# #         )

# #     return Response(
# #         {
# #             "error": {
# #                 "code": "VALIDATION_ERROR",
# #                 "message": "Please correct the highlighted fields.",
# #                 "fields": form.errors,
# #             }
# #         },
# #         status=status.HTTP_400_BAD_REQUEST,
# #     )


# # @api_view(["GET", "PUT"])
# # @permission_classes([IsAuthenticated])
# # def medication_detail_resource(request, medication_id):
# #     if not _is_admin(request.user):
# #         return Response(
# #             {"error": {"code": "FORBIDDEN", "message": "You do not have permission."}},
# #             status=status.HTTP_403_FORBIDDEN,
# #         )

# #     medication = get_object_or_404(
# #         Medicamento.objects.select_related(
# #             "forma",
# #             "presentacion",
# #             "via_administracion",
# #             "laboratorio",
# #             "proveedor",
# #             "estado",
# #             "responsable",
# #             "creado_por",
# #         ),
# #         pk=medication_id
# #     )

# #     if request.method == "GET":
# #         return Response({
# #             "data": {
# #                 "medication": _serialize_medication(medication)
# #             },
# #             "message": "Medication retrieved successfully."
# #         })

# #     form = ActualizarMedicamentoForm(request.data, instance=medication)
# #     if form.is_valid():
# #         updated = form.save(commit=False)
# #         updated.laboratorio_texto = updated.laboratorio.nombre if updated.laboratorio else None
# #         updated.save()

# #         MedicamentoHistorial.objects.create(
# #             medicamento=updated,
# #             accion="ACTUALIZADO",
# #             usuario=request.user,
# #             detalle="Medication updated from SPA integration."
# #         )

# #         return Response({
# #             "data": {
# #                 "medication": _serialize_medication(updated)
# #             },
# #             "message": "Medication updated successfully."
# #         })

# #     return Response(
# #         {
# #             "error": {
# #                 "code": "VALIDATION_ERROR",
# #                 "message": "Please correct the highlighted fields.",
# #                 "fields": form.errors,
# #             }
# #         },
# #         status=status.HTTP_400_BAD_REQUEST,
# #     )


# # @api_view(["PATCH"])
# # @permission_classes([IsAuthenticated])
# # def medication_status_resource(request, medication_id):
# #     if not _is_admin(request.user):
# #         return Response(
# #             {"error": {"code": "FORBIDDEN", "message": "You do not have permission."}},
# #             status=status.HTTP_403_FORBIDDEN,
# #         )

# #     medication = get_object_or_404(Medicamento.objects.select_related("estado"), pk=medication_id)
# #     status_id = request.data.get("status_id")

# #     if not status_id:
# #         return Response(
# #             {
# #                 "error": {
# #                     "code": "VALIDATION_ERROR",
# #                     "message": "Status is required.",
# #                     "fields": {"status_id": ["This field is required."]},
# #                 }
# #             },
# #             status=status.HTTP_400_BAD_REQUEST,
# #         )

# #     new_status = EstadoMedicamento.objects.filter(pk=status_id, activo=True).first()
# #     if not new_status:
# #         return Response(
# #             {
# #                 "error": {
# #                     "code": "INVALID_STATUS",
# #                     "message": "Invalid status.",
# #                     "fields": {"status_id": ["Invalid status."]},
# #                 }
# #             },
# #             status=status.HTTP_400_BAD_REQUEST,
# #         )

# #     old_status = medication.estado.nombre if medication.estado else None
# #     medication.estado = new_status
# #     medication.save(update_fields=["estado", "actualizado_en"])

# #     MedicamentoHistorial.objects.create(
# #         medicamento=medication,
# #         accion="CAMBIO_ESTADO",
# #         usuario=request.user,
# #         detalle=f"Status changed: {old_status} -> {new_status.nombre}",
# #     )

# #     return Response({
# #         "data": {
# #             "medication": _serialize_medication(medication)
# #         },
# #         "message": "Medication status updated successfully."
# #     })


# # @api_view(["GET"])
# # @permission_classes([IsAuthenticated])
# # def pharmaceutical_forms_catalog(request):
# #     items = FormaFarmaceutica.objects.filter(activo=True).order_by("nombre")
# #     return Response({
# #         "data": {
# #             "results": [_serialize_catalog_item(item) for item in items]
# #         },
# #         "message": "Pharmaceutical forms retrieved successfully."
# #     })


# # @api_view(["GET"])
# # @permission_classes([IsAuthenticated])
# # def presentations_catalog(request):
# #     form_id = request.GET.get("pharmaceutical_form_id")
# #     queryset = Presentacion.objects.filter(activo=True)

# #     if form_id:
# #         queryset = queryset.filter(forma_id=form_id)

# #     queryset = queryset.order_by("nombre")

# #     results = [
# #         {
# #             "id": item.id,
# #             "name": item.nombre,
# #             "pharmaceutical_form_id": item.forma_id,
# #         }
# #         for item in queryset
# #     ]

# #     return Response({
# #         "data": {
# #             "results": results
# #         },
# #         "message": "Presentations retrieved successfully."
# #     })


# # @api_view(["GET"])
# # @permission_classes([IsAuthenticated])
# # def administration_routes_catalog(request):
# #     items = ViaAdministracion.objects.filter(activo=True).order_by("nombre")
# #     return Response({
# #         "data": {
# #             "results": [_serialize_catalog_item(item) for item in items]
# #         },
# #         "message": "Administration routes retrieved successfully."
# #     })


# # @api_view(["GET"])
# # @permission_classes([IsAuthenticated])
# # def laboratories_catalog(request):
# #     items = Laboratorio.objects.filter(activo=True).order_by("nombre")
# #     return Response({
# #         "data": {
# #             "results": [_serialize_catalog_item(item) for item in items]
# #         },
# #         "message": "Laboratories retrieved successfully."
# #     })


# # @api_view(["GET"])
# # @permission_classes([IsAuthenticated])
# # def medication_statuses_catalog(request):
# #     items = EstadoMedicamento.objects.filter(activo=True).order_by("nombre")
# #     return Response({
# #         "data": {
# #             "results": [_serialize_catalog_item(item) for item in items]
# #         },
# #         "message": "Medication statuses retrieved successfully."
# #     })


# # @api_view(["GET"])
# # @permission_classes([IsAuthenticated])
# # def suppliers_catalog(request):
# #     queryset = Proveedor.objects.all().order_by("nombre")
# #     supplier_status = (request.GET.get("status") or "").strip()

# #     if supplier_status:
# #         queryset = queryset.filter(estado=supplier_status)

# #     results = [
# #         {
# #             "id": item.nit,
# #             "name": item.nombre,
# #             "nit": item.nit,
# #             "status": item.estado,
# #         }
# #         for item in queryset
# #     ]

# #     return Response({
# #         "data": {
# #             "results": results
# #         },
# #         "message": "Suppliers retrieved successfully."
# #     })

# # @api_view(["GET"])
# # @permission_classes([AllowAny])
# # def catalog_medications_resource(request):
# #     """
# #     Recurso de consulta read-only de medicamentos.

# #     Casos soportados:
# #     - búsqueda por id exacto -> ?id=12
# #     - búsqueda por nombre exacto -> ?query=Acetaminofen
# #     - búsqueda aproximada -> retorna sugerencias
# #     - búsqueda vacía -> lista paginada básica
# #     """
# #     queryset = Medicamento.objects.select_related(
# #         "forma",
# #         "presentacion",
# #         "via_administracion",
# #         "laboratorio",
# #         "proveedor",
# #         "estado",
# #     ).order_by("nombre")

# #     raw_id = (request.GET.get("id") or "").strip()
# #     raw_query = (request.GET.get("query") or "").strip()
# #     page = int(request.GET.get("page", 1))
# #     page_size = int(request.GET.get("page_size", 10))

# #     # =========================
# #     # BÚSQUEDA POR ID EXACTO
# #     # =========================
# #     if raw_id:
# #         if not raw_id.isdigit():
# #             return Response(
# #                 {
# #                     "error": {
# #                         "code": "INVALID_ID",
# #                         "message": "Medication id must be numeric.",
# #                         "fields": {
# #                             "id": ["Medication id must be numeric."]
# #                         },
# #                     }
# #                 },
# #                 status=status.HTTP_400_BAD_REQUEST,
# #             )

# #         medication = queryset.filter(pk=int(raw_id)).first()

# #         if not medication:
# #             return Response(
# #                 {
# #                     "data": {
# #                         "exact_match": None,
# #                         "results": [],
# #                         "suggestions": [],
# #                     },
# #                     "message": "Medication not found."
# #                 },
# #                 status=status.HTTP_200_OK,
# #             )

# #         return Response(
# #             {
# #                 "data": {
# #                     "exact_match": _serialize_catalog_medication(medication),
# #                     "results": [_serialize_catalog_medication(medication)],
# #                     "suggestions": [],
# #                 },
# #                 "message": "Medication retrieved successfully."
# #             },
# #             status=status.HTTP_200_OK,
# #         )

# #     # =========================
# #     # BÚSQUEDA POR NOMBRE
# #     # =========================
# #     if raw_query:
# #         exact_match = queryset.filter(nombre__iexact=raw_query).first()

# #         if exact_match:
# #             return Response(
# #                 {
# #                     "data": {
# #                         "exact_match": _serialize_catalog_medication(exact_match),
# #                         "results": [_serialize_catalog_medication(exact_match)],
# #                         "suggestions": [],
# #                     },
# #                     "message": "Medication retrieved successfully."
# #                 },
# #                 status=status.HTTP_200_OK,
# #             )

# #         partial_results = queryset.filter(nombre__icontains=raw_query)[:10]
# #         suggestions = _build_name_suggestions(queryset, raw_query)

# #         return Response(
# #             {
# #                 "data": {
# #                     "exact_match": None,
# #                     "results": [_serialize_catalog_medication(item) for item in partial_results],
# #                     "suggestions": suggestions,
# #                 },
# #                 "message": "Medication search completed."
# #             },
# #             status=status.HTTP_200_OK,
# #         )

# #     # =========================
# #     # LISTADO BÁSICO SIN FILTRO
# #     # =========================
# #     paginator = Paginator(queryset, page_size)
# #     page_obj = paginator.get_page(page)

# #     return Response(
# #         {
# #             "data": {
# #                 "exact_match": None,
# #                 "results": [_serialize_catalog_medication(item) for item in page_obj],
# #                 "suggestions": [],
# #                 "pagination": {
# #                     "count": paginator.count,
# #                     "num_pages": paginator.num_pages,
# #                     "page": page_obj.number,
# #                     "page_size": page_size,
# #                     "has_next": page_obj.has_next(),
# #                     "has_previous": page_obj.has_previous(),
# #                 },
# #             },
# #             "message": "Catalog medications retrieved successfully."
# #         },
# #         status=status.HTTP_200_OK,
# #     )


# # @api_view(["GET"])
# # @permission_classes([AllowAny])
# # def catalog_medication_detail_resource(request, medication_id):
# #     """
# #     Detalle read-only de medicamento para:
# #     - cliente público
# #     - cliente autenticado
# #     - admin
# #     - farmaceuta

# #     No expone edición.
# #     """
# #     medication = get_object_or_404(
# #         Medicamento.objects.select_related(
# #             "forma",
# #             "presentacion",
# #             "via_administracion",
# #             "laboratorio",
# #             "proveedor",
# #             "estado",
# #         ),
# #         pk=medication_id
# #     )

# #     return Response(
# #         {
# #             "data": {
# #                 "medication": _serialize_catalog_medication(medication)
# #             },
# #             "message": "Catalog medication retrieved successfully."
# #         },
# #         status=status.HTTP_200_OK,
# #     )

# # @api_view(["GET"])
# # @permission_classes([AllowAny])
# # def public_medications_search_resource(request):
# #     """
# #     Búsqueda pública/comercial de medicamentos.

# #     Este endpoint sirve para:
# #     - cliente sin login
# #     - cliente con login
# #     - admin/farmaceuta desde navbar
# #     - autocompletado del buscador
# #     - búsqueda por id o por nombre

# #     Reglas:
# #     - solo se listan medicamentos en estado Activo
# #     - solo se listan medicamentos vendibles
# #     """
# #     query = (request.GET.get("query") or "").strip()
# #     medication_id = (request.GET.get("id") or "").strip()

# #     queryset = Medicamento.objects.select_related(
# #         "forma",
# #         "presentacion",
# #         "via_administracion",
# #         "laboratorio",
# #         "proveedor",
# #         "estado",
# #     ).filter(
# #         estado__nombre="Activo"
# #     ).order_by("nombre")

# #     # =========================
# #     # BÚSQUEDA POR ID EXACTO
# #     # =========================
# #     if medication_id:
# #         medication = queryset.filter(pk=medication_id).first()

# #         if medication:
# #             return Response(
# #                 {
# #                     "data": {
# #                         "exact_match": _serialize_public_medication_search_item(medication),
# #                         "top_results": [_serialize_public_medication_search_item(medication)],
# #                         "suggestions": [],
# #                         "total_matches": 1,
# #                     },
# #                     "message": "Medication search completed successfully."
# #                 },
# #                 status=status.HTTP_200_OK,
# #             )

# #         return Response(
# #             {
# #                 "data": {
# #                     "exact_match": None,
# #                     "top_results": [],
# #                     "suggestions": [],
# #                     "total_matches": 0,
# #                 },
# #                 "message": "No medications found for the provided id."
# #             },
# #             status=status.HTTP_200_OK,
# #         )

# #     # =========================
# #     # BÚSQUEDA POR NOMBRE/TEXTO
# #     # =========================
# #     if not query:
# #         return Response(
# #             {
# #                 "data": {
# #                     "exact_match": None,
# #                     "top_results": [],
# #                     "suggestions": [],
# #                     "total_matches": 0,
# #                 },
# #                 "message": "Medication search completed successfully."
# #             },
# #             status=status.HTTP_200_OK,
# #         )

# #     filtered_queryset = queryset.filter(
# #         Q(nombre__icontains=query) |
# #         Q(concentracion__icontains=query) |
# #         Q(laboratorio__nombre__icontains=query) |
# #         Q(presentacion__nombre__icontains=query)
# #     )

# #     exact_match = queryset.filter(nombre__iexact=query).first()

# #     top_results = [
# #         _serialize_public_medication_search_item(item)
# #         for item in filtered_queryset[:6]
# #     ]

# #     suggestions = []

# #     # Si no hay coincidencia exacta o hay muy pocos resultados,
# #     # se intenta sugerir por similitud
# #     if not exact_match or len(top_results) < 3:
# #         suggestions = _build_medication_suggestions(
# #             query=query,
# #             queryset=queryset[:50],
# #             limit=5,
# #         )

# #     return Response(
# #         {
# #             "data": {
# #                 "exact_match": (
# #                     _serialize_public_medication_search_item(exact_match)
# #                     if exact_match else None
# #                 ),
# #                 "top_results": top_results,
# #                 "suggestions": suggestions,
# #                 "total_matches": filtered_queryset.count(),
# #             },
# #             "message": "Medication search completed successfully."
# #         },
# #         status=status.HTTP_200_OK,
# #     )


# # @api_view(["GET"])
# # @permission_classes([AllowAny])
# # def public_medication_detail_resource(request, medication_id):
# #     """
# #     Detalle público/comercial de medicamento.

# #     Este endpoint lo puede consumir:
# #     - cliente sin login
# #     - cliente logueado
# #     - admin
# #     - farmaceuta

# #     Regla:
# #     - solo expone medicamentos activos
# #     """
# #     medication = get_object_or_404(
# #         Medicamento.objects.select_related(
# #             "forma",
# #             "presentacion",
# #             "via_administracion",
# #             "laboratorio",
# #             "proveedor",
# #             "estado",
# #         ).filter(estado__nombre="Activo"),
# #         pk=medication_id
# #     )

# #     return Response(
# #         {
# #             "data": {
# #                 "medication": {
# #                     "id": medication.id,
# #                     "name": medication.nombre,
# #                     "description": medication.descripcion or "",
# #                     "pharmaceutical_form": medication.forma.nombre if medication.forma else "",
# #                     "presentation": medication.presentacion.nombre if medication.presentacion else "",
# #                     "concentration": medication.concentracion or "",
# #                     "administration_route": medication.via_administracion.nombre if medication.via_administracion else "",
# #                     "laboratory": medication.laboratorio.nombre if medication.laboratorio else "",
# #                     "batch": medication.lote or "",
# #                     "expiration_date": (
# #                         medication.fecha_vencimiento.isoformat()
# #                         if medication.fecha_vencimiento else None
# #                     ),
# #                     "stock": medication.stock or 0,
# #                     "sale_price": str(medication.precio_venta or 0),
# #                     "status": medication.estado.nombre if medication.estado else "",
# #                     "can_be_sold": medication.puede_venderse,
# #                 }
# #             },
# #             "message": "Medication retrieved successfully."
# #         },
# #         status=status.HTTP_200_OK,
# #     )

# from difflib import SequenceMatcher

# from django.core.paginator import Paginator
# from django.db.models import Q
# from django.shortcuts import get_object_or_404

# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated, AllowAny
# from rest_framework.response import Response
# from rest_framework import status

# from .models import (
#     Medicamento,
#     FormaFarmaceutica,
#     Presentacion,
#     ViaAdministracion,
#     Laboratorio,
#     EstadoMedicamento,
#     Proveedor,
#     MedicamentoHistorial,
# )
# from .forms import CrearMedicamentoForm, ActualizarMedicamentoForm


# def _is_admin(user):
#     return getattr(user, "rol", None) == "Administrador"


# def _build_media_url(request, file_field):
#     """
#     Construye la URL absoluta del archivo si existe.
#     """
#     if not file_field:
#         return None

#     try:
#         return request.build_absolute_uri(file_field.url)
#     except Exception:
#         return None


# def _serialize_medication(m, request=None):
#     """
#     Serialización administrativa completa.
#     """
#     return {
#         "id": m.id,
#         "name": m.nombre,
#         "image_url": _build_media_url(request, m.imagen) if request else None,
#         "pharmaceutical_form": {
#             "id": m.forma.id,
#             "name": m.forma.nombre,
#         } if m.forma else None,
#         "presentation": {
#             "id": m.presentacion.id,
#             "name": m.presentacion.nombre,
#         } if m.presentacion else None,
#         "concentration": m.concentracion,
#         "description": m.descripcion,
#         "administration_route": {
#             "id": m.via_administracion.id,
#             "name": m.via_administracion.nombre,
#         } if m.via_administracion else None,
#         "laboratory": {
#             "id": m.laboratorio.id,
#             "name": m.laboratorio.nombre,
#         } if m.laboratorio else None,
#         "batch": m.lote,
#         "manufacturing_date": m.fecha_fabricacion.isoformat() if m.fecha_fabricacion else None,
#         "expiration_date": m.fecha_vencimiento.isoformat() if m.fecha_vencimiento else None,
#         "stock": m.stock,
#         "purchase_price": str(m.precio_compra),
#         "sale_price": str(m.precio_venta),
#         "supplier": {
#             "id": m.proveedor.nit,
#             "name": m.proveedor.nombre,
#             "nit": m.proveedor.nit,
#         } if m.proveedor else None,
#         "requires_prescription": m.requiere_formula,
#         "status": {
#             "id": m.estado.id,
#             "name": m.estado.nombre,
#         } if m.estado else None,
#         "can_be_sold": m.puede_venderse,
#         "responsible": {
#             "id": m.responsable.id,
#             "name": m.responsable.nombre,
#             "email": m.responsable.email,
#         } if m.responsable else None,
#         "created_by": {
#             "id": m.creado_por.id,
#             "name": m.creado_por.nombre,
#             "email": m.creado_por.email,
#         } if m.creado_por else None,
#         "created_at": m.creado_en.isoformat() if m.creado_en else None,
#         "updated_at": m.actualizado_en.isoformat() if m.actualizado_en else None,
#     }


# def _serialize_catalog_medication(m, request=None):
#     """
#     Serialización read-only para consulta comercial/pública.
#     """
#     return {
#         "id": m.id,
#         "name": m.nombre,
#         "image_url": _build_media_url(request, m.imagen) if request else None,
#         "pharmaceutical_form": {
#             "id": m.forma.id,
#             "name": m.forma.nombre,
#         } if m.forma else None,
#         "presentation": {
#             "id": m.presentacion.id,
#             "name": m.presentacion.nombre,
#         } if m.presentacion else None,
#         "concentration": m.concentracion,
#         "description": m.descripcion,
#         "administration_route": {
#             "id": m.via_administracion.id,
#             "name": m.via_administracion.nombre,
#         } if m.via_administracion else None,
#         "laboratory": {
#             "id": m.laboratorio.id,
#             "name": m.laboratorio.nombre,
#         } if m.laboratorio else None,
#         "batch": m.lote,
#         "manufacturing_date": m.fecha_fabricacion.isoformat() if m.fecha_fabricacion else None,
#         "expiration_date": m.fecha_vencimiento.isoformat() if m.fecha_vencimiento else None,
#         "stock": m.stock,
#         "purchase_price": str(m.precio_compra),
#         "sale_price": str(m.precio_venta),
#         "supplier": {
#             "id": m.proveedor.nit,
#             "name": m.proveedor.nombre,
#             "nit": m.proveedor.nit,
#         } if m.proveedor else None,
#         "requires_prescription": m.requiere_formula,
#         "status": {
#             "id": m.estado.id,
#             "name": m.estado.nombre,
#         } if m.estado else None,
#         "can_be_sold": m.puede_venderse,
#         "created_at": m.creado_en.isoformat() if m.creado_en else None,
#         "updated_at": m.actualizado_en.isoformat() if m.actualizado_en else None,
#     }


# def _serialize_catalog_item(item):
#     return {
#         "id": getattr(item, "id", None),
#         "name": getattr(item, "nombre", None),
#     }


# def _serialize_public_medication_search_item(medication, request=None):
#     """
#     Serializa un medicamento para resultados de búsqueda pública/comercial.
#     """
#     return {
#         "id": medication.id,
#         "name": medication.nombre,
#         "image_url": _build_media_url(request, medication.imagen) if request else None,
#         "presentation": medication.presentacion.nombre if medication.presentacion else "",
#         "concentration": medication.concentracion or "",
#         "laboratory": medication.laboratorio.nombre if medication.laboratorio else "",
#         "description": medication.descripcion or "",
#         "sale_price": str(medication.precio_venta or 0),
#         "stock": medication.stock or 0,
#         "status": medication.estado.nombre if medication.estado else "",
#         "can_be_sold": medication.puede_venderse,
#     }


# def _build_name_suggestions(queryset, raw_query, request=None, limit=5):
#     """
#     Construye sugerencias cuando no existe coincidencia exacta.
#     """
#     normalized_query = (raw_query or "").strip().lower()

#     if not normalized_query:
#         return []

#     suggestions = []

#     for item in queryset:
#         candidate_name = (item.nombre or "").strip().lower()
#         length_diff = abs(len(candidate_name) - len(normalized_query))
#         similarity = SequenceMatcher(None, normalized_query, candidate_name).ratio()

#         if length_diff <= 2 or similarity >= 0.75:
#             suggestions.append((similarity, item))

#     suggestions.sort(key=lambda pair: pair[0], reverse=True)

#     return [_serialize_catalog_medication(item, request=request) for _, item in suggestions[:limit]]


# def _build_medication_suggestions(query, queryset, limit=5):
#     """
#     Construye sugerencias por similitud de nombre.
#     """
#     query_normalized = (query or "").strip().lower()
#     suggestions = []

#     if not query_normalized:
#         return suggestions

#     for medication in queryset:
#         medication_name = (medication.nombre or "").strip().lower()
#         similarity_ratio = SequenceMatcher(None, query_normalized, medication_name).ratio()

#         if similarity_ratio >= 0.75:
#             suggestions.append({
#                 "id": medication.id,
#                 "name": medication.nombre,
#             })

#         if len(suggestions) >= limit:
#             break

#     return suggestions


# @api_view(["GET", "POST"])
# @permission_classes([IsAuthenticated])
# def medications_resource(request):
#     """
#     Recurso administrativo de medicamentos.
#     """
#     if not _is_admin(request.user):
#         return Response(
#             {"error": {"code": "FORBIDDEN", "message": "You do not have permission."}},
#             status=status.HTTP_403_FORBIDDEN,
#         )

#     if request.method == "GET":
#         queryset = Medicamento.objects.select_related(
#             "forma",
#             "presentacion",
#             "via_administracion",
#             "laboratorio",
#             "proveedor",
#             "estado",
#             "responsable",
#             "creado_por",
#         ).order_by("nombre")

#         search = (request.GET.get("search") or "").strip()
#         administration_route = (request.GET.get("administration_route") or "").strip()
#         laboratory = (request.GET.get("laboratory") or "").strip()
#         medication_status = (request.GET.get("status") or "").strip()
#         page = int(request.GET.get("page", 1))
#         page_size = int(request.GET.get("page_size", 10))

#         if search:
#             queryset = queryset.filter(
#                 Q(nombre__icontains=search) |
#                 Q(concentracion__icontains=search) |
#                 Q(lote__icontains=search) |
#                 Q(proveedor__nombre__icontains=search)
#             )

#         if administration_route:
#             queryset = queryset.filter(via_administracion_id=administration_route)

#         if laboratory:
#             queryset = queryset.filter(laboratorio_id=laboratory)

#         if medication_status:
#             queryset = queryset.filter(estado_id=medication_status)

#         paginator = Paginator(queryset, page_size)
#         page_obj = paginator.get_page(page)

#         return Response({
#             "data": {
#                 "results": [_serialize_medication(item, request=request) for item in page_obj],
#                 "pagination": {
#                     "count": paginator.count,
#                     "num_pages": paginator.num_pages,
#                     "page": page_obj.number,
#                     "page_size": page_size,
#                     "has_next": page_obj.has_next(),
#                     "has_previous": page_obj.has_previous(),
#                 },
#                 "filters": {
#                     "search": search,
#                     "administration_route": administration_route,
#                     "laboratory": laboratory,
#                     "status": medication_status,
#                 }
#             },
#             "message": "Medications retrieved successfully."
#         })

#     # Importante:
#     # Para ImageField hay que pasar request.FILES al form.
#     form = CrearMedicamentoForm(request.data, request.FILES)

#     if form.is_valid():
#         medication = form.save(commit=False)
#         medication.creado_por = request.user
#         medication.requiere_formula = False
#         medication.laboratorio_texto = medication.laboratorio.nombre if medication.laboratorio else None
#         medication.save()

#         MedicamentoHistorial.objects.create(
#             medicamento=medication,
#             accion="CREADO",
#             usuario=request.user,
#             detalle="Medication created from SPA integration."
#         )

#         return Response(
#             {
#                 "data": {
#                     "medication": _serialize_medication(medication, request=request)
#                 },
#                 "message": "Medication created successfully."
#             },
#             status=status.HTTP_201_CREATED,
#         )

#     return Response(
#         {
#             "error": {
#                 "code": "VALIDATION_ERROR",
#                 "message": "Please correct the highlighted fields.",
#                 "fields": form.errors,
#             }
#         },
#         status=status.HTTP_400_BAD_REQUEST,
#     )


# @api_view(["GET", "PUT"])
# @permission_classes([IsAuthenticated])
# def medication_detail_resource(request, medication_id):
#     """
#     Detalle administrativo de medicamento.
#     """
#     if not _is_admin(request.user):
#         return Response(
#             {"error": {"code": "FORBIDDEN", "message": "You do not have permission."}},
#             status=status.HTTP_403_FORBIDDEN,
#         )

#     medication = get_object_or_404(
#         Medicamento.objects.select_related(
#             "forma",
#             "presentacion",
#             "via_administracion",
#             "laboratorio",
#             "proveedor",
#             "estado",
#             "responsable",
#             "creado_por",
#         ),
#         pk=medication_id
#     )

#     if request.method == "GET":
#         return Response({
#             "data": {
#                 "medication": _serialize_medication(medication, request=request)
#             },
#             "message": "Medication retrieved successfully."
#         })

#     # Importante:
#     # Para actualización con imagen también se debe pasar request.FILES.
#     form = ActualizarMedicamentoForm(request.data, request.FILES, instance=medication)

#     if form.is_valid():
#         updated = form.save(commit=False)
#         updated.laboratorio_texto = updated.laboratorio.nombre if updated.laboratorio else None
#         updated.save()

#         MedicamentoHistorial.objects.create(
#             medicamento=updated,
#             accion="ACTUALIZADO",
#             usuario=request.user,
#             detalle="Medication updated from SPA integration."
#         )

#         return Response({
#             "data": {
#                 "medication": _serialize_medication(updated, request=request)
#             },
#             "message": "Medication updated successfully."
#         })

#     return Response(
#         {
#             "error": {
#                 "code": "VALIDATION_ERROR",
#                 "message": "Please correct the highlighted fields.",
#                 "fields": form.errors,
#             }
#         },
#         status=status.HTTP_400_BAD_REQUEST,
#     )


# @api_view(["PATCH"])
# @permission_classes([IsAuthenticated])
# def medication_status_resource(request, medication_id):
#     """
#     Cambio de estado administrativo.
#     """
#     if not _is_admin(request.user):
#         return Response(
#             {"error": {"code": "FORBIDDEN", "message": "You do not have permission."}},
#             status=status.HTTP_403_FORBIDDEN,
#         )

#     medication = get_object_or_404(Medicamento.objects.select_related("estado"), pk=medication_id)
#     status_id = request.data.get("status_id")

#     if not status_id:
#         return Response(
#             {
#                 "error": {
#                     "code": "VALIDATION_ERROR",
#                     "message": "Status is required.",
#                     "fields": {"status_id": ["This field is required."]},
#                 }
#             },
#             status=status.HTTP_400_BAD_REQUEST,
#         )

#     new_status = EstadoMedicamento.objects.filter(pk=status_id, activo=True).first()
#     if not new_status:
#         return Response(
#             {
#                 "error": {
#                     "code": "INVALID_STATUS",
#                     "message": "Invalid status.",
#                     "fields": {"status_id": ["Invalid status."]},
#                 }
#             },
#             status=status.HTTP_400_BAD_REQUEST,
#         )

#     old_status = medication.estado.nombre if medication.estado else None
#     medication.estado = new_status
#     medication.save(update_fields=["estado", "actualizado_en"])

#     MedicamentoHistorial.objects.create(
#         medicamento=medication,
#         accion="CAMBIO_ESTADO",
#         usuario=request.user,
#         detalle=f"Status changed: {old_status} -> {new_status.nombre}",
#     )

#     return Response({
#         "data": {
#             "medication": _serialize_medication(medication, request=request)
#         },
#         "message": "Medication status updated successfully."
#     })


# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def pharmaceutical_forms_catalog(request):
#     items = FormaFarmaceutica.objects.filter(activo=True).order_by("nombre")
#     return Response({
#         "data": {
#             "results": [_serialize_catalog_item(item) for item in items]
#         },
#         "message": "Pharmaceutical forms retrieved successfully."
#     })


# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def presentations_catalog(request):
#     form_id = request.GET.get("pharmaceutical_form_id")
#     queryset = Presentacion.objects.filter(activo=True)

#     if form_id:
#         queryset = queryset.filter(forma_id=form_id)

#     queryset = queryset.order_by("nombre")

#     results = [
#         {
#             "id": item.id,
#             "name": item.nombre,
#             "pharmaceutical_form_id": item.forma_id,
#         }
#         for item in queryset
#     ]

#     return Response({
#         "data": {
#             "results": results
#         },
#         "message": "Presentations retrieved successfully."
#     })


# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def administration_routes_catalog(request):
#     items = ViaAdministracion.objects.filter(activo=True).order_by("nombre")
#     return Response({
#         "data": {
#             "results": [_serialize_catalog_item(item) for item in items]
#         },
#         "message": "Administration routes retrieved successfully."
#     })


# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def laboratories_catalog(request):
#     items = Laboratorio.objects.filter(activo=True).order_by("nombre")
#     return Response({
#         "data": {
#             "results": [_serialize_catalog_item(item) for item in items]
#         },
#         "message": "Laboratories retrieved successfully."
#     })


# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def medication_statuses_catalog(request):
#     items = EstadoMedicamento.objects.filter(activo=True).order_by("nombre")
#     return Response({
#         "data": {
#             "results": [_serialize_catalog_item(item) for item in items]
#         },
#         "message": "Medication statuses retrieved successfully."
#     })


# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def suppliers_catalog(request):
#     queryset = Proveedor.objects.all().order_by("nombre")
#     supplier_status = (request.GET.get("status") or "").strip()

#     if supplier_status:
#         queryset = queryset.filter(estado=supplier_status)

#     results = [
#         {
#             "id": item.nit,
#             "name": item.nombre,
#             "nit": item.nit,
#             "status": item.estado,
#         }
#         for item in queryset
#     ]

#     return Response({
#         "data": {
#             "results": results
#         },
#         "message": "Suppliers retrieved successfully."
#     })


# @api_view(["GET"])
# @permission_classes([AllowAny])
# def catalog_medications_resource(request):
#     """
#     Recurso de consulta read-only de medicamentos.
#     """
#     queryset = Medicamento.objects.select_related(
#         "forma",
#         "presentacion",
#         "via_administracion",
#         "laboratorio",
#         "proveedor",
#         "estado",
#     ).order_by("nombre")

#     raw_id = (request.GET.get("id") or "").strip()
#     raw_query = (request.GET.get("query") or "").strip()
#     page = int(request.GET.get("page", 1))
#     page_size = int(request.GET.get("page_size", 10))

#     if raw_id:
#         if not raw_id.isdigit():
#             return Response(
#                 {
#                     "error": {
#                         "code": "INVALID_ID",
#                         "message": "Medication id must be numeric.",
#                         "fields": {
#                             "id": ["Medication id must be numeric."]
#                         },
#                     }
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         medication = queryset.filter(pk=int(raw_id)).first()

#         if not medication:
#             return Response(
#                 {
#                     "data": {
#                         "exact_match": None,
#                         "results": [],
#                         "suggestions": [],
#                     },
#                     "message": "Medication not found."
#                 },
#                 status=status.HTTP_200_OK,
#             )

#         return Response(
#             {
#                 "data": {
#                     "exact_match": _serialize_catalog_medication(medication, request=request),
#                     "results": [_serialize_catalog_medication(medication, request=request)],
#                     "suggestions": [],
#                 },
#                 "message": "Medication retrieved successfully."
#             },
#             status=status.HTTP_200_OK,
#         )

#     if raw_query:
#         exact_match = queryset.filter(nombre__iexact=raw_query).first()

#         if exact_match:
#             return Response(
#                 {
#                     "data": {
#                         "exact_match": _serialize_catalog_medication(exact_match, request=request),
#                         "results": [_serialize_catalog_medication(exact_match, request=request)],
#                         "suggestions": [],
#                     },
#                     "message": "Medication retrieved successfully."
#                 },
#                 status=status.HTTP_200_OK,
#             )

#         partial_results = queryset.filter(nombre__icontains=raw_query)[:10]
#         suggestions = _build_name_suggestions(queryset, raw_query, request=request)

#         return Response(
#             {
#                 "data": {
#                     "exact_match": None,
#                     "results": [_serialize_catalog_medication(item, request=request) for item in partial_results],
#                     "suggestions": suggestions,
#                 },
#                 "message": "Medication search completed."
#             },
#             status=status.HTTP_200_OK,
#         )

#     paginator = Paginator(queryset, page_size)
#     page_obj = paginator.get_page(page)

#     return Response(
#         {
#             "data": {
#                 "exact_match": None,
#                 "results": [_serialize_catalog_medication(item, request=request) for item in page_obj],
#                 "suggestions": [],
#                 "pagination": {
#                     "count": paginator.count,
#                     "num_pages": paginator.num_pages,
#                     "page": page_obj.number,
#                     "page_size": page_size,
#                     "has_next": page_obj.has_next(),
#                     "has_previous": page_obj.has_previous(),
#                 },
#             },
#             "message": "Catalog medications retrieved successfully."
#         },
#         status=status.HTTP_200_OK,
#     )


# @api_view(["GET"])
# @permission_classes([AllowAny])
# def catalog_medication_detail_resource(request, medication_id):
#     """
#     Detalle read-only de medicamento para consulta general.
#     """
#     medication = get_object_or_404(
#         Medicamento.objects.select_related(
#             "forma",
#             "presentacion",
#             "via_administracion",
#             "laboratorio",
#             "proveedor",
#             "estado",
#         ),
#         pk=medication_id
#     )

#     return Response(
#         {
#             "data": {
#                 "medication": _serialize_catalog_medication(medication, request=request)
#             },
#             "message": "Catalog medication retrieved successfully."
#         },
#         status=status.HTTP_200_OK,
#     )


# @api_view(["GET"])
# @permission_classes([AllowAny])
# def public_medications_search_resource(request):
#     """
#     Búsqueda pública/comercial de medicamentos.
#     """
#     query = (request.GET.get("query") or "").strip()
#     medication_id = (request.GET.get("id") or "").strip()

#     queryset = Medicamento.objects.select_related(
#         "forma",
#         "presentacion",
#         "via_administracion",
#         "laboratorio",
#         "proveedor",
#         "estado",
#     ).filter(
#         estado__nombre="Activo"
#     ).order_by("nombre")

#     if medication_id:
#         medication = queryset.filter(pk=medication_id).first()

#         if medication:
#             return Response(
#                 {
#                     "data": {
#                         "exact_match": _serialize_public_medication_search_item(medication, request=request),
#                         "top_results": [_serialize_public_medication_search_item(medication, request=request)],
#                         "suggestions": [],
#                         "total_matches": 1,
#                     },
#                     "message": "Medication search completed successfully."
#                 },
#                 status=status.HTTP_200_OK,
#             )

#         return Response(
#             {
#                 "data": {
#                     "exact_match": None,
#                     "top_results": [],
#                     "suggestions": [],
#                     "total_matches": 0,
#                 },
#                 "message": "No medications found for the provided id."
#             },
#             status=status.HTTP_200_OK,
#         )

#     if not query:
#         return Response(
#             {
#                 "data": {
#                     "exact_match": None,
#                     "top_results": [],
#                     "suggestions": [],
#                     "total_matches": 0,
#                 },
#                 "message": "Medication search completed successfully."
#             },
#             status=status.HTTP_200_OK,
#         )

#     filtered_queryset = queryset.filter(
#         Q(nombre__icontains=query) |
#         Q(concentracion__icontains=query) |
#         Q(laboratorio__nombre__icontains=query) |
#         Q(presentacion__nombre__icontains=query)
#     )

#     exact_match = queryset.filter(nombre__iexact=query).first()

#     top_results = [
#         _serialize_public_medication_search_item(item, request=request)
#         for item in filtered_queryset[:6]
#     ]

#     suggestions = []
#     if not exact_match or len(top_results) < 3:
#         suggestions = _build_medication_suggestions(
#             query=query,
#             queryset=queryset[:50],
#             limit=5,
#         )

#     return Response(
#         {
#             "data": {
#                 "exact_match": (
#                     _serialize_public_medication_search_item(exact_match, request=request)
#                     if exact_match else None
#                 ),
#                 "top_results": top_results,
#                 "suggestions": suggestions,
#                 "total_matches": filtered_queryset.count(),
#             },
#             "message": "Medication search completed successfully."
#         },
#         status=status.HTTP_200_OK,
#     )


# @api_view(["GET"])
# @permission_classes([AllowAny])
# def public_medication_detail_resource(request, medication_id):
#     """
#     Detalle público/comercial de medicamento.
#     """
#     medication = get_object_or_404(
#         Medicamento.objects.select_related(
#             "forma",
#             "presentacion",
#             "via_administracion",
#             "laboratorio",
#             "proveedor",
#             "estado",
#         ).filter(estado__nombre="Activo"),
#         pk=medication_id
#     )

#     return Response(
#         {
#             "data": {
#                 "medication": {
#                     "id": medication.id,
#                     "name": medication.nombre,
#                     "image_url": _build_media_url(request, medication.imagen),
#                     "description": medication.descripcion or "",
#                     "pharmaceutical_form": medication.forma.nombre if medication.forma else "",
#                     "presentation": medication.presentacion.nombre if medication.presentacion else "",
#                     "concentration": medication.concentracion or "",
#                     "administration_route": medication.via_administracion.nombre if medication.via_administracion else "",
#                     "laboratory": medication.laboratorio.nombre if medication.laboratorio else "",
#                     "batch": medication.lote or "",
#                     "expiration_date": (
#                         medication.fecha_vencimiento.isoformat()
#                         if medication.fecha_vencimiento else None
#                     ),
#                     "stock": medication.stock or 0,
#                     "sale_price": str(medication.precio_venta or 0),
#                     "status": medication.estado.nombre if medication.estado else "",
#                     "can_be_sold": medication.puede_venderse,
#                 }
#             },
#             "message": "Medication retrieved successfully."
#         },
#         status=status.HTTP_200_OK,
#     )
