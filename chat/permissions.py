from rest_framework.permissions import BasePermission

from .models import ConversationParticipant


class IsConversationParticipant(BasePermission):

    def has_object_permission(self, request, view, obj):

        return ConversationParticipant.objects.filter(
            conversation=obj,
            user=request.user
        ).exists()