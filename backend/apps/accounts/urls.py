"""
URLs para autenticação e usuários
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import UserViewSet, AuthViewSet, BrandSettingsViewSet, NotificationViewSet, UserReminderViewSet, NotificationChannelViewSet

app_name = 'accounts'

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'', AuthViewSet, basename='auth')  # Sem prefixo - evita duplicação /auth/auth/
router.register(r'brand-settings', BrandSettingsViewSet, basename='brand-settings')
router.register(r'reminders', UserReminderViewSet, basename='reminder')
router.register(r'notification-channels', NotificationChannelViewSet, basename='notification-channel')

urlpatterns = [
    # JWT Token Refresh (padrão simplejwt)
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Portal do Cliente
    path('client-portal/', include('apps.accounts.urls_client_portal')),

    # LGPD endpoints
    path('lgpd/', include('apps.accounts.urls_lgpd')),

    # Gestão de Equipe
    path('equipes/', include('apps.accounts.urls_teams')),

    # Dashboard Customizável (#24)
    path('dashboard-config/', include('apps.accounts.urls_dashboard_config')),

    # Templates de E-mail (#19)
    path('email-templates/', include('apps.accounts.urls_email_templates')),

    # Fluxo de confirmação de e-mail
    path('', include('apps.accounts.urls_auth')),

    # Router URLs (inclui todos os endpoints de user e auth)
    path('', include(router.urls)),
]
