from django.urls import path
from . import views
from . import api_products_views as api_views

urlpatterns = [
    # =========================
    # SPA / V1
    # =========================
    path("v1/inventory/medications/", api_views.medications_resource, name="medications_resource"),
    path("v1/inventory/medications/client/list/",api_views.medications_client_list_resource,name="medications_client_list"),
    path("v1/inventory/medications/client/view/",api_views.medication_client_view_resource,name="medication_client_view"),
    path("v1/inventory/medications/<int:medication_id>/", api_views.medication_detail_resource, name="medication_detail_resource"),
    path("v1/inventory/medications/<int:medication_id>/status/", api_views.medication_status_resource, name="medication_status_resource"),

    path("v1/catalogs/pharmaceutical-forms/", api_views.pharmaceutical_forms_catalog, name="pharmaceutical_forms_catalog"),
    path("v1/catalogs/presentations/", api_views.presentations_catalog, name="presentations_catalog"),
    path("v1/catalogs/administration-routes/", api_views.administration_routes_catalog, name="administration_routes_catalog"),
    path("v1/catalogs/laboratories/", api_views.laboratories_catalog, name="laboratories_catalog"),
    path("v1/catalogs/medication-statuses/", api_views.medication_statuses_catalog, name="medication_statuses_catalog"),
    path("v1/procurement/suppliers/", api_views.suppliers_catalog, name="suppliers_catalog"),

    # =========================
    # LEGACY / PRUEBAS
    # =========================
    path("medicamentos/crear/", views.crear_medicamento, name="crear_medicamento"),
    path("medicamentos/", views.listar_medicamentos, name="listar_medicamentos"),
    path("medicamentos/<int:pk>/cambiar-estado/", views.cambiar_estado_medicamento, name="cambiar_estado_medicamento"),
    path("api/medicamentos/", views.api_listar_medicamentos, name="api_listar_medicamentos"),
    path("medicamentos/reporte/", views.reporte_medicamentos, name="reporte_medicamentos"),
    path("api/presentaciones/", views.presentaciones_por_forma, name="presentaciones_por_forma"),
    path("medicamentos/<int:pk>/editar/", views.editar_medicamento, name="editar_medicamento"),

    path("proveedores/crear/", views.crear_proveedor, name="crear_proveedor"),
    path("proveedores/visualizar/", views.visualizar_proveedores, name="visualizar_proveedores"),
    path("proveedores/<str:pk>/editar/", views.editar_proveedor, name="editar_proveedor"),
    path("proveedores/<str:pk>/cambiar-estado/", views.cambiar_estado_proveedor, name="cambiar_estado_proveedor"),
]