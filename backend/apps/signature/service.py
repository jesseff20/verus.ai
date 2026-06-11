"""
Serviço de assinatura digital.

Responsável por:
- Orquestrar a assinatura via qualquer provider
- Registrar a assinatura no banco
- Verificar a validade de uma assinatura
"""
import hashlib
import logging
from datetime import datetime, timezone

from django.db import transaction

from .models import DigitalSignature, SignatureStatus
from .providers import get_provider, list_providers

logger = logging.getLogger(__name__)


def _hash_content(content: str | bytes) -> str:
    """Calcula o SHA-256 de um conteúdo e retorna hex."""
    if isinstance(content, str):
        content = content.encode('utf-8')
    return hashlib.sha256(content).hexdigest()


@transaction.atomic
def sign_document(
    *,
    signer,
    content: str | bytes,
    document_type: str,
    document_ref: str,
    document_title: str = '',
    provider_name: str = 'internal',
    organ=None,
    request_ip: str = '',
    request_ua: str = '',
    **provider_kwargs,
) -> DigitalSignature:
    """
    Assina um documento via o provider especificado.

    Args:
        signer: User Django (o assinante)
        content: conteúdo a assinar (str ou bytes). Será convertido para hash.
        document_type: tipo do documento ('despacho', 'parecer', 'peticao', etc.)
        document_ref: ID do objeto assinado (UUID como string)
        document_title: título legível para exibição
        provider_name: nome do provider (default: 'internal')
        organ: Organ Django (para isolamento)
        request_ip: IP do requisitante para auditoria
        request_ua: User-Agent para auditoria
        **provider_kwargs: kwargs extras passados ao provider

    Returns:
        DigitalSignature criada e salva

    Raises:
        ValueError: provider não encontrado ou assinatura falhou
    """
    content_hash = _hash_content(content)

    provider = get_provider(provider_name)
    if not provider.is_available():
        raise ValueError(
            f'Provider "{provider_name}" não está disponível. '
            'Verifique as configurações ou use o provider interno.'
        )

    result = provider.sign(content_hash, signer, **provider_kwargs)
    if not result.success:
        raise ValueError(f'Falha na assinatura: {result.error}')

    now = datetime.now(tz=timezone.utc)

    sig = DigitalSignature.objects.create(
        signer=signer,
        document_type=document_type,
        document_ref=document_ref,
        document_title=document_title,
        content_hash=content_hash,
        provider=provider_name,
        status=SignatureStatus.SIGNED,
        signature_data=result.signature_data,
        public_key_fingerprint=result.public_key_fingerprint,
        signed_at=now,
        expires_at=result.expires_at,
        signer_ip=request_ip or None,
        signer_user_agent=request_ua[:500] if request_ua else '',
        organ=organ,
    )

    logger.info(
        'Documento assinado: type=%s ref=%s provider=%s signer=%s',
        document_type, document_ref, provider_name, signer.id
    )
    return sig


def verify_signature(signature_id: str) -> dict:
    """
    Verifica a validade de uma assinatura pelo ID.

    Returns:
        {'valid': bool, 'reason': str, 'signature': DigitalSignature}
    """
    try:
        sig = DigitalSignature.objects.select_related('signer').get(pk=signature_id)
    except DigitalSignature.DoesNotExist:
        return {'valid': False, 'reason': 'Assinatura não encontrada.'}

    if sig.status == SignatureStatus.REVOKED:
        return {'valid': False, 'reason': 'Assinatura foi revogada.', 'signature': sig}

    if sig.expires_at:
        from datetime import timezone
        if sig.expires_at < datetime.now(tz=timezone.utc):
            sig.status = SignatureStatus.EXPIRED
            sig.save(update_fields=['status'])
            return {'valid': False, 'reason': 'Assinatura expirada.', 'signature': sig}

    provider = get_provider(sig.provider)
    valid = provider.verify(sig.content_hash, sig.signature_data, sig.public_key_fingerprint)

    return {
        'valid': valid,
        'reason': 'Assinatura válida.' if valid else 'Assinatura inválida (hash não confere).',
        'signature': sig,
    }


def get_document_signatures(document_ref: str, document_type: str = '') -> list:
    """Retorna todas as assinaturas de um documento."""
    qs = DigitalSignature.objects.filter(document_ref=document_ref)
    if document_type:
        qs = qs.filter(document_type=document_type)
    return list(qs.select_related('signer').order_by('-signed_at'))


def available_providers() -> list[dict]:
    """Retorna lista de providers com status de disponibilidade."""
    return list_providers()
