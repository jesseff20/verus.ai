"""
Integração DocuSign — Assinatura Digital.
Preparado para quando as credenciais estiverem disponíveis.

Documentação: https://developers.docusign.com/
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class DocuSignService:
    """Integração com DocuSign para assinatura digital."""

    AUTH_URL = 'https://account-d.docusign.com'  # Demo
    PROD_AUTH_URL = 'https://account.docusign.com'
    API_BASE = 'https://demo.docusign.net/restapi/v2.1'
    PROD_API_BASE = 'https://na1.docusign.net/restapi/v2.1'

    def __init__(self):
        self.integration_key = getattr(settings, 'DOCUSIGN_INTEGRATION_KEY', '')
        self.secret_key = getattr(settings, 'DOCUSIGN_SECRET_KEY', '')
        self.account_id = getattr(settings, 'DOCUSIGN_ACCOUNT_ID', '')
        self.use_production = getattr(settings, 'DOCUSIGN_PRODUCTION', False)
        self.api_base = self.PROD_API_BASE if self.use_production else self.API_BASE

    @property
    def is_configured(self) -> bool:
        return bool(self.integration_key and self.secret_key and self.account_id)

    def get_auth_url(self, redirect_uri: str, state: str = '') -> dict:
        """Gera URL de autorização OAuth2."""
        if not self.integration_key:
            return {
                'success': False,
                'error': 'DocuSign não configurado.',
                'setup_required': True,
                'env_vars': ['DOCUSIGN_INTEGRATION_KEY', 'DOCUSIGN_SECRET_KEY', 'DOCUSIGN_ACCOUNT_ID'],
            }

        import urllib.parse
        base = self.PROD_AUTH_URL if self.use_production else self.AUTH_URL
        params = {
            'response_type': 'code',
            'scope': 'signature',
            'client_id': self.integration_key,
            'redirect_uri': redirect_uri,
            'state': state,
        }
        return {'success': True, 'auth_url': f"{base}/oauth/auth?{urllib.parse.urlencode(params)}"}

    def exchange_code(self, code: str, redirect_uri: str) -> dict:
        """Troca authorization code por access token."""
        if not self.is_configured:
            return {'success': False, 'error': 'DocuSign não configurado.', 'setup_required': True}

        import base64
        auth_header = base64.b64encode(f"{self.integration_key}:{self.secret_key}".encode()).decode()
        base = self.PROD_AUTH_URL if self.use_production else self.AUTH_URL

        try:
            response = requests.post(
                f"{base}/oauth/token",
                data={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': redirect_uri},
                headers={'Authorization': f'Basic {auth_header}'},
                timeout=15,
            )
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def create_envelope(self, access_token: str, document_base64: str,
                        document_name: str, signers: list, subject: str = '') -> dict:
        """
        Cria envelope (documento para assinatura).
        signers: [{'name': 'Nome', 'email': 'email@test.com', 'routing_order': '1'}]
        """
        if not self.is_configured:
            return {'success': False, 'error': 'DocuSign não configurado.', 'setup_required': True}

        signer_tabs = []
        for i, signer in enumerate(signers, 1):
            signer_tabs.append({
                'email': signer['email'],
                'name': signer['name'],
                'recipientId': str(i),
                'routingOrder': signer.get('routing_order', str(i)),
                'tabs': {
                    'signHereTabs': [{'documentId': '1', 'pageNumber': '1', 'xPosition': '100', 'yPosition': '700'}],
                    'dateSignedTabs': [{'documentId': '1', 'pageNumber': '1', 'xPosition': '100', 'yPosition': '750'}],
                },
            })

        envelope = {
            'emailSubject': subject or f'Assinar: {document_name}',
            'documents': [{
                'documentBase64': document_base64,
                'name': document_name,
                'fileExtension': 'pdf',
                'documentId': '1',
            }],
            'recipients': {'signers': signer_tabs},
            'status': 'sent',
        }

        try:
            response = requests.post(
                f"{self.api_base}/accounts/{self.account_id}/envelopes",
                json=envelope,
                headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'},
                timeout=30,
            )
            if response.status_code in (200, 201):
                return {'success': True, 'data': response.json()}
            return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_envelope_status(self, access_token: str, envelope_id: str) -> dict:
        """Consulta status do envelope."""
        try:
            response = requests.get(
                f"{self.api_base}/accounts/{self.account_id}/envelopes/{envelope_id}",
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=15,
            )
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}
