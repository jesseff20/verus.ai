"""
Radar de Precedentes — Análise jurisprudencial com % de sucesso.

Funcionalidades:
  - Análise de jurisprudência por tribunal
  - Cálculo de taxa de sucesso por tese jurídica
  - Identificação de precedentes favoráveis/desfavoráveis
  - Timeline de julgamentos
  - Detecção de tendências jurisprudenciais
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum

from django.db.models import Count, Avg, Q, F, ExpressionWrapper, FloatField
from django.db.models.functions import TruncMonth, TruncYear
from django.utils import timezone

from apps.jurisprudence.models import JurisprudenceResult, JurisprudenceSearch


class PrecedentOutcome(str, Enum):
    """Resultado do precedente."""
    FAVORABLE = 'favorable'      # Favorável ao argumento
    UNFAVORABLE = 'unfavorable'  # Desfavorável
    NEUTRAL = 'neutral'          # Neutro/informativo
    MIXED = 'mixed'             # Resultado misto


class PrecedentWeight(str, Enum):
    """Peso do precedente na hierarquia."""
    BINDING = 'binding'          # Vinculante (Súmula, Repercussão Geral)
    PERSUASIVE = 'persuasive'    # Persuasivo (STJ, STF)
    INFORMATIVE = 'informative'  # Informativo (Tribunais inferiores)


@dataclass
class PrecedentAnalysis:
    """Análise de um precedente individual."""
    id: str
    tribunal: str
    case_number: str
    outcome: PrecedentOutcome
    weight: PrecedentWeight
    relevance_score: float
    summary: str
    judgment_date: Optional[datetime] = None
    relator: Optional[str] = None
    organ: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    citation: str = ''


@dataclass
class TribunalStatistics:
    """Estatísticas por tribunal."""
    tribunal: str
    total_cases: int
    favorable_count: int
    unfavorable_count: int
    success_rate: float  # 0.0 - 1.0
    avg_judgment_time_days: Optional[float] = None
    recent_trend: str = 'stable'  # 'improving', 'worsening', 'stable'


@dataclass
class ThesisStatistics:
    """Estatísticas por tese jurídica."""
    thesis: str
    total_cases: int
    favorable_count: int
    success_rate: float
    tribunals: Dict[str, int] = field(default_factory=dict)
    recent_judgments: List[PrecedentAnalysis] = field(default_factory=list)


@dataclass
class RadarReport:
    """Relatório completo do Radar de Precedentes."""
    query: str
    total_analyzed: int
    overall_success_rate: float
    tribunal_stats: List[TribunalStatistics]
    thesis_stats: List[ThesisStatistics]
    timeline: List[Dict[str, Any]]
    key_precedents: List[PrecedentAnalysis]
    recommendations: List[str]
    generated_at: datetime = field(default_factory=timezone.now)


class PrecedentRadarService:
    """
    Serviço de análise de precedentes jurisprudenciais.

    Analisa jurisprudência para identificar:
    1. Taxa de sucesso por tribunal
    2. Tendências temporais
    3. Precedentes chave (favoráveis e desfavoráveis)
    4. Recomendações estratégicas
    """

    # Mapeamento de tribunais para peso hierárquico
    TRIBUNAL_WEIGHTS = {
        'STF': PrecedentWeight.BINDING,
        'STJ': PrecedentWeight.PERSUASIVE,
        'TST': PrecedentWeight.PERSUASIVE,
        'TSE': PrecedentWeight.PERSUASIVE,
        'TRF': PrecedentWeight.INFORMATIVE,
        'TJ': PrecedentWeight.INFORMATIVE,
    }

    # Palavras-chave que indicam resultado favorável
    FAVORABLE_KEYWORDS = [
        'procedente', 'improcedente', 'provimento', 'desprovimento',
        'ganhou causa', 'razão', 'direito', 'amparo legal',
        'acolhido', 'deferido', 'concedido', 'reconhecido',
    ]

    # Palavras-chave que indicam resultado desfavorável
    UNFAVORABLE_KEYWORDS = [
        'improcedente', 'indeferido', 'negado', 'rejeitado',
        'sem razão', 'ausência de direito', 'não amparado',
        'desacolhido', 'prejudicado', 'extinto',
    ]

    def analyze_precedents(
        self,
        query: str,
        specialty: Optional[str] = None,
        date_range: Optional[tuple] = None,
        tribunals: Optional[List[str]] = None,
        user_id: Optional[int] = None,
    ) -> RadarReport:
        """
        Analisa precedentes jurisprudenciais.

        Args:
            query: Termo de busca/tese jurídica
            specialty: Especialidade jurídica (ex: CIV, PEN, TRB)
            date_range: Tupla (start_date, end_date) para filtro temporal
            tribunals: Lista de tribunais para filtrar
            user_id: ID do usuário para buscar histórico pessoal

        Returns:
            RadarReport com análise completa
        """
        # Construir queryset base
        queryset = self._build_queryset(
            query, specialty, date_range, tribunals, user_id
        )

        # Executar análises
        tribunal_stats = self._analyze_by_tribunal(queryset)
        thesis_stats = self._analyze_by_thesis(queryset, query)
        timeline = self._build_timeline(queryset)
        key_precedents = self._identify_key_precedents(queryset)

        # Calcular taxa de sucesso geral
        total = queryset.count()
        favorable = self._count_favorable(queryset)
        overall_success_rate = favorable / total if total > 0 else 0.0

        # Gerar recomendações
        recommendations = self._generate_recommendations(
            tribunal_stats, thesis_stats, key_precedents, overall_success_rate
        )

        return RadarReport(
            query=query,
            total_analyzed=total,
            overall_success_rate=overall_success_rate,
            tribunal_stats=tribunal_stats,
            thesis_stats=thesis_stats,
            timeline=timeline,
            key_precedents=key_precedents,
            recommendations=recommendations,
        )

    def _build_queryset(
        self,
        query: str,
        specialty: Optional[str],
        date_range: Optional[tuple],
        tribunals: Optional[List[str]],
        user_id: Optional[int],
    ):
        """Constrói queryset filtrado para análise."""
        queryset = JurisprudenceResult.objects.all()

        # Filtro por usuário (histórico pessoal)
        if user_id:
            queryset = queryset.filter(search__user_id=user_id)

        # Filtro por query (busca no summary)
        if query:
            queryset = queryset.filter(
                Q(summary__icontains=query) |
                Q(full_text_url__icontains=query) |
                Q(case_number__icontains=query)
            )

        # Filtro por especialidade
        if specialty:
            queryset = queryset.filter(search__specialty__code=specialty)

        # Filtro temporal
        if date_range:
            start_date, end_date = date_range
            queryset = queryset.filter(
                search__created_at__range=[start_date, end_date]
            )

        # Filtro por tribunais
        if tribunals:
            queryset = queryset.filter(tribunal__in=tribunals)

        return queryset.order_by('-relevance_score', '-judgment_date')

    def _analyze_by_tribunal(self, queryset) -> List[TribunalStatistics]:
        """Analisa estatísticas por tribunal."""
        stats = []

        # Agrupar por tribunal
        tribunals = queryset.values('tribunal').annotate(
            total=Count('id'),
            avg_score=Avg('relevance_score'),
        ).order_by('-total')

        for tribunal_data in tribunals:
            tribunal = tribunal_data['tribunal']
            tribunal_qs = queryset.filter(tribunal=tribunal)

            # Contar favoráveis e desfavoráveis
            favorable_count = self._count_favorable(tribunal_qs)
            unfavorable_count = self._count_unfavorable(tribunal_qs)

            # Calcular success rate
            total = tribunal_data['total']
            success_rate = favorable_count / total if total > 0 else 0.0

            # Determinar tendência recente
            recent_trend = self._calculate_trend(tribunal_qs)

            stats.append(TribunalStatistics(
                tribunal=tribunal,
                total_cases=total,
                favorable_count=favorable_count,
                unfavorable_count=unfavorable_count,
                success_rate=success_rate,
                recent_trend=recent_trend,
            ))

        return stats

    def _analyze_by_thesis(
        self,
        queryset,
        query: str,
    ) -> List[ThesisStatistics]:
        """Analisa estatísticas por tese jurídica."""
        # Para MVP, tratamos a query como uma única tese
        # Em produção, isso seria expandido para múltiplas teses

        favorable_count = self._count_favorable(queryset)
        total = queryset.count()

        # Distribuição por tribunal
        tribunal_dist = {}
        for item in queryset.values('tribunal').annotate(count=Count('id')):
            tribunal_dist[item['tribunal']] = item['count']

        # Julgamentos recentes
        recent = queryset.order_by('-judgment_date')[:5]
        recent_judgments = [
            self._result_to_precedent(r) for r in recent
        ]

        return [ThesisStatistics(
            thesis=query,
            total_cases=total,
            favorable_count=favorable_count,
            success_rate=favorable_count / total if total > 0 else 0.0,
            tribunals=tribunal_dist,
            recent_judgments=recent_judgments,
        )]

    def _build_timeline(self, queryset) -> List[Dict[str, Any]]:
        """Constrói timeline de julgamentos."""
        # Agrupar por mês/ano
        timeline = queryset.filter(
            judgment_date__isnull=False
        ).annotate(
            year=TruncYear('judgment_date'),
            month=TruncMonth('judgment_date'),
        ).values(
            'year', 'month'
        ).annotate(
            count=Count('id'),
            favorable=Count('id', filter=Q(
                summary__icontains='procedente'
            )),
            avg_score=Avg('relevance_score'),
        ).order_by('year', 'month')

        return [
            {
                'date': f"{item['year'].strftime('%Y')}-{item['month'].strftime('%m')}",
                'count': item['count'],
                'favorable': item['favorable'],
                'avg_score': float(item['avg_score']) if item['avg_score'] else 0,
            }
            for item in timeline
        ]

    def _identify_key_precedents(
        self,
        queryset,
        limit: int = 10,
    ) -> List[PrecedentAnalysis]:
        """Identifica precedentes chave (mais relevantes)."""
        key_precedents = []

        # Selecionar mais relevantes
        for result in queryset[:limit]:
            precedent = self._result_to_precedent(result)
            key_precedents.append(precedent)

        return key_precedents

    def _result_to_precedent(
        self,
        result: JurisprudenceResult,
    ) -> PrecedentAnalysis:
        """Converte JurisprudenceResult em PrecedentAnalysis."""
        # Determinar outcome
        outcome = self._determine_outcome(result.summary)

        # Determinar weight baseado no tribunal
        weight = PrecedentWeight.INFORMATIVE
        for tribunal_prefix, w in self.TRIBUNAL_WEIGHTS.items():
            if result.tribunal.startswith(tribunal_prefix):
                weight = w
                break

        # Extrair keywords
        keywords = self._extract_keywords(result.summary)

        # Construir citação
        citation = self._build_citation(result)

        return PrecedentAnalysis(
            id=str(result.id),
            tribunal=result.tribunal,
            case_number=result.case_number or 'Sem número',
            outcome=outcome,
            weight=weight,
            relevance_score=result.relevance_score,
            summary=result.summary[:500] if len(result.summary) > 500 else result.summary,
            judgment_date=result.judgment_date,
            relator=result.relator,
            organ=result.organ,
            keywords=keywords,
            citation=citation,
        )

    def _count_favorable(self, queryset) -> int:
        """Conta resultados favoráveis."""
        count = 0
        for item in queryset:
            if self._determine_outcome(item.summary) == PrecedentOutcome.FAVORABLE:
                count += 1
        return count

    def _count_unfavorable(self, queryset) -> int:
        """Conta resultados desfavoráveis."""
        count = 0
        for item in queryset:
            if self._determine_outcome(item.summary) == PrecedentOutcome.UNFAVORABLE:
                count += 1
        return count

    def _determine_outcome(self, summary: str) -> PrecedentOutcome:
        """Determina se resultado é favorável, desfavorável ou neutro."""
        summary_lower = summary.lower()

        favorable_score = 0
        unfavorable_score = 0

        # Contar palavras favoráveis
        for keyword in self.FAVORABLE_KEYWORDS:
            if keyword in summary_lower:
                favorable_score += 1

        # Contar palavras desfavoráveis
        for keyword in self.UNFAVORABLE_KEYWORDS:
            if keyword in summary_lower:
                unfavorable_score += 1

        # Determinar outcome
        if favorable_score > unfavorable_score:
            return PrecedentOutcome.FAVORABLE
        elif unfavorable_score > favorable_score:
            return PrecedentOutcome.UNFAVORABLE
        elif favorable_score > 0 or unfavorable_score > 0:
            return PrecedentOutcome.MIXED
        else:
            return PrecedentOutcome.NEUTRAL

    def _calculate_trend(self, queryset) -> str:
        """Calcula tendência recente do tribunal."""
        now = timezone.now()

        # Últimos 3 meses
        recent = queryset.filter(
            search__created_at__gte=now - timedelta(days=90)
        )

        # 3 meses anteriores
        previous = queryset.filter(
            search__created_at__gte=now - timedelta(days=180),
            search__created_at__lt=now - timedelta(days=90)
        )

        if recent.count() == 0:
            return 'stable'

        recent_rate = self._count_favorable(recent) / recent.count() if recent.count() > 0 else 0
        previous_rate = self._count_favorable(previous) / previous.count() if previous.count() > 0 else 0

        diff = recent_rate - previous_rate

        if diff > 0.1:
            return 'improving'
        elif diff < -0.1:
            return 'worsening'
        else:
            return 'stable'

    def _extract_keywords(self, summary: str) -> List[str]:
        """Extrai palavras-chave do resumo."""
        # Palavras-chave jurídicas comuns
        legal_keywords = [
            'responsabilidade civil', 'dano moral', 'dano material',
            'boa-fé', 'função social', 'coisa julgada',
            'prescrição', 'decadência', 'liminar',
            'tutela antecipada', 'recurso especial', 'recurso extraordinário',
        ]

        keywords = []
        summary_lower = summary.lower()

        for keyword in legal_keywords:
            if keyword in summary_lower:
                keywords.append(keyword)

        return keywords[:5]  # Limitar a 5 keywords

    def _build_citation(self, result: JurisprudenceResult) -> str:
        """Constrói citação formatada do precedente."""
        parts = [result.tribunal]

        if result.case_number:
            parts.append(result.case_number)

        if result.relator:
            parts.append(f'Rel. {result.relator}')

        if result.judgment_date:
            parts.append(result.judgment_date.strftime('%d/%m/%Y'))

        if result.organ:
            parts.append(result.organ)

        return ', '.join(parts)

    def _generate_recommendations(
        self,
        tribunal_stats: List[TribunalStatistics],
        thesis_stats: List[ThesisStatistics],
        key_precedents: List[PrecedentAnalysis],
        overall_success_rate: float,
    ) -> List[str]:
        """Gera recomendações estratégicas baseadas na análise."""
        recommendations = []

        # Recomendação baseada na taxa geral
        if overall_success_rate >= 0.7:
            recommendations.append(
                f'Alta taxa de sucesso ({overall_success_rate:.0%}). '
                f'Tese jurídica bem consolidada nos tribunais.'
            )
        elif overall_success_rate >= 0.4:
            recommendations.append(
                f'Taxa de sucesso moderada ({overall_success_rate:.0%}). '
                f'Recomenda-se fortalecer argumentação com precedentes específicos.'
            )
        else:
            recommendations.append(
                f'Baixa taxa de sucesso ({overall_success_rate:.0%}). '
                f'Considere revisar a tese ou buscar alternativas jurídicas.'
            )

        # Recomendação por tribunal
        best_tribunal = max(
            tribunal_stats,
            key=lambda s: s.success_rate if s.total_cases >= 3 else 0,
            default=None
        )

        if best_tribunal and best_tribunal.success_rate >= 0.6:
            recommendations.append(
                f'Melhor tribunal: {best_tribunal.tribunal} '
                f'({best_tribunal.success_rate:.0%} de sucesso). '
                f'Priorize este foro quando possível.'
            )

        # Recomendação de tendência
        worsening_tribunals = [
            s for s in tribunal_stats if s.recent_trend == 'worsening'
        ]

        if worsening_tribunals:
            names = ', '.join([s.tribunal for s in worsening_tribunals])
            recommendations.append(
                f'Atenção: Tendência desfavorável em {names}. '
                f'Monitore julgamentos recentes.'
            )

        # Precedentes vinculantes
        binding_precedents = [
            p for p in key_precedents if p.weight == PrecedentWeight.BINDING
        ]

        if binding_precedents:
            recommendations.append(
                f'{len(binding_precedents)} precedente(s) vinculante(s) identificado(s). '
                f'Destaque estes precedentes na petição.'
            )

        return recommendations
