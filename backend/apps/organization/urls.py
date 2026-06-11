from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganViewSet, UnitViewSet

app_name = 'organization'

router = DefaultRouter()
router.register(r'organs', OrganViewSet, basename='organ')
router.register(r'units', UnitViewSet, basename='unit')

urlpatterns = [
    path('', include(router.urls)),
]
