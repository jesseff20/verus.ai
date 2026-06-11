from django.urls import path

from .views.session_views import SessionView, ClearSessionView, SyncSessionView, SessionsListView, SessionDetailView
from .views.chat_views import chat_stream
from .views.export_views import ExportView, ExportSessionView
from .views.share_views import CreateShareView, GetShareView, DeleteShareView, ListSharesView, RevokeShareView

urlpatterns = [
    path('session/', SessionView.as_view(), name='copilot-session'),
    path('session/clear/', ClearSessionView.as_view(), name='copilot-session-clear'),
    path('session/sync/', SyncSessionView.as_view(), name='copilot-session-sync'),
    path('sessions/', SessionsListView.as_view(), name='copilot-sessions-list'),
    path('session/<str:session_id>/', SessionDetailView.as_view(), name='copilot-session-detail'),
    path('chat/stream/', chat_stream, name='copilot-chat-stream'),
    path('export/', ExportView.as_view(), name='copilot-export'),
    path('export-session/', ExportSessionView.as_view(), name='copilot-export-session'),

    # Compartilhamento
    path('share/create/', CreateShareView.as_view(), name='copilot-share-create'),
    path('share/<str:share_code>/', GetShareView.as_view(), name='copilot-share-get'),
    path('share/<str:share_code>/delete/', DeleteShareView.as_view(), name='copilot-share-delete'),
    path('share/list/', ListSharesView.as_view(), name='copilot-share-list'),
    path('share/<str:share_code>/revoke/', RevokeShareView.as_view(), name='copilot-share-revoke'),
]
