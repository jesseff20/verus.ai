"""
Views para Colaboração em Tempo Real.

Endpoints:
  POST /api/v1/collaboration/sessions/
    - Criar nova sessão de colaboração

  GET /api/v1/collaboration/sessions/{id}/
    - Detalhes da sessão com colaboradores ativos

  POST /api/v1/collaboration/sessions/{id}/join/
    - Entrar na sessão

  POST /api/v1/collaboration/sessions/{id}/leave/
    - Sair da sessão

  POST /api/v1/collaboration/sessions/{id}/heartbeat/
    - Manter usuário ativo na sessão

  POST /api/v1/collaboration/sessions/{id}/operations/
    - Registrar operação de edição

  GET /api/v1/collaboration/sessions/{id}/operations/
    - Listar operações para sync

  GET/POST /api/v1/collaboration/sessions/{id}/comments/
    - Listar/criar comentários

  POST /api/v1/collaboration/sessions/{id}/comments/{comment_id}/resolve/
    - Resolver comentário

  GET/POST /api/v1/collaboration/sessions/{id}/suggestions/
    - Listar/criar sugestões

  POST /api/v1/collaboration/sessions/{id}/suggestions/{id}/review/
    - Revisar sugestão (aceitar/rejeitar)
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse

from .models import (
    CollaborationSession,
    CollaboratorPresence,
    OperationLog,
    Comment,
    Suggestion,
)
from .serializers import (
    CollaborationSessionSerializer,
    CollaborationSessionCreateSerializer,
    CollaboratorPresenceSerializer,
    OperationLogSerializer,
    CommentSerializer,
    CommentCreateSerializer,
    SuggestionSerializer,
    SuggestionCreateSerializer,
    SuggestionReviewSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="Listar sessões de colaboração",
        description="Retorna sessões ativas do usuário",
        tags=["Collaboration"],
    ),
    create=extend_schema(
        summary="Criar sessão de colaboração",
        description="Cria nova sessão para edição colaborativa",
        tags=["Collaboration"],
        request=CollaborationSessionCreateSerializer,
    ),
)
class CollaborationSessionViewSet(viewsets.ModelViewSet):
    """ViewSet para Sessões de Colaboração"""
    queryset = CollaborationSession.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return CollaborationSessionCreateSerializer
        return CollaborationSessionSerializer

    def get_queryset(self):
        from django.db.models import Q

        user = self.request.user
        # Sessions where user is creator OR active collaborator
        return CollaborationSession.objects.filter(
            Q(created_by=user) | Q(presences__user=user)
        ).select_related('created_by').prefetch_related('presences').distinct()

    def perform_create(self, serializer):
        session = serializer.save(created_by=self.request.user)
        # Criador entra automaticamente na sessão
        CollaboratorPresence.objects.create(
            session=session,
            user=self.request.user,
            status='editing',
        )

    @extend_schema(
        summary="Entrar na sessão",
        description="Registra usuário como colaborador na sessão",
        tags=["Collaboration"],
        responses={200: CollaboratorPresenceSerializer},
    )
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Entrar na sessão"""
        session = self.get_object()

        if not session.is_active():
            return Response(
                {'detail': 'Sessão não está ativa'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar limite de colaboradores
        active_count = session.presences.filter(
            left_at__isnull=True,
            last_heartbeat__gt=timezone.now() - timedelta(minutes=5)
        ).count()

        if active_count >= session.max_collaborators:
            return Response(
                {'detail': 'Sessão lotada'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Criar ou atualizar presença
        presence, created = CollaboratorPresence.objects.get_or_create(
            session=session,
            user=request.user,
            defaults={'status': 'editing'}
        )

        if not created:
            presence.left_at = None
            presence.status = 'editing'
            presence.save()

        serializer = CollaboratorPresenceSerializer(presence)
        return Response(serializer.data)

    @extend_schema(
        summary="Sair da sessão",
        description="Remove usuário da sessão",
        tags=["Collaboration"],
        responses={200: OpenApiResponse(description='Saída registrada')},
    )
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Sair da sessão"""
        session = self.get_object()

        try:
            presence = CollaboratorPresence.objects.get(
                session=session,
                user=request.user,
                left_at__isnull=True,
            )
            presence.left_at = timezone.now()
            presence.status = 'away'
            presence.save()
        except CollaboratorPresence.DoesNotExist:
            pass

        return Response({'detail': 'Saída registrada'})

    @extend_schema(
        summary="Manter heartbeat",
        description="Atualiza último heartbeat do usuário",
        tags=["Collaboration"],
        responses={200: OpenApiResponse(description='Heartbeat atualizado')},
    )
    @action(detail=True, methods=['post'])
    def heartbeat(self, request, pk=None):
        """Manter usuário ativo"""
        session = self.get_object()
        status_param = request.data.get('status', 'editing')
        cursor_position = request.data.get('cursor_position', 0)
        selected_section = request.data.get('selected_section', '')

        presence = CollaboratorPresence.objects.filter(
            session=session,
            user=request.user,
            left_at__isnull=True,
        ).first()

        if not presence:
            return Response(
                {'detail': 'Usuário não está na sessão'},
                status=status.HTTP_400_BAD_REQUEST
            )

        presence.last_heartbeat = timezone.now()
        presence.status = status_param
        presence.cursor_position = cursor_position
        presence.selected_section = selected_section
        presence.save()

        return Response({'detail': 'Heartbeat atualizado'})

    @extend_schema(
        summary="Listar colaboradores ativos",
        description="Retorna lista de colaboradores presentes na sessão",
        tags=["Collaboration"],
        responses={200: OpenApiResponse(description='Lista de colaboradores')},
    )
    @action(detail=True, methods=['get'])
    def collaborators(self, request, pk=None):
        """Listar colaboradores ativos"""
        session = self.get_object()

        # Filtrar colaboradores ativos (heartbeat nos últimos 30s)
        active_presences = session.presences.filter(
            left_at__isnull=True,
            last_heartbeat__gt=timezone.now() - timedelta(seconds=30)
        )

        serializer = CollaboratorPresenceSerializer(active_presences, many=True)
        return Response({
            'collaborators': serializer.data,
            'count': active_presences.count(),
        })

    @extend_schema(
        summary="Listar operações",
        description="Retorna operações para sincronização",
        tags=["Collaboration"],
        parameters=[
            OpenApiParameter(name='since_version', description='Versão mínima'),
        ],
        responses={200: OpenApiResponse(description='Lista de operações')},
    )
    @action(detail=True, methods=['get'])
    def operations(self, request, pk=None):
        """Listar operações para sync"""
        session = self.get_object()
        since_version = request.query_params.get('since_version', 0)

        operations = session.operations.filter(
            version__gt=int(since_version)
        ).order_by('version')

        paginator = PageNumberPagination()
        paginator.page_size = 100
        paginator.page_size_query_param = 'page_size'
        paginator.max_page_size = 200
        page = paginator.paginate_queryset(operations, request)
        if page is not None:
            serializer = OperationLogSerializer(page, many=True)
            return paginator.get_paginated_response({
                'operations': serializer.data,
                'latest_version': page[-1].version if page else 0,
            })
        serializer = OperationLogSerializer(operations, many=True)
        return Response({
            'operations': serializer.data,
            'latest_version': operations.last().version if operations else 0,
        })

    @extend_schema(
        summary="Registrar operação",
        description="Registra uma edição para OT",
        tags=["Collaboration"],
        request=OperationLogSerializer,
        responses={200: OpenApiResponse(description='Operação registrada')},
    )
    @operations.mapping.post
    def create_operation(self, request, pk=None):
        """Registrar operação"""
        session = self.get_object()

        if not session.is_active():
            return Response(
                {'detail': 'Sessão não está ativa'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = OperationLogSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        operation = serializer.save(
            session=session,
            user=request.user,
        )

        # Atualizar last_activity
        session.last_activity_at = timezone.now()
        session.save(update_fields=['last_activity_at'])

        return Response(OperationLogSerializer(operation).data)


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet para Comentários"""
    queryset = Comment.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return CommentCreateSerializer
        return CommentSerializer

    def get_queryset(self):
        # Filtrar por session_id via query param
        session_id = self.request.query_params.get('session_id')
        if session_id:
            return Comment.objects.filter(
                session_id=session_id,
                parent__isnull=True  # Apenas comentários de topo
            ).select_related('author', 'session').prefetch_related('replies')
        return Comment.objects.none()

    def perform_create(self, serializer):
        session_id = self.kwargs.get('session_id')
        session = get_object_or_404(CollaborationSession, id=session_id)
        serializer.save(author=self.request.user, session=session)

    @extend_schema(
        summary="Resolver comentário",
        description="Marca comentário como resolvido",
        tags=["Collaboration"],
        responses={200: OpenApiResponse(description='Comentário resolvido')},
    )
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolver comentário"""
        comment = self.get_object()
        comment.is_resolved = True
        comment.resolved_at = timezone.now()
        comment.resolved_by = request.user
        comment.save()

        return Response({'detail': 'Comentário resolvido'})


class SuggestionViewSet(viewsets.ModelViewSet):
    """ViewSet para Sugestões"""
    queryset = Suggestion.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return SuggestionCreateSerializer
        return SuggestionSerializer

    def get_queryset(self):
        session_id = self.request.query_params.get('session_id')
        if session_id:
            return Suggestion.objects.filter(
                session_id=session_id
            ).select_related('author', 'reviewed_by', 'session')
        return Suggestion.objects.none()

    def perform_create(self, serializer):
        session_id = self.kwargs.get('session_id')
        session = get_object_or_404(CollaborationSession, id=session_id)
        serializer.save(author=self.request.user, session=session)

    @extend_schema(
        summary="Revisar sugestão",
        description="Aceita ou rejeita sugestão",
        tags=["Collaboration"],
        request=SuggestionReviewSerializer,
        responses={200: OpenApiResponse(description='Sugestão revisada')},
    )
    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Revisar sugestão"""
        suggestion = self.get_object()
        serializer = SuggestionReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        suggestion.status = serializer.validated_data['status']
        suggestion.reviewed_at = timezone.now()
        suggestion.reviewed_by = request.user

        if serializer.validated_data.get('comment'):
            suggestion.comment = serializer.validated_data['comment']

        suggestion.save()

        return Response(SuggestionSerializer(suggestion).data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_session_for_document(request, document_id):
    """
    POST /api/v1/collaboration/documents/{id}/start-session/

    Cria sessão de colaboração para um documento existente.
    """
    from apps.documents.models import Document

    try:
        document = Document.objects.get(id=document_id)

        # Verificar permissão
        if document.user != request.user and not request.user.is_staff:
            return Response(
                {'detail': 'Sem permissão para criar sessão'},
                status=status.HTTP_403_FORBIDDEN
            )

        session = CollaborationSession.objects.create(
            document_id=document_id,
            document_type='legal',
            created_by=request.user,
            allow_comments=True,
            allow_suggestions=True,
        )

        # Criador entra automaticamente
        CollaboratorPresence.objects.create(
            session=session,
            user=request.user,
            status='editing',
        )

        return Response(CollaborationSessionSerializer(session).data, status=status.HTTP_201_CREATED)

    except Document.DoesNotExist:
        return Response(
            {'detail': 'Documento não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'detail': f'Erro ao criar sessão: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
