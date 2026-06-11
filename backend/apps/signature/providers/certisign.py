"""
Provider Certisign — AC brasileira autorizada ICP-Brasil.
Para ativar, configure: CERTISIGN_API_KEY, CERTISIGN_API_URL
"""
from django.conf import settings
from .base import SignatureProviderBase, SignatureResult


class CertisignProvider(SignatureProviderBase):

    @classmethod
    def metadata(cls) -> dict:
        return {
            'id': 'certisign',
            'name': 'Certisign',
            'description': 'Assinatura via Certisign (AC ICP-Brasil). '
                          'Aceita para documentos com exigência legal de certificação ICP-Brasil.',
            'icon': 'award',
            'available': bool(getattr(settings, 'CERTISIGN_API_KEY', None)),
            'requires_config': ['CERTISIGN_API_KEY', 'CERTISIGN_API_URL'],
            'validade_anos': 3,
            'aceito_juridicamente': True,
            'lei': 'MP nº 2.200-2/2001',
        }

    def is_available(self) -> bool:
        return bool(getattr(settings, 'CERTISIGN_API_KEY', None))

    def sign(self, content_hash: str, signer, **kwargs) -> SignatureResult:
        raise NotImplementedError('Certisign: configure CERTISIGN_API_KEY e implemente via API REST.')

    def verify(self, content_hash: str, signature_data: str, public_key_fingerprint: str = '') -> bool:
        raise NotImplementedError()
