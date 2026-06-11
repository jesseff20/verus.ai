"""
ContextBuilder — Monta o contexto de KB e trunca histórico para o Copilot.
"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Estimativa conservadora: 4 chars ≈ 1 token
CHARS_PER_TOKEN = 4
MAX_HISTORY_TOKENS = 80_000


def build_kb_context(query: str, n: int = 0) -> str:
    if n == 0:
        try:
            from .chat_service import get_max_kb_results
            n = get_max_kb_results()
        except Exception:
            logger.warning("Failed to get max_kb_results, using default 10", exc_info=True)
            n = 10
    """
    Busca nas KBs globais do sistema e retorna contexto formatado.
    Usa include_global_kb=True, include_blueprint_kb=False, include_agent_kb=False.
    """
    try:
        from apps.intelligent_assistant.services.knowledge_base_service import KnowledgeBaseService

        service = KnowledgeBaseService()
        results = service.query(
            collection_name='copilot',
            query_text=query,
            n_results=n,
            include_global_kb=True,
            include_blueprint_kb=False,
            include_agent_kb=False,
            include_session_docs=False,
        )

        documents: list = results.get('documents', [])
        if not documents:
            return ''

        context_parts = ['## BASE DE CONHECIMENTO\n']
        for i, doc in enumerate(documents, 1):
            content = doc.get('content', '') if isinstance(doc, dict) else str(doc)
            if content.strip():
                context_parts.append(f'### Referência {i}\n{content.strip()}\n')

        return '\n'.join(context_parts)

    except Exception as e:
        logger.warning(f'[copilot] Falha ao buscar KB: {e}')
        return ''


def truncate_history_for_context(messages: List[Dict], max_tokens: int = MAX_HISTORY_TOKENS) -> List[Dict]:
    """
    Retorna as mensagens mais recentes que cabem no limite de tokens estimado.
    Garante que sempre inclui ao menos a última mensagem do usuário.
    """
    if not messages:
        return []

    max_chars = max_tokens * CHARS_PER_TOKEN
    total_chars = 0
    kept: List[Dict] = []

    for msg in reversed(messages):
        content_len = len(msg.get('content', ''))
        if total_chars + content_len > max_chars and kept:
            break
        kept.append(msg)
        total_chars += content_len

    kept.reverse()
    return kept
