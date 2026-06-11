from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentTemplateViewSet

app_name = 'templates'

router = DefaultRouter()
router.register(r'', DocumentTemplateViewSet, basename='template')

urlpatterns = [
    path('', include(router.urls)),
]
