"""
URLs para Integração com Tribunais.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TribunalIntegrationViewSet,
    ProcessSyncViewSet,
    PetitionProtocolViewSet,
    sync_process,
)

app_name = 'integration'

router = DefaultRouter()
router.register(r'tribunais', TribunalIntegrationViewSet, basename='tribunal')
router.register(r'processes', ProcessSyncViewSet, basename='process-sync')
router.register(r'petitions', PetitionProtocolViewSet, basename='petition')

urlpatterns = [
    path('', include(router.urls)),
    path('processes/sync/', sync_process, name='sync-process'),
]
