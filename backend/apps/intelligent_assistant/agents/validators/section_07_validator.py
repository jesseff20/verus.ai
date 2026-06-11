"""
Section07Validator - Validador da Seção 7 do ETP.

Valida se a Seção 7 (Descrição da Solução como um Todo)
atende aos requisitos da Lei 14.133/2021 e Decreto regulamentador local.
"""
from apps.intelligent_assistant.agents.validators.base_validator import (
    BaseValidator, create_validator_system_prompt
)


class Section07Validator(BaseValidator):
    """Validador da Seção 7 - Descrição da Solução como um Todo."""

    SECTION_NUMBER = 7
    SECTION_NAME = "Descrição da Solução como um Todo"
    MIN_WORDS = 400
    MAX_WORDS = 900
    KEYWORDS = ['solução', 'manutenção', 'assistência', 'técnica', 'garantia', 'suporte']

    SYSTEM_PROMPT = create_validator_system_prompt(
        section_number=7,
        section_name="Descrição da Solução como um Todo",
        criteria="""Avalie se a seção:

1. **Descreve a solução escolhida**
   - Solução está bem descrita?
   - Escopo completo é apresentado?
   - Componentes são detalhados?

2. **Detalha entregas esperadas**
   - Itens/serviços que compõem a solução?
   - Funcionalidades principais?
   - Cronograma de implantação?

3. **Aborda manutenção (quando aplicável)**
   - Tipo de manutenção necessária?
   - Periodicidade?
   - Responsabilidades?

4. **Aborda assistência técnica (quando aplicável)**
   - Suporte técnico necessário?
   - SLA de atendimento?
   - Canais de suporte?

5. **Considera garantias e treinamento**
   - Garantias exigidas?
   - Treinamentos necessários?
   - Documentação técnica?

6. **Está alinhada com a Lei 14.133/2021**
   - Atende ao Art. 18, § 1º, inciso VII?

7. **Tem qualidade técnica adequada**
   - Texto entre 400 e 900 palavras?
   - Solução coerente com Seção 5 (mercado)?"""
    )

    def __init__(self, claude_service, kb_service):
        super().__init__(claude_service, kb_service, "Section07Validator")
