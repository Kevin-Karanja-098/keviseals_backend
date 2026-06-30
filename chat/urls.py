from django.urls import path
from . import views

urlpatterns = [
    path("", views.single_page_chat_view, name="chat_home"),
    path("api/users/", views.list_users_api, name="api_users"),
    path("api/messages/<int:other_user_id>/", views.fetch_chat_history_api, name="api_messages"),
    path("api/upload/", views.upload_file_attachment, name="api_upload"),
]


