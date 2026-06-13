import logging
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)

from .models import FlowInstance, TaskInstance, TaskRequest
from .permissions import BelongsToOrgan, CanStartFlow, CanApproveRequests, IsTaskAssigneeOrManager
from .serializers import (
    FlowInstanceListSerializer, FlowInstanceDetailSerializer,
    StartFlowSerializer, TaskInstanceSerializer,
    CompleteTaskSerializer, CreateTaskRequestSerializer,
    ResolveRequestSerializer, TaskRequestSerializer,
)
from . import service


class FlowInstanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Gerencia instâncias de fluxo do órgão do usuário logado.

    list    GET  /executions/
    retrieve GET /executions/{id}/
    start   POST /executions/start/
    cancel  POST /executions/{id}/cancel/
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = FlowInstance.objects.select_related(
            'template', 'started_by', 'organ'
        ).annotate(
            pending_task_count_annotation=Count(
                'tasks',
                filter=Q(tasks__status__in=('pending', 'in_progress')),
            )
        )
        # Superadmin/admin veem todas as instâncias (cross-organ)
        if getattr(user, 'is_admin', False):
            pass  # sem filtro de órgão
        elif hasattr(user, 'organ') and user.organ:
            qs = qs.filter(organ=user.organ)
        else:
            qs = qs.none()

        # Filtros opcionais
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        template_id = self.request.query_params.get('template_id')
        if template_id:
            qs = qs.filter(template_id=template_id)

        return qs.order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return FlowInstanceDetailSerializer
        return FlowInstanceListSerializer

    @action(detail=False, methods=['post'], url_path='start',
            permission_classes=[CanStartFlow])
    def start(self, request):
        """POST /executions/start/ — inicia uma nova instância."""
        serializer = StartFlowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not (hasattr(user, 'organ') and user.organ):
            return Response(
                {'detail': 'Usuário não está vinculado a um órgão.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            instance = service.start_flow(
                template_id=serializer.validated_data['template_id'],
                organ=user.organ,
                started_by=user,
                case_ref=serializer.validated_data.get('case_ref', ''),
                case_title=serializer.validated_data.get('case_title', ''),
                case_id=str(serializer.validated_data['case_id']) if serializer.validated_data.get('case_id') else None,
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            FlowInstanceDetailSerializer(instance).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """POST /executions/{id}/cancel/"""
        instance = self.get_object()
        try:
            service.cancel_flow(str(instance.id), cancelled_by=request.user)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(FlowInstanceDetailSerializer(instance).data)


class TaskInstanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Tarefas de uma FlowInstance específica.

    list    GET  /executions/{instance_pk}/tasks/
    complete POST /executions/{instance_pk}/tasks/{id}/complete/
    request  POST /executions/{instance_pk}/tasks/{id}/request/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TaskInstanceSerializer

    def get_queryset(self):
        instance_pk = self.kwargs.get('instance_pk')
        user = self.request.user
        qs = TaskInstance.objects.filter(instance_id=instance_pk)
        # Superadmin/admin veem tasks de qualquer órgão
        if not getattr(user, 'is_admin', False):
            organ = getattr(user, 'organ', None)
            if organ:
                qs = qs.filter(instance__organ=organ)
        return qs.select_related(
            'assigned_to', 'completed_by',
            'instance', 'instance__template',
        ).prefetch_related('requests')

    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, instance_pk=None, pk=None):
        """POST /executions/{instance_pk}/tasks/{id}/complete/"""
        task = self.get_object()
        serializer = CompleteTaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Verifica se usuário pode completar esta task
        perm = IsTaskAssigneeOrManager()
        if not perm.has_object_permission(request, self, task):
            return Response(
                {'detail': 'Você não tem permissão para concluir esta tarefa.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            instance = service.complete_task(
                task_id=str(task.id),
                completed_by=request.user,
                notes=serializer.validated_data.get('notes', ''),
                gateway_choice=serializer.validated_data.get('gateway_choice', ''),
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(FlowInstanceDetailSerializer(instance).data)

    @action(detail=True, methods=['post'], url_path='request')
    def create_request(self, request, instance_pk=None, pk=None):
        """POST /executions/{instance_pk}/tasks/{id}/request/"""
        task = self.get_object()
        serializer = CreateTaskRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Resolve target_user se fornecido
        target_user = None
        target_user_id = serializer.validated_data.get('target_user')
        if target_user_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            target_user = get_object_or_404(User, pk=target_user_id)

        req = TaskRequest.objects.create(
            task=task,
            request_type=serializer.validated_data['request_type'],
            requester=request.user,
            target_user=target_user,
            justification=serializer.validated_data['justification'],
        )

        from apps.workflow_execution.models import ExecutionEvent
        ExecutionEvent.objects.create(
            instance=task.instance,
            event_type='request_created',
            node_id=task.node_id,
            node_label=task.label,
            actor=request.user,
            metadata={
                'request_id': str(req.id),
                'request_type': req.request_type,
            },
        )

        return Response(TaskRequestSerializer(req).data, status=status.HTTP_201_CREATED)


class MyTasksViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /my-tasks/ — tarefas atribuídas ao usuário logado.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TaskInstanceSerializer

    def get_queryset(self):
        user = self.request.user
        # Superadmin/admin veem suas tasks sem filtro de órgão
        if getattr(user, 'is_admin', False):
            qs = TaskInstance.objects.filter(
                assigned_to=user,
            ).select_related(
                'instance', 'instance__template',
                'assigned_to', 'completed_by',
            ).prefetch_related('requests')
        else:
            organ = getattr(user, 'organ', None)
            if not organ:
                return TaskInstance.objects.none()
            qs = TaskInstance.objects.filter(
                assigned_to=user,
                instance__organ=organ,
            ).select_related(
                'instance', 'instance__template',
                'assigned_to', 'completed_by',
            ).prefetch_related('requests')

        status_filter = self.request.query_params.get('status', 'pending')
        if status_filter != 'all':
            qs = qs.filter(status=status_filter)

        return qs.order_by('due_date', 'created_at')


class TaskRequestAdminViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Gerencia solicitações pendentes do órgão (para gerentes/distribuidores).

    list    GET /task-requests/
    approve POST /task-requests/{id}/approve/
    reject  POST /task-requests/{id}/reject/
    """
    permission_classes = [CanApproveRequests]
    serializer_class = TaskRequestSerializer

    def get_queryset(self):
        user = self.request.user
        qs = TaskRequest.objects.select_related(
            'task', 'requester', 'target_user', 'resolved_by',
        )
        # Superadmin/admin veem solicitações de todos os órgãos
        if not getattr(user, 'is_admin', False):
            organ = getattr(user, 'organ', None)
            if not organ:
                return TaskRequest.objects.none()
            qs = qs.filter(task__instance__organ=organ)

        status_filter = self.request.query_params.get('status', 'pending')
        if status_filter != 'all':
            qs = qs.filter(status=status_filter)

        return qs.order_by('-created_at')

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        req = self.get_object()
        serializer = ResolveRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            req = service.approve_request(
                request_id=str(req.id),
                resolved_by=request.user,
                resolution_note=serializer.validated_data.get('resolution_note', ''),
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(TaskRequestSerializer(req).data)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        req = self.get_object()
        serializer = ResolveRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            req = service.reject_request(
                request_id=str(req.id),
                resolved_by=request.user,
                resolution_note=serializer.validated_data.get('resolution_note', ''),
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(TaskRequestSerializer(req).data)


# =============================================================================
# Fase 5 — Analytics de Fluxos
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def flow_analytics(request):
    """
    GET /api/v1/workflow-execution/analytics/

    Retorna métricas consolidadas de execução de fluxos para o órgão do usuário.
    Query params:
      days (int, default 30): janela de tempo para métricas temporais
    """
    user = request.user
    from . import analytics as a
    days = int(request.query_params.get('days', 30))
    organ = getattr(user, 'organ', None)

    # Superadmin/admin sem órgão: analytics globais (organ=None)
    if not organ and not getattr(user, 'is_admin', False):
        return Response({'detail': 'Usuário não vinculado a um órgão.'}, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'summary': a.flow_summary(organ),
        'by_template': a.flows_by_template(organ, days=days),
        'avg_completion_time': a.avg_completion_time_by_template(organ),
        'tasks_by_role': a.tasks_by_role(organ, days=days),
        'executions_over_time': a.flow_executions_over_time(organ, days=days),
        'pending_by_user': a.pending_tasks_by_user(organ),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def suggest_flow(request):
    """
    POST /api/v1/workflow-execution/suggest-flow/

    Body: { "especialidade": "administrativo", "descricao": "...", "tribunal": "TJSP" }

    Sugere o template de fluxo mais adequado com base nos campos do processo.
    Usa heurística simples (score por categoria) sem chamada de LLM para não
    bloquear o MVP; pode ser substituído por LLM na iteração seguinte.
    """
    user = request.user
    organ = getattr(user, 'organ', None)
    if not organ and not getattr(user, 'is_admin', False):
        return Response({'detail': 'Usuário não vinculado a um órgão.'}, status=status.HTTP_400_BAD_REQUEST)

    from apps.workflow_definition.models import FlowTemplate, FLOW_CATEGORY_CHOICES

    especialidade = request.data.get('especialidade', '').lower()
    descricao = (request.data.get('descricao') or '').lower()
    tribunal = (request.data.get('tribunal') or '').lower()

    # Score heurístico por categoria
    scores: dict[str, float] = {}

    # Palavras-chave → categoria
    KEYWORDS = {
        'judicial_1': [
            'mandado', 'ação', 'tjsp', 'tjrj', 'tjmg', 'vara', 'comarca',
            '1º grau', 'primeiro grau', 'cível', 'criminal', 'trabalhista',
        ],
        'judicial_2': [
            'recurso', 'apelação', 'agravo', '2º grau', 'segundo grau',
            'trt', 'trf', 'stj', 'stf', 'acórdão',
        ],
        'administrative': [
            'administrativo', 'licitação', 'contrato', 'parecer', 'nota técnica',
            'pregão', 'concurso', 'servidor', 'administrativo',
        ],
    }

    text = f'{especialidade} {descricao} {tribunal}'
    for category, keywords in KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        scores[category] = score

    # Mapeamento direto de especialidade → categoria
    ESPECIALIDADE_MAP = {
        'administrativo': 'administrative',
        'tributario': 'administrative',
        'civel': 'judicial_1',
        'criminal': 'judicial_1',
        'trabalhista': 'judicial_1',
        'previdenciario': 'judicial_1',
    }
    if especialidade in ESPECIALIDADE_MAP:
        scores[ESPECIALIDADE_MAP[especialidade]] = scores.get(ESPECIALIDADE_MAP[especialidade], 0) + 2

    best_category = max(scores, key=lambda k: scores[k]) if scores else 'judicial_1'

    from apps.workflow_definition.models import FlowTemplate as FT
    from django.db.models import Q, Count
    organ_filter = Q(organ__isnull=True)
    if organ:
        organ_filter = Q(organ=organ) | Q(organ__isnull=True)
    suggestions = list(
        FT.objects.filter(
            status='published',
            category=best_category,
        ).filter(organ_filter)
        .values('id', 'name', 'category', 'version')
        .annotate(node_count=Count('nodes'))[:5]
    )

    return Response({
        'suggested_category': best_category,
        'category_label': dict(FLOW_CATEGORY_CHOICES).get(best_category, best_category),
        'score_breakdown': scores,
        'suggestions': [
            {**s, 'id': str(s['id'])}
            for s in suggestions
        ],
    })

