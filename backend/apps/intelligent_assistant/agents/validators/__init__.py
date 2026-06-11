"""
Agentes Validadores de Seções do ETP.

Cada validador é responsável por verificar se uma seção
gerada atende aos requisitos da Lei 14.133/2021.

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
from apps.intelligent_assistant.agents.validators.base_validator import (
    BaseValidator,
    create_validator_system_prompt
)
from apps.intelligent_assistant.agents.validators.section_01_validator import (
    Section01Validator
)
from apps.intelligent_assistant.agents.validators.section_02_validator import (
    Section02Validator
)
from apps.intelligent_assistant.agents.validators.section_03_validator import (
    Section03Validator
)
from apps.intelligent_assistant.agents.validators.section_04_validator import (
    Section04Validator
)
from apps.intelligent_assistant.agents.validators.section_05_validator import (
    Section05Validator
)
from apps.intelligent_assistant.agents.validators.section_06_validator import (
    Section06Validator
)
from apps.intelligent_assistant.agents.validators.section_07_validator import (
    Section07Validator
)
from apps.intelligent_assistant.agents.validators.section_08_validator import (
    Section08Validator
)
from apps.intelligent_assistant.agents.validators.section_09_validator import (
    Section09Validator
)
from apps.intelligent_assistant.agents.validators.section_10_validator import (
    Section10Validator
)
from apps.intelligent_assistant.agents.validators.section_11_validator import (
    Section11Validator
)
from apps.intelligent_assistant.agents.validators.section_12_validator import (
    Section12Validator
)
from apps.intelligent_assistant.agents.validators.section_13_validator import (
    Section13Validator
)
from apps.intelligent_assistant.agents.validators.section_14_validator import (
    Section14Validator
)
from apps.intelligent_assistant.agents.validators.section_15_validator import (
    Section15Validator
)

__all__ = [
    # Base
    'BaseValidator',
    'create_validator_system_prompt',
    # Validators - 15 Seções
    'Section01Validator',  # Descrição da Necessidade
    'Section02Validator',  # Previsão no PCA
    'Section03Validator',  # Requisitos da Contratação
    'Section04Validator',  # Estimativa das Quantidades
    'Section05Validator',  # Levantamento de Mercado
    'Section06Validator',  # Estimativa do Preço
    'Section07Validator',  # Descrição da Solução
    'Section08Validator',  # Justificativa Parcelamento
    'Section09Validator',  # Resultados Pretendidos
    'Section10Validator',  # Providências Prévias
    'Section11Validator',  # Contratações Correlatas
    'Section12Validator',  # Impactos Ambientais
    'Section13Validator',  # Viabilidade da Contratação
    'Section14Validator',  # Publicidade do ETP
    'Section15Validator',  # Responsáveis pela Elaboração
]

# Mapeamento de número da seção para validador
SECTION_VALIDATORS = {
    1: Section01Validator,
    2: Section02Validator,
    3: Section03Validator,
    4: Section04Validator,
    5: Section05Validator,
    6: Section06Validator,
    7: Section07Validator,
    8: Section08Validator,
    9: Section09Validator,
    10: Section10Validator,
    11: Section11Validator,
    12: Section12Validator,
    13: Section13Validator,
    14: Section14Validator,
    15: Section15Validator,
}


def get_validator(section_number: int):
    """Retorna a classe do validador para a seção especificada."""
    return SECTION_VALIDATORS.get(section_number)
