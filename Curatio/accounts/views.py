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
