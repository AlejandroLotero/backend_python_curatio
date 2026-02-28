#CODIGO INICIAL CREADO POR ALEJANDRO LOTERO SE COMENTA PARA QUE NO ENTRE EN CONFLICTO CON EL NUEVO CODIGO Y EL NUEVO CODIGO SE CREA DE ACUERDO A LOS REQUERIMIENTOS DEL PROYECTO
# from django.db import models
# from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
# # Create your models here.
# #esto es  el RQ 01
# class UserManager(BaseUserManager):
#     def create_user(self, email, password=None, **extra_fields):
#         if not email:
#             raise ValueError("El correo es obligatorio")
#         email = self.normalize_email(email)
#         user = self.model(email=email, **extra_fields)
#         user.set_password(password)
#         user.save(using=self._db)
#         return user

#     def create_superuser(self, email, password=None, **extra_fields):
#         extra_fields.setdefault('is_staff', True)
#         extra_fields.setdefault('is_superuser', True)
#         return self.create_user(email, password, **extra_fields)

# class User(AbstractBaseUser, PermissionsMixin):
#     email = models.EmailField(unique=True)
#     is_active = models.BooleanField(default=True) # Regla: Correo confirmado
#     is_staff = models.BooleanField(default=False)
    
#     objects = UserManager()

#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = []

#OJOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
#IMPORTANTE ====> PARA LA EJECUCION CORRECTA DEL CODIGO SE DEBE INSTALA LA LIBRERIA DE PILLOW PARA EL MANEJO DE IMAGENES EN EL CAMPO FOTO, SE PUEDE HACER CON EL SIGUIENTE COMANDO:
#python -m pip install Pillow
# # esto es el RQ01--RQ02

import re
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError


# =========================
# SUPERUSUARIO
# =========================

class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El correo es obligatorio")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("rol", "Administrador")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, password, **extra_fields)


# =========================
# MODELO USER (RQ01 + RQ02)
# =========================

class User(AbstractBaseUser, PermissionsMixin):

    ROLES = (
        ("Administrador", "Administrador"),
        ("Farmaceuta", "Farmaceuta"),
        ("Cliente", "Cliente"),
    )

    TIPOS_DOCUMENTO = (
        ("NIT", "NIT"),
        ("CC", "Cédula Ciudadanía"),
        ("CE", "Cédula Extranjería"),
        ("TI", "Tarjeta Identidad"),
        ("PEP", "Permiso Especial de Permanencia"),
        ("PPT", "Permiso por Protección Temporal"),
    )

    # ========= RQ02 CAMPOS =========

    nombre = models.CharField(max_length=100)

    tipo_documento = models.CharField(
        max_length=10,
        choices=TIPOS_DOCUMENTO
    )

    numero_documento = models.CharField(
        max_length=15,
        unique=True
    )

    rol = models.CharField(
        max_length=20,
        choices=ROLES
    )

    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)

    email = models.EmailField(unique=True)

    telefono = models.CharField(max_length=15)
    telefono_secundario = models.CharField(
        max_length=15,
        null=True,
        blank=True
    )

    direccion = models.CharField(max_length=100)

    foto = models.ImageField(
        upload_to="usuarios/",
        null=True,
        blank=True
    )

    estado = models.BooleanField(default=True)  # Activo por defecto

    # ========= CAMPOS OBLIGATORIOS DJANGO ========= 

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    # =========================
    # VALIDACIONES BACKEND
    # =========================

    def clean(self):
        # Regla: Fechas obligatorias si es Farmaceuta
        if self.rol == "Farmaceuta":
            if not self.fecha_inicio or not self.fecha_fin:
                raise ValidationError(
                    "Si el usuario es Farmaceuta, fecha_inicio y fecha_fin son obligatorias."
                )

        # Regla: número documento solo numérico
        if not self.numero_documento.isdigit():
            raise ValidationError("El número de documento debe ser numérico.")

        # Regla: teléfono solo numérico
        if not self.telefono.isdigit():
            raise ValidationError("El teléfono debe contener solo números.")

        if self.telefono_secundario:
            if not self.telefono_secundario.isdigit():
                raise ValidationError("El teléfono secundario debe contener solo números.")

                    # ===== VALIDAR NOMBRE =====
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', self.nombre):
                raise ValidationError("El nombre solo puede contener letras y espacios.")

            # ===== FARMACEUTA FECHAS =====
        if self.rol == "Farmaceuta":
                if not self.fecha_inicio or not self.fecha_fin:
                    raise ValidationError(
                        "Si el usuario es Farmaceuta, fecha_inicio y fecha_fin son obligatorias."
                    )

            # ===== DOCUMENTO =====
        if not self.numero_documento.isdigit():
                raise ValidationError("El número de documento debe ser numérico.")

            # ===== TELÉFONO =====
        if not self.telefono.isdigit():
                raise ValidationError("El teléfono debe contener solo números.")
        if len(self.telefono) < 7 or len(self.telefono) > 15:
                raise ValidationError("El teléfono debe tener entre 7 y 15 dígitos.")

            # ===== TELÉFONO SECUNDARIO =====
        if self.telefono_secundario:
                if not self.telefono_secundario.isdigit():
                    raise ValidationError("El teléfono secundario debe contener solo números.")

            # ===== DIRECCIÓN =====
        if len(self.direccion) < 10 or len(self.direccion) > 100:
                raise ValidationError("La dirección debe tener entre 10 y 100 caracteres.")

            # ===== FOTO VALIDACIÓN =====
        if self.foto:
            if self.foto.size > 2 * 1024 * 1024:
                raise ValidationError("La imagen no puede superar 2MB.")

            if not self.foto.name.endswith(('.jpg', '.jpeg', '.png')):
                raise ValidationError("Formato de imagen no permitido.")



#BITACORA: registro histórico de acciones importantes que se hacen en el sistema.
class BitacoraUsuario(models.Model):
    admin = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="acciones_admin"
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="acciones_usuario"
    )

    accion = models.CharField(max_length=50)
    motivo = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin.email} -> {self.usuario.email} ({self.accion})"


