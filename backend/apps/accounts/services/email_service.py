"""
Serviço de envio de e-mails transacionais (confirmação e boas-vindas).

Usa EMAIL_PROVIDER_API_KEY do .env para enviar via API REST (provedor externo).
Em desenvolvimento (DEBUG=True), usa o console backend do Django.
"""
import logging
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def _get_env(name, default=None):
    """Retorna variável de ambiente do settings ou default."""
    return getattr(settings, name, default) or default


def enviar_email_html(destinatario, assunto, template_name, contexto):
    """
    Envia e-mail HTML usando o template especificado.

    Args:
        destinatario: String ou lista de e-mails destinatários
        assunto: Assunto do e-mail
        template_name: Nome do template (ex: 'emails/confirm_email.html')
        contexto: Dict com variáveis para o template
    """
    if isinstance(destinatario, str):
        destinatario = [destinatario]

    # Renderiza o template HTML
    contexto['app_base_url'] = _get_env('APP_BASE_URL', 'http://localhost:3000')
    contexto['frontend_url'] = _get_env('FRONTEND_URL', 'http://localhost:3000')

    html_content = render_to_string(template_name, contexto)
    text_content = strip_tags(html_content)  # Fallback plain text

    # Em DEBUG, usa console backend do Django
    if settings.DEBUG:
        _enviar_console(destinatario, assunto, text_content, html_content)
    else:
        _enviar_api(destinatario, assunto, text_content, html_content)

    logger.info('E-mail enviado para %s — assunto: %s', destinatario, assunto)


def _enviar_console(destinatario, assunto, text_content, html_content):
    """Envia e-mail via console backend do Django (desenvolvimento)."""
    from django.core.mail import send_mail
    send_mail(
        subject=assunto,
        message=text_content,
        from_email=_get_env(
            'EMAIL_FROM',
            'noreply-bravonix@ictatechnology.com.br'
        ),
        recipient_list=destinatario,
        html_message=html_content,
        fail_silently=False,
    )


def _enviar_api(destinatario, assunto, text_content, html_content):
    """
    Envia e-mail via API REST do provedor externo.
    Usa o serviço Resend (compatível com chave re_*).
    """
    api_key = _get_env('EMAIL_PROVIDER_API_KEY', '')
    if not api_key:
        logger.error('EMAIL_PROVIDER_API_KEY não configurada')
        return

    url = 'https://api.resend.com/emails'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    payload = {
        'from': _get_env('EMAIL_FROM', 'noreply-bravonix@ictatechnology.com.br'),
        'to': destinatario,
        'subject': assunto,
        'html': html_content,
        'text': text_content,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        logger.info('API Resend: e-mail enviado — id=%s', resp.json().get('id'))
    except requests.RequestException as e:
        logger.error('Falha ao enviar e-mail via API: %s', str(e))


def enviar_email_confirmacao(destinatario, nome_usuario, token):
    """
    Envia e-mail de confirmação de cadastro com link de ativação.

    Args:
        destinatario: E-mail do destinatário
        nome_usuario: Nome completo do usuário
        token: Token JWT de confirmação
    """
    app_base_url = _get_env('APP_BASE_URL', 'http://localhost:3000')
    link_confirmacao = f"{app_base_url}/auth/confirm?token={token}"

    contexto = {
        'nome': nome_usuario,
        'link_confirmacao': link_confirmacao,
        'expiracao': '30 dias',
    }

    enviar_email_html(
        destinatario=destinatario,
        assunto='Verus.AI — Confirme seu cadastro',
        template_name='emails/confirm_email.html',
        contexto=contexto,
    )


def enviar_email_boas_vindas(destinatario, nome_usuario):
    """
    Envia e-mail de boas-vindas informando que o login está liberado.

    Args:
        destinatario: E-mail do destinatário
        nome_usuario: Nome completo do usuário
    """
    frontend_url = _get_env('FRONTEND_URL', 'http://localhost:3000')
    link_login = f"{frontend_url}/login"

    contexto = {
        'nome': nome_usuario,
        'link_login': link_login,
    }

    enviar_email_html(
        destinatario=destinatario,
        assunto='Verus.AI — Conta ativada com sucesso!',
        template_name='emails/welcome.html',
        contexto=contexto,
    )


# =============================================================================
# FUNÇÕES PARA RESET DE SENHA
# =============================================================================


def enviar_email_reset_senha(destinatario, nome_usuario, token):
    """
    Envia e-mail com link para reset de senha.

    Args:
        destinatario: E-mail do destinatário
        nome_usuario: Nome completo do usuário
        token: Token JWT de reset de senha
    """
    app_base_url = _get_env('APP_BASE_URL', 'http://localhost:3000')
    link_reset = f"{app_base_url}/auth/reset-password?token={token}"

    contexto = {
        'nome': nome_usuario,
        'link_reset': link_reset,
        'expiracao': '1 hora',
    }

    enviar_email_html(
        destinatario=destinatario,
        assunto='Verus.AI — Redefinição de senha solicitada',
        template_name='emails/reset_password.html',
        contexto=contexto,
    )


def enviar_email_senha_alterada(destinatario, nome_usuario):
    """
    Envia e-mail de confirmação informando que a senha foi alterada.

    Args:
        destinatario: E-mail do destinatário
        nome_usuario: Nome completo do usuário
    """
    app_base_url = _get_env('APP_BASE_URL', 'http://localhost:3000')

    contexto = {
        'nome': nome_usuario,
        'link_login': f"{app_base_url}/login",
    }

    enviar_email_html(
        destinatario=destinatario,
        assunto='Verus.AI — Sua senha foi alterada com sucesso',
        template_name='emails/password_changed.html',
        contexto=contexto,
    )
