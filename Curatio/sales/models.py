from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Venta(models.Model):
    """
    RFADMIN20 — Venta de medicamentos (Admin o Farmaceuta → Cliente).
    Stock solo se descuenta al pasar a Completada tras doble confirmación de pago.
    """

    ESTADOS = (
        ("Pendiente", "Pendiente de confirmación"),
        ("Completada", "Completada"),
        ("Anulada", "Anulada"),
    )

    TIPOS_PAGO = (
        ("Efectivo", "Efectivo"),
        ("Tarjeta débito", "Tarjeta débito"),
        ("Tarjeta crédito", "Tarjeta crédito"),
        ("Transferencia", "Transferencia"),
    )

    numero_factura = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Número de factura",
    )
    fecha_hora = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha y hora de la venta",
    )

    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ventas_como_cliente",
        limit_choices_to={"rol": "Cliente"},
        verbose_name="Cliente",
    )

    # Quien registra la venta (Administrador o Farmaceuta, según RQ).
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ventas_realizadas",
        limit_choices_to={"rol__in": ["Administrador", "Farmaceuta"]},
        verbose_name="Usuario que realiza la venta",
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    iva = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    descuento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )

    tipo_pago = models.CharField(
        max_length=30,
        choices=TIPOS_PAGO,
        verbose_name="Tipo de pago",
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="Pendiente",
        verbose_name="Estado de la venta",
    )

    confirmacion_vendedor_en = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Confirmación de pago (vendedor)",
    )
    confirmacion_vendedor_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    confirmacion_cliente_en = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Confirmación de pago (cliente)",
    )
    confirmacion_cliente_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ["-fecha_hora"]

    def __str__(self):
        return f"{self.numero_factura} — {self.get_estado_display()}"

    def clean(self):
        if self.cliente_id and self.vendedor_id and self.cliente_id == self.vendedor_id:
            raise ValidationError("La venta debe involucrar al cliente y al usuario que realiza la venta como personas distintas.")

        esperado = self.subtotal + self.iva - self.descuento
        if self.total != esperado:
            raise ValidationError(
                {"total": f"El total debe ser subtotal + IVA - descuento ({esperado})."}
            )

    def aplicar_descuento_stock_si_completa(self):
        """
        Si hay doble confirmación y sigue Pendiente, valida stock, descuenta y marca Completada.
        Debe llamarse dentro de transaction.atomic().
        """
        if self.estado != "Pendiente":
            return False

        if not (
            self.confirmacion_vendedor_en
            and self.confirmacion_cliente_en
            and self.confirmacion_vendedor_por_id
            and self.confirmacion_cliente_por_id
        ):
            return False

        from products.models import Medicamento

        lineas = list(self.lineas.select_related("medicamento", "medicamento__estado"))

        for linea in lineas:
            med = Medicamento.objects.select_for_update().get(pk=linea.medicamento_id)
            if not med.puede_venderse:
                raise ValidationError(
                    f"El medicamento «{med}» no está disponible para la venta (estado distinto de Activo)."
                )
            if linea.cantidad > med.stock:
                raise ValidationError(
                    f"Stock insuficiente para «{med}»: solicitado {linea.cantidad}, disponible {med.stock}."
                )

        for linea in lineas:
            med = Medicamento.objects.select_for_update().get(pk=linea.medicamento_id)
            med.stock -= linea.cantidad
            med.save(update_fields=["stock", "actualizado_en"])

        self.estado = "Completada"
        self.save(update_fields=["estado"])
        return True


class VentaLinea(models.Model):
    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name="lineas",
    )
    medicamento = models.ForeignKey(
        "products.Medicamento",
        on_delete=models.PROTECT,
        related_name="lineas_venta",
    )
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Precio unitario (venta)",
    )

    class Meta:
        verbose_name = "Línea de venta"
        verbose_name_plural = "Líneas de venta"

    def subtotal_linea(self):
        return (self.precio_unitario * self.cantidad).quantize(Decimal("0.01"))

    def clean(self):
        med = self.medicamento
        if med and not med.puede_venderse:
            raise ValidationError("Solo se pueden vender medicamentos en estado Activo.")
        if med and self.cantidad and self.cantidad > med.stock:
            raise ValidationError(
                f"Cantidad ({self.cantidad}) supera el stock disponible ({med.stock})."
            )


class VentaHistorial(models.Model):
    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name="historial",
    )
    accion = models.CharField(max_length=50)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )
    detalle = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Historial de venta"
        verbose_name_plural = "Historial de ventas"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.venta_id} — {self.accion}"
