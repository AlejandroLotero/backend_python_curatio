# FORMULARIOS DE USUARIOS
# RQ relacionados con creación y validación de cuentas

from django import forms
from .models import User


class CrearUsuarioForm(forms.ModelForm):
    """
    Formulario de creación de usuario con confirmación de correo.
    La contraseña se genera desde backend.
    """

    confirmar_email = forms.EmailField(label="Confirmar correo")

    class Meta:
        model = User
        exclude = [
            "estado",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
            "last_login",
            "password",
            "creado_en",
            "actualizado_en",
        ]

    def clean(self):
        cleaned_data = super().clean()

        email = cleaned_data.get("email")
        confirmar = cleaned_data.get("confirmar_email")

        if email and confirmar and email != confirmar:
            raise forms.ValidationError("Los correos no coinciden.")

        return cleaned_data


class EditarUsuarioAdminForm(forms.ModelForm):
    """
    Edición de cuenta por administrador (RFADMIN04).
    Sin confirmación de correo; valida unicidad de email y documento respecto a otros usuarios.
    """

    class Meta:
        model = User
        fields = [
            "nombre",
            "tipo_documento",
            "numero_documento",
            "rol",
            "fecha_inicio",
            "fecha_fin",
            "email",
            "telefono",
            "telefono_secundario",
            "direccion",
            "estado",
        ]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            return email
        qs = User.objects.filter(email__iexact=email.strip())
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ya existe un usuario con este correo electrónico.")
        return email

    def clean_numero_documento(self):
        numero = (self.cleaned_data.get("numero_documento") or "").strip()
        if not numero:
            raise forms.ValidationError("Este campo es obligatorio.")
        qs = User.objects.filter(numero_documento=numero)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("El número de documento ya está en uso.")
        return numero

    def save(self, commit=True):
        user = super().save(commit=False)
        user.estado = bool(user.estado)
        user.is_active = user.estado
        if commit:
            user.save()
        return user