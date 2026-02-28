from django import forms
from .models import Medicamento, Presentacion

class CrearMedicamentoForm(forms.ModelForm):
    class Meta:
        model = Medicamento
        exclude = ["requiere_formula", "creado_por", "creado_en"]
        widgets = {
            "fecha_fabricacion": forms.DateInput(attrs={"type": "date"}),
            "fecha_vencimiento": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Por defecto, presentación vacía hasta que elijan forma
        self.fields["presentacion"].queryset = Presentacion.objects.none()

        if "forma" in self.data:
            try:
                forma_id = int(self.data.get("forma"))
                self.fields["presentacion"].queryset = Presentacion.objects.filter(forma_id=forma_id, activo=True).order_by("nombre")
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.forma_id:
            self.fields["presentacion"].queryset = Presentacion.objects.filter(forma_id=self.instance.forma_id, activo=True).order_by("nombre")

    def clean_stock(self):
        stock = self.cleaned_data.get("stock")
        if stock is None:
            raise forms.ValidationError("Stock obligatorio.")
        if stock < 0 or stock > 999:
            raise forms.ValidationError("El stock debe estar entre 0 y 999.")
        return stock

    def clean(self):
        cleaned = super().clean()
        pc = cleaned.get("precio_compra")
        pv = cleaned.get("precio_venta")
        if pc is not None and pc < 0:
            raise forms.ValidationError("El precio de compra no puede ser negativo.")
        if pv is not None and pv < 0:
            raise forms.ValidationError("El precio de venta no puede ser negativo.")
        return cleaned