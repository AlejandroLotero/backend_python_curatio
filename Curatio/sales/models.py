# from decimal import Decimal

# from django.conf import settings
# from django.core.exceptions import ValidationError
# from django.core.validators import MinValueValidator
# from django.db import models

# from django.core.exceptions import ValidationError
# from django.db import transaction

# class Venta(models.Model):
#     """
#     RFADMIN20 — Venta de medicamentos (Admin o Farmaceuta → Cliente).
#     Stock solo se descuenta al pasar a Completada tras doble confirmación de pago.
#     """

#     ESTADOS = (
#         ("Pendiente", "Pendiente de confirmación"),
#         ("Completada", "Completada"),
#         ("Anulada", "Anulada"),
#     )

#     TIPOS_PAGO = (
#         ("Efectivo", "Efectivo"),
#         ("Tarjeta débito", "Tarjeta débito"),
#         ("Tarjeta crédito", "Tarjeta crédito"),
#         ("Transferencia", "Transferencia"),
#     )

#     # =========================
#     # NUEVO: MÉTODO DE ENTREGA
#     # =========================
#     METODOS_ENTREGA = (
#         ("delivery", "Domicilio"),
#         ("pickup", "Recogida en tienda"),
#     )

#     numero_factura = models.CharField(
#         max_length=50,
#         unique=True,
#         verbose_name="Número de factura",
#     )
#     fecha_hora = models.DateTimeField(
#         auto_now_add=True,
#         verbose_name="Fecha y hora de la venta",
#     )

#     cliente = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.PROTECT,
#         related_name="ventas_como_cliente",
#         limit_choices_to={"rol": "Cliente"},
#         verbose_name="Cliente",
#     )

#     vendedor = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.PROTECT,
#         related_name="ventas_realizadas",
#         limit_choices_to={"rol__in": ["Administrador", "Farmaceuta"]},
#         verbose_name="Usuario que realiza la venta",
#     )

#     subtotal = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         validators=[MinValueValidator(Decimal("0"))],
#     )
#     iva = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         validators=[MinValueValidator(Decimal("0"))],
#     )
#     descuento = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         default=Decimal("0"),
#         validators=[MinValueValidator(Decimal("0"))],
#     )
#     total = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         validators=[MinValueValidator(Decimal("0"))],
#     )

#     tipo_pago = models.CharField(
#         max_length=30,
#         choices=TIPOS_PAGO,
#         verbose_name="Tipo de pago",
#     )

#     estado = models.CharField(
#         max_length=20,
#         choices=ESTADOS,
#         default="Pendiente",
#         verbose_name="Estado de la venta",
#     )

#     # =========================
#     # NUEVO: DATOS DE ENTREGA
#     # =========================
#     metodo_entrega = models.CharField(
#         max_length=20,
#         choices=METODOS_ENTREGA,
#         null=True,
#         blank=True,
#         verbose_name="Método de entrega",
#     )

#     direccion_entrega = models.CharField(
#         max_length=255,
#         blank=True,
#         default="",
#         verbose_name="Dirección de entrega",
#     )
#     ciudad_entrega = models.CharField(
#         max_length=120,
#         blank=True,
#         default="",
#         verbose_name="Ciudad de entrega",
#     )
#     telefono_entrega = models.CharField(
#         max_length=30,
#         blank=True,
#         default="",
#         verbose_name="Teléfono de entrega",
#     )

#     punto_retiro = models.CharField(
#         max_length=150,
#         blank=True,
#         default="",
#         verbose_name="Punto de retiro",
#     )
#     nombre_contacto_retiro = models.CharField(
#         max_length=150,
#         blank=True,
#         default="",
#         verbose_name="Nombre de contacto para retiro",
#     )
#     telefono_contacto_retiro = models.CharField(
#         max_length=30,
#         blank=True,
#         default="",
#         verbose_name="Teléfono de contacto para retiro",
#     )

#     confirmacion_vendedor_en = models.DateTimeField(
#         null=True,
#         blank=True,
#         verbose_name="Confirmación de pago (vendedor)",
#     )
#     confirmacion_vendedor_por = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         null=True,
#         blank=True,
#         on_delete=models.SET_NULL,
#         related_name="+",
#     )

#     confirmacion_cliente_en = models.DateTimeField(
#         null=True,
#         blank=True,
#         verbose_name="Confirmación de pago (cliente)",
#     )
#     confirmacion_cliente_por = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         null=True,
#         blank=True,
#         on_delete=models.SET_NULL,
#         related_name="+",
#     )

#     def __str__(self):
#         return f"{self.numero_factura} - {self.cliente}"

#     def clean(self):
#         """
#         Validaciones de coherencia adicionales para el método de entrega.
#         """
#         super().clean()

#         if self.metodo_entrega == "delivery":
#             if not self.direccion_entrega:
#                 raise ValidationError(
#                     {"direccion_entrega": "La dirección de entrega es obligatoria para domicilio."}
#                 )

#         if self.metodo_entrega == "pickup":
#             if not self.punto_retiro:
#                 raise ValidationError(
#                     {"punto_retiro": "El punto de retiro es obligatorio para recogida en tienda."}
#                 )

# class VentaLinea(models.Model):
#     venta = models.ForeignKey(
#         Venta,
#         on_delete=models.CASCADE,
#         related_name="lineas",
#     )
#     medicamento = models.ForeignKey(
#         "products.Medicamento",
#         on_delete=models.PROTECT,
#         related_name="lineas_venta",
#     )
#     cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
#     precio_unitario = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         validators=[MinValueValidator(Decimal("0"))],
#         verbose_name="Precio unitario (venta)",
#     )

#     class Meta:
#         verbose_name = "Línea de venta"
#         verbose_name_plural = "Líneas de venta"

#     def subtotal_linea(self):
#         return (self.precio_unitario * self.cantidad).quantize(Decimal("0.01"))

#     def clean(self):
#         med = self.medicamento
#         if med and not med.puede_venderse:
#             raise ValidationError("Solo se pueden vender medicamentos en estado Activo.")
#         if med and self.cantidad and self.cantidad > med.stock:
#             raise ValidationError(
#                 f"Cantidad ({self.cantidad}) supera el stock disponible ({med.stock})."
#             )


# class VentaHistorial(models.Model):
#     venta = models.ForeignKey(
#         Venta,
#         on_delete=models.CASCADE,
#         related_name="historial",
#     )
#     accion = models.CharField(max_length=50)
#     usuario = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.PROTECT,
#     )
#     detalle = models.TextField(blank=True)
#     fecha = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         verbose_name = "Historial de venta"
#         verbose_name_plural = "Historial de ventas"
#         ordering = ["-fecha"]

#     def __str__(self):
#         return f"{self.venta_id} — {self.accion}"

# class NotificacionVenta(models.Model):
#     """
#     Notificación interna del módulo de ventas / carritos.

#     Se usa para:
#     - compras web pendientes de aprobación
#     - cancelaciones
#     - cambios operativos relevantes

#     En esta fase se mostrará principalmente a:
#     - Administrador
#     - Farmaceuta
#     """

#     TIPOS = (
#         ("VENTA_WEB_PENDIENTE", "Venta web pendiente"),
#         ("VENTA_APROBADA", "Venta aprobada"),
#         ("VENTA_ANULADA", "Venta anulada"),
#         ("CARRITO_ACTIVO", "Carrito activo"),
#         ("GENERAL", "General"),
#     )

#     usuario = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name="notificaciones_ventas",
#         verbose_name="Usuario destinatario",
#     )
#     venta = models.ForeignKey(
#         "Venta",
#         null=True,
#         blank=True,
#         on_delete=models.CASCADE,
#         related_name="notificaciones",
#         verbose_name="Venta asociada",
#     )
#     tipo = models.CharField(
#         max_length=40,
#         choices=TIPOS,
#         default="GENERAL",
#         verbose_name="Tipo de notificación",
#     )
#     titulo = models.CharField(
#         max_length=150,
#         verbose_name="Título",
#     )
#     mensaje = models.TextField(
#         verbose_name="Mensaje",
#     )
#     leida = models.BooleanField(
#         default=False,
#         verbose_name="Leída",
#     )
#     creada_en = models.DateTimeField(
#         auto_now_add=True,
#         verbose_name="Fecha de creación",
#     )
#     leida_en = models.DateTimeField(
#         null=True,
#         blank=True,
#         verbose_name="Fecha de lectura",
#     )

#     class Meta:
#         ordering = ("-creada_en",)

#     def __str__(self):
#         return f"{self.usuario} - {self.titulo}"
    


# def aplicar_descuento_stock_si_completa(self):
#     """
#     Completa la venta cuando existen ambas confirmaciones
#     y descuenta el stock.

#     Retorna True si la venta fue completada.
#     Retorna False si todavía no cumple condiciones o ya estaba cerrada.
#     """
#     if self.estado != "Pendiente":
#         return False

#     if not self.confirmacion_cliente_en or not self.confirmacion_vendedor_en:
#         return False

#     lineas = self.lineas.select_related("medicamento").all()

#     # Validación previa de stock
#     for linea in lineas:
#         medicamento = linea.medicamento

#         if linea.cantidad > medicamento.stock:
#             raise ValidationError(
#                 f"Stock insuficiente para '{medicamento.nombre}'. Disponible: {medicamento.stock}."
#             )

#     # Descuento real de stock
#     for linea in lineas:
#         medicamento = linea.medicamento
#         medicamento.stock = medicamento.stock - linea.cantidad
#         medicamento.save(update_fields=["stock"])

#     # Cambio de estado de la venta
#     self.estado = "Completada"
#     self.save(update_fields=["estado"])

#     return True

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction


class Venta(models.Model):
    """
    RFADMIN20 — Venta de medicamentos (Admin o Farmaceuta → Cliente).

    Reglas principales:
    - El stock solo se descuenta cuando la venta pasa a Completada.
    - Para completarse, la venta debe tener confirmación del cliente
      y confirmación del vendedor / personal interno.
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

    # =========================
    # MÉTODO DE ENTREGA
    # =========================
    METODOS_ENTREGA = (
        ("delivery", "Domicilio"),
        ("pickup", "Recogida en tienda"),
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

    # =========================
    # DATOS DE ENTREGA
    # =========================
    metodo_entrega = models.CharField(
        max_length=20,
        choices=METODOS_ENTREGA,
        null=True,
        blank=True,
        verbose_name="Método de entrega",
    )

    direccion_entrega = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Dirección de entrega",
    )
    ciudad_entrega = models.CharField(
        max_length=120,
        blank=True,
        default="",
        verbose_name="Ciudad de entrega",
    )
    telefono_entrega = models.CharField(
        max_length=30,
        blank=True,
        default="",
        verbose_name="Teléfono de entrega",
    )

    punto_retiro = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="Punto de retiro",
    )
    nombre_contacto_retiro = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="Nombre de contacto para retiro",
    )
    telefono_contacto_retiro = models.CharField(
        max_length=30,
        blank=True,
        default="",
        verbose_name="Teléfono de contacto para retiro",
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
        ordering = ("-fecha_hora",)

    def __str__(self):
        return f"{self.numero_factura} - {self.cliente}"

    def clean(self):
        """
        Validaciones de coherencia adicionales para el método de entrega.
        """
        super().clean()

        if self.metodo_entrega == "delivery":
            if not self.direccion_entrega:
                raise ValidationError(
                    {"direccion_entrega": "La dirección de entrega es obligatoria para domicilio."}
                )

        if self.metodo_entrega == "pickup":
            if not self.punto_retiro:
                raise ValidationError(
                    {"punto_retiro": "El punto de retiro es obligatorio para recogida en tienda."}
                )

    def aplicar_descuento_stock_si_completa(self):
        """
        Completa la venta cuando existen ambas confirmaciones
        y descuenta el stock.

        Retorna True si la venta fue completada.
        Retorna False si todavía no cumple condiciones o si la venta
        ya no está en estado Pendiente.
        """
        if self.estado != "Pendiente":
            return False

        if not self.confirmacion_cliente_en or not self.confirmacion_vendedor_en:
            return False

        lineas = self.lineas.select_related("medicamento").all()

        # Validación previa de stock antes de descontar.
        for linea in lineas:
            medicamento = linea.medicamento

            if linea.cantidad > medicamento.stock:
                raise ValidationError(
                    f"Stock insuficiente para '{medicamento.nombre}'. Disponible: {medicamento.stock}."
                )

        # Descuento real de stock.
        for linea in lineas:
            medicamento = linea.medicamento
            medicamento.stock = medicamento.stock - linea.cantidad
            medicamento.save(update_fields=["stock"])

        # Cambio de estado de la venta.
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


class NotificacionVenta(models.Model):
    """
    Notificación interna del módulo de ventas / carritos.
    """

    TIPOS = (
        ("VENTA_WEB_PENDIENTE", "Venta web pendiente"),
        ("VENTA_APROBADA", "Venta aprobada"),
        ("VENTA_ANULADA", "Venta anulada"),
        ("CARRITO_ACTIVO", "Carrito activo"),
        ("GENERAL", "General"),
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notificaciones_ventas",
        verbose_name="Usuario destinatario",
    )
    venta = models.ForeignKey(
        "Venta",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="notificaciones",
        verbose_name="Venta asociada",
    )
    tipo = models.CharField(
        max_length=40,
        choices=TIPOS,
        default="GENERAL",
        verbose_name="Tipo de notificación",
    )
    titulo = models.CharField(
        max_length=150,
        verbose_name="Título",
    )
    mensaje = models.TextField(
        verbose_name="Mensaje",
    )
    leida = models.BooleanField(
        default=False,
        verbose_name="Leída",
    )
    creada_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )
    leida_en = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de lectura",
    )

    class Meta:
        ordering = ("-creada_en",)

    def __str__(self):
        return f"{self.usuario} - {self.titulo}"