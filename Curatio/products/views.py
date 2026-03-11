from django.shortcuts import render

#Importación para editar medicamento 
from .forms import CrearMedicamentoForm, ActualizarMedicamentoForm

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
#para la paginación
from django.core.paginator import Paginator
#para exportar a excel y pdf
from urllib.parse import urlparse

from .forms import CrearMedicamentoForm
from .models import (
    Presentacion,
    MedicamentoHistorial,
    Medicamento,
    ViaAdministracion,
    Laboratorio,
    EstadoMedicamento,
)
#para el historial de medicamentos
from accounts.models import BitacoraUsuario
from io import BytesIO

try:
    from openpyxl import Workbook
except ImportError:
    Workbook = None
try:
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
except ImportError:
    SimpleDocTemplate = None

# Tamaño de página según regla de negocio: si hay más de 50 registros, paginación
PAGE_SIZE_MEDICAMENTOS = 50

@login_required
def crear_medicamento(request):
    if request.user.rol != "Administrador":
        return redirect("login")

    if request.method == "POST":
        form = CrearMedicamentoForm(request.POST)
        if form.is_valid():
            med = form.save(commit=False)
            med.creado_por = request.user
            med.requiere_formula = False  # oculto, default backend
            med.full_clean()
            med.save()

            MedicamentoHistorial.objects.create(
                medicamento=med,
                accion="CREADO",
                usuario=request.user,
                detalle="Medicamento creado desde el módulo de gestión."
            )

            messages.success(request, "Medicamento creado exitosamente.")
            return redirect("crear_medicamento")
    else:
        form = CrearMedicamentoForm()

    return render(request, "products/crear_medicamento.html", {"form": form})


@login_required
def presentaciones_por_forma(request):
    if request.user.rol != "Administrador":
        return JsonResponse({"detail": "No autorizado"}, status=403)

    forma_id = request.GET.get("forma_id")
    if not forma_id:
        return JsonResponse({"results": []})

    items = list(
        Presentacion.objects.filter(forma_id=forma_id, activo=True)
        .order_by("nombre")
        .values("id", "nombre")
    )
    return JsonResponse({"results": items})


def _get_medicamentos_queryset(request):
    """Queryset base de medicamentos con filtros opcionales (RFADMIN08)."""
    qs = Medicamento.objects.select_related(
        "forma", "presentacion", "via_administracion", "laboratorio",
        "proveedor", "estado", "responsable", "creado_por"
    ).order_by("nombre")

    via_id = (request.GET.get("via_administracion") or "").strip()
    laboratorio_id = (request.GET.get("laboratorio") or "").strip()
    nombre = (request.GET.get("nombre") or "").strip()
    estado_id = (request.GET.get("estado") or "").strip()

    if via_id:
        qs = qs.filter(via_administracion_id=via_id)
    if laboratorio_id:
        qs = qs.filter(laboratorio_id=laboratorio_id)
    if nombre:
        qs = qs.filter(nombre__icontains=nombre)
    if estado_id:
        qs = qs.filter(estado_id=estado_id)

    return qs, {
        "via_administracion": via_id,
        "laboratorio": laboratorio_id,
        "nombre": nombre,
        "estado": estado_id,
    }


@login_required
def listar_medicamentos(request):
    """
    RFADMIN08 - Listar medicamentos.
    Solo ADMIN. Filtros: Vía de administración, Laboratorio, Nombre, Estado.
    Orden alfabético por defecto. Paginación de 50 registros.
    """
    if request.user.rol != "Administrador":
        return redirect("login")

    qs, filtros = _get_medicamentos_queryset(request)
    paginator = Paginator(qs, PAGE_SIZE_MEDICAMENTOS)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "vias": ViaAdministracion.objects.filter(activo=True).order_by("nombre"),
        "laboratorios": Laboratorio.objects.filter(activo=True).order_by("nombre"),
        "estados": EstadoMedicamento.objects.filter(activo=True).order_by("nombre"),
        **filtros,
    }
    return render(request, "products/lista_medicamentos.html", context)


@login_required
def api_listar_medicamentos(request):
    """
    API JSON para listado de medicamentos (tiempo real al aplicar filtros).
    Solo ADMIN. Mismos filtros que listar_medicamentos. Paginación 50.
    """
    if request.user.rol != "Administrador":
        return JsonResponse({"detail": "No autorizado"}, status=403)

    qs, filtros = _get_medicamentos_queryset(request)
    paginator = Paginator(qs, PAGE_SIZE_MEDICAMENTOS)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    resultados = []
    for m in page_obj:
        resultados.append({
            "nombre": m.nombre,
            "forma": m.forma.nombre,
            "presentacion": m.presentacion.nombre,
            "concentracion": m.concentracion,
            "via_administracion": m.via_administracion.nombre,
            "laboratorio": m.laboratorio.nombre,
            "lote": m.lote,
            "fecha_fabricacion": m.fecha_fabricacion.isoformat() if m.fecha_fabricacion else None,
            "fecha_vencimiento": m.fecha_vencimiento.isoformat() if m.fecha_vencimiento else None,
            "stock": m.stock,
            "precio_compra": str(m.precio_compra),
            "precio_venta": str(m.precio_venta),
            "proveedor": m.proveedor.nombre,
            "requiere_formula": m.requiere_formula,
            "descripcion": m.descripcion,
            "estado": m.estado.nombre,
            #para la regla de negocio de que solo se puede vender si el estado es Activo
            "puede_venderse": m.puede_venderse,
            "responsable": m.responsable.email if m.responsable else None,
            "creado_por": m.creado_por.email,
            "creado_en": m.creado_en.isoformat() if m.creado_en else None,
        })

    return JsonResponse({
        "results": resultados,
        "count": paginator.count,
        "num_pages": paginator.num_pages,
        "page": page_obj.number,
        "filtros": filtros,
    })

#cambiar estado de medicamento
@login_required
def cambiar_estado_medicamento(request, pk):
    """
    Cambiar Estado Medicamento (RF). Solo ADMIN.
    Entradas: medicamento (pk en URL), estado (id en POST).
    Reglas: cambio registrado en MedicamentoHistorial y Bitácora.
    """
    if request.user.rol != "Administrador":
        messages.error(request, "No tiene permisos para cambiar el estado de medicamentos.")
        return redirect("login")

    if request.method != "POST":
        messages.error(request, "Método no permitido.")
        return redirect("listar_medicamentos")

    medicamento = Medicamento.objects.filter(pk=pk).select_related("estado").first()
    if not medicamento:
        messages.error(request, "Medicamento no encontrado.")
        return redirect("listar_medicamentos")

    estado_id = (request.POST.get("estado") or "").strip()
    if not estado_id:
        messages.error(request, "Debe seleccionar un estado.")
        return redirect("listar_medicamentos")

    nuevo_estado = EstadoMedicamento.objects.filter(pk=estado_id, activo=True).first()
    if not nuevo_estado:
        messages.error(request, "Estado no válido.")
        return redirect("listar_medicamentos")

    estado_anterior = medicamento.estado.nombre
    if medicamento.estado_id == nuevo_estado.pk:
        messages.info(request, "El medicamento ya tiene ese estado.")
        return redirect("listar_medicamentos")

    medicamento.estado = nuevo_estado
    medicamento.save(update_fields=["estado"])

    detalle_historial = f"Estado: {estado_anterior} → {nuevo_estado.nombre}"
    MedicamentoHistorial.objects.create(
        medicamento=medicamento,
        accion="CAMBIO_ESTADO",
        usuario=request.user,
        detalle=detalle_historial,
    )

    motivo_bitacora = f"Medicamento ID {medicamento.pk} ({medicamento.nombre}): {estado_anterior} → {nuevo_estado.nombre}"
    BitacoraUsuario.objects.create(
        admin=request.user,
        usuario=request.user,
        accion="Cambio estado medicamento",
        motivo=motivo_bitacora,
    )

    messages.success(request, "Estado del medicamento actualizado exitosamente.")
    referer = request.META.get("HTTP_REFERER")
    if referer:
        try:
            p = urlparse(referer)
            if p.netloc == request.get_host() and "cambiar-estado" not in referer:
                return redirect(referer)
        except Exception:
            pass
    return redirect("listar_medicamentos")


@login_required
def reporte_medicamentos(request):
    """Exportar listado de medicamentos a Excel o PDF (mismos filtros que listar). Solo ADMIN."""
    if request.user.rol != "Administrador":
        return redirect("login")

    formato = request.GET.get("formato")
    qs, filtros = _get_medicamentos_queryset(request)
    qs = qs.order_by("nombre")

    if not qs.exists():
        messages.warning(request, "No hay medicamentos para el filtro seleccionado.")
        return redirect("listar_medicamentos")

    if formato == "excel" and Workbook:
        wb = Workbook()
        ws = wb.active
        ws.title = "Medicamentos"
        headers = [
            "Nombre", "Forma farmacéutica", "Presentación", "Concentración",
            "Vía administración", "Laboratorio", "Lote", "F. fabricación", "F. vencimiento",
            "Stock", "Precio compra", "Precio venta", "Proveedor", "Requiere fórmula",
            "Descripción", "Estado", "Responsable", "Creado por", "Creado en",
        ]
        ws.append(headers)
        for m in qs:
            ws.append([
                m.nombre, m.forma.nombre, m.presentacion.nombre, m.concentracion,
                m.via_administracion.nombre, m.laboratorio.nombre, m.lote,
                m.fecha_fabricacion.isoformat() if m.fecha_fabricacion else "",
                m.fecha_vencimiento.isoformat() if m.fecha_vencimiento else "",
                m.stock, m.precio_compra, m.precio_venta, m.proveedor.nombre,
                "Sí" if m.requiere_formula else "No", m.descripcion, m.estado.nombre,
                m.responsable.email if m.responsable else "",
                m.creado_por.email,
                m.creado_en.strftime("%Y-%m-%d %H:%M") if m.creado_en else "",
            ])
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="reporte_medicamentos.xlsx"'
        wb.save(response)
        return response

    if formato == "pdf" and SimpleDocTemplate:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        data = [[
            "Nombre", "Forma", "Presentación", "Vía", "Laboratorio", "Lote",
            "F. Fab", "F. Venc", "Stock", "P. Compra", "P. Venta", "Estado",
        ]]
        for m in qs:
            data.append([
                m.nombre[:20] if len(m.nombre) > 20 else m.nombre,
                m.forma.nombre[:15] if len(m.forma.nombre) > 15 else m.forma.nombre,
                m.presentacion.nombre[:15] if len(m.presentacion.nombre) > 15 else m.presentacion.nombre,
                m.via_administracion.nombre[:12] if len(m.via_administracion.nombre) > 12 else m.via_administracion.nombre,
                m.laboratorio.nombre[:15] if len(m.laboratorio.nombre) > 15 else m.laboratorio.nombre,
                m.lote,
                str(m.fecha_fabricacion) if m.fecha_fabricacion else "",
                str(m.fecha_vencimiento) if m.fecha_vencimiento else "",
                str(m.stock), str(m.precio_compra), str(m.precio_venta),
                m.estado.nombre,
            ])
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
        ]))
        doc.build([table])
        buffer.seek(0)
        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="reporte_medicamentos.pdf"'
        return response

    return redirect("listar_medicamentos")

@login_required
def editar_medicamento(request, pk):

    if request.user.rol != "Administrador":
        return redirect("login")

    medicamento = Medicamento.objects.filter(pk=pk).first()

    if not medicamento:
        messages.error(request, "Medicamento no encontrado.")
        return redirect("listar_medicamentos")

    if request.method == "POST":

        form = ActualizarMedicamentoForm(request.POST, instance=medicamento)

        if form.is_valid():

            med = form.save()

            MedicamentoHistorial.objects.create(
                medicamento=med,
                accion="ACTUALIZADO",
                usuario=request.user,
                detalle="Medicamento actualizado desde el módulo de gestión."
            )

            messages.success(request, "Medicamento actualizado correctamente.")

            return redirect("listar_medicamentos")

    else:
        form = ActualizarMedicamentoForm(instance=medicamento)

    return render(
        request,
        "products/editar_medicamento.html",
        {
            "form": form,
            "medicamento": medicamento
        }
    )
