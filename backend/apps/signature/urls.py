from rest_framework.routers import DefaultRouter
from .views import DigitalSignatureViewSet

router = DefaultRouter()
router.register('', DigitalSignatureViewSet, basename='signature')

urlpatterns = router.urls
