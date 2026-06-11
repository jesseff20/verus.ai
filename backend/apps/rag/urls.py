"""
URLs para RAG
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RAGQueryViewSet, RAGContextViewSet

app_name = 'rag'

router = DefaultRouter()
router.register(r'queries', RAGQueryViewSet, basename='query')
router.register(r'contexts', RAGContextViewSet, basename='context')

urlpatterns = [
    path('', include(router.urls)),
]
