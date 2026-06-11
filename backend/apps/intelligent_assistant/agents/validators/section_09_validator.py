"""
Section09Validator - Validador da Seção 9 do ETP.

Valida se a Seção 9 (Demonstrativo dos Resultados Pretendidos)
atende aos requisitos da Lei 14.133/2021 e Decreto regulamentador local.
"""
from apps.intelligent_assistant.agents.validators.base_validator import (
    BaseValidator, create_validator_system_prompt
)


class Section09Validator(BaseValidator):
    """Validador da Seção 9 - Demonstrativo dos Resultados Pretendidos."""

    SECTION_NUMBER = 9
    SECTION_NAME = "Demonstrativo dos Resultados Pretendidos"
    MIN_WORDS = 250
    MAX_WORDS = 600
    KEYWORDS = ['resultado', 'economicidade', 'recurso', 'humano', 'material', 'financeiro']

    SYSTEM_PROMPT = create_validator_system_prompt(
        section_number=9,
        section_name="Demonstrativo dos Resultados Pretendidos",
        criteria="""Avalie se a seção:

1. **Demonstra resultados em ECONOMICIDADE**
   - Economia esperada com a contratação?
   - Comparação com situação atual?
   - Otimização de recursos financeiros?

2. **Demonstra aproveitamento de RECURSOS HUMANOS**
   - Liberação de servidores para atividades finalísticas?
   - Redução de sobrecarga de trabalho?
   - Melhoria na qualidade do trabalho?

3. **Demonstra aproveitamento de RECURSOS MATERIAIS**
   - Otimização do uso de materiais?
   - Redução de desperdícios?

4. **Demonstra aproveitamento de RECURSOS FINANCEIROS**
   - Otimização do orçamento?
   - Melhor relação custo-benefício?

5. **Apresenta indicadores (quando possível)**
   - Indicadores de desempenho?
   - Metas quantitativas/qualitativas?

6. **Está alinhada com a Lei 14.133/2021**
   - Atende ao Art. 18, § 1º, inciso IX?

7. **Tem qualidade técnica adequada**
   - Texto entre 250 e 600 palavras?
   - Resultados são realistas?"""
    )

    def __init__(self, claude_service, kb_service):
        super().__init__(claude_service, kb_service, "Section09Validator")
