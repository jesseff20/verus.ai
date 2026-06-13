"""
Analytics e relatórios de execução de fluxos para procuradorias.

Funções puras que calculam métricas a partir dos models,
chamadas pelos views sem lógica de acesso a dados.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from django.db.models import Count, Avg, F, Q, ExpressionWrapper, DurationField
from django.db.models.functions import TruncDate, TruncMonth

from .models import FlowInstance, TaskInstance


def _now():
    return datetime.now(tz=timezone.utc)


def _organ_filter(organ):
    """Retorna filtro de órgão; se None, retorna filtro vazio (global)."""
    if organ is None:
        return Q()
    return Q(organ=organ)


def _organ_filter_nested(organ, prefix='instance__'):
    """Retorna filtro de órgão em relação aninhada (ex: instance__organ)."""
    if organ is None:
        return Q()
    return Q(**{f'{prefix}organ': organ})


def flow_summary(organ) -> dict:
    """
    Resumo geral de execuções para o órgão.
    Retorna totais por status e taxa de conclusão.
    Se organ=None, retorna dados globais (cross-organ).
    """
    qs = FlowInstance.objects.filter(_organ_filter(organ))
    total = qs.count()
    by_status = {
        row['status']: row['count']
        for row in qs.values('status').annotate(count=Count('id'))
    }
    completed = by_status.get('completed', 0)
    completion_rate = round((completed / total * 100), 1) if total else 0.0

    return {
        'total': total,
        'running': by_status.get('running', 0),
        'completed': completed,
        'cancelled': by_status.get('cancelled', 0),
        'pending': by_status.get('pending', 0),
        'completion_rate': completion_rate,
    }


def flows_by_template(organ, days: int = 30) -> list[dict]:
    """
    Execuções agrupadas por template nos últimos N dias.
    """
    since = _now() - timedelta(days=days)
    qs = (
        FlowInstance.objects
        .filter(_organ_filter(organ), created_at__gte=since)
        .values('template_name_snapshot')
        .annotate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='completed')),
            running=Count('id', filter=Q(status='running')),
            cancelled=Count('id', filter=Q(status='cancelled')),
        )
        .order_by('-total')
    )
    return list(qs)


def avg_completion_time_by_template(organ) -> list[dict]:
    """
    Tempo médio de conclusão (em horas) por template.
    Apenas instâncias concluídas com started_at e completed_at.
    """
    qs = (
        FlowInstance.objects
        .filter(_organ_filter(organ), status='completed',
                started_at__isnull=False, completed_at__isnull=False)
        .annotate(
            duration=ExpressionWrapper(
                F('completed_at') - F('started_at'),
                output_field=DurationField(),
            )
        )
        .values('template_name_snapshot')
        .annotate(avg_duration=Avg('duration'))
        .order_by('template_name_snapshot')
    )
    result = []
    for row in qs:
        avg = row['avg_duration']
        hours = round(avg.total_seconds() / 3600, 1) if avg else None
        result.append({
            'template': row['template_name_snapshot'],
            'avg_hours': hours,
        })
    return result


def tasks_by_role(organ, days: int = 30) -> list[dict]:
    """
    Tarefas completadas por papel nos últimos N dias.
    Útil para identificar gargalos por papel.
    """
    since = _now() - timedelta(days=days)
    qs = (
        TaskInstance.objects
        .filter(_organ_filter_nested(organ), created_at__gte=since)
        .values('role_required')
        .annotate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='completed')),
            pending=Count('id', filter=Q(status='pending')),
        )
        .order_by('-total')
    )
    return list(qs)


def flow_executions_over_time(organ, days: int = 30) -> list[dict]:
    """
    Número de instâncias iniciadas por dia nos últimos N dias.
    """
    since = _now() - timedelta(days=days)
    qs = (
        FlowInstance.objects
        .filter(_organ_filter(organ), created_at__gte=since)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    return [{'date': str(row['date']), 'count': row['count']} for row in qs]


def pending_tasks_by_user(organ) -> list[dict]:
    """
    Distribuição de tarefas pendentes por usuário assignado.
    """
    qs = (
        TaskInstance.objects
        .filter(
            _organ_filter_nested(organ),
            status__in=('pending', 'in_progress'),
            assigned_to__isnull=False,
        )
        .values('assigned_to__id', 'assigned_to__first_name',
                'assigned_to__last_name', 'assigned_to__email')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    result = []
    for row in qs:
        name = f"{row['assigned_to__first_name']} {row['assigned_to__last_name']}".strip()
        result.append({
            'user_id': str(row['assigned_to__id']),
            'name': name or row['assigned_to__email'],
            'pending_tasks': row['count'],
        })
    return result
