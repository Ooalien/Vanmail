from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import datetime
import os
from django.conf import settings
from django.utils import timezone

#Saturday comment 
class User(AbstractUser):
    pass


def get_attachment_path(instance, filename):
    # Create a unique path for each attachment
    return f'email_attachments/{instance.email.id}/{filename}'

class EmailAttachment(models.Model):
    email = models.ForeignKey("Email", on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to=get_attachment_path)
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)

    def __str__(self):
        return f"Attachment: {self.filename} for Email {self.email.id}"


class Email(models.Model):
    sender = models.ForeignKey("User", on_delete=models.PROTECT, related_name="emails_sent")
    recipients = models.ManyToManyField("User", related_name="emails_received")
    subject = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['sender', 'subject', 'body', 'timestamp'],
                name='unique_email_within_minute'
            )
        ]
        indexes = [
            models.Index(fields=['timestamp']),
        ]

    def save(self, *args, **kwargs):
        # Round timestamp to minute to prevent duplicates within same minute
        if not self.pk:  # Only on creation
            now = timezone.now()
            self.timestamp = now.replace(second=0, microsecond=0)
        super().save(*args, **kwargs)

    def serialize(self):
        return {
            "id": self.id,
            "sender": self.sender.email,
            "recipients": [user.email for user in self.recipients.all()],
            "subject": self.subject,
            "body": self.body,
            "timestamp": self.timestamp.strftime("%b %d %Y, %I:%M %p"),
            "read": self.read,
            "archived": self.archived,
            "attachments": [{
                "id": attachment.id,
                "filename": attachment.filename,
                "url": f"/attachment/{attachment.id}"
            } for attachment in self.attachments.all()]
        }
