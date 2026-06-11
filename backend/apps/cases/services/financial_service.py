"""
Serviço financeiro — agregações para o Dashboard Financeiro.
"""
from datetime import date
from decimal import Decimal

from django.db.models import Sum, Q, F
from django.utils import timezone

from apps.cases.models import MovimentacaoFinanceira


class FinancialService:
    """Agregações financeiras sobre MovimentacaoFinanceira."""

    @staticmethod
    def revenue_by_period(start: date, end: date) -> list[dict]:
        """Receitas (honorários pagos) agrupadas por mês no período."""
        qs = (
            MovimentacaoFinanceira.objects
            .filter(tipo='honorario', status='pago')
            .filter(data_pagamento__gte=start, data_pagamento__lte=end)
            .extra(select={'month': "TO_CHAR(data_pagamento, 'YYYY-MM')"})
            .values('month')
            .annotate(total=Sum('valor'))
            .order_by('month')
        )
        return list(qs)

    @staticmethod
    def expenses_by_period(start: date, end: date) -> list[dict]:
        """Despesas agrupadas por mês no período."""
        qs = (
            MovimentacaoFinanceira.objects
            .filter(tipo__in=['despesa', 'custas', 'pericia'], status='pago')
            .filter(data_pagamento__gte=start, data_pagamento__lte=end)
            .extra(select={'month': "TO_CHAR(data_pagamento, 'YYYY-MM')"})
            .values('month')
            .annotate(total=Sum('valor'))
            .order_by('month')
        )
        return list(qs)

    @staticmethod
    def revenue_by_client(start: date, end: date) -> list[dict]:
        """Receitas agrupadas por cliente."""
        qs = (
            MovimentacaoFinanceira.objects
            .filter(tipo='honorario', status='pago')
            .filter(data_pagamento__gte=start, data_pagamento__lte=end)
            .values(client_name=F('caso__cliente_nome'))
            .annotate(total=Sum('valor'))
            .order_by('-total')
        )
        return list(qs)

    @staticmethod
    def revenue_by_lawyer(start: date, end: date) -> list[dict]:
        """Receitas agrupadas por advogado responsavel."""
        qs = (
            MovimentacaoFinanceira.objects
            .filter(tipo='honorario', status='pago')
            .filter(data_pagamento__gte=start, data_pagamento__lte=end)
            .values(
                lawyer_name=F('caso__advogado_responsavel__first_name'),
                lawyer_email=F('caso__advogado_responsavel__email'),
            )
            .annotate(total=Sum('valor'))
            .order_by('-total')
        )
        return list(qs)

    @staticmethod
    def kpi_summary() -> dict:
        """KPIs financeiros: a receber, em atraso, pago no mes."""
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)

        total_receivable = (
            MovimentacaoFinanceira.objects
            .filter(tipo='honorario', status='pendente')
            .aggregate(total=Sum('valor'))
        )['total'] or Decimal('0')

        total_overdue = (
            MovimentacaoFinanceira.objects
            .filter(tipo='honorario', status='pendente', data_vencimento__lt=today)
            .aggregate(total=Sum('valor'))
        )['total'] or Decimal('0')

        paid_this_month = (
            MovimentacaoFinanceira.objects
            .filter(
                tipo='honorario',
                status='pago',
                data_pagamento__gte=first_day_of_month,
                data_pagamento__lte=today,
            )
            .aggregate(total=Sum('valor'))
        )['total'] or Decimal('0')

        expenses_this_month = (
            MovimentacaoFinanceira.objects
            .filter(
                tipo__in=['despesa', 'custas', 'pericia'],
                status='pago',
                data_pagamento__gte=first_day_of_month,
                data_pagamento__lte=today,
            )
            .aggregate(total=Sum('valor'))
        )['total'] or Decimal('0')

        return {
            'total_receivable': str(total_receivable),
            'total_overdue': str(total_overdue),
            'paid_this_month': str(paid_this_month),
            'expenses_this_month': str(expenses_this_month),
            'profit_this_month': str(paid_this_month - expenses_this_month),
        }
