import re
from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings


# =========================
# CATÁLOGOS GESTIONABLES
# =========================

class FormaFarmaceutica(models.Model):
    id = models.AutoField(primary_key=True, db_column="id_forma")
    nombre = models.CharField(max_length=50, db_column="nombre_forma", unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "formas_farmaceuticas"
        verbose_name = "Forma farmacéutica"
        verbose_name_plural = "Formas farmacéuticas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Presentacion(models.Model):
    id = models.AutoField(primary_key=True, db_column="id_presentacion")
    nombre = models.CharField(max_length=60, db_column="nombre_presentacion")
    forma = models.ForeignKey(
        FormaFarmaceutica,
        on_delete=models.PROTECT,
        related_name="presentaciones",
        db_column="id_forma"
    )
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "presentacion"
        verbose_name = "Presentación"
        verbose_name_plural = "Presentaciones"
        ordering = ["nombre"]
        unique_together = ("forma", "nombre")

    def __str__(self):
        return f"{self.forma.nombre} - {self.nombre}"


class ViaAdministracion(models.Model):
    id = models.AutoField(primary_key=True, db_column="id_via_administracion")
    nombre = models.CharField(max_length=50, db_column="nombre_via", unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "via_administracion"
        verbose_name = "Vía de administración"
        verbose_name_plural = "Vías de administración"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Laboratorio(models.Model):
    id = models.AutoField(primary_key=True, db_column="id_laboratorio")
    nombre = models.CharField(max_length=120, db_column="nombre_laboratorio", unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "laboratorios"
        verbose_name = "Laboratorio"
        verbose_name_plural = "Laboratorios"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class EstadoMedicamento(models.Model):
    id = models.AutoField(primary_key=True, db_column="id_estado")
    nombre = models.CharField(max_length=30, db_column="nombre_estado", unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "estados_medicamentos"
        verbose_name = "Estado de medicamento"
        verbose_name_plural = "Estados de medicamentos"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


# =========================
# PROVEEDOR
# =========================

class Proveedor(models.Model):
    """
    El NIT queda como PK funcional por decisión de negocio y alineación con el dump.
    """

    ESTADOS = (
        ("Activo", "Activo"),
        ("Inactivo", "Inactivo"),
    )

    nit = models.CharField(primary_key=True, max_length=20, db_column="nit_proveedor")
    nombre = models.CharField(max_length=100)
    razon_social = models.CharField(max_length=100, blank=True, null=True)
    nombre_contacto = models.CharField(max_length=100, blank=True, null=True)
    telefono_contacto = models.CharField(max_length=20, blank=True, null=True)
    correo_contacto = models.EmailField(max_length=100, blank=True, null=True, db_column="correo")
    direccion = models.CharField(max_length=150, blank=True, null=True)
    ciudad = models.CharField(max_length=50, blank=True, null=True)
    estado = models.CharField(max_length=10, choices=ESTADOS, default="Activo")

    # Trazabilidad agregada por RQ
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_column="creado_por_id",
        null=True,
        blank=True,
        related_name="proveedores_creados"
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "proveedor"
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ["nombre"]

    def clean(self):
        if not self.nit or not re.match(r'^\d{8,10}-\d$', self.nit):
            raise ValidationError(
                "El NIT debe tener entre 8 y 10 dígitos, guión y dígito verificador. Ej: 12345678-9"
            )

    def __str__(self):
        return f"{self.nombre} ({self.nit})"


# =========================
# MEDICAMENTO
# =========================

class Medicamento(models.Model):
    """
    Modelo principal de medicamentos alineado al dump extendido según RQ.
    """

    id = models.AutoField(primary_key=True, db_column="id_medicamento")
    nombre = models.CharField(max_length=100)

    # Imagen comercial/pública del medicamento.
    # Se usa en:
    # - catálogo público
    # - ProductShowPage
    # - cards del home
    # - resultados del buscador
    #
    # Es opcional para no romper medicamentos ya existentes.
    imagen = models.ImageField(
        upload_to="medicamentos/",
        null=True,
        blank=True
    )

    forma = models.ForeignKey(
        FormaFarmaceutica,
        on_delete=models.PROTECT,
        db_column="id_forma"
    )

    presentacion = models.ForeignKey(
        Presentacion,
        on_delete=models.PROTECT,
        db_column="id_presentacion"
    )

    concentracion = models.CharField(max_length=50, blank=True, null=True)

    via_administracion = models.ForeignKey(
        ViaAdministracion,
        on_delete=models.PROTECT,
        db_column="id_via_administracion"
    )

    # Campo heredado del dump. Se conserva por compatibilidad.
    laboratorio_texto = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_column="laboratorio"
    )

    laboratorio = models.ForeignKey(
        Laboratorio,
        on_delete=models.PROTECT,
        db_column="id_laboratorio",
        related_name="medicamentos_rel"
    )

    lote = models.CharField(max_length=50, blank=True, null=True)
    fecha_fabricacion = models.DateField(blank=True, null=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)

    stock = models.PositiveSmallIntegerField()
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)

    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        db_column="nit_proveedor",
        to_field="nit"
    )

    requiere_formula = models.BooleanField(default=False)
    descripcion = models.TextField(blank=True, null=True)

    estado = models.ForeignKey(
        EstadoMedicamento,
        on_delete=models.PROTECT,
        db_column="id_estado"
    )

    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="medicamentos_a_cargo",
        db_column="responsable_id",
        limit_choices_to={"rol": "Farmaceuta"},
        null=True,
        blank=True
    )

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_column="creado_por_id",
        related_name="medicamentos_creados"
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "medicamentos"
        verbose_name = "Medicamento"
        verbose_name_plural = "Medicamentos"
        ordering = ["nombre"]

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

        # Stock: 0..999
        if self.stock is None:
            raise ValidationError("El stock es obligatorio.")
        if self.stock < 0 or self.stock > 999:
            raise ValidationError("El stock debe estar entre 0 y 999.")

        # Precios no negativos
        if self.precio_compra is None or self.precio_compra < 0:
            raise ValidationError("El precio de compra no puede ser negativo.")
        if self.precio_venta is None or self.precio_venta < 0:
            raise ValidationError("El precio de venta no puede ser negativo.")

        # Validación opcional de imagen
        if self.imagen:
            if self.imagen.size > 3 * 1024 * 1024:
                raise ValidationError("La imagen del medicamento no puede superar 3MB.")

            if not self.imagen.name.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                raise ValidationError("Formato de imagen no permitido para el medicamento.")

        # Fechas
        if self.fecha_fabricacion and self.fecha_vencimiento:
            if self.fecha_vencimiento <= self.fecha_fabricacion:
                raise ValidationError("La fecha de vencimiento debe ser posterior a la fecha de fabricación.")

        # Presentación debe pertenecer a la forma seleccionada
        if self.presentacion_id and self.forma_id:
            if self.presentacion.forma_id != self.forma_id:
                raise ValidationError("La presentación seleccionada no corresponde a la forma farmacéutica.")

    @property
    def puede_venderse(self):
        """
        Regla de negocio:
        solo medicamento en estado Activo puede venderse.
        """
        return self.estado and self.estado.nombre == "Activo"

    def __str__(self):
        return f"{self.nombre} ({self.presentacion})"


# =========================
# HISTORIAL DE MEDICAMENTOS
# =========================

class MedicamentoHistorial(models.Model):
    id = models.AutoField(primary_key=True, db_column="id_historial")

    ACCIONES = (
        ("CREADO", "CREADO"),
        ("ACTUALIZADO", "ACTUALIZADO"),
        ("DESHABILITADO", "DESHABILITADO"),
        ("CAMBIO_ESTADO", "CAMBIO_ESTADO"),
    )

    medicamento = models.ForeignKey(
        Medicamento,
        on_delete=models.CASCADE,
        related_name="historial",
        db_column="id_medicamento"
    )
    accion = models.CharField(max_length=20, choices=ACCIONES)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_column="usuario_id"
    )
    fecha = models.DateTimeField(auto_now_add=True)
    detalle = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "medicamento_historial"
        verbose_name = "Historial de medicamento"
        verbose_name_plural = "Historial de medicamentos"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.medicamento_id} - {self.accion} - {self.fecha}"


# =========================
# HISTORIAL DE PROVEEDORES
# =========================

class ProveedorHistorial(models.Model):
    id = models.AutoField(primary_key=True, db_column="id_historial")

    ACCIONES = (
        ("CREADO", "CREADO"),
        ("ACTUALIZADO", "ACTUALIZADO"),
        ("CAMBIO_ESTADO", "CAMBIO_ESTADO"),
    )

    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.CASCADE,
        related_name="historial",
        db_column="nit_proveedor",
        to_field="nit"
    )

    accion = models.CharField(max_length=20, choices=ACCIONES)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_column="usuario_id"
    )

    fecha = models.DateTimeField(auto_now_add=True)
    detalle = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "proveedor_historial"
        verbose_name = "Historial de proveedor"
        verbose_name_plural = "Historial de proveedores"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.proveedor.nombre} - {self.accion}"
