# from django.urls import path
# from . import api_views

# urlpatterns = [

#      # =========================
#     # SPA / V1 PÚBLICO-COMERCIAL
#     # =========================
#     path("v1/catalogs/medications/", api_views.public_medications_search_resource, name="public_medications_search_resource"),
#     path("v1/catalogs/medications/<int:medication_id>/", api_views.public_medication_detail_resource, name="public_medication_detail_resource"),
#     path("v1/catalog/medications/search/", api_views.public_medications_search_resource, name="public_medications_search_resource"),
#     path("v1/catalog/medications/<int:medication_id>/", api_views.public_medication_detail_resource, name="public_medication_detail_resource"),
#     # =========================
#     # INVENTARIO / GESTIÓN
#     # =========================
#     path("v1/inventory/medications/", api_views.medications_resource, name="medications_resource"),
#     path("v1/inventory/medications/<int:medication_id>/", api_views.medication_detail_resource, name="medication_detail_resource"),
#     path("v1/inventory/medications/<int:medication_id>/status/", api_views.medication_status_resource, name="medication_status_resource"),

#     path("v1/catalogs/pharmaceutical-forms/", api_views.pharmaceutical_forms_catalog, name="pharmaceutical_forms_catalog"),
#     path("v1/catalogs/presentations/", api_views.presentations_catalog, name="presentations_catalog"),
#     path("v1/catalogs/administration-routes/", api_views.administration_routes_catalog, name="administration_routes_catalog"),
#     path("v1/catalogs/laboratories/", api_views.laboratories_catalog, name="laboratories_catalog"),
#     path("v1/catalogs/medication-statuses/", api_views.medication_statuses_catalog, name="medication_statuses_catalog"),
#     path("v1/procurement/suppliers/", api_views.suppliers_catalog, name="suppliers_catalog"),
# ]

from django.urls import path
from . import api_views

urlpatterns = [
    # =========================
    # SPA / V1 PÚBLICO-COMERCIAL
    # =========================

    # Listado/catálogo general para home y resultados amplios
    path(
        "v1/catalogs/medications/",
        api_views.catalog_medications_resource,
        name="catalog_medications_resource",
    ),

    # Detalle público/comercial
    path(
        "v1/catalogs/medications/<int:medication_id>/",
        api_views.public_medication_detail_resource,
        name="public_medication_detail_resource",
    ),

    # Búsqueda rápida/autocompletado del navbar
    path(
        "v1/catalog/medications/search/",
        api_views.public_medications_search_resource,
        name="public_medications_search_resource",
    ),

    # Alias opcional del detalle público
    path(
        "v1/catalog/medications/<int:medication_id>/",
        api_views.public_medication_detail_resource,
        name="public_medication_detail_alias_resource",
    ),

    # =========================
    # INVENTARIO / GESTIÓN
    # =========================
    path("v1/inventory/medications/", api_views.medications_resource, name="medications_resource"),
    path("v1/inventory/medications/<int:medication_id>/", api_views.medication_detail_resource, name="medication_detail_resource"),
    path("v1/inventory/medications/<int:medication_id>/status/", api_views.medication_status_resource, name="medication_status_resource"),

    path("v1/catalogs/pharmaceutical-forms/", api_views.pharmaceutical_forms_catalog, name="pharmaceutical_forms_catalog"),
    path("v1/catalogs/presentations/", api_views.presentations_catalog, name="presentations_catalog"),
    path("v1/catalogs/administration-routes/", api_views.administration_routes_catalog, name="administration_routes_catalog"),
    path("v1/catalogs/laboratories/", api_views.laboratories_catalog, name="laboratories_catalog"),
    path("v1/catalogs/medication-statuses/", api_views.medication_statuses_catalog, name="medication_statuses_catalog"),
    path("v1/procurement/suppliers/", api_views.suppliers_catalog, name="suppliers_catalog"),
]