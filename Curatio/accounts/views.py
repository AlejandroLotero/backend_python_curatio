from django.shortcuts import render

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
