"""
ETP State - Definição do estado do grafo LangGraph.

Define o TypedDict com todos os campos necessários para
o fluxo de geração de ETP com 15 seções (Lei 14.133/2021).
"""
from typing import TypedDict, Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class SectionStatus(str, Enum):
    """Status de processamento de uma seção."""
    PENDING = "pending"
    GENERATING = "generating"
    VALIDATING = "validating"
    VALID = "valid"
    INVALID = "invalid"
    REGENERATING = "regenerating"
    ERROR = "error"


class ValidationResult(TypedDict, total=False):
    """Resultado da validação de uma seção."""
    is_valid: bool
    score: float
    structural_issues: List[str]
    semantic_issues: List[str]
    suggestions: List[str]
    word_count: int
    keywords_found: List[str]
    keywords_missing: List[str]


class SectionData(TypedDict, total=False):
    """Dados de uma seção do ETP."""
    content: str
    status: SectionStatus
    validation: ValidationResult
    generation_attempts: int
    last_updated: str
    error_message: Optional[str]


class ETPState(TypedDict, total=False):
    """
    Estado completo do grafo de geração de ETP.

    Lei 14.133/2021 - 15 Seções:
    1. Descrição da Necessidade (Art. 18, § 1º, I)
    2. Previsão no Plano de Contratações Anual (Art. 18, § 1º, II)
    3. Requisitos da Contratação (Art. 18, § 1º, III)
    4. Estimativa das Quantidades (Art. 18, § 1º, IV)
    5. Levantamento de Mercado (Art. 18, § 1º, V)
    6. Estimativa do Preço (Art. 18, § 1º, VI)
    7. Descrição da Solução (Art. 18, § 1º, VII)
    8. Justificativa para Parcelamento (Art. 18, § 1º, VIII)
    9. Resultados Pretendidos (Art. 18, § 1º, IX)
    10. Providências Prévias (Art. 18, § 1º, X)
    11. Contratações Correlatas (Art. 18, § 1º, XI)
    12. Impactos Ambientais (Art. 18, § 1º, XII)
    13. Viabilidade da Contratação (Art. 18, § 1º, XIII e XIV)
    14. Publicidade do ETP (Art. 10, Decreto 10.541)
    15. Responsáveis pela Elaboração (Art. 18, caput)
    """
    # === Inputs do usuário ===
    objective: str  # Objetivo da contratação
    collection_name: Optional[str]  # Collection do ChromaDB para RAG
    user_id: Optional[str]  # ID do usuário
    organization_id: Optional[str]  # ID da organização

    # === Metadados do ETP ===
    etp_id: Optional[str]
    created_at: str
    updated_at: str
    status: str  # draft, generating, validating, completed, error

    # === Seções do ETP (15 seções) ===
    section_01: SectionData  # Descrição da Necessidade
    section_02: SectionData  # Previsão no PCA
    section_03: SectionData  # Requisitos da Contratação
    section_04: SectionData  # Estimativa das Quantidades
    section_05: SectionData  # Levantamento de Mercado
    section_06: SectionData  # Estimativa do Preço
    section_07: SectionData  # Descrição da Solução
    section_08: SectionData  # Justificativa Parcelamento
    section_09: SectionData  # Resultados Pretendidos
    section_10: SectionData  # Providências Prévias
    section_11: SectionData  # Contratações Correlatas
    section_12: SectionData  # Impactos Ambientais
    section_13: SectionData  # Viabilidade da Contratação
    section_14: SectionData  # Publicidade do ETP
    section_15: SectionData  # Responsáveis pela Elaboração

    # === Controle do fluxo ===
    current_section: int  # Seção atual sendo processada (1-15)
    max_retries: int  # Máximo de tentativas por seção
    errors: List[str]  # Lista de erros ocorridos
    sections_to_generate: List[int]  # Lista de seções a gerar (1-15)

    # === Resultado final ===
    final_document: Optional[str]  # Documento ETP completo
    overall_validation: Optional[Dict[str, Any]]  # Validação geral


# Nomes das seções (Lei 14.133/2021)
SECTION_NAMES = {
    1: "Descrição da Necessidade",
    2: "Previsão no Plano de Contratações Anual",
    3: "Requisitos da Contratação",
    4: "Estimativa das Quantidades e Memória de Cálculo",
    5: "Levantamento de Mercado",
    6: "Estimativa do Preço da Contratação",
    7: "Descrição da Solução como um Todo",
    8: "Justificativa para Parcelamento ou Não",
    9: "Demonstrativo dos Resultados Pretendidos",
    10: "Providências Prévias ao Contrato",
    11: "Contratações Correlatas e/ou Interdependentes",
    12: "Impactos Ambientais",
    13: "Viabilidade da Contratação / Declaração de Viabilidade",
    14: "Publicidade do ETP",
    15: "Responsáveis pela Elaboração do ETP",
}

# Referências legais por seção
SECTION_LEGAL_REFS = {
    1: "Art. 18, § 1º, inciso I - Lei 14.133/2021",
    2: "Art. 18, § 1º, inciso II - Lei 14.133/2021",
    3: "Art. 18, § 1º, inciso III - Lei 14.133/2021",
    4: "Art. 18, § 1º, inciso IV - Lei 14.133/2021",
    5: "Art. 18, § 1º, inciso V - Lei 14.133/2021",
    6: "Art. 18, § 1º, inciso VI - Lei 14.133/2021",
    7: "Art. 18, § 1º, inciso VII - Lei 14.133/2021",
    8: "Art. 18, § 1º, inciso VIII - Lei 14.133/2021",
    9: "Art. 18, § 1º, inciso IX - Lei 14.133/2021",
    10: "Art. 18, § 1º, inciso X - Lei 14.133/2021",
    11: "Art. 18, § 1º, inciso XI - Lei 14.133/2021",
    12: "Art. 18, § 1º, inciso XII - Lei 14.133/2021",
    13: "Art. 18, § 1º, incisos XIII e XIV - Lei 14.133/2021",
    14: "Art. 10 - Decreto regulamentador local",
    15: "Art. 18, caput - Lei 14.133/2021",
}


def create_initial_state(
    objective: str,
    collection_name: Optional[str] = None,
    user_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    max_retries: int = 3,
    sections_to_generate: Optional[List[int]] = None
) -> ETPState:
    """
    Cria o estado inicial do grafo ETP.

    Args:
        objective: Objetivo da contratação
        collection_name: Collection do ChromaDB para RAG
        user_id: ID do usuário
        organization_id: ID da organização
        max_retries: Máximo de tentativas por seção
        sections_to_generate: Lista de seções a gerar (1-15). Se None, gera todas.

    Returns:
        Estado inicial do ETPState
    """
    now = datetime.utcnow().isoformat()

    # Seções a gerar (default: todas)
    sections = sections_to_generate if sections_to_generate else list(range(1, 16))
    first_section = min(sections) if sections else 1

    # Cria estado inicial para cada seção
    def create_section_data(section_num: int) -> SectionData:
        # Se a seção não está na lista de seções a gerar, marca como SKIPPED
        if section_num not in sections:
            return {
                "content": "",
                "status": "skipped",  # Seção será pulada
                "validation": {},
                "generation_attempts": 0,
                "last_updated": now,
                "error_message": None,
            }
        return {
            "content": "",
            "status": SectionStatus.PENDING,
            "validation": {},
            "generation_attempts": 0,
            "last_updated": now,
            "error_message": None,
        }

    return {
        # Inputs
        "objective": objective,
        "collection_name": collection_name,
        "user_id": user_id,
        "organization_id": organization_id,

        # Metadados
        "etp_id": None,
        "created_at": now,
        "updated_at": now,
        "status": "draft",

        # 15 Seções
        "section_01": create_section_data(1),
        "section_02": create_section_data(2),
        "section_03": create_section_data(3),
        "section_04": create_section_data(4),
        "section_05": create_section_data(5),
        "section_06": create_section_data(6),
        "section_07": create_section_data(7),
        "section_08": create_section_data(8),
        "section_09": create_section_data(9),
        "section_10": create_section_data(10),
        "section_11": create_section_data(11),
        "section_12": create_section_data(12),
        "section_13": create_section_data(13),
        "section_14": create_section_data(14),
        "section_15": create_section_data(15),

        # Controle
        "current_section": first_section,
        "max_retries": max_retries,
        "errors": [],
        "sections_to_generate": sections,  # Lista de seções a gerar

        # Resultado
        "final_document": None,
        "overall_validation": None,
    }


def get_section_key(section_number: int) -> str:
    """Retorna a chave do estado para uma seção."""
    return f"section_{section_number:02d}"


def get_section_name(section_number: int) -> str:
    """Retorna o nome da seção."""
    return SECTION_NAMES.get(section_number, f"Seção {section_number}")


def get_section_legal_ref(section_number: int) -> str:
    """Retorna a referência legal da seção."""
    return SECTION_LEGAL_REFS.get(section_number, "")
