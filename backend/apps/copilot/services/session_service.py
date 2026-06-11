"""
SessionService — Gerencia histórico de conversas do Copilot no Redis.

Chave: copilot:session:{user_id}:{session_id}
TTL renovado a cada mensagem (SESSION_TTL segundos).
"""
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from django.core.cache import cache

logger = logging.getLogger(__name__)

SESSION_TTL = 7200  # 2 horas
SESSION_KEY_PREFIX = 'copilot:session'
MAX_MESSAGES = 200  # Limite de mensagens por sessão para evitar payloads gigantes


def _session_key(user_id: int, session_id: str) -> str:
    return f'{SESSION_KEY_PREFIX}:{user_id}:{session_id}'


def create_session(user_id: int) -> str:
    """
    Cria uma nova sessão para o usuário e armazena no Redis.
    Retorna o session_id (UUID).
    """
    session_id = str(uuid.uuid4())
    key = _session_key(user_id, session_id)
    payload = {
        'created_at': datetime.now(timezone.utc).isoformat(),
        'user_id': user_id,
        'messages': [],
    }
    cache.set(key, json.dumps(payload), timeout=SESSION_TTL)
    _add_to_session_index(user_id, session_id)
    logger.info(f'[copilot] Sessão criada: {session_id} (user={user_id})')
    return session_id


def get_history(user_id: int, session_id: str) -> Optional[List[dict]]:
    """
    Retorna a lista de mensagens da sessão ou None se não existir/expirou.
    """
    key = _session_key(user_id, session_id)
    raw = cache.get(key)
    if raw is None:
        return None
    try:
        payload = json.loads(raw)
        return payload.get('messages', [])
    except (json.JSONDecodeError, TypeError):
        logger.warning(f'[copilot] Falha ao desserializar sessão {session_id}')
        return None


def append_message(user_id: int, session_id: str, role: str, content: str, has_attachment: bool = False) -> bool:
    """
    Adiciona uma mensagem ao histórico da sessão e renova o TTL.
    Retorna False se a sessão não existir.
    """
    key = _session_key(user_id, session_id)
    raw = cache.get(key)
    if raw is None:
        logger.warning(f'[copilot] Sessão {session_id} não encontrada ao tentar append')
        return False

    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return False

    message: dict = {
        'role': role,
        'content': content,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
    if role == 'user':
        message['has_attachment'] = has_attachment

    messages: list = payload.get('messages', [])
    messages.append(message)

    # Manter apenas as últimas MAX_MESSAGES mensagens
    if len(messages) > MAX_MESSAGES:
        messages = messages[-MAX_MESSAGES:]

    payload['messages'] = messages
    cache.set(key, json.dumps(payload), timeout=SESSION_TTL)
    return True


def set_history(user_id: int, session_id: str, messages: List[dict]) -> bool:
    """
    Sobrescreve o histórico completo da sessão com a lista fornecida.
    Usado para sincronizar após edição de mensagem.
    Retorna False se a sessão não existir.
    """
    key = _session_key(user_id, session_id)
    raw = cache.get(key)
    if raw is None:
        return False

    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return False

    # Garantir estrutura mínima de cada mensagem
    clean_messages = [
        {
            'role': m.get('role', 'user'),
            'content': m.get('content', ''),
            'timestamp': m.get('timestamp', datetime.now(timezone.utc).isoformat()),
        }
        for m in messages
        if m.get('role') in ('user', 'assistant') and m.get('content')
    ]

    payload['messages'] = clean_messages[-MAX_MESSAGES:]
    cache.set(key, json.dumps(payload), timeout=SESSION_TTL)
    logger.info(f'[copilot] Histórico sincronizado: {session_id} ({len(clean_messages)} msgs, user={user_id})')
    return True


def clear_session(user_id: int, session_id: str) -> bool:
    """
    Limpa o histórico de mensagens da sessão (mantém a sessão ativa).
    Retorna False se a sessão não existir.
    """
    key = _session_key(user_id, session_id)
    raw = cache.get(key)
    if raw is None:
        return False

    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return False

    payload['messages'] = []
    cache.set(key, json.dumps(payload), timeout=SESSION_TTL)
    logger.info(f'[copilot] Histórico limpo: {session_id} (user={user_id})')
    return True


def _get_session_index_key(user_id: int) -> str:
    """Chave do índice de sessões do usuário."""
    return f'{SESSION_KEY_PREFIX}:index:{user_id}'


def _add_to_session_index(user_id: int, session_id: str) -> None:
    """Adiciona session_id ao índice do usuário no cache."""
    index_key = _get_session_index_key(user_id)
    raw = cache.get(index_key)
    session_ids = json.loads(raw) if raw else []
    if session_id not in session_ids:
        session_ids.append(session_id)
    cache.set(index_key, json.dumps(session_ids), timeout=SESSION_TTL * 10)


def _remove_from_session_index(user_id: int, session_id: str) -> None:
    """Remove session_id do índice do usuário."""
    index_key = _get_session_index_key(user_id)
    raw = cache.get(index_key)
    if not raw:
        return
    session_ids = json.loads(raw)
    if session_id in session_ids:
        session_ids.remove(session_id)
        cache.set(index_key, json.dumps(session_ids), timeout=SESSION_TTL * 10)


def list_sessions(user_id: int, limit: int = 20, search_query: str = '') -> List[dict]:
    """
    Lista todas as sessões do usuário, ordenadas por última atividade.
    Retorna lista limitada com id, created_at e last_message_at.
    Se search_query for fornecido, filtra sessões que contêm o termo.

    Usa um índice auxiliar em vez de cache.keys() para compatibilidade
    com todos os backends de cache do Django (LocMemCache, RedisCache).
    """
    index_key = _get_session_index_key(user_id)
    raw_index = cache.get(index_key)
    session_ids = json.loads(raw_index) if raw_index else []

    sessions = []
    expired_ids = []
    for session_id in session_ids:
        key = _session_key(user_id, session_id)
        raw = cache.get(key)
        if raw is None:
            expired_ids.append(session_id)
            continue
        try:
            payload = json.loads(raw)
            messages = payload.get('messages', [])

            # Filtrar por search_query se fornecido
            if search_query:
                query_lower = search_query.lower()
                # Buscar em todas as mensagens
                found = any(
                    query_lower in msg.get('content', '').lower()
                    for msg in messages
                )
                if not found:
                    continue

            # Extrair timestamp da última mensagem
            last_message_at = None
            if messages:
                last_msg = messages[-1]
                last_message_at = last_msg.get('timestamp')

            sessions.append({
                'id': session_id,
                'created_at': payload.get('created_at'),
                'last_message_at': last_message_at,
                'message_count': len(messages),
                # Extrair preview da última mensagem
                'preview': messages[-1].get('content', '')[:100] if messages else '',
            })
        except (json.JSONDecodeError, TypeError):
            continue

    # Limpar sessões expiradas do índice
    if expired_ids:
        for sid in expired_ids:
            if sid in session_ids:
                session_ids.remove(sid)
        cache.set(index_key, json.dumps(session_ids), timeout=SESSION_TTL * 10)

    # Ordenar por última mensagem (mais recente primeiro)
    sessions.sort(key=lambda s: s['last_message_at'] or s['created_at'], reverse=True)
    return sessions[:limit]


def delete_session(user_id: int, session_id: str) -> bool:
    """
    Exclui permanentemente uma sessão.
    Retorna False se a sessão não existir.
    """
    key = _session_key(user_id, session_id)
    raw = cache.get(key)
    if raw is None:
        return False

    cache.delete(key)
    _remove_from_session_index(user_id, session_id)
    logger.info(f'[copilot] Sessão excluída: {session_id} (user={user_id})')
    return True
