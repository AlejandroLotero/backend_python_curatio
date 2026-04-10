# from django import forms
# from .models import Medicamento, Presentacion, Proveedor
# import re


# # =========================
# # FORMULARIO CREAR MEDICAMENTO
# # =========================

# class CrearMedicamentoForm(forms.ModelForm):
#     class Meta:
#         model = Medicamento
#         exclude = ["requiere_formula", "creado_por", "creado_en", "actualizado_en", "laboratorio_texto"]
#         widgets = {
#             "fecha_fabricacion": forms.DateInput(attrs={"type": "date"}),
#             "fecha_vencimiento": forms.DateInput(attrs={"type": "date"}),
#         }

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         # Solo proveedores activos pueden surtir medicamentos
#         self.fields["proveedor"].queryset = Proveedor.objects.filter(estado="Activo").order_by("nombre")

#         # Por defecto, presentación vacía hasta elegir forma farmacéutica
#         self.fields["presentacion"].queryset = Presentacion.objects.none()

#         if self.data and "forma" in self.data:
#             try:
#                 forma_id = int(self.data.get("forma"))
#                 self.fields["presentacion"].queryset = Presentacion.objects.filter(
#                     forma_id=forma_id,
#                     activo=True
#                 ).order_by("nombre")
#             except (ValueError, TypeError):
#                 pass
#         elif self.instance.pk and self.instance.forma_id:
#             self.fields["presentacion"].queryset = Presentacion.objects.filter(
#                 forma_id=self.instance.forma_id,
#                 activo=True
#             ).order_by("nombre")

#     def clean_stock(self):
#         stock = self.cleaned_data.get("stock")
#         if stock is None:
#             raise forms.ValidationError("Stock obligatorio.")
#         if stock < 0 or stock > 999:
#             raise forms.ValidationError("El stock debe estar entre 0 y 999.")
#         return stock

#     def clean(self):
#         cleaned = super().clean()

#         pc = cleaned.get("precio_compra")
#         pv = cleaned.get("precio_venta")

#         if pc is not None and pc < 0:
#             raise forms.ValidationError("El precio de compra no puede ser negativo.")

#         if pv is not None and pv < 0:
#             raise forms.ValidationError("El precio de venta no puede ser negativo.")

#         return cleaned


# # =========================
# # FORMULARIO ACTUALIZAR MEDICAMENTO
# # =========================

# class ActualizarMedicamentoForm(forms.ModelForm):
#     class Meta:
#         model = Medicamento
#         exclude = ["requiere_formula", "creado_por", "creado_en", "actualizado_en", "laboratorio_texto"]
#         widgets = {
#             "fecha_fabricacion": forms.DateInput(attrs={"type": "date"}),
#             "fecha_vencimiento": forms.DateInput(attrs={"type": "date"}),
#         }

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         self.fields["proveedor"].queryset = Proveedor.objects.filter(estado="Activo").order_by("nombre")
#         self.fields["presentacion"].queryset = Presentacion.objects.none()

#         if self.data and "forma" in self.data:
#             try:
#                 forma_id = int(self.data.get("forma"))
#                 self.fields["presentacion"].queryset = Presentacion.objects.filter(
#                     forma_id=forma_id,
#                     activo=True
#                 ).order_by("nombre")
#             except (ValueError, TypeError):
#                 pass
#         elif self.instance.pk:
#             self.fields["presentacion"].queryset = Presentacion.objects.filter(
#                 forma=self.instance.forma,
#                 activo=True
#             ).order_by("nombre")


# # =========================
# # FORMULARIO CREAR PROVEEDOR
# # =========================

# class CrearProveedorForm(forms.ModelForm):
#     class Meta:
#         model = Proveedor
#         exclude = ["creado_por", "creado_en", "actualizado_en"]

#     def clean_nit(self):
#         nit = self.cleaned_data.get("nit")

#         if not re.match(r'^\d{8,10}-\d$', nit or ""):
#             raise forms.ValidationError(
#                 "Formato de NIT inválido. Ej: 12345678-9"
#             )

#         return nit


# # =========================
# # FORMULARIO ACTUALIZAR PROVEEDOR
# # =========================

# class ActualizarProveedorForm(forms.ModelForm):
#     class Meta:
#         model = Proveedor
#         fields = [
#             "nombre",
#             "nombre_contacto",
#             "telefono_contacto",
#             "correo_contacto",
#             "direccion",
#             "ciudad",
#             "estado",
#         ]

#     def clean(self):
#         cleaned = super().clean()

#         campos_obligatorios = [
#             "nombre",
#             "nombre_contacto",
#             "telefono_contacto",
#             "correo_contacto",
#             "estado",
#         ]

#         for campo in campos_obligatorios:
#             valor = cleaned.get(campo)
#             if valor is None or str(valor).strip() == "":
#                 raise forms.ValidationError(
#                     f"El campo {campo.replace('_', ' ')} es obligatorio."
#                 )

#         return cleaned

from django import forms
from .models import Medicamento, Presentacion, Proveedor
import re


# =========================
# FORMULARIO CREAR MEDICAMENTO
# =========================

class CrearMedicamentoForm(forms.ModelForm):
    class Meta:
        model = Medicamento
        # No excluimos imagen porque sí debe poder cargarse desde el formulario.
        exclude = [
            "requiere_formula",
            "creado_por",
            "creado_en",
            "actualizado_en",
            "laboratorio_texto",
        ]
        widgets = {
            "fecha_fabricacion": forms.DateInput(attrs={"type": "date"}),
            "fecha_vencimiento": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Solo proveedores activos pueden surtir medicamentos
        self.fields["proveedor"].queryset = Proveedor.objects.filter(
            estado="Activo"
        ).order_by("nombre")

        # Por defecto, presentación vacía hasta elegir forma farmacéutica
        self.fields["presentacion"].queryset = Presentacion.objects.none()

        if self.data and "forma" in self.data:
            try:
                forma_id = int(self.data.get("forma"))
                self.fields["presentacion"].queryset = Presentacion.objects.filter(
                    forma_id=forma_id,
                    activo=True
                ).order_by("nombre")
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.forma_id:
            self.fields["presentacion"].queryset = Presentacion.objects.filter(
                forma_id=self.instance.forma_id,
                activo=True
            ).order_by("nombre")

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


# =========================
# FORMULARIO ACTUALIZAR MEDICAMENTO
# =========================

class ActualizarMedicamentoForm(forms.ModelForm):
    class Meta:
        model = Medicamento
        exclude = [
            "requiere_formula",
            "creado_por",
            "creado_en",
            "actualizado_en",
            "laboratorio_texto",
        ]
        widgets = {
            "fecha_fabricacion": forms.DateInput(attrs={"type": "date"}),
            "fecha_vencimiento": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["proveedor"].queryset = Proveedor.objects.filter(
            estado="Activo"
        ).order_by("nombre")
        self.fields["presentacion"].queryset = Presentacion.objects.none()

        if self.data and "forma" in self.data:
            try:
                forma_id = int(self.data.get("forma"))
                self.fields["presentacion"].queryset = Presentacion.objects.filter(
                    forma_id=forma_id,
                    activo=True
                ).order_by("nombre")
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields["presentacion"].queryset = Presentacion.objects.filter(
                forma=self.instance.forma,
                activo=True
            ).order_by("nombre")


# # =========================
# # FORMULARIO CREAR PROVEEDOR
# # =========================

# class CrearProveedorForm(forms.ModelForm):
#     class Meta:
#         model = Proveedor
#         exclude = ["creado_por", "creado_en", "actualizado_en"]

#     def clean_nit(self):
#         nit = self.cleaned_data.get("nit")

#         if not re.match(r'^\d{8,10}-\d$', nit or ""):
#             raise forms.ValidationError(
#                 "Formato de NIT inválido. Ej: 12345678-9"
#             )

#         return nit


# # =========================
# # FORMULARIO ACTUALIZAR PROVEEDOR
# # =========================

# class ActualizarProveedorForm(forms.ModelForm):
#     class Meta:
#         model = Proveedor
#         fields = [
#             "nombre",
#             "nombre_contacto",
#             "telefono_contacto",
#             "correo_contacto",
#             "direccion",
#             "ciudad",
#             "estado",
#         ]

#     def clean(self):
#         cleaned = super().clean()

#         campos_obligatorios = [
#             "nombre",
#             "nombre_contacto",
#             "telefono_contacto",
#             "correo_contacto",
#             "estado",
#         ]

#         for campo in campos_obligatorios:
#             valor = cleaned.get(campo)
#             if valor is None or str(valor).strip() == "":
#                 raise forms.ValidationError(
#                     f"El campo {campo.replace('_', ' ')} es obligatorio."
#                 )

#         return cleaned

# =========================
# FORMULARIO CREAR PROVEEDOR
# =========================

class CrearProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = [
            "nit",
            "nombre",
            "razon_social",
            "nombre_contacto",
            "telefono_contacto",
            "correo_contacto",
            "direccion",
            "ciudad",
            "estado",
        ]

    def clean_nit(self):
        """
        Valida formato del NIT:
        - 8 a 10 dígitos
        - un guion
        - un dígito de verificación
        """
        nit = (self.cleaned_data.get("nit") or "").strip()

        if not re.fullmatch(r"^\d{8,10}-\d$", nit):
            raise forms.ValidationError(
                "El NIT debe tener entre 8 y 10 dígitos, un guion y un dígito verificador. Ejemplo: 80000000-0."
            )

        if Proveedor.objects.filter(nit=nit).exists():
            raise forms.ValidationError("Ya existe un proveedor registrado con este NIT.")

        return nit

    def clean_telefono_contacto(self):
        telefono = (self.cleaned_data.get("telefono_contacto") or "").strip()

        if not telefono:
            raise forms.ValidationError("El teléfono de contacto es obligatorio.")

        if not telefono.isdigit():
            raise forms.ValidationError("El teléfono de contacto debe contener solo números.")

        return telefono

    def clean_estado(self):
        """
        Si el cliente no envía estado, se fuerza el valor por defecto Activo.
        """
        estado = (self.cleaned_data.get("estado") or "").strip()
        return estado or "Activo"


# =========================
# FORMULARIO ACTUALIZAR PROVEEDOR
# =========================

class ActualizarProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = [
            # El NIT se deja visible en el modelo, pero no editable desde la API.
            "nombre",
            "razon_social",
            "nombre_contacto",
            "telefono_contacto",
            "correo_contacto",
            "direccion",
            "ciudad",
            "estado",
        ]

    def clean_telefono_contacto(self):
        telefono = (self.cleaned_data.get("telefono_contacto") or "").strip()

        if not telefono:
            raise forms.ValidationError("El teléfono de contacto es obligatorio.")

        if not telefono.isdigit():
            raise forms.ValidationError("El teléfono de contacto debe contener solo números.")

        return telefono

    def clean_estado(self):
        estado = (self.cleaned_data.get("estado") or "").strip()

        if estado not in ("Activo", "Inactivo"):
            raise forms.ValidationError('Debe ser "Activo" o "Inactivo".')

        return estado