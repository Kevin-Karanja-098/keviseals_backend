# from django.db import models
# from django.contrib.auth import get_user_model

# User = get_user_model()

# class Message(models.Model):
#     sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
#     receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
#     content = models.TextField()
#     timestamp = models.DateTimeField(auto_now_add=True)
#     is_read = models.BooleanField(default=False)

#     class Meta:
#         ordering = ['timestamp']

#     def __str__(self):
#         return f"{self.sender.email} -> {self.receiver.email}: {self.content[:20]}"

from django.conf import settings
from django.db import models

class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages")
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_messages")
    content = models.TextField(blank=True, null=True)
    
    # Media Attachments
    file_attachment = models.FileField(upload_to='chat_attachments/', blank=True, null=True)
    file_type = models.CharField(max_length=20, blank=True, null=True) # 'image', 'pdf', 'document'
    
    # Status Flags
    is_read = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.sender} -> {self.receiver} ({self.timestamp})"