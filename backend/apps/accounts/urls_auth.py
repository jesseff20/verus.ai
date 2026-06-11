"""
URLs para o fluxo de confirmação de e-mail e reset de senha.

Endpoints adicionados ao prefixo /api/v1/auth/:
- POST register-with-confirm/ — Registro com confirmação de e-mail
- POST confirm-email/ — Confirmação de e-mail via token
- POST request-password-reset/ — Solicita link de reset de senha
- POST reset-password/ — Executa reset de senha via token
"""
from django.urls import path, include
from . import views_auth

app_name = 'auth_confirm'

urlpatterns = [
    # Registro com confirmação de e-mail
    path(
        'register-with-confirm/',
        views_auth.register_with_confirm,
        name='register_with_confirm',
    ),
    # Confirmação de e-mail via token JWT
    path(
        'confirm-email/',
        views_auth.confirm_email,
        name='confirm_email',
    ),
    # Fluxo de reset de senha
    path('', include('apps.accounts.urls_password')),
]
