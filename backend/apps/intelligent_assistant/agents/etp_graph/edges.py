"""
ETP Edges - Funções de roteamento condicional para o grafo LangGraph.

Define as funções que determinam o próximo nó baseado no estado atual.
"""
import logging
from typing import Literal

from apps.intelligent_assistant.agents.etp_graph.state import (
    ETPState, SectionStatus, get_section_key
)

logger = logging.getLogger(__name__)


def should_regenerate_section(
    state: ETPState, section_num: int
) -> Literal["regenerate", "next", "error"]:
    """
    Determina se uma seção deve ser regenerada após validação.

    Args:
        state: Estado atual do grafo
        section_num: Número da seção

    Returns:
        "regenerate": Se deve tentar gerar novamente
        "next": Se deve ir para próxima seção
        "error": Se atingiu limite de tentativas
    """
    section_key = get_section_key(section_num)
    section_data = state.get(section_key, {})
    status = section_data.get("status")

    if status == SectionStatus.VALID:
        logger.info(f"Seção {section_num} válida, avançando...")
        return "next"

    if status == SectionStatus.REGENERATING:
        logger.info(f"Seção {section_num} precisa ser regenerada...")
        return "regenerate"

    if status in (SectionStatus.INVALID, SectionStatus.ERROR):
        logger.warning(f"Seção {section_num} com erro/inválida permanentemente, continuando para próxima seção...")
        return "next"  # Continua gerando as demais seções ao invés de parar

    # Default: avança
    return "next"


# === Funções de roteamento para cada seção ===

def route_after_validate_01(state: ETPState) -> Literal["regenerate", "next", "error"]:
    """Roteamento após validação da seção 01."""
    return should_regenerate_section(state, 1)


def route_after_validate_02(state: ETPState) -> Literal["regenerate", "next", "error"]:
    """Roteamento após validação da seção 02."""
    return should_regenerate_section(state, 2)


def route_after_validate_03(state: ETPState) -> Literal["regenerate", "next", "error"]:
    """Roteamento após validação da seção 03."""
    return should_regenerate_section(state, 3)


def route_after_validate_04(state: ETPState) -> Literal["regenerate", "next", "error"]:
    """Roteamento após validação da seção 04."""
    return should_regenerate_section(state, 4)


def route_after_validate_05(state: ETPState) -> Literal["regenerate", "next", "error"]:
    """Roteamento após validação da seção 05."""
    return should_regenerate_section(state, 5)


def route_after_validate_06(state: ETPState) -> Literal["regenerate", "next", "error"]:
    """Roteamento após validação da seção 06."""
    return should_regenerate_section(state, 6)


def route_after_validate_07(state: ETPState) -> Literal["regenerate", "next", "error"]:
    """Roteamento após validação da seção 07."""
    return should_regenerate_section(state, 7)


def route_after_validate_08(state: ETPState) -> Literal["regenerate", "next", "error"]:
    """Roteamento após validação da seção 08."""
    return should_regenerate_section(state, 8)


def route_after_validate_09(state: ETPState) -> Literal["regenerate", "next", "error"]:
    """Roteamento após validação da seção 09."""
    return should_regenerate_section(state, 9)


def route_after_validate_10(state: ETPState) -> Literal["regenerate", "next", "error"]:
    """Roteamento após validação da seção 10."""
    return should_regenerate_section(state, 10)


def route_after_validate_11(state: ETPState) -> Literal["regenerate", "next", "error"]:
    """Roteamento após validação da seção 11."""
    return should_regenerate_section(state, 11)


def route_after_validate_12(state: ETPState) -> Literal["regenerate", "next", "error"]:
    """Roteamento após validação da seção 12."""
    return should_regenerate_section(state, 12)


def route_after_validate_13(state: ETPState) -> Literal["regenerate", "next", "error"]:
    """Roteamento após validação da seção 13."""
    return should_regenerate_section(state, 13)


def route_after_validate_14(state: ETPState) -> Literal["regenerate", "next", "error"]:
    """Roteamento após validação da seção 14."""
    return should_regenerate_section(state, 14)


def route_after_validate_15(state: ETPState) -> Literal["regenerate", "next", "error"]:
    """Roteamento após validação da seção 15."""
    return should_regenerate_section(state, 15)


# Mapeamento de funções de roteamento
ROUTE_FUNCTIONS = {
    1: route_after_validate_01,
    2: route_after_validate_02,
    3: route_after_validate_03,
    4: route_after_validate_04,
    5: route_after_validate_05,
    6: route_after_validate_06,
    7: route_after_validate_07,
    8: route_after_validate_08,
    9: route_after_validate_09,
    10: route_after_validate_10,
    11: route_after_validate_11,
    12: route_after_validate_12,
    13: route_after_validate_13,
    14: route_after_validate_14,
    15: route_after_validate_15,
}


def get_route_function(section_num: int):
    """Retorna a função de roteamento para uma seção."""
    return ROUTE_FUNCTIONS.get(section_num)
