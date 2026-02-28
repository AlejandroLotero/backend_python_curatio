from django.shortcuts import render
from django.shortcuts import get_object_or_404
from .models import User
# Create your views here.
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    return render(request, 'accounts/dashboard.html')

# RQ02: Vista para el dashboard, protegida por login_required para asegurar que solo usuarios autenticados puedan acceder. JHONIER

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from .forms import CrearUsuarioForm
from .utils import generar_password
from django.core.paginator import Paginator
from django.db.models import Q

@login_required
def crear_usuario(request):

    #Validar rol ADMIN
    if request.user.rol != "Administrador":
        return redirect("login")

    if request.method == "POST":
        form = CrearUsuarioForm(request.POST, request.FILES)

        if form.is_valid():
            user = form.save(commit=False)

            password = generar_password()
            user.set_password(password)
            user.save()

            #Enviar correo
            send_mail(
                subject="Cuenta creada",
                message=f"Su contraseña es: {password}",
                from_email=None,
                recipient_list=[user.email],
            )

            return redirect("lista_usuarios")
    else:
        form = CrearUsuarioForm()

    return render(request, "accounts/crear_usuario.html", {"form": form})

def ver_usuario(request, user_id=None):
    """
    RQ: Visualizar cuenta de usuario
    ADMIN puede ver cualquier usuario
    Otros usuarios solo su cuenta
    """

    # ADMIN puede ver otros usuarios
    if request.user.rol == "Administrador" and user_id:
        usuario = get_object_or_404(User, id=user_id)
    else:
        # Usuario normal solo se ve a sí mismo
        usuario = request.user

    return render(request, "accounts/ver_usuario.html", {"usuario": usuario})


@login_required
def lista_usuarios(request):
    # Validar rol ADMIN
    if request.user.rol != "Administrador":
        return redirect("login")

    qs = User.objects.all()

    # --- Filtros (opcionales) ---
    nombre = (request.GET.get("nombre") or "").strip()
    rol = (request.GET.get("rol") or "").strip()
    estado = (request.GET.get("estado") or "").strip()
    documento = (request.GET.get("documento") or "").strip()

    if nombre:
        qs = qs.filter(nombre__icontains=nombre)

    if rol:
        qs = qs.filter(rol=rol)

    # estado: "1" activo, "0" inactivo (o "true"/"false")
    if estado != "":
        if estado in ["1", "true", "True", "activo", "Activo"]:
            qs = qs.filter(estado=True)
        elif estado in ["0", "false", "False", "inactivo", "Inactivo"]:
            qs = qs.filter(estado=False)

    if documento:
        # permite buscar por número o por tipo_doc (por ejemplo "CC")
        qs = qs.filter(
            Q(numero_documento__icontains=documento) |
            Q(tipo_documento__icontains=documento)
        )

    # --- Orden por defecto ---
    qs = qs.order_by("nombre")

    # --- Paginación ---
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

#Importaciones para Generación de reportes de usuarios 
from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from io import BytesIO
from django.contrib import messages

@login_required
def generar_reporte_usuarios(request):

    # 🔐 Validar rol ADMIN
    if request.user.rol != "Administrador":
        return redirect("login")

    formato = request.GET.get("formato")  # excel o pdf

    # ===== Reutilizamos lógica de filtros =====
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

    # 🔎 Si no hay datos
    if not qs.exists():
        messages.warning(request, "No existen datos para el filtro seleccionado.")
        return redirect("lista_usuarios")

    # =========================
    # 📊 GENERAR EXCEL
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
    # 📄 GENERAR PDF
    # =========================
    elif formato == "pdf":

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
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
        ]))

        elements.append(table)
        doc.build(elements)

        buffer.seek(0)

        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="reporte_usuarios.pdf"'

        return response

    return redirect("lista_usuarios")


