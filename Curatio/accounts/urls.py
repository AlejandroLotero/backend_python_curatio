from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from accounts import views as account_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', account_views.dashboard, name='dashboard'),
    path('admin-panel/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
       
    # Rutas de recuperación
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    

    #Visualizar usuario
    # Usuario autenticado ve su perfil
    path('accounts/crear/', account_views.crear_usuario, name='crear_usuario'),
    path('accounts/perfil/', account_views.ver_usuario, name='mi_perfil'),

    # ADMIN ve cualquier usuario
    path('accounts/usuario/<int:user_id>/', account_views.ver_usuario, name='ver_usuario_admin'),

    #ADMIN lista usuarios
    path('accounts/usuarios/', account_views.lista_usuarios, name='lista_usuarios'),

        #ADMIN Habilitar y deshabilitar
    path('accounts/cambiar-estado/<int:user_id>/', account_views.cambiar_estado_usuario, name='cambiar_estado'),

    #Cambiar estado de usuario
    path(
    'accounts/cambiar-estado/<int:user_id>/', account_views.cambiar_estado_usuario, name='cambiar_estado_usuario'),

    #Admin medicamentos
    path("products/", include("products.urls")),

     #Generación de reporte de usuarios 
    path('accounts/reporte-usuarios/', account_views.generar_reporte_usuarios, name='reporte_usuarios'),
    
    #ADMIN Habilitar y deshabilitar
    path('accounts/cambiar-estado/<int:user_id>/', account_views.cambiar_estado_usuario, name='cambiar_estado'),

    #Cambiar estado de usuario
    path(
    'accounts/cambiar-estado/<int:user_id>/', account_views.cambiar_estado_usuario, name='cambiar_estado_usuario'),
]