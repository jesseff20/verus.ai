"""
Section13Validator - Validador da Seção 13 do ETP.

Valida se a Seção 13 (Viabilidade da Contratação / Declaração de Viabilidade)
atende aos requisitos da Lei 14.133/2021 e Decreto regulamentador local.
"""
from apps.intelligent_assistant.agents.validators.base_validator import (
    BaseValidator, create_validator_system_prompt
)


class Section13Validator(BaseValidator):
    """Validador da Seção 13 - Viabilidade da Contratação."""

    SECTION_NUMBER = 13
    SECTION_NAME = "Viabilidade da Contratação / Declaração de Viabilidade"
    MIN_WORDS = 300
    MAX_WORDS = 700
    KEYWORDS = ['viabilidade', 'viável', 'técnica', 'econômica', 'legal', 'declaração']

    SYSTEM_PROMPT = create_validator_system_prompt(
        section_number=13,
        section_name="Viabilidade da Contratação / Declaração de Viabilidade",
        criteria="""Avalie se a seção:

1. **Avalia VIABILIDADE TÉCNICA**
   - Solução atende requisitos técnicos?
   - Fornecedores disponíveis?
   - Prazo realizável?

2. **Avalia VIABILIDADE ECONÔMICA**
   - Custo compatível com orçamento?
   - Relação custo-benefício adequada?
   - Preços compatíveis com mercado?

3. **Avalia VIABILIDADE LEGAL**
   - Amparo legal para contratação?
   - Requisitos atendem legislação?
   - Impedimentos legais identificados?

4. **Avalia VIABILIDADE OPERACIONAL**
   - Capacidade de gestão?
   - Estrutura para fiscalização?
   - Riscos mapeados?

5. **Emite POSICIONAMENTO CONCLUSIVO**
   - Declaração clara: VIÁVEL ou NÃO VIÁVEL?
   - Fundamentação da decisão?
   - Ressalvas ou condicionantes?

6. **Está alinhada com a Lei 14.133/2021**
   - Atende ao Art. 18, § 1º, incisos XIII e XIV?

7. **Tem qualidade técnica adequada**
   - Texto entre 300 e 700 palavras?
   - Declaração formal ao final?
   - Tabela resumo de viabilidade?"""
    )

    def __init__(self, claude_service, kb_service):
        super().__init__(claude_service, kb_service, "Section13Validator")
