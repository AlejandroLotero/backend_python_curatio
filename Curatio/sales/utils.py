from decimal import Decimal


def construir_cuerpo_correo_venta(venta):
    """
    Texto plano con el detalle de la venta para notificación al cliente (RFADMIN20).
    """
    lineas = venta.lineas.select_related("medicamento").order_by("id")
    partes = [
        f"Hola {venta.cliente.nombre},",
        "",
        f"Se registró una venta en Curatio con factura N.º {venta.numero_factura}.",
        f"Fecha y hora: {venta.fecha_hora:%Y-%m-%d %H:%M}.",
        f"Estado: {venta.get_estado_display()}.",
        f"Tipo de pago: {venta.get_tipo_pago_display()}.",
        "",
        "Detalle de medicamentos:",
    ]
    for ln in lineas:
        sub = (ln.precio_unitario * ln.cantidad).quantize(Decimal("0.01"))
        partes.append(
            f"  - {ln.medicamento.nombre}: {ln.cantidad} x {ln.precio_unitario} = {sub}"
        )
    partes.extend(
        [
            "",
            f"Subtotal: {venta.subtotal}",
            f"IVA: {venta.iva}",
            f"Descuento: {venta.descuento}",
            f"Total: {venta.total}",
            "",
            "Gracias por confiar en Curatio.",
        ]
    )
    return "\n".join(partes)
