from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages

from .forms import CrearMedicamentoForm
from .models import Presentacion, MedicamentoHistorial

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