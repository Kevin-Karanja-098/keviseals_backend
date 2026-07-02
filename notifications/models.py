from django.conf import settings
from django.db import models


class Device(models.Model):
    PLATFORM_CHOICES = (
        ("web", "Web"),
        ("android", "Android"),
        ("ios", "iOS"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="devices",
    )

    fcm_token = models.TextField(unique=True)

    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
    )

    device_name = models.CharField(
        max_length=300,
        blank=True,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_seen"]

    def __str__(self):
        return f"{self.user.email} ({self.platform})"


class Notification(models.Model):

    TYPE_CHOICES = (
        ("chat", "Chat"),
        ("payment", "Payment"),
        ("invoice", "Invoice"),
        ("lease", "Lease"),
        ("maintenance", "Maintenance"),
        ("property", "Property"),
        ("account", "Account"),
        ("security", "Security"),
        ("announcement", "Announcement"),
        ("reminder", "Reminder"),
        ("system", "System"),
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    title = models.CharField(max_length=255)

    body = models.TextField()

    notification_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
    )

    data = models.JSONField(
        default=dict,
        blank=True,
    )

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} -> {self.recipient.email}"