from django.urls import path
from . import views

urlpatterns = [
    path("medicamentos/crear/", views.crear_medicamento, name="crear_medicamento"),
    path("medicamentos/", views.listar_medicamentos, name="listar_medicamentos"),
    #URL para cambiar estado de medicamento solo para ADMIN
    path("medicamentos/<int:pk>/cambiar-estado/", views.cambiar_estado_medicamento, name="cambiar_estado_medicamento"),
    #URL para listar medicamentos
    path("api/medicamentos/", views.api_listar_medicamentos, name="api_listar_medicamentos"),
    #URL para reporte de medicamentos
    path("medicamentos/reporte/", views.reporte_medicamentos, name="reporte_medicamentos"),
    #URL para presentaciones por forma
    path("api/presentaciones/", views.presentaciones_por_forma, name="presentaciones_por_forma"),
    #URL para editar medicamento Daya 
    path("medicamentos/<int:pk>/editar/", views.editar_medicamento, name="editar_medicamento"),

]