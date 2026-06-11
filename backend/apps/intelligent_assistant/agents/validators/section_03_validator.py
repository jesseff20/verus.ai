"""
Section03Validator - Validador da Seção 3 do ETP.

Valida se a Seção 3 (Requisitos da Contratação)
atende aos requisitos da Lei 14.133/2021 e Decreto regulamentador local.
"""
from apps.intelligent_assistant.agents.validators.base_validator import (
    BaseValidator, create_validator_system_prompt
)


class Section03Validator(BaseValidator):
    """Validador da Seção 3 - Requisitos da Contratação."""

    SECTION_NUMBER = 3
    SECTION_NAME = "Requisitos da Contratação"
    MIN_WORDS = 300
    MAX_WORDS = 800
    KEYWORDS = ['requisitos', 'técnico', 'funcional', 'sustentabilidade', 'norma', 'padrão']

    SYSTEM_PROMPT = create_validator_system_prompt(
        section_number=3,
        section_name="Requisitos da Contratação",
        criteria="""Avalie se a seção:

1. **Define requisitos técnicos**
   - Especificações técnicas estão claras?
   - Padrões de qualidade são mencionados?
   - Características do objeto estão definidas?

2. **Define requisitos funcionais**
   - Funcionalidades necessárias estão listadas?
   - Níveis de serviço (SLA) são mencionados?
   - Capacidades requeridas são descritas?

3. **Aborda requisitos normativos**
   - Normas técnicas são citadas (ABNT, ISO)?
   - Legislação aplicável é mencionada?
   - Certificações necessárias são indicadas?

4. **Considera sustentabilidade**
   - Critérios de sustentabilidade são mencionados?
   - Requisitos ambientais são considerados?

5. **Está alinhada com a Lei 14.133/2021**
   - Atende ao Art. 18, § 1º, inciso III?
   - Requisitos são proporcionais ao objeto?

6. **Tem qualidade técnica adequada**
   - Texto entre 300 e 800 palavras?
   - Linguagem clara e objetiva?
   - Sem erros graves?"""
    )

    def __init__(self, claude_service, kb_service):
        super().__init__(claude_service, kb_service, "Section03Validator")
