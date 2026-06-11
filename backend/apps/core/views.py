"""
Views para o app Core.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import DocumentType, ProcessType, ProcessStatus, AuditLog, LLMProvider, TokenUsageLog
from .serializers import (
    DocumentTypeSerializer,
    DocumentTypeListSerializer,
    ProcessTypeSerializer,
    ProcessTypeListSerializer,
    ProcessStatusSerializer,
    ProcessStatusListSerializer,
    AuditLogSerializer,
    AuditLogListSerializer,
    LLMProviderSerializer,
    LLMProviderListSerializer,
    TokenUsageLogSerializer,
    TokenUsageLogListSerializer,
)


class DocumentTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para tipos de documento.

    Apenas leitura - tipos são gerenciados pelo admin.

    Sem paginação: a lista completa de tipos é necessária para o wizard
    do Gerador de Peças (mapeamento de áreas/categorias). São ~70-100
    registros leves — não justifica paginação.
    """
    queryset = DocumentType.objects.filter(is_active=True).select_related('category')
    pagination_class = None
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['code', 'name', 'short_name', 'description']
    ordering_fields = ['display_order', 'name', 'category']
    ordering = ['category', 'display_order', 'name']

    def get_serializer_class(self):
        if self.action == 'list':
            return DocumentTypeListSerializer
        return DocumentTypeSerializer

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Retorna tipos agrupados por categoria."""
        categories = {}
        for dt in self.get_queryset().select_related('category'):
            if not dt.category_id:
                continue
            cat_code = dt.category.code
            if cat_code not in categories:
                categories[cat_code] = {
                    'category': cat_code,
                    'category_display': dt.category.name,
                    'types': []
                }
            categories[cat_code]['types'].append(
                DocumentTypeListSerializer(dt).data
            )

        return Response(list(categories.values()))

    @action(detail=False, methods=['get'])
    def choices(self, request):
        """Retorna lista simples de code/name para uso em selects."""
        types = self.get_queryset().values_list('code', 'name')
        return Response([
            {'value': code, 'label': name}
            for code, name in types
        ])


class ProcessTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para tipos de caso/processo jurídico.

    Apenas leitura - tipos são gerenciados pelo admin.
    """
    queryset = ProcessType.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['code', 'name', 'short_name', 'description']
    ordering_fields = ['display_order', 'name', 'category']
    ordering = ['category', 'display_order', 'name']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProcessTypeListSerializer
        return ProcessTypeSerializer

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Retorna tipos agrupados por categoria."""
        categories = {}
        for pt in self.get_queryset():
            cat = pt.category
            if cat not in categories:
                categories[cat] = {
                    'category': cat,
                    'category_display': pt.get_category_display(),
                    'types': []
                }
            categories[cat]['types'].append(
                ProcessTypeListSerializer(pt).data
            )

        return Response(list(categories.values()))

    @action(detail=False, methods=['get'])
    def choices(self, request):
        """Retorna lista simples de code/name para uso em selects."""
        types = self.get_queryset().values_list('code', 'name')
        return Response([
            {'value': code, 'label': name}
            for code, name in types
        ])


class ProcessStatusViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para status de processo.

    Apenas leitura - status são gerenciados pelo admin.
    """
    queryset = ProcessStatus.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_active', 'is_default', 'is_final']
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['display_order', 'name', 'category']
    ordering = ['display_order', 'name']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProcessStatusListSerializer
        return ProcessStatusSerializer

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Retorna status agrupados por categoria."""
        categories = {}
        for ps in self.get_queryset():
            cat = ps.category
            if cat not in categories:
                categories[cat] = {
                    'category': cat,
                    'category_display': ps.get_category_display(),
                    'statuses': []
                }
            categories[cat]['statuses'].append(
                ProcessStatusListSerializer(ps).data
            )

        return Response(list(categories.values()))

    @action(detail=False, methods=['get'])
    def choices(self, request):
        """Retorna lista simples de code/name para uso em selects."""
        statuses = self.get_queryset().values_list('code', 'name')
        return Response([
            {'value': code, 'label': name}
            for code, name in statuses
        ])

    @action(detail=False, methods=['get'])
    def default(self, request):
        """Retorna o status padrão para novos processos."""
        default_status = ProcessStatus.get_default()
        if default_status:
            return Response(ProcessStatusSerializer(default_status).data)
        return Response({'error': 'Nenhum status padrão configurado'}, status=status.HTTP_404_NOT_FOUND)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para logs de auditoria.

    Apenas leitura - logs são criados automaticamente pelo sistema.
    """
    queryset = AuditLog.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['action', 'severity', 'entity_type', 'user']
    search_fields = ['entity_name', 'entity_id', 'description', 'user_email']
    ordering_fields = ['created_at', 'action', 'severity']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return AuditLogListSerializer
        return AuditLogSerializer

    def get_queryset(self):
        """Filtra por usuário se não for admin."""
        queryset = super().get_queryset()
        user = self.request.user

        # Admins veem tudo
        if user.is_staff or user.is_superuser:
            return queryset

        # Usuários comuns veem apenas seus próprios logs
        return queryset.filter(user=user)

    @action(detail=False, methods=['get'])
    def my_activity(self, request):
        """Retorna atividade recente do usuário atual."""
        logs = self.get_queryset().filter(user=request.user)
        paginator = PageNumberPagination()
        paginator.page_size = 50
        paginator.page_size_query_param = 'page_size'
        paginator.max_page_size = 100
        page = paginator.paginate_queryset(logs, request)
        if page is not None:
            serializer = AuditLogListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        serializer = AuditLogListSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def entity_history(self, request):
        """Retorna histórico de uma entidade específica."""
        entity_type = request.query_params.get('entity_type')
        entity_id = request.query_params.get('entity_id')

        if not entity_type or not entity_id:
            return Response(
                {'error': 'entity_type e entity_id são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST
            )

        logs = self.get_queryset().filter(
            entity_type=entity_type,
            entity_id=entity_id
        )
        serializer = AuditLogListSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retorna estatísticas de auditoria."""
        from django.db.models import Count
        from django.utils import timezone
        from datetime import timedelta

        queryset = self.get_queryset()
        last_7_days = timezone.now() - timedelta(days=7)

        # Contagem por ação (últimos 7 dias)
        actions = queryset.filter(
            created_at__gte=last_7_days
        ).values('action').annotate(
            count=Count('id')
        ).order_by('-count')

        # Contagem por severidade (últimos 7 dias)
        severities = queryset.filter(
            created_at__gte=last_7_days
        ).values('severity').annotate(
            count=Count('id')
        ).order_by('-count')

        # Contagem por tipo de entidade (últimos 7 dias)
        entities = queryset.filter(
            created_at__gte=last_7_days
        ).values('entity_type').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        return Response({
            'by_action': list(actions),
            'by_severity': list(severities),
            'by_entity_type': list(entities),
            'total_last_7_days': queryset.filter(created_at__gte=last_7_days).count(),
        })


class LLMProviderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para provedores LLM.

    Apenas leitura - providers são gerenciados pelo admin.
    Retorna apenas providers ativos com seus modelos ativos.
    """
    queryset = LLMProvider.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['code', 'name']
    ordering_fields = ['display_order', 'name']
    ordering = ['display_order', 'name']

    def get_serializer_class(self):
        if self.action == 'list':
            return LLMProviderListSerializer
        return LLMProviderSerializer

    @action(detail=False, methods=['get'])
    def with_models(self, request):
        """Retorna todos os providers ativos com seus modelos ativos aninhados."""
        providers = self.get_queryset().prefetch_related('models')
        serializer = LLMProviderSerializer(providers, many=True)
        return Response(serializer.data)


class TokenUsageLogViewSet(viewsets.ModelViewSet):
    """
    ViewSet para logs de uso de tokens de IA.

    GET /token-usage/ - lista com filtros
    GET /token-usage/stats/ - estatísticas agregadas
    POST /token-usage/ - registrar novo uso
    """
    queryset = TokenUsageLog.objects.select_related('user')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['model_provider', 'usage_type', 'user']
    search_fields = ['description', 'model_name']
    ordering_fields = ['created_at', 'total_tokens', 'cost_estimate']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return TokenUsageLogListSerializer
        return TokenUsageLogSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Filtro por data
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        # Não-admins veem apenas seus próprios logs
        if not (user.is_staff or user.is_superuser):
            queryset = queryset.filter(user=user)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estatísticas agregadas de uso de tokens."""
        from django.db.models import Sum, Count, Avg
        from django.utils import timezone
        from datetime import timedelta

        queryset = self.get_queryset()
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        month_start = today_start.replace(day=1)

        def aggregate(qs):
            agg = qs.aggregate(
                total_tokens=Sum('total_tokens'),
                total_input=Sum('input_tokens'),
                total_output=Sum('output_tokens'),
                total_cost=Sum('cost_estimate'),
                count=Count('id'),
            )
            return {k: v or 0 for k, v in agg.items()}

        # Por período
        today_stats = aggregate(queryset.filter(created_at__gte=today_start))
        week_stats = aggregate(queryset.filter(created_at__gte=week_start))
        month_stats = aggregate(queryset.filter(created_at__gte=month_start))
        all_time = aggregate(queryset)

        # Por provedor (último mês)
        by_provider = list(
            queryset.filter(created_at__gte=month_start)
            .values('model_provider')
            .annotate(
                total_tokens=Sum('total_tokens'),
                total_cost=Sum('cost_estimate'),
                count=Count('id'),
            )
            .order_by('-total_tokens')
        )

        # Por tipo de uso (último mês)
        by_usage_type = list(
            queryset.filter(created_at__gte=month_start)
            .values('usage_type')
            .annotate(
                total_tokens=Sum('total_tokens'),
                total_cost=Sum('cost_estimate'),
                count=Count('id'),
            )
            .order_by('-total_tokens')
        )

        # Por usuário (último mês, apenas admins)
        by_user = []
        if request.user.is_staff or request.user.is_superuser:
            by_user = list(
                queryset.filter(created_at__gte=month_start)
                .values('user__email')
                .annotate(
                    total_tokens=Sum('total_tokens'),
                    total_cost=Sum('cost_estimate'),
                    count=Count('id'),
                )
                .order_by('-total_tokens')[:20]
            )

        # Timeline (últimos 30 dias, agrupado por dia)
        from django.db.models.functions import TruncDate
        timeline = list(
            queryset.filter(created_at__gte=today_start - timedelta(days=30))
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(
                total_tokens=Sum('total_tokens'),
                total_cost=Sum('cost_estimate'),
                count=Count('id'),
            )
            .order_by('date')
        )
        # Convert date to string for JSON
        for entry in timeline:
            entry['date'] = entry['date'].isoformat() if entry['date'] else None

        return Response({
            'today': today_stats,
            'week': week_stats,
            'month': month_stats,
            'all_time': all_time,
            'by_provider': by_provider,
            'by_usage_type': by_usage_type,
            'by_user': by_user,
            'timeline': timeline,
        })
