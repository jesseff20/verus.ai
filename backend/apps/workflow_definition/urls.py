from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FlowTemplateViewSet

app_name = 'workflow_definition'

router = DefaultRouter()
router.register(r'templates', FlowTemplateViewSet, basename='flow-template')

urlpatterns = [
    path('', include(router.urls)),
]
