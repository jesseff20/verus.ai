"""
user_kb_context - Query user's personal knowledge base for Copilot context.

Uses keyword-based text search (no embedding needed for MVP).
Called during chat to inject relevant user data into the LLM prompt.
"""
import logging

from django.db.models import Q

logger = logging.getLogger(__name__)


def get_user_context(user, user_message: str) -> str:
    """
    Get relevant entries from user's personal knowledge base.

    Performs keyword search on UserKnowledgeEntry content/title
    and returns formatted context for the LLM prompt.

    Args:
        user: The authenticated user
        user_message: The user's chat message (used for keyword extraction)

    Returns:
        Formatted context string, or empty string if no entries found.
    """
    from apps.copilot.models import UserKnowledgeEntry

    entries = UserKnowledgeEntry.objects.filter(user=user)

    if not entries.exists():
        return ''

    # Search by keywords in message
    words = [w for w in user_message.lower().split() if len(w) > 3]
    if words:
        q = Q()
        for word in words[:5]:  # Max 5 keywords
            q |= Q(content__icontains=word) | Q(title__icontains=word)
        filtered = entries.filter(q)
        # Fall back to all entries if keyword search returns nothing
        if filtered.exists():
            entries = filtered

    # Get most recent and relevant entries
    entries = entries.order_by('-context_date')[:10]

    if not entries:
        return ''

    context_parts = ['## Contexto do Usuário (Base de Conhecimento Pessoal)\n']
    for entry in entries:
        context_parts.append(f'### {entry.get_category_display()}: {entry.title}')
        context_parts.append(entry.content[:500])  # Truncate long content
        context_parts.append('')

    return '\n'.join(context_parts)
