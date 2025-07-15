from anymail.message import AnymailMessage
from django.conf import settings
from django.core.mail import EmailMessage


def send_email(subject, message, recipient, fail_silently=False):
    msg = AnymailMessage(
        subject,
        message,
        from_email=settings.FROM_EMAIL,
        to=[recipient],
    )

    return msg.send(fail_silently=fail_silently)


def send_email_template(
    email, template_id: str, dynamic_template_data: dict = None, fail_silently=True
):
    """
    Helper to send emails system wide.
    Special consideration made for sendgrid's dynamic templating.

    https://docs.sendgrid.com/ui/sending-email/how-to-send-an-email-with-dynamic-transactional-templates
    """
    msg = AnymailMessage(
        from_email=settings.FROM_EMAIL,
        to=[email],
    )
    msg.template_id = template_id

    if dynamic_template_data:
        msg.merge_data = dynamic_template_data

    return msg.send(fail_silently=fail_silently)
