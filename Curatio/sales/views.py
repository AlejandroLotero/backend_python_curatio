import json
from decimal import Decimal
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

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
