from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    Conversation,
    ConversationParticipant,
    Message,
)

User = get_user_model()


class ChatUserSerializer(serializers.ModelSerializer):

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "full_name",
        )

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class ParticipantSerializer(serializers.ModelSerializer):

    user = ChatUserSerializer()

    class Meta:
        model = ConversationParticipant
        fields = (
            "id",
            "user",
            "joined_at",
            "last_read_at",
        )


class MessageSerializer(serializers.ModelSerializer):

    sender = ChatUserSerializer()

    class Meta:
        model = Message
        fields = (
            "id",
            "sender",
            "message",
            "is_edited",
            "is_deleted",
            "created_at",
            "updated_at",
        )


class ConversationSerializer(serializers.ModelSerializer):

    participants = ParticipantSerializer(
        many=True,
        read_only=True,
    )

    last_message = serializers.SerializerMethodField()

    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = (
            "id",
            "participants",
            "last_message",
            "unread_count",
            "created_at",
            "updated_at",
        )

    def get_last_message(self, obj):

        last = obj.messages.last()

        if not last:
            return None

        return MessageSerializer(last).data

    def get_unread_count(self, obj):

        request = self.context["request"]

        participant = obj.participants.filter(
            user=request.user
        ).first()

        if not participant:
            return 0

        if participant.last_read_at is None:
            return obj.messages.exclude(
                sender=request.user
            ).count()

        return obj.messages.filter(
            created_at__gt=participant.last_read_at
        ).exclude(
            sender=request.user
        ).count()