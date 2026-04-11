from django.conf import settings

def get_email_branding_context(extra=None):
    context = dict(getattr(settings, "EMAIL_BRAND", {}))
    if extra:
        context.update(extra)
    return context