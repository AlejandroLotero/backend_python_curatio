from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from accounts.api_identity_views import csrf_token_view, session_resource_view

urlpatterns = [
    path("admin-panel/", admin.site.urls),

    path("v1/identity/csrf-token/", csrf_token_view, name="identity_csrf_token"),
    path("v1/identity/session/", session_resource_view, name="identity_session"),

    path("", include("accounts.urls")),
    path("", include("products.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)