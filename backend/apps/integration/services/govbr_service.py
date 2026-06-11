"""
Integração GOV.BR — Autenticação e Assinatura Digital via Login Único.
Preparado para quando as credenciais estiverem disponíveis.

Documentação: https://manual-roteiro-integracao-login-unico.servicos.gov.br/
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class GovBRService:
    """Integração com Login Único GOV.BR e Assinatura Eletrônica Gov.br."""

    # Ambientes
    AUTH_URL_STAGING = 'https://sso.staging.acesso.gov.br'
    AUTH_URL_PROD = 'https://sso.acesso.gov.br'

    SIGN_URL_STAGING = 'https://assinador.staging.iti.br'
    SIGN_URL_PROD = 'https://assinador.iti.br'

    def __init__(self):
        self.client_id = getattr(settings, 'GOVBR_CLIENT_ID', '')
        self.client_secret = getattr(settings, 'GOVBR_CLIENT_SECRET', '')
        self.use_production = getattr(settings, 'GOVBR_PRODUCTION', False)
        self.auth_url = self.AUTH_URL_PROD if self.use_production else self.AUTH_URL_STAGING
        self.sign_url = self.SIGN_URL_PROD if self.use_production else self.SIGN_URL_STAGING

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def get_login_url(self, redirect_uri: str, state: str = '', nonce: str = '') -> dict:
        """Gera URL de login GOV.BR (OpenID Connect)."""
        if not self.is_configured:
            return {
                'success': False,
                'error': 'GOV.BR não configurado.',
                'setup_required': True,
                'env_vars': ['GOVBR_CLIENT_ID', 'GOVBR_CLIENT_SECRET', 'GOVBR_PRODUCTION'],
                'docs': 'https://manual-roteiro-integracao-login-unico.servicos.gov.br/',
            }

        import urllib.parse
        import secrets

        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'scope': 'openid email phone profile govbr_empresa',
            'redirect_uri': redirect_uri,
            'nonce': nonce or secrets.token_urlsafe(32),
            'state': state or secrets.token_urlsafe(32),
        }

        return {
            'success': True,
            'auth_url': f"{self.auth_url}/authorize?{urllib.parse.urlencode(params)}",
            'state': params['state'],
            'nonce': params['nonce'],
        }

    def exchange_code(self, code: str, redirect_uri: str) -> dict:
        """Troca authorization code por tokens."""
        if not self.is_configured:
            return {'success': False, 'error': 'GOV.BR não configurado.', 'setup_required': True}

        try:
            response = requests.post(
                f"{self.auth_url}/token",
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': redirect_uri,
                },
                auth=(self.client_id, self.client_secret),
                timeout=15,
            )
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_user_info(self, access_token: str) -> dict:
        """Obtém dados do usuário autenticado."""
        try:
            response = requests.get(
                f"{self.auth_url}/userinfo",
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'cpf': data.get('sub', ''),
                    'name': data.get('name', ''),
                    'email': data.get('email', ''),
                    'phone': data.get('phone_number', ''),
                    'picture': data.get('picture', ''),
                    'email_verified': data.get('email_verified', False),
                    'phone_verified': data.get('phone_number_verified', False),
                    'nivel_conta': data.get('amr', []),  # bronze, prata, ouro
                }
            return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def sign_document(self, access_token: str, document_base64: str,
                      document_name: str, mime_type: str = 'application/pdf') -> dict:
        """
        Assina documento via Assinatura Eletrônica Gov.br.
        Requer nível de conta Prata ou Ouro.
        """
        if not self.is_configured:
            return {'success': False, 'error': 'GOV.BR não configurado.', 'setup_required': True}

        try:
            payload = {
                'document': {
                    'content': document_base64,
                    'content-type': mime_type,
                    'name': document_name,
                },
                'signature_type': 'CAdES',  # CAdES for PDF
            }

            response = requests.post(
                f"{self.sign_url}/externo/v2/assinarPKCS7",
                json=payload,
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=60,
            )
            if response.status_code in (200, 201):
                return {'success': True, 'data': response.json()}
            return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def verify_signature(self, signed_document_base64: str) -> dict:
        """Verifica assinatura eletrônica."""
        try:
            response = requests.post(
                f"{self.sign_url}/externo/v2/validarAssinatura",
                json={'signed_document': signed_document_base64},
                timeout=30,
            )
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_confiabilidade(self, access_token: str) -> dict:
        """Verifica nível de confiabilidade (bronze/prata/ouro) do selo GOV.BR."""
        try:
            response = requests.get(
                f"{self.auth_url}/api/v1/confiabilidades",
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10,
            )
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}
