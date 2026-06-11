"""
Provider ICP-Brasil — Certificado Digital A1/A3.

Padrão brasileiro de certificação digital (SERPRO/AC Raiz).
Aceito para assinatura qualificada com validade jurídica plena (MP 2.200-2/2001).

Para ativar: instalar biblioteca python-pkcs11 e configurar leitor de cartão.
"""
from django.conf import settings
from .base import SignatureProviderBase, SignatureResult


class ICPBrasilSignatureProvider(SignatureProviderBase):

    @classmethod
    def metadata(cls) -> dict:
        return {
            'id': 'icpbrasil',
            'name': 'ICP-Brasil (Certificado A1/A3)',
            'description': 'Assinatura com certificado digital ICP-Brasil. '
                          'Validade jurídica plena, equivalente a assinatura manuscrita. '
                          'Requer certificado A1 (software) ou A3 (token/cartão).',
            'icon': 'certificate',
            'available': False,  # Requer hardware/certificado
            'requires_config': ['ICP_BRASIL_PKCS11_LIB', 'ICP_BRASIL_SLOT'],
            'validade_anos': 3,
            'aceito_juridicamente': True,
            'lei': 'MP nº 2.200-2/2001',
            'tipo': 'Assinatura Qualificada',
        }

    def is_available(self) -> bool:
        return False  # Requer PKCS#11 hardware token

    def sign(self, content_hash: str, signer, **kwargs) -> SignatureResult:
        raise NotImplementedError(
            'ICP-Brasil requer certificado digital instalado. '
            'Configure ICP_BRASIL_PKCS11_LIB e implemente via python-pkcs11.'
        )

    def verify(self, content_hash: str, signature_data: str,
               public_key_fingerprint: str = '') -> bool:
        raise NotImplementedError('Verificação ICP-Brasil não implementada.')
