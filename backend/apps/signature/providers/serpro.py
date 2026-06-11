"""
Provider SERPRO — Assinador SERPRO (serviço federal).
Para ativar, configure: SERPRO_API_KEY, SERPRO_CPFCNPJ_RESPONSAVEL
"""
from django.conf import settings
from .base import SignatureProviderBase, SignatureResult


class SerproSignatureProvider(SignatureProviderBase):

    @classmethod
    def metadata(cls) -> dict:
        return {
            'id': 'serpro',
            'name': 'SERPRO (Assinador)',
            'description': 'Assinatura via Assinador SERPRO. '
                          'Integrado aos sistemas do Governo Federal.',
            'icon': 'server',
            'available': bool(getattr(settings, 'SERPRO_API_KEY', None)),
            'requires_config': ['SERPRO_API_KEY', 'SERPRO_CPFCNPJ_RESPONSAVEL'],
            'validade_anos': 1,
            'aceito_juridicamente': True,
        }

    def is_available(self) -> bool:
        return bool(getattr(settings, 'SERPRO_API_KEY', None))

    def sign(self, content_hash: str, signer, **kwargs) -> SignatureResult:
        raise NotImplementedError('SERPRO: configure SERPRO_API_KEY e implemente via API REST.')

    def verify(self, content_hash: str, signature_data: str, public_key_fingerprint: str = '') -> bool:
        raise NotImplementedError()
