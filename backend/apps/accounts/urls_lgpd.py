"""
URLs LGPD - /api/v1/auth/lgpd/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_lgpd import (
    ConsentTermViewSet,
    ConsentRecordViewSet,
    DataProcessingActivityViewSet,
    DataSubjectRequestViewSet,
    LGPDAIViewSet,
)

router = DefaultRouter()
router.register(r'consent-terms', ConsentTermViewSet, basename='consent-term')
router.register(r'consent-records', ConsentRecordViewSet, basename='consent-record')
router.register(r'data-processing-activities', DataProcessingActivityViewSet, basename='data-processing-activity')
router.register(r'data-subject-requests', DataSubjectRequestViewSet, basename='data-subject-request')
router.register(r'ai', LGPDAIViewSet, basename='lgpd-ai')

urlpatterns = [
    path('', include(router.urls)),
]
