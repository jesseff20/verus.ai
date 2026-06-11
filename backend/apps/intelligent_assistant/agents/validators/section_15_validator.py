"""
Section15Validator - Validador da Seção 15 do ETP.

Valida se a Seção 15 (Responsáveis pela Elaboração)
atende aos requisitos da Lei 14.133/2021 e Decreto regulamentador local.
"""
from apps.intelligent_assistant.agents.validators.base_validator import (
    BaseValidator, create_validator_system_prompt
)


class Section15Validator(BaseValidator):
    """Validador da Seção 15 - Responsáveis pela Elaboração."""

    SECTION_NUMBER = 15
    SECTION_NAME = "Responsáveis pela Elaboração do ETP"
    MIN_WORDS = 80
    MAX_WORDS = 250
    KEYWORDS = ['responsável', 'elaboração', 'assinatura', 'servidor', 'equipe', 'aprovação']

    SYSTEM_PROMPT = create_validator_system_prompt(
        section_number=15,
        section_name="Responsáveis pela Elaboração do ETP",
        criteria="""Avalie se a seção:

1. **Identifica os RESPONSÁVEIS**
   - Nomes (ou placeholders para preenchimento)?
   - Cargos/funções?
   - Setores de lotação?
   - Papel no ETP (elaborador, colaborador)?

2. **Identifica o SETOR DEMANDANTE**
   - Nome do setor/departamento?
   - Órgão vinculado?

3. **Registra declaração de responsabilidade**
   - Texto formal de responsabilidade?
   - Referência à Lei 14.133/2021?

4. **Apresenta campos para assinatura**
   - Espaço para assinaturas?
   - Local e data?
   - Campo para aprovação da autoridade?

5. **Está alinhada com a Lei 14.133/2021**
   - Art. 18, caput (elaboração conjunta)?

6. **Tem qualidade técnica adequada**
   - Formato adequado para assinaturas?
   - Placeholders claros para preenchimento?"""
    )

    def __init__(self, claude_service, kb_service):
        super().__init__(claude_service, kb_service, "Section15Validator")
