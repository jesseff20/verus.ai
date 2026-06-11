"""
Serviço de IA para análise de movimentações e publicações do Tribunal Push.
Integração com Copilot para:
- Análise e interpretação de movimentações processuais
- Sugestão de ações jurídicas baseadas no contexto
- Resumo de publicações do Diário Oficial
- Classificação de relevância (alta/média/baixa)
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class PushAnalysisService:
    """Serviço de análise de eventos do Tribunal Push com IA."""

    # Mapeamento de tipos de evento para ações sugeridas
    ACTION_SUGGESTIONS = {
        'movimentacao': [
            'Verificar teor da movimentação e atualizar fase do processo',
            'Analisar impacto no prazo processual',
            'Comunicar cliente sobre nova movimentação',
            'Preparar manifestação se necessário',
        ],
        'intimacao': [
            'Calcular prazo processual a partir da intimação',
            'Verificar tipo de intimação e urgência',
            'Preparar manifestação ou recurso',
            'Incluir tarefa no calendário da equipe',
        ],
        'publicacao': [
            'Ler publicação completa no DJe',
            'Identificar informações relevantes',
            'Verificar necessidade de manifestação',
            'Arquivar publicação nos autos digitais',
        ],
        'despacho': [
            'Analisar teor do despacho',
            'Verificar se há determinação a cumprir',
            'Preparar manifestação ou cumprimento',
            'Acompanhar próximo andamento',
        ],
        'sentenca': [
            'Analisar fundamentos da sentença',
            'Verificar prazo para recursos (15 dias úteis)',
            'Comunicar cliente sobre resultado',
            'Preparar minuta de apelação se cabível',
        ],
        'decisao': [
            'Analisar decisão interlocutória',
            'Verificar cabimento de agravo',
            'Cumprir determinações judiciais',
            'Acompanhar próximo andamento',
        ],
        'audiencia': [
            'Preparar cliente para audiência',
            'Reunir documentos e provas',
            'Confirmar presença de testemunhas',
            'Elaborar roteiro de perguntas',
        ],
        'citacao': [
            'Acompanhar validade da citação',
            'Verificar prazo para contestação (15 dias)',
            'Preparar defesa se citado',
            'Monitorar revelia se aplicável',
        ],
        'juntada': [
            'Verificar documento juntado',
            'Analisar necessidade de manifestação',
            'Atualizar cronologia processual',
            'Comunicar cliente se relevante',
        ],
    }

    # Palavras-chave de alta relevância por tipo
    HIGH_RELEVANCE_KEYWORDS = {
        'movimentacao': ['concluso', 'sentença', 'decisão', 'liminar', 'tutela', 'urgência'],
        'intimacao': ['sentença', 'decisão', 'liminar', 'tutela', 'embargos', 'recurso'],
        'publicacao': ['sentença', 'acórdão', 'decisão', 'liminar', 'tutela'],
        'despacho': ['cite-se', 'intime-se', 'defiro', 'indefiro', 'liminar'],
        'sentenca': ['procedente', 'improcedente', 'homologo', 'extinção'],
        'decisao': ['tutela', 'liminar', 'antecipação', 'indefiro', 'defiro'],
        'audiencia': ['conciliação', 'instrução', 'mediação'],
        'citacao': ['citação', 'edital', 'hora certa'],
        'juntada': ['contestação', 'réplica', 'laudo', 'parecer'],
    }

    @staticmethod
    async def analyze_movement(
        movement_text: str,
        case_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analisa e interpreta uma movimentação processual.

        Args:
            movement_text: Texto da movimentação
            case_data: Dados contextuais do caso (opcional)

        Returns:
            Dict com:
            - interpretation: interpretação da movimentação
            - key_points: pontos-chave identificados
            - urgency_level: baixo/medio/alto
            - suggested_actions: lista de ações sugeridas
            - legal_implications: implicações jurídicas
        """
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        case_context = ""
        if case_data:
            case_context = f"""
**Contexto do Caso:**
- Número: {case_data.get('numero_processo', 'N/A')}
- Título: {case_data.get('titulo', 'N/A')}
- Área: {case_data.get('area', 'N/A')}
- Fase atual: {case_data.get('fase_atual', 'N/A')}
"""

        prompt = f"""
Analise esta movimentação processual e forneça uma interpretação jurídica detalhada.

**Movimentação:**
{movement_text[:1000] if movement_text else 'Não informada'}

{case_context}

**Tarefa:**
1. Interprete o significado jurídico da movimentação
2. Identifique 3-5 pontos-chave
3. Avalie o nível de urgência (baixo/médio/alto)
4. Sugira 3-5 ações práticas
5. Explique implicações jurídicas

**Formato de resposta (JSON):**
{{
    "interpretation": "texto da interpretação",
    "key_points": ["ponto 1", "ponto 2", ...],
    "urgency_level": "baixo|medio|alto",
    "suggested_actions": ["ação 1", "ação 2", ...],
    "legal_implications": "texto das implicações"
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
                    'interpretation': result.get('interpretation', ''),
                    'key_points': result.get('key_points', []),
                    'urgency_level': result.get('urgency_level', 'medio'),
                    'suggested_actions': result.get('suggested_actions', []),
                    'legal_implications': result.get('legal_implications', ''),
                }
            else:
                return PushAnalysisService._heuristic_analysis(movement_text, case_data)

        except Exception as e:
            logger.warning(f'Erro na análise IA da movimentação: {e}')
            return PushAnalysisService._heuristic_analysis(movement_text, case_data)

    @staticmethod
    def _heuristic_analysis(
        movement_text: str,
        case_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Análise heurística fallback quando IA não está disponível."""
        text_lower = movement_text.lower() if movement_text else ''

        # Detectar urgência por palavras-chave
        urgency_keywords = ['urgente', 'liminar', 'tutela', 'prisão', 'prisao', 'prazo', 'imediato']
        urgency_level = 'alto' if any(kw in text_lower for kw in urgency_keywords) else 'medio'

        # Pontos-chave básicos
        key_points = []
        if 'sentença' in text_lower or 'sentenca' in text_lower:
            key_points.append('Sentença proferida')
        if 'prazo' in text_lower:
            key_points.append('Prazo processual mencionado')
        if 'intimação' in text_lower or 'intimacao' in text_lower:
            key_points.append('Intimação realizada')

        return {
            'interpretation': movement_text[:200] if movement_text else 'Sem informações',
            'key_points': key_points or ['Movimentação registrada'],
            'urgency_level': urgency_level,
            'suggested_actions': ['Verificar teor completo', 'Acompanhar próximos andamentos'],
            'legal_implications': 'Análise detalhada indisponível no momento.',
        }

    @staticmethod
    async def suggest_actions(
        movement_type: str,
        case_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Sugere próximas ações baseadas no tipo de movimentação e contexto.

        Args:
            movement_type: Tipo de evento (movimentacao, intimacao, etc.)
            case_context: Contexto adicional do caso

        Returns:
            Lista de ações sugeridas com prioridade e descrição
        """
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        context_str = ""
        if case_context:
            context_str = f"""
**Contexto Adicional:**
- Fase: {case_context.get('fase', 'N/A')}
- Últimas ações: {case_context.get('ultimas_acoes', 'N/A')}
- Prazos ativos: {case_context.get('prazos_ativos', 'N/A')}
"""

        base_actions = PushAnalysisService.ACTION_SUGGESTIONS.get(
            movement_type,
            ['Verificar teor do evento', 'Acompanhar andamento']
        )

        prompt = f"""
Sugira ações práticas para um advogado baseado neste evento processual.

**Tipo de Evento:** {movement_type}
{context_str}

**Ações básicas sugeridas:** {', '.join(base_actions)}

**Tarefa:**
1. Priorize as ações (alta/média/baixa prioridade)
2. Adicione estimativa de tempo para cada ação
3. Inclua ações específicas para o contexto

**Formato (JSON array):**
[
    {{
        "action": "descrição da ação",
        "priority": "alta|media|baixa",
        "estimated_time": "15min|1h|1dia",
        "category": "analise|manifestacao|comunicacao|arquivo"
    }}
]
"""

        try:
            llm = UnifiedLLMService.get_service()
            response = await llm.generate_async(prompt, temperature=0.4)

            import json
            import re

            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                result = json.loads(json_match.group())
                return result if isinstance(result, list) else []

        except Exception as e:
            logger.warning(f'Erro ao sugerir ações: {e}')

        # Fallback: retorna ações básicas
        return [
            {'action': action, 'priority': 'media', 'estimated_time': '30min', 'category': 'analise'}
            for action in base_actions[:3]
        ]

    @staticmethod
    async def summarize_publication(publication_text: str) -> str:
        """
        Resume uma publicação do Diário Oficial mantendo informações críticas.

        Args:
            publication_text: Texto completo da publicação

        Returns:
            Resumo conciso da publicação
        """
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        if not publication_text or len(publication_text) < 200:
            return publication_text or 'Publicação sem conteúdo'

        prompt = f"""
Resuma esta publicação do Diário Oficial de forma concisa mas mantendo todas as informações jurídicas críticas.

**Publicação:**
{publication_text[:2000] if len(publication_text) > 2000 else publication_text}

**Instruções:**
1. Mantenha números de processo, prazos, nomes das partes
2. Destaque decisões, intimações e determinações
3. Use linguagem jurídica precisa
4. Limite a 3-5 frases

**Resumo:**
"""

        try:
            llm = UnifiedLLMService.get_service()
            response = await llm.generate_async(prompt, temperature=0.3)
            return response.strip()

        except Exception as e:
            logger.warning(f'Erro ao resumir publicação: {e}')
            return PushAnalysisService._extractive_summary(publication_text)

    @staticmethod
    def _extractive_summary(publication_text: str) -> str:
        """Resumo extrativo fallback."""
        if not publication_text:
            return 'Sem conteúdo'

        # Pegar primeiras frases significativas
        sentences = publication_text.replace('\n', ' ').split('.')
        summary = []
        for sentence in sentences[:3]:
            sentence = sentence.strip()
            if len(sentence) > 20:
                summary.append(sentence)

        return '. '.join(summary)[:300] + '...' if summary else 'Sem conteúdo'

    @staticmethod
    async def classify_relevance(
        movement: Dict[str, Any],
        case_priority: str = 'normal',
    ) -> Dict[str, Any]:
        """
        Classifica a relevância de uma movimentação.

        Args:
            movement: Dados da movimentação (tipo, descrição, etc.)
            case_priority: Prioridade do caso (alta/normal/baixa)

        Returns:
            Dict com:
            - relevance: alta/media/baixa
            - confidence: 0-100
            - reasons: justificativas da classificação
            - score: score numérico 0-100
        """
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        movement_type = movement.get('event_type', 'movimentacao')
        description = movement.get('description', '')

        # Buscar palavras-chave de alta relevância
        high_keywords = PushAnalysisService.HIGH_RELEVANCE_KEYWORDS.get(movement_type, [])
        desc_lower = description.lower() if description else ''
        matched_keywords = [kw for kw in high_keywords if kw in desc_lower]

        prompt = f"""
Classifique a relevância desta movimentação processual para o advogado.

**Dados da Movimentação:**
- Tipo: {movement_type}
- Descrição: {description[:500] if description else 'Não informada'}
- Prioridade do caso: {case_priority}
- Palavras-chave detectadas: {', '.join(matched_keywords) or 'nenhuma'}

**Tarefa:**
1. Classifique relevância como ALTA, MÉDIA ou BAIXA
2. Atribua confiança 0-100%
3. Liste razões para classificação
4. Calcule score 0-100

**Formato (JSON):**
{{
    "relevance": "alta|media|baixa",
    "confidence": 0-100,
    "reasons": ["razão 1", "razão 2", ...],
    "score": 0-100
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
                    'relevance': result.get('relevance', 'media').lower(),
                    'confidence': result.get('confidence', 50),
                    'reasons': result.get('reasons', []),
                    'score': result.get('score', 50),
                }

        except Exception as e:
            logger.warning(f'Erro na classificação de relevância: {e}')

        # Fallback heurístico
        return PushAnalysisService._heuristic_relevance(
            movement_type, description, case_priority, matched_keywords
        )

    @staticmethod
    def _heuristic_relevance(
        movement_type: str,
        description: str,
        case_priority: str,
        matched_keywords: List[str],
    ) -> Dict[str, Any]:
        """Classificação heurística de relevância."""
        score = 50  # Base neutra
        reasons = []

        # Tipo de evento influencia relevância
        high_impact_types = ['sentenca', 'decisao', 'intimacao', 'audiencia']
        if movement_type in high_impact_types:
            score += 20
            reasons.append(f'Tipo de alto impacto: {movement_type}')

        # Palavras-chave de relevância
        if matched_keywords:
            score += 25
            reasons.append(f'Palavras-chave críticas: {", ".join(matched_keywords[:3])}')

        # Prioridade do caso
        if case_priority == 'alta':
            score += 15
            reasons.append('Caso de alta prioridade')

        # Descrição longa = mais detalhes = mais relevante
        if description and len(description) > 100:
            score += 10
            reasons.append('Descrição detalhada')

        # Determinar classificação
        if score >= 80:
            relevance = 'alta'
        elif score >= 55:
            relevance = 'media'
        else:
            relevance = 'baixa'

        return {
            'relevance': relevance,
            'confidence': min(95, max(30, score)),
            'reasons': reasons[:5],
            'score': min(100, max(0, score)),
        }
