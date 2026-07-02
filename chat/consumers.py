import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.cache import cache
from .models import Message
from notifications.services import send_chat_notification
from notifications.models import Notification

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return

        self.target_id = self.scope["url_route"]["kwargs"]["target_id"]
        
        user_ids = sorted([int(self.user.id), int(self.target_id)])
        self.room_group_name = f"chat_{user_ids[0]}_{user_ids[1]}"
        self.presence_group_name = "global_presence"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.channel_layer.group_add(self.presence_group_name, self.channel_name)
        
        await self.accept()
        await self.set_active_chat()

        # Update active chat connections tracker
        current_count = await self.increment_connection()
        # Always make sure they show online on initial load or swap fallback
        await self.broadcast_presence("online")

    async def disconnect(self, close_code):
        # Decrement tracking count when moving away from a room/person
        still_connected_count = await self.decrement_connection()
        
        # CRITICAL FIX: Only broadcast offline if they have 0 active chat screens left open
        if still_connected_count == 0:
            await self.broadcast_presence("offline")
            
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.channel_layer.group_discard(self.presence_group_name, self.channel_name)
        await self.clear_active_chat()

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action", "message")

        if action == "typing":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_typing", 
                    "user_id": self.user.id, 
                    "is_typing": data.get("is_typing", False)
                }
            )
            
        elif action == "read_receipt":
            await self.mark_messages_as_read()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_read_receipt", 
                    "reader_id": self.user.id
                }
            )
            
        elif action == "edit":
            message_id = data.get("message_id")
            new_content = data.get("new_content", "").strip()
            if message_id and new_content:
                await self.update_message_content(message_id, new_content)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat_edit", 
                        "message_id": message_id, 
                        "new_content": new_content
                    }
                )
                
        elif action == "delete":
            message_id = data.get("message_id")
            if message_id:
                await self.soft_delete_message(message_id)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat_delete", 
                        "message_id": message_id
                    }
                )
                
        elif action == "message":
            content_text = data.get("message", "").strip()
            
            if not content_text and not data.get("file_url"):
                return

            msg_obj = await self.save_message(
                content=content_text,
                file_type=data.get("file_type"),
                file_url=data.get("file_url")
            )
            await database_sync_to_async(
                    send_chat_notification
                )(msg_obj)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "id": msg_obj.id,
                    "sender_id": self.user.id,
                    "sender_email": self.user.email,
                    "message": msg_obj.content,
                    "file_type": msg_obj.file_type,
                    "file_url": data.get("file_url"), 
                    "is_edited": False,
                    "is_deleted": False,
                    "timestamp": msg_obj.timestamp.strftime("%H:%M")
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def chat_typing(self, event):
        await self.send(text_data=json.dumps({
            "action": "typing", "user_id": event["user_id"], "is_typing": event["is_typing"]
        }))

    async def chat_read_receipt(self, event):
        await self.send(text_data=json.dumps({
            "action": "read_receipt", "reader_id": event["reader_id"]
        }))

    async def chat_edit(self, event):
        await self.send(text_data=json.dumps({
            "action": "edit", "message_id": event["message_id"], "new_content": event["new_content"]
        }))

    async def chat_delete(self, event):
        await self.send(text_data=json.dumps({
            "action": "delete", "message_id": event["message_id"]
        }))

    async def presence_update(self, event):
        await self.send(text_data=json.dumps({
            "action": "presence_update", "user_id": event["user_id"], "status": event["status"]
        }))

    async def broadcast_presence(self, status):
        await self.channel_layer.group_send(
            self.presence_group_name,
            {"type": "presence_update", "user_id": self.user.id, "status": status}
        )

    # -------------------------------------------------------------------------
    # Thread-Safe Presence Connection Helpers
    # -------------------------------------------------------------------------
    @database_sync_to_async
    def increment_connection(self):
        cache_key = f"user_online_conn_{self.user.id}"
        count = cache.get(cache_key, 0) + 1
        cache.set(cache_key, count, timeout=None)
        return count

    @database_sync_to_async
    def decrement_connection(self):
        cache_key = f"user_online_conn_{self.user.id}"
        count = cache.get(cache_key, 0) - 1
        count = max(0, count)
        
        if count == 0:
            cache.delete(cache_key)
        else:
            cache.set(cache_key, count, timeout=None)
        return count

    # -------------------------------------------------------------------------
    # Database Layer Alignment
    # -------------------------------------------------------------------------
    @database_sync_to_async
    def save_message(self, content, file_type=None, file_url=None):
        recipient_id = int(self.target_id)
        kwargs = {
            "sender": self.user,
            "receiver_id": recipient_id,
            "content": content,
            "file_type": file_type if file_type else None,
            "is_read": False
        }
        if file_url:
            kwargs["file_attachment"] = file_url
            
        return Message.objects.create(**kwargs)

    @database_sync_to_async
    def update_message_content(self, message_id, new_content):
        Message.objects.filter(id=message_id, sender=self.user).update(
            content=new_content, is_edited=True
        )

    @database_sync_to_async
    def soft_delete_message(self, message_id):
        Message.objects.filter(id=message_id, sender=self.user).update(is_deleted=True)


    @database_sync_to_async
    def mark_messages_as_read(self):
        sender_id = int(self.target_id)

        # Mark chat messages as read
        Message.objects.filter(
            sender_id=sender_id,
            receiver=self.user,
            is_read=False
        ).update(is_read=True)

        # Mark chat notifications as read
        Notification.objects.filter(
            recipient=self.user,
            notification_type="chat",
            is_read=False,
            data__sender_id=sender_id
        ).update(is_read=True)

    @database_sync_to_async
    def set_active_chat(self):
        cache.set(
            f"user_active_chat_{self.user.id}",
            int(self.target_id),
            timeout=None,
        )


    @database_sync_to_async
    def clear_active_chat(self):
        key = f"user_active_chat_{self.user.id}"

        current = cache.get(key)

        if current == int(self.target_id):
            cache.delete(key)