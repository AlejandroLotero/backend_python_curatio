from django.urls import path
from . import views

urlpatterns = [
    path("medicamentos/crear/", views.crear_medicamento, name="crear_medicamento"),
    path("api/presentaciones/", views.presentaciones_por_forma, name="presentaciones_por_forma"),
]