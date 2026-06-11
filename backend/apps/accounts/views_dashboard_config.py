"""
Views para Dashboard Customizável — Feature #24.
"""
import logging
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import DashboardConfig
from .serializers_dashboard_config import DashboardConfigSerializer

logger = logging.getLogger(__name__)

# Layout padrão de widgets
DEFAULT_LAYOUT = [
    {'id': '1', 'type': 'cases_summary', 'position': 0, 'size': 'medium', 'config': {}},
    {'id': '2', 'type': 'deadlines_upcoming', 'position': 1, 'size': 'medium', 'config': {}},
    {'id': '3', 'type': 'financial_summary', 'position': 2, 'size': 'medium', 'config': {}},
    {'id': '4', 'type': 'activity_feed', 'position': 3, 'size': 'medium', 'config': {}},
    {'id': '5', 'type': 'calendar_today', 'position': 4, 'size': 'medium', 'config': {}},
    {'id': '6', 'type': 'kpis', 'position': 5, 'size': 'medium', 'config': {}},
]


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def dashboard_config_get_or_create(request):
    """
    GET  /api/v1/auth/dashboard-config/ — Retorna config (cria padrão se não existir)
    PATCH /api/v1/auth/dashboard-config/ — Atualiza layout/theme/refresh
    """
    config, created = DashboardConfig.objects.get_or_create(
        user=request.user,
        defaults={'layout': DEFAULT_LAYOUT},
    )

    if request.method == 'PATCH':
        serializer = DashboardConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer = DashboardConfigSerializer(config)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_widgets_data(request):
    """
    GET /api/v1/auth/dashboard-config/widgets/
    Retorna dados para todos os tipos de widget.
    """
    now = timezone.now()
    today = now.date()
    user = request.user

    widgets_data = {}

    # cases_summary
    try:
        from apps.cases.models import LegalCase
        active_cases = LegalCase.objects.filter(
            advogado_responsavel=user,
            status__in=['ativo', 'aguardando', 'suspenso'],
        ).count()
        non_archived_qs = LegalCase.objects.filter(advogado_responsavel=user).exclude(status='arquivado')
        recent_cases = list(
            non_archived_qs
            .order_by('-created_at')[:5]
            .values('id', 'titulo', 'status', 'created_at')
        )
        widgets_data['cases_summary'] = {
            'active_count': active_cases,
            'total_count': non_archived_qs.count(),
            'recent_cases': recent_cases,
        }
    except Exception as e:
        logger.warning(f"Erro ao buscar resumo de casos: {e}")
        widgets_data['cases_summary'] = {'active_count': 0, 'total_count': 0, 'recent_cases': []}

    # deadlines_upcoming
    try:
        from apps.cases.models import LegalDeadline
        upcoming = list(
            LegalDeadline.objects.filter(
                caso__advogado_responsavel=user,
                status__in=['pendente', 'em_andamento'],
                data_prazo__gte=today,
            )
            .exclude(caso__status='arquivado')
            .order_by('data_prazo')[:5]
            .values('id', 'titulo', 'data_prazo', 'prioridade', 'caso__titulo')
        )
        widgets_data['deadlines_upcoming'] = {'deadlines': upcoming}
    except Exception as e:
        logger.warning(f"Erro ao buscar prazos: {e}")
        widgets_data['deadlines_upcoming'] = {'deadlines': []}

    # financial_summary
    try:
        from apps.cases.models import MovimentacaoFinanceira
        movs = MovimentacaoFinanceira.objects.filter(
            caso__advogado_responsavel=user,
        ).exclude(caso__status='arquivado')
        receitas = movs.filter(tipo='receita', status='pago').aggregate(total=Sum('valor'))
        pendentes = movs.filter(status='pendente').aggregate(total=Sum('valor'))
        vencidas = movs.filter(
            status='pendente',
            data_vencimento__lt=today,
        ).aggregate(total=Sum('valor'))
        widgets_data['financial_summary'] = {
            'revenue': float(receitas['total'] or 0),
            'pending': float(pendentes['total'] or 0),
            'overdue': float(vencidas['total'] or 0),
        }
    except Exception as e:
        logger.warning(f"Erro ao buscar resumo financeiro: {e}")
        widgets_data['financial_summary'] = {'revenue': 0, 'pending': 0, 'overdue': 0}

    # activity_feed
    try:
        from apps.core.models import AuditLog
        recent_activity = list(
            AuditLog.objects.filter(user=user)
            .order_by('-created_at')[:10]
            .values('id', 'action', 'entity_type', 'entity_name', 'description', 'created_at')
        )
        widgets_data['activity_feed'] = {'activities': recent_activity}
    except Exception as e:
        logger.warning(f"Erro ao buscar atividades: {e}")
        widgets_data['activity_feed'] = {'activities': []}

    # calendar_today
    try:
        from apps.cases.models import LegalDeadline, Audiencia
        today_deadlines = list(
            LegalDeadline.objects.filter(
                caso__advogado_responsavel=user,
                data_prazo=today,
            )
            .exclude(caso__status='arquivado')
            .values('id', 'titulo', 'data_prazo', 'prioridade')
        )
        today_audiencias = list(
            Audiencia.objects.filter(
                caso__advogado_responsavel=user,
                data_hora__date=today,
            )
            .exclude(caso__status='arquivado')
            .values('id', 'tipo', 'data_hora', 'local')
        )
        widgets_data['calendar_today'] = {
            'deadlines': today_deadlines,
            'audiencias': today_audiencias,
        }
    except Exception as e:
        logger.warning(f"Erro ao buscar calendário: {e}")
        widgets_data['calendar_today'] = {'deadlines': [], 'audiencias': []}

    # kpis
    try:
        from apps.cases.models import LegalCase, LegalDeadline
        non_archived_qs = LegalCase.objects.filter(advogado_responsavel=user).exclude(status='arquivado')
        total_cases = non_archived_qs.count()
        won_cases = non_archived_qs.filter(status='ganho').count()
        overdue_deadlines = LegalDeadline.objects.filter(
            caso__advogado_responsavel=user,
            caso__status__in=['ativo', 'aguardando', 'suspenso'],
            status__in=['pendente', 'em_andamento'],
            data_prazo__lt=today,
        ).count()
        widgets_data['kpis'] = {
            'total_cases': total_cases,
            'won_cases': won_cases,
            'win_rate': round(won_cases / total_cases * 100, 1) if total_cases > 0 else 0,
            'overdue_deadlines': overdue_deadlines,
        }
    except Exception as e:
        logger.warning(f"Erro ao buscar KPIs: {e}")
        widgets_data['kpis'] = {'total_cases': 0, 'won_cases': 0, 'win_rate': 0, 'overdue_deadlines': 0}

    return Response(widgets_data)
