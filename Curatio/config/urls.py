"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
#Anterior
# from django.contrib import admin
# from django.urls import path

# urlpatterns = [
#     path('admin/', admin.site.urls),
# ]

# urlpatterns = [
#     path('admin-panel/', admin.site.urls),
#     # Login profesional
#     path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
#     # Recuperación de contraseña (RFADMIN01)
#     path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
#     path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
# ]

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from accounts import views as account_views
from django.conf import settings
from django.conf.urls.static import static





urlpatterns = [
    path('admin-panel/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Esta es la ruta que te falta para el error 404:
    path('', account_views.dashboard, name='dashboard'),
    
    # Rutas de recuperación
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('accounts/crear/', account_views.crear_usuario, name='crear_usuario'),

    #Visualizar usuario
    # Usuario autenticado ve su perfil
    path('accounts/perfil/', account_views.ver_usuario, name='mi_perfil'),

    # ADMIN ve cualquier usuario
    path('accounts/usuario/<int:user_id>/', account_views.ver_usuario, name='ver_usuario_admin'),

    #ADMIN lista usuarios
    path('accounts/usuarios/', account_views.lista_usuarios, name='lista_usuarios'),
    

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)