"""
Estado compartilhado do grafo LangGraph para geração de ETP.

O State é a estrutura de dados que flui entre todos os nós do grafo,
acumulando informações e resultados ao longo da execução.

Baseado na Lei 14.133/2021 com 15 seções.
"""
from typing import TypedDict, List, Optional, Dict, Any
from typing_extensions import Annotated
from operator import add


class ETPGenerationState(TypedDict):
    """
    Estado compartilhado entre todos os nós do grafo de geração de ETP.

    Este estado é imutável - cada nó retorna uma cópia modificada.

    Seções conforme Lei 14.133/2021:
    1. Descrição da Necessidade
    2. Previsão no Plano de Contratações Anual
    3. Requisitos da Contratação
    4. Estimativa das Quantidades e Memória de Cálculo
    5. Levantamento de Mercado
    6. Estimativa do Preço da Contratação
    7. Descrição da Solução como um Todo
    8. Justificativa para Parcelamento
    9. Demonstrativo dos Resultados Pretendidos
    10. Providências Prévias ao Contrato
    11. Contratações Correlatas/Interdependentes
    12. Impactos Ambientais
    13. Viabilidade da Contratação
    14. Publicidade do ETP
    15. Responsáveis
    """

    # ========== INPUT INICIAL ==========
    objective: str
    """Objetivo da contratação (ex: 'Contratar serviço de desenvolvimento de software')"""

    collection_name: str
    """Nome da collection do ChromaDB para busca de contexto"""

    # ========== SEÇÕES DO ETP (15 seções) ==========

    section_01: Optional[str]
    """Seção 1: Descrição da Necessidade da Contratação"""

    section_02: Optional[str]
    """Seção 2: Previsão no Plano de Contratações Anual"""

    section_03: Optional[str]
    """Seção 3: Requisitos da Contratação"""

    section_04: Optional[str]
    """Seção 4: Estimativa das Quantidades e Memória de Cálculo"""

    section_05: Optional[str]
    """Seção 5: Levantamento de Mercado"""

    section_06: Optional[str]
    """Seção 6: Estimativa do Preço da Contratação"""

    section_07: Optional[str]
    """Seção 7: Descrição da Solução como um Todo"""

    section_08: Optional[str]
    """Seção 8: Justificativa para Parcelamento"""

    section_09: Optional[str]
    """Seção 9: Demonstrativo dos Resultados Pretendidos"""

    section_10: Optional[str]
    """Seção 10: Providências Prévias ao Contrato"""

    section_11: Optional[str]
    """Seção 11: Contratações Correlatas/Interdependentes"""

    section_12: Optional[str]
    """Seção 12: Impactos Ambientais"""

    section_13: Optional[str]
    """Seção 13: Viabilidade da Contratação"""

    section_14: Optional[str]
    """Seção 14: Publicidade do ETP"""

    section_15: Optional[str]
    """Seção 15: Responsáveis"""

    # ========== VALIDAÇÕES ==========

    section_01_validation: Optional[Dict[str, Any]]
    """Resultado da validação da Seção 1"""

    section_02_validation: Optional[Dict[str, Any]]
    """Resultado da validação da Seção 2"""

    section_03_validation: Optional[Dict[str, Any]]
    """Resultado da validação da Seção 3"""

    section_04_validation: Optional[Dict[str, Any]]
    """Resultado da validação da Seção 4"""

    section_05_validation: Optional[Dict[str, Any]]
    """Resultado da validação da Seção 5"""

    section_06_validation: Optional[Dict[str, Any]]
    """Resultado da validação da Seção 6"""

    section_07_validation: Optional[Dict[str, Any]]
    """Resultado da validação da Seção 7"""

    section_08_validation: Optional[Dict[str, Any]]
    """Resultado da validação da Seção 8"""

    section_09_validation: Optional[Dict[str, Any]]
    """Resultado da validação da Seção 9"""

    section_10_validation: Optional[Dict[str, Any]]
    """Resultado da validação da Seção 10"""

    section_11_validation: Optional[Dict[str, Any]]
    """Resultado da validação da Seção 11"""

    section_12_validation: Optional[Dict[str, Any]]
    """Resultado da validação da Seção 12"""

    section_13_validation: Optional[Dict[str, Any]]
    """Resultado da validação da Seção 13"""

    section_14_validation: Optional[Dict[str, Any]]
    """Resultado da validação da Seção 14"""

    section_15_validation: Optional[Dict[str, Any]]
    """Resultado da validação da Seção 15"""

    # ========== CONTROLE DE REFINAMENTO ==========

    section_01_refine_attempts: int
    """Número de tentativas de refinamento da Seção 1 (máx 2)"""

    section_02_refine_attempts: int
    """Número de tentativas de refinamento da Seção 2 (máx 2)"""

    section_03_refine_attempts: int
    """Número de tentativas de refinamento da Seção 3 (máx 2)"""

    section_04_refine_attempts: int
    """Número de tentativas de refinamento da Seção 4 (máx 2)"""

    section_05_refine_attempts: int
    """Número de tentativas de refinamento da Seção 5 (máx 2)"""

    section_06_refine_attempts: int
    """Número de tentativas de refinamento da Seção 6 (máx 2)"""

    section_07_refine_attempts: int
    """Número de tentativas de refinamento da Seção 7 (máx 2)"""

    section_08_refine_attempts: int
    """Número de tentativas de refinamento da Seção 8 (máx 2)"""

    section_09_refine_attempts: int
    """Número de tentativas de refinamento da Seção 9 (máx 2)"""

    section_10_refine_attempts: int
    """Número de tentativas de refinamento da Seção 10 (máx 2)"""

    section_11_refine_attempts: int
    """Número de tentativas de refinamento da Seção 11 (máx 2)"""

    section_12_refine_attempts: int
    """Número de tentativas de refinamento da Seção 12 (máx 2)"""

    section_13_refine_attempts: int
    """Número de tentativas de refinamento da Seção 13 (máx 2)"""

    section_14_refine_attempts: int
    """Número de tentativas de refinamento da Seção 14 (máx 2)"""

    section_15_refine_attempts: int
    """Número de tentativas de refinamento da Seção 15 (máx 2)"""

    # ========== METADADOS E CONTROLE ==========

    current_section: int
    """Número da seção atual sendo processada (1-15)"""

    errors: Annotated[List[str], add]
    """Lista de erros encontrados durante a geração"""

    warnings: Annotated[List[str], add]
    """Lista de avisos durante a geração"""

    reasoning_log: Annotated[List[str], add]
    """Log de raciocínio dos agentes (para debug e transparência)"""

    total_tokens_used: int
    """Total de tokens consumidos (input + output)"""

    # ========== STATUS ==========

    requires_manual_review: bool
    """Flag indicando se o ETP requer revisão manual"""

    generation_complete: bool
    """Flag indicando se a geração foi concluída com sucesso"""


# Mapeamento das seções para referência
ETP_SECTIONS = {
    1: "Descrição da Necessidade",
    2: "Previsão no Plano de Contratações Anual",
    3: "Requisitos da Contratação",
    4: "Estimativa das Quantidades e Memória de Cálculo",
    5: "Levantamento de Mercado",
    6: "Estimativa do Preço da Contratação",
    7: "Descrição da Solução como um Todo",
    8: "Justificativa para Parcelamento",
    9: "Demonstrativo dos Resultados Pretendidos",
    10: "Providências Prévias ao Contrato",
    11: "Contratações Correlatas/Interdependentes",
    12: "Impactos Ambientais",
    13: "Viabilidade da Contratação",
    14: "Publicidade do ETP",
    15: "Responsáveis",
}


def create_initial_state(objective: str, collection_name: str = 'default') -> ETPGenerationState:
    """
    Cria o estado inicial do grafo de geração de ETP.

    Args:
        objective: Objetivo da contratação
        collection_name: Nome da collection do ChromaDB

    Returns:
        Estado inicial preenchido com valores padrão
    """
    return ETPGenerationState(
        # Input
        objective=objective,
        collection_name=collection_name,

        # Seções (todas None inicialmente)
        section_01=None,
        section_02=None,
        section_03=None,
        section_04=None,
        section_05=None,
        section_06=None,
        section_07=None,
        section_08=None,
        section_09=None,
        section_10=None,
        section_11=None,
        section_12=None,
        section_13=None,
        section_14=None,
        section_15=None,

        # Validações (todas None inicialmente)
        section_01_validation=None,
        section_02_validation=None,
        section_03_validation=None,
        section_04_validation=None,
        section_05_validation=None,
        section_06_validation=None,
        section_07_validation=None,
        section_08_validation=None,
        section_09_validation=None,
        section_10_validation=None,
        section_11_validation=None,
        section_12_validation=None,
        section_13_validation=None,
        section_14_validation=None,
        section_15_validation=None,

        # Contadores de refinamento (todos 0 inicialmente)
        section_01_refine_attempts=0,
        section_02_refine_attempts=0,
        section_03_refine_attempts=0,
        section_04_refine_attempts=0,
        section_05_refine_attempts=0,
        section_06_refine_attempts=0,
        section_07_refine_attempts=0,
        section_08_refine_attempts=0,
        section_09_refine_attempts=0,
        section_10_refine_attempts=0,
        section_11_refine_attempts=0,
        section_12_refine_attempts=0,
        section_13_refine_attempts=0,
        section_14_refine_attempts=0,
        section_15_refine_attempts=0,

        # Metadados
        current_section=1,
        errors=[],
        warnings=[],
        reasoning_log=[],
        total_tokens_used=0,

        # Status
        requires_manual_review=False,
        generation_complete=False,
    )
