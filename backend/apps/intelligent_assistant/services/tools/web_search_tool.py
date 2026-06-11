"""
Web Search Tool - busca Google via Serper.dev para agentes jurídicos.
"""
import logging
import os
import requests

logger = logging.getLogger(__name__)

SERPER_API_URL = "https://google.serper.dev/search"


class WebSearchTool:
    """Busca web via Serper.dev para uso como Agent Tool jurídico."""

    @staticmethod
    def execute(query, config=None):
        """
        Executa busca web via Serper e retorna resultados formatados em markdown.

        Args:
            query: Query de busca
            config: {"max_results": 10}

        Returns:
            str: Resultados formatados em markdown ou '' se sem resultados
        """
        config = config or {}
        max_results = config.get('max_results', 10)

        try:
            results = WebSearchTool._search_serper(query, max_results)

            if not results:
                logger.info(f"[WebSearchTool] 0 resultados para '{query[:50]}'")
                return ''

            logger.info(f"[WebSearchTool] {len(results)} resultados para '{query[:50]}'")
            return WebSearchTool._format_results(results)

        except Exception as e:
            logger.warning(f"[WebSearchTool] Erro: {e}")
            return ''

    @staticmethod
    def _search_serper(query, max_results=10):
        """Busca via Serper.dev API."""
        api_key = os.environ.get('SERPER_API_KEY', '')
        if not api_key:
            logger.warning("[WebSearchTool] SERPER_API_KEY não configurada")
            return []

        try:
            resp = requests.post(
                SERPER_API_URL,
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": query, "num": max_results, "hl": "pt", "gl": "br"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            organic = data.get('organic', [])
            return [
                {
                    'orgao': r.get('source', r.get('displayLink', '')),
                    'descricao': r.get('snippet', ''),
                    'link': r.get('link', ''),
                    'titulo': r.get('title', ''),
                }
                for r in organic[:max_results]
            ]
        except Exception as e:
            logger.warning(f"[WebSearchTool] Serper error: {e}")
            return []

    @staticmethod
    def _format_results(results):
        """Formata resultados em tabela markdown."""
        if not results:
            return ''

        lines = ["### Resultados Web (Google)\n"]
        lines.append("| Fonte | Descrição | Link |")
        lines.append("|-------|-----------|------|")

        for r in results[:10]:
            desc = r.get('descricao', '')[:80]
            orgao = r.get('orgao', '')[:30]
            link = r.get('link', '')
            lines.append(f"| {orgao} | {desc} | [ver]({link}) |")

        return "\n".join(lines)
