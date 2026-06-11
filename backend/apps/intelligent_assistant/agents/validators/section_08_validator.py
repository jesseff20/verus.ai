"""
Section08Validator - Validador da Seção 8 do ETP.

Valida se a Seção 8 (Justificativa para Parcelamento)
atende aos requisitos da Lei 14.133/2021 e Decreto regulamentador local.
"""
from apps.intelligent_assistant.agents.validators.base_validator import (
    BaseValidator, create_validator_system_prompt
)


class Section08Validator(BaseValidator):
    """Validador da Seção 8 - Justificativa para Parcelamento."""

    SECTION_NUMBER = 8
    SECTION_NAME = "Justificativa para Parcelamento"
    MIN_WORDS = 250
    MAX_WORDS = 600
    KEYWORDS = ['parcelamento', 'divisão', 'lote', 'adjudicação', 'economia', 'escala']

    SYSTEM_PROMPT = create_validator_system_prompt(
        section_number=8,
        section_name="Justificativa para Parcelamento",
        criteria="""Avalie se a seção:

1. **Analisa divisibilidade do objeto**
   - Características técnicas são avaliadas?
   - Independência técnica de itens é verificada?

2. **Se PARCELAR - justifica divisão**
   - Quantos lotes/itens?
   - Critério de divisão?
   - Benefícios esperados?

3. **Se NÃO PARCELAR - justifica exceção**
   - Cita Art. 40, § 3° da Lei 14.133/2021?
   - Economia de escala justifica?
   - Objeto tecnicamente indivisível?

4. **Considera impacto em ME/EPP**
   - Participação de ME/EPP é analisada?
   - Art. 47 é considerado?
   - Cota reservada, se aplicável?

5. **Define critério de adjudicação**
   - Por item, grupo/lote ou global?
   - Decisão é justificada?

6. **Está alinhada com a Lei 14.133/2021**
   - Atende ao Art. 18, § 1º, inciso VIII?
   - Art. 40, § 3° (exceções ao parcelamento)?

7. **Tem qualidade técnica adequada**
   - Texto entre 250 e 600 palavras?
   - Decisão clara e fundamentada?"""
    )

    def __init__(self, claude_service, kb_service):
        super().__init__(claude_service, kb_service, "Section08Validator")
