"""
URLs do Portal do Cliente — autenticacao, consulta de casos, documentos, contratos,
mensagens, financeiro, consentimentos, audiencias e perfil.
"""
from django.urls import path
from . import views_client_portal

urlpatterns = [
    # Auth
    path('login/', views_client_portal.client_portal_login, name='client-portal-login'),
    path('me/', views_client_portal.client_portal_me, name='client-portal-me'),

    # Cases
    path('cases/', views_client_portal.client_portal_cases, name='client-portal-cases'),
    path('cases/<uuid:case_id>/', views_client_portal.client_portal_case_detail, name='client-portal-case-detail'),
    path('cases/<uuid:case_id>/documents/', views_client_portal.client_portal_case_documents, name='client-portal-case-documents'),
    path('cases/<uuid:case_id>/documents/upload/', views_client_portal.client_portal_upload_document, name='client-portal-upload-document'),

    # Contracts & Signatures
    path('contracts/', views_client_portal.client_portal_contracts, name='client-portal-contracts'),
    path('contracts/<uuid:contract_id>/', views_client_portal.client_portal_contract_detail, name='client-portal-contract-detail'),
    path('contracts/<uuid:contract_id>/sign/', views_client_portal.client_portal_sign_contract, name='client-portal-sign-contract'),

    # Consents (LGPD)
    path('consents/', views_client_portal.client_portal_my_consents, name='client-portal-consents'),
    path('consents/pending/', views_client_portal.client_portal_pending_consents, name='client-portal-pending-consents'),
    path('consents/<uuid:term_id>/accept/', views_client_portal.client_portal_accept_consent, name='client-portal-accept-consent'),

    # Messages
    path('messages/', views_client_portal.client_portal_messages, name='client-portal-messages'),
    path('messages/<uuid:message_id>/read/', views_client_portal.client_portal_mark_read, name='client-portal-mark-read'),

    # Financial
    path('financial/', views_client_portal.client_portal_financial, name='client-portal-financial'),

    # Notifications
    path('notifications/', views_client_portal.client_portal_notifications, name='client-portal-notifications'),

    # Profile
    path('profile/', views_client_portal.client_portal_profile, name='client-portal-profile'),
    path('profile/change-password/', views_client_portal.client_portal_change_password, name='client-portal-change-password'),

    # Hearings
    path('hearings/', views_client_portal.client_portal_hearings, name='client-portal-hearings'),

    # Copilot (Client AI Assistant)
    path('copilot/', views_client_portal.client_portal_copilot, name='client-copilot'),
    path('copilot/sugestoes/', views_client_portal.client_portal_copilot_suggestions, name='client-copilot-suggestions'),

    # Admin
    path('activate/<uuid:client_id>/', views_client_portal.client_portal_activate, name='client-portal-activate'),
]
