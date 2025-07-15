import logging

from django.db import models
from django.dispatch import receiver

from apps.common import email
from apps.common import models as base_models
from apps.users.models import User

logger = logging.getLogger(__name__)


class Invitation(base_models.BaseModel):
    inviter = models.ForeignKey(
        User, on_delete=models.CASCADE
    )  # The user who is sending the invitation
    email = models.EmailField()  # The email address of the invitee
    join = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invitation from {self.inviter.username} to {self.email}"


# SIGNALS


@receiver(models.signals.post_save, sender=Invitation)
def send_invitation_email(sender, instance, created, **kwargs):
    if created:
        try:
            email.send_email_template(
                instance.email,
                "d-f695a7a6facd42c2ab77cd18db2c2363",
                {
                    instance.email: {
                        "username": instance.inviter.username,
                        "referral_code": instance.inviter.username,
                    }
                },
            )
        except Exception as e:
            logger.error(f"Error sending invitation email: {e}")
