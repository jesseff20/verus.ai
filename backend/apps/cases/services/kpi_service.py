"""
Serviço de KPIs Gamificados — cálculo e ranking de advogados.
"""
import logging
from datetime import date
from django.db.models import Sum, Count, Q, F
from django.utils import timezone

logger = logging.getLogger(__name__)


class KPIService:
    """Serviço de KPIs gamificados estilo ADVBOX Taskscore."""

    BADGE_DEFINITIONS = [
        {'id': 'speed_demon', 'name': 'Velocista', 'description': 'Cumpriu 100% dos prazos no período', 'icon': '⚡'},
        {'id': 'closer', 'name': 'Fechador', 'description': 'Ganhou 5+ casos no período', 'icon': '🏆'},
        {'id': 'work_horse', 'name': 'Cavalo de Batalha', 'description': '100+ horas registradas no período', 'icon': '💪'},
        {'id': 'writer', 'name': 'Escritor', 'description': '20+ documentos gerados no período', 'icon': '✍️'},
        {'id': 'negotiator', 'name': 'Negociador', 'description': '3+ acordos no período', 'icon': '🤝'},
        {'id': 'revenue_king', 'name': 'Rei da Receita', 'description': 'Maior receita gerada no período', 'icon': '💰'},
        {'id': 'perfect_month', 'name': 'Mês Perfeito', 'description': 'Zero prazos perdidos + 50+ horas', 'icon': '⭐'},
    ]

    @classmethod
    def calculate_period_scores(cls, period_start: date, period_end: date):
        """Calcula scores para todos os advogados no período."""
        from apps.cases.models import (
            LegalCase, LegalDeadline, CaseTask, TimeEntry, LawyerScore
        )
        from django.contrib.auth import get_user_model
        User = get_user_model()

        lawyers = User.objects.filter(
            role__in=['advogado', 'socio', 'advogado_senior', 'advogado_junior', 'estagiario']
        )

        scores = []
        for lawyer in lawyers:
            # Cases won/lost/settled
            cases = LegalCase.objects.filter(
                advogado_responsavel=lawyer,
                updated_at__date__gte=period_start,
                updated_at__date__lte=period_end,
            )
            cases_won = cases.filter(status='ganho').count()
            cases_lost = cases.filter(status='perdido').count()
            cases_settled = cases.filter(status='acordo').count()

            # Deadlines
            deadlines = LegalDeadline.objects.filter(
                responsavel=lawyer,
                data_prazo__gte=period_start,
                data_prazo__lte=period_end,
            )
            deadlines_met = deadlines.filter(status='concluido').count()
            deadlines_missed = deadlines.filter(status='atrasado').count()

            # Tasks
            tasks_completed = CaseTask.objects.filter(
                responsavel=lawyer,
                status='concluida',
                data_conclusao__gte=period_start,
                data_conclusao__lte=period_end,
            ).count()

            # Hours
            hours_agg = TimeEntry.objects.filter(
                advogado=lawyer,
                date__gte=period_start,
                date__lte=period_end,
            ).aggregate(
                total_hours=Sum('hours'),
                total_value=Sum('total_value'),
            )
            hours_logged = hours_agg['total_hours'] or 0
            revenue = hours_agg['total_value'] or 0

            # Documents generated (from intelligent_assistant)
            from apps.intelligent_assistant.models import GeneratedDocument
            docs_generated = GeneratedDocument.objects.filter(
                session__user=lawyer,
                created_at__date__gte=period_start,
                created_at__date__lte=period_end,
            ).count()

            # Create/update score
            score_obj, created = LawyerScore.objects.update_or_create(
                lawyer=lawyer,
                period_start=period_start,
                period_end=period_end,
                defaults={
                    'cases_won': cases_won,
                    'cases_lost': cases_lost,
                    'cases_settled': cases_settled,
                    'deadlines_met': deadlines_met,
                    'deadlines_missed': deadlines_missed,
                    'tasks_completed': tasks_completed,
                    'hours_logged': hours_logged,
                    'documents_generated': docs_generated,
                    'revenue_generated': revenue,
                }
            )

            # Calculate score
            score_obj.calculate_score()

            # Assign badges
            badges = []
            if deadlines_met > 0 and deadlines_missed == 0:
                badges.append('speed_demon')
            if cases_won >= 5:
                badges.append('closer')
            if hours_logged >= 100:
                badges.append('work_horse')
            if docs_generated >= 20:
                badges.append('writer')
            if cases_settled >= 3:
                badges.append('negotiator')
            if deadlines_missed == 0 and hours_logged >= 50:
                badges.append('perfect_month')

            score_obj.badges = badges
            score_obj.save()
            scores.append(score_obj)

        # Update rankings
        sorted_scores = sorted(scores, key=lambda s: s.total_score, reverse=True)
        for i, score_obj in enumerate(sorted_scores, 1):
            score_obj.rank_position = i
            score_obj.save(update_fields=['rank_position'])

        return sorted_scores

    @classmethod
    def get_leaderboard(cls, period_start: date, period_end: date) -> list:
        """Retorna leaderboard formatado."""
        from apps.cases.models import LawyerScore

        scores = LawyerScore.objects.filter(
            period_start=period_start,
            period_end=period_end,
        ).select_related('lawyer').order_by('rank_position')

        leaderboard = []
        for score in scores:
            badge_details = [
                b for b in cls.BADGE_DEFINITIONS if b['id'] in score.badges
            ]
            leaderboard.append({
                'rank': score.rank_position,
                'lawyer_id': str(score.lawyer.id),
                'lawyer_name': score.lawyer.get_full_name() or score.lawyer.username,
                'total_score': score.total_score,
                'cases_won': score.cases_won,
                'deadlines_met': score.deadlines_met,
                'deadlines_missed': score.deadlines_missed,
                'tasks_completed': score.tasks_completed,
                'hours_logged': float(score.hours_logged),
                'revenue_generated': float(score.revenue_generated),
                'badges': badge_details,
            })

        return leaderboard
