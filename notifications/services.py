from django.core.cache import cache
from firebase_admin import messaging

from .firebase import initialize_firebase
from .models import Device, Notification




def send_push_notification(
    user,
    title,
    body,
    notification_type="chat",
    data=None,
):
    initialize_firebase()


    if data is None:
        data = {}

    Notification.objects.create(
        recipient=user,
        title=title,
        body=body,
        notification_type=notification_type,
        data=data,
    )

    devices = Device.objects.filter(
        user=user,
        is_active=True,
    )

    for device in devices:

        try:

            message = messaging.Message(

                token=device.fcm_token,

                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),

                data={
                    k: str(v)
                    for k, v in data.items()
                },
            )

            messaging.send(message)

        except Exception as e:

            print(e)

            # Invalid token

            device.delete()

def send_chat_notification(message):

    if not should_send_chat_notification(message):
        return

    body = message.content

    if message.file_type == "image":
        body = "📷 Image"

    elif message.file_type == "pdf":
        body = "📄 PDF"

    elif message.file_type == "document":
        body = "📎 Document"

    send_push_notification(
        user=message.receiver,
        title=message.sender.get_full_name() or message.sender.email,
        body=body,
        notification_type="chat",
        data={
            "type": "chat",
            "sender_id": message.sender.id,
            "receiver_id": message.receiver.id,
            "message_id": message.id,
            "chat_user_id": message.sender.id,
        },
    )
def should_send_chat_notification(message):

    active_chat = cache.get(
        f"user_active_chat_{message.receiver.id}"
    )

    if active_chat == message.sender.id:
        return False

    return True