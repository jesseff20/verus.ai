"""
Provider DocuSign — Plataforma de assinatura eletrônica internacional.
Para ativar, configure: DOCUSIGN_ACCOUNT_ID, DOCUSIGN_INTEGRATION_KEY, DOCUSIGN_PRIVATE_KEY
"""
from django.conf import settings
from .base import SignatureProviderBase, SignatureResult


class DocuSignProvider(SignatureProviderBase):

    @classmethod
    def metadata(cls) -> dict:
        return {
            'id': 'docusign',
            'name': 'DocuSign',
            'description': 'Assinatura eletrônica DocuSign. Amplamente aceita internacionalmente.',
            'icon': 'pen-tool',
            'available': bool(getattr(settings, 'DOCUSIGN_ACCOUNT_ID', None)),
            'requires_config': ['DOCUSIGN_ACCOUNT_ID', 'DOCUSIGN_INTEGRATION_KEY', 'DOCUSIGN_PRIVATE_KEY'],
            'validade_anos': 1,
            'aceito_juridicamente': True,
        }

    def is_available(self) -> bool:
        return bool(getattr(settings, 'DOCUSIGN_ACCOUNT_ID', None))

    def sign(self, content_hash: str, signer, **kwargs) -> SignatureResult:
        raise NotImplementedError('DocuSign: configure DOCUSIGN_ACCOUNT_ID e implemente JWT Grant flow.')

    def verify(self, content_hash: str, signature_data: str, public_key_fingerprint: str = '') -> bool:
        raise NotImplementedError()
