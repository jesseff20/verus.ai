"""
URLs para Colaboração em Tempo Real.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CollaborationSessionViewSet,
    CommentViewSet,
    SuggestionViewSet,
    create_session_for_document,
)

app_name = 'collaboration'

router = DefaultRouter()
router.register(r'sessions', CollaborationSessionViewSet, basename='collaboration-session')
router.register(r'comments', CommentViewSet, basename='collaboration-comment')
router.register(r'suggestions', SuggestionViewSet, basename='collaboration-suggestion')

urlpatterns = [
    path('', include(router.urls)),
    # Endpoint helper para criar sessão a partir de documento
    path('documents/<uuid:document_id>/start-session/', create_session_for_document, name='start-session'),
]
