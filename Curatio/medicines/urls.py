from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para API REST
router = DefaultRouter()
router.register(r'', views.MedicineViewSet, basename='medicine')

# URLs Web
web_patterns = [
    path('', views.medicine_list, name='medicine_list'),
    path('crear/', views.medicine_create, name='medicine_create'),
    path('<int:pk>/', views.medicine_detail, name='medicine_detail'),
    path('<int:pk>/editar/', views.medicine_update, name='medicine_update'),
    path('<int:pk>/eliminar/', views.medicine_delete, name='medicine_delete'),
]

urlpatterns = web_patterns + router.urls
