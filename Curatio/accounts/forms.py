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