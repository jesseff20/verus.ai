"""
Agent Tools Service — executa tools vinculados a um agente antes da geração.

Busca AgentToolLink do agente, executa cada tool em ordem de prioridade,
e retorna contexto formatado para injetar no prompt do LLM.
"""
import logging
import importlib

logger = logging.getLogger(__name__)

# Registry de tools por tipo (fallback caso service_path não funcione)
TOOL_REGISTRY = {
    'web_search': 'apps.intelligent_assistant.services.tools.web_search_tool.WebSearchTool',
    'pncp_search': 'apps.intelligent_assistant.services.tools.pncp_search_tool.PNCPSearchTool',
}


class AgentToolsService:
    """Executa tools habilitados para um agente antes da chamada ao LLM."""

    @classmethod
    def execute_agent_tools(cls, agent_config, objective_summary, section_name):
        """
        Busca tools vinculados ao agente, executa em ordem de prioridade,
        e retorna contexto formatado para injetar no prompt.

        Args:
            agent_config: SectionAgentConfig com tool_links
            objective_summary: Resumo do objetivo (para montar query)
            section_name: Nome da seção sendo gerada

        Returns:
            str: Contexto formatado com resultados dos tools, ou '' se nenhum tool
        """
        if not agent_config:
            return ''

        try:
            tool_links = (
                agent_config.tool_links
                .filter(enabled=True)
                .select_related('tool')
                .order_by('priority')
            )
        except Exception as e:
            logger.warning(f"[AgentTools] Erro ao buscar tool_links do agente {agent_config.id}: {e}")
            return ''

        if not tool_links.exists():
            return ''

        queries = cls._build_queries(objective_summary, section_name)
        logger.info(
            f"[AgentTools] Executando {tool_links.count()} tool(s) para '{section_name}' | "
            f"google='{queries['google'][:50]}' | pncp='{queries['pncp'][:50]}'"
        )

        results_parts = []
        for link in tool_links:
            tool = link.tool
            if not tool.is_active:
                continue

            # Usar query específica por tipo de tool
            if tool.tool_type == 'pncp_search':
                query = queries['pncp']
            else:
                query = queries['google']

            config = {**tool.default_config, **link.custom_config}
            result = cls._execute_tool(tool, query, config)

            if result:
                results_parts.append(result)

        if not results_parts:
            logger.info(f"[AgentTools] Nenhum resultado retornado para '{section_name}'")
            return ''

        header = "## DADOS REAIS DE MERCADO (busca automática)\n\n"
        footer = "\n\n**Nota:** Dados obtidos automaticamente via busca web. Verificar vigência e aplicabilidade."

        return header + "\n\n".join(results_parts) + footer

    @classmethod
    def _build_queries(cls, objective_summary, section_name):
        """
        Usa IA para criar duas strings de busca a partir do objetivo:
        - google: para buscar soluções e referências na web
        - pncp: para buscar editais e contratos com preços no PNCP

        Returns:
            dict: {'google': 'query web', 'pncp': 'query pncp'}
        """
        fallback = section_name or 'contratação TI'

        if not objective_summary:
            return {'google': fallback, 'pncp': fallback}

        try:
            from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService
            llm = UnifiedLLMService()

            prompt = (
                "Analise o objetivo de contratação abaixo e crie DUAS strings de busca:\n\n"
                "1. GOOGLE: string para buscar soluções, fornecedores e referências na web "
                "(3 a 5 palavras-chave focadas no objeto)\n"
                "2. PNCP: string para buscar editais e contratos similares no Portal Nacional "
                "de Contratações Públicas (2 a 4 palavras genéricas do objeto, sem termos técnicos demais)\n\n"
                f"OBJETIVO:\n{objective_summary[:500]}\n\n"
                "Responda EXATAMENTE neste formato, sem explicação:\n"
                "GOOGLE: [palavras-chave]\n"
                "PNCP: [palavras-chave]"
            )

            result = llm.generate(
                user_prompt=prompt,
                system_prompt="Você cria strings de busca. Responda apenas no formato solicitado.",
                temperature=0.1,
                max_tokens=100,
                provider='watsonx',
                model='mistralai/mistral-medium-2505',
            )

            content = result.get('content', '').strip()
            queries = {'google': fallback, 'pncp': fallback}

            for line in content.split('\n'):
                line = line.strip()
                if line.upper().startswith('GOOGLE:'):
                    q = line.split(':', 1)[1].strip().replace('"', '').replace("'", '')
                    if q and len(q) < 100:
                        queries['google'] = q
                elif line.upper().startswith('PNCP:'):
                    q = line.split(':', 1)[1].strip().replace('"', '').replace("'", '')
                    if q and len(q) < 80:
                        queries['pncp'] = q

            logger.info(f"[AgentTools] Queries por IA — Google: '{queries['google']}' | PNCP: '{queries['pncp']}'")
            return queries

        except Exception as e:
            logger.warning(f"[AgentTools] Erro ao criar queries: {e}")
            return {'google': fallback, 'pncp': fallback}

    @classmethod
    def _execute_tool(cls, tool, query, config):
        """
        Executa um tool individual.

        Tenta carregar o service via service_path do tool.
        Fallback: usa TOOL_REGISTRY por tool_type.
        """
        try:
            # Usar registry de tools por tipo (cada tool sabe parsear config)
            registry_path = TOOL_REGISTRY.get(tool.tool_type)
            if registry_path:
                tool_cls = cls._import_class(registry_path)
                if tool_cls:
                    result = tool_cls.execute(query, config)
                    if result:
                        logger.info(f"[AgentTools] {tool.name}: resultado obtido")
                        return result

        except Exception as e:
            logger.warning(f"[AgentTools] Erro ao executar {tool.name}: {e}")

        return ''

    @staticmethod
    def _import_tool_class(service_path, method_name):
        """Importa e retorna callable do service.method."""
        try:
            parts = service_path.rsplit('.', 1)
            if len(parts) != 2:
                return None
            module_path, class_name = parts
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            return getattr(cls, method_name, None)
        except (ImportError, AttributeError) as e:
            logger.debug(f"[AgentTools] Import falhou para {service_path}: {e}")
            return None

    @staticmethod
    def _import_class(full_path):
        """Importa classe por path completo."""
        try:
            parts = full_path.rsplit('.', 1)
            module = importlib.import_module(parts[0])
            return getattr(module, parts[1])
        except (ImportError, AttributeError):
            return None
