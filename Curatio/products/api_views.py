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

from difflib import SequenceMatcher

from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
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
from .forms import (
    CrearMedicamentoForm,
    ActualizarMedicamentoForm,
    CrearProveedorForm,
    ActualizarProveedorForm,
)


def _is_admin(user):
    """
    Valida si el usuario autenticado es Administrador.
    """
    return getattr(user, "rol", None) == "Administrador"


def _puede_gestionar_proveedores(user):
    """
    Permite gestión de proveedores a:
    - Administrador
    - Farmaceuta

    Se consulta el rol real en BD para evitar inconsistencias
    entre sesión y datos actuales del usuario.
    """
    if not getattr(user, "is_authenticated", False):
        return False

    pk = getattr(user, "pk", None)
    if not pk:
        return False

    rol = (
        get_user_model()
        .objects.filter(pk=pk)
        .values_list("rol", flat=True)
        .first()
    )

    if rol is None:
        return False

    return str(rol).strip().casefold() in ("administrador", "farmaceuta")


def _forbidden_suppliers_response():
    """
    Respuesta estándar cuando un usuario no tiene permisos
    para gestionar proveedores.
    """
    return Response(
        {
            "error": {
                "code": "FORBIDDEN",
                "message": "You do not have permission.",
            }
        },
        status=status.HTTP_403_FORBIDDEN,
    )


def _normalize_supplier_estado_payload(data):
    """
    Normaliza el estado enviado para proveedor.

    Acepta:
    - estado=Activo / Inactivo
    - status=active / inactive
    - otras variantes equivalentes
    """
    raw = (data.get("estado") or data.get("status") or "").strip()

    if raw in ("Activo", "Inactivo"):
        return raw

    low = raw.casefold()

    if low in ("active", "activo", "true", "1", "enabled", "habilitado"):
        return "Activo"

    if low in ("inactive", "inactivo", "false", "0", "disabled", "deshabilitado"):
        return "Inactivo"

    return None


def _build_media_url(request, file_field):
    """
    Construye la URL absoluta del archivo si existe.
    """
    if not file_field:
        return None

    try:
        return request.build_absolute_uri(file_field.url)
    except Exception:
        return None


def _serialize_medication(m, request=None):
    """
    Serialización administrativa completa del medicamento.
    """
    return {
        "id": m.id,
        "name": m.nombre,
        "image_url": _build_media_url(request, m.imagen) if request else None,
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


def _serialize_catalog_medication(m, request=None):
    """
    Serialización read-only para consulta comercial/pública.
    """
    return {
        "id": m.id,
        "name": m.nombre,
        "image_url": _build_media_url(request, m.imagen) if request else None,
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
        "created_at": m.creado_en.isoformat() if m.creado_en else None,
        "updated_at": m.actualizado_en.isoformat() if m.actualizado_en else None,
    }


def _serialize_catalog_item(item):
    """
    Serialización genérica de catálogos simples.
    """
    return {
        "id": getattr(item, "id", None),
        "name": getattr(item, "nombre", None),
    }


def _serialize_public_medication_search_item(medication, request=None):
    """
    Serializa un medicamento para resultados de búsqueda pública/comercial.
    """
    return {
        "id": medication.id,
        "name": medication.nombre,
        "image_url": _build_media_url(request, medication.imagen) if request else None,
        "presentation": medication.presentacion.nombre if medication.presentacion else "",
        "concentration": medication.concentracion or "",
        "laboratory": medication.laboratorio.nombre if medication.laboratorio else "",
        "description": medication.descripcion or "",
        "sale_price": str(medication.precio_venta or 0),
        "stock": medication.stock or 0,
        "status": medication.estado.nombre if medication.estado else "",
        "can_be_sold": medication.puede_venderse,
    }


def _serialize_supplier_row(item):
    """
    Serialización estándar del proveedor.

    Mantiene:
    - id
    - name
    - nit
    - status

    Y además incluye campos útiles para la SPA de proveedores.
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


def _build_name_suggestions(queryset, raw_query, request=None, limit=5):
    """
    Construye sugerencias cuando no existe coincidencia exacta.
    """
    normalized_query = (raw_query or "").strip().lower()

    if not normalized_query:
        return []

    suggestions = []

    for item in queryset:
        candidate_name = (item.nombre or "").strip().lower()
        length_diff = abs(len(candidate_name) - len(normalized_query))
        similarity = SequenceMatcher(None, normalized_query, candidate_name).ratio()

        if length_diff <= 2 or similarity >= 0.75:
            suggestions.append((similarity, item))

    suggestions.sort(key=lambda pair: pair[0], reverse=True)

    return [
        _serialize_catalog_medication(item, request=request)
        for _, item in suggestions[:limit]
    ]


def _build_medication_suggestions(query, queryset, limit=5):
    """
    Construye sugerencias por similitud de nombre.
    """
    query_normalized = (query or "").strip().lower()
    suggestions = []

    if not query_normalized:
        return suggestions

    for medication in queryset:
        medication_name = (medication.nombre or "").strip().lower()
        similarity_ratio = SequenceMatcher(None, query_normalized, medication_name).ratio()

        if similarity_ratio >= 0.75:
            suggestions.append({
                "id": medication.id,
                "name": medication.nombre,
            })

        if len(suggestions) >= limit:
            break

    return suggestions


def _supplier_estado_change_response(request, proveedor):
    """
    Actualiza el estado Activo/Inactivo del proveedor y registra historial.
    """
    nuevo_estado = _normalize_supplier_estado_payload(request.data)

    if nuevo_estado is None:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid status.",
                    "fields": {
                        "estado": [
                            'Debe ser "Activo" o "Inactivo" (o status active/inactive).'
                        ]
                    },
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    estado_anterior = proveedor.estado

    if estado_anterior == nuevo_estado:
        return Response(
            {
                "data": {
                    "supplier": _serialize_supplier_row(proveedor),
                },
                "message": "Supplier status unchanged.",
            }
        )

    proveedor.estado = nuevo_estado
    proveedor.save(update_fields=["estado", "actualizado_en"])

    ProveedorHistorial.objects.create(
        proveedor=proveedor,
        accion="CAMBIO_ESTADO",
        usuario=request.user,
        detalle=f"Estado: {estado_anterior} → {nuevo_estado}",
    )

    return Response(
        {
            "data": {
                "supplier": _serialize_supplier_row(proveedor),
            },
            "message": "Supplier status updated successfully.",
        }
    )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def medications_resource(request):
    """
    Recurso administrativo de medicamentos.
    """
    if not _is_admin(request.user):
        return Response(
            {
                "error": {
                    "code": "FORBIDDEN",
                    "message": "You do not have permission.",
                }
            },
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
                "results": [_serialize_medication(item, request=request) for item in page_obj],
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

    form = CrearMedicamentoForm(request.data, request.FILES)

    if form.is_valid():
        medication = form.save(commit=False)
        medication.creado_por = request.user
        medication.requiere_formula = False
        medication.laboratorio_texto = (
            medication.laboratorio.nombre if medication.laboratorio else None
        )
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
                    "medication": _serialize_medication(medication, request=request)
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
    """
    Detalle administrativo de medicamento.
    """
    if not _is_admin(request.user):
        return Response(
            {
                "error": {
                    "code": "FORBIDDEN",
                    "message": "You do not have permission.",
                }
            },
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
                "medication": _serialize_medication(medication, request=request)
            },
            "message": "Medication retrieved successfully."
        })

    form = ActualizarMedicamentoForm(request.data, request.FILES, instance=medication)

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
                "medication": _serialize_medication(updated, request=request)
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
    """
    Cambio de estado administrativo.
    """
    if not _is_admin(request.user):
        return Response(
            {
                "error": {
                    "code": "FORBIDDEN",
                    "message": "You do not have permission.",
                }
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    medication = get_object_or_404(
        Medicamento.objects.select_related("estado"),
        pk=medication_id
    )
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
            "medication": _serialize_medication(medication, request=request)
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


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def suppliers_catalog(request):
    """
    GET: listado de proveedores para la SPA.
         Soporta filtros por NIT, nombre y estado.
    POST: creación de proveedor por Administrador o Farmaceuta.
    """
    if request.method == "GET":
        queryset = Proveedor.objects.all().order_by("nombre")

        supplier_nit = (request.GET.get("nit") or "").strip()
        supplier_name = (request.GET.get("name") or "").strip()
        supplier_status = (request.GET.get("status") or "").strip()

        if supplier_nit:
            queryset = queryset.filter(nit__icontains=supplier_nit)

        if supplier_name:
            queryset = queryset.filter(nombre__icontains=supplier_name)

        if supplier_status:
            queryset = queryset.filter(estado=supplier_status)

        results = [_serialize_supplier_row(item) for item in queryset]

        return Response(
            {
                "data": {
                    "results": results,
                    "filters": {
                        "nit": supplier_nit,
                        "name": supplier_name,
                        "status": supplier_status,
                    },
                    "count": len(results),
                },
                "message": "Suppliers retrieved successfully.",
            }
        )

    if not _puede_gestionar_proveedores(request.user):
        return _forbidden_suppliers_response()

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
            detalle=(
                "Proveedor creado desde API (SPA) "
                f"el {proveedor.creado_en.strftime('%Y-%m-%d %H:%M:%S')}."
                if proveedor.creado_en
                else "Proveedor creado desde API (SPA)."
            ),
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


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def supplier_detail_resource(request, supplier_nit):
    """
    GET: detalle por NIT.
    PATCH: actualización completa de campos editables del proveedor.

    Importante:
    - El NIT se usa como PK y no se actualiza desde este recurso.
    - El cambio exclusivo de estado también puede hacerse mediante
      la ruta /status/ cuando el frontend quiera separar ambas acciones.
    """
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

    if request.method == "GET":
        return Response(
            {
                "data": {
                    "supplier": _serialize_supplier_row(proveedor),
                },
                "message": "Supplier retrieved successfully.",
            }
        )

    if not _puede_gestionar_proveedores(request.user):
        return _forbidden_suppliers_response()

    return _supplier_update_response(request, proveedor)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def supplier_status_resource(request, supplier_nit):
    """
    Cambio específico de estado Activo/Inactivo del proveedor.

    Se mantiene como recurso dedicado para que la SPA pueda cambiar
    el estado sin enviar el resto del formulario de edición.
    """
    if not _puede_gestionar_proveedores(request.user):
        return _forbidden_suppliers_response()

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

    return _supplier_estado_change_response(request, proveedor)


@api_view(["GET"])
@permission_classes([AllowAny])
def catalog_medications_resource(request):
    """
    Recurso de consulta read-only de medicamentos.
    """
    queryset = Medicamento.objects.select_related(
        "forma",
        "presentacion",
        "via_administracion",
        "laboratorio",
        "proveedor",
        "estado",
    ).order_by("nombre")

    raw_id = (request.GET.get("id") or "").strip()
    raw_query = (request.GET.get("query") or "").strip()
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 10))

    if raw_id:
        if not raw_id.isdigit():
            return Response(
                {
                    "error": {
                        "code": "INVALID_ID",
                        "message": "Medication id must be numeric.",
                        "fields": {
                            "id": ["Medication id must be numeric."]
                        },
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        medication = queryset.filter(pk=int(raw_id)).first()

        if not medication:
            return Response(
                {
                    "data": {
                        "exact_match": None,
                        "results": [],
                        "suggestions": [],
                    },
                    "message": "Medication not found."
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "data": {
                    "exact_match": _serialize_catalog_medication(medication, request=request),
                    "results": [_serialize_catalog_medication(medication, request=request)],
                    "suggestions": [],
                },
                "message": "Medication retrieved successfully."
            },
            status=status.HTTP_200_OK,
        )

    if raw_query:
        exact_match = queryset.filter(nombre__iexact=raw_query).first()

        if exact_match:
            return Response(
                {
                    "data": {
                        "exact_match": _serialize_catalog_medication(exact_match, request=request),
                        "results": [_serialize_catalog_medication(exact_match, request=request)],
                        "suggestions": [],
                    },
                    "message": "Medication retrieved successfully."
                },
                status=status.HTTP_200_OK,
            )

        partial_results = queryset.filter(nombre__icontains=raw_query)[:10]
        suggestions = _build_name_suggestions(queryset, raw_query, request=request)

        return Response(
            {
                "data": {
                    "exact_match": None,
                    "results": [
                        _serialize_catalog_medication(item, request=request)
                        for item in partial_results
                    ],
                    "suggestions": suggestions,
                },
                "message": "Medication search completed."
            },
            status=status.HTTP_200_OK,
        )

    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)

    return Response(
        {
            "data": {
                "exact_match": None,
                "results": [
                    _serialize_catalog_medication(item, request=request)
                    for item in page_obj
                ],
                "suggestions": [],
                "pagination": {
                    "count": paginator.count,
                    "num_pages": paginator.num_pages,
                    "page": page_obj.number,
                    "page_size": page_size,
                    "has_next": page_obj.has_next(),
                    "has_previous": page_obj.has_previous(),
                },
            },
            "message": "Catalog medications retrieved successfully."
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def catalog_medication_detail_resource(request, medication_id):
    """
    Detalle read-only de medicamento para consulta general.
    """
    medication = get_object_or_404(
        Medicamento.objects.select_related(
            "forma",
            "presentacion",
            "via_administracion",
            "laboratorio",
            "proveedor",
            "estado",
        ),
        pk=medication_id
    )

    return Response(
        {
            "data": {
                "medication": _serialize_catalog_medication(medication, request=request)
            },
            "message": "Catalog medication retrieved successfully."
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def public_medications_search_resource(request):
    """
    Búsqueda pública/comercial de medicamentos.
    """
    query = (request.GET.get("query") or "").strip()
    medication_id = (request.GET.get("id") or "").strip()

    queryset = Medicamento.objects.select_related(
        "forma",
        "presentacion",
        "via_administracion",
        "laboratorio",
        "proveedor",
        "estado",
    ).filter(
        estado__nombre="Activo"
    ).order_by("nombre")

    if medication_id:
        medication = queryset.filter(pk=medication_id).first()

        if medication:
            return Response(
                {
                    "data": {
                        "exact_match": _serialize_public_medication_search_item(
                            medication,
                            request=request
                        ),
                        "top_results": [_serialize_public_medication_search_item(
                            medication,
                            request=request
                        )],
                        "suggestions": [],
                        "total_matches": 1,
                    },
                    "message": "Medication search completed successfully."
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "data": {
                    "exact_match": None,
                    "top_results": [],
                    "suggestions": [],
                    "total_matches": 0,
                },
                "message": "No medications found for the provided id."
            },
            status=status.HTTP_200_OK,
        )

    if not query:
        return Response(
            {
                "data": {
                    "exact_match": None,
                    "top_results": [],
                    "suggestions": [],
                    "total_matches": 0,
                },
                "message": "Medication search completed successfully."
            },
            status=status.HTTP_200_OK,
        )

    filtered_queryset = queryset.filter(
        Q(nombre__icontains=query) |
        Q(concentracion__icontains=query) |
        Q(laboratorio__nombre__icontains=query) |
        Q(presentacion__nombre__icontains=query)
    )

    exact_match = queryset.filter(nombre__iexact=query).first()

    top_results = [
        _serialize_public_medication_search_item(item, request=request)
        for item in filtered_queryset[:6]
    ]

    suggestions = []
    if not exact_match or len(top_results) < 3:
        suggestions = _build_medication_suggestions(
            query=query,
            queryset=queryset[:50],
            limit=5,
        )

    return Response(
        {
            "data": {
                "exact_match": (
                    _serialize_public_medication_search_item(exact_match, request=request)
                    if exact_match else None
                ),
                "top_results": top_results,
                "suggestions": suggestions,
                "total_matches": filtered_queryset.count(),
            },
            "message": "Medication search completed successfully."
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def public_medication_detail_resource(request, medication_id):
    """
    Detalle público/comercial de medicamento.
    """
    medication = get_object_or_404(
        Medicamento.objects.select_related(
            "forma",
            "presentacion",
            "via_administracion",
            "laboratorio",
            "proveedor",
            "estado",
        ).filter(estado__nombre="Activo"),
        pk=medication_id
    )

    return Response(
        {
            "data": {
                "medication": {
                    "id": medication.id,
                    "name": medication.nombre,
                    "image_url": _build_media_url(request, medication.imagen),
                    "description": medication.descripcion or "",
                    "pharmaceutical_form": (
                        medication.forma.nombre if medication.forma else ""
                    ),
                    "presentation": (
                        medication.presentacion.nombre if medication.presentacion else ""
                    ),
                    "concentration": medication.concentracion or "",
                    "administration_route": (
                        medication.via_administracion.nombre
                        if medication.via_administracion else ""
                    ),
                    "laboratory": (
                        medication.laboratorio.nombre if medication.laboratorio else ""
                    ),
                    "batch": medication.lote or "",
                    "expiration_date": (
                        medication.fecha_vencimiento.isoformat()
                        if medication.fecha_vencimiento else None
                    ),
                    "stock": medication.stock or 0,
                    "sale_price": str(medication.precio_venta or 0),
                    "status": medication.estado.nombre if medication.estado else "",
                    "can_be_sold": medication.puede_venderse,
                }
            },
            "message": "Medication retrieved successfully."
        },
        status=status.HTTP_200_OK,
    )

def _serialize_supplier_suggestion(item):
    """
    Serialización reducida para sugerencias de búsqueda de proveedor.
    """
    return {
        "id": item.nit,
        "nit": item.nit,
        "name": item.nombre,
    }


def _build_supplier_suggestions(queryset, raw_query, limit=5):
    """
    Construye sugerencias de proveedores cuando no existe coincidencia exacta.

    Regla de negocio soportada:
    - sugerir proveedores cuyo nombre difiera en 1 o 2 letras
    - o que tengan similitud razonable por comparación difusa
    """
    normalized_query = (raw_query or "").strip().lower()

    if not normalized_query:
        return []

    suggestions = []

    for item in queryset:
        candidate_name = (item.nombre or "").strip().lower()
        length_diff = abs(len(candidate_name) - len(normalized_query))
        similarity = SequenceMatcher(None, normalized_query, candidate_name).ratio()

        if length_diff <= 2 or similarity >= 0.75:
            suggestions.append((similarity, item))

    suggestions.sort(key=lambda pair: pair[0], reverse=True)

    return [
        _serialize_supplier_suggestion(item)
        for _, item in suggestions[:limit]
    ]


def _supplier_update_response(request, proveedor):
    """
    Actualiza los campos editables del proveedor y registra historial.

    Campos permitidos por requerimiento:
    - nombre
    - razon_social
    - nombre_contacto
    - telefono_contacto
    - correo_contacto
    - direccion
    - ciudad
    - estado

    Regla de negocio:
    - el NIT no se modifica desde la API de actualización
    """
    # Se toma una copia mutable para ignorar cualquier intento
    # de cambiar el NIT desde el cliente.
    payload = request.data.copy()
    payload.pop("nit", None)

    form = ActualizarProveedorForm(payload, instance=proveedor)

    if form.is_valid():
        proveedor_actualizado = form.save()

        ProveedorHistorial.objects.create(
            proveedor=proveedor_actualizado,
            accion="ACTUALIZADO",
            usuario=request.user,
            detalle=(
                "Proveedor actualizado desde API (SPA) "
                f"el {proveedor_actualizado.actualizado_en.strftime('%Y-%m-%d %H:%M:%S')}."
                if proveedor_actualizado.actualizado_en
                else "Proveedor actualizado desde API (SPA)."
            ),
        )

        return Response(
            {
                "data": {
                    "supplier": _serialize_supplier_row(proveedor_actualizado),
                },
                "message": "Supplier updated successfully.",
            }
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