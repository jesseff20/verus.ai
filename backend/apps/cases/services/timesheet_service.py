"""
Serviço de Timesheet — relatórios e cálculos de horas.
"""
import logging
from decimal import Decimal
from datetime import date, timedelta
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone

logger = logging.getLogger(__name__)


class TimesheetService:
    """Serviço para cálculos e relatórios de timesheet."""

    @staticmethod
    def monthly_report(lawyer_id, year: int, month: int) -> dict:
        """Relatório mensal de horas por advogado."""
        from apps.cases.models import TimeEntry

        entries = TimeEntry.objects.filter(
            advogado_id=lawyer_id,
            date__year=year,
            date__month=month,
        )

        summary = entries.aggregate(
            total_hours=Sum('hours'),
            billable_hours=Sum('hours', filter=Q(billing_type='billable')),
            non_billable_hours=Sum('hours', filter=Q(billing_type='non_billable')),
            pro_bono_hours=Sum('hours', filter=Q(billing_type='pro_bono')),
            total_value=Sum('total_value', filter=Q(billing_type='billable')),
            entries_count=Count('id'),
            avg_hourly_rate=Avg('hourly_rate', filter=Q(billing_type='billable')),
        )

        # By case breakdown
        by_case = entries.values(
            'caso__id', 'caso__titulo', 'caso__numero_processo'
        ).annotate(
            hours=Sum('hours'),
            value=Sum('total_value'),
            entries=Count('id'),
        ).order_by('-hours')

        # By day breakdown
        by_day = entries.values('date').annotate(
            hours=Sum('hours'),
            entries=Count('id'),
        ).order_by('date')

        return {
            'lawyer_id': str(lawyer_id),
            'year': year,
            'month': month,
            'summary': {
                'total_hours': float(summary['total_hours'] or 0),
                'billable_hours': float(summary['billable_hours'] or 0),
                'non_billable_hours': float(summary['non_billable_hours'] or 0),
                'pro_bono_hours': float(summary['pro_bono_hours'] or 0),
                'total_value': float(summary['total_value'] or 0),
                'entries_count': summary['entries_count'] or 0,
                'avg_hourly_rate': float(summary['avg_hourly_rate'] or 0),
                'utilization_rate': round(
                    float(summary['billable_hours'] or 0) / float(summary['total_hours'] or 1) * 100, 1
                ),
            },
            'by_case': list(by_case),
            'by_day': list(by_day),
        }

    @staticmethod
    def calculate_case_honorarios(case_id) -> dict:
        """Calcula honorários acumulados para um caso baseado nas horas registradas."""
        from apps.cases.models import TimeEntry

        entries = TimeEntry.objects.filter(
            caso_id=case_id,
            billing_type='billable',
        )

        result = entries.aggregate(
            total_hours=Sum('hours'),
            total_value=Sum('total_value'),
            approved_value=Sum('total_value', filter=Q(is_approved=True)),
            pending_value=Sum('total_value', filter=Q(is_approved=False)),
        )

        return {
            'case_id': str(case_id),
            'total_billable_hours': float(result['total_hours'] or 0),
            'total_value': float(result['total_value'] or 0),
            'approved_value': float(result['approved_value'] or 0),
            'pending_approval_value': float(result['pending_value'] or 0),
        }

    @staticmethod
    def ranking(period_start: date, period_end: date) -> list:
        """Ranking de advogados por horas faturáveis no período."""
        from apps.cases.models import TimeEntry

        ranking = TimeEntry.objects.filter(
            date__gte=period_start,
            date__lte=period_end,
            billing_type='billable',
        ).values(
            'advogado__id', 'advogado__first_name', 'advogado__last_name',
        ).annotate(
            total_hours=Sum('hours'),
            total_value=Sum('total_value'),
            cases_count=Count('caso', distinct=True),
        ).order_by('-total_hours')

        return list(ranking)
