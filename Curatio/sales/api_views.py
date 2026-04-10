from decimal import Decimal, InvalidOperation
from io import BytesIO
import traceback

from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from openpyxl import Workbook
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.pdfencrypt import StandardEncryption
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import User
from products.models import Medicamento

from .models import Venta, VentaLinea, VentaHistorial, NotificacionVenta
from .utils import construir_cuerpo_correo_venta


# =========================
# HELPERS DE PERMISOS
# =========================

def _usuario_puede_vender(user):
    """
    Valida si el usuario autenticado puede realizar operaciones
    administrativas sobre ventas.

    Roles permitidos:
    - Administrador
    - Farmaceuta
    """
    return getattr(user, "is_authenticated", False) and getattr(user, "rol", None) in (
        "Administrador",
        "Farmaceuta",
    )


def _forbidden_sales_response():
    """
    Respuesta estándar cuando un usuario no tiene permisos
    para gestionar ventas.
    """
    return Response(
        {
            "error": {
                "code": "FORBIDDEN",
                "message": "No tienes permisos para realizar esta acción.",
            }
        },
        status=status.HTTP_403_FORBIDDEN,
    )


def _puede_ver_venta(user, venta):
    """
    Reglas de visibilidad por rol:

    - Administrador: puede ver todas las ventas.
    - Farmaceuta: solo las ventas registradas por él.
    - Cliente: solo las ventas donde él participa como cliente.
    """
    rol = getattr(user, "rol", None)

    if rol == "Administrador":
        return True

    if rol == "Farmaceuta" and venta.vendedor_id == user.id:
        return True

    if rol == "Cliente" and venta.cliente_id == user.id:
        return True

    return False


# =========================
# HELPERS DE VALIDACIÓN
# =========================

def _parse_decimal(value, field_name, required=True):
    """
    Convierte un valor recibido desde la API a Decimal con dos decimales.

    Reglas:
    - Si el campo es obligatorio, no puede venir vacío.
    - No se permiten valores negativos.
    """
    raw = str(value).strip() if value is not None else ""

    if raw == "":
        if required:
            raise ValueError({field_name: ["Este campo es obligatorio."]})
        return Decimal("0.00")

    try:
        number = Decimal(raw).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError({field_name: ["Ingrese un número decimal válido."]})

    if number < 0:
        raise ValueError({field_name: ["No se permiten valores negativos."]})

    return number


def _validate_payment_type(tipo_pago):
    """
    Valida que el tipo de pago exista dentro de los choices del modelo.
    """
    valid_types = {choice[0] for choice in Venta.TIPOS_PAGO}

    if tipo_pago not in valid_types:
        raise ValueError({"payment_type": ["Tipo de pago no válido."]})

    return tipo_pago


def _validate_sale_status(estado):
    """
    Valida que el estado de la venta exista dentro de los choices del modelo.
    """
    valid_statuses = {choice[0] for choice in Venta.ESTADOS}

    if estado not in valid_statuses:
        raise ValueError({"status": ["Estado de la venta no válido."]})

    return estado


def _validate_sale_lines(lines):
    """
    Valida y normaliza las líneas de venta recibidas desde la SPA.

    Estructura esperada:
    [
        {
            "medication_id": 1,
            "quantity": 2
        }
    ]

    Reglas:
    - Debe existir al menos una línea.
    - El medicamento debe existir.
    - Debe poder venderse.
    - La cantidad debe ser positiva.
    - La cantidad no puede superar el stock disponible.
    """
    if not isinstance(lines, list) or not lines:
        raise ValueError({"lines": ["Debe incluir al menos una línea de medicamentos."]})

    normalized_lines = []

    for index, item in enumerate(lines):
        if not isinstance(item, dict):
            raise ValueError({"lines": [f"La línea {index + 1} es inválida."]})

        medication_id = item.get("medication_id")
        quantity = item.get("quantity")

        if not medication_id:
            raise ValueError({"lines": [f"La línea {index + 1}: medication_id es obligatorio."]})

        if quantity in (None, ""):
            raise ValueError({"lines": [f"La línea {index + 1}: quantity es obligatorio."]})

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            raise ValueError({"lines": [f"La línea {index + 1}: la cantidad debe ser un entero."]})

        if quantity <= 0:
            raise ValueError({"lines": [f"La línea {index + 1}: la cantidad debe ser mayor que cero."]})

        medicamento = Medicamento.objects.select_related("estado").filter(pk=medication_id).first()

        if not medicamento:
            raise ValueError({"lines": [f"La línea {index + 1}: el medicamento no existe."]})

        if not medicamento.puede_venderse:
            raise ValueError(
                {
                    "lines": [
                        f"La línea {index + 1}: el medicamento '{medicamento.nombre}' no está disponible para la venta."
                    ]
                }
            )

        if quantity > medicamento.stock:
            raise ValueError(
                {
                    "lines": [
                        (
                            f"La línea {index + 1}: stock insuficiente para "
                            f"'{medicamento.nombre}'. Disponible: {medicamento.stock}."
                        )
                    ]
                }
            )

        normalized_lines.append(
            {
                "medicamento": medicamento,
                "cantidad": quantity,
                "precio_unitario": medicamento.precio_venta.quantize(Decimal("0.01")),
            }
        )

    return normalized_lines


def _expected_subtotal_from_lines(lines):
    """
    Calcula el subtotal esperado a partir de las líneas normalizadas.
    """
    subtotal = Decimal("0.00")

    for line in lines:
        subtotal += (line["precio_unitario"] * line["cantidad"]).quantize(Decimal("0.01"))

    return subtotal.quantize(Decimal("0.01"))


def _validar_datos_entrega_checkout(request_data):
    """
    Valida los datos de entrega enviados desde el checkout web.
    """
    delivery_method = (request_data.get("delivery_method") or "").strip()

    if delivery_method not in ("delivery", "pickup"):
        raise ValueError(
            {"delivery_method": ["Debe seleccionar domicilio o recogida en tienda."]}
        )

    delivery_payload = {
        "delivery_method": delivery_method,
        "delivery_address": (request_data.get("delivery_address") or "").strip(),
        "delivery_city": (request_data.get("delivery_city") or "").strip(),
        "delivery_phone": (request_data.get("delivery_phone") or "").strip(),
        "pickup_point": (request_data.get("pickup_point") or "").strip(),
        "pickup_contact_name": (request_data.get("pickup_contact_name") or "").strip(),
        "pickup_contact_phone": (request_data.get("pickup_contact_phone") or "").strip(),
    }

    if delivery_method == "delivery":
        if not delivery_payload["delivery_address"]:
            raise ValueError({"delivery_address": ["La dirección es obligatoria."]})
        if not delivery_payload["delivery_city"]:
            raise ValueError({"delivery_city": ["La ciudad es obligatoria."]})
        if not delivery_payload["delivery_phone"]:
            raise ValueError({"delivery_phone": ["El teléfono es obligatorio."]})

    if delivery_method == "pickup":
        if not delivery_payload["pickup_point"]:
            raise ValueError({"pickup_point": ["El punto de retiro es obligatorio."]})
        if not delivery_payload["pickup_contact_name"]:
            raise ValueError({"pickup_contact_name": ["El nombre de contacto es obligatorio."]})
        if not delivery_payload["pickup_contact_phone"]:
            raise ValueError({"pickup_contact_phone": ["El teléfono de contacto es obligatorio."]})

    return delivery_payload


# =========================
# HELPERS DE NOTIFICACIONES
# =========================

def _usuarios_internos_notificables():
    """
    Retorna usuarios internos que deben recibir notificaciones operativas.

    En esta fase:
    - Administrador
    - Farmaceuta
    """
    return User.objects.filter(
        rol__in=["Administrador", "Farmaceuta"],
        estado=True,
        is_active=True,
    ).order_by("id")


def _serialize_notification_row(item):
    """
    Serialización estándar de notificación interna.
    """
    return {
        "id": item.id,
        "type": item.tipo,
        "title": item.titulo,
        "message": item.mensaje,
        "is_read": item.leida,
        "created_at": timezone.localtime(item.creada_en).strftime("%Y-%m-%d %H:%M:%S"),
        "read_at": (
            timezone.localtime(item.leida_en).strftime("%Y-%m-%d %H:%M:%S")
            if item.leida_en else None
        ),
        "sale": (
            {
                "id": item.venta.id,
                "invoice_number": item.venta.numero_factura,
                "status": item.venta.estado,
            }
            if item.venta_id else None
        ),
    }


def _crear_notificacion_interna_para_todos(venta, tipo, titulo, mensaje):
    """
    Crea la misma notificación para todo el personal interno autorizado.
    """
    notificaciones = []

    for usuario in _usuarios_internos_notificables():
        notificaciones.append(
            NotificacionVenta(
                usuario=usuario,
                venta=venta,
                tipo=tipo,
                titulo=titulo,
                mensaje=mensaje,
            )
        )

    if notificaciones:
        NotificacionVenta.objects.bulk_create(notificaciones)


def _crear_notificacion_para_usuario(usuario, venta, tipo, titulo, mensaje):
    """
    Crea una notificación individual.
    """
    NotificacionVenta.objects.create(
        usuario=usuario,
        venta=venta,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
    )


def _mark_pending_sale_notifications_as_read(sale):
    """
    Marca como leídas las notificaciones internas pendientes asociadas a la venta.

    Se usa cuando una compra web deja de estar pendiente porque ya fue
    aprobada por Administrador o Farmaceuta.
    """
    NotificacionVenta.objects.filter(
        venta=sale,
        tipo="VENTA_WEB_PENDIENTE",
        leida=False,
    ).update(
        leida=True,
        leida_en=timezone.now(),
    )


def _construir_mensaje_cliente_aprobacion(venta):
    """
    Construye el mensaje para el cliente una vez la compra es aprobada manualmente.

    Reglas:
    - domicilio -> pedido será despachado
    - recogida -> disponible para retiro después de 45 minutos
    """
    if venta.metodo_entrega == "delivery":
        return (
            f"Hola {venta.cliente.nombre},\n\n"
            f"Tu compra con factura {venta.numero_factura} fue aprobada correctamente.\n"
            "Tu pedido será despachado a la dirección registrada.\n\n"
            "Gracias por confiar en Curatio."
        )

    return (
        f"Hola {venta.cliente.nombre},\n\n"
        f"Tu compra con factura {venta.numero_factura} fue aprobada correctamente.\n"
        "Tu pedido estará disponible para recogida en tienda después de 45 minutos.\n\n"
        "Gracias por confiar en Curatio."
    )


# =========================
# HELPERS DE SERIALIZACIÓN
# =========================

def _serialize_sale_line(item):
    """
    Serialización estándar de una línea de venta.
    """
    return {
        "id": item.id,
        "medication": {
            "id": item.medicamento.id,
            "name": item.medicamento.nombre,
        },
        "quantity": item.cantidad,
        "unit_price": str(item.precio_unitario),
        "line_subtotal": str(item.subtotal_linea()),
    }


def _serialize_sale_row(venta):
    """
    Serialización resumida para listados de ventas.
    """
    return {
        "id": venta.id,
        "invoice_number": venta.numero_factura,
        "sale_datetime": timezone.localtime(venta.fecha_hora).strftime("%Y-%m-%d %H:%M:%S"),
        "customer": {
            "id": venta.cliente.id,
            "name": venta.cliente.nombre,
            "email": venta.cliente.email,
        },
        "seller": {
            "id": venta.vendedor.id,
            "name": venta.vendedor.nombre,
            "email": venta.vendedor.email,
        },
        "approved_by": (
            {
                "id": venta.confirmacion_vendedor_por.id,
                "name": venta.confirmacion_vendedor_por.nombre,
                "email": venta.confirmacion_vendedor_por.email,
            }
            if venta.confirmacion_vendedor_por_id
            else None
        ),
        "subtotal": str(venta.subtotal),
        "iva": str(venta.iva),
        "discount": str(venta.descuento),
        "total": str(venta.total),
        "payment_type": venta.tipo_pago,
        "status": venta.estado,
        "delivery": {
            "method": venta.metodo_entrega,
            "method_label": venta.get_metodo_entrega_display() if venta.metodo_entrega else "",
            "delivery_address": venta.direccion_entrega,
            "delivery_city": venta.ciudad_entrega,
            "delivery_phone": venta.telefono_entrega,
            "pickup_point": venta.punto_retiro,
            "pickup_contact_name": venta.nombre_contacto_retiro,
            "pickup_contact_phone": venta.telefono_contacto_retiro,
        },
    }


def _serialize_sale_detail(venta):
    """
    Serialización completa para detalle de una venta.
    """
    return {
        **_serialize_sale_row(venta),
        "lines": [
            _serialize_sale_line(item)
            for item in venta.lineas.select_related("medicamento").all()
        ],
        "history": [
            {
                "id": item.id,
                "action": item.accion,
                "detail": item.detalle,
                "date": timezone.localtime(item.fecha).strftime("%Y-%m-%d %H:%M:%S"),
                "user": {
                    "id": item.usuario.id,
                    "name": item.usuario.nombre,
                    "email": item.usuario.email,
                },
            }
            for item in venta.historial.select_related("usuario").all()
        ],
        "seller_confirmation_at": (
            timezone.localtime(venta.confirmacion_vendedor_en).strftime("%Y-%m-%d %H:%M:%S")
            if venta.confirmacion_vendedor_en
            else None
        ),
        "customer_confirmation_at": (
            timezone.localtime(venta.confirmacion_cliente_en).strftime("%Y-%m-%d %H:%M:%S")
            if venta.confirmacion_cliente_en
            else None
        ),
    }


# =========================
# HELPERS DE FILTROS
# =========================

def _sales_queryset_for_user(user):
    """
    Queryset base restringido por rol.

    - Administrador: ve todas las ventas.
    - Farmaceuta: ve solo sus ventas.
    - Cliente: ve solo sus ventas como cliente.
    """
    queryset = Venta.objects.select_related(
        "cliente",
        "vendedor",
        "confirmacion_vendedor_por",
        "confirmacion_cliente_por",
    ).prefetch_related(
        "lineas__medicamento",
        "historial__usuario",
    ).all()

    if getattr(user, "rol", None) == "Farmaceuta":
        queryset = queryset.filter(vendedor=user)

    elif getattr(user, "rol", None) == "Cliente":
        queryset = queryset.filter(cliente=user)

    return queryset


def _filter_sales_queryset(request, queryset):
    """
    Aplica filtros opcionales de listado y reporte.
    """
    invoice_number = (request.GET.get("invoice_number") or "").strip()
    sale_date = (request.GET.get("sale_date") or "").strip()
    date_from = (request.GET.get("date_from") or "").strip()
    date_to = (request.GET.get("date_to") or "").strip()
    customer = (request.GET.get("customer") or "").strip()
    seller = (request.GET.get("seller") or "").strip()
    sale_status = (request.GET.get("status") or "").strip()

    if invoice_number:
        queryset = queryset.filter(numero_factura__icontains=invoice_number)

    if sale_date:
        queryset = queryset.filter(fecha_hora__date=sale_date)

    if date_from:
        queryset = queryset.filter(fecha_hora__date__gte=date_from)

    if date_to:
        queryset = queryset.filter(fecha_hora__date__lte=date_to)

    if customer:
        queryset = queryset.filter(cliente__nombre__icontains=customer)

    if seller:
        queryset = queryset.filter(vendedor__nombre__icontains=seller)

    if sale_status:
        queryset = queryset.filter(estado=sale_status)

    return queryset, {
        "invoice_number": invoice_number,
        "sale_date": sale_date,
        "date_from": date_from,
        "date_to": date_to,
        "customer": customer,
        "seller": seller,
        "status": sale_status,
    }


# =========================
# HELPERS DE REPORTES
# =========================

def _export_sales_excel(sales, request):
    """
    Genera reporte Excel de ventas.
    """
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Reporte ventas"

    generated_at = timezone.localtime(timezone.now()).strftime("%Y-%m-%d %H:%M:%S")
    generated_by = f"{request.user.nombre} ({request.user.email})"

    worksheet.append(["Reporte de ventas - Curatio"])
    worksheet.append([f"Generado por: {generated_by}"])
    worksheet.append([f"Fecha y hora de generación: {generated_at}"])
    worksheet.append([])
    worksheet.append(
        [
            "Número de factura",
            "Fecha y hora",
            "Cliente",
            "Farmaceuta",
            "Tipo de pago",
            "Aprobador",
            "Estado",
            "Subtotal",
            "IVA",
            "Descuento",
            "Total",
        ]
    )

    for sale in sales:
        worksheet.append(
            [
                sale.numero_factura,
                timezone.localtime(sale.fecha_hora).strftime("%Y-%m-%d %H:%M:%S"),
                sale.cliente.nombre,
                sale.vendedor.nombre,
                sale.get_tipo_pago_display(),
                sale.confirmacion_vendedor_por.nombre if sale.confirmacion_vendedor_por_id else "-",
                sale.get_estado_display(),
                float(sale.subtotal),
                float(sale.iva),
                float(sale.descuento),
                float(sale.total),
            ]
        )

    for col in ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K"):
        worksheet.column_dimensions[col].width = 22

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="reporte_ventas_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    )
    return response


def _export_sales_pdf(sales, request):
    """
    Genera reporte PDF de ventas.
    """
    generated_at = timezone.localtime(timezone.now()).strftime("%Y-%m-%d %H:%M:%S")
    generated_by = f"{request.user.nombre} ({request.user.email})"

    output = BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        leftMargin=8 * mm,
        rightMargin=8 * mm,
        topMargin=8 * mm,
        bottomMargin=8 * mm,
        title="Reporte de ventas Curatio",
        author=request.user.email,
        encrypt=StandardEncryption(
            userPassword="",
            ownerPassword="curatio-report-owner",
            canPrint=1,
            canModify=0,
            canCopy=1,
            canAnnotate=0,
        ),
    )

    styles = getSampleStyleSheet()

    story = [
        Paragraph("Reporte de ventas - Curatio", styles["Title"]),
        Spacer(1, 4),
        Paragraph(f"Generado por: {generated_by}", styles["Normal"]),
        Paragraph(f"Fecha y hora de generación: {generated_at}", styles["Normal"]),
        Spacer(1, 8),
    ]

    data = [
        [
            "Factura",
            "Fecha",
            "Cliente",
            "Farmaceuta",
            "Tipo pago",
            "Aprobador",
            "Estado",
            "Subtotal",
            "IVA",
            "Descuento",
            "Total",
        ]
    ]

    for sale in sales:
        data.append(
            [
                sale.numero_factura,
                timezone.localtime(sale.fecha_hora).strftime("%Y-%m-%d %H:%M"),
                sale.cliente.nombre,
                sale.vendedor.nombre,
                sale.get_tipo_pago_display(),
                sale.confirmacion_vendedor_por.nombre if sale.confirmacion_vendedor_por_id else "-",
                sale.get_estado_display(),
                str(sale.subtotal),
                str(sale.iva),
                str(sale.descuento),
                str(sale.total),
            ]
        )

    table = Table(data, repeatRows=1)

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#243b63")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#9aa7bf")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
            ]
        )
    )

    story.append(table)
    document.build(story)

    output.seek(0)
    response = HttpResponse(output.getvalue(), content_type="application/pdf; charset=utf-8")
    response["Content-Disposition"] = (
        f'attachment; filename="reporte_ventas_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    )
    return response


def _build_sale_invoice_pdf_enterprise(venta):
    """
    Genera una factura / comprobante PDF con estilo empresarial.
    """
    output = BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title=f"Factura {venta.numero_factura}",
        author="Curatio",
        encrypt=StandardEncryption(
            userPassword="",
            ownerPassword="curatio-invoice-owner",
            canPrint=1,
            canModify=0,
            canCopy=1,
            canAnnotate=0,
        ),
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"].clone("invoice_title")
    title_style.fontName = "Helvetica-Bold"
    title_style.fontSize = 18
    title_style.leading = 22
    title_style.alignment = TA_LEFT
    title_style.textColor = colors.HexColor("#111827")
    title_style.spaceAfter = 3

    subtitle_style = styles["Normal"].clone("invoice_subtitle")
    subtitle_style.fontName = "Helvetica"
    subtitle_style.fontSize = 9
    subtitle_style.leading = 11
    subtitle_style.textColor = colors.HexColor("#4B5563")
    subtitle_style.spaceAfter = 2

    section_title_style = styles["Normal"].clone("invoice_section_title")
    section_title_style.fontName = "Helvetica-Bold"
    section_title_style.fontSize = 10
    section_title_style.leading = 12
    section_title_style.textColor = colors.HexColor("#1F2937")
    section_title_style.spaceAfter = 4

    normal_style = styles["Normal"].clone("invoice_normal")
    normal_style.fontName = "Helvetica"
    normal_style.fontSize = 9
    normal_style.leading = 11
    normal_style.textColor = colors.HexColor("#1F2937")
    normal_style.spaceAfter = 2

    strong_style = styles["Normal"].clone("invoice_strong")
    strong_style.fontName = "Helvetica-Bold"
    strong_style.fontSize = 9
    strong_style.leading = 11
    strong_style.textColor = colors.HexColor("#111827")
    strong_style.spaceAfter = 2

    small_center_style = styles["Normal"].clone("invoice_small_center")
    small_center_style.fontName = "Helvetica"
    small_center_style.fontSize = 8
    small_center_style.leading = 10
    small_center_style.textColor = colors.HexColor("#6B7280")
    small_center_style.alignment = TA_CENTER
    small_center_style.spaceAfter = 2

    total_label_style = styles["Normal"].clone("invoice_total_label")
    total_label_style.fontName = "Helvetica-Bold"
    total_label_style.fontSize = 10
    total_label_style.leading = 12
    total_label_style.textColor = colors.HexColor("#111827")

    total_value_style = styles["Normal"].clone("invoice_total_value")
    total_value_style.fontName = "Helvetica-Bold"
    total_value_style.fontSize = 13
    total_value_style.leading = 15
    total_value_style.textColor = colors.HexColor("#111827")

    badge_style = styles["Normal"].clone("invoice_badge")
    badge_style.fontName = "Helvetica-Bold"
    badge_style.fontSize = 9
    badge_style.leading = 11
    badge_style.alignment = TA_CENTER
    badge_style.textColor = colors.HexColor("#065F46")

    def divider():
        table = Table([[""]], colWidths=[178 * mm], rowHeights=[0.6 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#D1D5DB")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        return table

    def info_card(title, rows, width=86 * mm):
        content = [[Paragraph(title, section_title_style)]]

        for label, value in rows:
            content.append(
                [
                    Paragraph(
                        f"<b>{label}:</b> {value}",
                        normal_style,
                    )
                ]
            )

        table = Table(content, colWidths=[width])
        table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#D1D5DB")),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        return table

    story = []

    header_left = [
        Paragraph("CURATIO", title_style),
        Paragraph("Farmacia y bienestar", subtitle_style),
        Paragraph("NIT: 901234567-8", subtitle_style),
        Paragraph("Bogotá D.C. - Colombia", subtitle_style),
        Paragraph("Teléfono: (601) 123 4567", subtitle_style),
        Paragraph("Correo: soporte@curatio.com", subtitle_style),
    ]

    status_badge = Table(
        [[Paragraph("FACTURA GENERADA", badge_style)]],
        colWidths=[52 * mm],
    )
    status_badge.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ECFDF5")),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#A7F3D0")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    header_right = [
        Paragraph("FACTURA / COMPROBANTE", strong_style),
        Spacer(1, 2),
        status_badge,
        Spacer(1, 5),
        Paragraph(f"<b>Número:</b> {venta.numero_factura}", normal_style),
        Paragraph(f"<b>Referencia:</b> {venta.id}", normal_style),
        Paragraph(
            f"<b>Fecha:</b> {timezone.localtime(venta.fecha_hora).strftime('%Y-%m-%d %H:%M:%S')}",
            normal_style,
        ),
        Paragraph(f"<b>Estado:</b> {venta.get_estado_display()}", normal_style),
        Paragraph(f"<b>Tipo de pago:</b> {venta.get_tipo_pago_display()}", normal_style),
    ]

    header_table = Table(
        [
            [
                header_left,
                header_right,
            ]
        ],
        colWidths=[106 * mm, 72 * mm],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    story.append(header_table)
    story.append(Spacer(1, 8))
    story.append(divider())
    story.append(Spacer(1, 10))

    customer_card = info_card(
        "Información del cliente",
        [
            ("Nombre", venta.cliente.nombre),
            ("Correo", venta.cliente.email),
        ],
    )

    seller_card = info_card(
        "Información del vendedor",
        [
            ("Nombre", venta.vendedor.nombre),
            ("Correo", venta.vendedor.email),
        ],
    )

    info_cards_table = Table(
        [[customer_card, seller_card]],
        colWidths=[88 * mm, 88 * mm],
    )
    info_cards_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    story.append(info_cards_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Detalle de productos", section_title_style))

    detail_data = [
        [
            Paragraph("<b>Medicamento</b>", strong_style),
            Paragraph("<b>Cantidad</b>", strong_style),
            Paragraph("<b>Precio unitario</b>", strong_style),
            Paragraph("<b>Subtotal</b>", strong_style),
        ]
    ]

    for line in venta.lineas.select_related("medicamento").all():
        detail_data.append(
            [
                Paragraph(line.medicamento.nombre, normal_style),
                Paragraph(str(line.cantidad), normal_style),
                Paragraph(str(line.precio_unitario), normal_style),
                Paragraph(str(line.subtotal_linea()), normal_style),
            ]
        )

    detail_table = Table(
        detail_data,
        colWidths=[82 * mm, 22 * mm, 34 * mm, 40 * mm],
        repeatRows=1,
    )
    detail_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#243B63")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#F8FAFC")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    story.append(detail_table)
    story.append(Spacer(1, 12))

    totals_table = Table(
        [
            [Paragraph("Subtotal", normal_style), Paragraph(str(venta.subtotal), normal_style)],
            [Paragraph("IVA", normal_style), Paragraph(str(venta.iva), normal_style)],
            [Paragraph("Descuento", normal_style), Paragraph(str(venta.descuento), normal_style)],
            [Paragraph("TOTAL", total_label_style), Paragraph(str(venta.total), total_value_style)],
        ],
        colWidths=[36 * mm, 44 * mm],
    )
    totals_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -2), colors.white),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E5E7EB")),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#D1D5DB")),
                ("LINEABOVE", (0, -1), (-1, -1), 0.7, colors.HexColor("#9CA3AF")),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    qr_value = (
        f"Curatio|Factura:{venta.numero_factura}|"
        f"Venta:{venta.id}|"
        f"Cliente:{venta.cliente.nombre}|"
        f"Total:{venta.total}|"
        f"Fecha:{timezone.localtime(venta.fecha_hora).strftime('%Y-%m-%d %H:%M:%S')}"
    )

    qr_code = qr.QrCodeWidget(qr_value)
    bounds = qr_code.getBounds()
    qr_width = bounds[2] - bounds[0]
    qr_height = bounds[3] - bounds[1]

    qr_size = 34 * mm
    drawing = Drawing(
        qr_size,
        qr_size,
        transform=[qr_size / qr_width, 0, 0, qr_size / qr_height, 0, 0],
    )
    drawing.add(qr_code)

    qr_box = Table(
        [
            [Paragraph("Validación digital", section_title_style)],
            [drawing],
            [Paragraph("Código interno de trazabilidad", small_center_style)],
        ],
        colWidths=[54 * mm],
    )
    qr_box.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#D1D5DB")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    totals_and_qr = Table(
        [[qr_box, totals_table]],
        colWidths=[62 * mm, 96 * mm],
    )
    totals_and_qr.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    story.append(totals_and_qr)
    story.append(Spacer(1, 14))

    observations_box = Table(
        [
            [Paragraph("Observaciones", section_title_style)],
            [
                Paragraph(
                    "Este documento sirve como soporte de compra y comprobante de pago. "
                    "Conserve esta factura para validaciones, reclamaciones o solicitudes relacionadas con la transacción.",
                    normal_style,
                )
            ],
        ],
        colWidths=[178 * mm],
    )
    observations_box.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#D1D5DB")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F9FAFB")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(observations_box)
    story.append(Spacer(1, 12))
    story.append(divider())
    story.append(Spacer(1, 8))
    story.append(Paragraph("Gracias por confiar en Curatio", strong_style))
    story.append(
        Paragraph(
            "Farmacia y bienestar con atención responsable.",
            small_center_style,
        )
    )
    story.append(
        Paragraph(
            "www.curatio.com · soporte@curatio.com",
            small_center_style,
        )
    )

    document.build(story)

    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type="application/pdf; charset=utf-8",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="factura_{venta.numero_factura}.pdf"'
    )
    return response


def _build_sale_invoice_pdf_pos(venta):
    """
    Genera una factura / comprobante PDF premium tipo POS / tirilla.
    """
    output = BytesIO()

    receipt_width = 80 * mm
    receipt_height = 500 * mm

    document = SimpleDocTemplate(
        output,
        pagesize=(receipt_width, receipt_height),
        leftMargin=6 * mm,
        rightMargin=6 * mm,
        topMargin=8 * mm,
        bottomMargin=8 * mm,
        title=f"Factura {venta.numero_factura}",
        author="Curatio",
        encrypt=StandardEncryption(
            userPassword="",
            ownerPassword="curatio-invoice-owner",
            canPrint=1,
            canModify=0,
            canCopy=1,
            canAnnotate=0,
        ),
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"].clone("receipt_title")
    title_style.fontName = "Helvetica-Bold"
    title_style.fontSize = 14
    title_style.leading = 16
    title_style.alignment = TA_CENTER
    title_style.spaceAfter = 2
    title_style.textColor = colors.HexColor("#111827")

    brand_style = styles["Normal"].clone("receipt_brand")
    brand_style.fontName = "Helvetica-Bold"
    brand_style.fontSize = 8.5
    brand_style.leading = 10
    brand_style.alignment = TA_CENTER
    brand_style.spaceAfter = 1
    brand_style.textColor = colors.HexColor("#1F2937")

    business_style = styles["Normal"].clone("receipt_business")
    business_style.fontName = "Helvetica"
    business_style.fontSize = 7
    business_style.leading = 8.5
    business_style.alignment = TA_CENTER
    business_style.spaceAfter = 1
    business_style.textColor = colors.HexColor("#4B5563")

    section_title_style = styles["Normal"].clone("receipt_section_title")
    section_title_style.fontName = "Helvetica-Bold"
    section_title_style.fontSize = 8.5
    section_title_style.leading = 10
    section_title_style.spaceAfter = 3
    section_title_style.textColor = colors.HexColor("#111827")

    normal_style = styles["Normal"].clone("receipt_normal")
    normal_style.fontName = "Helvetica"
    normal_style.fontSize = 7.6
    normal_style.leading = 9.2
    normal_style.spaceAfter = 1
    normal_style.textColor = colors.HexColor("#1F2937")

    strong_style = styles["Normal"].clone("receipt_strong")
    strong_style.fontName = "Helvetica-Bold"
    strong_style.fontSize = 7.8
    strong_style.leading = 9.4
    strong_style.spaceAfter = 1
    strong_style.textColor = colors.HexColor("#111827")

    small_center_style = styles["Normal"].clone("receipt_small_center")
    small_center_style.fontName = "Helvetica"
    small_center_style.fontSize = 6.8
    small_center_style.leading = 8.2
    small_center_style.alignment = TA_CENTER
    small_center_style.spaceAfter = 1
    small_center_style.textColor = colors.HexColor("#4B5563")

    total_style = styles["Normal"].clone("receipt_total")
    total_style.fontName = "Helvetica-Bold"
    total_style.fontSize = 11.5
    total_style.leading = 13
    total_style.spaceAfter = 2
    total_style.textColor = colors.HexColor("#111827")

    highlight_style = styles["Normal"].clone("receipt_highlight")
    highlight_style.fontName = "Helvetica-Bold"
    highlight_style.fontSize = 8.5
    highlight_style.leading = 10
    highlight_style.alignment = TA_CENTER
    highlight_style.spaceAfter = 2
    highlight_style.textColor = colors.HexColor("#065F46")

    legal_style = styles["Normal"].clone("receipt_legal")
    legal_style.fontName = "Helvetica"
    legal_style.fontSize = 6.5
    legal_style.leading = 7.8
    legal_style.alignment = TA_CENTER
    legal_style.spaceAfter = 1
    legal_style.textColor = colors.HexColor("#6B7280")

    def divider():
        return Paragraph("─" * 38, small_center_style)

    def build_key_value_table(rows, col_widths=None, emphasize_last=False):
        data = []

        for index, (label, value) in enumerate(rows):
            value_style = strong_style if (emphasize_last and index == len(rows) - 1) else normal_style
            data.append(
                [
                    Paragraph(str(label), normal_style),
                    Paragraph(str(value), value_style),
                ]
            )

        if col_widths is None:
            col_widths = [28 * mm, 40 * mm]

        table = Table(data, colWidths=col_widths)
        table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ]
            )
        )
        return table

    def build_badge(text):
        table = Table([[Paragraph(text, strong_style)]], colWidths=[64 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ECFDF5")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#A7F3D0")),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        return table

    story = []

    story.append(Paragraph("CURATIO", title_style))
    story.append(Paragraph("Farmacia y bienestar", brand_style))
    story.append(Paragraph("Comprobante de venta / Factura", business_style))
    story.append(Paragraph("NIT: 901234567-8", business_style))
    story.append(Paragraph("Bogotá D.C. - Colombia", business_style))
    story.append(Paragraph("Línea de atención: (601) 123 4567", business_style))
    story.append(Spacer(1, 4))
    story.append(divider())
    story.append(Spacer(1, 4))
    story.append(build_badge("PAGO REGISTRADO CORRECTAMENTE"))
    story.append(Spacer(1, 5))

    story.append(Paragraph("DATOS DE LA TRANSACCIÓN", section_title_style))
    story.append(
        build_key_value_table(
            [
                ("Factura", venta.numero_factura),
                ("Referencia", str(venta.id)),
                ("Fecha", timezone.localtime(venta.fecha_hora).strftime("%Y-%m-%d")),
                ("Hora", timezone.localtime(venta.fecha_hora).strftime("%H:%M:%S")),
                ("Estado", venta.get_estado_display()),
                ("Pago", venta.get_tipo_pago_display()),
            ]
        )
    )

    story.append(Spacer(1, 4))
    story.append(
        build_key_value_table(
            [
                ("Cliente", venta.cliente.nombre),
                ("Correo", venta.cliente.email),
                ("Vendedor", venta.vendedor.nombre),
            ]
        )
    )

    story.append(Spacer(1, 4))
    story.append(divider())
    story.append(Spacer(1, 4))

    story.append(Paragraph("DETALLE DE PRODUCTOS", section_title_style))
    story.append(
        build_key_value_table(
            [
                ("Cant. x Unit.", "Subtotal"),
            ],
            col_widths=[36 * mm, 32 * mm],
        )
    )
    story.append(Spacer(1, 2))

    for line in venta.lineas.select_related("medicamento").all():
        medication_name = line.medicamento.nombre
        quantity = line.cantidad
        unit_price = line.precio_unitario
        line_subtotal = line.subtotal_linea()

        story.append(Paragraph(medication_name, strong_style))

        detail_table = Table(
            [
                [
                    Paragraph(f"{quantity} x {unit_price}", normal_style),
                    Paragraph(str(line_subtotal), strong_style),
                ]
            ],
            colWidths=[36 * mm, 32 * mm],
        )
        detail_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (0, 0), (0, 0), "LEFT"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ]
            )
        )
        story.append(detail_table)
        story.append(Spacer(1, 3))

    story.append(divider())
    story.append(Spacer(1, 4))

    story.append(Paragraph("RESUMEN DE PAGO", section_title_style))
    story.append(
        build_key_value_table(
            [
                ("Subtotal", str(venta.subtotal)),
                ("IVA", str(venta.iva)),
                ("Descuento", str(venta.descuento)),
            ]
        )
    )

    story.append(Spacer(1, 4))

    total_table = Table(
        [
            [
                Paragraph("TOTAL", total_style),
                Paragraph(str(venta.total), total_style),
            ]
        ],
        colWidths=[28 * mm, 40 * mm],
    )
    total_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E5E7EB")),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#9CA3AF")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(total_table)

    story.append(Spacer(1, 6))
    story.append(divider())
    story.append(Spacer(1, 4))

    qr_value = (
        f"Curatio|Factura:{venta.numero_factura}|"
        f"Venta:{venta.id}|"
        f"Cliente:{venta.cliente.nombre}|"
        f"Total:{venta.total}|"
        f"Fecha:{timezone.localtime(venta.fecha_hora).strftime('%Y-%m-%d %H:%M:%S')}"
    )

    qr_code = qr.QrCodeWidget(qr_value)
    bounds = qr_code.getBounds()
    qr_width = bounds[2] - bounds[0]
    qr_height = bounds[3] - bounds[1]

    qr_size = 28 * mm
    drawing = Drawing(qr_size, qr_size, transform=[qr_size / qr_width, 0, 0, qr_size / qr_height, 0, 0])
    drawing.add(qr_code)

    qr_table = Table([[drawing]], colWidths=[68 * mm])
    qr_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    story.append(Paragraph("VALIDACIÓN DIGITAL", section_title_style))
    story.append(qr_table)
    story.append(Paragraph("Escanee este código para referencia interna de la compra.", small_center_style))
    story.append(Spacer(1, 5))
    story.append(divider())
    story.append(Spacer(1, 4))
    story.append(Paragraph("Gracias por confiar en Curatio", highlight_style))
    story.append(
        Paragraph(
            "Este documento sirve como soporte de compra y comprobante de pago.",
            legal_style,
        )
    )
    story.append(
        Paragraph(
            "Conserve esta factura para solicitudes, validaciones o reclamaciones.",
            legal_style,
        )
    )
    story.append(
        Paragraph(
            "Medicamentos sujetos a disponibilidad y políticas internas de dispensación.",
            legal_style,
        )
    )
    story.append(Spacer(1, 3))
    story.append(Paragraph("www.curatio.com", small_center_style))
    story.append(Paragraph("soporte@curatio.com", small_center_style))

    document.build(story)

    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type="application/pdf; charset=utf-8",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="factura_{venta.numero_factura}.pdf"'
    )
    return response


def _build_sale_invoice_pdf_by_context(request, venta):
    """
    Decide qué formato de factura generar según el contexto de la venta.

    Regla aplicada:
    - Si la venta fue creada desde checkout web del cliente, se genera
      factura empresarial.
    - En cualquier otro caso, se genera comprobante tipo POS para venta interna.
    """
    is_web_checkout = venta.historial.filter(accion="CHECKOUT_WEB_CREADO").exists()

    if is_web_checkout:
        return _build_sale_invoice_pdf_enterprise(venta)

    return _build_sale_invoice_pdf_pos(venta)


# =========================
# RECURSOS API SPA
# =========================

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def sales_resource(request):
    """
    GET: listado de ventas con filtros opcionales.
    POST: creación de venta desde la SPA.
    """
    if request.method == "GET":
        queryset = _sales_queryset_for_user(request.user)
        queryset, filters = _filter_sales_queryset(request, queryset)

        results = [_serialize_sale_row(item) for item in queryset]

        return Response(
            {
                "data": {
                    "results": results,
                    "filters": filters,
                    "count": len(results),
                },
                "message": "Ventas obtenidas correctamente.",
            }
        )

    if not _usuario_puede_vender(request.user):
        return _forbidden_sales_response()

    try:
        invoice_number = (request.data.get("invoice_number") or "").strip()
        customer_id = request.data.get("customer_id")
        payment_type = _validate_payment_type((request.data.get("payment_type") or "").strip())

        subtotal = _parse_decimal(request.data.get("subtotal"), "subtotal")
        iva = _parse_decimal(request.data.get("iva"), "iva")
        discount = _parse_decimal(request.data.get("discount"), "discount", required=False)
        total = _parse_decimal(request.data.get("total"), "total")

        lines = _validate_sale_lines(request.data.get("lines", []))

        if not invoice_number:
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Por favor corrige los campos resaltados.",
                        "fields": {"invoice_number": ["Este campo es obligatorio."]},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        customer = User.objects.filter(
            pk=customer_id,
            rol="Cliente",
            estado=True,
            is_active=True,
        ).first()

        if not customer:
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Por favor corrige los campos resaltados.",
                        "fields": {"customer_id": ["Se requiere un cliente válido."]},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        expected_subtotal = _expected_subtotal_from_lines(lines)
        expected_total = (subtotal + iva - discount).quantize(Decimal("0.01"))

        if subtotal != expected_subtotal:
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "El subtotal no coincide con las líneas de la venta.",
                        "fields": {
                            "subtotal": [
                                f"El subtotal esperado es {expected_subtotal} según las líneas de la venta."
                            ]
                        },
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if total != expected_total:
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "El total no coincide con subtotal + IVA - descuento.",
                        "fields": {
                            "total": [
                                f"El total esperado es {expected_total}."
                            ]
                        },
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            sale = Venta(
                numero_factura=invoice_number,
                cliente=customer,
                vendedor=request.user,
                subtotal=subtotal,
                iva=iva,
                descuento=discount,
                total=total,
                tipo_pago=payment_type,
                estado="Pendiente",
            )
            sale.full_clean()
            sale.save()

            for line in lines:
                sale_line = VentaLinea(
                    venta=sale,
                    medicamento=line["medicamento"],
                    cantidad=line["cantidad"],
                    precio_unitario=line["precio_unitario"],
                )
                sale_line.full_clean()
                sale_line.save()

            VentaHistorial.objects.create(
                venta=sale,
                accion="CREADA",
                usuario=request.user,
                detalle=(
                    f"Venta {sale.numero_factura} registrada en estado "
                    "Pendiente de confirmación."
                ),
            )

        try:
            send_mail(
                subject=f"Curatio — Detalle de venta {sale.numero_factura}",
                message=construir_cuerpo_correo_venta(sale),
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[sale.cliente.email],
                fail_silently=False,
            )
        except Exception as exc:
            VentaHistorial.objects.create(
                venta=sale,
                accion="NOTIFICACION_CORREO_ERROR",
                usuario=request.user,
                detalle=f"No se pudo enviar correo al cliente: {exc}",
            )
        else:
            VentaHistorial.objects.create(
                venta=sale,
                accion="NOTIFICACION_CORREO",
                usuario=request.user,
                detalle="Notificación enviada al cliente.",
            )

        sale = Venta.objects.select_related(
            "cliente",
            "vendedor",
            "confirmacion_vendedor_por",
            "confirmacion_cliente_por",
        ).prefetch_related(
            "lineas__medicamento",
            "historial__usuario",
        ).get(pk=sale.pk)

        return Response(
            {
                "data": {
                    "sale": _serialize_sale_detail(sale),
                },
                "message": "Venta creada correctamente.",
            },
            status=status.HTTP_201_CREATED,
        )

    except ValueError as exc:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Por favor corrige los campos resaltados.",
                    "fields": exc.args[0] if exc.args else {},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as exc:
        return Response(
            {
                "error": {
                    "code": "SERVER_ERROR",
                    "message": str(exc),
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def sale_detail_resource(request, sale_id):
    """
    GET: detalle de una venta.
    PATCH: actualización de campos permitidos de una venta existente.

    Campos editables:
    - payment_type
    - status
    """
    sale = get_object_or_404(
        Venta.objects.select_related(
            "cliente",
            "vendedor",
            "confirmacion_vendedor_por",
            "confirmacion_cliente_por",
        ).prefetch_related(
            "lineas__medicamento",
            "historial__usuario",
        ),
        pk=sale_id,
    )

    if not _puede_ver_venta(request.user, sale):
        return _forbidden_sales_response()

    if request.method == "GET":
        return Response(
            {
                "data": {
                    "sale": _serialize_sale_detail(sale),
                },
                "message": "Venta obtenida correctamente.",
            }
        )

    if not _usuario_puede_vender(request.user):
        return _forbidden_sales_response()

    if request.user.rol == "Farmaceuta" and sale.vendedor_id != request.user.id:
        return _forbidden_sales_response()

    if sale.estado not in ("Pendiente", "Completada"):
        return Response(
            {
                "error": {
                    "code": "INVALID_STATUS",
                    "message": "Solo se pueden actualizar ventas en estado pendiente o completada.",
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    fields_changed = []

    if "payment_type" in request.data:
        new_payment_type = _validate_payment_type((request.data.get("payment_type") or "").strip())
        if sale.tipo_pago != new_payment_type:
            fields_changed.append(f"tipo_pago: {sale.tipo_pago} -> {new_payment_type}")
            sale.tipo_pago = new_payment_type

    if "status" in request.data:
        new_status = _validate_sale_status((request.data.get("status") or "").strip())
        if sale.estado != new_status:
            if new_status == "Completada":
                return Response(
                    {
                        "error": {
                            "code": "INVALID_STATUS_TRANSITION",
                            "message": "Usa el endpoint de confirmación de pago para completar la venta.",
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            fields_changed.append(f"estado: {sale.estado} -> {new_status}")
            sale.estado = new_status

    if not fields_changed:
        return Response(
            {
                "data": {
                    "sale": _serialize_sale_detail(sale),
                },
                "message": "La venta no tuvo cambios.",
            }
        )

    sale.full_clean()
    sale.save()

    VentaHistorial.objects.create(
        venta=sale,
        accion="ACTUALIZADA",
        usuario=request.user,
        detalle="; ".join(fields_changed),
    )

    return Response(
        {
            "data": {
                "sale": _serialize_sale_detail(sale),
            },
            "message": "Venta actualizada correctamente.",
        }
    )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def sale_confirm_payment_resource(request, sale_id):
    """
    Confirma el pago de una venta.

    Comportamiento:
    - Si llama ADMIN o FARMACEUTA, registra confirmación del vendedor.
    - Si llama CLIENTE, registra confirmación del cliente.
    - Cuando existen ambas confirmaciones, la venta pasa a Completada
      y se descuenta stock.
    """
    sale = get_object_or_404(
        Venta.objects.select_related(
            "cliente",
            "vendedor",
            "confirmacion_vendedor_por",
            "confirmacion_cliente_por",
        ).prefetch_related(
            "lineas__medicamento",
            "historial__usuario",
        ),
        pk=sale_id,
    )

    if not _puede_ver_venta(request.user, sale):
        return _forbidden_sales_response()

    if sale.estado != "Pendiente":
        return Response(
            {
                "error": {
                    "code": "INVALID_STATUS",
                    "message": "Solo se pueden confirmar ventas en estado pendiente.",
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        if request.user.rol in ("Administrador", "Farmaceuta"):
            if request.user.rol == "Farmaceuta" and sale.vendedor_id != request.user.id:
                return _forbidden_sales_response()

            if sale.confirmacion_vendedor_en is None:
                sale.confirmacion_vendedor_en = timezone.now()
                sale.confirmacion_vendedor_por = request.user

                VentaHistorial.objects.create(
                    venta=sale,
                    accion="CONFIRMACION_VENDEDOR",
                    usuario=request.user,
                    detalle="Pago confirmado por el vendedor.",
                )

        elif request.user.rol == "Cliente":
            if sale.cliente_id != request.user.id:
                return _forbidden_sales_response()

            if sale.confirmacion_cliente_en is None:
                sale.confirmacion_cliente_en = timezone.now()
                sale.confirmacion_cliente_por = request.user

                VentaHistorial.objects.create(
                    venta=sale,
                    accion="CONFIRMACION_CLIENTE",
                    usuario=request.user,
                    detalle="Pago confirmado por el cliente.",
                )

        else:
            return _forbidden_sales_response()

        sale.save()

        completed = sale.aplicar_descuento_stock_si_completa()

        if completed:
            VentaHistorial.objects.create(
                venta=sale,
                accion="COMPLETADA",
                usuario=request.user,
                detalle="Venta completada tras confirmación de pago.",
            )

    sale.refresh_from_db()

    return Response(
        {
            "data": {
                "sale": _serialize_sale_detail(sale),
                "completed": completed,
            },
            "message": (
                "La venta se completó correctamente."
                if completed
                else "La confirmación de pago fue registrada correctamente."
            ),
        }
    )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def sale_cancel_resource(request, sale_id):
    """
    Anula una venta pendiente o completada.

    Reglas:
    - ADMIN puede anular cualquier venta.
    - FARMACEUTA solo puede anular sus ventas.
    - Debe enviarse un motivo / observación.
    """
    sale = get_object_or_404(
        Venta.objects.select_related(
            "cliente",
            "vendedor",
            "confirmacion_vendedor_por",
            "confirmacion_cliente_por",
        ).prefetch_related(
            "lineas__medicamento",
            "historial__usuario",
        ),
        pk=sale_id,
    )

    if not _usuario_puede_vender(request.user):
        return _forbidden_sales_response()

    if request.user.rol == "Farmaceuta" and sale.vendedor_id != request.user.id:
        return _forbidden_sales_response()

    if sale.estado not in ("Pendiente", "Completada"):
        return Response(
            {
                "error": {
                    "code": "INVALID_STATUS",
                    "message": "Solo se pueden anular ventas en estado pendiente o completada.",
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    reason = (request.data.get("reason") or "").strip()

    if not reason:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "El motivo de anulación es obligatorio.",
                    "fields": {"reason": ["Este campo es obligatorio."]},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    previous_status = sale.estado
    sale.estado = "Anulada"
    sale.save(update_fields=["estado"])

    VentaHistorial.objects.create(
        venta=sale,
        accion="ANULADA",
        usuario=request.user,
        detalle=f"Venta anulada. Estado anterior: {previous_status}. Motivo: {reason}",
    )

    sale.refresh_from_db()

    return Response(
        {
            "data": {
                "sale": _serialize_sale_detail(sale),
            },
            "message": "Venta anulada correctamente.",
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sales_report_resource(request):
    """
    Exporta reporte de ventas filtrado en Excel o PDF.
    """
    if not _usuario_puede_vender(request.user):
        return _forbidden_sales_response()

    queryset = _sales_queryset_for_user(request.user)
    queryset, _filters = _filter_sales_queryset(request, queryset)

    if not queryset.exists():
        return Response(
            {
                "error": {
                    "code": "NO_RESULTS",
                    "message": "No se encontraron ventas con los filtros seleccionados.",
                }
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    report_format = (request.GET.get("format") or "").strip().lower()

    if report_format == "excel":
        return _export_sales_excel(queryset, request)

    if report_format == "pdf":
        return _export_sales_pdf(queryset, request)

    return Response(
        {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Formato de reporte no válido. Usa excel o pdf.",
            }
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sales_customers_catalog_resource(request):
    """
    Catálogo de clientes activos para el checkout de ventas.
    Solo ADMIN y FARMACEUTA pueden consultar este recurso.
    """
    if not _usuario_puede_vender(request.user):
        return _forbidden_sales_response()

    customers = (
        User.objects.filter(
            rol="Cliente",
            estado=True,
            is_active=True,
        )
        .order_by("nombre")
        .values("id", "nombre", "email")
    )

    results = [
        {
            "id": item["id"],
            "name": item["nombre"],
            "email": item["email"],
        }
        for item in customers
    ]

    return Response(
        {
            "data": {
                "results": results,
            },
            "message": "Clientes obtenidos correctamente.",
        }
    )


def _resolve_checkout_web_seller():
    """
    Resuelve el usuario interno que quedará asociado como vendedor
    para una compra web del cliente.
    """
    return (
        User.objects.filter(
            rol__in=["Administrador", "Farmaceuta"],
            estado=True,
            is_active=True,
        )
        .order_by("id")
        .first()
    )


def _serialize_checkout_web_result(sale):
    """
    Serialización resumida para el resultado del checkout web.
    """
    return {
        "id": sale.id,
        "invoice_number": sale.numero_factura,
        "sale_datetime": timezone.localtime(sale.fecha_hora).strftime("%Y-%m-%d %H:%M:%S"),
        "customer": {
            "id": sale.cliente.id,
            "name": sale.cliente.nombre,
            "email": sale.cliente.email,
        },
        "seller": {
            "id": sale.vendedor.id,
            "name": sale.vendedor.nombre,
            "email": sale.vendedor.email,
        },
        "payment_type": sale.tipo_pago,
        "status": sale.estado,
        "subtotal": str(sale.subtotal),
        "iva": str(sale.iva),
        "discount": str(sale.descuento),
        "total": str(sale.total),
        "lines": [_serialize_sale_line(item) for item in sale.lineas.select_related("medicamento").all()],
    }


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def customer_checkout_resource(request):
    """
    Checkout web para el rol Cliente.

    Flujo:
    - el cliente autenticado compra para sí mismo
    - se valida stock y montos
    - se asigna automáticamente un vendedor interno
    - la venta queda pendiente de aprobación interna
    - no se descuenta stock hasta que ADMIN / FARMACEUTA apruebe manualmente
    """
    if getattr(request.user, "rol", None) != "Cliente":
        return Response(
            {
                "error": {
                    "code": "FORBIDDEN",
                    "message": "Solo los clientes pueden usar el checkout web.",
                }
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        invoice_number = (request.data.get("invoice_number") or "").strip()
        payment_type = _validate_payment_type((request.data.get("payment_type") or "").strip())

        subtotal = _parse_decimal(request.data.get("subtotal"), "subtotal")
        iva = _parse_decimal(request.data.get("iva"), "iva")
        discount = _parse_decimal(request.data.get("discount"), "discount", required=False)
        total = _parse_decimal(request.data.get("total"), "total")

        lines = _validate_sale_lines(request.data.get("lines", []))
        delivery_data = _validar_datos_entrega_checkout(request.data)

        if not invoice_number:
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Por favor corrige los campos resaltados.",
                        "fields": {"invoice_number": ["Este campo es obligatorio."]},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        seller = _resolve_checkout_web_seller()

        if not seller:
            return Response(
                {
                    "error": {
                        "code": "CONFIGURATION_ERROR",
                        "message": "No hay un vendedor interno disponible para registrar la compra.",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        expected_subtotal = _expected_subtotal_from_lines(lines)
        expected_total = (subtotal + iva - discount).quantize(Decimal("0.01"))

        if subtotal != expected_subtotal:
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "El subtotal no coincide con las líneas de la venta.",
                        "fields": {
                            "subtotal": [
                                f"El subtotal esperado es {expected_subtotal} según las líneas de la venta."
                            ]
                        },
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if total != expected_total:
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "El total no coincide con subtotal + IVA - descuento.",
                        "fields": {
                            "total": [f"El total esperado es {expected_total}."]
                        },
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            sale = Venta(
                numero_factura=invoice_number,
                cliente=request.user,
                vendedor=seller,
                subtotal=subtotal,
                iva=iva,
                descuento=discount,
                total=total,
                tipo_pago=payment_type,
                estado="Pendiente",
                metodo_entrega=delivery_data["delivery_method"],
                direccion_entrega=delivery_data["delivery_address"],
                ciudad_entrega=delivery_data["delivery_city"],
                telefono_entrega=delivery_data["delivery_phone"],
                punto_retiro=delivery_data["pickup_point"],
                nombre_contacto_retiro=delivery_data["pickup_contact_name"],
                telefono_contacto_retiro=delivery_data["pickup_contact_phone"],
            )
            sale.full_clean()
            sale.save()

            for line in lines:
                sale_line = VentaLinea(
                    venta=sale,
                    medicamento=line["medicamento"],
                    cantidad=line["cantidad"],
                    precio_unitario=line["precio_unitario"],
                )
                sale_line.full_clean()
                sale_line.save()

            VentaHistorial.objects.create(
                venta=sale,
                accion="CHECKOUT_WEB_CREADO",
                usuario=request.user,
                detalle="Venta creada desde checkout web del cliente y pendiente de aprobación interna.",
            )

            sale.confirmacion_cliente_en = timezone.now()
            sale.confirmacion_cliente_por = request.user
            sale.save(
                update_fields=[
                    "confirmacion_cliente_en",
                    "confirmacion_cliente_por",
                ]
            )

            VentaHistorial.objects.create(
                venta=sale,
                accion="CONFIRMACION_CLIENTE",
                usuario=request.user,
                detalle="Pago confirmado desde checkout web por el cliente.",
            )

            _crear_notificacion_interna_para_todos(
                venta=sale,
                tipo="VENTA_WEB_PENDIENTE",
                titulo="Nueva compra web pendiente",
                mensaje=(
                    f"La compra {sale.numero_factura} del cliente {sale.cliente.nombre} "
                    "quedó pendiente de aprobación interna."
                ),
            )

        try:
            send_mail(
                subject=f"Curatio — Compra registrada {sale.numero_factura}",
                message=construir_cuerpo_correo_venta(sale),
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[sale.cliente.email],
                fail_silently=False,
            )
        except Exception as exc:
            VentaHistorial.objects.create(
                venta=sale,
                accion="NOTIFICACION_CORREO_ERROR",
                usuario=request.user,
                detalle=f"No se pudo enviar correo al cliente: {exc}",
            )
        else:
            VentaHistorial.objects.create(
                venta=sale,
                accion="NOTIFICACION_CORREO",
                usuario=request.user,
                detalle="Confirmación inicial enviada al cliente.",
            )

        sale = Venta.objects.select_related(
            "cliente",
            "vendedor",
            "confirmacion_vendedor_por",
            "confirmacion_cliente_por",
        ).prefetch_related(
            "lineas__medicamento",
            "historial__usuario",
        ).get(pk=sale.pk)

        return Response(
            {
                "data": {
                    "checkout_sale": _serialize_checkout_web_result(sale),
                },
                "message": "La compra web fue registrada correctamente. Está pendiente de aprobación interna.",
            },
            status=status.HTTP_201_CREATED,
        )

    except ValueError as exc:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Por favor corrige los campos resaltados.",
                    "fields": exc.args[0] if exc.args else {},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as exc:
        return Response(
            {
                "error": {
                    "code": "SERVER_ERROR",
                    "message": str(exc),
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sales_customer_lookup_resource(request):
    """
    Búsqueda de cliente por tipo y número de documento para venta interna.
    """
    if not _usuario_puede_vender(request.user):
        return _forbidden_sales_response()

    document_type = (request.GET.get("document_type") or "CC").strip()
    document_number = (request.GET.get("document_number") or "").strip()

    if not document_number:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "El número de documento es obligatorio.",
                    "fields": {
                        "document_number": ["Este campo es obligatorio."]
                    },
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    customer = User.objects.filter(
        rol="Cliente",
        estado=True,
        is_active=True,
        tipo_documento=document_type,
        numero_documento=document_number,
    ).first()

    if not customer:
        return Response(
            {
                "error": {
                    "code": "NOT_FOUND",
                    "message": "No se encontró el cliente.",
                    "fields": {},
                }
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(
        {
            "data": {
                "customer": {
                    "id": customer.id,
                    "name": customer.nombre,
                    "email": customer.email,
                    "document_type": customer.tipo_documento,
                    "document_number": customer.numero_documento,
                    "phone": customer.telefono,
                    "address": customer.direccion,
                }
            },
            "message": "Cliente obtenido correctamente.",
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sale_invoice_resource(request, sale_id):
    """
    Descarga factura / comprobante individual de una venta.
    """
    sale = get_object_or_404(
        Venta.objects.select_related(
            "cliente",
            "vendedor",
            "confirmacion_vendedor_por",
            "confirmacion_cliente_por",
        ).prefetch_related(
            "lineas__medicamento",
            "historial",
        ),
        pk=sale_id,
    )

    if not _puede_ver_venta(request.user, sale):
        return _forbidden_sales_response()

    return _build_sale_invoice_pdf_by_context(request, sale)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sales_notifications_resource(request):
    """
    Lista notificaciones internas del módulo de ventas.

    Solo aplica para:
    - Administrador
    - Farmaceuta
    """
    if getattr(request.user, "rol", None) not in ("Administrador", "Farmaceuta"):
        return _forbidden_sales_response()

    notifications = NotificacionVenta.objects.filter(usuario=request.user).select_related("venta")

    unread_only = (request.GET.get("unread_only") or "").strip().lower()
    if unread_only == "true":
        notifications = notifications.filter(leida=False)

    return Response(
        {
            "data": {
                "results": [_serialize_notification_row(item) for item in notifications],
                "count": notifications.count(),
                "unread_count": notifications.filter(leida=False).count(),
            },
            "message": "Notificaciones obtenidas correctamente.",
        }
    )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def sales_notification_read_resource(request, notification_id):
    """
    Marca una notificación como leída.
    """
    if getattr(request.user, "rol", None) not in ("Administrador", "Farmaceuta"):
        return _forbidden_sales_response()

    notification = get_object_or_404(
        NotificacionVenta,
        pk=notification_id,
        usuario=request.user,
    )

    if notification.leida:
        return Response(
            {
                "data": {
                    "notification": _serialize_notification_row(notification),
                },
                "message": "La notificación ya estaba marcada como leída.",
            }
        )

    notification.leida = True
    notification.leida_en = timezone.now()
    notification.save(update_fields=["leida", "leida_en"])

    return Response(
        {
            "data": {
                "notification": _serialize_notification_row(notification),
            },
            "message": "Notificación marcada como leída.",
        }
    )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def sale_internal_approval_resource(request, sale_id):
    """
    Aprueba manualmente una compra web pendiente.

    Solo:
    - Administrador
    - Farmaceuta

    Reglas:
    - la venta debe estar pendiente
    - el cliente ya debió haber confirmado el pago
    - al aprobar se completa la venta y se descuenta stock
    - se notifica al cliente según el método de entrega
    """
    if not _usuario_puede_vender(request.user):
        return _forbidden_sales_response()

    try:
        sale = get_object_or_404(
            Venta.objects.select_related(
                "cliente",
                "vendedor",
                "confirmacion_vendedor_por",
                "confirmacion_cliente_por",
            ).prefetch_related(
                "lineas__medicamento",
                "historial__usuario",
            ),
            pk=sale_id,
        )

        if request.user.rol == "Farmaceuta" and sale.vendedor_id != request.user.id:
            return _forbidden_sales_response()

        if sale.estado != "Pendiente":
            return Response(
                {
                    "error": {
                        "code": "INVALID_STATUS",
                        "message": "Solo se pueden aprobar ventas en estado pendiente.",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if sale.confirmacion_cliente_en is None:
            return Response(
                {
                    "error": {
                        "code": "PAYMENT_NOT_CONFIRMED",
                        "message": "Aún no se ha confirmado el pago del cliente.",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            sale = (
                Venta.objects.select_for_update()
                .select_related(
                    "cliente",
                    "vendedor",
                    "confirmacion_vendedor_por",
                    "confirmacion_cliente_por",
                )
                .prefetch_related(
                    "lineas__medicamento",
                    "historial__usuario",
                )
                .get(pk=sale.pk)
            )

            if sale.confirmacion_vendedor_en is not None:
                sale.refresh_from_db()
                return Response(
                    {
                        "data": {
                            "sale": _serialize_sale_detail(sale),
                        },
                        "message": "La aprobación interna ya había sido registrada.",
                    }
                )

            sale.confirmacion_vendedor_en = timezone.now()
            sale.confirmacion_vendedor_por = request.user
            sale.save(
                update_fields=[
                    "confirmacion_vendedor_en",
                    "confirmacion_vendedor_por",
                ]
            )

            VentaHistorial.objects.create(
                venta=sale,
                accion="CONFIRMACION_VENDEDOR",
                usuario=request.user,
                detalle="Compra web aprobada manualmente por el personal interno.",
            )

            completed = sale.aplicar_descuento_stock_si_completa()

            sale.refresh_from_db()

            if completed and sale.estado != "Completada":
                sale.estado = "Completada"
                sale.save(update_fields=["estado"])
                sale.refresh_from_db()

            if completed:
                VentaHistorial.objects.create(
                    venta=sale,
                    accion="COMPLETADA",
                    usuario=request.user,
                    detalle="Venta completada tras aprobación manual interna.",
                )

            _mark_pending_sale_notifications_as_read(sale)

            _crear_notificacion_interna_para_todos(
                venta=sale,
                tipo="VENTA_APROBADA",
                titulo="Compra aprobada",
                mensaje=(
                    f"La compra {sale.numero_factura} del cliente {sale.cliente.nombre} "
                    "fue aprobada y completada correctamente."
                ),
            )

        try:
            send_mail(
                subject=f"Curatio — Compra aprobada {sale.numero_factura}",
                message=_construir_mensaje_cliente_aprobacion(sale),
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[sale.cliente.email],
                fail_silently=False,
            )
        except Exception as exc:
            VentaHistorial.objects.create(
                venta=sale,
                accion="NOTIFICACION_CORREO_ERROR",
                usuario=request.user,
                detalle=f"No se pudo enviar correo de aprobación al cliente: {exc}",
            )
        else:
            VentaHistorial.objects.create(
                venta=sale,
                accion="NOTIFICACION_CORREO",
                usuario=request.user,
                detalle="Correo de aprobación y entrega enviado al cliente.",
            )

        sale = Venta.objects.select_related(
            "cliente",
            "vendedor",
            "confirmacion_vendedor_por",
            "confirmacion_cliente_por",
        ).prefetch_related(
            "lineas__medicamento",
            "historial__usuario",
        ).get(pk=sale.pk)

        return Response(
            {
                "data": {
                    "sale": _serialize_sale_detail(sale),
                    "completed": completed,
                },
                "message": "La venta fue aprobada y completada correctamente.",
            }
        )

    except ValidationError as exc:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "No fue posible aprobar la venta.",
                    "fields": {
                        "approval": exc.messages if hasattr(exc, "messages") else [str(exc)]
                    },
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as exc:
        traceback.print_exc()

        return Response(
            {
                "error": {
                    "code": "SERVER_ERROR",
                    "message": "Ocurrió un error inesperado al aprobar la venta.",
                    "fields": {
                        "detail": [str(exc)]
                    },
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
# =========================
# HELPERS CARTSHOPS
# =========================

def _usuario_puede_listar_carritos(user):
    """
    Solo ADMIN y FARMACEUTA pueden listar carritos.
    """
    return getattr(user, "is_authenticated", False) and getattr(user, "rol", None) in (
        "Administrador",
        "Farmaceuta",
    )


def _forbidden_cartshops_response():
    return Response(
        {
            "error": {
                "code": "FORBIDDEN",
                "message": "No tienes permisos para listar carritos.",
            }
        },
        status=status.HTTP_403_FORBIDDEN,
    )


def _map_sale_status_to_cart_state(sale_status):
    """
    Mapeo de estados del dominio ventas -> dominio carritos.
    """
    if sale_status == "Pendiente":
        return "Activo"
    if sale_status == "Completada":
        return "Completado"
    if sale_status == "Anulada":
        return "Cancelado"
    return "Activo"


def _filter_cartshops_queryset(request, queryset):
    """
    Filtros específicos del módulo de carritos.

    Soporta:
    - invoice_number
    - date
    - status (Activo / Completado / Cancelado)
    """
    invoice_number = (request.GET.get("invoice_number") or "").strip()
    exact_date = (request.GET.get("date") or "").strip()
    cart_status = (request.GET.get("status") or "").strip()

    if invoice_number:
        queryset = queryset.filter(numero_factura__icontains=invoice_number)

    if exact_date:
        queryset = queryset.filter(fecha_hora__date=exact_date)

    if cart_status == "Activo":
        queryset = queryset.filter(estado="Pendiente")
    elif cart_status == "Completado":
        queryset = queryset.filter(estado="Completada")
    elif cart_status == "Cancelado":
        queryset = queryset.filter(estado="Anulada")

    return queryset, {
        "invoice_number": invoice_number,
        "date": exact_date,
        "status": cart_status,
    }


def _serialize_cartshop_row(venta, line):
    """
    Cada fila de la tabla de carritos representa una línea del carrito/venta.
    """
    return {
        "id": f"{venta.id}-{line.id}",
        "sale_id": venta.id,
        "line_id": line.id,
        "invoice_number": venta.numero_factura,
        "date": timezone.localtime(venta.fecha_hora).strftime("%Y-%m-%d"),
        "date_time": timezone.localtime(venta.fecha_hora).strftime("%Y-%m-%d %H:%M:%S"),
        "product": line.medicamento.nombre,
        "amount": line.cantidad,
        "unit_value": str(line.precio_unitario),
        "subtotal": str(line.subtotal_linea()),
        "state": _map_sale_status_to_cart_state(venta.estado),
        "approver": (
            venta.confirmacion_vendedor_por.nombre
            if venta.confirmacion_vendedor_por_id
            else ""
        ),
        "customer": {
            "id": venta.cliente.id,
            "name": venta.cliente.nombre,
            "email": venta.cliente.email,
        },
        "seller": {
            "id": venta.vendedor.id,
            "name": venta.vendedor.nombre,
            "email": venta.vendedor.email,
        },
        "is_active": venta.estado == "Pendiente",
    }


def _serialize_cartshop_detail(venta):
    return {
        "id": venta.id,
        "invoice_number": venta.numero_factura,
        "date_time": timezone.localtime(venta.fecha_hora).strftime("%Y-%m-%d %H:%M:%S"),
        "state": _map_sale_status_to_cart_state(venta.estado),
        "payment_type": venta.tipo_pago,
        "subtotal": str(venta.subtotal),
        "iva": str(venta.iva),
        "discount": str(venta.descuento),
        "total": str(venta.total),
        "approver": (
            {
                "id": venta.confirmacion_vendedor_por.id,
                "name": venta.confirmacion_vendedor_por.nombre,
                "email": venta.confirmacion_vendedor_por.email,
            }
            if venta.confirmacion_vendedor_por_id
            else None
        ),
        "customer": {
            "id": venta.cliente.id,
            "name": venta.cliente.nombre,
            "email": venta.cliente.email,
        },
        "seller": {
            "id": venta.vendedor.id,
            "name": venta.vendedor.nombre,
            "email": venta.vendedor.email,
        },
        "lines": [
            {
                "id": item.id,
                "product": item.medicamento.nombre,
                "amount": item.cantidad,
                "unit_value": str(item.precio_unitario),
                "subtotal": str(item.subtotal_linea()),
            }
            for item in venta.lineas.select_related("medicamento").all()
        ],
    }


# =========================
# CARTSHOPS API
# =========================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cartshops_resource(request):
    """
    Listado administrativo de carritos.

    Fuente real:
    - se monta sobre Venta + VentaLinea
    - Pendiente  -> Activo
    - Completada -> Completado
    - Anulada    -> Cancelado
    """
    if not _usuario_puede_listar_carritos(request.user):
        return _forbidden_cartshops_response()

    queryset = _sales_queryset_for_user(request.user)
    queryset, filters = _filter_cartshops_queryset(request, queryset)

    rows = []
    for venta in queryset.order_by("-fecha_hora"):
        for line in venta.lineas.select_related("medicamento").all():
            rows.append(_serialize_cartshop_row(venta, line))

    return Response(
        {
            "data": {
                "results": rows,
                "filters": filters,
                "count": len(rows),
            },
            "message": "Carritos obtenidos correctamente.",
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cartshop_detail_resource(request, sale_id):
    """
    Visualización detallada de un carrito.
    """
    if not _usuario_puede_listar_carritos(request.user):
        return _forbidden_cartshops_response()

    venta = get_object_or_404(
        _sales_queryset_for_user(request.user),
        pk=sale_id,
    )

    return Response(
        {
            "data": {
                "cartshop": _serialize_cartshop_detail(venta),
            },
            "message": "Detalle del carrito obtenido correctamente.",
        },
        status=status.HTTP_200_OK,
    )