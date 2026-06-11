"""
Views de Auditoria de Acessos — Feature #23.
"""
import logging
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import AuditLog
from .serializers import AuditLogSerializer, AuditLogListSerializer

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def audit_log_list(request):
    """
    GET /api/v1/core/auditoria/
    Lista paginada de logs de auditoria com filtros.
    """
    qs = AuditLog.objects.select_related('user').all()

    # Filtros
    user_id = request.query_params.get('user')
    if user_id:
        qs = qs.filter(user_id=user_id)

    action = request.query_params.get('action')
    if action:
        qs = qs.filter(action=action)

    date_from = request.query_params.get('date_from')
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)

    date_to = request.query_params.get('date_to')
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    resource_type = request.query_params.get('resource_type')
    if resource_type:
        qs = qs.filter(entity_type__icontains=resource_type)

    search = request.query_params.get('search', '').strip()
    if search:
        qs = qs.filter(
            Q(description__icontains=search) |
            Q(entity_name__icontains=search) |
            Q(user_email__icontains=search)
        )

    # Paginacao
    try:
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
    except (ValueError, TypeError):
        page_size = 20
        page = 1
    offset = (page - 1) * page_size

    total = qs.count()
    logs = qs[offset:offset + page_size]

    serializer = AuditLogListSerializer(logs, many=True)
    return Response({
        'count': total,
        'next': None,
        'previous': None,
        'results': serializer.data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def audit_log_stats(request):
    """
    GET /api/v1/core/auditoria/stats/
    Estatisticas de auditoria.
    """
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    last_24h = now - timedelta(hours=24)

    total = AuditLog.objects.count()
    today_count = AuditLog.objects.filter(created_at__gte=today_start).count()
    last_24h_count = AuditLog.objects.filter(created_at__gte=last_24h).count()

    # Usuarios ativos (ultimos 7 dias)
    active_users = AuditLog.objects.filter(
        created_at__gte=now - timedelta(days=7),
        user__isnull=False,
    ).values('user').distinct().count()

    # Por tipo de acao
    by_action = list(
        AuditLog.objects.values('action')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    # Por usuario (top 10)
    by_user = list(
        AuditLog.objects.filter(user__isnull=False)
        .values('user_email')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    # Por tipo de recurso (top 10)
    by_resource = list(
        AuditLog.objects.values('entity_type')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    # Atividade recente (ultimas 10 entradas)
    recent = AuditLogListSerializer(
        AuditLog.objects.all()[:10], many=True
    ).data

    return Response({
        'total': total,
        'today': today_count,
        'last_24h': last_24h_count,
        'active_users': active_users,
        'by_action': by_action,
        'by_user': by_user,
        'by_resource': by_resource,
        'recent_activity': recent,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def audit_log_user_activity(request, user_id):
    """
    GET /api/v1/core/auditoria/usuario/<uuid:user_id>/
    Atividade de um usuario especifico.
    """
    qs = AuditLog.objects.filter(user_id=user_id).select_related('user')

    # Paginacao
    try:
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
    except (ValueError, TypeError):
        page_size = 20
        page = 1
    offset = (page - 1) * page_size

    total = qs.count()
    logs = qs[offset:offset + page_size]

    # Resumo do usuario
    now = timezone.now()
    summary = {
        'total_actions': total,
        'last_7_days': qs.filter(created_at__gte=now - timedelta(days=7)).count(),
        'last_30_days': qs.filter(created_at__gte=now - timedelta(days=30)).count(),
        'by_action': list(
            qs.values('action').annotate(count=Count('id')).order_by('-count')
        ),
    }

    serializer = AuditLogSerializer(logs, many=True)
    return Response({
        'count': total,
        'summary': summary,
        'results': serializer.data,
    })
