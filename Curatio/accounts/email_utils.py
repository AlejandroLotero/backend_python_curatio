# from django.conf import settings
# from django.core.mail import EmailMultiAlternatives
# from django.template.loader import render_to_string


# # =========================
# # CONFIGURACIÓN VISUAL DE CORREOS
# # =========================
# # Recomendación:
# # - EMAIL_BRAND_NAME: nombre visible de la marca
# # - EMAIL_BRAND_LOGO_URL: URL pública absoluta del logo
# # - FRONTEND_BASE_URL: URL base del frontend
# #
# # Si no existen, se usan valores por defecto seguros.

# def _brand_context():
#     return {
#         "brand_name": getattr(settings, "EMAIL_BRAND_NAME", "Curatio"),
#         "brand_logo_url": getattr(settings, "EMAIL_BRAND_LOGO_URL", ""),
#         "support_email": getattr(settings, "DEFAULT_FROM_EMAIL", ""),
#         "frontend_base_url": getattr(settings, "FRONTEND_BASE_URL", ""),
#     }


# def send_account_created_email(user, temporary_password):
#     """
#     Envía correo profesional de cuenta creada.
#     Incluye:
#     - versión texto plano
#     - versión HTML
#     """

#     context = {
#         **_brand_context(),
#         "user": user,
#         "temporary_password": temporary_password,
#         "login_url": f"{getattr(settings, 'FRONTEND_BASE_URL', '').rstrip('/')}/login",
#     }

#     subject = "Cuenta creada - Curatio"

#     text_body = render_to_string("emails/account_created.txt", context)
#     html_body = render_to_string("emails/account_created.html", context)

#     email = EmailMultiAlternatives(
#         subject=subject,
#         body=text_body,
#         from_email=settings.DEFAULT_FROM_EMAIL,
#         to=[user.email],
#     )
#     email.attach_alternative(html_body, "text/html")
#     email.send(fail_silently=False)


# def send_password_reset_email(user, uidb64, token):
#     """
#     Envía correo profesional de recuperación de contraseña.
#     Incluye:
#     - link directo
#     - token visible como respaldo
#     - versión texto plano
#     - versión HTML
#     """

#     reset_link = f"{getattr(settings, 'FRONTEND_BASE_URL', '').rstrip('/')}/reset-password?uid={uidb64}&token={token}"

#     context = {
#         **_brand_context(),
#         "user": user,
#         "uid": uidb64,
#         "token": token,
#         "reset_link": reset_link,
#     }

#     subject = "Restablecimiento de contraseña - Curatio"

#     text_body = render_to_string("emails/password_reset.txt", context)
#     html_body = render_to_string("emails/password_reset.html", context)

#     email = EmailMultiAlternatives(
#         subject=subject,
#         body=text_body,
#         from_email=settings.DEFAULT_FROM_EMAIL,
#         to=[user.email],
#     )
#     email.attach_alternative(html_body, "text/html")
#     email.send(fail_silently=False)

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


# =========================
# CONFIGURACIÓN VISUAL DE CORREOS
# =========================

def _brand_context():
    """
    Contexto base visual para todos los correos transaccionales.
    """
    frontend_base_url = getattr(settings, "FRONTEND_BASE_URL", "").rstrip("/")

    return {
        "brand_name": getattr(settings, "EMAIL_BRAND_NAME", "Curatio"),
        "brand_logo_url": getattr(settings, "EMAIL_BRAND_LOGO_URL", ""),
        "support_email": getattr(settings, "DEFAULT_FROM_EMAIL", ""),
        "frontend_base_url": frontend_base_url,
        "primary_color": "#0F4C81",   # azul clínico / corporativo
        "accent_color": "#2BB3A3",    # verde médico suave
        "text_color": "#1F2937",
        "muted_color": "#6B7280",
        "background_color": "#F4F7FB",
        "card_color": "#FFFFFF",
        "border_color": "#E5E7EB",
    }


def _send_html_email(subject, to_email, text_template, html_template, context):
    """
    Helper genérico para enviar correo con versión texto + HTML.
    """
    text_body = render_to_string(text_template, context)
    html_body = render_to_string(html_template, context)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    email.attach_alternative(html_body, "text/html")
    email.send(fail_silently=False)


def send_account_created_email(user, temporary_password):
    """
    Correo profesional de cuenta creada.
    """
    frontend_base_url = getattr(settings, "FRONTEND_BASE_URL", "").rstrip("/")

    context = {
        **_brand_context(),
        "user": user,
        "temporary_password": temporary_password,
        "login_url": f"{frontend_base_url}/login" if frontend_base_url else "",
    }

    _send_html_email(
        subject="Cuenta creada - Curatio",
        to_email=user.email,
        text_template="emails/account_created.txt",
        html_template="emails/account_created.html",
        context=context,
    )


def send_password_reset_email(user, uidb64, token):
    """
    Correo profesional de restablecimiento de contraseña.
    """
    frontend_base_url = getattr(settings, "FRONTEND_BASE_URL", "").rstrip("/")
    reset_link = f"{frontend_base_url}/reset-password?uid={uidb64}&token={token}" if frontend_base_url else ""

    context = {
        **_brand_context(),
        "user": user,
        "uid": uidb64,
        "token": token,
        "reset_link": reset_link,
    }

    _send_html_email(
        subject="Restablecimiento de contraseña - Curatio",
        to_email=user.email,
        text_template="emails/password_reset.txt",
        html_template="emails/password_reset.html",
        context=context,
    )