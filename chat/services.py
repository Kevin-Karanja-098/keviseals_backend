from django.db import transaction

from .models import (
    Conversation,
    ConversationParticipant,
)


@transaction.atomic
def get_or_create_private_conversation(user1, user2):

    conversations = Conversation.objects.filter(
        participants__user=user1
    ).distinct()

    for conversation in conversations:

        users = set(
            conversation.participants.values_list(
                "user_id",
                flat=True,
            )
        )

        if users == {user1.id, user2.id}:
            return conversation

    conversation = Conversation.objects.create()

    ConversationParticipant.objects.create(
        conversation=conversation,
        user=user1,
    )

    ConversationParticipant.objects.create(
        conversation=conversation,
        user=user2,
    )

    return conversation