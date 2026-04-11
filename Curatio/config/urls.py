from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from accounts.api_user_views import (
    users_resource,
    # Recurso colección de usuarios.
    user_me_profile_resource, 
    user_detail_resource,
    user_status_resource,
)
from accounts.api_identity_views import (
    csrf_token_view,
    session_resource_view,
    password_recovery_request_view,
    password_recovery_validate_view,
    password_recovery_confirm_view,
    session_takeover_view,
)

urlpatterns = [
    path("admin-panel/", admin.site.urls),

    # =========================
    # IDENTITY / SESSION
    # =========================
    path("v1/identity/csrf-token/", csrf_token_view, name="identity_csrf_token"),
    path("v1/identity/session/", session_resource_view, name="identity_session"),

    # =========================
    # PASSWORD RECOVERY
    # =========================
    path("v1/identity/password-recovery/",
        password_recovery_request_view,
        name="password_recovery_request",
    ),
    path(
        "v1/identity/password-recovery/validate/",
        password_recovery_validate_view,
        name="password_recovery_validate",
    ),
    path(
        "v1/identity/password-recovery/confirm/",
        password_recovery_confirm_view,
        name="password_recovery_confirm",
    ),
    path(
        "v1/identity/session/takeover/",
        session_takeover_view,
        name="identity_session_takeover",
    ),

    # ============================
    # USERS
    # =========================
    path("v1/people/users/", users_resource, name="users_resource"),
    path("v1/people/users/<int:user_id>/", user_detail_resource, name="user_detail_resource"),
    path("v1/people/users/<int:user_id>/status/", user_status_resource, name="user_status_resource"),

    path("", include("accounts.urls")),
    path("", include("products.urls")),
    path("", include("sales.urls")),
    path("api/", include("sales.urls")),    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")
    