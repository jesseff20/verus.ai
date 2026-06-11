"""
Section12Validator - Validador da Seção 12 do ETP.

Valida se a Seção 12 (Impactos Ambientais)
atende aos requisitos da Lei 14.133/2021 e Decreto regulamentador local.
"""
from apps.intelligent_assistant.agents.validators.base_validator import (
    BaseValidator, create_validator_system_prompt
)


class Section12Validator(BaseValidator):
    """Validador da Seção 12 - Impactos Ambientais."""

    SECTION_NUMBER = 12
    SECTION_NAME = "Impactos Ambientais"
    MIN_WORDS = 200
    MAX_WORDS = 500
    KEYWORDS = ['ambiental', 'sustentabilidade', 'energia', 'resíduo', 'logística', 'reversa']

    SYSTEM_PROMPT = create_validator_system_prompt(
        section_number=12,
        section_name="Impactos Ambientais",
        criteria="""Avalie se a seção:

1. **Identifica IMPACTOS AMBIENTAIS**
   - Geração de resíduos?
   - Consumo de recursos naturais?
   - Consumo energético?

2. **Descreve MEDIDAS DE MITIGAÇÃO**
   - Medidas preventivas?
   - Medidas corretivas?
   - Tecnologias mais limpas?

3. **Considera EFICIÊNCIA ENERGÉTICA**
   - Requisitos de baixo consumo?
   - Certificações (PROCEL, etc.)?

4. **Aborda LOGÍSTICA REVERSA (quando aplicável)**
   - Responsabilidade pelo desfazimento?
   - Reciclagem de materiais?
   - Lei 12.305/2010?

5. **Considera CRITÉRIOS DE SUSTENTABILIDADE**
   - Selo Verde/certificações?
   - Materiais reciclados?

6. **Se NÃO há impactos significativos**
   - Declara e justifica?

7. **Está alinhada com a Lei 14.133/2021**
   - Atende ao Art. 18, § 1º, inciso XII?
   - Art. 11, IV (sustentabilidade)?

8. **Tem qualidade técnica adequada**
   - Texto entre 200 e 500 palavras?"""
    )

    def __init__(self, claude_service, kb_service):
        super().__init__(claude_service, kb_service, "Section12Validator")
