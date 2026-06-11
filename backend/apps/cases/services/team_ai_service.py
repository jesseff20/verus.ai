"""
Serviço de IA para sugestão de alocação de equipes em casos jurídicos.
Integração com Copilot para:
- Sugestão de equipes baseada em especialidade e carga
- Balanceamento de carga de trabalho
- Match por especialidade
- Previsão de disponibilidade
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from django.db.models import Count, Q
from django.utils import timezone

logger = logging.getLogger(__name__)


class TeamAIService:
    """Serviço de IA para análise e sugestão de alocação de equipes."""

    @staticmethod
    async def suggest_allocation(
        case_data: dict,
        available_teams: list,
        user_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Sugere equipes para alocação em um caso jurídico.

        Args:
            case_data: Dados do caso (especialidade, complexidade, valor_causa, etc.)
            available_teams: Lista de equipes disponíveis
            user_id: ID do usuário solicitante (opcional)

        Returns:
            Lista de sugestões ordenadas por score:
            - team_id, team_name, score (0-100), reasons, specialty_match, availability
        """
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        # Preparar dados para análise
        case_summary = f"""
- Especialidade: {case_data.get('specialty', 'N/A')}
- Complexidade: {case_data.get('complexity', 'N/A')}
- Valor da causa: R$ {case_data.get('valor_causa', 0)}
- Urgência: {'Sim' if case_data.get('urgency') else 'Não'}
- Fase atual: {case_data.get('fase', 'N/A')}
"""

        # Preparar resumo das equipes
        teams_summary = []
        for team in available_teams:
            teams_summary.append({
                'id': str(team.get('id', '')),
                'name': team.get('name', ''),
                'specialty': team.get('specialty', ''),
                'members_count': team.get('members_count', 0),
                'active_cases': team.get('active_cases', 0),
            })

        prompt = f"""
Analise as equipes disponíveis e sugira as melhores para alocação neste caso jurídico.

**Dados do Caso:**
{case_summary}

**Equipes Disponíveis:**
{teams_summary}

**Critérios de análise:**
1. Match de especialidade (prioridade máxima)
2. Carga atual de casos (equipes menos carregadas preferidas)
3. Número de membros (casos complexos preferem equipes maiores)
4. Urgência (equipes com menor carga para casos urgentes)

**Tarefa:**
1. Classifique cada equipe com score 0-100
2. Liste razões para cada sugestão
3. Ordene por score decrescente

**Formato (JSON):**
{{
    "suggestions": [
        {{
            "team_id": "uuid",
            "team_name": "nome",
            "score": 85,
            "reasons": ["razão 1", "razão 2"],
            "specialty_match": true/false,
            "availability": "high/medium/low"
        }}
    ],
    "top_recommendation": "uuid da melhor equipe",
    "analysis": "explicação geral"
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
                return result.get('suggestions', [])
        except Exception as e:
            logger.warning(f'Erro na sugestão de alocação: {e}')

        # Fallback heurístico
        return TeamAIService._heuristic_suggestion(case_data, available_teams)

    @staticmethod
    def _heuristic_suggestion(
        case_data: dict,
        available_teams: list,
    ) -> List[Dict[str, Any]]:
        """Sugestão heurística fallback quando IA não está disponível."""
        suggestions = []
        case_specialty = case_data.get('specialty', '').lower()
        case_complexity = case_data.get('complexity', 'media').lower()
        is_urgent = case_data.get('urgency', False)

        for team in available_teams:
            score = 50  # Começa neutro
            reasons = []

            # Match de especialidade (+40 pontos)
            team_specialty = team.get('specialty', '').lower()
            if team_specialty == case_specialty:
                score += 40
                reasons.append('Especialidade compatível')
            elif team_specialty in ['geral', 'outros', '']:
                score += 15
                reasons.append('Equipe generalista')
            else:
                score -= 20
                reasons.append('Especialidade diferente')

            # Carga de casos (-3 pontos por caso ativo, max -30)
            active_cases = team.get('active_cases', 0)
            case_penalty = min(30, active_cases * 3)
            score -= case_penalty
            if active_cases <= 2:
                reasons.append('Baixa carga de casos')
            elif active_cases <= 5:
                reasons.append('Carga moderada')
            else:
                reasons.append(f'Carga alta ({active_cases} casos)')

            # Tamanho da equipe (+2 pontos por membro, max +20)
            members_count = team.get('members_count', 1)
            member_bonus = min(20, members_count * 2)
            score += member_bonus
            if members_count >= 5:
                reasons.append('Equipe grande')
            elif members_count >= 3:
                reasons.append('Equipe média')
            else:
                reasons.append('Equipe pequena')

            # Complexidade do caso
            if case_complexity in ['alta', 'complexo']:
                if members_count >= 4:
                    score += 10
                    reasons.append('Equipe adequada para caso complexo')
            elif case_complexity in ['baixa', 'simples']:
                if members_count <= 3:
                    score += 5
                    reasons.append('Equipe adequada para caso simples')

            # Urgência
            if is_urgent and active_cases <= 2:
                score += 15
                reasons.append('Disponível para caso urgente')

            # Normalizar score
            score = min(95, max(10, score))

            # Determinar disponibilidade
            if active_cases <= 2:
                availability = 'high'
            elif active_cases <= 5:
                availability = 'medium'
            else:
                availability = 'low'

            suggestions.append({
                'team_id': str(team.get('id', '')),
                'team_name': team.get('name', ''),
                'score': score,
                'reasons': reasons[:4],
                'specialty_match': team_specialty == case_specialty,
                'availability': availability,
            })

        # Ordenar por score decrescente
        suggestions.sort(key=lambda x: x['score'], reverse=True)

        return suggestions

    @staticmethod
    async def balance_workload(
        teams: list,
        cases: Optional[list] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Analisa balanceamento de carga de trabalho entre equipes.

        Args:
            teams: Lista de equipes com dados de casos ativos
            cases: Lista de casos para distribuição (opcional)
            user_id: ID do usuário (opcional)

        Returns:
            Dict com:
            - balance_score: 0-100 (100 = perfeitamente balanceado)
            - team_loads: carga por equipe
            - overloaded: equipes sobrecarregadas
            - underloaded: equipes com capacidade ociosa
            - recommendations: sugestões de redistribuição
        """
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        # Preparar dados
        teams_data = []
        total_cases = 0
        for team in teams:
            cases_count = team.get('active_cases', 0)
            total_cases += cases_count
            teams_data.append({
                'id': str(team.get('id', '')),
                'name': team.get('name', ''),
                'members_count': team.get('members_count', 1),
                'active_cases': cases_count,
            })

        avg_cases = total_cases / len(teams) if teams else 0

        prompt = f"""
Analise o balanceamento de carga de trabalho entre as equipes jurídicas.

**Equipes e Carga Atual:**
{teams_data}

**Média de casos por equipe:** {avg_cases:.1f}
**Total de casos distribuídos:** {total_cases}

**Tarefa:**
1. Calcule score de balanceamento (0-100)
2. Identifique equipes sobrecarregadas (>150% da média)
3. Identifique equipes com capacidade ociosa (<50% da média)
4. Sugira redistribuições se necessário

**Formato (JSON):**
{{
    "balance_score": 0-100,
    "team_loads": [{{"team_id": "...", "load_percentage": 0-200}}],
    "overloaded": ["team_id1", "team_id2"],
    "underloaded": ["team_id3"],
    "recommendations": ["sugestão 1", "sugestão 2"],
    "analysis": "explicação"
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
                return result
        except Exception as e:
            logger.warning(f'Erro na análise de balanceamento: {e}')

        # Fallback heurístico
        return TeamAIService._heuristic_balance(teams_data, avg_cases)

    @staticmethod
    def _heuristic_balance(
        teams_data: list,
        avg_cases: float,
    ) -> Dict[str, Any]:
        """Análise heurística de balanceamento."""
        if not teams_data or avg_cases == 0:
            return {
                'balance_score': 100,
                'team_loads': [],
                'overloaded': [],
                'underloaded': [],
                'recommendations': ['Sem dados suficientes para análise'],
                'analysis': 'Sem equipes ou casos para analisar.',
            }

        team_loads = []
        overloaded = []
        underloaded = []
        variance = 0

        for team in teams_data:
            load_pct = (team['active_cases'] / avg_cases) * 100 if avg_cases > 0 else 0
            team_loads.append({
                'team_id': team['id'],
                'team_name': team['name'],
                'load_percentage': round(load_pct, 1),
                'active_cases': team['active_cases'],
            })

            # Sobrecarregado (>150% da média)
            if load_pct > 150:
                overloaded.append(team['id'])
            # Subcarregado (<50% da média)
            elif load_pct < 50:
                underloaded.append(team['id'])

            # Calcular variância
            variance += (load_pct - 100) ** 2

        # Score de balanceamento (100 = perfeito, diminui com variância)
        std_dev = (variance / len(teams_data)) ** 0.5
        balance_score = max(0, min(100, 100 - std_dev))

        # Gerar recomendações
        recommendations = []
        if overloaded and underloaded:
            recommendations.append(
                f'Redistribuir casos das equipes {", ".join(overloaded)} '
                f'para {", ".join(underloaded)}'
            )
        elif overloaded:
            recommendations.append(
                f'Equipes sobrecarregadas: {", ".join(overloaded)}. '
                'Considerar nova contratação ou redistribuição.'
            )
        elif underloaded:
            recommendations.append(
                f'Equipes com capacidade ociosa: {", ".join(underloaded)}. '
                'Atribuir mais casos ou consolidar equipes.'
            )

        if balance_score >= 80:
            recommendations.append('Balanceamento geral está bom.')
        elif balance_score >= 60:
            recommendations.append('Balanceamento aceitável, mas pode melhorar.')
        else:
            recommendations.append('Balanceamento crítico - ação recomendada.')

        return {
            'balance_score': round(balance_score, 1),
            'team_loads': team_loads,
            'overloaded': overloaded,
            'underloaded': underloaded,
            'recommendations': recommendations,
            'analysis': f'Score {balance_score:.1f}% indica balanceamento '
                       f'{"bom" if balance_score >= 80 else "regular" if balance_score >= 60 else "crítico"}.',
        }

    @staticmethod
    def match_specialty(
        case_specialty: str,
        teams: list,
        include_related: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Faz match de equipes por especialidade com o caso.

        Args:
            case_specialty: Especialidade do caso (civel, criminal, trabalhista, etc.)
            teams: Lista de equipes
            include_related: Incluir especialidades relacionadas

        Returns:
            Lista de equipes ordenadas por relevância
        """
        # Mapeamento de especialidades relacionadas
        related_specialties = {
            'civel': ['familia', 'empresarial', 'previdenciario'],
            'criminal': [],
            'trabalhista': ['previdenciario'],
            'tributario': ['administrativo', 'empresarial'],
            'familia': ['civel', 'previdenciario'],
            'empresarial': ['civel', 'tributario'],
            'previdenciario': ['trabalhista', 'familia'],
            'administrativo': ['tributario', 'civel'],
        }

        case_specialty_lower = case_specialty.lower() if case_specialty else ''
        related = related_specialties.get(case_specialty_lower, []) if include_related else []

        matches = []
        for team in teams:
            team_specialty = team.get('specialty', '').lower()
            members_count = team.get('members_count', 1)
            active_cases = team.get('active_cases', 0)

            # Determinar tipo de match
            if team_specialty == case_specialty_lower:
                match_type = 'exact'
                score = 100
            elif team_specialty in related:
                match_type = 'related'
                score = 60
            elif team_specialty in ['geral', 'outros', '']:
                match_type = 'general'
                score = 30
            else:
                match_type = 'none'
                score = 10

            # Ajustar score por disponibilidade
            availability_score = max(0, 100 - (active_cases * 10))
            score = (score * 0.7) + (availability_score * 0.3)

            matches.append({
                'team_id': str(team.get('id', '')),
                'team_name': team.get('name', ''),
                'team_specialty': team_specialty,
                'match_type': match_type,
                'score': round(score, 1),
                'members_count': members_count,
                'active_cases': active_cases,
                'availability': 'high' if active_cases <= 2 else 'medium' if active_cases <= 5 else 'low',
            })

        # Ordenar por score
        matches.sort(key=lambda x: x['score'], reverse=True)

        return matches

    @staticmethod
    async def predict_availability(
        team_id: str,
        urgent_case: bool = False,
        case_data: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """
        Prevê disponibilidade da equipe para novo caso.

        Args:
            team_id: ID da equipe
            urgent_case: Se é caso urgente
            case_data: Dados adicionais do caso

        Returns:
            Dict com:
            - available: bool
            - availability_score: 0-100
            - estimated_capacity: capacidade estimada
            - factors: fatores considerados
            - recommendation: recomendação
        """
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService
        from apps.accounts.models import Team, TeamAssignment

        # Buscar dados da equipe
        try:
            team = Team.objects.filter(id=team_id).prefetch_related('members', 'assignments').first()
            if not team:
                return {
                    'available': False,
                    'availability_score': 0,
                    'error': 'Equipe não encontrada',
                }

            active_assignments = team.assignments.filter(
                case__status__in=['ativo', 'aguardando', 'suspenso']
            ).count()
            members_count = team.members.count() or 1

        except Exception as e:
            logger.error(f'Erro ao buscar dados da equipe: {e}')
            return {
                'available': False,
                'availability_score': 0,
                'error': str(e),
            }

        # Dados para análise
        team_data = {
            'name': team.name,
            'members_count': members_count,
            'active_cases': active_assignments,
            'specialty': team.specialty,
        }

        prompt = f"""
Preveja a disponibilidade desta equipe para assumir um novo caso.

**Dados da Equipe:**
- Nome: {team.name}
- Membros: {members_count}
- Casos ativos: {active_assignments}
- Especialidade: {team.specialty or 'Não definida'}

**Novo Caso:**
- Urgente: {'Sim' if urgent_case else 'Não'}
- Dados adicionais: {case_data or 'Nenhum'}

**Tarefa:**
1. Calcule score de disponibilidade (0-100)
2. Determine se está disponível
3. Liste fatores considerados
4. Dê recomendação clara

**Formato (JSON):**
{{
    "available": true/false,
    "availability_score": 0-100,
    "estimated_capacity": "baixa/media/alta",
    "factors": ["fator 1", "fator 2"],
    "recommendation": "texto",
    "estimated_response_time": "imediato/24h/48h/semana"
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
                return result
        except Exception as e:
            logger.warning(f'Erro na previsão de disponibilidade: {e}')

        # Fallback heurístico
        return TeamAIService._heuristic_availability(
            team_data, urgent_case
        )

    @staticmethod
    def _heuristic_availability(
        team_data: dict,
        urgent_case: bool,
    ) -> Dict[str, Any]:
        """Previsão heurística de disponibilidade."""
        members_count = team_data.get('members_count', 1)
        active_cases = team_data.get('active_cases', 0)

        # Casos por membro
        cases_per_member = active_cases / members_count if members_count > 0 else 999

        # Score base (100 - penalidade por caso)
        base_score = max(0, 100 - (active_cases * 10))

        # Ajustar por membro
        if cases_per_member < 1:
            base_score = min(100, base_score + 20)
        elif cases_per_member > 3:
            base_score = max(0, base_score - 20)

        # Caso urgente reduz threshold
        if urgent_case:
            available = cases_per_member < 2
            recommendation = (
                'Equipe disponível para caso urgente.' if available
                else 'Equipe sobrecarregada para caso urgente. Considerar outra equipe.'
            )
            response_time = 'imediato' if available else 'não recomendado'
        else:
            available = cases_per_member < 4
            recommendation = (
                'Equipe disponível para novo caso.' if available
                else 'Equipe com carga cheia. Aguardar liberação ou redistribuir.'
            )
            response_time = (
                'imediato' if cases_per_member < 1
                else '24h' if cases_per_member < 2
                else '48h' if cases_per_member < 3
                else 'semana'
            )

        # Determinar capacidade estimada
        if cases_per_member < 1:
            capacity = 'alta'
        elif cases_per_member < 2:
            capacity = 'media'
        elif cases_per_member < 3:
            capacity = 'baixa'
        else:
            capacity = 'critica'

        factors = [
            f'{active_cases} casos ativos',
            f'{members_count} membros',
            f'{cases_per_member:.1f} casos/membro',
        ]

        return {
            'available': available,
            'availability_score': round(base_score, 1),
            'estimated_capacity': capacity,
            'factors': factors,
            'recommendation': recommendation,
            'estimated_response_time': response_time,
        }
