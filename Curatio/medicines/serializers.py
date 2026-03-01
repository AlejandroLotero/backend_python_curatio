from rest_framework import serializers
from .models import Medicine

class MedicineSerializer(serializers.ModelSerializer):
    """
    Serializer para lectura completa de medicamentos
    RFADMIN09: Visualizar medicamento
    RFADMIN13: Datos para reportes
    """
    days_to_expire = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    pharmaceutical_form_display = serializers.CharField(source='get_pharmaceutical_form_display', read_only=True)
    administration_route_display = serializers.CharField(source='get_administration_route_display', read_only=True)
    laboratory_display = serializers.CharField(source='get_laboratory_display', read_only=True)
    state_display = serializers.CharField(source='get_state_display', read_only=True)
    
    class Meta:
        model = Medicine
        fields = [
            'id',
            'name',
            'description',
            'active_ingredient',
            'concentration',
            'pharmaceutical_form',
            'pharmaceutical_form_display',
            'presentation',
            'administration_route',
            'administration_route_display',
            'laboratory',
            'laboratory_display',
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
            'is_active',
            'state',
            'state_display',
            'is_expired',
            'days_to_expire',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'is_expired',
            'days_to_expire',
            'pharmaceutical_form_display',
            'administration_route_display',
            'laboratory_display',
            'state_display',
        ]
    
    def get_days_to_expire(self, obj):
        """Obtiene los días para que expire el medicamento"""
        return obj.days_to_expire()
    
    def get_is_expired(self, obj):
        """Obtiene el estado de caducidad"""
        return obj.is_expired()


class MedicineCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear y actualizar medicamentos
    RFADMIN08: Registrar medicamento
    """
    
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
            'is_active',
            'state',
        ]
    
    def validate(self, data):
        """Validaciones adicionales en el serializer"""
        if data.get('expiration_date') and data.get('manufacture_date'):
            if data['expiration_date'] <= data['manufacture_date']:
                raise serializers.ValidationError(
                    "La fecha de caducidad debe ser posterior a la fecha de manufactura"
                )
        return data
