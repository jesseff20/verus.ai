"""
PNCP Search Tool - desativado no Verus.AI.

O PNCP (Portal Nacional de Contratações Públicas) era usado no projeto anterior para
pesquisa de preços em licitações. No Verus.AI, este tool não é relevante.
Mantido como stub para compatibilidade com seeds existentes.
"""
import logging

logger = logging.getLogger(__name__)


class PNCPSearchTool:
    """Stub desativado — PNCP é específico de licitações, não aplicável ao Verus.AI."""

    @staticmethod
    def execute(query, config=None):
        logger.info("[PNCPSearchTool] Tool desativado no Verus.AI.")
        return ''
