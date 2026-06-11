from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FormTemplateViewSet, FormAssistantViewSet

app_name = 'forms'

router = DefaultRouter()
router.register(r'templates', FormTemplateViewSet, basename='form')
router.register(r'assistants', FormAssistantViewSet, basename='form-assistant')

urlpatterns = [
    path('', include(router.urls)),
]
