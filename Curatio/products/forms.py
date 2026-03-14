from django import forms
from .models import Medicamento, Presentacion
from .models import Proveedor
import re


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
        self.fields["proveedor"].queryset = Proveedor.objects.filter(estado="Activo").order_by("nombre")        

        if self.data and "forma" in self.data:
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
    
class ActualizarMedicamentoForm(forms.ModelForm):

    class Meta:
        model = Medicamento
        exclude = ["requiere_formula", "creado_por", "creado_en"]

        widgets = {
            "fecha_fabricacion": forms.DateInput(attrs={"type": "date"}),
            "fecha_vencimiento": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["presentacion"].queryset = Presentacion.objects.none()
        self.fields["proveedor"].queryset = Proveedor.objects.filter(estado="Activo").order_by("nombre")

        if self.data and "forma" in self.data:
            try:
                forma_id = int(self.data.get("forma"))
                self.fields["presentacion"].queryset = Presentacion.objects.filter(
                    forma_id=forma_id,
                    activo=True
                )
            except (ValueError, TypeError):
                pass

        elif self.instance.pk:
            self.fields["presentacion"].queryset = Presentacion.objects.filter(
                forma=self.instance.forma,
                activo=True
            )

class CrearProveedorForm(forms.ModelForm):

    class Meta:
        model = Proveedor

        exclude = ["creado_por", "creado_en"]

    def clean_nit(self):

        nit = self.cleaned_data.get("nit")

        if not re.match(r'^\d{8,10}-\d$', nit):
            raise forms.ValidationError(
                "Formato de NIT inválido. Ej: 12345678-9"
            )

        return nit

class ActualizarProveedorForm(forms.ModelForm):

    class Meta:
        model = Proveedor
        fields = [
            "nombre",
            "nombre_contacto",
            "telefono_contacto",
            "correo_contacto",
            "direccion",
            "ciudad",
            "estado",
        ]

    def clean(self):
        cleaned = super().clean()

        campos_obligatorios = [
            "nombre",
            "nombre_contacto",
            "telefono_contacto",
            "correo_contacto",
            "estado",
        ]

        for campo in campos_obligatorios:
            valor = cleaned.get(campo)
            if valor is None or str(valor).strip() == "":
                raise forms.ValidationError(f"El campo {campo.replace('_', ' ')} es obligatorio.")

        return cleaned            
