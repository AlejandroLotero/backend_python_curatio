from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import (
    FormaFarmaceutica, Presentacion, ViaAdministracion, Laboratorio,
    EstadoMedicamento, Proveedor, Medicamento, MedicamentoHistorial
)

admin.site.register(FormaFarmaceutica)
admin.site.register(Presentacion)
admin.site.register(ViaAdministracion)
admin.site.register(Laboratorio)
admin.site.register(EstadoMedicamento)
admin.site.register(Proveedor)
admin.site.register(Medicamento)
admin.site.register(MedicamentoHistorial)