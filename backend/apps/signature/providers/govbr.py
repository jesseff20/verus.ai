"""
Provider Gov.BR — Assinatura via plataforma de autenticação do Governo Federal.

Para ativar, configure:
  GOVBR_CLIENT_ID=...
  GOVBR_CLIENT_SECRET=...
  GOVBR_REDIRECT_URI=...

Documentação: https://acesso.gov.br/roteiro-tecnico/assinatura/index.html
"""
import logging
from django.conf import settings
from .base import SignatureProviderBase, SignatureResult

logger = logging.getLogger(__name__)


class GovBRSignatureProvider(SignatureProviderBase):
    """
    Integração com Gov.BR Assinatura Digital.
    Requer conta Gov.BR nível Prata ou Ouro.
    Aceita por lei como assinatura eletrônica avançada (Lei 14.063/2020).
    """

    @classmethod
    def metadata(cls) -> dict:
        return {
            'id': 'govbr',
            'name': 'Gov.BR',
            'description': 'Assinatura via conta Gov.BR. Aceita legalmente como '
                          'assinatura eletrônica avançada (Lei 14.063/2020). '
                          'Requer conta nível Prata ou Ouro.',
            'icon': 'govbr',
            'available': bool(getattr(settings, 'GOVBR_CLIENT_ID', None)),
            'requires_config': ['GOVBR_CLIENT_ID', 'GOVBR_CLIENT_SECRET', 'GOVBR_REDIRECT_URI'],
            'validade_anos': 1,
            'aceito_juridicamente': True,
            'lei': 'Lei nº 14.063/2020',
            'nivel_minimo': 'Prata',
        }

    def is_available(self) -> bool:
        return bool(
            getattr(settings, 'GOVBR_CLIENT_ID', None) and
            getattr(settings, 'GOVBR_CLIENT_SECRET', None)
        )

    def sign(self, content_hash: str, signer, **kwargs) -> SignatureResult:
        """
        Fluxo OAuth2 com Gov.BR:
        1. Redirecionar usuário para /authorize
        2. Receber code de retorno
        3. Trocar code por access_token
        4. Chamar /sign com content_hash + access_token
        """
        if not self.is_available():
            return SignatureResult(
                success=False, signature_data='', public_key_fingerprint='',
                signed_at='', expires_at=None,
                error='Gov.BR não configurado. Defina GOVBR_CLIENT_ID e GOVBR_CLIENT_SECRET.'
            )

        # TODO: Implementar fluxo OAuth2 Gov.BR
        # Referência: https://acesso.gov.br/roteiro-tecnico/assinatura/index.html
        raise NotImplementedError(
            'Integração Gov.BR requer configuração OAuth2. '
            'Defina as variáveis de ambiente e implemente o fluxo de redirecionamento.'
        )

    def verify(self, content_hash: str, signature_data: str,
               public_key_fingerprint: str = '') -> bool:
        # TODO: Verificar via API Gov.BR
        raise NotImplementedError('Verificação Gov.BR não implementada.')
