from django.urls import path
from . import views

urlpatterns = [
    # =========================
    # MEDICAMENTOS
    # =========================
    path("medicamentos/crear/", views.crear_medicamento, name="crear_medicamento"),
    path("medicamentos/", views.listar_medicamentos, name="listar_medicamentos"),
    path("medicamentos/<int:pk>/cambiar-estado/", views.cambiar_estado_medicamento, name="cambiar_estado_medicamento"),
    path("api/medicamentos/", views.api_listar_medicamentos, name="api_listar_medicamentos"),
    path("medicamentos/reporte/", views.reporte_medicamentos, name="reporte_medicamentos"),
    path("api/presentaciones/", views.presentaciones_por_forma, name="presentaciones_por_forma"),
    path("medicamentos/<int:pk>/editar/", views.editar_medicamento, name="editar_medicamento"),

    # =========================
    # PROVEEDORES
    # =========================
    path("proveedores/crear/", views.crear_proveedor, name="crear_proveedor"),
    path("proveedores/visualizar/", views.visualizar_proveedores, name="visualizar_proveedores"),
    path("proveedores/<str:pk>/editar/", views.editar_proveedor, name="editar_proveedor"),
    path("proveedores/<str:pk>/cambiar-estado/", views.cambiar_estado_proveedor, name="cambiar_estado_proveedor"),
]