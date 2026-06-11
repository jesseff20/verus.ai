"""
ETP Graph - Construção e compilação do grafo LangGraph.

Este módulo constrói o StateGraph completo para geração de ETP
com 15 seções conforme Lei 14.133/2021.

Fluxo do Grafo:
    START
      │
      ▼
    generate_01 → validate_01 ─┬─ regenerate → generate_01
      │                        │
      │◄───────────────────────┘
      ▼
    generate_02 → validate_02 ─┬─ regenerate → generate_02
      │                        │
      │◄───────────────────────┘
      ▼
    ... (seções 03-14 seguem o mesmo padrão)
      │
      ▼
    generate_15 → validate_15 ─┬─ regenerate → generate_15
      │                        │
      │◄───────────────────────┘
      ▼
    finalize
      │
      ▼
     END
"""
import logging
from typing import Optional, List

from langgraph.graph import StateGraph, END

from apps.intelligent_assistant.agents.etp_graph.state import (
    ETPState, create_initial_state
)
from apps.intelligent_assistant.agents.etp_graph.nodes import (
    ETPNodes, create_nodes
)
from apps.intelligent_assistant.agents.etp_graph.edges import (
    route_after_validate_01, route_after_validate_02, route_after_validate_03,
    route_after_validate_04, route_after_validate_05, route_after_validate_06,
    route_after_validate_07, route_after_validate_08, route_after_validate_09,
    route_after_validate_10, route_after_validate_11, route_after_validate_12,
    route_after_validate_13, route_after_validate_14, route_after_validate_15,
)

logger = logging.getLogger(__name__)


def create_etp_graph(claude_service, kb_service) -> StateGraph:
    """
    Cria o grafo de geração de ETP.

    Args:
        claude_service: Serviço de comunicação com Claude API
        kb_service: Serviço de Knowledge Base (ChromaDB)

    Returns:
        StateGraph configurado (não compilado)
    """
    logger.info("Criando grafo ETP com 15 seções")

    # Cria instância dos nós
    nodes = create_nodes(claude_service, kb_service)

    # Cria o grafo
    graph = StateGraph(ETPState)

    # === Adiciona nós de geração ===
    graph.add_node("generate_01", nodes.generate_section_01)
    graph.add_node("generate_02", nodes.generate_section_02)
    graph.add_node("generate_03", nodes.generate_section_03)
    graph.add_node("generate_04", nodes.generate_section_04)
    graph.add_node("generate_05", nodes.generate_section_05)
    graph.add_node("generate_06", nodes.generate_section_06)
    graph.add_node("generate_07", nodes.generate_section_07)
    graph.add_node("generate_08", nodes.generate_section_08)
    graph.add_node("generate_09", nodes.generate_section_09)
    graph.add_node("generate_10", nodes.generate_section_10)
    graph.add_node("generate_11", nodes.generate_section_11)
    graph.add_node("generate_12", nodes.generate_section_12)
    graph.add_node("generate_13", nodes.generate_section_13)
    graph.add_node("generate_14", nodes.generate_section_14)
    graph.add_node("generate_15", nodes.generate_section_15)

    # === Adiciona nós de validação ===
    graph.add_node("validate_01", nodes.validate_section_01)
    graph.add_node("validate_02", nodes.validate_section_02)
    graph.add_node("validate_03", nodes.validate_section_03)
    graph.add_node("validate_04", nodes.validate_section_04)
    graph.add_node("validate_05", nodes.validate_section_05)
    graph.add_node("validate_06", nodes.validate_section_06)
    graph.add_node("validate_07", nodes.validate_section_07)
    graph.add_node("validate_08", nodes.validate_section_08)
    graph.add_node("validate_09", nodes.validate_section_09)
    graph.add_node("validate_10", nodes.validate_section_10)
    graph.add_node("validate_11", nodes.validate_section_11)
    graph.add_node("validate_12", nodes.validate_section_12)
    graph.add_node("validate_13", nodes.validate_section_13)
    graph.add_node("validate_14", nodes.validate_section_14)
    graph.add_node("validate_15", nodes.validate_section_15)

    # === Adiciona nós auxiliares ===
    graph.add_node("finalize", nodes.finalize_document)
    graph.add_node("handle_error", nodes.handle_error)

    # === Define ponto de entrada ===
    graph.set_entry_point("generate_01")

    # === Define arestas (edges) ===

    # Seção 01: Geração → Validação → Roteamento
    graph.add_edge("generate_01", "validate_01")
    graph.add_conditional_edges(
        "validate_01",
        route_after_validate_01,
        {
            "regenerate": "generate_01",
            "next": "generate_02",
            "error": "handle_error",
        }
    )

    # Seção 02
    graph.add_edge("generate_02", "validate_02")
    graph.add_conditional_edges(
        "validate_02",
        route_after_validate_02,
        {
            "regenerate": "generate_02",
            "next": "generate_03",
            "error": "handle_error",
        }
    )

    # Seção 03
    graph.add_edge("generate_03", "validate_03")
    graph.add_conditional_edges(
        "validate_03",
        route_after_validate_03,
        {
            "regenerate": "generate_03",
            "next": "generate_04",
            "error": "handle_error",
        }
    )

    # Seção 04
    graph.add_edge("generate_04", "validate_04")
    graph.add_conditional_edges(
        "validate_04",
        route_after_validate_04,
        {
            "regenerate": "generate_04",
            "next": "generate_05",
            "error": "handle_error",
        }
    )

    # Seção 05
    graph.add_edge("generate_05", "validate_05")
    graph.add_conditional_edges(
        "validate_05",
        route_after_validate_05,
        {
            "regenerate": "generate_05",
            "next": "generate_06",
            "error": "handle_error",
        }
    )

    # Seção 06
    graph.add_edge("generate_06", "validate_06")
    graph.add_conditional_edges(
        "validate_06",
        route_after_validate_06,
        {
            "regenerate": "generate_06",
            "next": "generate_07",
            "error": "handle_error",
        }
    )

    # Seção 07
    graph.add_edge("generate_07", "validate_07")
    graph.add_conditional_edges(
        "validate_07",
        route_after_validate_07,
        {
            "regenerate": "generate_07",
            "next": "generate_08",
            "error": "handle_error",
        }
    )

    # Seção 08
    graph.add_edge("generate_08", "validate_08")
    graph.add_conditional_edges(
        "validate_08",
        route_after_validate_08,
        {
            "regenerate": "generate_08",
            "next": "generate_09",
            "error": "handle_error",
        }
    )

    # Seção 09
    graph.add_edge("generate_09", "validate_09")
    graph.add_conditional_edges(
        "validate_09",
        route_after_validate_09,
        {
            "regenerate": "generate_09",
            "next": "generate_10",
            "error": "handle_error",
        }
    )

    # Seção 10
    graph.add_edge("generate_10", "validate_10")
    graph.add_conditional_edges(
        "validate_10",
        route_after_validate_10,
        {
            "regenerate": "generate_10",
            "next": "generate_11",
            "error": "handle_error",
        }
    )

    # Seção 11
    graph.add_edge("generate_11", "validate_11")
    graph.add_conditional_edges(
        "validate_11",
        route_after_validate_11,
        {
            "regenerate": "generate_11",
            "next": "generate_12",
            "error": "handle_error",
        }
    )

    # Seção 12
    graph.add_edge("generate_12", "validate_12")
    graph.add_conditional_edges(
        "validate_12",
        route_after_validate_12,
        {
            "regenerate": "generate_12",
            "next": "generate_13",
            "error": "handle_error",
        }
    )

    # Seção 13
    graph.add_edge("generate_13", "validate_13")
    graph.add_conditional_edges(
        "validate_13",
        route_after_validate_13,
        {
            "regenerate": "generate_13",
            "next": "generate_14",
            "error": "handle_error",
        }
    )

    # Seção 14
    graph.add_edge("generate_14", "validate_14")
    graph.add_conditional_edges(
        "validate_14",
        route_after_validate_14,
        {
            "regenerate": "generate_14",
            "next": "generate_15",
            "error": "handle_error",
        }
    )

    # Seção 15 (última) → Finalização
    graph.add_edge("generate_15", "validate_15")
    graph.add_conditional_edges(
        "validate_15",
        route_after_validate_15,
        {
            "regenerate": "generate_15",
            "next": "finalize",
            "error": "handle_error",
        }
    )

    # Finalização → END
    graph.add_edge("finalize", END)
    graph.add_edge("handle_error", END)

    logger.info("Grafo ETP criado com sucesso")
    return graph


def compile_etp_graph(claude_service, kb_service, checkpointer=None):
    """
    Compila o grafo ETP para execução.

    Args:
        claude_service: Serviço Claude API
        kb_service: Serviço Knowledge Base
        checkpointer: Opcional - checkpointer para persistência de estado

    Returns:
        CompiledGraph pronto para execução
    """
    graph = create_etp_graph(claude_service, kb_service)

    if checkpointer:
        compiled = graph.compile(checkpointer=checkpointer)
    else:
        compiled = graph.compile()

    logger.info("Grafo ETP compilado e pronto para execução")
    return compiled


class ETPGraphRunner:
    """
    Classe para execução do grafo ETP.

    Encapsula a lógica de criação, compilação e execução do grafo.
    """

    def __init__(self, claude_service, kb_service, checkpointer=None):
        """
        Inicializa o runner do grafo.

        Args:
            claude_service: Serviço Claude API
            kb_service: Serviço Knowledge Base
            checkpointer: Opcional - checkpointer para persistência
        """
        self.claude_service = claude_service
        self.kb_service = kb_service
        self.checkpointer = checkpointer
        self._compiled_graph = None

    @property
    def graph(self):
        """Retorna o grafo compilado (lazy loading)."""
        if self._compiled_graph is None:
            self._compiled_graph = compile_etp_graph(
                self.claude_service,
                self.kb_service,
                self.checkpointer
            )
        return self._compiled_graph

    def run(
        self,
        objective: str,
        collection_name: Optional[str] = None,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        max_retries: int = 2,
        config: Optional[dict] = None
    ) -> ETPState:
        """
        Executa o grafo de geração de ETP.

        Args:
            objective: Objetivo da contratação
            collection_name: ID da sessão para buscar embeddings no PgVector
            user_id: ID do usuário
            organization_id: ID da organização
            max_retries: Máximo de tentativas por seção (default: 2)
            config: Configuração adicional do LangGraph

        Returns:
            Estado final após execução completa
        """
        logger.info(f"Iniciando geração de ETP para: {objective[:100]}...")

        # Cria estado inicial
        initial_state = create_initial_state(
            objective=objective,
            collection_name=collection_name,
            user_id=user_id,
            organization_id=organization_id,
            max_retries=max_retries
        )

        # Calcula recursion_limit baseado na arquitetura do grafo
        # 15 seções × 2 nós (gen+val) × max_retries + margem de segurança
        calculated_limit = (15 * 2 * max_retries) + 10

        # Mescla config com recursion_limit calculado
        run_config = config or {}
        if "recursion_limit" not in run_config:
            run_config["recursion_limit"] = calculated_limit
            logger.info(f"Recursion limit definido para: {calculated_limit}")

        # Executa o grafo
        final_state = self.graph.invoke(initial_state, config=run_config)

        logger.info(
            f"Geração de ETP concluída. "
            f"Status: {final_state.get('status')}"
        )

        return final_state

    async def arun(
        self,
        objective: str,
        collection_name: Optional[str] = None,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        max_retries: int = 2,
        config: Optional[dict] = None
    ) -> ETPState:
        """
        Executa o grafo de forma assíncrona.

        Args:
            objective: Objetivo da contratação
            collection_name: ID da sessão para buscar embeddings no PgVector
            user_id: ID do usuário
            organization_id: ID da organização
            max_retries: Máximo de tentativas por seção (default: 2)
            config: Configuração adicional do LangGraph

        Returns:
            Estado final após execução completa
        """
        logger.info(f"Iniciando geração de ETP (async) para: {objective[:100]}...")

        # Cria estado inicial
        initial_state = create_initial_state(
            objective=objective,
            collection_name=collection_name,
            user_id=user_id,
            organization_id=organization_id,
            max_retries=max_retries
        )

        # Calcula recursion_limit baseado na arquitetura do grafo
        calculated_limit = (15 * 2 * max_retries) + 10
        run_config = config or {}
        if "recursion_limit" not in run_config:
            run_config["recursion_limit"] = calculated_limit

        # Executa o grafo assincronamente
        final_state = await self.graph.ainvoke(initial_state, config=run_config)

        logger.info(
            f"Geração de ETP (async) concluída. "
            f"Status: {final_state.get('status')}"
        )

        return final_state

    def stream(
        self,
        objective: str,
        collection_name: Optional[str] = None,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        max_retries: int = 2,
        sections: Optional[List[int]] = None,
        config: Optional[dict] = None
    ):
        """
        Executa o grafo com streaming de estados intermediários.

        Args:
            objective: Objetivo da contratação
            collection_name: ID da sessão para buscar embeddings no PgVector
            user_id: ID do usuário
            organization_id: ID da organização
            max_retries: Máximo de tentativas por seção (default: 2)
            sections: Lista de seções a gerar (1-15). Se None, gera todas.
            config: Configuração adicional do LangGraph

        Yields:
            Estados intermediários durante a execução
        """
        sections_to_generate = sections if sections else list(range(1, 16))
        logger.info(
            f"Iniciando geração de ETP (stream) para: {objective[:100]}... "
            f"Seções: {sections_to_generate}"
        )

        # Cria estado inicial
        initial_state = create_initial_state(
            objective=objective,
            collection_name=collection_name,
            user_id=user_id,
            organization_id=organization_id,
            max_retries=max_retries,
            sections_to_generate=sections_to_generate
        )

        # Calcula recursion_limit baseado em TODAS as 15 seções (mesmo pulando, cada pulo conta como iteração)
        # 15 seções × 2 nós (gen+val) × max_retries + margem
        num_sections = len(sections_to_generate)
        calculated_limit = (15 * 2 * max_retries) + 20  # Sempre considera 15 seções
        run_config = config or {}
        if "recursion_limit" not in run_config:
            run_config["recursion_limit"] = calculated_limit

        logger.info(f"Recursion limit calculado: {calculated_limit} (gerando {num_sections} seções)")

        # Executa com streaming
        for state in self.graph.stream(initial_state, config=run_config):
            yield state

        logger.info("Geração de ETP (stream) concluída")
