"""
Section05Validator - Validador da Seção 5 do ETP.

Valida se a Seção 5 (Levantamento de Mercado)
atende aos requisitos da Lei 14.133/2021 e Decreto regulamentador local.
"""
from apps.intelligent_assistant.agents.validators.base_validator import (
    BaseValidator, create_validator_system_prompt
)


class Section05Validator(BaseValidator):
    """Validador da Seção 5 - Levantamento de Mercado."""

    SECTION_NUMBER = 5
    SECTION_NAME = "Levantamento de Mercado"
    MIN_WORDS = 400
    MAX_WORDS = 900
    KEYWORDS = ['mercado', 'alternativa', 'solução', 'fornecedor', 'comparação', 'análise']

    SYSTEM_PROMPT = create_validator_system_prompt(
        section_number=5,
        section_name="Levantamento de Mercado",
        criteria="""Avalie se a seção:

1. **Apresenta alternativas de soluções**
   - Diferentes soluções são identificadas?
   - Descrições são adequadas?
   - Preços estimados são apresentados?

2. **Faz análise comparativa**
   - Comparação objetiva entre soluções?
   - Critérios de conveniência e economicidade?
   - Tabela comparativa é utilizada?

3. **Considera ciclo de vida**
   - Custos de aquisição?
   - Custos de operação/manutenção?
   - Melhor relação custo-benefício?

4. **Analisa contratações similares**
   - Outros órgãos são consultados?
   - TCU é mencionado?

5. **Justifica escolha da solução**
   - Decisão é fundamentada?
   - Evita direcionamento?

6. **Está alinhada com a Lei 14.133/2021**
   - Atende ao Art. 18, § 1º, inciso V?
   - Art. 44 (ciclo de vida)?

7. **Tem qualidade técnica adequada**
   - Texto entre 400 e 900 palavras?
   - Análise fundamentada?"""
    )

    def __init__(self, claude_service, kb_service):
        super().__init__(claude_service, kb_service, "Section05Validator")
