from django.contrib import admin

from .models import Device, Notification


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "platform",
        "device_name",
        "is_active",
        "last_seen",
    )

    search_fields = (
        "user__email",
        "fcm_token",
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "recipient",
        "notification_type",
        "title",
        "is_read",
        "created_at",
    )

    list_filter = (
        "notification_type",
        "is_read",
    )

    search_fields = (
        "recipient__email",
        "title",
    )