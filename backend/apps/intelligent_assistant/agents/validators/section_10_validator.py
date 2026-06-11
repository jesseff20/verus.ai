"""
Section10Validator - Validador da Seção 10 do ETP.

Valida se a Seção 10 (Providências Prévias ao Contrato)
atende aos requisitos da Lei 14.133/2021 e Decreto regulamentador local.
"""
from apps.intelligent_assistant.agents.validators.base_validator import (
    BaseValidator, create_validator_system_prompt
)


class Section10Validator(BaseValidator):
    """Validador da Seção 10 - Providências Prévias ao Contrato."""

    SECTION_NUMBER = 10
    SECTION_NAME = "Providências Prévias ao Contrato"
    MIN_WORDS = 200
    MAX_WORDS = 500
    KEYWORDS = ['providência', 'capacitação', 'fiscal', 'gestor', 'infraestrutura', 'treinamento']

    SYSTEM_PROMPT = create_validator_system_prompt(
        section_number=10,
        section_name="Providências Prévias ao Contrato",
        criteria="""Avalie se a seção:

1. **Identifica providências de CAPACITAÇÃO**
   - Treinamentos para gestores e fiscais?
   - Conhecimentos técnicos específicos?

2. **Identifica providências de INFRAESTRUTURA**
   - Adequação de espaço físico?
   - Aquisição de equipamentos?

3. **Identifica providências ADMINISTRATIVAS**
   - Designação de gestores e fiscais?
   - Elaboração de procedimentos?

4. **Identifica providências TÉCNICAS**
   - Sistemas de TI a preparar?
   - Integrações necessárias?

5. **Define cronograma de providências**
   - Sequência de ações?
   - Prazos estimados?
   - Responsáveis?

6. **Está alinhada com a Lei 14.133/2021**
   - Atende ao Art. 18, § 1º, inciso X?
   - Art. 117 (fiscalização)?

7. **Tem qualidade técnica adequada**
   - Texto entre 200 e 500 palavras?
   - Providências são realizáveis?"""
    )

    def __init__(self, claude_service, kb_service):
        super().__init__(claude_service, kb_service, "Section10Validator")
