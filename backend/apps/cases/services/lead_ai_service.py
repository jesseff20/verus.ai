"""
Serviço de IA para análise e classificação de Leads no CRM.
Integração com Copilot para:
- Classificação automática de temperatura (hot/warm/cold)
- Sugestão de abordagem
- Previsão de conversão
- Follow-up automático
"""
import logging
from typing import Optional, Dict, Any
from django.utils import timezone

logger = logging.getLogger(__name__)


class LeadAIService:
    """Serviço de IA para análise de leads de CRM."""

    @staticmethod
    async def classify_lead_temperature(
        description: str,
        specialty: str,
        urgency: bool = False,
        estimated_value: Optional[float] = None,
        source: str = 'outro',
        intake_data: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Classifica a temperatura do lead (hot/warm/cold) baseado em análise de IA.

        Critérios considerados:
        - Urgência explícita na descrição
        - Palavras-chave de urgência ("urgente", "imediato", "prisão", "prazo")
        - Valor estimado alto
        - Origem qualificada (indicação, evento)
        - Dados completos no intake

        Returns:
            Dict com:
            - temperature: 'hot' | 'warm' | 'cold'
            - confidence: 0-100
            - reasons: lista de justificativas
            - suggested_approach: string com sugestão de abordagem
        """
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        # Montar prompt de análise
        prompt = f"""
Analise este lead jurídico e classifique sua temperatura (probabilidade de conversão):

**Dados do Lead:**
- Especialidade: {specialty}
- Origem: {source}
- Urgência declarada: {'Sim' if urgency else 'Não'}
- Valor estimado: R$ {estimated_value or 'Não informado'}
- Descrição: {description[:500] if description else 'Não informada'}
- Dados complementares: {intake_data or 'Nenhum'}

**Tarefa:**
1. Classifique a temperatura como HOT, WARM ou COLD
2. Atribua uma confiança de 0-100%
3. Liste 3-5 razões para a classificação
4. Sugira uma abordagem inicial personalizada

**Formato de resposta (JSON):**
{{
    "temperature": "hot|warm|cold",
    "confidence": 0-100,
    "reasons": ["razão 1", "razão 2", ...],
    "suggested_approach": "texto da abordagem sugerida"
}}
"""

        try:
            llm = UnifiedLLMService.get_service()
            response = await llm.generate_async(prompt, temperature=0.3)

            # Parse da resposta JSON
            import json
            import re

            # Extrair JSON da resposta
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    'temperature': result.get('temperature', 'warm').lower(),
                    'confidence': result.get('confidence', 50),
                    'reasons': result.get('reasons', []),
                    'suggested_approach': result.get('suggested_approach', ''),
                }
            else:
                # Fallback para análise heurística
                return LeadAIService._heuristic_classification(
                    description, urgency, estimated_value, source
                )

        except Exception as e:
            logger.warning(f'Erro na classificação IA do lead, usando fallback: {e}')
            return LeadAIService._heuristic_classification(
                description, urgency, estimated_value, source
            )

    @staticmethod
    def _heuristic_classification(
        description: str,
        urgency: bool,
        estimated_value: Optional[float],
        source: str,
    ) -> Dict[str, Any]:
        """Classificação heurística fallback quando IA não está disponível."""
        score = 50  # Começa neutro
        reasons = []

        # Urgência declarada (+20)
        if urgency:
            score += 20
            reasons.append('Urgência declarada')

        # Palavras-chave de urgência na descrição
        urgency_keywords = ['urgente', 'imediato', 'prisão', 'prisao', 'prazo',
                           'emergência', 'emergencia', 'hoje', 'agora', 'rápido', 'rapido']
        desc_lower = description.lower() if description else ''
        for keyword in urgency_keywords:
            if keyword in desc_lower:
                score += 15
                reasons.append(f'Palavra-chave de urgência: "{keyword}"')
                break

        # Valor estimado alto (+15)
        if estimated_value and estimated_value >= 10000:
            score += 15
            reasons.append('Valor estimado alto')
        elif estimated_value and estimated_value >= 5000:
            score += 8
            reasons.append('Valor estimado médio-alto')

        # Origem qualificada
        qualified_sources = ['indicacao', 'evento', 'whatsapp']
        if source in qualified_sources:
            score += 10
            reasons.append(f'Origem qualificada: {source}')

        # Descrição longa e detalhada (+10)
        if description and len(description) > 200:
            score += 10
            reasons.append('Descrição detalhada demonstra interesse')

        # Determinar temperatura
        if score >= 75:
            temperature = 'hot'
        elif score >= 55:
            temperature = 'warm'
        else:
            temperature = 'cold'
            if not description:
                reasons.append('Sem descrição = baixo engajamento')

        # Gerar abordagem sugerida
        approach = LeadAIService._generate_approach(temperature, source, urgency)

        return {
            'temperature': temperature,
            'confidence': min(95, max(30, score)),
            'reasons': reasons[:5],
            'suggested_approach': approach,
        }

    @staticmethod
    def _generate_approach(
        temperature: str,
        source: str,
        urgency: bool,
    ) -> str:
        """Gera sugestão de abordagem baseada no perfil do lead."""

        approaches = {
            'hot': {
                'default': 'Lead demonstra alto interesse. Contatar imediatamente (mesmo dia). Oferecer consulta urgente e apresentar proposta comercial na primeira conversa.',
                'indicacao': 'Lead quente por indicação. Usar nome de quem indicou como quebra-gelo. Agendar reunião ainda hoje.',
                'urgency': 'Situação urgente identificada. Prioridade máxima - contatar nos próximos 30 minutos se possível.',
            },
            'warm': {
                'default': 'Lead com interesse moderado. Contatar em até 24h. Focar em entender necessidade e construir relacionamento.',
                'indicacao': 'Lead morno por indicação. Contatar em até 48h mencionando quem indicou. Não pressionar por fechamento imediato.',
            },
            'cold': {
                'default': 'Lead frio ou pouco engajado. Enviar email informativo primeiro, aguardar resposta antes de ligar. Nutrir com conteúdo relevante.',
                'no_description': 'Lead sem detalhes. Enviar formulário de qualificação ou email com perguntas para entender melhor a necessidade.',
            },
        }

        if temperature == 'hot' and urgency:
            return approaches['hot']['urgency']
        elif temperature == 'hot' and source == 'indicacao':
            return approaches['hot']['indicacao']
        elif temperature == 'warm' and source == 'indicacao':
            return approaches['warm']['indicacao']
        elif temperature == 'cold':
            return approaches['cold'].get('no_description' if source == 'outro' else 'default')

        return approaches[temperature]['default']

    @staticmethod
    async def generate_follow_up_message(
        lead_name: str,
        temperature: str,
        specialty: str,
        last_interaction: Optional[str] = None,
        stage_name: Optional[str] = None,
    ) -> str:
        """
        Gera mensagem personalizada de follow-up para o lead.

        Args:
            lead_name: Nome do lead
            temperature: hot/warm/cold
            specialty: Área do direito
            last_interaction: Descrição da última interação (opcional)
            stage_name: Etapa atual do pipeline (opcional)

        Returns:
            Mensagem personalizada para email/whatsapp
        """
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        prompt = f"""
Gere uma mensagem de follow-up profissional e personalizada para um lead jurídico.

**Dados:**
- Nome: {lead_name}
- Temperatura: {temperature}
- Especialidade: {specialty}
- Etapa atual: {stage_name or 'Não definida'}
- Última interação: {last_interaction or 'Primeiro contato'}

**Objetivo:**
Criar mensagem que:
1. Demonstre interesse genuíno
2. Ofereça valor (insight, informação útil)
3. Tenha call-to-action claro mas não agressivo
4. Seja apropriada para o nível de temperatura ({temperature})

**Tom:**
- Hot: Mais direto, foco em fechamento
- Warm: Equilibrado, foco em relacionamento
- Cold: Informativo, foco em educação e confiança

**Formato:** Mensagem pronta para envio (email ou whatsapp), ~100-150 palavras.
"""

        try:
            llm = UnifiedLLMService.get_service()
            response = await llm.generate_async(prompt, temperature=0.7)
            return response.strip()
        except Exception as e:
            logger.warning(f'Erro ao gerar follow-up: {e}')
            return LeadAIService._fallback_follow_up(temperature, lead_name)

    @staticmethod
    def _fallback_follow_up(temperature: str, lead_name: str) -> str:
        """Fallback de follow-up quando IA não está disponível."""

        templates = {
            'hot': f"""
Olá, {lead_name}! Tudo bem?

Vi que demonstrou interesse em nossos serviços jurídicos e gostaria de agendar uma conversa ainda hoje para entender melhor sua necessidade e apresentar como podemos ajudar.

Tem disponibilidade para uma rápida ligação às [HORÁRIO]?

Aguardo seu retorno!
""",
            'warm': f"""
Olá, {lead_name}! Espero que esteja bem.

Gostaria de saber se teve oportunidade de refletir sobre nossa conversa e se ficou alguma dúvida sobre como podemos auxiliar em sua situação jurídica.

Fico à disposição para qualquer questão!

Abraços,
""",
            'cold': f"""
Olá, {lead_name}! Tudo bem?

Vi que entrou em contato conosco recentemente. Sei que às vezes a correria do dia a dia dificulta, então estou passando apenas para deixar as portas abertas.

Caso precise de orientação jurídica, conte conosco!

Atenciosamente,
""",
        }

        return templates.get(temperature, templates['warm']).strip()

    @staticmethod
    async def predict_conversion_probability(
        lead_data: Dict[str, Any],
        historical_data: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Prevê probabilidade de conversão do lead baseado em padrões históricos.

        Args:
            lead_data: Dados completos do lead
            historical_data: Dados históricos de leads convertidos (opcional)

        Returns:
            Dict com probability (0-100), factors (lista de fatores), recommendation
        """
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        # Preparar dados para análise
        lead_summary = f"""
- Especialidade: {lead_data.get('specialty', 'N/A')}
- Temperatura: {lead_data.get('temperature', 'warm')}
- Origem: {lead_data.get('source', 'outro')}
- Valor estimado: R$ {lead_data.get('estimated_value', 0)}
- Urgência: {'Sim' if lead_data.get('urgency') else 'Não'}
- Canal: {lead_data.get('lead_channel', 'N/A')}
"""

        prompt = f"""
Analise este lead e preveja a probabilidade de conversão em cliente pagante.

**Dados do Lead:**
{lead_summary}

**Tarefa:**
1. Estime probabilidade de conversão (0-100%)
2. Liste 3-5 fatores que mais influenciam
3. Dê uma recomendação de ação (investir tempo, nutrir, qualificar melhor, etc.)

**Formato (JSON):**
{{
    "probability": 0-100,
    "factors": ["fator 1", "fator 2", ...],
    "recommendation": "texto da recomendação"
}}
"""

        try:
            llm = UnifiedLLMService.get_service()
            response = await llm.generate_async(prompt, temperature=0.3)

            import json
            import re

            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    'probability': result.get('probability', 50),
                    'factors': result.get('factors', []),
                    'recommendation': result.get('recommendation', ''),
                }
        except Exception as e:
            logger.warning(f'Erro na previsão de conversão: {e}')

        # Fallback simples
        base_prob = {'hot': 75, 'warm': 45, 'cold': 20}
        temp = lead_data.get('temperature', 'warm')
        return {
            'probability': base_prob.get(temp, 45),
            'factors': ['Baseado apenas na temperatura do lead'],
            'recommendation': 'Aguardar mais dados para análise precisa.',
        }
