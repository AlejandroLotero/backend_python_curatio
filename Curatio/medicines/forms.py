from django import forms
from .models import Medicine

class MedicineForm(forms.ModelForm):
    """Formulario para crear/editar medicamentos (RFADMIN08)"""
    
    class Meta:
        model = Medicine
        fields = [
            'name',
            'description',
            'active_ingredient',
            'concentration',
            'pharmaceutical_form',
            'presentation',
            'administration_route',
            'laboratory',
            'registration_number',
            'batch_number',
            'stock_quantity',
            'minimum_stock',
            'manufacture_date',
            'expiration_date',
            'purchase_price',
            'sale_price',
            'supplier',
            'requires_formula',
            'state',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Ibuprofeno'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del medicamento'
            }),
            'active_ingredient': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Ibuprofen'
            }),
            'concentration': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 400mg'
            }),
            'pharmaceutical_form': forms.Select(attrs={
                'class': 'form-control'
            }),
            'presentation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Pastilla, Cápsula'
            }),
            'administration_route': forms.Select(attrs={
                'class': 'form-control'
            }),
            'laboratory': forms.Select(attrs={
                'class': 'form-control'
            }),
            'registration_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de registro'
            }),
            'batch_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de lote'
            }),
            'stock_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'minimum_stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'manufacture_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expiration_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'sale_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'supplier': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del proveedor'
            }),
            'requires_formula': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'state': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
