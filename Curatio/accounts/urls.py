from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

from accounts import views as account_views


urlpatterns = [
    # =========================
    # INICIO / AUTENTICACIÓN
    # =========================
    path("", account_views.dashboard, name="dashboard"),   
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # =========================
    # RECUPERACIÓN DE CONTRASEÑA
    # =========================
    path("password-reset/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),

    # =========================
    # USUARIOS
    # =========================
    path("accounts/crear/", account_views.crear_usuario, name="crear_usuario"),
    path("accounts/perfil/", account_views.ver_usuario, name="mi_perfil"),
    path("accounts/usuario/<int:user_id>/", account_views.ver_usuario, name="ver_usuario_admin"),
    path("accounts/usuarios/", account_views.lista_usuarios, name="lista_usuarios"),
    path("accounts/cambiar-estado/<int:user_id>/", account_views.cambiar_estado_usuario, name="cambiar_estado_usuario"),
    path("accounts/reporte-usuarios/", account_views.generar_reporte_usuarios, name="reporte_usuarios"),


]