from django.contrib import admin

from .models import Venta, VentaHistorial, VentaLinea


class VentaLineaInline(admin.TabularInline):
    model = VentaLinea
    extra = 0


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = (
        "numero_factura",
        "fecha_hora",
        "cliente",
        "vendedor",
        "estado",
        "total",
        "tipo_pago",
    )
    list_filter = ("estado", "tipo_pago")
    search_fields = ("numero_factura", "cliente__email", "vendedor__email")
    inlines = [VentaLineaInline]


@admin.register(VentaHistorial)
class VentaHistorialAdmin(admin.ModelAdmin):
    list_display = ("venta", "accion", "usuario", "fecha")
    list_filter = ("accion",)
