"""
Section04Validator - Validador da Seção 4 do ETP.

Valida se a Seção 4 (Estimativa das Quantidades e Memória de Cálculo)
atende aos requisitos da Lei 14.133/2021 e Decreto regulamentador local.
"""
from apps.intelligent_assistant.agents.validators.base_validator import (
    BaseValidator, create_validator_system_prompt
)


class Section04Validator(BaseValidator):
    """Validador da Seção 4 - Estimativa das Quantidades e Memória de Cálculo."""

    SECTION_NUMBER = 4
    SECTION_NAME = "Estimativa das Quantidades e Memória de Cálculo"
    MIN_WORDS = 300
    MAX_WORDS = 700
    KEYWORDS = ['quantidade', 'memória', 'cálculo', 'estimativa', 'consumo', 'histórico']

    SYSTEM_PROMPT = create_validator_system_prompt(
        section_number=4,
        section_name="Estimativa das Quantidades e Memória de Cálculo",
        criteria="""Avalie se a seção:

1. **Apresenta estimativa de quantidades**
   - Quantidades estão especificadas?
   - Unidades de medida são indicadas?
   - Itens/serviços são detalhados?

2. **Apresenta memória de cálculo**
   - Metodologia de cálculo está descrita?
   - Fórmulas ou critérios são apresentados?
   - Dados base são citados?

3. **Considera bases de estimativa**
   - Consumo histórico é mencionado?
   - Projeção de demanda é apresentada?
   - Normas internas são citadas?

4. **Avalia economia de escala**
   - Interdependência com outras contratações?
   - Ganhos de escala são considerados?

5. **Está alinhada com a Lei 14.133/2021**
   - Atende ao Art. 18, § 1º, inciso IV?

6. **Tem qualidade técnica adequada**
   - Texto entre 300 e 700 palavras?
   - Quantidades justificadas?
   - Usa tabelas quando apropriado?"""
    )

    def __init__(self, claude_service, kb_service):
        super().__init__(claude_service, kb_service, "Section04Validator")
