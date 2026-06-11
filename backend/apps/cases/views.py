"""
Views do app Cases — Gestão de Casos Jurídicos.
"""
import os
import logging
from datetime import timedelta
from django.db.models import Q, Count
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from apps.core.throttles import (
    AIGenerationThrottle,
    OCRUploadThrottle,
    NFSeEmitThrottle,
    ConflictCheckThrottle,
    ExportThrottle,
    ProtocolSubmitThrottle,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

from apps.core.models import AuditLog
from apps.intelligent_assistant.models import IntelligentSession, GeneratedDocument
from apps.simulations.models import Simulation
from .models import (
    Client, LegalCase, LegalDeadline, CaseTask, CaseDocument, CasePhase,
    Audiencia, MovimentacaoFinanceira, LegalNotification, OABFeeTable,
    ElectronicProtocol, TribunalPushConfig, TribunalPushEvent,
    LegalContract, CourtFeeGuide, DigitalSignature, SignatureVerification,
    WorkflowTemplate, WorkflowExecution,
)
from .serializers import (
    ClientSerializer,
    LegalCaseListSerializer,
    LegalCaseDetailSerializer,
    LegalDeadlineSerializer,
    CaseTaskSerializer,
    CaseDocumentSerializer,
    CasePhaseSerializer,
    AudienciaSerializer,
    MovimentacaoFinanceiraSerializer,
    LegalNotificationSerializer,
    ElectronicProtocolSerializer,
    TribunalPushConfigSerializer,
    TribunalPushEventSerializer,
    LegalContractSerializer,
    CourtFeeGuideSerializer,
    DigitalSignatureSerializer,
    SignatureVerificationSerializer,
    CalendarEventSerializer,
    WorkflowTemplateSerializer,
    WorkflowExecutionSerializer,
)

logger = logging.getLogger(__name__)


def paginate_queryset(request, queryset, page_size=20):
    """Helper to paginate a queryset in function-based views."""
    paginator = PageNumberPagination()
    paginator.page_size = page_size
    paginator.page_size_query_param = 'page_size'
    paginator.max_page_size = 100
    page = paginator.paginate_queryset(queryset, request)
    return page, paginator


# ─────────────────────────────────────────────────────────────────────────────
# PERMISSION HELPERS
# ─────────────────────────────────────────────────────────────────────────────

_PRIVILEGED_ROLES = ('superadmin', 'admin', 'socio', 'gestor')


def _is_privileged(user):
    """Return True if user has a privileged role (full access)."""
    return (
        user.is_staff
        or user.is_superuser
        or getattr(user, 'role', '') in _PRIVILEGED_ROLES
    )


def user_can_access_case(user, case):
    """Check if user has access to a case."""
    if _is_privileged(user):
        return True
    return (
        case.advogado_responsavel_id == user.id
        or case.created_by_id == user.id
    )


def check_object_permission(user, obj):
    """Check if user can access an object that belongs to a case."""
    if _is_privileged(user):
        return True
    caso = getattr(obj, 'caso', None) or getattr(obj, 'case', None)
    if caso:
        return user_can_access_case(user, caso)
    created_by = getattr(obj, 'created_by_id', None)
    if created_by:
        return created_by == user.id
    return False


def _deny():
    """Return a 403 response."""
    return Response({'error': 'Acesso negado'}, status=status.HTTP_403_FORBIDDEN)


MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_UPLOAD_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.xlsx', '.xls', '.csv', '.txt',
    '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.odt',
}


def validate_upload(file):
    """Validate uploaded file size and extension."""
    if file.size > MAX_UPLOAD_SIZE:
        return False, f'Arquivo muito grande. Máximo: {MAX_UPLOAD_SIZE // (1024 * 1024)}MB'
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        return False, f'Tipo de arquivo não permitido: {ext}'
    return True, ''


# ─────────────────────────────────────────────────────────────────────────────
# CLIENTES
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def clients_list_create(request):
    """
    GET  /api/v1/clientes/  — Lista clientes
    POST /api/v1/clientes/  — Cria novo cliente
    """
    if request.method == 'GET':
        qs = Client.objects.select_related('responsible_lawyer').all()

        # Filtros
        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(cpf_cnpj__icontains=search) |
                Q(email__icontains=search) |
                Q(company_name__icontains=search)
            )

        client_type = request.query_params.get('client_type')
        if client_type:
            qs = qs.filter(client_type=client_type)

        is_active = request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active in ('true', '1', 'True'))

        # Paginação simples
        try:
            page_size = int(request.query_params.get('page_size', 20))
            page = int(request.query_params.get('page', 1))
        except (ValueError, TypeError):
            page_size = 20
            page = 1
        offset = (page - 1) * page_size

        try:
            total = qs.count()
            clients = qs[offset:offset + page_size]

            serializer = ClientSerializer(clients, many=True)
            return Response({
                'count': total,
                'next': None,
                'previous': None,
                'results': serializer.data,
            })
        except Exception as exc:
            logger.error(f"[clients_list_create] Erro ao listar clientes: {exc}", exc_info=True)
            return Response(
                {'error': 'Erro ao carregar clientes. Verifique se as migrações estão aplicadas.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # POST
    serializer = ClientSerializer(data=request.data)
    if serializer.is_valid():
        client = serializer.save(created_by=request.user)
        return Response(ClientSerializer(client).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def client_detail(request, client_id):
    """
    GET    /api/v1/clientes/<id>/  — Detalhe do cliente
    PUT    /api/v1/clientes/<id>/  — Atualizar cliente (completo)
    PATCH  /api/v1/clientes/<id>/  — Atualizar cliente (parcial)
    DELETE /api/v1/clientes/<id>/  — Remover cliente
    """
    try:
        client = Client.objects.select_related('responsible_lawyer', 'created_by').get(id=client_id)
    except Client.DoesNotExist:
        return Response({'error': 'Cliente não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    # Permission: privileged roles see all; others only their own clients
    if not _is_privileged(request.user):
        if (
            getattr(client, 'responsible_lawyer_id', None) != request.user.id
            and getattr(client, 'created_by_id', None) != request.user.id
        ):
            return _deny()

    if request.method == 'GET':
        serializer = ClientSerializer(client)
        client_data = serializer.data

        # Include all linked cases (by FK or matching cliente_nome)
        cases = LegalCase.objects.filter(
            Q(client=client) | Q(cliente_nome__icontains=client.name),
            deleted_at__isnull=True,
        ).select_related('advogado_responsavel', 'client').annotate(
            prazos_pendentes_count=Count(
                'prazos', filter=Q(prazos__status='pendente')
            ),
            tarefas_pendentes_count=Count(
                'tarefas', filter=Q(tarefas__status__in=['pendente', 'em_andamento'])
            ),
        ).order_by('-created_at')

        client_data['cases'] = LegalCaseListSerializer(cases, many=True).data
        return Response(client_data)

    if request.method in ('PUT', 'PATCH'):
        serializer = ClientSerializer(
            client, data=request.data, partial=(request.method == 'PATCH')
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE
    client.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────────────────────────────────────
# CASOS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def cases_list_create(request):
    """
    GET  /api/v1/processos/  — Lista casos do usuário
    POST /api/v1/processos/  — Cria novo caso
    """
    if request.method == 'GET':
        qs = LegalCase.objects.select_related('advogado_responsavel', 'client').annotate(
            prazos_pendentes_count=Count(
                'prazos', filter=Q(prazos__status='pendente')
            ),
            tarefas_pendentes_count=Count(
                'tarefas', filter=Q(tarefas__status__in=['pendente', 'em_andamento'])
            ),
        )

        # Filtro de multi-tenancy: sempre restringir ao órgão do usuário
        user_organ = getattr(request.user, 'organ', None)
        if user_organ:
            qs = qs.filter(organ=user_organ)

        # Filtrar por usuário (privileged vê tudo do órgão, outros só os seus)
        if not _is_privileged(request.user):
            qs = qs.filter(
                Q(advogado_responsavel=request.user) | Q(created_by=request.user)
            )

        # Filtros opcionais
        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(numero_processo__icontains=search) |
                Q(titulo__icontains=search) |
                Q(cliente_nome__icontains=search) |
                Q(parte_contraria__icontains=search)
            )

        especialidade = request.query_params.get('especialidade')
        if especialidade:
            qs = qs.filter(especialidade=especialidade)

        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        # Paginação simples
        try:
            page_size = int(request.query_params.get('page_size', 20))
            page = int(request.query_params.get('page', 1))
        except (ValueError, TypeError):
            page_size = 20
            page = 1
        offset = (page - 1) * page_size

        try:
            total = qs.count()
            casos = qs[offset:offset + page_size]

            serializer = LegalCaseListSerializer(casos, many=True)
            return Response({
                'count': total,
                'next': None,
                'previous': None,
                'results': serializer.data,
            })
        except Exception as exc:
            logger.error(f"[cases_list_create] {exc}", exc_info=True)
            return Response(
                {'error': 'Erro interno ao carregar casos.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # POST
    serializer = LegalCaseDetailSerializer(data=request.data)
    if serializer.is_valid():
        save_kwargs = {
            'created_by': request.user,
            'advogado_responsavel': serializer.validated_data.get(
                'advogado_responsavel', request.user
            ),
        }
        user_organ = getattr(request.user, 'organ', None)
        if user_organ and 'organ' not in serializer.validated_data:
            save_kwargs['organ'] = user_organ
        caso = serializer.save(**save_kwargs)

        # Criar prazos processuais automaticamente
        try:
            from apps.cases.services import DeadlineService
            prazos_identificados = request.data.get('prazos_identificados')
            DeadlineService.create_default_deadlines(
                caso,
                user=request.user,
                prazos_identificados=prazos_identificados,
            )
        except Exception as exc:
            logger.warning(f"[cases_list_create] Erro ao criar prazos automáticos: {exc}")

        # Criar fases processuais automaticamente
        try:
            from apps.cases.services.case_phases import create_phases_for_case
            create_phases_for_case(caso)
        except Exception as exc:
            logger.warning(f"[cases_list_create] Erro ao criar fases processuais: {exc}")

        # Criar checklist automático se solicitado (#14)
        auto_checklist = request.data.get('auto_checklist')
        if auto_checklist in (True, 'true', '1', 1):
            try:
                from apps.cases.services.checklist_service import ChecklistService
                ChecklistService.create_checklist_for_case(caso, user=request.user)
            except Exception as exc:
                logger.warning(f"[cases_list_create] Erro ao criar checklist automático: {exc}")

        return Response(
            LegalCaseDetailSerializer(caso).data,
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def case_detail(request, case_id):
    """
    GET    /api/v1/processos/<id>/  — Detalhe do caso
    PUT    /api/v1/processos/<id>/  — Atualizar caso (completo)
    PATCH  /api/v1/processos/<id>/  — Atualizar caso (parcial)
    DELETE /api/v1/processos/<id>/  — Remover caso
    """
    try:
        caso = LegalCase.objects.select_related('advogado_responsavel', 'created_by', 'client').get(id=case_id)
    except LegalCase.DoesNotExist:
        return Response({'error': 'Caso não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    # Permissão
    if not user_can_access_case(request.user, caso):
        return _deny()

    if request.method == 'GET':
        serializer = LegalCaseDetailSerializer(caso)
        return Response(serializer.data)

    if request.method in ('PUT', 'PATCH'):
        serializer = LegalCaseDetailSerializer(
            caso, data=request.data, partial=(request.method == 'PATCH')
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE (soft delete — preserva registro no banco)
    caso.soft_delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────────────────────────────────────
# PRAZOS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def deadlines_list_create(request, case_id=None):
    """
    GET  /api/v1/processos/prazos/             — Todos os prazos do usuário
    GET  /api/v1/processos/<id>/prazos/        — Prazos de um caso
    POST /api/v1/processos/<id>/prazos/        — Adicionar prazo
    """
    if request.method == 'GET':
        if case_id:
            qs = LegalDeadline.objects.filter(caso_id=case_id).select_related('responsavel')
        else:
            # Todos os prazos dos casos do usuário
            if _is_privileged(request.user):
                qs = LegalDeadline.objects.select_related('caso', 'responsavel')
            else:
                qs = LegalDeadline.objects.filter(
                    Q(caso__advogado_responsavel=request.user) |
                    Q(caso__created_by=request.user) |
                    Q(responsavel=request.user)
                ).distinct()

        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        qs = qs.select_related('responsavel')
        page, paginator = paginate_queryset(request, qs)
        if page is not None:
            return paginator.get_paginated_response(LegalDeadlineSerializer(page, many=True).data)
        return Response(LegalDeadlineSerializer(qs, many=True).data)

    # POST
    data = request.data.copy()
    if case_id:
        data['caso'] = str(case_id)

    serializer = LegalDeadlineSerializer(data=data)
    if serializer.is_valid():
        prazo = serializer.save(created_by=request.user)
        return Response(LegalDeadlineSerializer(prazo).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def deadline_detail(request, deadline_id):
    """Detalhe/edição/remoção de prazo."""
    try:
        prazo = LegalDeadline.objects.select_related('caso', 'responsavel').get(id=deadline_id)
    except LegalDeadline.DoesNotExist:
        return Response({'error': 'Prazo não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    # Permission: case access or assigned as responsavel
    if not _is_privileged(request.user):
        if not (
            user_can_access_case(request.user, prazo.caso)
            or prazo.responsavel_id == request.user.id
        ):
            return _deny()

    if request.method == 'GET':
        return Response(LegalDeadlineSerializer(prazo).data)

    if request.method in ('PUT', 'PATCH'):
        serializer = LegalDeadlineSerializer(
            prazo, data=request.data, partial=(request.method == 'PATCH')
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    prazo.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────────────────────────────────────
# TAREFAS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def tasks_list_create(request, case_id):
    """
    GET  /api/v1/processos/<id>/tarefas/  — Tarefas do caso
    POST /api/v1/processos/<id>/tarefas/  — Adicionar tarefa
    """
    # Verify case access
    try:
        caso = LegalCase.objects.select_related('advogado_responsavel', 'created_by').get(id=case_id)
    except LegalCase.DoesNotExist:
        return Response({'error': 'Caso não encontrado'}, status=status.HTTP_404_NOT_FOUND)
    if not user_can_access_case(request.user, caso):
        return _deny()

    if request.method == 'GET':
        qs = CaseTask.objects.filter(caso_id=case_id).select_related('responsavel')
        page, paginator = paginate_queryset(request, qs)
        if page is not None:
            return paginator.get_paginated_response(CaseTaskSerializer(page, many=True).data)
        return Response(CaseTaskSerializer(qs, many=True).data)

    data = request.data.copy()
    data['caso'] = str(case_id)
    serializer = CaseTaskSerializer(data=data)
    if serializer.is_valid():
        tarefa = serializer.save(created_by=request.user)
        return Response(CaseTaskSerializer(tarefa).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def task_detail(request, task_id):
    """Detalhe/edição/remoção de tarefa."""
    try:
        tarefa = CaseTask.objects.select_related('caso', 'responsavel').get(id=task_id)
    except CaseTask.DoesNotExist:
        return Response({'error': 'Tarefa não encontrada'}, status=status.HTTP_404_NOT_FOUND)

    # Permission: case access or assigned as responsavel
    if not _is_privileged(request.user):
        if not (
            check_object_permission(request.user, tarefa)
            or tarefa.responsavel_id == request.user.id
        ):
            return _deny()

    if request.method == 'GET':
        return Response(CaseTaskSerializer(tarefa).data)

    if request.method in ('PUT', 'PATCH'):
        serializer = CaseTaskSerializer(
            tarefa, data=request.data, partial=(request.method == 'PATCH')
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    tarefa.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENTOS DO CASO
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def case_documents_list_create(request, case_id):
    """Documentos vinculados ao caso."""
    # Verify case access
    try:
        caso = LegalCase.objects.select_related('advogado_responsavel', 'created_by').get(id=case_id)
    except LegalCase.DoesNotExist:
        return Response({'error': 'Caso não encontrado'}, status=status.HTTP_404_NOT_FOUND)
    if not user_can_access_case(request.user, caso):
        return _deny()

    if request.method == 'GET':
        qs = CaseDocument.objects.filter(caso_id=case_id)
        page, paginator = paginate_queryset(request, qs)
        if page is not None:
            return paginator.get_paginated_response(CaseDocumentSerializer(page, many=True).data)
        return Response(CaseDocumentSerializer(qs, many=True).data)

    data = request.data.copy()
    data['caso'] = str(case_id)
    serializer = CaseDocumentSerializer(data=data)
    if serializer.is_valid():
        doc = serializer.save(created_by=request.user)
        return Response(CaseDocumentSerializer(doc).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────────────────────────
# AUDIÊNCIAS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def case_audiencias(request, case_id):
    """
    GET  /api/v1/processos/<case_id>/audiencias/  — Lista audiências do caso
    POST /api/v1/processos/<case_id>/audiencias/  — Cria audiência
    """
    try:
        caso = LegalCase.objects.select_related('advogado_responsavel', 'created_by').get(id=case_id)
    except LegalCase.DoesNotExist:
        return Response({'error': 'Caso não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    if not user_can_access_case(request.user, caso):
        return _deny()

    if request.method == 'GET':
        qs = Audiencia.objects.filter(caso=caso)
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        page, paginator = paginate_queryset(request, qs)
        if page is not None:
            return paginator.get_paginated_response(AudienciaSerializer(page, many=True).data)
        return Response(AudienciaSerializer(qs, many=True).data)

    data = request.data.copy()
    data['caso'] = str(case_id)
    serializer = AudienciaSerializer(data=data)
    if serializer.is_valid():
        audiencia = serializer.save()
        return Response(AudienciaSerializer(audiencia).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def audiencia_detail(request, case_id, audiencia_id):
    """
    GET    /api/v1/processos/<case_id>/audiencias/<audiencia_id>/  — Detalhe
    PATCH  /api/v1/processos/<case_id>/audiencias/<audiencia_id>/  — Atualizar
    DELETE /api/v1/processos/<case_id>/audiencias/<audiencia_id>/  — Remover
    """
    try:
        audiencia = Audiencia.objects.select_related('caso').get(id=audiencia_id, caso_id=case_id)
    except Audiencia.DoesNotExist:
        return Response({'error': 'Audiência não encontrada'}, status=status.HTTP_404_NOT_FOUND)

    if not check_object_permission(request.user, audiencia):
        return _deny()

    if request.method == 'GET':
        return Response(AudienciaSerializer(audiencia).data)

    if request.method == 'PATCH':
        serializer = AudienciaSerializer(audiencia, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    audiencia.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────────────────────────────────────
# MOVIMENTAÇÕES FINANCEIRAS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def case_movimentacoes(request, case_id):
    """
    GET  /api/v1/processos/<case_id>/movimentacoes/  — Lista movimentações do caso
    POST /api/v1/processos/<case_id>/movimentacoes/  — Cria movimentação
    """
    try:
        caso = LegalCase.objects.select_related('advogado_responsavel', 'created_by').get(id=case_id)
    except LegalCase.DoesNotExist:
        return Response({'error': 'Caso não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    if not user_can_access_case(request.user, caso):
        return _deny()

    if request.method == 'GET':
        qs = MovimentacaoFinanceira.objects.filter(caso=caso)
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        tipo_filter = request.query_params.get('tipo')
        if tipo_filter:
            qs = qs.filter(tipo=tipo_filter)
        page, paginator = paginate_queryset(request, qs)
        if page is not None:
            return paginator.get_paginated_response(MovimentacaoFinanceiraSerializer(page, many=True).data)
        return Response(MovimentacaoFinanceiraSerializer(qs, many=True).data)

    data = request.data.copy()
    data['caso'] = str(case_id)
    serializer = MovimentacaoFinanceiraSerializer(data=data)
    if serializer.is_valid():
        mov = serializer.save(created_by=request.user)
        return Response(MovimentacaoFinanceiraSerializer(mov).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def movimentacao_detail(request, case_id, mov_id):
    """
    GET    /api/v1/processos/<case_id>/movimentacoes/<mov_id>/  — Detalhe
    PATCH  /api/v1/processos/<case_id>/movimentacoes/<mov_id>/  — Atualizar
    DELETE /api/v1/processos/<case_id>/movimentacoes/<mov_id>/  — Remover
    """
    try:
        mov = MovimentacaoFinanceira.objects.select_related('caso').get(id=mov_id, caso_id=case_id)
    except MovimentacaoFinanceira.DoesNotExist:
        return Response({'error': 'Movimentação não encontrada'}, status=status.HTTP_404_NOT_FOUND)

    if not check_object_permission(request.user, mov):
        return _deny()

    if request.method == 'GET':
        return Response(MovimentacaoFinanceiraSerializer(mov).data)

    if request.method == 'PATCH':
        serializer = MovimentacaoFinanceiraSerializer(mov, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    mov.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────────────────────────────────────
# NOTIFICAÇÕES JURÍDICAS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def case_notifications_list_create(request, case_id):
    """
    GET  /api/v1/processos/<case_id>/notificacoes/  — Lista notificações do caso
    POST /api/v1/processos/<case_id>/notificacoes/  — Registra notificação
    """
    try:
        caso = LegalCase.objects.select_related('advogado_responsavel', 'created_by').get(id=case_id)
    except LegalCase.DoesNotExist:
        return Response({'error': 'Caso não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    if not user_can_access_case(request.user, caso):
        return _deny()

    if request.method == 'GET':
        qs = LegalNotification.objects.filter(caso=caso)
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        tipo_filter = request.query_params.get('tipo')
        if tipo_filter:
            qs = qs.filter(tipo=tipo_filter)
        direcao_filter = request.query_params.get('direcao')
        if direcao_filter:
            qs = qs.filter(direcao=direcao_filter)
        page, paginator = paginate_queryset(request, qs)
        if page is not None:
            return paginator.get_paginated_response(LegalNotificationSerializer(page, many=True).data)
        return Response(LegalNotificationSerializer(qs, many=True).data)

    # POST
    data = request.data.copy()
    data['caso'] = str(case_id)
    serializer = LegalNotificationSerializer(data=data)
    if serializer.is_valid():
        notification = serializer.save(created_by=request.user)

        # Process: calculate deadline and auto-create LegalDeadline
        from apps.cases.services.notification_service import NotificationService
        notification = NotificationService.process_notification(notification, user=request.user)
        notification.save()

        return Response(LegalNotificationSerializer(notification).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def notification_detail(request, case_id, notif_id):
    """
    GET    /api/v1/processos/<case_id>/notificacoes/<notif_id>/  — Detalhe
    PATCH  /api/v1/processos/<case_id>/notificacoes/<notif_id>/  — Atualizar
    DELETE /api/v1/processos/<case_id>/notificacoes/<notif_id>/  — Remover
    """
    try:
        notification = LegalNotification.objects.select_related('caso', 'deadline_created').get(
            id=notif_id, caso_id=case_id
        )
    except LegalNotification.DoesNotExist:
        return Response({'error': 'Notificação não encontrada'}, status=status.HTTP_404_NOT_FOUND)

    if not check_object_permission(request.user, notification):
        return _deny()

    if request.method == 'GET':
        return Response(LegalNotificationSerializer(notification).data)

    if request.method == 'PATCH':
        serializer = LegalNotificationSerializer(notification, data=request.data, partial=True)
        if serializer.is_valid():
            notification = serializer.save()

            # Re-process if data_ciencia or data_publicacao_dje changed
            if 'data_ciencia' in request.data or 'data_publicacao_dje' in request.data:
                from apps.cases.services.notification_service import NotificationService
                notification = NotificationService.process_notification(notification, user=request.user)
                notification.save()

            return Response(LegalNotificationSerializer(notification).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE
    notification.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────────────────────────────────────
# STATS / DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cases_stats(request):
    """Estatísticas dos casos do usuário para o dashboard."""
    from django.utils import timezone

    if _is_privileged(request.user):
        casos_qs = LegalCase.objects.all()
        prazos_qs = LegalDeadline.objects.all()
    else:
        casos_qs = LegalCase.objects.filter(
            Q(advogado_responsavel=request.user) | Q(created_by=request.user)
        )
        prazos_qs = LegalDeadline.objects.filter(
            Q(caso__advogado_responsavel=request.user) |
            Q(caso__created_by=request.user) |
            Q(responsavel=request.user)
        )

    hoje = timezone.now().date()
    from datetime import timedelta
    proximos_7_dias = hoje + timedelta(days=7)

    return Response({
        'total_casos': casos_qs.count(),
        'casos_ativos': casos_qs.filter(status='ativo').count(),
        'casos_encerrados': casos_qs.filter(status__in=['encerrado', 'ganho', 'perdido', 'acordo']).count(),
        'casos_arquivados': casos_qs.filter(status='arquivado').count(),
        'casos_por_especialidade': dict(
            casos_qs.values('especialidade').annotate(n=Count('id')).values_list('especialidade', 'n')
        ),
        'prazos_pendentes': prazos_qs.filter(status='pendente').exclude(caso__status='arquivado').count(),
        'prazos_proximos_7_dias': prazos_qs.filter(
            status='pendente',
            data_prazo__gte=hoje,
            data_prazo__lte=proximos_7_dias,
        ).exclude(caso__status='arquivado').count(),
        'prazos_atrasados': prazos_qs.filter(
            status='pendente',
            data_prazo__lt=hoje,
        ).exclude(caso__status='arquivado').count(),
    })


# ─────────────────────────────────────────────────────────────────────────────
# ACTIVITY LOG
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def case_activity_log(request, case_id):
    """
    GET /api/v1/processos/<case_id>/atividades/
    Retorna os últimos 50 registros de auditoria associados ao caso.
    """
    # Verify case access
    try:
        caso = LegalCase.objects.select_related('advogado_responsavel', 'created_by').get(id=case_id)
    except LegalCase.DoesNotExist:
        return Response({'error': 'Caso não encontrado'}, status=status.HTTP_404_NOT_FOUND)
    if not user_can_access_case(request.user, caso):
        return _deny()

    qs = (
        AuditLog.objects
        .filter(entity_id=str(case_id))
        .order_by('-created_at')
    )
    page, paginator = paginate_queryset(request, qs)
    if page is not None:
        data = [
            {
                'id': str(log.id),
                'action': log.action,
                'severity': log.severity,
                'entity_type': log.entity_type,
                'entity_name': log.entity_name,
                'description': log.description,
                'user_email': log.user_email,
                'user_role': log.user_role,
                'created_at': log.created_at.isoformat(),
                'metadata': log.metadata,
            }
            for log in page
        ]
        return paginator.get_paginated_response(data)
    data = [
        {
            'id': str(log.id),
            'action': log.action,
            'severity': log.severity,
            'entity_type': log.entity_type,
            'entity_name': log.entity_name,
            'description': log.description,
            'user_email': log.user_email,
            'user_role': log.user_role,
            'created_at': log.created_at.isoformat(),
            'metadata': log.metadata,
        }
        for log in qs
    ]
    return Response(data)


# ─────────────────────────────────────────────────────────────────────────────
# APRIMORAMENTO DE TEXTO COM IA
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIGenerationThrottle])
def enhance_case_text(request):
    """
    POST /api/v1/processos/enhance-text/
    Aprimora o texto de um campo (descricao ou observacoes) com linguagem jurídica.
    """
    field = request.data.get('field', '')
    text = request.data.get('text', '').strip()
    context = request.data.get('context', {})

    if not field or field not in ('descricao', 'observacoes'):
        return Response(
            {'error': 'Campo inválido. Use "descricao" ou "observacoes".'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not text:
        return Response(
            {'error': 'O campo "text" não pode estar vazio.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    field_label = 'Descrição do Caso' if field == 'descricao' else 'Observações Internas'

    # Montar contexto do caso
    context_lines = []
    if context.get('titulo'):
        context_lines.append(f"Título: {context['titulo']}")
    if context.get('cliente_nome'):
        context_lines.append(f"Cliente: {context['cliente_nome']}")
    if context.get('especialidade'):
        context_lines.append(f"Especialidade: {context['especialidade']}")
    if context.get('tribunal'):
        context_lines.append(f"Tribunal: {context['tribunal']}")
    if context.get('parte_contraria'):
        context_lines.append(f"Parte Contrária: {context['parte_contraria']}")

    context_str = '\n'.join(context_lines) if context_lines else 'Não informado'

    system_prompt = (
        "Você é um advogado especialista em direito brasileiro com vasta experiência em "
        "redação jurídica. Seu papel é aprimorar textos jurídicos mantendo todos os fatos "
        "essenciais, mas melhorando a clareza, precisão terminológica e formalidade da "
        "linguagem. Preserve nomes, datas, valores e referências legais. "
        "Retorne APENAS o texto aprimorado, sem explicações, prefácios ou marcações extras."
    )

    user_prompt = (
        f"Contexto do caso:\n{context_str}\n\n"
        f"Campo a aprimorar ({field_label}):\n{text}"
    )

    try:
        llm_service = UnifiedLLMService()
        result = llm_service.generate(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            provider='watsonx',
            model='mistralai/mistral-medium-2505',
            temperature=0.4,
            max_tokens=2048,
            user=request.user if request.user.is_authenticated else None,
            usage_type='copilot',
            description=f'Aprimoramento de texto do caso ({field_label})',
        )
        enhanced_text = result.get('content', '').strip()
        if not enhanced_text:
            return Response(
                {'error': 'A IA não retornou conteúdo. Tente novamente.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({'enhanced_text': enhanced_text})
    except Exception as exc:
        logger.error(f"[enhance_case_text] Erro: {exc}", exc_info=True)
        return Response(
            {'error': 'Erro ao processar com IA. Tente novamente em instantes.'},
            status=status.HTTP_502_BAD_GATEWAY,
        )


# ─────────────────────────────────────────────────────────────────────────────
# EXTRAÇÃO DE DADOS DO CASO COM IA
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIGenerationThrottle])
def extract_case_data(request):
    """
    POST /api/v1/processos/extract-case-data/
    Extrai dados estruturados de um texto de petição inicial ou documento processual.

    Body:
      - text (str, required): texto do documento (petição inicial, etc.)

    Returns JSON com campos extraídos:
      - titulo, numero_processo, especialidade, cliente_nome, parte_contraria,
        tribunal, comarca, vara_juizo, valor_causa, estado
    """
    import json as json_module

    text = request.data.get('text', '').strip()

    if not text:
        return Response(
            {'error': 'O campo "text" não pode estar vazio.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(text) < 50:
        return Response(
            {'error': 'Texto muito curto para extração. Cole o conteúdo completo da petição.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    system_prompt = (
        "Você é um assistente jurídico especializado em extrair dados estruturados de "
        "documentos processuais brasileiros (petições iniciais, decisões, intimações, etc).\n\n"
        "Analise o texto fornecido e extraia os seguintes campos. Se um campo não puder ser "
        "identificado no texto, retorne string vazia para ele.\n\n"
        "Retorne APENAS um JSON válido (sem markdown, sem explicações) com exatamente estas chaves:\n"
        "{\n"
        '  "titulo": "título/assunto resumido do caso (ex: Ação de Indenização por Danos Morais)",\n'
        '  "numero_processo": "número do processo no formato CNJ (apenas dígitos, sem formatação)",\n'
        '  "especialidade": "uma das opções: civel, criminal, trabalhista, tributario, administrativo, '
        'previdenciario, familia, empresarial, ambiental, consumidor, imobiliario, outros",\n'
        '  "cliente_nome": "nome do autor/requerente",\n'
        '  "parte_contraria": "nome do réu/requerido",\n'
        '  "tribunal": "sigla do tribunal (ex: TJSP, TRT-2, STJ)",\n'
        '  "comarca": "nome da comarca",\n'
        '  "vara_juizo": "vara ou juízo (ex: 3ª Vara Cível)",\n'
        '  "valor_causa": "valor da causa como número (ex: 50000.00)",\n'
        '  "estado": "UF do estado (ex: SP, RJ, MG)"\n'
        "}"
    )

    user_prompt = f"TEXTO DO DOCUMENTO:\n\n{text[:8000]}"

    try:
        llm_service = UnifiedLLMService()
        result = llm_service.generate(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            provider='watsonx',
            model='mistralai/mistral-medium-2505',
            temperature=0.1,
            max_tokens=1024,
            user=request.user if request.user.is_authenticated else None,
            usage_type='analysis',
            description='Extração de dados do caso',
        )
        content = result.get('content', '').strip()

        if not content:
            return Response(
                {'error': 'A IA não retornou conteúdo. Tente novamente.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Tentar parsear JSON — a LLM pode retornar com blocos markdown
        json_str = content
        if '```json' in json_str:
            json_str = json_str.split('```json')[1].split('```')[0]
        elif '```' in json_str:
            json_str = json_str.split('```')[1].split('```')[0]

        try:
            extracted = json_module.loads(json_str.strip())
        except json_module.JSONDecodeError:
            logger.warning(f"[extract_case_data] JSON inválido da LLM: {content[:500]}")
            return Response(
                {'error': 'A IA retornou dados em formato inválido. Tente novamente.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Garantir que todas as chaves existem
        fields = [
            'titulo', 'numero_processo', 'especialidade', 'cliente_nome',
            'parte_contraria', 'tribunal', 'comarca', 'vara_juizo',
            'valor_causa', 'estado',
        ]
        result_data = {f: extracted.get(f, '') for f in fields}

        # Validar especialidade — garantir valor aceito pelo model
        valid_especialidades = [
            'civel', 'criminal', 'trabalhista', 'tributario', 'administrativo',
            'previdenciario', 'familia', 'empresarial', 'ambiental',
            'consumidor', 'imobiliario', 'outros',
        ]
        if result_data['especialidade'] not in valid_especialidades:
            result_data['especialidade'] = ''

        # Validar estado
        valid_states = [
            'AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
            'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN',
            'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO',
        ]
        if result_data['estado'] not in valid_states:
            result_data['estado'] = ''

        return Response(result_data)

    except Exception as exc:
        logger.error(f"[extract_case_data] Erro: {exc}", exc_info=True)
        return Response(
            {'error': 'Erro ao processar com IA. Tente novamente em instantes.'},
            status=status.HTTP_502_BAD_GATEWAY,
        )


# ─────────────────────────────────────────────────────────────────────────────
# EXTRAÇÃO DE DADOS DO CASO A PARTIR DE ARQUIVO (PDF/DOCX/ODT/TXT)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIGenerationThrottle])
def extract_case_from_document(request):
    """
    POST /api/v1/processos/extract-from-document/
    Extrai dados estruturados de caso a partir de documento PDF/DOCX/ODT/TXT anexado.

    Body (multipart/form-data):
      - file (File, required): arquivo do documento

    Returns JSON com campos extraídos incluindo prazos identificados.
    """
    import json as json_module

    file = request.FILES.get('file')
    if not file:
        return Response(
            {'error': 'Nenhum arquivo enviado.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validar extensão
    file_name = file.name.lower()
    allowed_extensions = ('.pdf', '.docx', '.doc', '.odt', '.txt')
    if not any(file_name.endswith(ext) for ext in allowed_extensions):
        return Response(
            {'error': f'Formato não suportado. Use: {", ".join(allowed_extensions)}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Extrair texto do arquivo usando o serviço da KB
    try:
        from apps.kb.services import DocumentProcessingService

        file_content = file.read()
        # Determinar tipo pelo nome do arquivo
        if file_name.endswith('.pdf'):
            file_type = 'pdf'
        elif file_name.endswith('.docx') or file_name.endswith('.doc'):
            file_type = 'docx'
        elif file_name.endswith('.odt'):
            file_type = 'odt'
        else:
            file_type = 'txt'

        text = DocumentProcessingService.extract_text_from_bytes(file_content, file_type)
    except Exception as exc:
        logger.error(f"[extract_case_from_document] Erro na extração de texto: {exc}", exc_info=True)
        return Response(
            {'error': 'Não foi possível extrair texto do documento. Verifique se o arquivo não está corrompido.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not text or len(text.strip()) < 50:
        return Response(
            {'error': 'Texto extraído muito curto. Verifique se o documento possui conteúdo legível.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Usar LLM para extrair dados estruturados
    system_prompt = (
        "Você é um assistente jurídico especializado em extrair dados estruturados de "
        "documentos processuais brasileiros (petições iniciais, citações, intimações, decisões, etc).\n\n"
        "Analise o texto fornecido e extraia TODOS os dados possíveis. Se um campo não puder ser "
        "identificado no texto, retorne string vazia para ele.\n\n"
        "Retorne APENAS um JSON válido (sem markdown, sem explicações) com exatamente estas chaves:\n"
        "{\n"
        '  "titulo": "título descritivo do caso",\n'
        '  "numero_processo": "número do processo no formato CNJ (apenas dígitos)",\n'
        '  "especialidade": "uma das opções: civel, criminal, trabalhista, tributario, administrativo, '
        'previdenciario, familia, empresarial, ambiental, consumidor, imobiliario, outros",\n'
        '  "descricao": "descrição detalhada do caso com fatos relevantes",\n'
        '  "observacoes": "observações adicionais importantes encontradas",\n'
        '  "cliente_nome": "nome do autor/requerente/parte representada",\n'
        '  "cliente_documento": "CPF ou CNPJ do cliente",\n'
        '  "parte_contraria": "nome do réu/requerido",\n'
        '  "parte_contraria_documento": "CPF ou CNPJ da parte contrária",\n'
        '  "tribunal": "sigla do tribunal (ex: TJSP, TRT-2, STJ)",\n'
        '  "comarca": "nome da comarca",\n'
        '  "vara_juizo": "vara e juízo (ex: 3ª Vara Cível)",\n'
        '  "estado": "UF de 2 letras",\n'
        '  "valor_causa": "valor da causa como número decimal (ex: 50000.00)",\n'
        '  "data_distribuicao": "data de distribuição no formato YYYY-MM-DD",\n'
        '  "advogado_autor": "nome do advogado do autor",\n'
        '  "oab_autor": "número OAB do advogado do autor",\n'
        '  "advogado_reu": "nome do advogado do réu",\n'
        '  "oab_reu": "número OAB do advogado do réu",\n'
        '  "prazos_identificados": [\n'
        '    {"tipo": "contestação|recurso|manifestação|etc", "prazo_dias": 15, '
        '"descricao": "descrição do prazo", "data_inicio": "YYYY-MM-DD"}\n'
        '  ]\n'
        "}"
    )

    # Limitar texto para evitar excesso de tokens
    user_prompt = f"TEXTO DO DOCUMENTO:\n\n{text[:12000]}"

    try:
        llm_service = UnifiedLLMService()
        result = llm_service.generate(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            provider='watsonx',
            model='mistralai/mistral-medium-2505',
            temperature=0.1,
            max_tokens=2048,
            user=request.user if request.user.is_authenticated else None,
            usage_type='analysis',
            description='Extracao de dados de documento',
        )
        content = result.get('content', '').strip()

        if not content:
            return Response(
                {'error': 'A IA não retornou conteúdo. Tente novamente.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Parsear JSON — a LLM pode retornar com blocos markdown
        json_str = content
        if '```json' in json_str:
            json_str = json_str.split('```json')[1].split('```')[0]
        elif '```' in json_str:
            json_str = json_str.split('```')[1].split('```')[0]

        try:
            extracted = json_module.loads(json_str.strip())
        except json_module.JSONDecodeError:
            logger.warning(f"[extract_case_from_document] JSON inválido da LLM: {content[:500]}")
            return Response(
                {'error': 'A IA retornou dados em formato inválido. Tente novamente.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Normalizar resposta
        fields = [
            'titulo', 'numero_processo', 'especialidade', 'descricao',
            'observacoes', 'cliente_nome', 'cliente_documento',
            'parte_contraria', 'parte_contraria_documento',
            'tribunal', 'comarca', 'vara_juizo', 'estado',
            'valor_causa', 'data_distribuicao',
            'advogado_autor', 'oab_autor', 'advogado_reu', 'oab_reu',
        ]
        result_data = {f: extracted.get(f, '') for f in fields}

        # Prazos identificados (lista)
        result_data['prazos_identificados'] = extracted.get('prazos_identificados', [])
        if not isinstance(result_data['prazos_identificados'], list):
            result_data['prazos_identificados'] = []

        # Validar especialidade
        valid_especialidades = [
            'civel', 'criminal', 'trabalhista', 'tributario', 'administrativo',
            'previdenciario', 'familia', 'empresarial', 'ambiental',
            'consumidor', 'imobiliario', 'outros',
        ]
        if result_data['especialidade'] not in valid_especialidades:
            result_data['especialidade'] = ''

        # Validar estado
        valid_states = [
            'AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
            'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN',
            'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO',
        ]
        if result_data['estado'] not in valid_states:
            result_data['estado'] = ''

        return Response(result_data)

    except Exception as exc:
        logger.error(f"[extract_case_from_document] Erro: {exc}", exc_info=True)
        return Response(
            {'error': 'Erro ao processar com IA. Tente novamente em instantes.'},
            status=status.HTTP_502_BAD_GATEWAY,
        )


# ─────────────────────────────────────────────────────────────────────────────
# TIMELINE DO CASO
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def case_timeline(request, case_id):
    """
    GET /api/v1/processos/<case_id>/timeline/
    Retorna todos os eventos vinculados ao caso em ordem cronológica reversa.
    Inclui: documentos gerados, simulações, prazos, tarefas, audiências, documentos do caso.
    """
    from django.utils import timezone as tz

    try:
        caso = LegalCase.objects.select_related('advogado_responsavel', 'created_by').get(id=case_id)
    except LegalCase.DoesNotExist:
        return Response({'error': 'Caso não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    if not user_can_access_case(request.user, caso):
        return _deny()

    events = []

    # 1. Documentos gerados (via IntelligentSession)
    sessions = IntelligentSession.objects.filter(case_id=case_id).select_related('blueprint')
    for session in sessions:
        docs = GeneratedDocument.objects.filter(session=session)
        for doc in docs:
            events.append({
                'type': 'documento_gerado',
                'icon': 'file-text',
                'title': doc.title or session.document_type_display,
                'description': f'Documento gerado via Assistente Inteligente',
                'date': doc.generated_at.isoformat(),
                'metadata': {
                    'session_id': str(session.id),
                    'document_id': str(doc.id),
                    'document_type': session.document_type,
                    'status': session.status,
                },
            })

    # 2. Simulações vinculadas
    simulations = Simulation.objects.filter(case_id=case_id)
    for sim in simulations:
        events.append({
            'type': 'simulacao',
            'icon': 'scale',
            'title': sim.title,
            'description': f'{sim.get_simulation_type_display()} — {sim.get_status_display()}',
            'date': sim.created_at.isoformat(),
            'metadata': {
                'simulation_id': str(sim.id),
                'simulation_type': sim.simulation_type,
                'status': sim.status,
            },
        })

    # 3. Documentos do caso (CaseDocument)
    case_docs = CaseDocument.objects.filter(caso_id=case_id)
    for cd in case_docs:
        events.append({
            'type': 'documento_caso',
            'icon': 'paperclip',
            'title': cd.titulo,
            'description': cd.get_tipo_display(),
            'date': cd.created_at.isoformat(),
            'metadata': {
                'case_document_id': str(cd.id),
                'tipo': cd.tipo,
            },
        })

    # 4. Prazos
    prazos = LegalDeadline.objects.filter(caso_id=case_id)
    for prazo in prazos:
        events.append({
            'type': 'prazo',
            'icon': 'clock',
            'title': prazo.titulo,
            'description': f'{prazo.get_tipo_display()} — {prazo.get_status_display()}',
            'date': prazo.created_at.isoformat(),
            'metadata': {
                'prazo_id': str(prazo.id),
                'data_prazo': prazo.data_prazo.isoformat(),
                'status': prazo.status,
                'prioridade': prazo.prioridade,
            },
        })

    # 5. Tarefas
    tarefas = CaseTask.objects.filter(caso_id=case_id)
    for tarefa in tarefas:
        events.append({
            'type': 'tarefa',
            'icon': 'check-circle',
            'title': tarefa.titulo,
            'description': f'{tarefa.get_status_display()} — {tarefa.get_prioridade_display()}',
            'date': tarefa.created_at.isoformat(),
            'metadata': {
                'tarefa_id': str(tarefa.id),
                'status': tarefa.status,
            },
        })

    # 6. Audiências
    audiencias = Audiencia.objects.filter(caso_id=case_id)
    for aud in audiencias:
        events.append({
            'type': 'audiencia',
            'icon': 'gavel',
            'title': f'{aud.get_tipo_display()}',
            'description': f'{aud.get_status_display()} — {aud.data_hora.strftime("%d/%m/%Y %H:%M")}',
            'date': aud.created_at.isoformat(),
            'metadata': {
                'audiencia_id': str(aud.id),
                'data_hora': aud.data_hora.isoformat(),
                'status': aud.status,
            },
        })

    # 7. Notificações jurídicas
    notificacoes = LegalNotification.objects.filter(caso_id=case_id)
    for notif in notificacoes:
        direcao_icon = 'mail' if notif.direcao == 'recebida' else 'send'
        events.append({
            'type': 'notificacao',
            'icon': direcao_icon,
            'title': notif.get_tipo_display(),
            'description': (
                f'{notif.get_direcao_display()} — {notif.get_status_display()}'
                + (f' — Prazo: {notif.prazo_vencimento.strftime("%d/%m/%Y")}' if notif.prazo_vencimento else '')
            ),
            'date': notif.created_at.isoformat(),
            'metadata': {
                'notificacao_id': str(notif.id),
                'tipo': notif.tipo,
                'direcao': notif.direcao,
                'status': notif.status,
                'prazo_vencimento': notif.prazo_vencimento.isoformat() if notif.prazo_vencimento else None,
            },
        })

    # Sort by date descending
    events.sort(key=lambda e: e['date'], reverse=True)

    page, paginator = paginate_queryset(request, events)
    if page is not None:
        return paginator.get_paginated_response(page)
    return Response(events)


# ─────────────────────────────────────────────────────────────────────────────
# VINCULAR DOCUMENTO GERADO AO CASO
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def link_document_to_case(request):
    """
    POST /api/v1/processos/link-document/
    Vincula um documento gerado (GeneratedDocument) ou sessão a um caso.

    Body:
      - case_id (UUID, required)
      - session_id (UUID, required) — IntelligentSession
      - document_id (UUID, optional) — GeneratedDocument specific
      - titulo (str, optional) — override title
    """
    case_id = request.data.get('case_id')
    session_id = request.data.get('session_id')
    document_id = request.data.get('document_id')
    titulo = request.data.get('titulo', '')

    if not case_id or not session_id:
        return Response(
            {'error': 'case_id e session_id são obrigatórios.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        caso = LegalCase.objects.get(id=case_id)
    except LegalCase.DoesNotExist:
        return Response({'error': 'Caso não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        session = IntelligentSession.objects.get(id=session_id)
    except IntelligentSession.DoesNotExist:
        return Response({'error': 'Sessão não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

    # Update session's case FK
    session.case = caso
    session.save(update_fields=['case'])

    # Find the generated document
    gen_doc = None
    if document_id:
        try:
            gen_doc = GeneratedDocument.objects.get(id=document_id)
        except GeneratedDocument.DoesNotExist:
            pass
    else:
        gen_doc = GeneratedDocument.objects.filter(session=session).order_by('-generated_at').first()

    # Create CaseDocument record
    doc_title = titulo or (gen_doc.title if gen_doc and gen_doc.title else session.document_type_display)
    case_doc = CaseDocument.objects.create(
        caso=caso,
        titulo=doc_title,
        tipo='peca',
        descricao=f'Documento gerado via Assistente Inteligente — {session.document_type_display}',
        data_documento=session.created_at.date(),
        generated_document_id=gen_doc.id if gen_doc else None,
        linked_document=gen_doc,
        created_by=request.user,
    )

    return Response({
        'status': 'linked',
        'case_document_id': str(case_doc.id),
        'case_id': str(caso.id),
        'case_titulo': caso.titulo,
    }, status=status.HTTP_201_CREATED)


# ─────────────────────────────────────────────────────────────────────────────
# FASES PROCESSUAIS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def case_phases_list(request, case_id):
    """
    GET /api/v1/processos/<case_id>/phases/
    Lista todas as fases processuais de um caso.
    """
    try:
        caso = LegalCase.objects.select_related('advogado_responsavel', 'created_by').get(id=case_id)
    except LegalCase.DoesNotExist:
        return Response({'error': 'Caso não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    if not user_can_access_case(request.user, caso):
        return _deny()

    phases = CasePhase.objects.filter(caso=caso).order_by('order')

    # Se o caso não tem fases, gera automaticamente
    if not phases.exists():
        try:
            from apps.cases.services.case_phases import create_phases_for_case
            create_phases_for_case(caso)
            phases = CasePhase.objects.filter(caso=caso).order_by('order')
        except Exception as exc:
            logger.error(f"[case_phases_list] Erro ao gerar fases: {exc}", exc_info=True)
            return Response(
                {'error': 'Erro ao gerar fases processuais.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # Auto-detect overdue phases
    from django.utils import timezone
    today = timezone.now().date()
    for phase in phases:
        if phase.status in ('in_progress', 'pending') and phase.estimated_date and phase.estimated_date < today:
            phase.status = 'overdue'
            phase.overdue_since = phase.overdue_since or phase.estimated_date
            phase.save(update_fields=['status', 'overdue_since'])

    serializer = CasePhaseSerializer(phases, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def case_phase_update(request, case_id, phase_id):
    """
    PATCH /api/v1/processos/<case_id>/phases/<phase_id>/
    Atualiza status, notas ou datas de uma fase processual.
    """
    try:
        phase = CasePhase.objects.select_related('caso__advogado_responsavel', 'caso__created_by').get(id=phase_id, caso_id=case_id)
    except CasePhase.DoesNotExist:
        return Response({'error': 'Fase não encontrada'}, status=status.HTTP_404_NOT_FOUND)

    if not user_can_access_case(request.user, phase.caso):
        return _deny()

    from django.utils import timezone

    new_status = request.data.get('status')
    old_status = phase.status

    # Reopening: completed -> in_progress requires justification
    if old_status == 'completed' and new_status == 'in_progress':
        reopened_reason = request.data.get('reopened_reason', '').strip()
        if not reopened_reason:
            return Response(
                {'error': 'Informe o motivo da reabertura desta etapa'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    serializer = CasePhaseSerializer(phase, data=request.data, partial=True)
    if serializer.is_valid():
        new_status = serializer.validated_data.get('status')

        # Reopening: completed -> in_progress
        if old_status == 'completed' and new_status == 'in_progress':
            serializer.validated_data['reopened_at'] = timezone.now()
            serializer.validated_data['reopened_reason'] = request.data.get('reopened_reason', '').strip()
            serializer.validated_data['actual_date'] = None

        # Completing a phase
        if new_status == 'completed':
            today = timezone.now().date()
            serializer.validated_data['actual_date'] = today
            # If completing an overdue phase, add note about delay
            if old_status == 'overdue' and phase.estimated_date:
                days_late = (today - phase.estimated_date).days
                delay_note = f"Concluída com atraso de {days_late} dias"
                existing_notes = serializer.validated_data.get('notes', phase.notes) or ''
                if delay_note not in existing_notes:
                    serializer.validated_data['notes'] = f"{existing_notes}\n{delay_note}".strip()

        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────────────────────────
# PRAZOS RECURSAIS (#6)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calcular_prazo_recursal(request):
    """
    POST /api/v1/processos/prazos/calcular-recursal/
    Calcula o prazo final de um recurso a partir do tipo e data de intimação.

    Body:
      - appeal_type (str, required): chave do tipo de recurso
      - intimation_date (str, required): data de intimação (YYYY-MM-DD)
      - caso_id (UUID, optional): ID do caso para salvar o prazo

    Returns:
      - deadline_date, dias, base_legal, descricao, intimation_date
    """
    from datetime import datetime
    from apps.cases.services.appeal_deadline_calculator import AppealDeadlineCalculator

    appeal_type = request.data.get('appeal_type', '').strip()
    intimation_date_str = request.data.get('intimation_date', '').strip()
    caso_id = request.data.get('caso_id')

    if not appeal_type:
        return Response({'error': 'appeal_type é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
    if not intimation_date_str:
        return Response({'error': 'intimation_date é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        intimation_date = datetime.strptime(intimation_date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({'error': 'intimation_date deve estar no formato YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        result = AppealDeadlineCalculator.calculate_deadline(appeal_type, intimation_date)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    response_data = {
        'appeal_type': result['appeal_type'],
        'deadline_date': result['deadline_date'].isoformat(),
        'dias': result['dias'],
        'base_legal': result['base_legal'],
        'descricao': result['descricao'],
        'intimation_date': result['intimation_date'].isoformat(),
    }

    # Se caso_id fornecido, salvar como LegalDeadline
    if caso_id:
        try:
            caso = LegalCase.objects.get(id=caso_id)
        except LegalCase.DoesNotExist:
            return Response({'error': 'Caso não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        prazo = LegalDeadline.objects.create(
            caso=caso,
            titulo=f"Prazo — {result['descricao']}",
            descricao=f"Prazo recursal. Base legal: {result['base_legal']}. "
                      f"{result['dias']} dias úteis a partir de {intimation_date.strftime('%d/%m/%Y')}.",
            tipo='recursal',
            prioridade='alta',
            data_prazo=result['deadline_date'],
            appeal_type=appeal_type,
            base_legal=result['base_legal'],
            auto_generated=False,
            created_by=request.user,
        )
        response_data['prazo_id'] = str(prazo.id)
        response_data['saved'] = True

    return Response(response_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tipos_recurso_list(request):
    """
    GET /api/v1/processos/prazos/tipos-recurso/
    Retorna todos os tipos de recurso com dias e base legal.
    """
    from apps.cases.services.appeal_deadline_calculator import AppealDeadlineCalculator

    tipos = AppealDeadlineCalculator.get_all_types()
    return Response(tipos)


# ─────────────────────────────────────────────────────────────────────────────
# CHECKLIST POR TIPO DE ACAO (#14)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def case_checklist(request, case_id):
    """
    GET  /api/v1/processos/<case_id>/checklist/  — Preview do checklist
    POST /api/v1/processos/<case_id>/checklist/  — Cria tarefas a partir do checklist
    """
    from apps.cases.services.checklist_service import ChecklistService

    try:
        caso = LegalCase.objects.select_related('advogado_responsavel', 'created_by').get(id=case_id)
    except LegalCase.DoesNotExist:
        return Response({'error': 'Caso não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    if not user_can_access_case(request.user, caso):
        return _deny()

    if request.method == 'GET':
        checklist = ChecklistService.preview_checklist(caso.especialidade)
        return Response({
            'especialidade': caso.especialidade,
            'checklist': checklist,
        })

    # POST — criar tarefas
    tasks = ChecklistService.create_checklist_for_case(caso, user=request.user)
    serializer = CaseTaskSerializer(tasks, many=True)
    return Response({
        'created': len(tasks),
        'tasks': serializer.data,
    }, status=status.HTTP_201_CREATED)


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD FINANCEIRO
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def financial_dashboard(request):
    """
    GET /api/v1/processos/financeiro/dashboard/
    Retorna KPIs, gráficos de receita/despesa, tabelas por cliente e advogado.

    Query params:
      - period: 'month' | 'quarter' | 'year' (default: 'month')
      - start: YYYY-MM-DD (overrides period)
      - end: YYYY-MM-DD   (overrides period)
    """
    from datetime import timedelta
    from apps.cases.services.financial_service import FinancialService

    today = timezone.now().date()
    period = request.query_params.get('period', 'month')

    start_param = request.query_params.get('start')
    end_param = request.query_params.get('end')

    if start_param and end_param:
        try:
            from datetime import date as date_cls
            parts_s = start_param.split('-')
            start = date_cls(int(parts_s[0]), int(parts_s[1]), int(parts_s[2]))
            parts_e = end_param.split('-')
            end = date_cls(int(parts_e[0]), int(parts_e[1]), int(parts_e[2]))
        except (ValueError, IndexError):
            return Response(
                {'error': 'Datas inválidas. Use formato YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
    else:
        if period == 'quarter':
            start = today - timedelta(days=90)
        elif period == 'year':
            start = today - timedelta(days=365)
        else:  # month
            start = today - timedelta(days=30)
        end = today

    try:
        kpis = FinancialService.kpi_summary()
        revenue_chart = FinancialService.revenue_by_period(start, end)
        expense_chart = FinancialService.expenses_by_period(start, end)
        by_client = FinancialService.revenue_by_client(start, end)
        by_lawyer = FinancialService.revenue_by_lawyer(start, end)

        return Response({
            'kpis': kpis,
            'revenue_chart': revenue_chart,
            'expense_chart': expense_chart,
            'by_client': by_client,
            'by_lawyer': by_lawyer,
            'period': {
                'start': start.isoformat(),
                'end': end.isoformat(),
                'label': period,
            },
        })
    except Exception as exc:
        logger.error(f"[financial_dashboard] Erro: {exc}", exc_info=True)
        return Response(
            {'error': 'Erro ao carregar dashboard financeiro.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ─────────────────────────────────────────────────────────────────────────────
# TABELA OAB DE HONORÁRIOS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def oab_fee_table_list(request):
    """
    GET /api/v1/processos/honorarios/tabela/
    Lista tabela OAB com filtros de estado e categoria.

    Query params:
      - state: UF (ex: SP)
      - category: civel, criminal, etc.
      - year: 2024
    """
    qs = OABFeeTable.objects.all()

    state = request.query_params.get('state')
    if state:
        qs = qs.filter(state=state.upper())

    category = request.query_params.get('category')
    if category:
        qs = qs.filter(service_category=category)

    year = request.query_params.get('year')
    if year:
        try:
            qs = qs.filter(year=int(year))
        except ValueError:
            pass

    _fields = (
        'id', 'state', 'service_category', 'service_type',
        'minimum_value', 'suggested_value', 'percentage', 'year',
    )
    available_states = sorted(
        OABFeeTable.objects.values_list('state', flat=True).distinct()
    )
    available_categories = sorted(
        OABFeeTable.objects.values_list('service_category', flat=True).distinct()
    )

    page, paginator = paginate_queryset(request, qs)
    if page is not None:
        results = [
            {f: getattr(obj, f) for f in _fields}
            for obj in page
        ]
        resp = paginator.get_paginated_response(results)
        resp.data['available_states'] = available_states
        resp.data['available_categories'] = available_categories
        return resp

    data = list(qs.values(
        'id', 'state', 'service_category', 'service_type',
        'minimum_value', 'suggested_value', 'percentage', 'year',
    ))
    return Response({
        'count': len(data),
        'results': data,
        'available_states': sorted(
            OABFeeTable.objects.values_list('state', flat=True).distinct()
        ),
        'available_categories': sorted(
            OABFeeTable.objects.values_list('service_category', flat=True).distinct()
        ),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def oab_fee_calculate(request):
    """
    POST /api/v1/processos/honorarios/calcular/
    Calcula honorários com base na tabela OAB.

    Body:
      - fee_id: UUID da entrada na tabela OAB
      - valor_causa: Decimal — valor da causa para calcular percentual
    """
    from decimal import Decimal, InvalidOperation

    fee_id = request.data.get('fee_id')
    valor_causa_str = request.data.get('valor_causa', '0')

    if not fee_id:
        return Response(
            {'error': 'fee_id é obrigatório.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        fee = OABFeeTable.objects.get(id=fee_id)
    except OABFeeTable.DoesNotExist:
        return Response(
            {'error': 'Entrada da tabela OAB não encontrada.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        valor_causa = Decimal(str(valor_causa_str))
    except (InvalidOperation, ValueError):
        valor_causa = Decimal('0')

    result = {
        'service_type': fee.service_type,
        'state': fee.state,
        'category': fee.service_category,
        'minimum_value': str(fee.minimum_value or 0),
        'suggested_value': str(fee.suggested_value or 0),
        'percentage': str(fee.percentage or 0),
        'valor_causa': str(valor_causa),
    }

    # Calcular valor por percentual se disponível
    if fee.percentage and valor_causa > 0:
        calculated = (fee.percentage / Decimal('100')) * valor_causa
        result['calculated_by_percentage'] = str(calculated.quantize(Decimal('0.01')))
    else:
        result['calculated_by_percentage'] = '0.00'

    # Valor recomendado: maior entre mínimo e percentual
    values = []
    if fee.minimum_value:
        values.append(fee.minimum_value)
    if fee.percentage and valor_causa > 0:
        values.append((fee.percentage / Decimal('100')) * valor_causa)
    result['recommended_value'] = str(
        max(values).quantize(Decimal('0.01')) if values else Decimal('0')
    )

    return Response(result)


# ─────────────────────────────────────────────────────────────────────────────
# PROTOCOLO ELETRÔNICO
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def protocols_list_create(request):
    """
    GET  /api/v1/processos/protocolos/        — Lista protocolos
    POST /api/v1/processos/protocolos/        — Cria protocolo (rascunho)
    """
    if request.method == 'GET':
        qs = ElectronicProtocol.objects.select_related('case', 'created_by').all()

        if not _is_privileged(request.user):
            qs = qs.filter(
                Q(created_by=request.user) |
                Q(case__advogado_responsavel=request.user) |
                Q(case__created_by=request.user)
            )

        # Filtros
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        court_system = request.query_params.get('court_system')
        if court_system:
            qs = qs.filter(court_system=court_system)

        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(protocol_number__icontains=search) |
                Q(petition_type__icontains=search) |
                Q(case__titulo__icontains=search) |
                Q(case__numero_processo__icontains=search)
            )

        # Paginação
        try:
            page_size = int(request.query_params.get('page_size', 20))
            page = int(request.query_params.get('page', 1))
        except (ValueError, TypeError):
            page_size = 20
            page = 1
        offset = (page - 1) * page_size

        total = qs.count()
        protocols = qs[offset:offset + page_size]
        serializer = ElectronicProtocolSerializer(protocols, many=True)
        return Response({
            'count': total,
            'results': serializer.data,
        })

    # POST
    serializer = ElectronicProtocolSerializer(data=request.data)
    if serializer.is_valid():
        protocol = serializer.save(created_by=request.user, status='draft')
        return Response(
            ElectronicProtocolSerializer(protocol).data,
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protocol_detail(request, protocol_id):
    """GET /api/v1/processos/protocolos/<id>/"""
    try:
        protocol = ElectronicProtocol.objects.select_related('case', 'document', 'created_by').get(id=protocol_id)
    except ElectronicProtocol.DoesNotExist:
        return Response({'error': 'Protocolo não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    if not check_object_permission(request.user, protocol):
        return _deny()

    return Response(ElectronicProtocolSerializer(protocol).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([ProtocolSubmitThrottle])
def protocol_submit(request, protocol_id):
    """POST /api/v1/processos/protocolos/<id>/submit/"""
    from apps.cases.services.protocol_service import ProtocolService

    # Permission check: load protocol first
    try:
        protocol_obj = ElectronicProtocol.objects.select_related('case', 'created_by').get(id=protocol_id)
    except ElectronicProtocol.DoesNotExist:
        return Response({'error': 'Protocolo não encontrado'}, status=status.HTTP_404_NOT_FOUND)
    if not check_object_permission(request.user, protocol_obj):
        return _deny()

    try:
        protocol = ProtocolService.submit_protocol(protocol_id)
        return Response(ElectronicProtocolSerializer(protocol).data)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def protocol_check_status(request, protocol_id):
    """POST /api/v1/processos/protocolos/<id>/check-status/"""
    from apps.cases.services.protocol_service import ProtocolService

    try:
        protocol = ProtocolService.check_protocol_status(protocol_id)
        return Response(ElectronicProtocolSerializer(protocol).data)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protocol_statistics(request):
    """GET /api/v1/processos/protocolos/statistics/"""
    from apps.cases.services.protocol_service import ProtocolService

    stats = ProtocolService.get_protocol_statistics(request.user)
    return Response(stats)


# ─────────────────────────────────────────────────────────────────────────────
# TRIBUNAL PUSH — CONFIGURAÇÃO
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def tribunal_push_configs_list_create(request):
    """
    GET  /api/v1/processos/tribunal-push/configs/  — Lista configs do usuário
    POST /api/v1/processos/tribunal-push/configs/  — Cria nova config
    """
    if request.method == 'GET':
        qs = TribunalPushConfig.objects.filter(user=request.user)
        serializer = TribunalPushConfigSerializer(qs, many=True)
        return Response(serializer.data)

    # POST
    serializer = TribunalPushConfigSerializer(data=request.data)
    if serializer.is_valid():
        config = serializer.save(user=request.user)
        return Response(
            TribunalPushConfigSerializer(config).data,
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def tribunal_push_config_detail(request, config_id):
    """
    GET    /api/v1/processos/tribunal-push/configs/<id>/
    PATCH  /api/v1/processos/tribunal-push/configs/<id>/
    DELETE /api/v1/processos/tribunal-push/configs/<id>/
    """
    try:
        config = TribunalPushConfig.objects.get(id=config_id, user=request.user)
    except TribunalPushConfig.DoesNotExist:
        return Response({'error': 'Configuração não encontrada'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(TribunalPushConfigSerializer(config).data)

    if request.method == 'PATCH':
        serializer = TribunalPushConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE
    config.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def tribunal_push_check_now(request, config_id):
    """POST /api/v1/processos/tribunal-push/configs/<id>/check-now/"""
    from apps.cases.services.tribunal_push_service import TribunalPushService

    try:
        config = TribunalPushConfig.objects.get(id=config_id, user=request.user)
    except TribunalPushConfig.DoesNotExist:
        return Response({'error': 'Configuração não encontrada'}, status=status.HTTP_404_NOT_FOUND)

    events = TribunalPushService.check_for_updates(config)
    TribunalPushService.process_events(config)

    return Response({
        'events_found': len(events),
        'events': TribunalPushEventSerializer(events, many=True).data,
        'last_checked': config.last_checked.isoformat() if config.last_checked else None,
    })


# ─────────────────────────────────────────────────────────────────────────────
# TRIBUNAL PUSH — EVENTOS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tribunal_push_events_list(request):
    """
    GET /api/v1/processos/tribunal-push/events/
    Lista eventos de tribunal do usuário.
    """
    from apps.cases.services.tribunal_push_service import TribunalPushService

    days = int(request.query_params.get('days', 30))
    events = TribunalPushService.get_user_events(request.user, days=days)

    # Filtros
    event_type = request.query_params.get('event_type')
    if event_type:
        events = events.filter(event_type=event_type)

    court_system = request.query_params.get('court_system')
    if court_system:
        events = events.filter(config__court_system=court_system)

    page, paginator = paginate_queryset(request, events)
    if page is not None:
        serializer = TribunalPushEventSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    serializer = TribunalPushEventSerializer(events, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def tribunal_push_event_mark_processed(request, event_id):
    """POST /api/v1/processos/tribunal-push/events/<id>/mark-processed/"""
    try:
        event = TribunalPushEvent.objects.get(id=event_id, config__user=request.user)
    except TribunalPushEvent.DoesNotExist:
        return Response({'error': 'Evento não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    event.is_processed = True
    event.save(update_fields=['is_processed'])
    return Response(TribunalPushEventSerializer(event).data)


# ─────────────────────────────────────────────────────────────────────────────
# CONTRATOS JURÍDICOS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def contracts_list_create(request):
    """
    GET  /api/v1/processos/contratos/
    POST /api/v1/processos/contratos/
    """
    if request.method == 'GET':
        qs = LegalContract.objects.select_related('client', 'case', 'created_by').order_by('-created_at')

        # Non-privileged users only see contracts they created or on their cases
        if not _is_privileged(request.user):
            qs = qs.filter(
                Q(created_by=request.user) |
                Q(case__advogado_responsavel=request.user) |
                Q(case__created_by=request.user)
            )

        contract_type = request.query_params.get('contract_type')
        if contract_type:
            qs = qs.filter(contract_type=contract_type)
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        client_id = request.query_params.get('client')
        if client_id:
            qs = qs.filter(client_id=client_id)
        page, paginator = paginate_queryset(request, qs)
        if page is not None:
            return paginator.get_paginated_response(LegalContractSerializer(page, many=True).data)
        return Response(LegalContractSerializer(qs, many=True).data)

    # POST - create contract
    serializer = LegalContractSerializer(data=request.data)
    if serializer.is_valid():
        contract = serializer.save(created_by=request.user)
        return Response(LegalContractSerializer(contract).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def contract_detail(request, contract_id):
    """GET/PATCH/DELETE /api/v1/processos/contratos/<id>/"""
    try:
        contract = LegalContract.objects.select_related(
            'client', 'case', 'created_by',
        ).prefetch_related(
            'honorarios_detail', 'procuracao_detail', 'substabelecimento_detail',
        ).get(id=contract_id)
    except LegalContract.DoesNotExist:
        return Response({'error': 'Contrato não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    # Permission: case access or created_by
    if not check_object_permission(request.user, contract):
        return _deny()

    if request.method == 'GET':
        return Response(LegalContractSerializer(contract).data)
    if request.method == 'PATCH':
        serializer = LegalContractSerializer(contract, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    contract.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIGenerationThrottle])
def contract_generate(request):
    """POST /api/v1/processos/contratos/gerar/ — gera contrato com IA."""
    from apps.cases.services.contract_service import ContractService

    contract_type = request.data.get('contract_type')
    client_id = request.data.get('client')
    case_id = request.data.get('case')

    if not contract_type or not client_id:
        return Response({'error': 'contract_type e client são obrigatórios'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        client = Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        return Response({'error': 'Cliente não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    case = None
    if case_id:
        try:
            case = LegalCase.objects.get(id=case_id)
        except LegalCase.DoesNotExist:
            pass

    svc = ContractService()
    try:
        if contract_type == 'honorarios':
            contract = svc.generate_honorarios(client, case, request.data.get('details', {}), request.user)
        elif contract_type == 'procuracao':
            contract = svc.generate_procuracao(client, case, request.data.get('details', {}), request.user)
        elif contract_type == 'substabelecimento':
            contract = svc.generate_substabelecimento(client, case, request.data.get('details', {}), request.user)
        else:
            return Response({'error': 'Tipo de contrato inválido'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception('Erro ao gerar contrato')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(LegalContractSerializer(contract).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIGenerationThrottle])
def contract_upload_analyze(request):
    """
    POST /api/v1/processos/contratos/upload-analyze/ — upload de contrato para análise com IA.

    Faz upload de um arquivo (PDF/DOCX) e usa IA para:
    - Extrair dados das partes
    - Identificar tipo de contrato
    - Preencher cadastro automaticamente
    """
    from apps.cases.services.contract_service import ContractService

    if 'file' not in request.FILES:
        return Response({'error': 'Arquivo é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

    uploaded_file = request.FILES['file']
    contract_type = request.data.get('contract_type')  # opcional, IA pode detectar

    try:
        contract, extracted_data = ContractService.upload_and_analyze_contract(
            uploaded_file=uploaded_file,
            user=request.user,
            contract_type=contract_type,
        )
        return Response({
            'contract': LegalContractSerializer(contract).data,
            'extracted_data': extracted_data,
            'message': 'Contrato analisado com sucesso. Dados extraídos automaticamente.',
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.exception('Erro ao analisar contrato com IA')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def contract_mark_signed(request, contract_id):
    """POST /api/v1/processos/contratos/<id>/assinar/"""
    try:
        contract = LegalContract.objects.select_related('case', 'created_by').get(id=contract_id)
    except LegalContract.DoesNotExist:
        return Response({'error': 'Contrato não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    if not check_object_permission(request.user, contract):
        return _deny()

    contract.status = 'signed'
    contract.signed_at = timezone.now()
    contract.save(update_fields=['status', 'signed_at'])
    return Response(LegalContractSerializer(contract).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def contract_statistics(request):
    """GET /api/v1/processos/contratos/stats/"""
    from django.db.models import Sum
    qs = LegalContract.objects.all()
    total = qs.count()
    by_status = {}
    for s in ['draft', 'pending_signature', 'signed', 'cancelled']:
        by_status[s] = qs.filter(status=s).count()
    by_type = {}
    for t in ['honorarios', 'procuracao', 'substabelecimento']:
        by_type[t] = qs.filter(contract_type=t).count()
    return Response({
        'total': total,
        'by_status': by_status,
        'by_type': by_type,
    })


# ─────────────────────────────────────────────────────────────────────────────
# GUIAS DE CUSTAS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def court_fees_list_create(request):
    """GET/POST /api/v1/processos/custas/"""
    if request.method == 'GET':
        qs = CourtFeeGuide.objects.select_related('case', 'created_by').order_by('-created_at')

        # Non-privileged users only see fees they created or on their cases
        if not _is_privileged(request.user):
            qs = qs.filter(
                Q(created_by=request.user) |
                Q(case__advogado_responsavel=request.user) |
                Q(case__created_by=request.user)
            )

        payment_status = request.query_params.get('payment_status')
        if payment_status:
            qs = qs.filter(payment_status=payment_status)
        state = request.query_params.get('state')
        if state:
            qs = qs.filter(state=state)
        page, paginator = paginate_queryset(request, qs)
        if page is not None:
            return paginator.get_paginated_response(CourtFeeGuideSerializer(page, many=True).data)
        return Response(CourtFeeGuideSerializer(qs, many=True).data)

    serializer = CourtFeeGuideSerializer(data=request.data)
    if serializer.is_valid():
        fee = serializer.save(created_by=request.user)
        return Response(CourtFeeGuideSerializer(fee).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def court_fee_detail(request, fee_id):
    """GET/PATCH /api/v1/processos/custas/<id>/"""
    try:
        fee = CourtFeeGuide.objects.select_related('case', 'created_by').get(id=fee_id)
    except CourtFeeGuide.DoesNotExist:
        return Response({'error': 'Guia não encontrada'}, status=status.HTTP_404_NOT_FOUND)

    # Permission: case access or created_by
    if not check_object_permission(request.user, fee):
        return _deny()

    if request.method == 'GET':
        return Response(CourtFeeGuideSerializer(fee).data)
    serializer = CourtFeeGuideSerializer(fee, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def court_fee_calculate(request):
    """POST /api/v1/processos/custas/calcular/ — calcula custas judiciais."""
    from apps.cases.services.court_fee_service import CourtFeeService

    fee_type = request.data.get('fee_type', 'custas_iniciais')
    court = request.data.get('court', 'TJSP')
    state = request.data.get('state', 'SP')
    case_value = request.data.get('case_value', 0)

    try:
        case_value = float(case_value)
    except (ValueError, TypeError):
        return Response({'error': 'Valor da causa inválido'}, status=status.HTTP_400_BAD_REQUEST)

    svc = CourtFeeService()
    result = svc.calculate_fee(None, fee_type, court, state, case_value)
    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def court_fee_mark_paid(request, fee_id):
    """POST /api/v1/processos/custas/<id>/pagar/"""
    try:
        fee = CourtFeeGuide.objects.select_related('case', 'created_by').get(id=fee_id)
    except CourtFeeGuide.DoesNotExist:
        return Response({'error': 'Guia não encontrada'}, status=status.HTTP_404_NOT_FOUND)

    if not check_object_permission(request.user, fee):
        return _deny()

    fee.payment_status = 'paid'
    fee.payment_date = request.data.get('payment_date', timezone.now().date())
    fee.save(update_fields=['payment_status', 'payment_date'])
    return Response(CourtFeeGuideSerializer(fee).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def court_fee_summary(request):
    """GET /api/v1/processos/custas/resumo/"""
    from apps.cases.services.court_fee_service import CourtFeeService
    svc = CourtFeeService()
    result = svc.get_fee_summary(request.user)
    return Response(result)


# ─────────────────────────────────────────────────────────────────────────────
# ASSINATURA DIGITAL
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def signatures_list_create(request):
    """GET/POST /api/v1/processos/assinaturas/"""
    if request.method == 'GET':
        qs = DigitalSignature.objects.filter(user=request.user).order_by('-signed_at')
        page, paginator = paginate_queryset(request, qs)
        if page is not None:
            return paginator.get_paginated_response(DigitalSignatureSerializer(page, many=True).data)
        return Response(DigitalSignatureSerializer(qs, many=True).data)

    # POST — sign document
    from apps.cases.services.signature_service import SignatureService
    svc = SignatureService()

    document_id = request.data.get('document')
    contract_id = request.data.get('contract')
    signature_type = request.data.get('signature_type', 'simple')

    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1'))
    if ',' in ip:
        ip = ip.split(',')[0].strip()

    document = None
    if document_id:
        try:
            document = CaseDocument.objects.get(id=document_id)
        except CaseDocument.DoesNotExist:
            return Response({'error': 'Documento não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    try:
        sig = svc.sign_document(request.user, document, signature_type, ip)
        if contract_id:
            sig.contract_id = contract_id
            sig.save(update_fields=['contract_id'])
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(DigitalSignatureSerializer(sig).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def signature_verify(request, signature_id):
    """GET /api/v1/processos/assinaturas/<id>/verificar/"""
    from apps.cases.services.signature_service import SignatureService
    try:
        sig = DigitalSignature.objects.select_related('document__caso', 'user').get(id=signature_id)
    except DigitalSignature.DoesNotExist:
        return Response({'error': 'Assinatura não encontrada'}, status=status.HTTP_404_NOT_FOUND)

    # Permission: own signature, document's case access, or privileged
    if not _is_privileged(request.user):
        is_owner = sig.user_id == request.user.id
        doc = getattr(sig, 'document', None)
        has_case_access = doc and getattr(doc, 'caso', None) and user_can_access_case(request.user, doc.caso)
        if not (is_owner or has_case_access):
            return _deny()

    svc = SignatureService()
    verification = svc.verify_signature(sig.id)
    return Response({
        'signature': DigitalSignatureSerializer(sig).data,
        'verification': SignatureVerificationSerializer(verification).data if verification else None,
    })


# ─────────────────────────────────────────────────────────────────────────────
# CALENDÁRIO
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def calendar_events(request):
    """GET /api/v1/processos/calendario/events/?start=...&end=..."""
    from apps.cases.services.calendar_service import CalendarService

    start = request.query_params.get('start')
    end = request.query_params.get('end')
    if not start or not end:
        return Response({'error': 'Parâmetros start e end são obrigatórios'}, status=status.HTTP_400_BAD_REQUEST)

    from datetime import date
    try:
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end)
    except ValueError:
        return Response({'error': 'Formato de data inválido (YYYY-MM-DD)'}, status=status.HTTP_400_BAD_REQUEST)

    svc = CalendarService()
    events = svc.get_events(request.user, start_date, end_date)
    return Response({'events': events})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def calendar_upcoming(request):
    """GET /api/v1/processos/calendario/proximos/"""
    from apps.cases.services.calendar_service import CalendarService
    days = int(request.query_params.get('days', 7))
    svc = CalendarService()
    deadlines = svc.get_upcoming_deadlines(request.user, days=days)
    return Response({'deadlines': deadlines})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def calendar_overdue(request):
    """GET /api/v1/processos/calendario/atrasados/"""
    from apps.cases.services.calendar_service import CalendarService
    svc = CalendarService()
    items = svc.get_overdue_items(request.user)
    return Response({'overdue': items})


# ─────────────────────────────────────────────────────────────────────────────
# RELATÓRIOS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def report_case_progress(request, case_id):
    """GET /api/v1/processos/relatorios/caso/<id>/"""
    from apps.cases.services.report_service import ReportService
    svc = ReportService()
    try:
        report = svc.generate_case_progress_report(case_id, request.user)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(report)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def report_portfolio(request):
    """GET /api/v1/processos/relatorios/portfolio/"""
    from apps.cases.services.report_service import ReportService
    svc = ReportService()
    report = svc.generate_portfolio_report(request.user)
    return Response(report)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def report_kpis(request):
    """GET /api/v1/processos/relatorios/kpis/"""
    from apps.cases.services.report_service import ReportService
    svc = ReportService()
    kpis = svc.get_kpi_metrics(request.user)
    return Response(kpis)


# ─────────────────────────────────────────────────────────────────────────────
# INTEGRAÇÃO CNJ DATAJUD (#2)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def datajud_search(request):
    """POST /api/v1/processos/datajud/buscar/ — Busca processo no DataJud."""
    from apps.cases.services.datajud_service import DataJudService

    numero_processo = request.data.get('numero_processo', '').strip()
    if not numero_processo:
        return Response(
            {'error': 'O número do processo é obrigatório.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    svc = DataJudService()
    data = svc.search_process(numero_processo)
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def datajud_sync(request, case_id):
    """POST /api/v1/processos/datajud/sync/<uuid:case_id>/ — Sincroniza DataJud com caso."""
    from apps.cases.services.datajud_service import DataJudService

    svc = DataJudService()
    result = svc.sync_case_data(case_id)

    if not result.get('success'):
        return Response(
            {'error': result.get('error', 'Erro ao sincronizar.')},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def datajud_movimentacoes(request):
    """GET /api/v1/processos/datajud/movimentacoes/?numero_processo=... — Movimentações do DataJud."""
    from apps.cases.services.datajud_service import DataJudService

    numero_processo = request.query_params.get('numero_processo', '').strip()
    if not numero_processo:
        return Response(
            {'error': 'O parâmetro numero_processo é obrigatório.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    limit = int(request.query_params.get('limit', 20))
    svc = DataJudService()
    movs = svc.get_movimentacoes(numero_processo, limit=limit)
    return Response(movs)


# ─────────────────────────────────────────────────────────────────────────────
# CONTROLE DE PRAZOS INTELIGENTE (#17)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def smart_deadline_analysis(request):
    """GET /api/v1/processos/prazos/inteligente/analise/ — Análise IA de prazos."""
    from apps.cases.services.smart_deadline_service import SmartDeadlineService

    svc = SmartDeadlineService()
    result = svc.analyze_deadlines(request.user)
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def smart_deadline_suggest(request, deadline_id):
    """GET /api/v1/processos/prazos/inteligente/<uuid>/sugestoes/ — Sugestões IA para prazo."""
    from apps.cases.services.smart_deadline_service import SmartDeadlineService

    svc = SmartDeadlineService()
    result = svc.suggest_actions(deadline_id)

    if 'error' in result and not result.get('sugestoes'):
        return Response(
            {'error': result['error']},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def smart_deadline_risk(request, case_id):
    """GET /api/v1/processos/prazos/inteligente/<uuid>/risco/ — Predição de risco do caso."""
    from apps.cases.services.smart_deadline_service import SmartDeadlineService

    svc = SmartDeadlineService()
    result = svc.predict_risk(case_id)

    if 'error' in result and not result.get('nivel_risco'):
        return Response(
            {'error': result['error']},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(result)


# ─────────────────────────────────────────────────────────────────────────────
# PILOTOS DE PRAZOS - COPILLOT (#115)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def copilot_calculate_deadline(request):
    """
    POST /api/v1/processos/prazos/copilot/calcular/ — Calcula prazo com IA.

    Body:
    {
        "deadline_type": "contestacao|replica|apelacao|...",
        "start_date": "YYYY-MM-DD",
        "case_data": {...}  // opcional
    }
    """
    from apps.cases.services.deadline_ai_service import DeadlineAIService

    data = request.data
    deadline_type = data.get('deadline_type')
    start_date = data.get('start_date')
    case_data = data.get('case_data', {})

    if not deadline_type or not start_date:
        return Response(
            {'error': 'deadline_type e start_date são obrigatórios'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Obter estado do caso para feriados estaduais
    state = case_data.get('estado') or case_data.get('state') or 'BR'

    service = DeadlineAIService(state=state)
    result = service.calculate_deadline(deadline_type, start_date, case_data)

    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def copilot_suggest_strategy(request):
    """
    POST /api/v1/processos/prazos/copilot/estrategia/ — Sugere estratégia com IA.

    Body:
    {
        "deadline_type": "contestacao|replica|apelacao|...",
        "days_remaining": 15,
        "case_urgency": "alta|media|baixa"
    }
    """
    from apps.cases.services.deadline_ai_service import DeadlineAIService

    data = request.data
    deadline_type = data.get('deadline_type')
    days_remaining = data.get('days_remaining')
    case_urgency = data.get('case_urgency', 'media')

    if not deadline_type or days_remaining is None:
        return Response(
            {'error': 'deadline_type e days_remaining são obrigatórios'},
            status=status.HTTP_400_BAD_REQUEST
        )

    service = DeadlineAIService()
    strategy = service.suggest_strategy(deadline_type, days_remaining, case_urgency)

    return Response({
        'deadline_type': deadline_type,
        'days_remaining': days_remaining,
        'case_urgency': case_urgency,
        'strategy': strategy,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def copilot_group_deadlines(request):
    """
    POST /api/v1/processos/prazos/copilot/agrupar/ — Agrupa prazos relacionados.

    Body:
    {
        "deadlines": [
            {"id": "...", "caso_id": "...", "tipo": "...", "titulo": "...", "data_prazo": "...", "status": "..."},
            ...
        ]
    }
    """
    from apps.cases.services.deadline_ai_service import DeadlineAIService

    data = request.data
    deadlines = data.get('deadlines', [])

    if not deadlines:
        return Response(
            {'error': 'Lista de prazos é obrigatória'},
            status=status.HTTP_400_BAD_REQUEST
        )

    service = DeadlineAIService()
    groups = service.group_related_deadlines(deadlines)

    return Response({
        'total_groups': len(groups),
        'groups': groups,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def copilot_critical_deadlines(request):
    """
    GET /api/v1/processos/prazos/copilot/criticos/ — Identifica prazos críticos.

    Query params:
    - case_id: opcional, filtra por caso específico
    - days_ahead: quantos dias à frente considerar (padrão: 30)
    """
    from apps.cases.services.deadline_ai_service import DeadlineAIService
    from apps.cases.models import LegalDeadline, LegalCase

    case_id = request.query_params.get('case_id')
    days_ahead = int(request.query_params.get('days_ahead', 30))

    # Buscar prazos pendentes
    filters = {
        'status__in': ['pendente', 'em_andamento'],
        'caso__advogado_responsavel': request.user,
    }

    if case_id:
        filters['caso_id'] = case_id

    # Filtrar prazos dos próximos dias_ahead dias
    today = timezone.now().date()
    future_date = today + timedelta(days=days_ahead)
    filters['data_prazo__lte'] = future_date

    deadlines_qs = LegalDeadline.objects.filter(**filters).select_related('caso').order_by('data_prazo')

    # Format deadlines for service
    deadlines_data = []
    for d in deadlines_qs:
        deadlines_data.append({
            'id': str(d.id),
            'titulo': d.titulo,
            'tipo': d.tipo,
            'data_prazo': d.data_prazo.isoformat() if d.data_prazo else None,
            'status': d.status,
            'prioridade': d.prioridade,
            'caso_id': str(d.caso.id) if d.caso else None,
            'case_name': d.caso.titulo if d.caso else None,
            'case_priority': 'alta' if d.caso and d.caso.status == 'ativo' else None,
        })

    service = DeadlineAIService()
    critical = service.identify_critical_deadlines(deadlines_data)

    return Response({
        'total_critical': len(critical),
        'critical_deadlines': critical,
    })


# ─────────────────────────────────────────────────────────────────────────────
# WORKFLOW AUTOMATIZADO (#18)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def workflow_templates_list_create(request):
    """GET lista templates | POST cria template."""
    if request.method == 'GET':
        qs = WorkflowTemplate.objects.select_related('created_by').all()
        specialty = request.query_params.get('specialty')
        if specialty:
            qs = qs.filter(specialty=specialty)
        active_only = request.query_params.get('active')
        if active_only == 'true':
            qs = qs.filter(is_active=True)
        serializer = WorkflowTemplateSerializer(qs, many=True)
        return Response(serializer.data)

    serializer = WorkflowTemplateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(created_by=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def workflow_template_detail(request, template_id):
    """GET/PATCH/DELETE template de workflow."""
    try:
        template = WorkflowTemplate.objects.get(id=template_id)
    except WorkflowTemplate.DoesNotExist:
        return Response({'error': 'Template não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(WorkflowTemplateSerializer(template).data)

    if request.method == 'DELETE':
        template.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = WorkflowTemplateSerializer(template, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def workflow_executions_list_create(request):
    """GET lista execuções | POST inicia workflow em um caso."""
    if request.method == 'GET':
        qs = WorkflowExecution.objects.select_related('template', 'case').all()
        case_id = request.query_params.get('case')
        if case_id:
            qs = qs.filter(case_id=case_id)
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        serializer = WorkflowExecutionSerializer(qs, many=True)
        return Response(serializer.data)

    # POST — iniciar workflow
    template_id = request.data.get('template')
    case_id = request.data.get('case')
    if not template_id or not case_id:
        return Response(
            {'error': 'Campos "template" e "case" são obrigatórios.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        template = WorkflowTemplate.objects.get(id=template_id)
    except WorkflowTemplate.DoesNotExist:
        return Response({'error': 'Template não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    try:
        case = LegalCase.objects.get(id=case_id)
    except LegalCase.DoesNotExist:
        return Response({'error': 'Caso não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    execution = WorkflowExecution.objects.create(
        template=template,
        case=case,
        current_step=0,
        status='active',
        step_history=[{
            'step': 0,
            'started_at': timezone.now().isoformat(),
            'completed_at': None,
            'notes': '',
        }],
    )
    return Response(WorkflowExecutionSerializer(execution).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def workflow_execution_detail(request, execution_id):
    """GET/PATCH execução de workflow."""
    try:
        execution = WorkflowExecution.objects.select_related(
            'template', 'case__advogado_responsavel', 'case__created_by'
        ).get(id=execution_id)
    except WorkflowExecution.DoesNotExist:
        return Response({'error': 'Execução não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

    if execution.case and not user_can_access_case(request.user, execution.case):
        return _deny()

    if request.method == 'GET':
        return Response(WorkflowExecutionSerializer(execution).data)

    serializer = WorkflowExecutionSerializer(execution, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def workflow_advance_step(request, execution_id):
    """POST avança para a próxima etapa do workflow."""
    try:
        execution = WorkflowExecution.objects.select_related(
            'template', 'case__advogado_responsavel', 'case__created_by'
        ).get(id=execution_id)
    except WorkflowExecution.DoesNotExist:
        return Response({'error': 'Execução não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

    if execution.case and not user_can_access_case(request.user, execution.case):
        return _deny()

    if execution.status != 'active':
        return Response(
            {'error': 'Workflow não está ativo.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    steps = execution.template.steps or []
    if execution.current_step >= len(steps) - 1:
        # Última etapa — concluir workflow
        history = list(execution.step_history)
        if history:
            history[-1]['completed_at'] = timezone.now().isoformat()
            history[-1]['notes'] = request.data.get('notes', '')
        execution.step_history = history
        execution.status = 'completed'
        execution.completed_at = timezone.now()
        execution.save()
        return Response(WorkflowExecutionSerializer(execution).data)

    # Avançar para próxima etapa
    history = list(execution.step_history)
    if history:
        history[-1]['completed_at'] = timezone.now().isoformat()
        history[-1]['notes'] = request.data.get('notes', '')

    next_step = execution.current_step + 1
    history.append({
        'step': next_step,
        'started_at': timezone.now().isoformat(),
        'completed_at': None,
        'notes': '',
    })

    execution.current_step = next_step
    execution.step_history = history
    execution.save()
    return Response(WorkflowExecutionSerializer(execution).data)


# ─────────────────────────────────────────────────────────────────────────────
# IMPORTAÇÃO EM MASSA (#21)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_cases_csv(request):
    """
    POST /api/v1/processos/importar/casos/
    Recebe arquivo CSV e cria casos em lote.
    Colunas esperadas: titulo, numero_processo, especialidade, status,
                       cliente_nome, cliente_cpf_cnpj
    """
    import csv
    import io

    file = request.FILES.get('file')
    if not file:
        return Response({'error': 'Nenhum arquivo enviado.'}, status=status.HTTP_400_BAD_REQUEST)

    if not file.name.endswith('.csv'):
        return Response({'error': 'Formato inválido. Envie um arquivo .csv.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        decoded = file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(decoded), delimiter=';')

        created = 0
        errors_list = []
        for i, row in enumerate(reader, start=2):
            try:
                titulo = row.get('titulo', '').strip()
                if not titulo:
                    errors_list.append({'linha': i, 'erro': 'Título é obrigatório.'})
                    continue

                LegalCase.objects.create(
                    titulo=titulo,
                    numero_processo=row.get('numero_processo', '').strip(),
                    especialidade=row.get('especialidade', 'civel').strip() or 'civel',
                    status=row.get('status', 'ativo').strip() or 'ativo',
                    cliente_nome=row.get('cliente_nome', '').strip(),
                    cliente_cpf_cnpj=row.get('cliente_cpf_cnpj', '').strip(),
                    created_by=request.user,
                )
                created += 1
            except Exception as e:
                errors_list.append({'linha': i, 'erro': str(e)})

        return Response({
            'importados': created,
            'erros_count': len(errors_list),
            'erros': errors_list[:50],
        })
    except Exception as e:
        logger.error(f"[import_cases_csv] Erro: {e}", exc_info=True)
        return Response({'error': f'Erro ao processar CSV: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_clients_csv(request):
    """
    POST /api/v1/processos/importar/clientes/
    Recebe arquivo CSV e cria clientes em lote.
    Colunas esperadas: nome, cpf_cnpj, email, telefone, endereco, tipo (PF/PJ)
    """
    import csv
    import io

    file = request.FILES.get('file')
    if not file:
        return Response({'error': 'Nenhum arquivo enviado.'}, status=status.HTTP_400_BAD_REQUEST)

    if not file.name.endswith('.csv'):
        return Response({'error': 'Formato inválido. Envie um arquivo .csv.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        decoded = file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(decoded), delimiter=';')

        created = 0
        errors_list = []
        for i, row in enumerate(reader, start=2):
            try:
                nome = row.get('nome', '').strip()
                if not nome:
                    errors_list.append({'linha': i, 'erro': 'Nome é obrigatório.'})
                    continue

                tipo_raw = row.get('tipo', 'PF').strip().upper()
                client_type = 'pessoa_juridica' if tipo_raw == 'PJ' else 'pessoa_fisica'

                Client.objects.create(
                    name=nome,
                    cpf_cnpj=row.get('cpf_cnpj', '').strip(),
                    email=row.get('email', '').strip(),
                    phone=row.get('telefone', '').strip(),
                    address=row.get('endereco', '').strip(),
                    client_type=client_type,
                    created_by=request.user,
                )
                created += 1
            except Exception as e:
                errors_list.append({'linha': i, 'erro': str(e)})

        return Response({
            'importados': created,
            'erros_count': len(errors_list),
            'erros': errors_list[:50],
        })
    except Exception as e:
        logger.error(f"[import_clients_csv] Erro: {e}", exc_info=True)
        return Response({'error': f'Erro ao processar CSV: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def import_template(request):
    """
    GET /api/v1/processos/importar/template/?tipo=casos|clientes
    Retorna template CSV para download.
    """
    import csv
    from django.http import HttpResponse

    tipo = request.query_params.get('tipo', 'casos')

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="template_{tipo}.csv"'
    response.write('\ufeff')

    writer = csv.writer(response, delimiter=';')

    if tipo == 'clientes':
        writer.writerow(['nome', 'cpf_cnpj', 'email', 'telefone', 'endereco', 'tipo'])
        writer.writerow(['João da Silva', '123.456.789-00', 'joao@email.com', '(11) 99999-0000', 'Rua A, 123', 'PF'])
        writer.writerow(['Empresa ABC Ltda', '12.345.678/0001-90', 'contato@abc.com', '(11) 3333-0000', 'Av. B, 456', 'PJ'])
    else:
        writer.writerow(['titulo', 'numero_processo', 'especialidade', 'status', 'cliente_nome', 'cliente_cpf_cnpj'])
        writer.writerow(['Ação de Cobrança', '0001234-56.2024.8.19.0001', 'civel', 'ativo', 'João da Silva', '123.456.789-00'])

    return response


# ─────────────────────────────────────────────────────────────────────────────
# EXPORTAÇÃO DE DADOS (#22)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ExportThrottle])
def export_cases(request):
    """
    GET /api/v1/processos/exportar/casos/?format=csv|json&start_date=&end_date=
    Exporta casos do usuário.
    """
    if not _is_privileged(request.user):
        return _deny()

    import csv
    from django.http import HttpResponse

    fmt = request.query_params.get('format', 'csv')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')

    qs = LegalCase.objects.select_related('advogado_responsavel', 'client').all().order_by('-created_at')
    if start_date:
        qs = qs.filter(created_at__date__gte=start_date)
    if end_date:
        qs = qs.filter(created_at__date__lte=end_date)

    if fmt == 'json':
        serializer = LegalCaseListSerializer(qs, many=True)
        return Response(serializer.data)

    # CSV
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="casos.csv"'
    response.write('\ufeff')

    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'titulo', 'numero_processo', 'especialidade', 'status', 'fase',
        'cliente_nome', 'cliente_cpf_cnpj', 'parte_contraria',
        'tribunal', 'vara_juizo', 'comarca', 'valor_causa',
        'data_distribuicao', 'created_at',
    ])
    for c in qs:
        writer.writerow([
            c.titulo, c.numero_processo, c.get_especialidade_display(),
            c.get_status_display(), c.get_fase_display(),
            c.cliente_nome, c.cliente_cpf_cnpj, c.parte_contraria,
            c.tribunal, c.vara_juizo, c.comarca, c.valor_causa or '',
            c.data_distribuicao or '', c.created_at.strftime('%Y-%m-%d'),
        ])

    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ExportThrottle])
def export_clients(request):
    """
    GET /api/v1/processos/exportar/clientes/?format=csv|json&start_date=&end_date=
    Exporta clientes.
    """
    if not _is_privileged(request.user):
        return _deny()

    import csv
    from django.http import HttpResponse

    fmt = request.query_params.get('format', 'csv')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')

    qs = Client.objects.select_related('responsible_lawyer').all().order_by('-created_at')
    if start_date:
        qs = qs.filter(created_at__date__gte=start_date)
    if end_date:
        qs = qs.filter(created_at__date__lte=end_date)

    if fmt == 'json':
        serializer = ClientSerializer(qs, many=True)
        return Response(serializer.data)

    # CSV
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="clientes.csv"'
    response.write('\ufeff')

    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'nome', 'tipo', 'cpf_cnpj', 'email', 'telefone',
        'endereco', 'cidade', 'uf', 'cep', 'ativo', 'created_at',
    ])
    for cl in qs:
        writer.writerow([
            cl.name, cl.get_client_type_display(), cl.cpf_cnpj,
            cl.email, cl.phone, cl.address, cl.city, cl.state,
            cl.zipcode, 'Sim' if cl.is_active else 'Não',
            cl.created_at.strftime('%Y-%m-%d'),
        ])

    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ExportThrottle])
def export_deadlines(request):
    """
    GET /api/v1/processos/exportar/prazos/?format=csv|json&start_date=&end_date=
    Exporta prazos processuais.
    """
    if not _is_privileged(request.user):
        return _deny()

    import csv
    from django.http import HttpResponse

    fmt = request.query_params.get('format', 'csv')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')

    qs = LegalDeadline.objects.select_related('caso', 'responsavel').all().order_by('data_prazo')
    if start_date:
        qs = qs.filter(data_prazo__gte=start_date)
    if end_date:
        qs = qs.filter(data_prazo__lte=end_date)

    if fmt == 'json':
        serializer = LegalDeadlineSerializer(qs, many=True)
        return Response(serializer.data)

    # CSV
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="prazos.csv"'
    response.write('\ufeff')

    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'titulo', 'caso', 'tipo', 'prioridade', 'status',
        'data_prazo', 'data_conclusao', 'responsavel',
    ])
    for d in qs:
        writer.writerow([
            d.titulo, str(d.caso), d.get_tipo_display(),
            d.get_prioridade_display(), d.get_status_display(),
            d.data_prazo, d.data_conclusao or '',
            d.responsavel.get_full_name() if d.responsavel else '',
        ])

    return response


# ─── Atividade do Portal do Cliente ─────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_portal_activity(request):
    """GET /api/v1/processos/atividade-portal/
    Returns recent client portal activity for the lawyer's clients.
    Shows: signed contracts, uploaded docs, messages, consent acceptances."""
    from apps.accounts.models import ClientMessage, ConsentRecord
    from apps.cases.models import LegalContract, CaseDocument, DigitalSignature

    activities = []

    # Recent client messages (last 7 days)
    from datetime import timedelta
    week_ago = timezone.now() - timedelta(days=7)

    try:
        msgs = ClientMessage.objects.filter(
            sender_type='client', created_at__gte=week_ago
        ).exclude(
            case__status='arquivado'
        ).select_related('client', 'case').order_by('-created_at')[:10]
        for m in msgs:
            activities.append({
                'type': 'message',
                'icon': 'MessageSquare',
                'title': f'Mensagem de {m.client.name}',
                'description': m.content[:100] + ('...' if len(m.content) > 100 else ''),
                'case': m.case.titulo if m.case else None,
                'case_id': str(m.case.id) if m.case else None,
                'date': m.created_at.isoformat(),
                'is_read': m.is_read,
            })
    except Exception as e:
        logger.warning(f"Non-critical error loading client messages: {e}")

    # Recent contract signatures (last 30 days)
    month_ago = timezone.now() - timedelta(days=30)
    try:
        sigs = LegalContract.objects.filter(
            status='signed', signed_at__gte=month_ago
        ).exclude(
            case__status='arquivado'
        ).select_related('client', 'case').order_by('-signed_at')[:5]
        for s in sigs:
            activities.append({
                'type': 'contract_signed',
                'icon': 'PenTool',
                'title': f'Contrato assinado por {s.client.name}',
                'description': s.title,
                'case': s.case.titulo if s.case else None,
                'case_id': str(s.case.id) if s.case else None,
                'date': s.signed_at.isoformat() if s.signed_at else s.updated_at.isoformat(),
                'is_read': True,
            })
    except Exception as e:
        logger.warning(f"Non-critical error loading contract signatures: {e}")

    # Sort by date
    activities.sort(key=lambda x: x['date'], reverse=True)

    return Response({
        'activities': activities[:20],
        'total': len(activities),
    })


# ─────────────────────────────────────────────────────────────────────────────
# MENSAGENS CLIENTE-ADVOGADO (lado do advogado)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_messages_list(request):
    """GET /api/v1/processos/mensagens-clientes/
    Lista todas as mensagens de clientes para o advogado.
    Filtra por caso do advogado ou todos se admin."""
    from apps.accounts.models import ClientMessage

    qs = ClientMessage.objects.select_related('client', 'case').order_by('-created_at')

    if not _is_privileged(request.user):
        qs = qs.filter(
            Q(case__advogado_responsavel=request.user) |
            Q(case__created_by=request.user)
        )

    # Filters
    client_id = request.query_params.get('client')
    if client_id:
        qs = qs.filter(client_id=client_id)
    case_id = request.query_params.get('case')
    if case_id:
        qs = qs.filter(case_id=case_id)
    unread = request.query_params.get('unread')
    if unread == 'true':
        qs = qs.filter(is_read=False, sender_type='client')

    from rest_framework import serializers as sz

    class ClientMessageSerializer(sz.ModelSerializer):
        client_name = sz.SerializerMethodField()
        client_email = sz.SerializerMethodField()
        client_phone = sz.SerializerMethodField()
        case_titulo = sz.SerializerMethodField()

        class Meta:
            model = ClientMessage
            fields = ['id', 'client', 'client_name', 'client_email', 'client_phone',
                      'case', 'case_titulo',
                      'sender_type', 'sender_name', 'content', 'is_read', 'created_at']

        def get_client_name(self, obj):
            return obj.client.name if obj.client else None

        def get_client_email(self, obj):
            return obj.client.email if obj.client else None

        def get_client_phone(self, obj):
            return obj.client.phone if obj.client else None

        def get_case_titulo(self, obj):
            return obj.case.titulo if obj.case else None

    unread_count = qs.filter(is_read=False, sender_type='client').count()
    page, paginator = paginate_queryset(request, qs)
    if page is not None:
        data = ClientMessageSerializer(page, many=True).data
        response = paginator.get_paginated_response(data)
        response.data['unread_count'] = unread_count
        return response
    data = ClientMessageSerializer(qs, many=True).data
    return Response({'results': data, 'unread_count': unread_count})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def client_message_reply(request):
    """POST /api/v1/processos/mensagens-clientes/responder/
    Advogado responde a mensagem de cliente.
    Body: {client: uuid, case: uuid (optional), content: string}"""
    from apps.accounts.models import ClientMessage

    client_id = request.data.get('client')
    case_id = request.data.get('case')
    content = request.data.get('content', '').strip()

    if not client_id or not content:
        return Response({'error': 'client e content são obrigatórios'}, status=status.HTTP_400_BAD_REQUEST)

    msg = ClientMessage.objects.create(
        client_id=client_id,
        case_id=case_id,
        sender_type='lawyer',
        sender_name=request.user.get_full_name() or request.user.username,
        content=content,
        is_read=False,
    )

    return Response({
        'id': str(msg.id),
        'content': msg.content,
        'sender_name': msg.sender_name,
        'created_at': msg.created_at.isoformat(),
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def client_messages_mark_read(request):
    """POST /api/v1/processos/mensagens-clientes/marcar-lidas/
    Marca mensagens de um cliente como lidas.
    Body: {client: uuid, case: uuid (optional)}"""
    from apps.accounts.models import ClientMessage

    client_id = request.data.get('client')
    case_id = request.data.get('case')

    qs = ClientMessage.objects.filter(client_id=client_id, sender_type='client', is_read=False)
    if case_id:
        qs = qs.filter(case_id=case_id)

    count = qs.update(is_read=True)
    return Response({'marked_read': count})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_messages_unread_count(request):
    """GET /api/v1/processos/mensagens-clientes/nao-lidas/
    Retorna contagem de mensagens não lidas de clientes."""
    from apps.accounts.models import ClientMessage

    qs = ClientMessage.objects.filter(sender_type='client', is_read=False)
    if not _is_privileged(request.user):
        qs = qs.filter(
            Q(case__advogado_responsavel=request.user) |
            Q(case__created_by=request.user)
        )

    return Response({'unread_count': qs.count()})


# ─────────────────────────────────────────────────────────────────────────────
# TIMESHEET / CONTROLE DE HORAS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def time_entries_list_create(request, case_id=None):
    """
    GET  — Lista registros de horas (por caso ou geral)
    POST — Cria registro de horas
    """
    if request.method == 'GET':
        from .models import TimeEntry
        qs = TimeEntry.objects.select_related('advogado', 'caso', 'task').all()
        if case_id:
            qs = qs.filter(caso_id=case_id)

        # Non-privileged users only see their own entries or entries on their cases
        if not _is_privileged(request.user):
            qs = qs.filter(
                Q(advogado=request.user) |
                Q(caso__advogado_responsavel=request.user) |
                Q(caso__created_by=request.user)
            )

        # Filters
        advogado = request.query_params.get('advogado')
        if advogado:
            qs = qs.filter(advogado_id=advogado)

        month = request.query_params.get('month')
        year = request.query_params.get('year')
        if month and year:
            qs = qs.filter(date__year=int(year), date__month=int(month))

        billing_type = request.query_params.get('billing_type')
        if billing_type:
            qs = qs.filter(billing_type=billing_type)

        from .serializers import TimeEntrySerializer
        page, paginator = paginate_queryset(request, qs)
        if page is not None:
            serializer = TimeEntrySerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        serializer = TimeEntrySerializer(qs, many=True)
        return Response(serializer.data)

    # POST
    from .serializers import TimeEntrySerializer
    serializer = TimeEntrySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(advogado=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def time_entry_detail(request, entry_id):
    """GET/PUT/DELETE de registro de horas."""
    from .models import TimeEntry
    try:
        entry = TimeEntry.objects.select_related('advogado', 'caso').get(id=entry_id)
    except TimeEntry.DoesNotExist:
        return Response({'error': 'Registro não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    # Permission: own entry or case access
    if not _is_privileged(request.user):
        is_owner = getattr(entry, 'advogado_id', None) == request.user.id
        caso = getattr(entry, 'caso', None)
        has_case_access = caso and user_can_access_case(request.user, caso)
        if not (is_owner or has_case_access):
            return _deny()

    if request.method == 'GET':
        from .serializers import TimeEntrySerializer
        return Response(TimeEntrySerializer(entry).data)

    if request.method == 'PUT':
        from .serializers import TimeEntrySerializer
        serializer = TimeEntrySerializer(entry, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    entry.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def time_entry_approve(request, entry_id):
    """Aprova registro de horas."""
    # Only privileged roles can approve time entries
    if not _is_privileged(request.user):
        return _deny()

    from .models import TimeEntry
    try:
        entry = TimeEntry.objects.get(id=entry_id)
    except TimeEntry.DoesNotExist:
        return Response({'error': 'Registro não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    entry.is_approved = True
    entry.approved_by = request.user
    entry.approved_at = timezone.now()
    entry.save(update_fields=['is_approved', 'approved_by', 'approved_at'])

    from .serializers import TimeEntrySerializer
    return Response(TimeEntrySerializer(entry).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def timesheet_monthly_report(request):
    """Relatório mensal de horas."""
    from .services.timesheet_service import TimesheetService

    lawyer_id = request.query_params.get('lawyer_id', request.user.id)
    year = int(request.query_params.get('year', timezone.now().year))
    month = int(request.query_params.get('month', timezone.now().month))

    report = TimesheetService.monthly_report(lawyer_id, year, month)
    return Response(report)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def timesheet_case_honorarios(request, case_id):
    """Honorários acumulados por horas em um caso."""
    from .services.timesheet_service import TimesheetService
    result = TimesheetService.calculate_case_honorarios(case_id)
    return Response(result)


# ─────────────────────────────────────────────────────────────────────────────
# COPILOT TIMESHEET
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def copilot_timesheet_suggest(request):
    """
    GET — Sugere registros de timesheet baseados em atividades do usuário.

    Query params:
    - days_back: Quantos dias atrás buscar (padrão: 7)
    """
    from .services.timesheet_ai_service import TimesheetAIService

    days_back = int(request.query_params.get('days_back', 7))

    try:
        suggestions = TimesheetAIService.analyze_activities_for_timesheet(
            user_id=str(request.user.id),
            days_back=days_back,
        )

        # Executar async
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        suggestions_result = loop.run_until_complete(suggestions)
        loop.close()

        return Response({
            'suggestions': suggestions_result,
            'count': len(suggestions_result),
        })
    except Exception as e:
        logger.warning(f'Erro ao sugerir timesheet: {e}')
        return Response({
            'error': 'Não foi possível gerar sugestões no momento',
            'suggestions': [],
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def copilot_timesheet_description(request):
    """
    POST — Gera descrição técnica para registro de timesheet.

    Body:
    {
        "activity_type": "reuniao|peticao|analise|...",
        "case_title": "Nome do caso",
        "details": {...}  // opcional
    }
    """
    from .services.timesheet_ai_service import TimesheetAIService

    data = request.data
    activity_type = data.get('activity_type', '')
    case_title = data.get('case_title', '')

    if not activity_type or not case_title:
        return Response({
            'error': 'activity_type e case_title são obrigatórios',
        }, status=status.HTTP_400_BAD_REQUEST)

    details = data.get('details', {})

    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        description = loop.run_until_complete(
            TimesheetAIService.suggest_description(
                activity_type=activity_type,
                case_title=case_title,
                details=details,
            )
        )
        loop.close()

        return Response({'description': description})
    except Exception as e:
        logger.warning(f'Erro ao gerar descrição: {e}')
        description = TimesheetAIService._fallback_description(activity_type, case_title)
        return Response({'description': description})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def copilot_timesheet_detect(request):
    """
    GET — Detecta horas não lançadas baseado em atividades.

    Query params:
    - start: Data inicial (YYYY-MM-DD)
    - end: Data final (YYYY-MM-DD)
    """
    from .services.timesheet_ai_service import TimesheetAIService
    from datetime import timedelta

    start = request.query_params.get('start')
    end = request.query_params.get('end')

    if not start or not end:
        # Default: últimos 7 dias
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)
        start = start_date.strftime('%Y-%m-%d')
        end = end_date.strftime('%Y-%m-%d')

    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        unlogged = loop.run_until_complete(
            TimesheetAIService.detect_unlogged_hours(
                user_id=str(request.user.id),
                date_range={'start': start, 'end': end},
            )
        )
        loop.close()

        return Response({
            'unlogged_hours': unlogged,
            'count': len(unlogged),
            'period': {'start': start, 'end': end},
        })
    except Exception as e:
        logger.warning(f'Erro ao detectar horas não lançadas: {e}')
        return Response({
            'error': 'Não foi possível detectar horas não lançadas',
            'unlogged_hours': [],
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def copilot_timesheet_optimize(request):
    """
    POST — Otimiza alocação de horas entre casos.

    Body:
    {
        "entries": [
            {"case_id": "...", "hours": 2.5, "case_title": "..."},
            ...
        ]
    }
    """
    from .services.timesheet_ai_service import TimesheetAIService

    data = request.data
    entries = data.get('entries', [])

    if not entries:
        return Response({
            'error': 'entries é obrigatório',
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        suggestions = loop.run_until_complete(
            TimesheetAIService.optimize_billing(entries)
        )
        loop.close()

        return Response({
            'suggestions': suggestions,
            'count': len(suggestions),
        })
    except Exception as e:
        logger.warning(f'Erro ao otimizar billing: {e}')
        return Response({
            'error': 'Não foi possível otimizar alocação',
            'suggestions': [],
        }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# VERIFICAÇÃO DE CONFLITO DE INTERESSES
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([ConflictCheckThrottle])
def check_conflict_of_interest(request):
    """
    POST — Verifica conflito de interesses antes de cadastrar cliente.
    Body: { "name": "...", "cpf_cnpj": "..." }
    """
    from .services.conflict_check_service import ConflictCheckService

    name = request.data.get('name', '')
    cpf_cnpj = request.data.get('cpf_cnpj', '')
    client_id = request.data.get('client_id')

    if not name:
        return Response({'error': 'Nome é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

    result = ConflictCheckService.check_conflicts(name, cpf_cnpj, client_id)
    return Response(result)


# ─────────────────────────────────────────────────────────────────────────────
# CRM / PIPELINE DE LEADS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def lead_stages_list_create(request):
    """GET — Lista etapas do funil. POST — Cria etapa."""
    from .models import LeadStage
    from .serializers import LeadStageSerializer

    if request.method == 'GET':
        stages = LeadStage.objects.all()
        return Response(LeadStageSerializer(stages, many=True).data)

    serializer = LeadStageSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def leads_list_create(request):
    """GET — Lista leads. POST — Cria lead."""
    from .models import Lead
    from .serializers import LeadSerializer

    if request.method == 'GET':
        qs = Lead.objects.select_related('stage', 'responsible').prefetch_related('activities').all()

        # Non-privileged users only see leads they are responsible for or created
        if not _is_privileged(request.user):
            qs = qs.filter(
                Q(responsible=request.user) | Q(created_by=request.user)
            )

        stage = request.query_params.get('stage')
        if stage:
            qs = qs.filter(stage_id=stage)

        temperature = request.query_params.get('temperature')
        if temperature:
            qs = qs.filter(temperature=temperature)

        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(email__icontains=search) | Q(phone__icontains=search))

        page, paginator = paginate_queryset(request, qs)
        if page is not None:
            return paginator.get_paginated_response(LeadSerializer(page, many=True).data)
        return Response(LeadSerializer(qs, many=True).data)

    serializer = LeadSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def lead_detail(request, lead_id):
    """CRUD de lead."""
    from .models import Lead
    from .serializers import LeadSerializer

    try:
        lead = Lead.objects.select_related('stage', 'responsible').get(id=lead_id)
    except Lead.DoesNotExist:
        return Response({'error': 'Lead não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    # Permission: responsible, created_by, or privileged
    if not _is_privileged(request.user):
        if (
            getattr(lead, 'responsible_id', None) != request.user.id
            and getattr(lead, 'created_by_id', None) != request.user.id
        ):
            return _deny()

    if request.method == 'GET':
        return Response(LeadSerializer(lead).data)

    if request.method in ('PUT', 'PATCH'):
        serializer = LeadSerializer(lead, data=request.data, partial=(request.method == 'PATCH'))
        if serializer.is_valid():
            # Track stage changes
            old_stage = lead.stage_id
            new_stage = serializer.validated_data.get('stage')
            obj = serializer.save()

            if new_stage and str(new_stage.id) != str(old_stage):
                from .models import LeadActivity
                LeadActivity.objects.create(
                    lead=obj,
                    activity_type='stage_change',
                    description=f'Movido para: {new_stage.name}',
                    created_by=request.user,
                )
            return Response(LeadSerializer(obj).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    lead.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def lead_add_activity(request, lead_id):
    """Adiciona atividade ao lead."""
    from .models import Lead
    from .serializers import LeadActivitySerializer

    try:
        lead = Lead.objects.select_related('responsible').get(id=lead_id)
    except Lead.DoesNotExist:
        return Response({'error': 'Lead não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    if not _is_privileged(request.user):
        if (
            getattr(lead, 'responsible_id', None) != request.user.id
            and getattr(lead, 'created_by_id', None) != request.user.id
        ):
            return _deny()

    data = {**request.data, 'lead': str(lead.id)}
    serializer = LeadActivitySerializer(data=data)
    if serializer.is_valid():
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def lead_convert(request, lead_id):
    """Converte lead em cliente + caso."""
    from .models import Lead
    from .serializers import LeadSerializer

    try:
        lead = Lead.objects.select_related('responsible').get(id=lead_id)
    except Lead.DoesNotExist:
        return Response({'error': 'Lead não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    if not _is_privileged(request.user):
        if (
            getattr(lead, 'responsible_id', None) != request.user.id
            and getattr(lead, 'created_by_id', None) != request.user.id
        ):
            return _deny()

    # Create client from lead
    client = Client.objects.create(
        name=lead.name,
        email=lead.email or '',
        phone=lead.phone or '',
        cpf_cnpj=lead.cpf_cnpj or '',
        responsible_lawyer=lead.responsible or request.user,
        created_by=request.user,
        notes=lead.notes or '',
    )

    # Create case if description exists
    caso = None
    if lead.description:
        caso = LegalCase.objects.create(
            titulo=f'Caso — {lead.name}',
            especialidade=lead.specialty or 'civel',
            client=client,
            cliente_nome=lead.name,
            cliente_cpf_cnpj=lead.cpf_cnpj or '',
            descricao=lead.description,
            valor_causa=lead.estimated_value,
            advogado_responsavel=lead.responsible or request.user,
            created_by=request.user,
        )

    # Mark lead as converted
    lead.converted_client = client
    lead.converted_case = caso
    lead.converted_at = timezone.now()
    lead.save(update_fields=['converted_client', 'converted_case', 'converted_at'])

    return Response({
        'lead': LeadSerializer(lead).data,
        'client_id': str(client.id),
        'case_id': str(caso.id) if caso else None,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lead_pipeline(request):
    """Retorna dados do pipeline (kanban) com leads agrupados por etapa."""
    from .models import LeadStage, Lead
    from .serializers import LeadStageSerializer, LeadSerializer
    from django.db.models import Sum

    stages = LeadStage.objects.all().order_by('order')
    leads = Lead.objects.select_related('stage', 'responsible').filter(converted_at__isnull=True)

    leads_by_stage = {}
    for stage in stages:
        stage_leads = [l for l in leads if l.stage_id == stage.id]
        leads_by_stage[str(stage.id)] = LeadSerializer(stage_leads, many=True).data

    # Leads without stage
    no_stage = [l for l in leads if l.stage_id is None]
    if no_stage:
        leads_by_stage['unassigned'] = LeadSerializer(no_stage, many=True).data

    total_value = leads.aggregate(total=Sum('estimated_value'))['total'] or 0
    total_leads = leads.count()
    converted_count = Lead.objects.filter(converted_at__isnull=False).count()
    all_count = Lead.objects.count()

    return Response({
        'stages': LeadStageSerializer(stages, many=True).data,
        'leads_by_stage': leads_by_stage,
        'total_leads': total_leads,
        'total_value': float(total_value),
        'conversion_rate': round(converted_count / max(all_count, 1) * 100, 1),
    })


# ─────────────────────────────────────────────────────────────────────────────
# KPIs GAMIFICADOS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def kpi_leaderboard(request):
    """Retorna leaderboard/ranking de advogados."""
    from .services.kpi_service import KPIService
    from datetime import date

    year = int(request.query_params.get('year', timezone.now().year))
    month = int(request.query_params.get('month', timezone.now().month))

    period_start = date(year, month, 1)
    if month == 12:
        period_end = date(year + 1, 1, 1)
    else:
        period_end = date(year, month + 1, 1)

    from datetime import timedelta
    period_end = period_end - timedelta(days=1)

    leaderboard = KPIService.get_leaderboard(period_start, period_end)

    if not leaderboard:
        # Calculate if not exists yet
        KPIService.calculate_period_scores(period_start, period_end)
        leaderboard = KPIService.get_leaderboard(period_start, period_end)

    return Response({
        'period_start': str(period_start),
        'period_end': str(period_end),
        'leaderboard': leaderboard,
        'badges_available': KPIService.BADGE_DEFINITIONS,
    })


# ─────────────────────────────────────────────────────────────────────────────
# COPILOT CRM — Análise de Leads com IA
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIGenerationThrottle])
def copilot_classify_lead(request):
    """
    POST — Classifica temperatura do lead usando IA.

    Body:
    {
        "description": "...",
        "specialty": "civel",
        "urgency": true,
        "estimated_value": 5000,
        "source": "indicacao",
        "intake_data": {...}
    }
    """
    from .services.lead_ai_service import LeadAIService

    data = request.data
    description = data.get('description', '')
    specialty = data.get('specialty', 'civel')
    urgency = data.get('urgency', False)
    estimated_value = data.get('estimated_value')
    source = data.get('source', 'outro')
    intake_data = data.get('intake_data', {})

    # Usar fallback heurístico (método síncrono)
    result = LeadAIService._heuristic_classification(
        description=description,
        urgency=urgency,
        estimated_value=estimated_value,
        source=source,
    )

    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIGenerationThrottle])
def copilot_generate_followup(request):
    """
    POST — Gera mensagem de follow-up personalizada para lead.

    Body:
    {
        "lead_name": "João Silva",
        "temperature": "warm",
        "specialty": "trabalhista",
        "last_interaction": "Cliente ligou pedindo informações sobre rescisão",
        "stage_name": "Qualificação"
    }
    """
    from .services.lead_ai_service import LeadAIService

    data = request.data
    lead_name = data.get('lead_name', 'Cliente')
    temperature = data.get('temperature', 'warm')
    specialty = data.get('specialty', 'civel')
    last_interaction = data.get('last_interaction')
    stage_name = data.get('stage_name')

    # Usar fallback (método síncrono)
    message = LeadAIService._fallback_follow_up(temperature=temperature, lead_name=lead_name)

    return Response({'message': message})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIGenerationThrottle])
def copilot_predict_conversion(request):
    """
    POST — Prevê probabilidade de conversão do lead.

    Body:
    {
        "lead_data": {
            "specialty": "civel",
            "temperature": "hot",
            "source": "indicacao",
            "estimated_value": 10000,
            "urgency": true,
            "lead_channel": "indicacao_cliente"
        }
    }
    """
    from .services.lead_ai_service import LeadAIService

    data = request.data
    lead_data = data.get('lead_data', {})

    # Usar fallback síncrono simples
    base_prob = {'hot': 75, 'warm': 45, 'cold': 20}
    temp = lead_data.get('temperature', 'warm')
    result = {
        'probability': base_prob.get(temp, 45),
        'factors': ['Baseado apenas na temperatura do lead'],
        'recommendation': 'Aguardar mais dados para análise precisa.',
    }

    return Response(result)


# ─────────────────────────────────────────────────────────────────────────────
# COPILOT CLIENTES — Análise de Clientes com IA
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIGenerationThrottle])
def copilot_extract_client_data(request):
    """
    POST — Extrai dados de documento uploadado (CPF/CNPJ, RG, Contrato Social).

    Form-data:
    - file: arquivo PDF/DOCX/IMG
    - document_type: cpf|cnpj|rg|contrato_social (opcional)
    """
    from .services.client_ai_service import ClientAIService

    if 'file' not in request.FILES:
        return Response({'error': 'Nenhum arquivo enviado'}, status=status.HTTP_400_BAD_REQUEST)

    uploaded_file = request.FILES['file']
    document_type = request.data.get('document_type')

    result = ClientAIService.extract_data_from_document_sync(
        file_content=uploaded_file.read(),
        filename=uploaded_file.name,
        document_type=document_type,
    )

    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIGenerationThrottle])
def copilot_check_client_conflict(request):
    """
    POST — Verifica conflito de interesses com novo cliente.

    Body:
    {
        "client_name": "João Silva",
        "cpf_cnpj": "000.000.000-00",
        "company_name": "Empresa XYZ",
        "case_description": "Descrição do caso..."
    }
    """
    from .services.client_ai_service import ClientAIService

    data = request.data

    result = ClientAIService.check_conflict_of_interest_sync(
        client_name=data.get('client_name', ''),
        cpf_cnpj=data.get('cpf_cnpj'),
        company_name=data.get('company_name'),
        case_description=data.get('case_description'),
    )

    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIGenerationThrottle])
def copilot_suggest_client_fees(request):
    """
    POST — Sugere faixa de honorários para cliente/caso.

    Body:
    {
        "client_data": {...},
        "case_data": {
            "specialty": "civel",
            "valor_causa": 100000,
            "complexity": "medio",
            "fase": "inicial"
        }
    }
    """
    from .services.client_ai_service import ClientAIService

    data = request.data

    result = ClientAIService.suggest_fee_range_sync(
        client_data=data.get('client_data', {}),
        case_data=data.get('case_data'),
    )

    return Response(result)


# ─────────────────────────────────────────────────────────────────────────────
# KPIs GAMIFICADOS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def kpi_recalculate(request):
    """Recalcula KPIs para um período."""
    from .services.kpi_service import KPIService
    from datetime import date

    year = int(request.data.get('year', timezone.now().year))
    month = int(request.data.get('month', timezone.now().month))

    period_start = date(year, month, 1)
    if month == 12:
        period_end = date(year + 1, 1, 1)
    else:
        period_end = date(year, month + 1, 1)

    from datetime import timedelta
    period_end = period_end - timedelta(days=1)

    scores = KPIService.calculate_period_scores(period_start, period_end)

    return Response({
        'message': f'{len(scores)} advogados calculados',
        'period_start': str(period_start),
        'period_end': str(period_end),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def kpi_my_scores(request):
    """Retorna KPIs do advogado logado."""
    from .models import LawyerScore
    from .serializers import LawyerScoreSerializer

    scores = LawyerScore.objects.filter(lawyer=request.user).order_by('-period_start')[:12]
    return Response(LawyerScoreSerializer(scores, many=True).data)


# ─────────────────────────────────────────────────────────────────────────────
# OCR DE DOCUMENTOS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([OCRUploadThrottle])
def ocr_extract_text(request):
    """Extrai texto de PDF/imagem escaneada via OCR."""
    from .services.ocr_service import OCRService

    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return Response({'error': 'Arquivo obrigatório (campo: file)'}, status=status.HTTP_400_BAD_REQUEST)

    language = request.data.get('language', 'por')
    result = OCRService.extract_from_upload(uploaded_file, language)

    return Response(result)


# ─────────────────────────────────────────────────────────────────────────────
# PETIÇÃO POR IA (CASO ESPECÍFICO)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIGenerationThrottle])
def generate_petition(request):
    """Gera petição completa baseada nos dados do caso."""
    from .services.petition_ai_service import PetitionAIService

    case_id = request.data.get('case_id') or request.data.get('caso_id') or request.data.get('caso')
    petition_type = request.data.get('petition_type') or request.data.get('tipo')
    extra_instructions = request.data.get('extra_instructions', '')

    if not case_id or not petition_type:
        return Response(
            {
                'error': 'case_id e petition_type são obrigatórios',
                'received_fields': list(request.data.keys()),
                'case_id_received': bool(case_id),
                'petition_type_received': bool(petition_type),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        result = PetitionAIService.generate_petition(
            case_id, petition_type, extra_instructions, request.user
        )
    except Exception as e:
        return Response(
            {'error': f'Erro interno ao gerar petição: {str(e)}', 'success': False},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if result.get('success'):
        return Response(result)
    return Response(result, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def petition_types_list(request):
    """Lista tipos de petição disponíveis."""
    from .services.petition_ai_service import PetitionAIService
    return Response(PetitionAIService.list_petition_types())


# ─────────────────────────────────────────────────────────────────────────────
# KANBAN DE TAREFAS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tasks_kanban(request):
    """Retorna tarefas em formato Kanban (agrupadas por status)."""
    qs = CaseTask.objects.select_related('caso', 'responsavel').all()

    case_id = request.query_params.get('case_id')
    if case_id:
        qs = qs.filter(caso_id=case_id)
    else:
        # Show only user's tasks if no case filter
        qs = qs.filter(responsavel=request.user)

    columns = [
        {'id': 'pendente', 'title': 'A Fazer', 'status': 'pendente', 'color': '#6B7280'},
        {'id': 'em_andamento', 'title': 'Em Andamento', 'status': 'em_andamento', 'color': '#3B82F6'},
        {'id': 'concluida', 'title': 'Concluída', 'status': 'concluida', 'color': '#10B981'},
        {'id': 'cancelada', 'title': 'Cancelada', 'status': 'cancelada', 'color': '#EF4444'},
    ]

    for col in columns:
        tasks = qs.filter(status=col['status'])
        col['tasks'] = CaseTaskSerializer(tasks, many=True).data

    return Response(columns)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def task_move(request, task_id):
    """Move tarefa para outro status (drag & drop do Kanban)."""
    try:
        task = CaseTask.objects.select_related('caso__advogado_responsavel', 'caso__created_by', 'responsavel').get(id=task_id)
    except CaseTask.DoesNotExist:
        return Response({'error': 'Tarefa não encontrada'}, status=status.HTTP_404_NOT_FOUND)

    if not _is_privileged(request.user):
        if not (
            check_object_permission(request.user, task)
            or task.responsavel_id == request.user.id
        ):
            return _deny()

    new_status = request.data.get('status')
    if new_status not in dict(CaseTask.STATUS_CHOICES):
        return Response({'error': 'Status inválido'}, status=status.HTTP_400_BAD_REQUEST)

    task.status = new_status
    if new_status == 'concluida':
        task.data_conclusao = timezone.now().date()
    task.save(update_fields=['status', 'data_conclusao', 'updated_at'])

    return Response(CaseTaskSerializer(task).data)


# ─────────────────────────────────────────────────────────────────────────────
# NFS-e (NOTA FISCAL DE SERVIÇO)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def nfse_list_create(request):
    """GET — Lista NFS-e. POST — Cria NFS-e (rascunho)."""
    from .models import InvoiceNFSe
    from .serializers import InvoiceNFSeSerializer

    if request.method == 'GET':
        qs = InvoiceNFSe.objects.select_related('client', 'caso').all()

        # Non-privileged users only see their own NFS-e or those on their cases
        if not _is_privileged(request.user):
            qs = qs.filter(
                Q(created_by=request.user) |
                Q(caso__advogado_responsavel=request.user) |
                Q(caso__created_by=request.user)
            )

        client_id = request.query_params.get('client')
        if client_id:
            qs = qs.filter(client_id=client_id)

        nfse_status = request.query_params.get('status')
        if nfse_status:
            qs = qs.filter(status=nfse_status)

        page, paginator = paginate_queryset(request, qs)
        if page is not None:
            return paginator.get_paginated_response(InvoiceNFSeSerializer(page, many=True).data)
        return Response(InvoiceNFSeSerializer(qs, many=True).data)

    serializer = InvoiceNFSeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def nfse_detail(request, nfse_id):
    """CRUD de NFS-e."""
    from .models import InvoiceNFSe
    from .serializers import InvoiceNFSeSerializer

    try:
        nfse = InvoiceNFSe.objects.select_related('caso', 'client').get(id=nfse_id)
    except InvoiceNFSe.DoesNotExist:
        return Response({'error': 'NFS-e não encontrada'}, status=status.HTTP_404_NOT_FOUND)

    # Permission: created_by or case access
    if not check_object_permission(request.user, nfse):
        return _deny()

    if request.method == 'GET':
        return Response(InvoiceNFSeSerializer(nfse).data)

    if request.method == 'PUT':
        serializer = InvoiceNFSeSerializer(nfse, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    nfse.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([NFSeEmitThrottle])
def nfse_emit(request, nfse_id):
    """Emite NFS-e na prefeitura."""
    from .models import InvoiceNFSe
    from .serializers import InvoiceNFSeSerializer
    from apps.integration.services.nfse_service import NFSeService

    try:
        nfse = InvoiceNFSe.objects.select_related('client', 'caso').get(id=nfse_id)
    except InvoiceNFSe.DoesNotExist:
        return Response({'error': 'NFS-e não encontrada'}, status=status.HTTP_404_NOT_FOUND)

    # Permission: created_by or privileged (emitting is a sensitive action)
    if not check_object_permission(request.user, nfse):
        return _deny()

    service = NFSeService()
    if not service.is_configured:
        return Response({
            'error': 'NFS-e não configurada',
            'setup_required': True,
            'env_vars': ['NFSE_CNPJ', 'NFSE_INSCRICAO_MUNICIPAL', 'NFSE_CERTIFICATE_PATH', 'NFSE_CERTIFICATE_PASSWORD', 'NFSE_MUNICIPIO'],
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    result = service.emitir_nfse({
        'tomador': {
            'cpf_cnpj': nfse.client.cpf_cnpj,
            'nome': nfse.client.name,
            'email': nfse.client.email,
        },
        'servico': {
            'descricao': nfse.descricao_servico,
            'valor': float(nfse.valor_servico),
            'codigo_cnae': nfse.codigo_servico,
        },
        'competencia': str(nfse.data_competencia),
    })

    if result.get('success'):
        data = result.get('data', {})
        nfse.status = 'authorized'
        nfse.numero_nfse = data.get('numero_nfse', '')
        nfse.codigo_verificacao = data.get('codigo_verificacao', '')
        nfse.data_emissao = timezone.now()
        nfse.xml_retorno = data.get('xml', '')
        nfse.save()
        return Response(InvoiceNFSeSerializer(nfse).data)
    else:
        nfse.status = 'error'
        nfse.error_message = result.get('error', '')
        nfse.save(update_fields=['status', 'error_message'])
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────────────────────────
# INTEGRAÇÃO ASSINATURA DIGITAL (D4Sign/DocuSign/GOV.BR)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def signature_providers_status(request):
    """Retorna status de configuração de cada provider de assinatura."""
    from apps.integration.services.d4sign_service import D4SignService
    from apps.integration.services.docusign_service import DocuSignService
    from apps.integration.services.govbr_service import GovBRService

    return Response({
        'providers': [
            {'provider': 'd4sign', 'name': 'D4Sign', 'is_configured': D4SignService().is_configured},
            {'provider': 'docusign', 'name': 'DocuSign', 'is_configured': DocuSignService().is_configured},
            {'provider': 'govbr', 'name': 'GOV.BR', 'is_configured': GovBRService().is_configured},
        ]
    })


# ─────────────────────────────────────────────────────────────────────────────
# INTEGRAÇÃO CALENDAR (Google/Outlook)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def calendar_sync_providers(request):
    """Retorna status dos providers de calendário."""
    from .services.calendar_sync_service import CalendarSyncService

    providers = []
    for key, config in CalendarSyncService.PROVIDERS.items():
        result = CalendarSyncService.get_auth_url(key, request.user.id, request.build_absolute_uri('/callback'))
        providers.append({
            'provider': key,
            'name': config['name'],
            'is_configured': not result.get('setup_required', False),
            'auth_url': result.get('auth_url', ''),
            'setup_required': result.get('setup_required', False),
            'env_vars': result.get('env_vars', []),
        })

    return Response({'providers': providers})


# ─────────────────────────────────────────────────────────────────────────────
# INTEGRAÇÃO TRIBUNAIS (PJe/e-SAJ)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tribunal_integration_status(request):
    """Retorna status das integrações com tribunais."""
    from apps.integration.services.pje_real_service import PJeRealService
    from apps.integration.services.esaj_real_service import ESAJRealService

    pje = PJeRealService()
    esaj = ESAJRealService()

    return Response({
        'pje': {
            'is_configured': pje.is_configured,
            'supported_tribunals': pje.list_supported_tribunals(),
        },
        'esaj': {
            'is_configured': esaj.is_configured,
            'supported_tribunals': esaj.list_supported_tribunals(),
        },
    })


# ─────────────────────────────────────────────────────────────────────────────
# HISTÓRICO DE AVALIAÇÃO DE RISCO
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def risk_assessments_list_create(request, case_id):
    """GET — Histórico de avaliações de risco. POST — Nova avaliação."""
    from .models import RiskAssessment
    from .serializers import RiskAssessmentSerializer

    # Permission: check case access
    try:
        caso = LegalCase.objects.select_related('advogado_responsavel', 'created_by').get(id=case_id)
    except LegalCase.DoesNotExist:
        return Response({'error': 'Caso não encontrado'}, status=status.HTTP_404_NOT_FOUND)
    if not user_can_access_case(request.user, caso):
        return _deny()

    if request.method == 'GET':
        qs = RiskAssessment.objects.filter(caso_id=case_id).order_by('-created_at')
        return Response(RiskAssessmentSerializer(qs, many=True).data)

    # POST — criar nova avaliação
    data = {**request.data, 'caso': str(case_id)}

    # Buscar nível anterior
    last = RiskAssessment.objects.filter(caso_id=case_id).order_by('-created_at').first()

    serializer = RiskAssessmentSerializer(data=data)
    if serializer.is_valid():
        obj = serializer.save(assessed_by=request.user)
        if last:
            obj.previous_level = last.risk_level
            obj.level_changed = obj.risk_level != last.risk_level
            obj.save(update_fields=['previous_level', 'level_changed'])
        return Response(RiskAssessmentSerializer(obj).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIGenerationThrottle])
def risk_assessment_ai(request, case_id):
    """Gera avaliação de risco com IA."""
    from .models import LegalCase, RiskAssessment
    from .serializers import RiskAssessmentSerializer

    try:
        case = LegalCase.objects.select_related('client', 'advogado_responsavel', 'created_by').get(id=case_id)
    except LegalCase.DoesNotExist:
        return Response({'error': 'Caso não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    # Permission: case access
    if not user_can_access_case(request.user, case):
        return _deny()

    # Build context
    deadlines_missed = case.prazos.filter(status='atrasado').count()
    deadlines_total = case.prazos.count()
    tasks_pending = case.tarefas.filter(status__in=['pendente', 'em_andamento']).count()

    context = f"""Caso: {case.titulo}
Especialidade: {case.get_especialidade_display()}
Status: {case.get_status_display()}
Fase: {case.get_fase_display()}
Valor da Causa: R$ {case.valor_causa or 0}
Prazos perdidos: {deadlines_missed}/{deadlines_total}
Tarefas pendentes: {tasks_pending}
Descrição: {case.descricao or 'Não informada'}"""

    try:
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService
        llm = UnifiedLLMService()
        response = llm.generate(
            system_prompt="""Você é um analista de risco jurídico. Avalie o risco do caso e retorne JSON:
{"risk_level": "very_low|low|medium|high|very_high|critical", "risk_score": 0-100,
"factors": [{"name": "...", "weight": 1-10, "description": "..."}],
"analysis": "análise detalhada", "recommendation": "recomendações"}""",
            user_prompt=context,
            max_tokens=2000,
            temperature=0.3,
            user=request.user if request.user.is_authenticated else None,
            usage_type='analysis',
            description=f'Avaliacao de risco IA - Caso {case_id}',
        )

        import json, re
        content = response.get('content', '')
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            ai_data = json.loads(match.group(0))
        else:
            ai_data = {'risk_level': 'medium', 'risk_score': 50, 'analysis': content, 'factors': [], 'recommendation': ''}

        last = RiskAssessment.objects.filter(caso_id=case_id).order_by('-created_at').first()

        assessment = RiskAssessment.objects.create(
            caso=case,
            risk_level=ai_data.get('risk_level', 'medium'),
            risk_score=ai_data.get('risk_score', 50),
            factors=ai_data.get('factors', []),
            analysis=ai_data.get('analysis', ''),
            recommendation=ai_data.get('recommendation', ''),
            trigger='ai_analysis',
            previous_level=last.risk_level if last else '',
            level_changed=last.risk_level != ai_data.get('risk_level') if last else False,
            ai_generated=True,
            ai_model=response.get('model', ''),
            tokens_used=response.get('total_tokens', 0),
            assessed_by=request.user,
        )

        return Response(RiskAssessmentSerializer(assessment).data, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"Risk assessment AI error: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────────────────────────────────
# COPILOT INTEGRATIONS (Tribunal, DataJud, Prazos)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIGenerationThrottle])
def copilot_analyze_context(request):
    """Envia contexto de qualquer funcionalidade para o Copilot analisar."""
    context_type = request.data.get('context_type', '')  # tribunal, datajud, prazo, risco
    context_data = request.data.get('context_data', {})
    question = request.data.get('question', '')

    if not question:
        return Response({'error': 'question é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

    prompts = {
        'tribunal': 'Você é um especialista em acompanhamento processual. Analise os dados do tribunal e responda:',
        'datajud': 'Você é um especialista em consulta processual via DataJud/CNJ. Analise os dados e responda:',
        'prazo': 'Você é um especialista em gestão de prazos processuais. Analise os prazos e responda:',
        'risco': 'Você é um analista de risco jurídico. Analise a avaliação de risco e responda:',
        'calendario': 'Você é um especialista em gestão de agenda jurídica. Analise o calendário e responda:',
    }

    system_prompt = prompts.get(context_type, 'Você é um assistente jurídico. Responda:')

    try:
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService
        llm = UnifiedLLMService()
        response = llm.generate(
            system_prompt=system_prompt,
            user_prompt=f"CONTEXTO:\n{str(context_data)}\n\nPERGUNTA:\n{question}",
            max_tokens=2000,
            temperature=0.4,
        )
        return Response({
            'answer': response.get('content', ''),
            'tokens_used': response.get('total_tokens', 0),
            'context_type': context_type,
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────────────────────────────────
# COPILOT DOCUMENTOS — Geração e Revisão de Documentos
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIGenerationThrottle])
def copilot_generate_document(request):
    """
    POST — Gera documento jurídico via IA.

    Body:
    {
        "prompt": "Descrição do documento a gerar",
        "template_type": "peticao_inicial|contestacao|recurso_apelacao|...",
        "context": {
            "cliente_nome": "João Silva",
            "parte_contraria": "Empresa X",
            "fatos": "Descrição dos fatos...",
            "fundamentos": "Fundamentos jurídicos...",
            "pedidos": "Pedidos..."
        }
    }
    """
    from .services.document_ai_service import DocumentAIService

    data = request.data
    prompt = data.get('prompt', '')
    template_type = data.get('template_type', 'peticao_inicial')
    context = data.get('context', {})

    if not prompt:
        return Response({'error': 'prompt é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

    result = DocumentAIService.generate_document(
        prompt=prompt,
        template_type=template_type,
        context=context,
    )

    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIGenerationThrottle])
def copilot_review_document(request):
    """
    POST — Revisa documento jurídico buscando erros e inconsistências.

    Body:
    {
        "content": "Conteúdo do documento...",
        "doc_type": "peticao_inicial|contestacao|..."
    }
    """
    from .services.document_ai_service import DocumentAIService

    data = request.data
    content = data.get('content', '')
    doc_type = data.get('doc_type', 'peticao_inicial')

    if not content:
        return Response({'error': 'content é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

    result = DocumentAIService.review_document(
        content=content,
        doc_type=doc_type,
    )

    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIGenerationThrottle])
def copilot_suggest_template(request):
    """
    POST — Sugere modelo de documento baseado no tipo de caso.

    Body:
    {
        "case_data": {
            "specialty": "civel|criminal|trabalhista|...",
            "phase": "inicial|contestacao|recursal|...",
            "case_type": "acao|defesa|recurso|..."
        }
    }
    """
    from .services.document_ai_service import DocumentAIService

    data = request.data
    case_data = data.get('case_data', {})

    if not case_data:
        return Response({'error': 'case_data é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

    result = DocumentAIService.suggest_template(
        case_data=case_data,
    )

    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIGenerationThrottle])
def copilot_auto_fill(request):
    """
    POST — Preenche template automaticamente com dados do caso.

    Body:
    {
        "template": "Texto do template com {{placeholders}}",
        "case_data": {
            "cliente_nome": "João Silva",
            "nacionalidade": "brasileiro",
            "estado_civil": "casado",
            "profissao": "engenheiro",
            ...
        }
    }
    """
    from .services.document_ai_service import DocumentAIService

    data = request.data
    template = data.get('template', '')
    case_data = data.get('case_data', {})

    if not template:
        return Response({'error': 'template é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

    result = DocumentAIService.auto_fill_template(
        template=template,
        case_data=case_data,
    )

    return Response(result)


# ─────────────────────────────────────────────────────────────────────────────
# COPILOT EQUIPE — Sugestão de Alocação de Equipes com IA
# ─────────────────────────────────────────────────────────────────────────────


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIGenerationThrottle])
def copilot_team_suggest(request):
    """
    POST — Sugere equipes para alocação em caso jurídico.

    Body:
    {
        "case_id": "uuid-do-caso" (opcional),
        "case_data": {
            "specialty": "civel|criminal|trabalhista|...",
            "complexity": "baixa|media|alta",
            "valor_causa": 100000,
            "urgency": true/false,
            "fase": "inicial|contestacao|recursal|..."
        }
    }
    """
    from .services.team_ai_service import TeamAIService
    from apps.accounts.models import Team, TeamAssignment
    from apps.cases.models import LegalCase

    data = request.data
    case_id = data.get('case_id')
    case_data = data.get('case_data', {})

    # Se case_id fornecido, buscar dados do caso
    if case_id:
        try:
            case = LegalCase.objects.filter(id=case_id).first()
            if case:
                case_data = {
                    'specialty': case.specialty or case_data.get('specialty'),
                    'complexity': case.complexity or case_data.get('complexity', 'media'),
                    'valor_causa': float(case.valor_causa) if case.valor_causa else case_data.get('valor_causa', 0),
                    'urgency': case.urgency if hasattr(case, 'urgency') else case_data.get('urgency', False),
                    'fase': case.fase or case_data.get('fase'),
                }
        except Exception as e:
            logger.warning(f'Erro ao buscar caso {case_id}: {e}')

    # Buscar todas as equipes ativas
    teams = Team.objects.filter(is_active=True).prefetch_related('members', 'assignments')

    # Preparar dados das equipes
    available_teams = []
    for team in teams:
        active_cases = team.assignments.filter(
            case__status__in=['ativo', 'aguardando', 'suspenso']
        ).count()
        available_teams.append({
            'id': str(team.id),
            'name': team.name,
            'specialty': team.specialty,
            'members_count': team.members.count(),
            'active_cases': active_cases,
        })

    # Usar fallback heurístico (método síncrono)
    suggestions = TeamAIService._heuristic_suggestion(
        case_data=case_data,
        available_teams=available_teams,
    )

    return Response({
        'suggestions': suggestions,
        'case_data': case_data,
        'total_teams': len(available_teams),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIGenerationThrottle])
def copilot_team_balance(request):
    """
    GET — Analisa balanceamento de carga de trabalho entre equipes.

    Query params:
    - user_id: ID do usuário (opcional, para filtrar equipes do usuário)
    """
    from .services.team_ai_service import TeamAIService
    from apps.accounts.models import Team, TeamAssignment

    user_id = request.query_params.get('user_id')

    # Buscar todas as equipes ativas
    teams_qs = Team.objects.filter(is_active=True).prefetch_related('members', 'assignments')

    # Preparar dados das equipes
    teams_data = []
    for team in teams_qs:
        active_cases = team.assignments.filter(
            case__status__in=['ativo', 'aguardando', 'suspenso']
        ).count()
        teams_data.append({
            'id': str(team.id),
            'name': team.name,
            'specialty': team.specialty,
            'members_count': team.members.count(),
            'active_cases': active_cases,
        })

    # Calcular análise heurística diretamente
    from django.db.models import Avg
    total_cases = sum(t['active_cases'] for t in teams_data)
    avg_cases = total_cases / len(teams_data) if teams_data else 0

    result = TeamAIService._heuristic_balance(
        teams_data=teams_data,
        avg_cases=avg_cases,
    )

    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIGenerationThrottle])
def copilot_team_availability(request):
    """
    GET — Prevê disponibilidade de equipe para novo caso.

    Query params:
    - team_id: ID da equipe (obrigatório)
    - urgent: true/false (opcional, default false)
    """
    from .services.team_ai_service import TeamAIService

    team_id = request.query_params.get('team_id')
    urgent = request.query_params.get('urgent', 'false').lower() == 'true'

    if not team_id:
        return Response(
            {'error': 'team_id é obrigatório'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Análise síncrona simples de disponibilidade
    from apps.accounts.models import Team
    try:
        team = Team.objects.filter(id=team_id).first()
        if not team:
            return Response(
                {'error': 'Equipe não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )

        active_cases = team.assignments.filter(
            case__status__in=['ativo', 'aguardando', 'suspenso']
        ).count()
        members_count = team.members.count() or 1

        # Score baseado em casos por membro
        cases_per_member = active_cases / members_count
        base_score = max(0, 100 - (cases_per_member * 10))

        if urgent:
            base_score *= 0.7  # Reduz score para urgentes se carga alta

        result = {
            'available': base_score >= 50,
            'availability_score': int(min(100, max(0, base_score))),
            'estimated_capacity': max(0, 10 - active_cases),
            'factors': [
                f'{active_cases} casos ativos',
                f'{members_count} membros',
                f'{cases_per_member:.1f} casos/membro',
            ],
            'recommendation': 'Equipe disponível' if base_score >= 50 else 'Equipe com carga elevada',
        }
    except Exception as e:
        result = {
            'available': False,
            'availability_score': 0,
            'error': str(e),
        }

    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def copilot_team_match_specialty(request):
    """
    GET — Faz match de equipes por especialidade.

    Query params:
    - specialty: especialidade do caso (obrigatório)
    - include_related: true/false (opcional, default true)
    """
    from .services.team_ai_service import TeamAIService
    from apps.accounts.models import Team, TeamAssignment

    specialty = request.query_params.get('specialty')
    include_related = request.query_params.get('include_related', 'true').lower() == 'true'

    if not specialty:
        return Response(
            {'error': 'specialty é obrigatório'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Buscar todas as equipes ativas
    teams = Team.objects.filter(is_active=True).prefetch_related('members', 'assignments')

    # Preparar dados das equipes
    teams_data = []
    for team in teams:
        active_cases = team.assignments.filter(
            case__status__in=['ativo', 'aguardando', 'suspenso']
        ).count()
        teams_data.append({
            'id': str(team.id),
            'name': team.name,
            'specialty': team.specialty,
            'members_count': team.members.count(),
            'active_cases': active_cases,
        })

    matches = TeamAIService.match_specialty(
        case_specialty=specialty,
        teams=teams_data,
        include_related=include_related,
    )

    return Response({
        'specialty': specialty,
        'matches': matches,
        'total': len(matches),
    })


# ─────────────────────────────────────────────────────────────────────────────
# COPILOT TRIBUNAL PUSH — Análise de Movimentações
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def copilot_analyze_movement(request):
    """
    POST /api/v1/processos/copilot/tribunal-push/analisar/

    Analisa uma movimentação processual com IA e retorna interpretação jurídica.

    Body:
    - movement_text: texto da movimentação
    - case_id (opcional): ID do caso para contexto adicional
    """
    from .services.push_analysis_service import PushAnalysisService

    movement_text = request.data.get('movement_text')
    case_id = request.data.get('case_id')

    if not movement_text:
        return Response(
            {'error': 'movement_text é obrigatório'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Buscar dados do caso se fornecido
    case_data = None
    if case_id:
        try:
            case = LegalCase.objects.get(id=case_id)
            if not check_object_permission(request.user, case):
                return Response(
                    {'error': 'Acesso negado ao caso'},
                    status=status.HTTP_403_FORBIDDEN
                )
            case_data = {
                'numero_processo': case.numero_processo,
                'titulo': case.titulo,
                'area': case.area,
                'fase_atual': case.fase_atual,
            }
        except LegalCase.DoesNotExist:
            return Response(
                {'error': 'Caso não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

    # Usar fallback heurístico (método síncrono)
    result = PushAnalysisService._heuristic_analysis(movement_text, case_data)

    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def copilot_suggest_actions(request):
    """
    POST /api/v1/processos/copilot/tribunal-push/sugerir-acoes/

    Sugere ações práticas baseadas no tipo de movimentação processual.

    Body:
    - movement_type: tipo de evento (movimentacao, intimacao, publicacao, etc.)
    - case_id (opcional): ID do caso para contexto
    - fase (opcional): fase atual do processo
    """
    from .services.push_analysis_service import PushAnalysisService

    movement_type = request.data.get('movement_type')
    case_id = request.data.get('case_id')

    if not movement_type:
        return Response(
            {'error': 'movement_type é obrigatório'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Buscar contexto do caso se fornecido
    case_context = None
    if case_id:
        try:
            case = LegalCase.objects.get(id=case_id)
            if not check_object_permission(request.user, case):
                return Response(
                    {'error': 'Acesso negado ao caso'},
                    status=status.HTTP_403_FORBIDDEN
                )
            case_context = {
                'fase': case.fase_atual,
                'ultimas_acoes': '',
                'prazos_ativos': '',
            }
        except LegalCase.DoesNotExist:
            case_context = None

    # Usar fallback heurístico (método síncrono)
    base_actions = PushAnalysisService.ACTION_SUGGESTIONS.get(
        movement_type,
        ['Verificar teor do evento', 'Acompanhar andamento']
    )
    suggestions = [
        {'action': action, 'priority': 'media', 'estimated_time': '30min', 'category': 'analise'}
        for action in base_actions[:3]
    ]

    return Response({'suggestions': suggestions})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def copilot_summarize_publication(request):
    """
    POST /api/v1/processos/copilot/tribunal-push/resumir/

    Resume uma publicação do Diário Oficial mantendo informações críticas.

    Body:
    - publication_text: texto completo da publicação
    """
    from .services.push_analysis_service import PushAnalysisService

    publication_text = request.data.get('publication_text')

    if not publication_text:
        return Response(
            {'error': 'publication_text é obrigatório'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Usar fallback extrativo (método síncrono)
    summary = PushAnalysisService._extractive_summary(publication_text)

    return Response({'summary': summary})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def copilot_classify_relevance(request):
    """
    POST /api/v1/processos/copilot/tribunal-push/classificar/

    Classifica a relevância de uma movimentação processual (alta/média/baixa).

    Body:
    - event_type: tipo de evento
    - description: descrição da movimentação
    - case_priority (opcional): prioridade do caso (alta/normal/baixa)
    """
    from .services.push_analysis_service import PushAnalysisService

    event_type = request.data.get('event_type')
    description = request.data.get('description')
    case_priority = request.data.get('case_priority', 'normal')

    if not event_type or not description:
        return Response(
            {'error': 'event_type e description são obrigatórios'},
            status=status.HTTP_400_BAD_REQUEST
        )

    movement = {
        'event_type': event_type,
        'description': description,
    }

    # Usar método síncrono de fallback heurístico
    matched_keywords = []
    high_keywords = PushAnalysisService.HIGH_RELEVANCE_KEYWORDS.get(event_type, [])
    desc_lower = description.lower() if description else ''
    matched_keywords = [kw for kw in high_keywords if kw in desc_lower]

    result = PushAnalysisService._heuristic_relevance(
        event_type, description, case_priority, matched_keywords
    )

    return Response(result)


# =============================================================================
# FASE 4 — CNJ Parser + Iniciar Fluxo por Processo
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cnj_parse(request):
    """
    GET /processos/cnj/parse/?numero=0001234-12.2024.8.26.0100

    Valida e faz o parsing de um número CNJ, retornando tribunal, ano, etc.
    """
    from .cnj_parser import parse_cnj
    numero = request.query_params.get('numero', '').strip()
    if not numero:
        return Response({'error': 'Parâmetro "numero" obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
    result = parse_cnj(numero)
    return Response(result.to_dict())


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def case_start_flow(request, case_id):
    """
    POST /processos/{case_id}/iniciar-fluxo/

    Body: { "template_id": "<uuid>" }

    Inicia um FlowInstance para o caso e vincula via LegalCase.active_flow.
    """
    from apps.workflow_execution import service as flow_service

    try:
        case = LegalCase.objects.get(pk=case_id)
    except LegalCase.DoesNotExist:
        return Response({'detail': 'Caso não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    if case.active_flow and case.active_flow.status == 'running':
        return Response(
            {'detail': 'Este caso já possui um fluxo em andamento.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    template_id = request.data.get('template_id')
    if not template_id:
        return Response({'detail': 'Campo "template_id" obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    if not (hasattr(user, 'organ') and user.organ):
        return Response({'detail': 'Usuário não vinculado a um órgão.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        instance = flow_service.start_flow(
            template_id=template_id,
            organ=user.organ,
            started_by=user,
            case_id=str(case_id),
        )
    except ValueError as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    from apps.workflow_execution.serializers import FlowInstanceDetailSerializer
    return Response(FlowInstanceDetailSerializer(instance).data, status=status.HTTP_201_CREATED)

