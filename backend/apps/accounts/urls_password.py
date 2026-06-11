"""
URLs para o fluxo de reset de senha.

Endpoints adicionados ao prefixo /api/v1/auth/:
- POST request-password-reset/ — Solicita link de reset (informa e-mail)
- POST reset-password/ — Executa reset (token + nova senha)
"""
from django.urls import path
from . import views_password

app_name = 'password_reset'

urlpatterns = [
    # Solicitação de reset de senha (informa e-mail)
    path(
        'request-password-reset/',
        views_password.request_password_reset,
        name='request_password_reset',
    ),
    # Execução do reset de senha (token + nova senha)
    path(
        'reset-password/',
        views_password.reset_password,
        name='reset_password',
    ),
]
