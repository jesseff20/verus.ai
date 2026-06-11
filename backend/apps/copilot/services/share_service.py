"""
ShareService - Gerencia compartilhamento de sessões do Copilot.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)

SHARE_TTL = 7 * 24 * 3600  # 7 dias


def create_share(
    user_id: int,
    session_id: str,
    shared_with_emails: Optional[List[str]] = None,
    is_public: bool = False,
    expires_days: Optional[int] = None,
) -> str:
    """
    Cria um compartilhamento de sessão.
    Retorna o share_code.
    """
    from apps.copilot.models import CopilotSessionShare
    from apps.accounts.models import User

    user = User.objects.get(id=user_id)

    # Gerar código único
    share_code = CopilotSessionShare.generate_share_code()

    # Verificar unicidade
    while CopilotSessionShare.objects.filter(share_code=share_code).exists():
        share_code = CopilotSessionShare.generate_share_code()

    # Calcular expiração
    expires_at = None
    if expires_days:
        expires_at = timezone.now() + timedelta(days=expires_days)

    share = CopilotSessionShare.objects.create(
        session_id=session_id,
        share_code=share_code,
        created_by=user,
        shared_with_emails=shared_with_emails or [],
        is_public=is_public,
        expires_at=expires_at,
    )

    # Cache para acesso rápido
    cache.set(f'copilot:share:{share_code}', {
        'session_id': session_id,
        'created_by_id': user_id,
        'is_public': is_public,
        'shared_with_emails': shared_with_emails or [],
    }, timeout=SHARE_TTL)

    logger.info(f'[copilot] Sessão compartilhada: {session_id[:8]}... código {share_code}')
    return share_code


def get_share(share_code: str, requesting_user_email: Optional[str] = None) -> Optional[dict]:
    """
    Obtém informações de um compartilhamento.
    Retorna dados da sessão se o usuário tiver acesso, None caso contrário.
    """
    from apps.copilot.models import CopilotSessionShare

    # Tentar cache primeiro
    cached = cache.get(f'copilot:share:{share_code}')
    if cached:
        # Verificar se existe no banco
        try:
            share = CopilotSessionShare.objects.get(share_code=share_code)
        except CopilotSessionShare.DoesNotExist:
            cache.delete(f'copilot:share:{share_code}')
            return None
    else:
        try:
            share = CopilotSessionShare.objects.get(share_code=share_code)
        except CopilotSessionShare.DoesNotExist:
            return None

    # Verificar expiração
    if share.is_expired():
        CopilotSessionShare.objects.filter(id=share.id).delete()
        cache.delete(f'copilot:share:{share_code}')
        return None

    # Verificar permissão
    can_access = False
    if share.is_public:
        can_access = True
    elif requesting_user_email:
        # Verificar se email está na lista
        if requesting_user_email in share.shared_with_emails:
            can_access = True
        # Ou se é o próprio criador
        if share.created_by.email == requesting_user_email:
            can_access = True

    if not can_access:
        return None

    # Incrementar contador de acessos
    share.access_count += 1
    share.save(update_fields=['access_count'])

    return {
        'session_id': share.session_id,
        'created_by_email': share.created_by.email,
        'created_at': share.created_at.isoformat(),
        'is_public': share.is_public,
        'access_count': share.access_count,
    }


def delete_share(share_code: str, user_id: int) -> bool:
    """
    Exclui um compartilhamento (apenas o criador pode excluir).
    """
    from apps.copilot.models import CopilotSessionShare

    try:
        share = CopilotSessionShare.objects.get(share_code=share_code)
    except CopilotSessionShare.DoesNotExist:
        return False

    # Verificar se é o criador
    if share.created_by.id != user_id:
        return False

    share.delete()
    cache.delete(f'copilot:share:{share_code}')
    logger.info(f'[copilot] Compartilhamento {share_code} excluído')
    return True


def list_user_shares(user_id: int) -> List[dict]:
    """
    Lista todos os compartilhamentos de um usuário.
    """
    from apps.copilot.models import CopilotSessionShare

    shares = CopilotSessionShare.objects.filter(created_by_id=user_id).order_by('-created_at')

    return [{
        'share_code': share.share_code,
        'session_id': share.session_id,
        'is_public': share.is_public,
        'expires_at': share.expires_at.isoformat() if share.expires_at else None,
        'access_count': share.access_count,
        'created_at': share.created_at.isoformat(),
        'shared_with_count': len(share.shared_with_emails),
    } for share in shares]


def revoke_share(share_code: str, email_to_revoke: str, user_id: int) -> bool:
    """
    Revoga acesso de um email específico.
    """
    from apps.copilot.models import CopilotSessionShare

    try:
        share = CopilotSessionShare.objects.get(share_code=share_code)
    except CopilotSessionShare.DoesNotExist:
        return False

    # Verificar se é o criador
    if share.created_by.id != user_id:
        return False

    # Remover email da lista
    if email_to_revoke in share.shared_with_emails:
        share.shared_with_emails.remove(email_to_revoke)
        share.save(update_fields=['shared_with_emails'])

        # Atualizar cache
        cache.delete(f'copilot:share:{share_code}')
        logger.info(f'[copilot] Email {email_to_revoke} revogado do compartilhamento {share_code}')

    return True
