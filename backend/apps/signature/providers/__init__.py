from .base import SignatureProviderBase, SignatureResult
from .internal import InternalSignatureProvider
from .govbr import GovBRSignatureProvider
from .icpbrasil import ICPBrasilSignatureProvider
from .docusign import DocuSignProvider
from .certisign import CertisignProvider
from .serpro import SerproSignatureProvider

REGISTRY: dict[str, type[SignatureProviderBase]] = {
    'internal': InternalSignatureProvider,
    'govbr': GovBRSignatureProvider,
    'icpbrasil': ICPBrasilSignatureProvider,
    'docusign': DocuSignProvider,
    'certisign': CertisignProvider,
    'serpro': SerproSignatureProvider,
}


def get_provider(name: str) -> SignatureProviderBase:
    cls = REGISTRY.get(name)
    if not cls:
        raise ValueError(f'Provider de assinatura desconhecido: {name}')
    return cls()


def list_providers() -> list[dict]:
    """Retorna lista de providers com metadados."""
    return [cls.metadata() for cls in REGISTRY.values()]
