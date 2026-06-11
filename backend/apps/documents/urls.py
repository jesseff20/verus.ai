"""
URLs para Documents
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet, DocumentGeneratorViewSet
from .views.version_views import (
    create_version,
    list_versions,
    get_version_detail,
    get_version_diff,
    rollback_version,
)

app_name = 'documents'

router = DefaultRouter()
router.register(r'items', DocumentViewSet, basename='document')
router.register(r'generators', DocumentGeneratorViewSet, basename='document-generator')

urlpatterns = [
    path('', include(router.urls)),

    # ========== Versionamento Semântico ==========
    path('items/<uuid:document_id>/versions/', list_versions, name='document-versions-list'),
    path('items/<uuid:document_id>/versions/create/', create_version, name='document-version-create'),
    path('items/<uuid:document_id>/versions/<uuid:version_id>/', get_version_detail, name='document-version-detail'),
    path('items/<uuid:document_id>/versions/diff/', get_version_diff, name='document-version-diff'),
    path('items/<uuid:document_id>/versions/<uuid:version_id>/rollback/', rollback_version, name='document-version-rollback'),
]
