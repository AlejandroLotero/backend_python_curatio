#FORMULARIO CON CONFIRMACIÓN DE CORREO

from django import forms
from .models import User

class CrearUsuarioForm(forms.ModelForm):

    confirmar_email = forms.EmailField()

    class Meta:
        model = User
        exclude = ['estado', 'is_active', 'is_staff', 'password']

    def clean(self):
        cleaned_data = super().clean()

        email = cleaned_data.get("email")
        confirmar = cleaned_data.get("confirmar_email")

        if email != confirmar:
            raise forms.ValidationError("Los correos no coinciden.")

        return cleaned_data
