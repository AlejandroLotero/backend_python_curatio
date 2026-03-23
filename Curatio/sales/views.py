import json
from decimal import Decimal
from functools import wraps
from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.pdfencrypt import StandardEncryption
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from products.models import Medicamento

from .forms import VentaForm, VentaLineaFormSet
from .models import Venta, VentaHistorial
from .utils import construir_cuerpo_correo_venta


def _precios_medicamentos_json():
    rows = Medicamento.objects.filter(estado__nombre="Activo", stock__gt=0).values(
        "id", "precio_venta"
    )
    return json.dumps(
        {str(r["id"]): str(r["precio_venta"]) for r in rows},
        ensure_ascii=False,
    )


def _usuario_puede_vender(user):
    return user.is_authenticated and user.rol in ("Administrador", "Farmaceuta")


def solo_admin_o_farmaceuta(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not _usuario_puede_vender(request.user):
            messages.error(
                request,
                "Solo usuarios con rol Administrador o Farmaceuta pueden acceder al módulo de ventas.",
            )
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)

    return _wrapped


def _puede_ver_venta(user, venta):
    if user.rol == "Administrador":
        return True
    if user.rol == "Farmaceuta" and venta.vendedor_id == user.id:
        return True
    if user.rol == "Cliente" and venta.cliente_id == user.id:
        return True
    return False


def _subtotal_esperado_desde_formset(formset):
    total = Decimal("0")
    for form in formset.forms:
        if not hasattr(form, "cleaned_data"):
            continue
        data = form.cleaned_data
        if not data or data.get("DELETE"):
            continue
        med = data.get("medicamento")
        cantidad = data.get("cantidad")
        if med and cantidad:
            total += (med.precio_venta * cantidad).quantize(Decimal("0.01"))
    return total


def _ventas_filtradas(request):
    ventas = Venta.objects.select_related(
        "cliente",
        "vendedor",
        "confirmacion_vendedor_por",
    ).all()

    numero_factura = request.GET.get("numero_factura")
    fecha = request.GET.get("fecha")
    fecha_desde = request.GET.get("fecha_desde")
    fecha_hasta = request.GET.get("fecha_hasta")
    cliente = request.GET.get("cliente")
    farmaceuta = request.GET.get("farmaceuta")
    estado = request.GET.get("estado")

    if numero_factura:
        ventas = ventas.filter(numero_factura__icontains=numero_factura)
    if fecha:
        ventas = ventas.filter(fecha_hora__date=fecha)
    if fecha_desde:
        ventas = ventas.filter(fecha_hora__date__gte=fecha_desde)
    if fecha_hasta:
        ventas = ventas.filter(fecha_hora__date__lte=fecha_hasta)
    if cliente:
        ventas = ventas.filter(cliente__nombre__icontains=cliente)
    if farmaceuta:
        ventas = ventas.filter(vendedor__nombre__icontains=farmaceuta)
    if estado:
        ventas = ventas.filter(estado=estado)

    if request.user.rol == "Farmaceuta":
        ventas = ventas.filter(vendedor=request.user)

    filtros = {
        "numero_factura": numero_factura or "",
        "fecha": fecha or "",
        "fecha_desde": fecha_desde or "",
        "fecha_hasta": fecha_hasta or "",
        "cliente": cliente or "",
        "farmaceuta": farmaceuta or "",
        "estado": estado or "",
    }
    return ventas, filtros


def _nombre_aprobador(venta):
    return venta.confirmacion_vendedor_por.nombre if venta.confirmacion_vendedor_por_id else "-"


def _exportar_ventas_excel(ventas, request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte ventas"

    generado_en = timezone.localtime(timezone.now()).strftime("%Y-%m-%d %H:%M:%S")
    generado_por = f"{request.user.nombre} ({request.user.email})"

    ws.append(["Reporte de ventas - Curatio"])
    ws.append([f"Generado por: {generado_por}"])
    ws.append([f"Fecha y hora de generación: {generado_en}"])
    ws.append([])
    ws.append(
        [
            "Número de factura",
            "Fecha y hora",
            "Cliente",
            "Farmaceuta",
            "Tipo de pago",
            "Aprobador (Admin/Farmaceuta)",
            "Estado de la venta",
            "Subtotal",
            "IVA",
            "Descuento",
            "Total",
        ]
    )

    for v in ventas:
        ws.append(
            [
                v.numero_factura,
                timezone.localtime(v.fecha_hora).strftime("%Y-%m-%d %H:%M"),
                v.cliente.nombre,
                v.vendedor.nombre,
                v.get_tipo_pago_display(),
                _nombre_aprobador(v),
                v.get_estado_display(),
                float(v.subtotal),
                float(v.iva),
                float(v.descuento),
                float(v.total),
            ]
        )

    for col in ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K"):
        ws.column_dimensions[col].width = 22

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="reporte_ventas_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    )
    return response


def _exportar_ventas_pdf(ventas, request):
    generado_en = timezone.localtime(timezone.now()).strftime("%Y-%m-%d %H:%M:%S")
    generado_por = f"{request.user.nombre} ({request.user.email})"

    output = BytesIO()
    doc = SimpleDocTemplate(
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
        Paragraph(f"Generado por: {generado_por}", styles["Normal"]),
        Paragraph(f"Fecha y hora de generación: {generado_en}", styles["Normal"]),
        Spacer(1, 8),
    ]

    data = [
        [
            "Factura",
            "Fecha/Hora",
            "Cliente",
            "Farmaceuta",
            "Tipo pago",
            "Aprobador",
            "Estado",
            "Total",
        ]
    ]

    for v in ventas:
        data.append(
            [
                v.numero_factura,
                timezone.localtime(v.fecha_hora).strftime("%Y-%m-%d %H:%M"),
                v.cliente.nombre,
                v.vendedor.nombre,
                v.get_tipo_pago_display(),
                _nombre_aprobador(v),
                v.get_estado_display(),
                f"${v.total}",
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
    doc.build(story)

    output.seek(0)
    response = HttpResponse(output.getvalue(), content_type="application/pdf; charset=utf-8")
    response["Content-Disposition"] = (
        f'attachment; filename="reporte_ventas_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    )
    return response


@login_required
@solo_admin_o_farmaceuta
def crear_venta(request):
    if request.method == "POST":
        borrador = Venta(vendedor=request.user, estado="Pendiente")
        form = VentaForm(request.POST, user=request.user, instance=borrador)
        formset = VentaLineaFormSet(request.POST, instance=borrador)
        if form.is_valid() and formset.is_valid():
            esperado = _subtotal_esperado_desde_formset(formset)
            sub = form.cleaned_data["subtotal"].quantize(Decimal("0.01"))
            if abs(esperado - sub) > Decimal("0.01"):
                messages.error(
                    request,
                    f"El subtotal no coincide con las líneas (esperado {esperado}, indicado {sub}).",
                )
            else:
                try:
                    with transaction.atomic():
                        venta = form.save(commit=False)
                        venta.vendedor = request.user
                        venta.estado = "Pendiente"
                        venta.full_clean()
                        venta.save()
                        formset.instance = venta
                        instances = formset.save(commit=False)
                        for obj in formset.deleted_objects:
                            obj.delete()
                        for inst in instances:
                            inst.precio_unitario = inst.medicamento.precio_venta
                            inst.save()
                        formset.save_m2m()

                        VentaHistorial.objects.create(
                            venta=venta,
                            accion="CREADA",
                            usuario=request.user,
                            detalle=f"Venta {venta.numero_factura} registrada en estado Pendiente de confirmación.",
                        )

                    try:
                        send_mail(
                            subject=f"Curatio — Detalle de venta {venta.numero_factura}",
                            message=construir_cuerpo_correo_venta(venta),
                            from_email=getattr(
                                settings,
                                "DEFAULT_FROM_EMAIL",
                                None,
                            ),
                            recipient_list=[venta.cliente.email],
                            fail_silently=False,
                        )
                    except Exception as exc:
                        messages.warning(
                            request,
                            f"Venta creada, pero no se pudo enviar el correo: {exc}",
                        )
                    else:
                        VentaHistorial.objects.create(
                            venta=venta,
                            accion="NOTIFICACION_CORREO",
                            usuario=request.user,
                            detalle="Notificación enviada al cliente.",
                        )

                    messages.success(
                        request,
                        "La venta se creó correctamente. Estado: pendiente de confirmación de pago.",
                    )
                    return redirect("detalle_venta", pk=venta.pk)
                except ValidationError as e:
                    for msg in e.error_list:
                        messages.error(request, msg)
                except Exception as exc:
                    messages.error(request, f"No se pudo guardar la venta: {exc}")
    else:
        form = VentaForm(user=request.user)
        formset = VentaLineaFormSet()

    return render(
        request,
        "sales/crear_venta.html",
        {
            "form": form,
            "formset": formset,
            "precios_medicamentos_json": _precios_medicamentos_json(),
        },
    )


@login_required
def detalle_venta(request, pk):
    venta = get_object_or_404(
        Venta.objects.select_related("cliente", "vendedor").prefetch_related(
            "lineas__medicamento__presentacion",
            "historial__usuario",
        ),
        pk=pk,
    )
    if not _puede_ver_venta(request.user, venta):
        messages.error(request, "No tiene permiso para ver esta venta.")
        return redirect("dashboard")

    puede_confirmar_vendedor = (
        venta.estado == "Pendiente"
        and request.user.rol in ("Administrador", "Farmaceuta")
        and (
            request.user.rol == "Administrador" or venta.vendedor_id == request.user.id
        )
        and venta.confirmacion_vendedor_en is None
    )
    puede_confirmar_cliente = (
        venta.estado == "Pendiente"
        and request.user.rol == "Cliente"
        and venta.cliente_id == request.user.id
        and venta.confirmacion_cliente_en is None
    )
    puede_anular = (
        venta.estado == "Pendiente"
        and request.user.rol in ("Administrador", "Farmaceuta")
        and (
            request.user.rol == "Administrador" or venta.vendedor_id == request.user.id
        )
    )

    return render(
        request,
        "sales/detalle_venta.html",
        {
            "venta": venta,
            "puede_confirmar_vendedor": puede_confirmar_vendedor,
            "puede_confirmar_cliente": puede_confirmar_cliente,
            "puede_anular": puede_anular,
        },
    )


@login_required
def confirmar_pago_vendedor(request, pk):
    if request.method != "POST":
        return redirect("detalle_venta", pk=pk)

    venta = get_object_or_404(Venta, pk=pk)
    if not _puede_ver_venta(request.user, venta):
        messages.error(request, "No autorizado.")
        return redirect("dashboard")

    if request.user.rol not in ("Administrador", "Farmaceuta"):
        messages.error(request, "Solo el personal autorizado puede confirmar este lado.")
        return redirect("detalle_venta", pk=pk)

    if request.user.rol == "Farmaceuta" and venta.vendedor_id != request.user.id:
        messages.error(request, "Solo quien registró la venta puede confirmar por la farmacia.")
        return redirect("detalle_venta", pk=pk)

    if venta.estado != "Pendiente":
        messages.error(request, "Solo se puede confirmar pago en ventas pendientes.")
        return redirect("detalle_venta", pk=pk)

    if venta.confirmacion_vendedor_en:
        messages.warning(request, "La confirmación del vendedor ya fue registrada.")
        return redirect("detalle_venta", pk=pk)

    try:
        with transaction.atomic():
            venta = Venta.objects.select_for_update().get(pk=pk)
            if venta.estado != "Pendiente" or venta.confirmacion_vendedor_en:
                messages.error(request, "El estado de la venta cambió. Intente de nuevo.")
                return redirect("detalle_venta", pk=pk)
            venta.confirmacion_vendedor_en = timezone.now()
            venta.confirmacion_vendedor_por = request.user
            venta.save(
                update_fields=[
                    "confirmacion_vendedor_en",
                    "confirmacion_vendedor_por",
                ]
            )
            VentaHistorial.objects.create(
                venta=venta,
                accion="CONFIRMACION_VENDEDOR",
                usuario=request.user,
                detalle=(
                    f"Usuario: {request.user.email}, "
                    f"método de pago: {venta.get_tipo_pago_display()}, "
                    f"confirmación de recepción del pago (lado farmacia)."
                ),
            )
            completada = venta.aplicar_descuento_stock_si_completa()
            if completada:
                VentaHistorial.objects.create(
                    venta=venta,
                    accion="COMPLETADA",
                    usuario=request.user,
                    detalle="Venta completada; stock descontado tras confirmación de ambas partes.",
                )
                messages.success(
                    request,
                    "Confirmación registrada. La venta quedó COMPLETADA y el stock fue actualizado.",
                )
            else:
                messages.success(
                    request,
                    "Confirmación del personal registrada. Falta la confirmación del cliente.",
                )
    except ValidationError as e:
        for msg in e.error_list:
            messages.error(request, msg)
    except Exception as exc:
        messages.error(request, str(exc))

    return redirect("detalle_venta", pk=pk)


@login_required
def confirmar_pago_cliente(request, pk):
    if request.method != "POST":
        return redirect("detalle_venta", pk=pk)

    venta = get_object_or_404(Venta, pk=pk)
    if request.user.rol != "Cliente" or venta.cliente_id != request.user.id:
        messages.error(request, "Solo el cliente de la venta puede confirmar desde esta acción.")
        return redirect("dashboard")

    if venta.estado != "Pendiente":
        messages.error(request, "Solo se puede confirmar en ventas pendientes.")
        return redirect("detalle_venta", pk=pk)

    if venta.confirmacion_cliente_en:
        messages.warning(request, "Su confirmación ya fue registrada.")
        return redirect("detalle_venta", pk=pk)

    try:
        with transaction.atomic():
            venta = Venta.objects.select_for_update().get(pk=pk)
            if venta.estado != "Pendiente" or venta.confirmacion_cliente_en:
                messages.error(request, "El estado de la venta cambió. Intente de nuevo.")
                return redirect("detalle_venta", pk=pk)
            venta.confirmacion_cliente_en = timezone.now()
            venta.confirmacion_cliente_por = request.user
            venta.save(
                update_fields=[
                    "confirmacion_cliente_en",
                    "confirmacion_cliente_por",
                ]
            )
            VentaHistorial.objects.create(
                venta=venta,
                accion="CONFIRMACION_CLIENTE",
                usuario=request.user,
                detalle=(
                    f"Usuario: {request.user.email}, "
                    f"método de pago acordado: {venta.get_tipo_pago_display()}, "
                    f"confirmación del pago por parte del cliente."
                ),
            )
            completada = venta.aplicar_descuento_stock_si_completa()
            if completada:
                VentaHistorial.objects.create(
                    venta=venta,
                    accion="COMPLETADA",
                    usuario=request.user,
                    detalle="Venta completada; stock descontado tras confirmación de ambas partes.",
                )
                messages.success(
                    request,
                    "Confirmación registrada. La venta quedó COMPLETADA.",
                )
            else:
                messages.success(
                    request,
                    "Su confirmación fue registrada. Falta la confirmación del personal de la farmacia.",
                )
    except ValidationError as e:
        for msg in e.error_list:
            messages.error(request, msg)
    except Exception as exc:
        messages.error(request, str(exc))

    return redirect("detalle_venta", pk=pk)


@login_required
@solo_admin_o_farmaceuta
def anular_venta(request, pk):
    if request.method != "POST":
        return redirect("detalle_venta", pk=pk)

    venta = get_object_or_404(Venta, pk=pk)
    if request.user.rol == "Farmaceuta" and venta.vendedor_id != request.user.id:
        messages.error(request, "No puede anular una venta que no registró.")
        return redirect("dashboard")

    if venta.estado != "Pendiente":
        messages.error(request, "Solo se pueden anular ventas en estado pendiente de confirmación.")
        return redirect("detalle_venta", pk=pk)

    venta.estado = "Anulada"
    venta.save(update_fields=["estado"])
    VentaHistorial.objects.create(
        venta=venta,
        accion="ANULADA",
        usuario=request.user,
        detalle="Venta anulada antes de completarse.",
    )
    messages.success(request, "La venta fue anulada.")
    return redirect("detalle_venta", pk=pk)


@login_required
@solo_admin_o_farmaceuta
def listar_ventas(request):
    """
    RF - Listar ventas con filtros
    """

    ventas, filtros = _ventas_filtradas(request)
    formato = (request.GET.get("formato") or "").lower().strip()
    exportar = (request.GET.get("exportar") or "").strip() == "1"

    data = [
        {
            "id": v.id,
            "numero_factura": v.numero_factura,
            "fecha_hora": v.fecha_hora.strftime("%Y-%m-%d %H:%M"),
            "cliente": v.cliente.nombre,
            "farmaceuta": v.vendedor.nombre,
            "estado": v.estado,
            "tipo_pago": v.get_tipo_pago_display(),
            "aprobador": _nombre_aprobador(v),
            "total": str(v.total),
        }
        for v in ventas
    ]

    if request.GET.get("format") == "json":
        if not data:
            return JsonResponse(
                {"mensaje": "No se encontraron ventas con los filtros aplicados"}
            )
        return JsonResponse(data, safe=False)

    if exportar:
        if not ventas.exists():
            messages.error(
                request,
                "No se encontraron registros con los filtros aplicados para generar el reporte.",
            )
            return redirect("listar_ventas")
        if formato == "excel":
            return _exportar_ventas_excel(ventas, request)
        if formato == "pdf":
            return _exportar_ventas_pdf(ventas, request)
        messages.error(request, "Formato de exportación no válido. Use Excel o PDF.")
        return redirect("listar_ventas")

    return render(
        request,
        "sales/listar_ventas.html",
        {
            "ventas": ventas,
            "filtros": filtros,
            "estados_venta": Venta.ESTADOS,
        },
    )
