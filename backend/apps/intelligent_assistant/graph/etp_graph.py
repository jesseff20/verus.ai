"""
Grafo LangGraph para geração completa de ETP.

Este módulo constrói o StateGraph que orquestra todo o fluxo de geração,
incluindo geração, validação e refinamento de cada seção.
"""
import logging
from langgraph.graph import StateGraph, END
from .state import ETPGenerationState

logger = logging.getLogger(__name__)
from .nodes import ETPNodes
from .edges import (
    should_refine_section_01,
    should_refine_section_02,
    should_refine_section_03,
    should_refine_section_04,
    should_refine_section_05,
    should_refine_section_06
)


def create_etp_graph(claude_service, kb_service):
    """
    Cria e compila o grafo LangGraph para geração de ETP.

    Fluxo do grafo (Seções 1-6):
    1. Gerar Seção 1 → Validar → [Refinar até 2x] → Prosseguir
    2. Gerar Seção 2 → Validar → [Refinar até 2x] → Prosseguir
    3. Gerar Seção 3 → Validar → [Refinar até 2x] → Prosseguir
    4. Gerar Seção 4 → Validar → [Refinar até 2x] → Prosseguir
    5. Gerar Seção 5 → Validar → [Refinar até 2x] → Prosseguir
    6. Gerar Seção 6 → Validar → [Refinar até 2x] → Finalizar

    Se esgotadas tentativas em qualquer seção → Revisão Manual

    Args:
        claude_service: Instância do ClaudeService
        kb_service: Instância do KnowledgeBaseService

    Returns:
        CompiledGraph pronto para execução
    """
    logger.debug("🔧 Construindo grafo LangGraph para geração de ETP (Seções 1-6)...")

    # Instanciar nós
    nodes = ETPNodes(claude_service, kb_service)

    # Criar grafo com o State
    graph = StateGraph(ETPGenerationState)

    # ========== ADICIONAR NÓS ==========

    # Seção 1 - Descrição da Necessidade
    graph.add_node("generate_section_01", nodes.generate_section_01)
    graph.add_node("validate_section_01", nodes.validate_section_01)
    graph.add_node("refine_section_01", nodes.refine_section_01)

    # Seção 2 - Estudos Técnicos Preliminares
    graph.add_node("generate_section_02", nodes.generate_section_02)
    graph.add_node("validate_section_02", nodes.validate_section_02)
    graph.add_node("refine_section_02", nodes.refine_section_02)

    # Seção 3 - Descrição da Solução
    graph.add_node("generate_section_03", nodes.generate_section_03)
    graph.add_node("validate_section_03", nodes.validate_section_03)
    graph.add_node("refine_section_03", nodes.refine_section_03)

    # Seção 4 - Estimativa de Preços
    graph.add_node("generate_section_04", nodes.generate_section_04)
    graph.add_node("validate_section_04", nodes.validate_section_04)
    graph.add_node("refine_section_04", nodes.refine_section_04)

    # Seção 5 - Metodologia de Seleção
    graph.add_node("generate_section_05", nodes.generate_section_05)
    graph.add_node("validate_section_05", nodes.validate_section_05)
    graph.add_node("refine_section_05", nodes.refine_section_05)

    # Seção 6 - Justificativa para Parcelamento
    graph.add_node("generate_section_06", nodes.generate_section_06)
    graph.add_node("validate_section_06", nodes.validate_section_06)
    graph.add_node("refine_section_06", nodes.refine_section_06)

    # Finalizadores
    graph.add_node("finalize_generation", nodes.finalize_generation)
    graph.add_node("mark_for_manual_review", nodes.mark_for_manual_review)

    # ========== DEFINIR FLUXO ==========

    # Ponto de entrada: começar gerando Seção 1
    graph.set_entry_point("generate_section_01")

    # ----- SEÇÃO 1 -----
    # Após gerar Seção 1 → validar
    graph.add_edge("generate_section_01", "validate_section_01")

    # Após validar Seção 1 → decisão condicional
    graph.add_conditional_edges(
        "validate_section_01",
        should_refine_section_01,
        {
            "proceed_to_section_02": "generate_section_02",
            "refine_section_01": "refine_section_01",
            "manual_review_required": "mark_for_manual_review"
        }
    )

    # Após refinar Seção 1 → voltar para validação
    graph.add_edge("refine_section_01", "validate_section_01")

    # ----- SEÇÃO 2 -----
    # Após gerar Seção 2 → validar
    graph.add_edge("generate_section_02", "validate_section_02")

    # Após validar Seção 2 → decisão condicional
    graph.add_conditional_edges(
        "validate_section_02",
        should_refine_section_02,
        {
            "proceed_to_section_03": "generate_section_03",
            "refine_section_02": "refine_section_02",
            "manual_review_required": "mark_for_manual_review"
        }
    )

    # Após refinar Seção 2 → voltar para validação
    graph.add_edge("refine_section_02", "validate_section_02")

    # ----- SEÇÃO 3 -----
    # Após gerar Seção 3 → validar
    graph.add_edge("generate_section_03", "validate_section_03")

    # Após validar Seção 3 → decisão condicional
    graph.add_conditional_edges(
        "validate_section_03",
        should_refine_section_03,
        {
            "proceed_to_section_04": "generate_section_04",
            "refine_section_03": "refine_section_03",
            "manual_review_required": "mark_for_manual_review"
        }
    )

    # Após refinar Seção 3 → voltar para validação
    graph.add_edge("refine_section_03", "validate_section_03")

    # ----- SEÇÃO 4 -----
    # Após gerar Seção 4 → validar
    graph.add_edge("generate_section_04", "validate_section_04")

    # Após validar Seção 4 → decisão condicional
    graph.add_conditional_edges(
        "validate_section_04",
        should_refine_section_04,
        {
            "proceed_to_section_05": "generate_section_05",
            "refine_section_04": "refine_section_04",
            "manual_review_required": "mark_for_manual_review"
        }
    )

    # Após refinar Seção 4 → voltar para validação
    graph.add_edge("refine_section_04", "validate_section_04")

    # ----- SEÇÃO 5 -----
    # Após gerar Seção 5 → validar
    graph.add_edge("generate_section_05", "validate_section_05")

    # Após validar Seção 5 → decisão condicional
    graph.add_conditional_edges(
        "validate_section_05",
        should_refine_section_05,
        {
            "proceed_to_section_06": "generate_section_06",
            "refine_section_05": "refine_section_05",
            "manual_review_required": "mark_for_manual_review"
        }
    )

    # Após refinar Seção 5 → voltar para validação
    graph.add_edge("refine_section_05", "validate_section_05")

    # ----- SEÇÃO 6 -----
    # Após gerar Seção 6 → validar
    graph.add_edge("generate_section_06", "validate_section_06")

    # Após validar Seção 6 → decisão condicional
    graph.add_conditional_edges(
        "validate_section_06",
        should_refine_section_06,
        {
            "finalize": "finalize_generation",
            "refine_section_06": "refine_section_06",
            "manual_review_required": "mark_for_manual_review"
        }
    )

    # Após refinar Seção 6 → voltar para validação
    graph.add_edge("refine_section_06", "validate_section_06")

    # Finalizadores → END
    graph.add_edge("finalize_generation", END)
    graph.add_edge("mark_for_manual_review", END)

    # ========== COMPILAR GRAFO ==========

    app = graph.compile()

    logger.debug("✅ Grafo LangGraph compilado com sucesso!")
    logger.debug(f"   - Seção 1: generate_section_01, validate_section_01, refine_section_01")
    logger.debug(f"   - Seção 2: generate_section_02, validate_section_02, refine_section_02")
    logger.debug(f"   - Seção 3: generate_section_03, validate_section_03, refine_section_03")
    logger.debug(f"   - Seção 4: generate_section_04, validate_section_04, refine_section_04")
    logger.debug(f"   - Seção 5: generate_section_05, validate_section_05, refine_section_05")
    logger.debug(f"   - Seção 6: generate_section_06, validate_section_06, refine_section_06")
    logger.debug(f"   - Finalizadores: finalize_generation, mark_for_manual_review")

    return app


def visualize_graph(graph_app):
    """
    Gera visualização do grafo (requer pygraphviz).

    Args:
        graph_app: Grafo compilado

    Returns:
        PNG bytes ou None se não conseguir gerar
    """
    try:
        from langgraph.graph import Graph
        # Tenta gerar imagem do grafo
        return graph_app.get_graph().draw_png()
    except ImportError:
        logger.debug("⚠️  pygraphviz não instalado - não é possível gerar visualização")
        return None
    except Exception as e:
        logger.debug(f"⚠️  Erro ao gerar visualização: {str(e)}")
        return None
