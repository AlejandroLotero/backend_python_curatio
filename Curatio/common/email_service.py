from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from accounts.email_branding import get_email_branding_context

def send_branded_email(*, subject, to, template_name, context, text_body=""):
    full_context = get_email_branding_context(context)

    html_body = render_to_string(template_name, full_context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body or "",
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        to=to,
    )
    message.attach_alternative(html_body, "text/html")
    message.send(fail_silently=False)