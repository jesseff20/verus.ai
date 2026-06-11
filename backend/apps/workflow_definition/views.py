"""
Views do app workflow_definition.
"""
import logging
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import FlowTemplate, FlowNode, FlowEdge, FlowVersion
from .serializers import (
    FlowTemplateListSerializer,
    FlowTemplateDetailSerializer,
    FlowTemplateSaveSerializer,
    FlowTemplatePublishSerializer,
    FlowVersionSerializer,
)
from .validators import validate_flow_for_publish

logger = logging.getLogger(__name__)


class FlowTemplateViewSet(viewsets.ModelViewSet):
    """
    CRUD de templates de fluxo.

    Endpoints especiais:
      POST   .../templates/{id}/save/    → salva nós e edges de uma vez
      POST   .../templates/{id}/publish/ → valida e publica
      POST   .../templates/{id}/duplicate/ → duplica como rascunho
      GET    .../templates/{id}/versions/ → lista versões publicadas
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = FlowTemplate.objects.prefetch_related('nodes', 'edges', 'versions')

        if user.is_staff:
            return qs.all()

        # Usuários veem templates do seu órgão + templates de sistema
        if hasattr(user, 'organ') and user.organ:
            return qs.filter(
                organ=user.organ
            ) | qs.filter(is_system_template=True)

        return qs.filter(is_system_template=True)

    def get_serializer_class(self):
        if self.action == 'list':
            return FlowTemplateListSerializer
        return FlowTemplateDetailSerializer

    def perform_create(self, serializer):
        user = self.request.user
        organ = getattr(user, 'organ', None)
        serializer.save(created_by=user, organ=organ)

    # ── Ação: salvar nós e edges atomicamente ─────────────────
    @action(detail=True, methods=['post'], url_path='save')
    def save_flow(self, request, pk=None):
        template = self.get_object()

        if template.is_system_template:
            return Response(
                {'error': 'Templates de sistema não podem ser editados.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if template.status == 'archived':
            return Response(
                {'error': 'Templates arquivados não podem ser editados.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = FlowTemplateSaveSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        with transaction.atomic():
            # Atualiza metadados do template
            template.name = data['name']
            template.description = data.get('description', '')
            template.category = data.get('category', template.category)
            template.status = 'draft'
            template.save()

            # Substitui todos os nós
            template.nodes.all().delete()
            for i, node_data in enumerate(data['nodes']):
                FlowNode.objects.create(
                    template=template,
                    order=i,
                    **node_data,
                )

            # Substitui todos as edges
            template.edges.all().delete()
            for edge_data in data['edges']:
                FlowEdge.objects.create(template=template, **edge_data)

        return Response(
            FlowTemplateDetailSerializer(template).data,
            status=status.HTTP_200_OK,
        )

    # ── Ação: publicar ────────────────────────────────────────
    @action(detail=True, methods=['post'], url_path='publish')
    def publish_flow(self, request, pk=None):
        template = self.get_object()

        if template.is_system_template:
            return Response(
                {'error': 'Templates de sistema não podem ser republicados.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Validação de integridade
        result = validate_flow_for_publish(template)
        if not result.valid:
            return Response(
                {'error': 'O fluxo não passou na validação.', 'details': result.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pub_serializer = FlowTemplatePublishSerializer(data=request.data)
        pub_serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            # Cria snapshot da versão
            snapshot = {
                'nodes': FlowTemplateDetailSerializer(template).data['nodes'],
                'edges': FlowTemplateDetailSerializer(template).data['edges'],
            }
            FlowVersion.objects.create(
                template=template,
                version_number=template.version,
                snapshot=snapshot,
                published_by=request.user,
                notes=pub_serializer.validated_data.get('notes', ''),
            )

            # Avança versão e marca como publicado
            template.version += 1
            template.status = 'published'
            template.published_at = timezone.now()
            template.save()

        logger.info(
            'Flow template published: %s v%s by %s',
            template.name, template.version - 1, request.user.username,
        )

        return Response(
            FlowTemplateDetailSerializer(template).data,
            status=status.HTTP_200_OK,
        )

    # ── Ação: duplicar ────────────────────────────────────────
    @action(detail=True, methods=['post'], url_path='duplicate')
    def duplicate_flow(self, request, pk=None):
        original = self.get_object()

        with transaction.atomic():
            new_template = FlowTemplate.objects.create(
                organ=getattr(request.user, 'organ', None),
                name=f'{original.name} (cópia)',
                description=original.description,
                category=original.category,
                status='draft',
                version=1,
                created_by=request.user,
            )
            for node in original.nodes.all():
                FlowNode.objects.create(
                    template=new_template,
                    node_id=node.node_id,
                    node_type=node.node_type,
                    label=node.label,
                    description=node.description,
                    role=node.role,
                    parent_node_id=node.parent_node_id,
                    position=node.position,
                    data=node.data,
                    order=node.order,
                )
            for edge in original.edges.all():
                FlowEdge.objects.create(
                    template=new_template,
                    edge_id=edge.edge_id,
                    source_node_id=edge.source_node_id,
                    target_node_id=edge.target_node_id,
                    source_handle=edge.source_handle,
                    target_handle=edge.target_handle,
                    label=edge.label,
                    condition=edge.condition,
                    data=edge.data,
                )

        return Response(
            FlowTemplateListSerializer(new_template).data,
            status=status.HTTP_201_CREATED,
        )

    # ── Ação: listar versões ──────────────────────────────────
    @action(detail=True, methods=['get'], url_path='versions')
    def list_versions(self, request, pk=None):
        template = self.get_object()
        versions = template.versions.all()
        return Response(FlowVersionSerializer(versions, many=True).data)
