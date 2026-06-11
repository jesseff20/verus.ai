from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet, legislation_search

app_name = 'kb'

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')

urlpatterns = [
    path('legislation/search/', legislation_search, name='legislation-search'),
    path('', include(router.urls)),
]
