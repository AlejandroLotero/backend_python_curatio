from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

from accounts.models import User
from products.models import Medicamento

from .models import Venta, VentaLinea


class BaseVentaLineaFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        activas = []
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            data = form.cleaned_data
            if not data or data.get("DELETE"):
                continue
            if data.get("medicamento") and data.get("cantidad"):
                activas.append(form)
        if not activas:
            raise ValidationError(
                "Debe incluir al menos un medicamento con cantidad válida."
            )


class VentaForm(forms.ModelForm):
    """
    Al crear, el estado siempre es Pendiente (no se expone Completada sin confirmaciones).
    """

    class Meta:
        model = Venta
        fields = (
            "numero_factura",
            "cliente",
            "subtotal",
            "iva",
            "descuento",
            "total",
            "tipo_pago",
        )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["cliente"].queryset = User.objects.filter(
            rol="Cliente",
            estado=True,
            is_active=True,
        ).order_by("nombre")
        for name in ("subtotal", "iva", "descuento", "total"):
            self.fields[name].widget.attrs.setdefault("step", "0.01")
            self.fields[name].widget.attrs.setdefault("min", "0")

    def clean_numero_factura(self):
        v = (self.cleaned_data.get("numero_factura") or "").strip()
        if not v:
            raise ValidationError("El número de factura es obligatorio.")
        return v

    def clean_descuento(self):
        d = self.cleaned_data.get("descuento")
        if d is None:
            return Decimal("0")
        return d


class VentaLineaForm(forms.ModelForm):
    class Meta:
        model = VentaLinea
        fields = ("medicamento", "cantidad")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["medicamento"].queryset = (
            Medicamento.objects.filter(
                estado__nombre="Activo",
                stock__gt=0,
            )
            .select_related("presentacion", "estado")
            .order_by("nombre")
        )

    def clean(self):
        cleaned = super().clean()
        med = cleaned.get("medicamento")
        cantidad = cleaned.get("cantidad")
        if med and cantidad:
            if not med.puede_venderse:
                raise ValidationError("El medicamento seleccionado no está disponible para venta.")
            if cantidad > med.stock:
                raise ValidationError(
                    f"Stock insuficiente: hay {med.stock} unidades de «{med.nombre}»."
                )
        return cleaned


VentaLineaFormSet = inlineformset_factory(
    Venta,
    VentaLinea,
    form=VentaLineaForm,
    formset=BaseVentaLineaFormSet,
    extra=3,
    can_delete=True,
)
