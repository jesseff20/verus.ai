"""
Views para templates de documentos
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample
from .models import DocumentTemplate
from .serializers import (
    DocumentTemplateListSerializer,
    DocumentTemplateDetailSerializer,
    DocumentTemplateCreateSerializer,
    DocumentTemplateUpdateSerializer,
    DocumentTemplateDuplicateSerializer,
    TemplatePreviewSerializer,
)
from .permissions import CanManageDocumentTemplates
from .services import template_service


@extend_schema_view(
    list=extend_schema(
        summary="Listar templates de documento",
        description="Retorna lista de todos os templates de documento disponíveis",
        tags=["Templates - Documentos"],
        responses={200: DocumentTemplateListSerializer(many=True)}
    ),
    retrieve=extend_schema(
        summary="Buscar template por ID",
        description="Retorna detalhes completos de um template específico",
        tags=["Templates - Documentos"],
        responses={200: DocumentTemplateDetailSerializer}
    ),
    create=extend_schema(
        summary="Criar novo template",
        description="Cria um novo template de documento (apenas admin/manager)",
        tags=["Templates - Documentos"],
        request=DocumentTemplateCreateSerializer,
        responses={201: DocumentTemplateDetailSerializer},
        examples=[
            OpenApiExample(
                name="Template HTML simples",
                value={
                    "name": "Estudo Técnico Preliminar Básico HTML",
                    "description": "Template HTML para Documents básicos",
                    "blueprint": "uuid-do-blueprint",
                    "template_type": "html",
                    "content": "<html><body><h1>{{titulo}}</h1><p>{{descricao_necessidade}}</p></body></html>",
                    "custom_css": "body { font-family: Arial; }",
                    "is_active": True,
                    "is_default": False
                },
                request_only=True
            )
        ]
    ),
    update=extend_schema(
        summary="Atualizar template",
        description="Atualiza todos os campos de um template (apenas admin/manager)",
        tags=["Templates - Documentos"],
        request=DocumentTemplateUpdateSerializer,
        responses={200: DocumentTemplateDetailSerializer}
    ),
    partial_update=extend_schema(
        summary="Atualizar parcialmente template",
        description="Atualiza campos específicos de um template (apenas admin/manager)",
        tags=["Templates - Documentos"],
        request=DocumentTemplateUpdateSerializer,
        responses={200: DocumentTemplateDetailSerializer}
    ),
    destroy=extend_schema(
        summary="Deletar template",
        description="Remove um template do sistema (apenas admin/manager)",
        tags=["Templates - Documentos"],
        responses={204: None}
    ),
)
class DocumentTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de templates de documento

    - GET /templates/ - Lista templates (todos podem ver)
    - POST /templates/ - Cria template (apenas admin/manager)
    - GET /templates/{id}/ - Detalhe do template
    - PUT/PATCH /templates/{id}/ - Atualiza template (apenas admin/manager)
    - DELETE /templates/{id}/ - Deleta template (apenas admin/manager)
    """
    queryset = DocumentTemplate.objects.all()
    permission_classes = [CanManageDocumentTemplates]

    def get_serializer_class(self):
        """Retorna serializer apropriado por ação"""
        if self.action == 'list':
            return DocumentTemplateListSerializer
        elif self.action == 'create':
            return DocumentTemplateCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DocumentTemplateUpdateSerializer
        return DocumentTemplateDetailSerializer

    def get_queryset(self):
        """Filtra templates com query params"""
        queryset = DocumentTemplate.objects.select_related('created_by', 'form_template', 'blueprint')

        # Filtrar por blueprint (para saber quais templates usar para gerar documento)
        blueprint = self.request.query_params.get('blueprint', None)
        if blueprint:
            queryset = queryset.filter(blueprint_id=blueprint)

        # Filtrar por formulário associado
        form_template = self.request.query_params.get('form_template', None)
        if form_template:
            queryset = queryset.filter(form_template_id=form_template)

        # Filtrar por tipo de template
        template_type = self.request.query_params.get('template_type', None)
        if template_type:
            queryset = queryset.filter(template_type=template_type)

        # Apenas templates padrão
        default_only = self.request.query_params.get('default_only', None)
        if default_only and default_only.lower() == 'true':
            queryset = queryset.filter(is_default=True)

        # Filtrar por status ativo (admin vê inativos também)
        from apps.accounts.permissions import is_admin_or_manager
        if not is_admin_or_manager(self.request.user):
            queryset = queryset.filter(is_active=True)
        else:
            is_active = self.request.query_params.get('is_active', None)
            if is_active is not None:
                queryset = queryset.filter(
                    is_active=is_active.lower() == 'true')

        return queryset.order_by('-created_at')

    @extend_schema(
        summary="Duplicar template",
        description="Cria uma cópia do template com versão incrementada (apenas admin/manager)",
        tags=["Templates - Documentos"],
        request=DocumentTemplateDuplicateSerializer,
        responses={201: DocumentTemplateDetailSerializer}
    )
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplica um template existente"""
        template = self.get_object()
        serializer = DocumentTemplateDuplicateSerializer(data=request.data)

        if serializer.is_valid():
            new_template = template.duplicate(request.user)

            # Atualiza nome se fornecido
            if 'name' in serializer.validated_data:
                new_template.name = serializer.validated_data['name']
                new_template.save()

            response_serializer = DocumentTemplateDetailSerializer(
                new_template)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Ativar template",
        description="Ativa um template desativado (apenas admin/manager)",
        tags=["Templates - Documentos"],
        responses={200: OpenApiResponse(
            description="Template ativado com sucesso")}
    )
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Ativa um template"""
        template = self.get_object()
        template.is_active = True
        template.save()
        return Response({'detail': 'Template ativado com sucesso.'}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Desativar template",
        description="Desativa um template (apenas admin/manager)",
        tags=["Templates - Documentos"],
        responses={200: OpenApiResponse(
            description="Template desativado com sucesso")}
    )
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Desativa um template"""
        template = self.get_object()
        template.is_active = False
        template.save()
        return Response({'detail': 'Template desativado com sucesso.'}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Definir como padrão",
        description="Define este template como padrão para seu tipo de documento (apenas admin/manager)",
        tags=["Templates - Documentos"],
        responses={200: OpenApiResponse(
            description="Template definido como padrão")}
    )
    @action(detail=True, methods=['post'], url_path='set-default')
    def set_default(self, request, pk=None):
        """Define template como padrão para o tipo de documento"""
        template = self.get_object()

        # Remove padrão anterior do mesmo blueprint
        DocumentTemplate.objects.filter(
            blueprint=template.blueprint,
            is_default=True
        ).exclude(id=template.id).update(is_default=False)

        # Define novo padrão
        template.is_default = True
        template.save()

        blueprint_name = template.blueprint.name if template.blueprint else 'sem blueprint'
        return Response(
            {'detail': f'Template definido como padrão para {blueprint_name}.'},
            status=status.HTTP_200_OK
        )

    @extend_schema(
        summary="Extrair placeholders",
        description="Retorna lista de placeholders encontrados no template",
        tags=["Templates - Documentos"],
        responses={200: OpenApiResponse(description="Lista de placeholders")}
    )
    @action(detail=True, methods=['get'])
    def placeholders(self, request, pk=None):
        """Retorna placeholders do template"""
        template = self.get_object()
        placeholders = template.extract_placeholders()
        return Response({'placeholders': placeholders}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Preview do template",
        description="Gera preview do template preenchido com dados de teste",
        tags=["Templates - Documentos"],
        request=TemplatePreviewSerializer,
        responses={200: OpenApiResponse(
            description="HTML do template renderizado")},
        examples=[
            OpenApiExample(
                name="Dados para preview",
                value={
                    "data": {
                        "titulo": "Estudo Técnico Preliminar",
                        "descricao_necessidade": "Contratação de serviços de TI"
                    }
                },
                request_only=True
            )
        ]
    )
    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        """
        Gera preview do template com dados fornecidos.
        Usa renderização inteligente que remove linhas vazias automaticamente.
        """
        template = self.get_object()
        serializer = TemplatePreviewSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data['data']
            content = template.get_template_content()

            # Usar renderização inteligente (remove linhas vazias automaticamente)
            if template.template_type in ['html', 'tinymce']:
                rendered_content = template_service.render_html_smart(content, data)
            else:
                rendered_content = template_service.render_smart(content, data)

            return Response({
                'rendered_content': rendered_content,
                'template_type': template.template_type
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Obter conteúdo do template",
        description="Retorna o conteúdo bruto do template (do campo content ou arquivo)",
        tags=["Templates - Documentos"],
        responses={200: OpenApiResponse(description="Conteúdo do template")}
    )
    @action(detail=True, methods=['get'])
    def content(self, request, pk=None):
        """Retorna conteúdo bruto do template"""
        template = self.get_object()
        content = template.get_template_content()
        return Response({
            'content': content,
            'template_type': template.template_type,
            'has_file': template.has_file
        }, status=status.HTTP_200_OK)

