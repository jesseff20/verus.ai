"""
Agentes Geradores de Seções do ETP.

Cada arquivo neste módulo representa um agente especializado
em gerar uma das 15 seções do ETP seguindo o modelo padrão
da Lei 14.133/2021.

Estrutura das 15 Seções do ETP (Lei 14.133/2021):

1. Descrição da Necessidade (inciso I)
2. Previsão no Plano de Contratações Anual (inciso II)
3. Requisitos da Contratação (inciso III)
4. Estimativa das Quantidades e Memória de Cálculo (inciso IV)
5. Levantamento de Mercado (inciso V)
6. Estimativa do Preço da Contratação (inciso VI)
7. Descrição da Solução como um Todo (inciso VII)
8. Justificativa para Parcelamento (inciso VIII)
9. Demonstrativo dos Resultados Pretendidos (inciso IX)
10. Providências Prévias ao Contrato (inciso X)
11. Contratações Correlatas e/ou Interdependentes (inciso XI)
12. Impactos Ambientais (inciso XII)
13. Viabilidade da Contratação / Declaração de Viabilidade (incisos XIII e XIV)
14. Publicidade do ETP (Art. 10 Decreto 10.541)
15. Responsáveis pela Elaboração do ETP

Fundamentação Legal:
- Lei 14.133/2021 (Nova Lei de Licitações), Art. 18, § 1°
- Decreto regulamentador local, Art. 8°, § 1°
"""

from apps.intelligent_assistant.agents.section_agents.section_01_agent import Section01Agent
from apps.intelligent_assistant.agents.section_agents.section_02_agent import Section02Agent
from apps.intelligent_assistant.agents.section_agents.section_03_agent import Section03Agent
from apps.intelligent_assistant.agents.section_agents.section_04_agent import Section04Agent
from apps.intelligent_assistant.agents.section_agents.section_05_agent import Section05Agent
from apps.intelligent_assistant.agents.section_agents.section_06_agent import Section06Agent
from apps.intelligent_assistant.agents.section_agents.section_07_agent import Section07Agent
from apps.intelligent_assistant.agents.section_agents.section_08_agent import Section08Agent
from apps.intelligent_assistant.agents.section_agents.section_09_agent import Section09Agent
from apps.intelligent_assistant.agents.section_agents.section_10_agent import Section10Agent
from apps.intelligent_assistant.agents.section_agents.section_11_agent import Section11Agent
from apps.intelligent_assistant.agents.section_agents.section_12_agent import Section12Agent
from apps.intelligent_assistant.agents.section_agents.section_13_agent import Section13Agent
from apps.intelligent_assistant.agents.section_agents.section_14_agent import Section14Agent
from apps.intelligent_assistant.agents.section_agents.section_15_agent import Section15Agent

__all__ = [
    'Section01Agent',
    'Section02Agent',
    'Section03Agent',
    'Section04Agent',
    'Section05Agent',
    'Section06Agent',
    'Section07Agent',
    'Section08Agent',
    'Section09Agent',
    'Section10Agent',
    'Section11Agent',
    'Section12Agent',
    'Section13Agent',
    'Section14Agent',
    'Section15Agent',
]

# Mapeamento de número da seção para classe do agente
SECTION_AGENTS = {
    1: Section01Agent,
    2: Section02Agent,
    3: Section03Agent,
    4: Section04Agent,
    5: Section05Agent,
    6: Section06Agent,
    7: Section07Agent,
    8: Section08Agent,
    9: Section09Agent,
    10: Section10Agent,
    11: Section11Agent,
    12: Section12Agent,
    13: Section13Agent,
    14: Section14Agent,
    15: Section15Agent,
}
