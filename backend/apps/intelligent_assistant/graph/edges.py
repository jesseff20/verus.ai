"""
Edges condicionais do grafo LangGraph.

Edges decidem qual será o próximo nó baseado no estado atual.
"""
import logging
from .state import ETPGenerationState

logger = logging.getLogger(__name__)

# ========== CONSTANTES ==========

MAX_REFINE_ATTEMPTS = 2
"""Número máximo de tentativas de refinamento por seção"""

MIN_SCORE_TO_PROCEED = 60
"""Score mínimo para prosseguir para próxima seção"""

MIN_SCORE_WITHOUT_WARNINGS = 80
"""Score mínimo para prosseguir sem avisos"""


# ========== EDGES PARA SEÇÃO 1 ==========

def should_refine_section_01(state: ETPGenerationState) -> str:
    """
    Edge condicional: decidir próxima ação após validação da Seção 1.

    Lógica de decisão:
    1. Se score >= 80 e válido → prosseguir para Seção 2
    2. Se score >= 60 e válido → prosseguir com avisos
    3. Se inválido e tentativas < 2 → refinar
    4. Se tentativas >= 2 → revisão manual

    Args:
        state: Estado atual do grafo

    Returns:
        Nome do próximo nó a ser executado
    """
    validation = state.get('section_01_validation', {})
    is_valid = validation.get('is_valid', False)
    score = validation.get('score', 0)
    refine_attempts = state.get('section_01_refine_attempts', 0)

    logger.debug(f"Decidindo próximo passo para Seção 1...")
    logger.debug(f"- Válido: {is_valid}")
    logger.debug(f"- Score: {score}")
    logger.debug(f"- Tentativas de refinamento: {refine_attempts}")

    # Caso 1: Seção excelente (score >= 80)
    if is_valid and score >= MIN_SCORE_WITHOUT_WARNINGS:
        logger.debug(f"→ Prosseguir para Seção 2 (score excelente)")
        return "proceed_to_section_02"

    # Caso 2: Seção aceitável (score >= 60)
    elif is_valid and score >= MIN_SCORE_TO_PROCEED:
        logger.debug(f"→ Prosseguir para Seção 2 (com avisos)")
        return "proceed_to_section_02"

    # Caso 3: Seção inválida, mas ainda pode refinar
    elif not is_valid and refine_attempts < MAX_REFINE_ATTEMPTS:
        logger.debug(f"→ Refinar Seção 1 (tentativa {refine_attempts + 1}/{MAX_REFINE_ATTEMPTS})")
        return "refine_section_01"

    # Caso 4: Seção inválida e já tentou refinar 2x
    else:
        logger.debug(f"→ Requer revisão manual (esgotadas tentativas de refinamento)")
        return "manual_review_required"


# ========== EDGES PARA SEÇÃO 2 ==========

def should_refine_section_02(state: ETPGenerationState) -> str:
    """
    Edge condicional: decidir próxima ação após validação da Seção 2.

    Mesma lógica da Seção 1, mas para Seção 2.
    """
    validation = state.get('section_02_validation', {})
    is_valid = validation.get('is_valid', False)
    score = validation.get('score', 0)
    refine_attempts = state.get('section_02_refine_attempts', 0)

    logger.debug(f"Decidindo próximo passo para Seção 2...")
    logger.debug(f"- Válido: {is_valid}")
    logger.debug(f"- Score: {score}")
    logger.debug(f"- Tentativas de refinamento: {refine_attempts}")

    # Caso 1: Seção excelente
    if is_valid and score >= MIN_SCORE_WITHOUT_WARNINGS:
        logger.debug(f"→ Prosseguir para Seção 3 (score excelente)")
        return "proceed_to_section_03"

    # Caso 2: Seção aceitável
    elif is_valid and score >= MIN_SCORE_TO_PROCEED:
        logger.debug(f"→ Prosseguir para Seção 3 (com avisos)")
        return "proceed_to_section_03"

    # Caso 3: Seção inválida, mas ainda pode refinar
    elif not is_valid and refine_attempts < MAX_REFINE_ATTEMPTS:
        logger.debug(f"→ Refinar Seção 2 (tentativa {refine_attempts + 1}/{MAX_REFINE_ATTEMPTS})")
        return "refine_section_02"

    # Caso 4: Seção inválida e já tentou refinar 2x
    else:
        logger.debug(f"→ Requer revisão manual")
        return "manual_review_required"


# ========== EDGES PARA SEÇÃO 3 ==========

def should_refine_section_03(state: ETPGenerationState) -> str:
    """
    Edge condicional: decidir próxima ação após validação da Seção 3.

    Mesma lógica das seções anteriores, mas para Seção 3.
    """
    validation = state.get('section_03_validation', {})
    is_valid = validation.get('is_valid', False)
    score = validation.get('score', 0)
    refine_attempts = state.get('section_03_refine_attempts', 0)

    logger.debug(f"Decidindo próximo passo para Seção 3...")
    logger.debug(f"- Válido: {is_valid}")
    logger.debug(f"- Score: {score}")
    logger.debug(f"- Tentativas de refinamento: {refine_attempts}")

    # Caso 1: Seção excelente
    if is_valid and score >= MIN_SCORE_WITHOUT_WARNINGS:
        logger.debug(f"→ Prosseguir para Seção 4 (score excelente)")
        return "proceed_to_section_04"

    # Caso 2: Seção aceitável
    elif is_valid and score >= MIN_SCORE_TO_PROCEED:
        logger.debug(f"→ Prosseguir para Seção 4 (com avisos)")
        return "proceed_to_section_04"

    # Caso 3: Seção inválida, mas ainda pode refinar
    elif not is_valid and refine_attempts < MAX_REFINE_ATTEMPTS:
        logger.debug(f"→ Refinar Seção 3 (tentativa {refine_attempts + 1}/{MAX_REFINE_ATTEMPTS})")
        return "refine_section_03"

    # Caso 4: Seção inválida e já tentou refinar 2x
    else:
        logger.debug(f"→ Requer revisão manual")
        return "manual_review_required"


# ========== EDGES PARA SEÇÃO 4 ==========

def should_refine_section_04(state: ETPGenerationState) -> str:
    """
    Edge condicional: decidir próxima ação após validação da Seção 4.

    Mesma lógica das seções anteriores, mas para Seção 4.
    Após Seção 4, prossegue para Seção 5.
    """
    validation = state.get('section_04_validation', {})
    is_valid = validation.get('is_valid', False)
    score = validation.get('score', 0)
    refine_attempts = state.get('section_04_refine_attempts', 0)

    logger.debug(f"Decidindo próximo passo para Seção 4...")
    logger.debug(f"- Válido: {is_valid}")
    logger.debug(f"- Score: {score}")
    logger.debug(f"- Tentativas de refinamento: {refine_attempts}")

    # Caso 1: Seção excelente
    if is_valid and score >= MIN_SCORE_WITHOUT_WARNINGS:
        logger.debug(f"→ Prosseguir para Seção 5 (score excelente)")
        return "proceed_to_section_05"

    # Caso 2: Seção aceitável
    elif is_valid and score >= MIN_SCORE_TO_PROCEED:
        logger.debug(f"→ Prosseguir para Seção 5 (com avisos)")
        return "proceed_to_section_05"

    # Caso 3: Seção inválida, mas ainda pode refinar
    elif not is_valid and refine_attempts < MAX_REFINE_ATTEMPTS:
        logger.debug(f"→ Refinar Seção 4 (tentativa {refine_attempts + 1}/{MAX_REFINE_ATTEMPTS})")
        return "refine_section_04"

    # Caso 4: Seção inválida e já tentou refinar 2x
    else:
        logger.debug(f"→ Requer revisão manual")
        return "manual_review_required"


# ========== EDGES PARA SEÇÃO 5 ==========

def should_refine_section_05(state: ETPGenerationState) -> str:
    """
    Edge condicional: decidir próxima ação após validação da Seção 5.

    Mesma lógica das seções anteriores, mas para Seção 5.
    Após Seção 5, prossegue para Seção 6.
    """
    validation = state.get('section_05_validation', {})
    is_valid = validation.get('is_valid', False)
    score = validation.get('score', 0)
    refine_attempts = state.get('section_05_refine_attempts', 0)

    logger.debug(f"Decidindo próximo passo para Seção 5...")
    logger.debug(f"- Válido: {is_valid}")
    logger.debug(f"- Score: {score}")
    logger.debug(f"- Tentativas de refinamento: {refine_attempts}")

    # Caso 1: Seção excelente
    if is_valid and score >= MIN_SCORE_WITHOUT_WARNINGS:
        logger.debug(f"→ Prosseguir para Seção 6 (score excelente)")
        return "proceed_to_section_06"

    # Caso 2: Seção aceitável
    elif is_valid and score >= MIN_SCORE_TO_PROCEED:
        logger.debug(f"→ Prosseguir para Seção 6 (com avisos)")
        return "proceed_to_section_06"

    # Caso 3: Seção inválida, mas ainda pode refinar
    elif not is_valid and refine_attempts < MAX_REFINE_ATTEMPTS:
        logger.debug(f"→ Refinar Seção 5 (tentativa {refine_attempts + 1}/{MAX_REFINE_ATTEMPTS})")
        return "refine_section_05"

    # Caso 4: Seção inválida e já tentou refinar 2x
    else:
        logger.debug(f"→ Requer revisão manual")
        return "manual_review_required"


# ========== EDGES PARA SEÇÃO 6 ==========

def should_refine_section_06(state: ETPGenerationState) -> str:
    """
    Edge condicional: decidir próxima ação após validação da Seção 6.

    Mesma lógica das seções anteriores, mas para Seção 6.
    Seção 6 é a última por enquanto, então finaliza após ela.
    """
    validation = state.get('section_06_validation', {})
    is_valid = validation.get('is_valid', False)
    score = validation.get('score', 0)
    refine_attempts = state.get('section_06_refine_attempts', 0)

    logger.debug(f"Decidindo próximo passo para Seção 6...")
    logger.debug(f"- Válido: {is_valid}")
    logger.debug(f"- Score: {score}")
    logger.debug(f"- Tentativas de refinamento: {refine_attempts}")

    # Caso 1: Seção excelente
    if is_valid and score >= MIN_SCORE_WITHOUT_WARNINGS:
        logger.debug(f"→ Finalizar geração (score excelente)")
        return "finalize"

    # Caso 2: Seção aceitável
    elif is_valid and score >= MIN_SCORE_TO_PROCEED:
        logger.debug(f"→ Finalizar geração (com avisos)")
        return "finalize"

    # Caso 3: Seção inválida, mas ainda pode refinar
    elif not is_valid and refine_attempts < MAX_REFINE_ATTEMPTS:
        logger.debug(f"→ Refinar Seção 6 (tentativa {refine_attempts + 1}/{MAX_REFINE_ATTEMPTS})")
        return "refine_section_06"

    # Caso 4: Seção inválida e já tentou refinar 2x
    else:
        logger.debug(f"→ Requer revisão manual")
        return "manual_review_required"


# ========== HELPER FUNCTIONS ==========

def get_section_validation(state: ETPGenerationState, section_number: int) -> dict:
    """
    Helper para obter validação de uma seção específica.

    Args:
        state: Estado atual
        section_number: Número da seção (1-8)

    Returns:
        Dict com resultado da validação
    """
    validation_key = f'section_{section_number:02d}_validation'
    return state.get(validation_key, {})


def get_section_refine_attempts(state: ETPGenerationState, section_number: int) -> int:
    """
    Helper para obter número de tentativas de refinamento de uma seção.

    Args:
        state: Estado atual
        section_number: Número da seção (1-8)

    Returns:
        Número de tentativas de refinamento
    """
    attempts_key = f'section_{section_number:02d}_refine_attempts'
    return state.get(attempts_key, 0)
