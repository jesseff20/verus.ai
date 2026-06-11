from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AgentPromptViewSet, AssistantAnalyticsViewSet

app_name = 'agents'

router = DefaultRouter()
# Registrar sem prefixo para que /api/v1/agents/ funcione diretamente
router.register(r'', AgentPromptViewSet, basename='agent')
# Analytics em /api/v1/agents/analytics/
router.register(r'analytics', AssistantAnalyticsViewSet, basename='analytics')

urlpatterns = [
    path('', include(router.urls)),
]
