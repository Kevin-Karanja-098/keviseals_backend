from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Message

User = get_user_model()

def single_page_chat_view(request):
    """Renders the unified login + chat interface wrapper."""
    return render(request, "chat/index.html")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_users_api(request):
    """Simple user retrieval fallback endpoint."""
    users = User.objects.exclude(id=request.user.id).values('id', 'email', 'role')
    return JsonResponse({"users": list(users)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_users_with_meta(request):
    """Fetches users, annotating role types and counting unread incoming messages."""
    current_user = request.user
    users = User.objects.exclude(id=current_user.id)
    
    user_list = []
    for u in users:
        # Calculate unread message counts from this specific user
        unread_count = Message.objects.filter(
            sender=u, 
            receiver=current_user, 
            is_read=False
        ).count()
        
        user_list.append({
            "id": u.id,
            "email": u.email,
            "role": getattr(u, 'role', 'User'),
            "unread_count": unread_count,
            "is_online": False  # Handled dynamically by real-time WebSocket presence updates
        })
        
    return JsonResponse({"users": user_list})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_chat_history_api(request, other_user_id):
    """Fetches all past conversation logs between the authenticated user and a peer."""
    # FIX: Update the database state for incoming unread messages from this user before loading history
    Message.objects.filter(
        sender_id=other_user_id,
        receiver=request.user,
        is_read=False
    ).update(is_read=True)

    # Query full bidirectional historical logs
    messages = Message.objects.filter(
        (Q(sender=request.user, receiver_id=other_user_id)) |
        (Q(sender_id=other_user_id, receiver=request.user))
    ).order_by('timestamp')
    
    data = []
    for m in messages:
        # Resolve the attachment absolute path safely if it exists
        file_url = None
        if m.file_attachment:
            try:
                file_url = request.build_absolute_uri(m.file_attachment.url)
            except ValueError:
                file_url = str(m.file_attachment)

        # Added "is_read" state parsing to feed historical read indicators cleanly to front-end
        data.append({
            "id": m.id,
            "sender_id": m.sender.id,
            "sender_email": m.sender.email,
            "message": m.content if not m.is_deleted else "This message was deleted",
            "file_url": file_url,
            "file_type": m.file_type,
            "is_edited": m.is_edited,
            "is_deleted": m.is_deleted,
            "is_read": m.is_read,
            "timestamp": m.timestamp.strftime("%H:%M")  # Matches consumer clock string
        })
        
    return JsonResponse({"messages": data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_file_attachment(request):
    """Handles secure file uploads for images, documents, and PDFs, creating a persistent log entry."""
    if 'file' not in request.FILES or 'receiver_id' not in request.data:
        return JsonResponse({"error": "Missing parameters"}, status=400)
        
    receiver_id = request.data['receiver_id']
    uploaded_file = request.FILES['file']
    
    # Basic file categorization mapping
    content_type = uploaded_file.content_type
    file_type = 'document'
    if content_type.startswith('image/'):
        file_type = 'image'
    elif content_type == 'application/pdf':
        file_type = 'pdf'
        
    # Commit directly into the FileField storage location layout
    msg = Message.objects.create(
        sender=request.user,
        receiver_id=receiver_id,
        file_attachment=uploaded_file,
        file_type=file_type,
        content=uploaded_file.name,
        is_read=False
    )
    
    return JsonResponse({
        "status": "uploaded",
        "message_id": msg.id,
        "file_url": request.build_absolute_uri(msg.file_attachment.url),
        "file_type": msg.file_type,
        "timestamp": msg.timestamp.strftime("%H:%M")
    })