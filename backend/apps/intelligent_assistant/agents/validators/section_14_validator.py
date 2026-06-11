"""
Section14Validator - Validador da Seção 14 do ETP.

Valida se a Seção 14 (Publicidade do ETP)
atende aos requisitos do Decreto regulamentador local.
"""
from apps.intelligent_assistant.agents.validators.base_validator import (
    BaseValidator, create_validator_system_prompt
)


class Section14Validator(BaseValidator):
    """Validador da Seção 14 - Publicidade do ETP."""

    SECTION_NUMBER = 14
    SECTION_NAME = "Publicidade do ETP"
    MIN_WORDS = 100
    MAX_WORDS = 300
    KEYWORDS = ['publicidade', 'sigilo', 'disponibilização', 'transparência', 'divulgação']

    SYSTEM_PROMPT = create_validator_system_prompt(
        section_number=14,
        section_name="Publicidade do ETP",
        criteria="""Avalie se a seção:

1. **Declara forma de publicidade**
   - Publicidade integral?
   - Publicidade parcial (com partes sigilosas)?
   - Classificação sigilosa total?

2. **Se houver SIGILO, justifica**
   - Motivos para classificação sigilosa?
   - Partes que serão sigilosas?
   - Fundamentação legal?

3. **Indica meios de disponibilização**
   - Portal de compras?
   - Diário Oficial?
   - Processo administrativo?

4. **Está alinhada com Decreto regulamentador local**
   - Atende ao Art. 10?
   - Sigilo é exceção justificada?

5. **Tem qualidade técnica adequada**
   - Texto entre 100 e 300 palavras?
   - Declaração formal clara?
   - Regra é publicidade integral?"""
    )

    def __init__(self, claude_service, kb_service):
        super().__init__(claude_service, kb_service, "Section14Validator")
