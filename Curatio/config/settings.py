# """
# Django settings for config project.
# """

# from pathlib import Path
# import os
# import environ

# BASE_DIR = Path(__file__).resolve().parent.parent

# #Para manejar tiempos de inactividad, correo el token
# env = environ.Env(
#     DEBUG=(bool, False),
#     EMAIL_PORT=(int, 587),
#     EMAIL_USE_TLS=(bool, True),
#     SESSION_COOKIE_AGE=(int, 1800),  # 30 min
#     SESSION_INACTIVITY_TIMEOUT=(int, 900),  # 15 min
#     PASSWORD_RESET_TIMEOUT=(int, 3600),  # 1 hora
# )
# environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# # =========================
# # SEGURIDAD / ENTORNO
# # =========================
# SECRET_KEY = env("SECRET_KEY", default="django-insecure-change-me")
# DEBUG = env("DEBUG")

# ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# # =========================
# # EMAIL
# # =========================
# EMAIL_BACKEND = env(
#     "EMAIL_BACKEND",
#     default="django.core.mail.backends.console.EmailBackend"
# )
# EMAIL_HOST = env("EMAIL_HOST", default="localhost")
# EMAIL_PORT = env("EMAIL_PORT")
# EMAIL_USE_TLS = env("EMAIL_USE_TLS")
# EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
# EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
# DEFAULT_FROM_EMAIL = env(
#     "DEFAULT_FROM_EMAIL",
#     default=f"Curatio Admin <{EMAIL_HOST_USER or 'no-reply@curatio.local'}>"
# )

# # =========================
# # FRONTEND / PASSWORD RESET
# # =========================
# FRONTEND_BASE_URL = env(
#     "FRONTEND_BASE_URL",
#     default="http://localhost:5173"
# )
# # Tiempo de vida del token de restablecimiento (segundos)q
# DJANGO_PASSWORD_RESET_TIMEOUT = env("PASSWORD_RESET_TIMEOUT")
# # Django usa esta variable para expirar el token de password reset
# PASSWORD_RESET_TIMEOUT = DJANGO_PASSWORD_RESET_TIMEOUT

# # =========================
# # MEDIA
# # =========================
# MEDIA_URL = "/media/"
# MEDIA_ROOT = BASE_DIR / "media"

# # =========================
# # AUTH
# # =========================
# AUTH_USER_MODEL = "accounts.User"

# # =========================
# # APPS
# # =========================
# INSTALLED_APPS = [
#     "django.contrib.admin",
#     "django.contrib.auth",
#     "django.contrib.contenttypes",
#     "django.contrib.sessions",
#     "django.contrib.messages",
#     "django.contrib.staticfiles",

#     "corsheaders",
#     "rest_framework",

#     "accounts",
#     "products",
#     "sales",
# ]

# # =========================
# # MIDDLEWARE
# # =========================
# MIDDLEWARE = [
#     "django.middleware.security.SecurityMiddleware",
#     "corsheaders.middleware.CorsMiddleware",
#     "django.contrib.sessions.middleware.SessionMiddleware",
#     "django.middleware.common.CommonMiddleware",
#     "django.middleware.csrf.CsrfViewMiddleware",
#     "django.contrib.auth.middleware.AuthenticationMiddleware",
#     "accounts.session_timeout.SessionInactivityMiddleware",
#     "django.contrib.messages.middleware.MessageMiddleware",
#     "django.middleware.clickjacking.XFrameOptionsMiddleware",
# ]

# ROOT_URLCONF = "config.urls"

# TEMPLATES = [
#     {
#         "BACKEND": "django.template.backends.django.DjangoTemplates",
#         "DIRS": [BASE_DIR / "templates"],
#         "APP_DIRS": True,
#         "OPTIONS": {
#             "context_processors": [
#                 "django.template.context_processors.request",
#                 "django.contrib.auth.context_processors.auth",
#                 "django.contrib.messages.context_processors.messages",
#             ],
#         },
#     },
# ]

# WSGI_APPLICATION = "config.wsgi.application"

# # =========================
# # DATABASE
# # =========================
# DATABASES = {
#     "default": {
#         "ENGINE": env("DB_ENGINE", default="django.db.backends.mysql"),
#         "NAME": env("DB_NAME", default="curatio"),
#         "USER": env("DB_USER", default="root"),
#         "PASSWORD": env("DB_PASSWORD", default="admin"),
#         "HOST": env("DB_HOST", default="localhost"),
#         "PORT": env("DB_PORT", default="3306"),
#     }
# }

# # =========================
# # PASSWORD VALIDATORS
# # =========================
# AUTH_PASSWORD_VALIDATORS = [
#     {
#         "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
#         "OPTIONS": {"min_length": 8},
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
#     },
#     {
#         "NAME": "accounts.validators.MaxLengthValidator",
#         "OPTIONS": {"max_length": 10},
#     },
# ]

# # =========================
# # I18N / TZ
# # =========================
# LANGUAGE_CODE = "es-co"
# TIME_ZONE = "America/Bogota"
# USE_I18N = True
# USE_TZ = True

# # =========================
# # STATIC
# # =========================
# STATIC_URL = "static/"

# # =========================
# # LOGIN REDIRECTS
# # =========================
# LOGIN_REDIRECT_URL = "dashboard"
# LOGOUT_REDIRECT_URL = "login"
# LOGIN_URL = "login"

# # =========================
# # CORS / CSRF
# # =========================
# CORS_ALLOWED_ORIGINS = env.list(
#     "CORS_ALLOWED_ORIGINS",
#     default=["http://localhost:5173"]
# )
# CSRF_TRUSTED_ORIGINS = env.list(
#     "CSRF_TRUSTED_ORIGINS",
#     default=["http://localhost:5173"]
# )
# CORS_ALLOW_CREDENTIALS = True

# # =========================
# # SESSION / COOKIES
# # =========================
# SESSION_COOKIE_AGE = env("SESSION_COOKIE_AGE")  # vida total de sesión en segundos
# SESSION_EXPIRE_AT_BROWSER_CLOSE = False
# SESSION_SAVE_EVERY_REQUEST = True
# SESSION_INACTIVITY_TIMEOUT = env("SESSION_INACTIVITY_TIMEOUT")

# SESSION_COOKIE_HTTPONLY = True
# CSRF_COOKIE_HTTPONLY = False

# SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=False)
# CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=False)
# SESSION_COOKIE_SAMESITE = env("SESSION_COOKIE_SAMESITE", default="Lax")
# CSRF_COOKIE_SAMESITE = env("CSRF_COOKIE_SAMESITE", default="Lax")

# # =========================
# # DRF
# # =========================
# REST_FRAMEWORK = {
#     "DEFAULT_AUTHENTICATION_CLASSES": [
#         "rest_framework.authentication.SessionAuthentication",
#     ],
#     "DEFAULT_PERMISSION_CLASSES": [
#         "rest_framework.permissions.IsAuthenticated",
#     ],
# }


# #============================
# #Para Envio del correo con template
# #============================
# EMAIL_BRAND_NAME = "Curatio"
# EMAIL_BRAND_LOGO_URL = "https://tu-dominio.com/static/img/logo-curatio.png"

"""
Django settings for config project.
"""

from pathlib import Path
import os

import environ

from .session import get_session_config

BASE_DIR = Path(__file__).resolve().parent.parent

# Carga y tipado de variables de entorno.
# Aquí se definen valores por defecto y tipos para facilitar la configuración
# del proyecto en distintos entornos.
env = environ.Env(
    DEBUG=(bool, False),
    EMAIL_PORT=(int, 587),
    EMAIL_USE_TLS=(bool, True),
    SESSION_COOKIE_AGE=(int, 1800),
    SESSION_INACTIVITY_TIMEOUT=(int, 900),
    PASSWORD_RESET_TIMEOUT=(int, 3600),
)

environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# =========================
# SEGURIDAD / ENTORNO
# =========================
SECRET_KEY = env("SECRET_KEY", default="django-insecure-change-me")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# =========================
# CONFIGURACION CENTRAL DE SESION
# =========================
# Se centraliza la configuración relacionada con sesión en un solo punto
# para evitar duplicación de valores en distintos archivos.
SESSION_CONFIG = get_session_config(env)

# =========================
# EMAIL
# =========================
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_USE_TLS = env("EMAIL_USE_TLS")
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL",
    default=f"Curatio Admin <{EMAIL_HOST_USER or 'no-reply@curatio.local'}>",
)

# =========================
# FRONTEND / PASSWORD RESET
# =========================
# URL base del frontend utilizada, por ejemplo, para construir enlaces
# de recuperación de contraseña enviados por correo.
FRONTEND_BASE_URL = env(
    "FRONTEND_BASE_URL",
    default="http://localhost:5173",
)

# Tiempo de vida del token de restablecimiento de contraseña en segundos.
PASSWORD_RESET_TIMEOUT = env("PASSWORD_RESET_TIMEOUT")

# =========================
# MEDIA
# =========================
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# =========================
# AUTH
# =========================
AUTH_USER_MODEL = "accounts.User"

# =========================
# APPS
# =========================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "accounts",
    "products",
    "sales",
]

# =========================
# MIDDLEWARE
# =========================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "accounts.session_exclusive_middleware.ExclusiveSessionMiddleware",
    "accounts.session_timeout.SessionInactivityMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# =========================
# DATABASE
# =========================
DATABASES = {
    "default": {
        "ENGINE": env("DB_ENGINE", default="django.db.backends.mysql"),
        "NAME": env("DB_NAME", default="curatio"),
        "USER": env("DB_USER", default="root"),
        "PASSWORD": env("DB_PASSWORD", default="admin"),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="3306"),
    }
}

# =========================
# PASSWORD VALIDATORS
# =========================
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
    {
        "NAME": "accounts.validators.MaxLengthValidator",
        "OPTIONS": {"max_length": 10},
    },
]

# =========================
# I18N / TZ
# =========================
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# =========================
# STATIC
# =========================
STATIC_URL = "static/"

# =========================
# LOGIN REDIRECTS
# =========================
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"
LOGIN_URL = "login"

# =========================
# CORS / CSRF
# =========================
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:5173"],
)
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=["http://localhost:5173"],
)
CORS_ALLOW_CREDENTIALS = True

# =========================
# SESSION / COOKIES
# =========================
# SESSION_COOKIE_AGE:
# Tiempo máximo de vida de la sesión.
SESSION_COOKIE_AGE = SESSION_CONFIG["COOKIE_AGE"]

# SESSION_INACTIVITY_TIMEOUT:
# Tiempo máximo permitido sin actividad antes de cerrar la sesión.
SESSION_INACTIVITY_TIMEOUT = SESSION_CONFIG["INACTIVITY_TIMEOUT"]

SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False

SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=False)
SESSION_COOKIE_SAMESITE = env("SESSION_COOKIE_SAMESITE", default="Lax")
CSRF_COOKIE_SAMESITE = env("CSRF_COOKIE_SAMESITE", default="Lax")

# =========================
# DJANGO REST FRAMEWORK
# =========================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# =========================
# CONFIGURACION DE CORREOS
# =========================
EMAIL_BRAND_NAME = "Curatio"
EMAIL_BRAND_LOGO_URL = "https://tu-dominio.com/static/img/logo-curatio.png"