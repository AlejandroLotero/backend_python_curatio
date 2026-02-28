from django.db import models

# Create your models here.

import re
from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings

# --- Catálogos gestionables (reglas 3,4,5) ---

class FormaFarmaceutica(models.Model):
    nombre = models.CharField(max_length=30, unique=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Presentacion(models.Model):
    forma = models.ForeignKey(FormaFarmaceutica, on_delete=models.PROTECT, related_name="presentaciones")
    nombre = models.CharField(max_length=60)
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ("forma", "nombre")

    def __str__(self):
        return f"{self.forma.nombre} - {self.nombre}"


class ViaAdministracion(models.Model):
    nombre = models.CharField(max_length=30, unique=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Laboratorio(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class EstadoMedicamento(models.Model):
    nombre = models.CharField(max_length=20, unique=True)  # Activo, Vencido, Agotado, Suspendido
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Proveedor(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


# --- Entidad principal ---

class Medicamento(models.Model):
    # id autoincrementable (Django) = requisito 1

    nombre = models.CharField(max_length=120)
    forma = models.ForeignKey(FormaFarmaceutica, on_delete=models.PROTECT)
    presentacion = models.ForeignKey(Presentacion, on_delete=models.PROTECT)
    concentracion = models.CharField(max_length=120)

    via_administracion = models.ForeignKey(ViaAdministracion, on_delete=models.PROTECT)
    laboratorio = models.ForeignKey(Laboratorio, on_delete=models.PROTECT)

    lote = models.CharField(max_length=60)
    fecha_fabricacion = models.DateField()
    fecha_vencimiento = models.DateField()

    stock = models.PositiveSmallIntegerField()  # no negativos, max práctico
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)

    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT)

    requiere_formula = models.BooleanField(default=False)  # oculto en el form (backend)

    descripcion = models.TextField()

    estado = models.ForeignKey(EstadoMedicamento, on_delete=models.PROTECT)

    # Regla 6: seleccionar Farmaceuta creado (accounts.User con rol Farmaceuta)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="medicamentos_a_cargo",
        limit_choices_to={"rol": "Farmaceuta"},
        null=True,
        blank=True
    )

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="medicamentos_creados"
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Nombre: solo letras y espacios, con tildes/ñ, sin números ni especiales
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', (self.nombre or "").strip()):
            raise ValidationError("El nombre solo puede contener letras y espacios (sin números ni caracteres especiales).")

        # Concentración: texto libre, mínimo 1 caracter no vacío
        if not (self.concentracion or "").strip():
            raise ValidationError("La concentración es obligatoria.")

        # Lote: mínimo 1 caracter no vacío
        if not (self.lote or "").strip():
            raise ValidationError("El lote es obligatorio.")

        # Stock: max 3 caracteres => 0..999
        if self.stock is None:
            raise ValidationError("El stock es obligatorio.")
        if self.stock < 0 or self.stock > 999:
            raise ValidationError("El stock debe estar entre 0 y 999.")

        # Precios no negativos
        if self.precio_compra is None or self.precio_compra < 0:
            raise ValidationError("El precio de compra no puede ser negativo.")
        if self.precio_venta is None or self.precio_venta < 0:
            raise ValidationError("El precio de venta no puede ser negativo.")

        # Fechas: vencimiento > fabricación
        if self.fecha_fabricacion and self.fecha_vencimiento:
            if self.fecha_vencimiento <= self.fecha_fabricacion:
                raise ValidationError("La fecha de vencimiento debe ser posterior a la fecha de fabricación.")

        # Presentación debe pertenecer a la forma seleccionada
        if self.presentacion_id and self.forma_id:
            if self.presentacion.forma_id != self.forma_id:
                raise ValidationError("La presentación seleccionada no corresponde a la forma farmacéutica.")

    def __str__(self):
        return f"{self.nombre} ({self.presentacion})"


class MedicamentoHistorial(models.Model):
    ACCIONES = (
        ("CREADO", "CREADO"),
        ("ACTUALIZADO", "ACTUALIZADO"),
        ("DESHABILITADO", "DESHABILITADO"),
    )
    medicamento = models.ForeignKey(Medicamento, on_delete=models.CASCADE, related_name="historial")
    accion = models.CharField(max_length=20, choices=ACCIONES)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    detalle = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.medicamento_id} - {self.accion} - {self.fecha}"