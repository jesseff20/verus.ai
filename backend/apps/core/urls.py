"""
URLs para o app Core.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import DocumentTypeViewSet, ProcessTypeViewSet, ProcessStatusViewSet, AuditLogViewSet, LLMProviderViewSet, TokenUsageLogViewSet

app_name = 'core'

router = DefaultRouter()
router.register('document-types', DocumentTypeViewSet, basename='document-types')
router.register('process-types', ProcessTypeViewSet, basename='process-types')
router.register('process-statuses', ProcessStatusViewSet, basename='process-statuses')
router.register('audit-logs', AuditLogViewSet, basename='audit-logs')
router.register('llm-providers', LLMProviderViewSet, basename='llm-providers')
router.register('token-usage', TokenUsageLogViewSet, basename='token-usage')

urlpatterns = [
    path('', include(router.urls)),

    # Auditoria de Acessos (#23)
    path('', include('apps.core.urls_audit')),
]
