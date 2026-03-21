from django.urls import path

from . import views

urlpatterns = [
    path("crear/", views.crear_venta, name="crear_venta"),
    path("<int:pk>/", views.detalle_venta, name="detalle_venta"),
    path(
        "<int:pk>/confirmar-vendedor/",
        views.confirmar_pago_vendedor,
        name="confirmar_pago_vendedor",
    ),
    path(
        "<int:pk>/confirmar-cliente/",
        views.confirmar_pago_cliente,
        name="confirmar_pago_cliente",
    ),
    path("<int:pk>/anular/", views.anular_venta, name="anular_venta"),
]
