from django.contrib import admin
from .models import Medicine


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'registration_number',
        'concentration',
        'laboratory',
        'stock_quantity',
        'state',
        'is_active',
        'expiration_date',
    ]
    list_filter = ['state', 'is_active', 'created_at', 'laboratory']
    search_fields = ['name', 'registration_number', 'active_ingredient']
    readonly_fields = ['created_at', 'updated_at', 'is_expired', 'days_to_expire']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Datos Farmacéuticos', {
            'fields': ('active_ingredient', 'concentration', 'presentation')
        }),
        ('Registro y Laboratorio', {
            'fields': ('laboratory', 'registration_number')
        }),
        ('Inventario', {
            'fields': ('stock_quantity', 'minimum_stock', 'unit_price')
        }),
        ('Fechas', {
            'fields': ('manufacture_date', 'expiration_date', 'is_expired', 'days_to_expire')
        }),
        ('Estado', {
            'fields': ('state',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_expired(self, obj):
        """Columna personalizada para mostrar si está expirado"""
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Expirado'
    
    def days_to_expire(self, obj):
        """Columna personalizada para mostrar días para expirar"""
        days = obj.days_to_expire()
        if days < 0:
            return f'Expirado hace {abs(days)} días'
        elif days == 0:
            return 'Expira hoy'
        else:
            return f'Expira en {days} días'
    days_to_expire.short_description = 'Tiempo a Vencimiento'
