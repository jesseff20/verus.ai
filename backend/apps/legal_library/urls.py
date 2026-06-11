"""
URLs para Biblioteca Viva de Argumentos.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LegalArgumentViewSet, ArgumentCollectionViewSet, import_argument

app_name = 'legal_library'

router = DefaultRouter()
router.register(r'arguments', LegalArgumentViewSet, basename='legal-argument')
router.register(r'collections', ArgumentCollectionViewSet, basename='argument-collection')

urlpatterns = [
    path('', include(router.urls)),
    path('import/', import_argument, name='argument-import'),
]
