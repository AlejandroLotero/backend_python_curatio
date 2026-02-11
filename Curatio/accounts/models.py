from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError

# RQ 01 - Manager personalizado
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El correo es obligatorio")
        if not password:
            raise ValueError("La contraseña es obligatoria")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)

# RFADMIN04 - Actualizar cuenta de usuario
class User(AbstractBaseUser, PermissionsMixin):
    # Campos base
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=False)  # Regla: Correo confirmado
    is_staff = models.BooleanField(default=False)
    
    # RFADMIN04 Entrada 2.1 - Nombre
    first_name = models.CharField(max_length=150, blank=True, default='')
    last_name = models.CharField(max_length=150, blank=True, default='')
    
    # RFADMIN04 Entrada 2.2 - Tipo de documento
    DOCUMENT_TYPES = [
        ('CC', 'Cédula de Ciudadanía'),
        ('CE', 'Cédula de Extranjería'),
        ('PP', 'Pasaporte'),
    ]
    document_type = models.CharField(max_length=2, choices=DOCUMENT_TYPES, blank=True, default='')
    
    # RFADMIN04 Entrada 2.3 - Número de documento
    # Regla negocio 2: No se puede cambiar si ya está en uso
    document_number = models.CharField(max_length=20, null=True, blank=True)
    
    # RFADMIN04 Entrada 2.4 - Tipo de usuario
    USER_TYPES = [
        ('ADMIN', 'Administrador'),
        ('PHARMACIST', 'Farmaceuta'),
        ('PATIENT', 'Paciente'),
    ]
    user_type = models.CharField(max_length=20, choices=USER_TYPES, blank=True, default='')
    
    # RFADMIN04 Entrada 2.6 - Teléfono
    phone = models.CharField(max_length=15, blank=True, default='')
    
    # RFADMIN04 Entrada 2.7 - Dirección
    address = models.TextField(blank=True, default='')
    
    # RFADMIN04 Entrada 2.9 - Estado
    # Regla negocio 4: No cambiar a Inactivo sin justificación
    STATE_CHOICES = [
        ('ACTIVE', 'Activo'),
        ('INACTIVE', 'Inactivo'),
    ]
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default='ACTIVE')
    
    # RFADMIN04 Entrada 2.10 - Fechas (inicio y finalización)
    # Regla negocio 3: Si user_type es Farmaceuta, son obligatorias
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # RFADMIN04 Entrada 2.11 - Foto de perfil
    profile_photo = models.ImageField(upload_to='profiles/', null=True, blank=True)
    
    # Auditoría - RFADMIN04 Salida 3: Registro de modificación
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    def clean(self):
        """Validaciones de reglas de negocio RFADMIN04"""
        # Regla negocio 3: Si es Farmaceuta, fechas obligatorias
        if self.user_type == 'PHARMACIST':
            if not self.start_date or not self.end_date:
                raise ValidationError("Las fechas de inicio y fin son obligatorias para Farmaceuta")
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-created_at']