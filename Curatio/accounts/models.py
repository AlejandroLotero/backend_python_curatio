# OJOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
# IMPORTANTE ====> PARA LA EJECUCION CORRECTA DEL CODIGO SE DEBE INSTALAR LA LIBRERIA PILLOW
# PARA EL MANEJO DE IMAGENES EN EL CAMPO FOTO, SE PUEDE HACER CON EL SIGUIENTE COMANDO:
# python -m pip install Pillow
#
# Este modelo cubre RQ01 - RQ02 y servirá como base de autenticación real del sistema
# sobre accounts_user. Más adelante será compatible con token porque mantiene el modelo
# personalizado de Django correctamente estructurado.

import re
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError


# =========================
# MANAGER DE USUARIOS
# =========================

class UserManager(BaseUserManager):
    """
    Manager personalizado para crear usuarios y superusuarios
    sobre accounts_user.
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El correo es obligatorio")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.full_clean()   # valida antes de guardar
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Superusuario del sistema.
        """
        extra_fields.setdefault("rol", "Administrador")
        extra_fields.setdefault("estado", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


# =========================
# MODELO USER (RQ01 + RQ02)
# =========================

class User(AbstractBaseUser, PermissionsMixin):
    """
    Modelo principal de usuarios del sistema.
    Esta tabla será la base para autenticación, sesión y futuro uso de token.
    """

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

    # ========= CAMPOS DE NEGOCIO =========

    nombre = models.CharField(max_length=100)

    tipo_documento = models.CharField(
        max_length=10,
        choices=TIPOS_DOCUMENTO
    )

    numero_documento = models.CharField(
        max_length=20,
        unique=True
    )

    rol = models.CharField(
        max_length=20,
        choices=ROLES
    )

    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)

    email = models.EmailField(unique=True)
    email_confirmed = models.BooleanField(default=True)
    telefono = models.CharField(max_length=15)

    telefono_secundario = models.CharField(
        max_length=15,
        null=True,
        blank=True
    )

    direccion = models.CharField(max_length=150)

    foto = models.ImageField(
        upload_to="usuarios/",
        null=True,
        blank=True
    )

    # Estado de negocio del usuario
    estado = models.BooleanField(default=True)

    # ========= CAMPOS TECNICOS DJANGO =========

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["nombre"]

    # =========================
    # PROPIEDADES DE APOYO
    # =========================

    @property
    def estado_texto(self):
        return "Activo" if self.estado else "Inactivo"

    # =========================
    # VALIDACIONES BACKEND
    # =========================

    def clean(self):
        """
        Validaciones de negocio para RQ de usuarios.
        """

        # ===== NOMBRE =====
        if not self.nombre or not self.nombre.strip():
            raise ValidationError("El nombre es obligatorio.")

        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', self.nombre):
            raise ValidationError("El nombre solo puede contener letras y espacios.")

        # ===== FARMACEUTA FECHAS =====
        if self.rol == "Farmaceuta":
            if not self.fecha_inicio or not self.fecha_fin:
                raise ValidationError(
                    "Si el usuario es Farmaceuta, fecha_inicio y fecha_fin son obligatorias."
                )

        # ===== DOCUMENTO =====
        if not self.numero_documento or not self.numero_documento.isdigit():
            raise ValidationError("El número de documento debe ser numérico.")

        # ===== TELÉFONO =====
        if not self.telefono or not self.telefono.isdigit():
            raise ValidationError("El teléfono debe contener solo números.")

        if len(self.telefono) < 7 or len(self.telefono) > 15:
            raise ValidationError("El teléfono debe tener entre 7 y 15 dígitos.")

        # ===== TELÉFONO SECUNDARIO =====
        if self.telefono_secundario:
            if not self.telefono_secundario.isdigit():
                raise ValidationError("El teléfono secundario debe contener solo números.")

        # ===== DIRECCIÓN =====
        if not self.direccion or len(self.direccion.strip()) < 10 or len(self.direccion.strip()) > 150:
            raise ValidationError("La dirección debe tener entre 10 y 150 caracteres.")

        # ===== FOTO VALIDACIÓN =====
        if self.foto:
            if self.foto.size > 2 * 1024 * 1024:
                raise ValidationError("La imagen no puede superar 2MB.")

            if not self.foto.name.lower().endswith((".jpg", ".jpeg", ".png")):
                raise ValidationError("Formato de imagen no permitido.")

    def __str__(self):
        return f"{self.nombre} - {self.email}"


# =========================
# BITÁCORA DE USUARIOS
# =========================
# Registro histórico de acciones importantes realizadas por administradores
# sobre cuentas de usuario del sistema.

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

    class Meta:
        verbose_name = "Bitácora de usuario"
        verbose_name_plural = "Bitácoras de usuarios"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.admin.email} -> {self.usuario.email} ({self.accion})"