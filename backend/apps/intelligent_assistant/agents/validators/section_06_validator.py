"""
Section06Validator - Validador da Seção 6 do ETP.

Valida se a Seção 6 (Estimativa do Preço da Contratação)
atende aos requisitos da Lei 14.133/2021 e Decreto regulamentador local.
"""
from apps.intelligent_assistant.agents.validators.base_validator import (
    BaseValidator, create_validator_system_prompt
)


class Section06Validator(BaseValidator):
    """Validador da Seção 6 - Estimativa do Preço da Contratação."""

    SECTION_NUMBER = 6
    SECTION_NAME = "Estimativa do Preço da Contratação"
    MIN_WORDS = 300
    MAX_WORDS = 700
    KEYWORDS = ['preço', 'estimativa', 'valor', 'pesquisa', 'custo', 'orçamento', 'painel']

    SYSTEM_PROMPT = create_validator_system_prompt(
        section_number=6,
        section_name="Estimativa do Preço da Contratação",
        criteria="""Avalie se a seção:

1. **Apresenta metodologia de pesquisa**
   - Método de pesquisa está descrito?
   - Fontes são identificadas?
   - Período de referência é indicado?

2. **Cita fontes obrigatórias (Art. 23)**
   - Painel de Preços do Governo Federal?
   - Contratações similares de outros órgãos?
   - Pesquisa com fornecedores?
   - Mínimo de fontes diversas?

3. **Descreve composição de custos**
   - Itens que compõem o preço?
   - Custos diretos e indiretos?
   - BDI quando aplicável?

4. **Apresenta valores ou metodologia**
   - Se há valores: organizados em tabela?
   - Se não há: metodologia futura descrita?

5. **Considera sigilo (se aplicável)**
   - Art. 24 é mencionado se orçamento sigiloso?

6. **Está alinhada com a Lei 14.133/2021**
   - Atende ao Art. 18, § 1º, inciso VI?
   - Art. 23 (parâmetros de pesquisa)?

7. **Tem qualidade técnica adequada**
   - Texto entre 300 e 700 palavras?
   - Valores justificados?"""
    )

    def __init__(self, claude_service, kb_service):
        super().__init__(claude_service, kb_service, "Section06Validator")
