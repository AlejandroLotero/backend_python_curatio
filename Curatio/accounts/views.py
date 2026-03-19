from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.contrib import messages

from openpyxl import Workbook
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from io import BytesIO

from .models import User, BitacoraUsuario
from .forms import CrearUsuarioForm
from .utils import generar_password


# =========================
# DASHBOARD
# =========================

@login_required
def dashboard(request):
    """
    Dashboard principal del sistema.
    Protegido con sesión activa.
    """
    return render(request, "accounts/dashboard.html")


# =========================
# CREAR USUARIO
# =========================

@login_required
def crear_usuario(request):
    """
    RQ creación de usuario.
    Solo ADMIN puede registrar nuevos usuarios.
    La contraseña se genera automáticamente y se envía al correo.
    """
    if request.user.rol != "Administrador":
        return redirect("login")

    if request.method == "POST":
        form = CrearUsuarioForm(request.POST, request.FILES)

        if form.is_valid():
            user = form.save(commit=False)

            # Estado de negocio y estado técnico
            user.estado = True
            user.is_active = True

            # Si es administrador, permitir acceso al panel/admin del sistema
            if user.rol == "Administrador":
                user.is_staff = True

            password = generar_password()
            user.set_password(password)
            user.save()

            # Registrar en bitácora
            BitacoraUsuario.objects.create(
                admin=request.user,
                usuario=user,
                accion="CREADO",
                motivo="Usuario creado desde el módulo de gestión de usuarios."
            )

            # Envío de correo con contraseña generada
            send_mail(
                subject="Cuenta creada",
                message=f"Su contraseña es: {password}",
                from_email=None,
                recipient_list=[user.email],
            )

            messages.success(request, "Usuario creado exitosamente.")
            return redirect("lista_usuarios")
    else:
        form = CrearUsuarioForm()

    return render(request, "accounts/crear_usuario.html", {"form": form})


# =========================
# VER PERFIL / VER USUARIO
# =========================

@login_required
def ver_usuario(request, user_id=None):
    """
    Visualizar cuenta de usuario.
    ADMIN puede ver cualquier usuario.
    Otros usuarios solo su propia cuenta.
    """
    if request.user.rol == "Administrador" and user_id:
        usuario = get_object_or_404(User, id=user_id)
    else:
        usuario = request.user

    return render(request, "accounts/ver_usuario.html", {"usuario": usuario})


# =========================
# CAMBIAR ESTADO DE USUARIO
# =========================

@login_required
def cambiar_estado_usuario(request, user_id):
    """
    Activar / desactivar usuario.
    Solo ADMIN.
    No se permite desactivar a otro administrador.
    """
    if request.user.rol != "Administrador":
        return redirect("login")

    usuario = get_object_or_404(User, id=user_id)

    # No permitir desactivar administradores
    if usuario.rol == "Administrador":
        messages.error(request, "No se puede desactivar un administrador.")
        return redirect("lista_usuarios")

    motivo = request.POST.get("motivo", "").strip()

    # Estado de negocio y estado técnico sincronizados
    usuario.estado = not usuario.estado
    usuario.is_active = usuario.estado
    usuario.save(update_fields=["estado", "is_active", "actualizado_en"])

    BitacoraUsuario.objects.create(
        admin=request.user,
        usuario=usuario,
        accion="ACTIVADO" if usuario.estado else "DESACTIVADO",
        motivo=motivo
    )

    messages.success(request, "Cuenta actualizada exitosamente.")
    return redirect("lista_usuarios")


# =========================
# LISTAR USUARIOS
# =========================

@login_required
def lista_usuarios(request):
    """
    RFADMIN06 - Listar usuarios
    Solo ADMIN.
    Filtros: nombre, rol, estado, documento.
    Orden alfabético por defecto.
    Paginación de 20 registros.
    """
    if request.user.rol != "Administrador":
        return redirect("login")

    qs = User.objects.all()

    nombre = (request.GET.get("nombre") or "").strip()
    rol = (request.GET.get("rol") or "").strip()
    estado = (request.GET.get("estado") or "").strip()
    documento = (request.GET.get("documento") or "").strip()

    if nombre:
        qs = qs.filter(nombre__icontains=nombre)

    if rol:
        qs = qs.filter(rol=rol)

    if estado != "":
        if estado in ["1", "true", "True", "activo", "Activo"]:
            qs = qs.filter(estado=True)
        elif estado in ["0", "false", "False", "inactivo", "Inactivo"]:
            qs = qs.filter(estado=False)

    if documento:
        qs = qs.filter(
            Q(numero_documento__icontains=documento) |
            Q(tipo_documento__icontains=documento)
        )

    qs = qs.order_by("nombre")

    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "nombre": nombre,
        "rol": rol,
        "estado": estado,
        "documento": documento,
        "roles": User.ROLES,
    }
    return render(request, "accounts/lista_usuarios.html", context)


# =========================
# REPORTE DE USUARIOS
# =========================

@login_required
def generar_reporte_usuarios(request):
    """
    Exportar usuarios en Excel o PDF.
    Reutiliza los mismos filtros de la lista.
    Solo ADMIN.
    """
    if request.user.rol != "Administrador":
        return redirect("login")

    formato = request.GET.get("formato")

    qs = User.objects.all()

    nombre = (request.GET.get("nombre") or "").strip()
    rol = (request.GET.get("rol") or "").strip()
    estado = (request.GET.get("estado") or "").strip()
    documento = (request.GET.get("documento") or "").strip()

    if nombre:
        qs = qs.filter(nombre__icontains=nombre)

    if rol:
        qs = qs.filter(rol=rol)

    if estado != "":
        if estado in ["1", "true", "True", "activo", "Activo"]:
            qs = qs.filter(estado=True)
        elif estado in ["0", "false", "False", "inactivo", "Inactivo"]:
            qs = qs.filter(estado=False)

    if documento:
        qs = qs.filter(
            Q(numero_documento__icontains=documento) |
            Q(tipo_documento__icontains=documento)
        )

    if not qs.exists():
        messages.warning(request, "No existen datos para el filtro seleccionado.")
        return redirect("lista_usuarios")

    # =========================
    # GENERAR EXCEL
    # =========================
    if formato == "excel":
        wb = Workbook()
        ws = wb.active
        ws.title = "Reporte Usuarios"

        headers = [
            "Nombre completo",
            "Tipo documento",
            "Número documento",
            "Tipo usuario",
            "Fecha inicio",
            "Fecha finalización",
            "Correo electrónico",
            "Teléfono",
            "Dirección",
            "Estado",
        ]
        ws.append(headers)

        for u in qs:
            ws.append([
                u.nombre,
                u.tipo_documento,
                u.numero_documento,
                u.rol,
                u.fecha_inicio.strftime("%Y-%m-%d") if u.fecha_inicio else "",
                u.fecha_fin.strftime("%Y-%m-%d") if u.fecha_fin else "",
                u.email,
                u.telefono,
                u.direccion,
                "Activo" if u.estado else "Inactivo",
            ])

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="reporte_usuarios.xlsx"'
        wb.save(response)
        return response

    # =========================
    # GENERAR PDF
    # =========================
    if formato == "pdf":
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        data = [[
            "Nombre",
            "Tipo Doc",
            "Número",
            "Rol",
            "Inicio",
            "Fin",
            "Email",
            "Teléfono",
            "Dirección",
            "Estado",
        ]]

        for u in qs:
            data.append([
                u.nombre,
                u.tipo_documento,
                u.numero_documento,
                u.rol,
                str(u.fecha_inicio or ""),
                str(u.fecha_fin or ""),
                u.email,
                u.telefono,
                u.direccion,
                "Activo" if u.estado else "Inactivo",
            ])

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
        ]))

        elements.append(table)
        doc.build(elements)

        buffer.seek(0)

        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="reporte_usuarios.pdf"'
        return response

    return redirect("lista_usuarios")