"""
Interface base para todos os providers de assinatura digital.
Cada provider deve implementar esta interface.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class SignatureResult:
    success: bool
    signature_data: str         # Base64 ou token externo
    public_key_fingerprint: str # SHA-256 da chave pública
    signed_at: str              # ISO datetime
    expires_at: Optional[str]   # ISO datetime ou None
    error: Optional[str] = None
    external_id: Optional[str] = None  # ID no sistema externo (GovBR, DocuSign)


class SignatureProviderBase(ABC):
    """
    Interface base para providers de assinatura digital.

    Todos os providers devem implementar:
    - sign(content_hash, signer, **kwargs) → SignatureResult
    - verify(content_hash, signature_data) → bool
    - is_available() → bool
    - metadata() → dict
    """

    @classmethod
    @abstractmethod
    def metadata(cls) -> dict:
        """
        Retorna metadados do provider para exibição na UI.
        Exemplo:
        {
            'id': 'govbr',
            'name': 'Gov.BR',
            'description': 'Assinatura via conta Gov.BR (nível Prata ou Ouro)',
            'icon': 'govbr',
            'available': True,
            'requires_config': ['GOVBR_CLIENT_ID', 'GOVBR_CLIENT_SECRET'],
            'validade_anos': 1,
            'aceito_juridicamente': True,
        }
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Retorna True se o provider está configurado e disponível."""

    @abstractmethod
    def sign(self, content_hash: str, signer, **kwargs) -> SignatureResult:
        """
        Assina o hash do conteúdo.

        Args:
            content_hash: SHA-256 hex do conteúdo a assinar
            signer: instância do User Django
            **kwargs: parâmetros extras do provider (ex: pin para ICP-Brasil)

        Returns:
            SignatureResult com os dados da assinatura
        """

    @abstractmethod
    def verify(self, content_hash: str, signature_data: str,
               public_key_fingerprint: str = '') -> bool:
        """
        Verifica se uma assinatura é válida para o hash dado.

        Returns:
            True se válida, False se inválida ou provider indisponível
        """
