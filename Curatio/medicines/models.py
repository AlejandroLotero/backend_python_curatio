from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta

# RFADMIN08 - Registrar medicamento
# RFADMIN09 - Visualizar medicamento
# RFADMIN13 - Generar reportes de medicamentos
class Medicine(models.Model):
    """
    Modelo de Medicamento para la gestión del inventario farmacéutico.
    Implementa los requerimientos RFADMIN08 (Registro), RFADMIN09 (Visualización)
    y RFADMIN13 (Reportes)
    """
    
    # === FORMAS FARMACÉUTICAS ===
    PHARMACEUTICAL_FORMS = [
        ('ESPECIAL', 'Especial'),
        ('LIQUIDA', 'Líquida'),
        ('GASEOSA', 'Gaseosa'),
        ('SEMISÓLIDA', 'Semisólida'),
        ('SOLIDA', 'Sólida'),
    ]
    pharmaceutical_form = models.CharField(
        max_length=20, 
        choices=PHARMACEUTICAL_FORMS, 
        default='SOLIDA'
    )
    
    # === PRESENTACIONES POR FORMA FARMACÉUTICA ===
    PRESENTATIONS_ESPECIAL = [
        ('COLIRIO', 'Colirio'),
        ('COLUTORIO', 'Colutorio'),
        ('ENJUAGE_BUCAL', 'Enjuague Bucal'),
        ('DENTIFRICO', 'Dentífrico'),
        ('DESINFECTANTE_ANTISEPTICO', 'Desinfectante - Antiséptico'),
        ('LOCION', 'Loción'),
        ('PARCHE_TRANSDERMICO', 'Parche transdérmico'),
        ('POMADA_OFTALMOLOGICA', 'Pomada oftálmica'),
        ('SOLUCION_NASAL_SPRAY', 'Solución nasal - Spray nasal'),
    ]
    
    PRESENTATIONS_GASEOSA = [
        ('AEROSOL_SPRAY', 'Aerosol - Spray'),
        ('INHALADOR', 'Inhalador'),
        ('NEBULIZADOR', 'Nebulizador'),
    ]
    
    PRESENTATIONS_LIQUIDA = [
        ('ENEMA', 'Enema'),
        ('EMULSION', 'Emulsión'),
        ('GOTAS', 'Gotas'),
        ('INFUSION_CONCENTRADO', 'Infusión - Concentrado para diluir'),
        ('INYECTABLE_AMPOLLA', 'Inyectable - Ampolla - Frasco ámpula'),
        ('JARABE', 'Jarabe'),
        ('SOLUCION_ORAL', 'Solución oral'),
        ('SUSPENSION', 'Suspensión'),
    ]
    
    PRESENTATIONS_SEMISÓLIDA = [
        ('CREMA', 'Crema'),
        ('GEL', 'Gel'),
        ('LINIMENTO_BALSAMO', 'Linimento - Bálsamo'),
        ('PASTA', 'Pasta'),
        ('UNGÜENTO_POMADA', 'Ungüento - Pomada'),
    ]
    
    PRESENTATIONS_SOLIDA = [
        ('CAPSULA', 'Cápsula'),
        ('GRAGEA', 'Gragea'),
        ('GRANULADO', 'Granulado'),
        ('IMPLANTE', 'Implante'),
        ('PASTILLA', 'Pastilla'),
        ('PILDORA', 'Píldora'),
        ('POLVO', 'Polvo'),
        ('SUPOSITORIO', 'Supositorio'),
        ('OVULO', 'Óvulo'),
    ]
    
    presentation = models.CharField(max_length=100, default='')
    
    # === VÍA DE ADMINISTRACIÓN ===
    ADMINISTRATION_ROUTES = [
        ('BUCAL', 'Bucal'),
        ('CUTANEA', 'Cutánea'),
        ('INHALATORIA', 'Inhalatoria'),
        ('INTRADERMICA', 'Intradérmica'),
        ('INTRAMUSCULAR', 'Intramuscular'),
        ('INTRAVENOSA', 'Intravenosa'),
        ('NASAL', 'Nasal'),
        ('OFTALMOLOGICA', 'Oftálmica'),
        ('ORAL', 'Oral'),
        ('OTICA', 'Ótica'),
        ('RECTAL', 'Rectal'),
        ('SUBCUTANEA', 'Subcutánea'),
        ('SUBLINGUAL', 'Sublingual'),
        ('TRANSDERMICA', 'Transdérmica'),
        ('URETRAL', 'Uretral'),
        ('VAGINAL', 'Vaginal'),
    ]
    administration_route = models.CharField(
        max_length=20,
        choices=ADMINISTRATION_ROUTES,
        default='ORAL'
    )
    
    # === INFORMACIÓN BÁSICA ===
    name = models.CharField(max_length=200, unique=True, db_index=True)
    description = models.TextField(blank=True, default='')
    
    # === DATOS FARMACÉUTICOS ===
    active_ingredient = models.CharField(max_length=200, help_text="Componente activo del medicamento")
    concentration = models.CharField(max_length=100, help_text="Ej: 500mg")
    
    # === LABORATORIO ===
    LABORATORIES = [
        ('ABBOTT', 'Abbott Laboratories de Colombia S.A.'),
        ('ANDROMACO', 'Andromaco'),
        ('BAGO', 'Bagó'),
        ('BAYER', 'Bayer S.A.'),
        ('BLASKOV', 'Blaskov S.A.'),
        ('BOEHRINGER', 'Boehringer Ingelheim Ltda.'),
        ('COLPHARMA', 'Colpharma S.A.'),
        ('DISANFAR', 'Disanfar S.A.'),
        ('ELI_LILLY', 'Eli Lilly Interamérica Inc.'),
        ('FARMA_COLOMBIA', 'Farma de Colombia S.A.S.'),
        ('GENFAR', 'Genfar S.A.'),
        ('GSK', 'GlaxoSmithKline (GSK)'),
        ('GRUNENTHAL', 'Grünenthal de Colombia S.A.'),
        ('JOHNSON', 'Johnson & Johnson de Colombia S.A.'),
        ('LAFRANCOL', 'Lafrancol S.A.S.'),
        ('LAPROFF', 'Laproff S.A.'),
        ('LA_SANTE', 'La Santé S.A.'),
        ('MERCK', 'Merck Sharp & Dohme (MSD)'),
        ('MK', 'MK'),
        ('NOVARTIS', 'Novartis de Colombia S.A.'),
        ('PFIZER', 'Pfizer Ltda.'),
        ('PROCAPS', 'ProCaps S.A.S.'),
        ('ROCHE', 'Roche S.A.'),
        ('ROPSOHN', 'Ropsohn Therapeutics S.A.'),
        ('SANOFI', 'Sanofi Aventis de Colombia S.A.'),
        ('SERVIER', 'Servier de Colombia Ltda.'),
        ('SYNTHESIS', 'Synthesis S.A.'),
        ('TECNOQUIMICAS', 'Tecnoquímicas S.A. (TQ)'),
    ]
    laboratory = models.CharField(max_length=50, choices=LABORATORIES, default='ABBOTT')
    registration_number = models.CharField(max_length=100, unique=True, db_index=True)
    
    # === LOTE Y FECHAS ===
    batch_number = models.CharField(max_length=100, db_index=True, default='BATCH-001')
    manufacture_date = models.DateField()
    expiration_date = models.DateField()
    
    # === INVENTARIO ===
    stock_quantity = models.IntegerField(default=0)
    minimum_stock = models.IntegerField(default=10)
    
    # === PRECIOS ===
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    
    # === PROVEEDOR ===
    supplier = models.CharField(max_length=200, default='Por Definir')
    
    # === FÓRULA ===
    requires_formula = models.BooleanField(default=False)
    
    # === ESTADOS PARA REPORTES (RFADMIN13) ===
    STATE_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('VENCIDO', 'Vencido'),
        ('AGOTADO', 'Agotado'),
        ('SUSPENDIDO', 'Suspendido'),
    ]
    state = models.CharField(
        max_length=20, 
        choices=STATE_CHOICES, 
        default='ACTIVO',
        db_index=True
    )
    
    # === COMPATIBILIDAD ANTERIOR ===
    is_active = models.BooleanField(default=True, db_index=True)
    
    # === AUDITORÍA ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def clean(self):
        """Validaciones de reglas de negocio"""
        if self.expiration_date <= self.manufacture_date:
            raise ValidationError("La fecha de caducidad debe ser posterior a la fecha de manufactura")
        
        if self.minimum_stock < 0:
            raise ValidationError("El stock mínimo no puede ser negativo")
        
        if self.purchase_price < 0:
            raise ValidationError("El precio de compra no puede ser negativo")
        
        if self.sale_price < 0:
            raise ValidationError("El precio de venta no puede ser negativo")
        
        # Validar presentación según forma farmacéutica
        valid_presentations = {
            'ESPECIAL': [v[0] for v in self.PRESENTATIONS_ESPECIAL],
            'LIQUIDA': [v[0] for v in self.PRESENTATIONS_LIQUIDA],
            'GASEOSA': [v[0] for v in self.PRESENTATIONS_GASEOSA],
            'SEMISÓLIDA': [v[0] for v in self.PRESENTATIONS_SEMISÓLIDA],
            'SOLIDA': [v[0] for v in self.PRESENTATIONS_SOLIDA],
        }
        
        if self.pharmaceutical_form in valid_presentations:
            if self.presentation not in valid_presentations[self.pharmaceutical_form]:
                raise ValidationError(
                    f"La presentación '{self.presentation}' no es válida para la forma farmacéutica '{self.pharmaceutical_form}'"
                )
    
    def is_expired(self):
        """Verifica si el medicamento ha expirado"""
        return timezone.now().date() > self.expiration_date
    
    def days_to_expire(self):
        """Retorna la cantidad de días para expirar"""
        delta = self.expiration_date - timezone.now().date()
        return delta.days
    
    def update_state_automatically(self):
        """
        Actualiza automáticamente el estado del medicamento según las reglas:
        - VENCIDO si la fecha de caducidad ha pasado
        - AGOTADO si el stock es 0
        - ACTIVO si cumple condiciones normales
        """
        if self.is_expired():
            self.state = 'VENCIDO'
        elif self.stock_quantity == 0:
            self.state = 'AGOTADO'
        elif self.state != 'SUSPENDIDO':  # No afectar medicamentos suspendidos manualmente
            self.state = 'ACTIVO'
        self.save()
    
    def __str__(self):
        return f"{self.name} - {self.concentration}"
    
    class Meta:
        verbose_name = 'Medicamento'
        verbose_name_plural = 'Medicamentos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['registration_number']),
            models.Index(fields=['batch_number']),
            models.Index(fields=['state']),
            models.Index(fields=['is_active']),
            models.Index(fields=['expiration_date']),
        ]
