"""
Integração D4Sign — Assinatura Digital com certificado ICP-Brasil.
Preparado para quando as credenciais estiverem disponíveis.

Documentação: https://docapi.d4sign.com.br/
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class D4SignService:
    """Integração com D4Sign para assinatura digital ICP-Brasil."""

    BASE_URL = 'https://secure.d4sign.com.br/api/v1'
    SANDBOX_URL = 'https://sandbox.d4sign.com.br/api/v1'

    def __init__(self):
        self.api_key = getattr(settings, 'D4SIGN_API_KEY', '')
        self.crypto_key = getattr(settings, 'D4SIGN_CRYPTO_KEY', '')
        self.use_sandbox = getattr(settings, 'D4SIGN_SANDBOX', True)
        self.base_url = self.SANDBOX_URL if self.use_sandbox else self.BASE_URL

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.crypto_key)

    def _get_headers(self):
        return {'tokenAPI': self.api_key, 'cryptKey': self.crypto_key}

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        if not self.is_configured:
            return {
                'success': False,
                'error': 'D4Sign não configurado. Configure D4SIGN_API_KEY e D4SIGN_CRYPTO_KEY nas variáveis de ambiente.',
                'setup_required': True,
                'env_vars': ['D4SIGN_API_KEY', 'D4SIGN_CRYPTO_KEY', 'D4SIGN_SANDBOX'],
            }

        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.request(method, url, headers=self._get_headers(), timeout=30, **kwargs)
            if response.status_code in (200, 201):
                return {'success': True, 'data': response.json()}
            else:
                return {'success': False, 'error': response.text, 'status_code': response.status_code}
        except Exception as e:
            logger.error(f"D4Sign API error: {e}")
            return {'success': False, 'error': str(e)}

    def list_safes(self) -> dict:
        """Lista cofres (safes) disponíveis."""
        return self._request('GET', 'safes')

    def upload_document(self, safe_id: str, file_path: str, filename: str) -> dict:
        """Envia documento para assinatura."""
        with open(file_path, 'rb') as f:
            files = {'file': (filename, f, 'application/pdf')}
            return self._request('POST', f'documents/{safe_id}/upload', files=files)

    def create_signature_list(self, document_id: str, signers: list) -> dict:
        """
        Cria lista de signatários.
        signers: [{'email': 'x@y.com', 'act': '1', 'foreign': '0', 'certificadoicpbr': '1'}]
        """
        return self._request('POST', f'documents/{document_id}/createlist', json={'signers': signers})

    def send_to_sign(self, document_id: str, message: str = '') -> dict:
        """Envia documento para assinatura."""
        data = {'message': message, 'skip_email': '0', 'workflow': '0'}
        return self._request('POST', f'documents/{document_id}/sendtosigner', json=data)

    def get_document_status(self, document_id: str) -> dict:
        """Consulta status do documento."""
        return self._request('GET', f'documents/{document_id}')

    def download_signed(self, document_id: str) -> dict:
        """Download do documento assinado."""
        return self._request('GET', f'documents/{document_id}/download')

    def cancel_document(self, document_id: str, comment: str = '') -> dict:
        """Cancela documento."""
        return self._request('POST', f'documents/{document_id}/cancel', json={'comment': comment})
