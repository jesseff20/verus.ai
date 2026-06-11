"""
Section11Validator - Validador da Seção 11 do ETP.

Valida se a Seção 11 (Contratações Correlatas e/ou Interdependentes)
atende aos requisitos da Lei 14.133/2021 e Decreto regulamentador local.
"""
from apps.intelligent_assistant.agents.validators.base_validator import (
    BaseValidator, create_validator_system_prompt
)


class Section11Validator(BaseValidator):
    """Validador da Seção 11 - Contratações Correlatas e/ou Interdependentes."""

    SECTION_NUMBER = 11
    SECTION_NAME = "Contratações Correlatas e/ou Interdependentes"
    MIN_WORDS = 150
    MAX_WORDS = 450
    KEYWORDS = ['correlata', 'interdependente', 'contrato', 'contratação', 'vigente', 'relacionada']

    SYSTEM_PROMPT = create_validator_system_prompt(
        section_number=11,
        section_name="Contratações Correlatas e/ou Interdependentes",
        criteria="""Avalie se a seção:

1. **Identifica contratações CORRELATAS**
   - Contratos vigentes similares?
   - Atas de registro de preços relacionadas?
   - Oportunidades de agregação de demandas?

2. **Identifica contratações INTERDEPENDENTES**
   - Contratos de infraestrutura necessários?
   - Serviços de suporte essenciais?
   - Licenças ou autorizações prévias?

3. **Analisa IMPACTOS**
   - Como afetam o planejamento?
   - Oportunidades de economia de escala?
   - Riscos de incompatibilidade?

4. **Propõe ações de integração**
   - Alinhamento de cronogramas?
   - Padronização de especificações?

5. **Se NÃO há correlatas/interdependentes**
   - Declara expressamente?
   - Justifica a ausência?

6. **Está alinhada com a Lei 14.133/2021**
   - Atende ao Art. 18, § 1º, inciso XI?

7. **Tem qualidade técnica adequada**
   - Texto entre 150 e 450 palavras?
   - Conclusão clara?"""
    )

    def __init__(self, claude_service, kb_service):
        super().__init__(claude_service, kb_service, "Section11Validator")
