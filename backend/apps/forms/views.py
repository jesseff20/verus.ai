"""
Views para templates de formulários
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample
from django.db.models.deletion import ProtectedError
from .models import FormTemplate
from .serializers import (
    FormTemplateListSerializer,
    FormTemplateDetailSerializer,
    FormTemplateCreateSerializer,
    FormTemplateUpdateSerializer,
    FormTemplateDuplicateSerializer,
    FieldTypeInfoSerializer,
    AddFieldSerializer,
    UpdateFieldSerializer,
    ReorderFieldsSerializer,
)
from .permissions import CanManageFormTemplates


@extend_schema_view(
    list=extend_schema(
        summary="Listar templates de formulário",
        description="Retorna lista de todos os templates de formulário disponíveis",
        tags=["Forms - Templates"],
        responses={200: FormTemplateListSerializer(many=True)}
    ),
    retrieve=extend_schema(
        summary="Buscar template por ID",
        description="Retorna detalhes completos de um template específico, incluindo todos os campos",
        tags=["Forms - Templates"],
        responses={200: FormTemplateDetailSerializer}
    ),
    create=extend_schema(
        summary="Criar novo template",
        description="Cria um novo template de formulário (apenas admin/manager)",
        tags=["Forms - Templates"],
        request=FormTemplateCreateSerializer,
        responses={201: FormTemplateDetailSerializer},
        examples=[
            OpenApiExample(
                name="Exemplo de template de Petição",
                value={
                    "name": "Petição Inicial Cível",
                    "description": "Template padrão para petição inicial cível",
                    "is_active": True,
                    "fields": [
                        {
                            "id": "descricao_necessidade",
                            "type": "textarea",
                            "label": "Descrição da Necessidade",
                            "required": True,
                            "help_text": "Descreva detalhadamente a necessidade que motivou a contratação",
                            "ai_assist": True,
                            "ai_prompt_type": "corretor",
                            "min_length": 100,
                            "max_length": 5000
                        },
                        {
                            "id": "justificativa",
                            "type": "textarea",
                            "label": "Justificativa",
                            "required": True,
                            "help_text": "Justifique a contratação",
                            "ai_assist": True,
                            "ai_prompt_type": "sugestao"
                        },
                        {
                            "id": "valor_estimado",
                            "type": "number",
                            "label": "Valor Estimado (R$)",
                            "required": True,
                            "placeholder": "0.00"
                        }
                    ]
                },
                request_only=True
            )
        ]
    ),
    update=extend_schema(
        summary="Atualizar template",
        description="Atualiza todos os campos de um template (apenas admin/manager)",
        tags=["Forms - Templates"],
        request=FormTemplateUpdateSerializer,
        responses={200: FormTemplateDetailSerializer}
    ),
    partial_update=extend_schema(
        summary="Atualizar parcialmente template",
        description="Atualiza campos específicos de um template (apenas admin/manager)",
        tags=["Forms - Templates"],
        request=FormTemplateUpdateSerializer,
        responses={200: FormTemplateDetailSerializer}
    ),
    destroy=extend_schema(
        summary="Deletar template",
        description="Remove um template do sistema (apenas admin/manager)",
        tags=["Forms - Templates"],
        responses={204: None}
    ),
)
class FormTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de templates de formulário

    - GET /forms/ - Lista templates (todos podem ver)
    - POST /forms/ - Cria template (apenas admin/manager)
    - GET /forms/{id}/ - Detalhe do template
    - PUT/PATCH /forms/{id}/ - Atualiza template (apenas admin/manager)
    - DELETE /forms/{id}/ - Deleta template (apenas admin/manager)
    """
    queryset = FormTemplate.objects.all()
    permission_classes = [CanManageFormTemplates]

    def get_serializer_class(self):
        """Retorna serializer apropriado por ação"""
        if self.action == 'list':
            return FormTemplateListSerializer
        elif self.action == 'create':
            return FormTemplateCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return FormTemplateUpdateSerializer
        return FormTemplateDetailSerializer

    def get_queryset(self):
        """Filtra templates ativos por padrão, admin vê todos"""
        from django.db.models import Q
        # Otimização: select_related para evitar N+1 queries
        queryset = FormTemplate.objects.select_related(
            'created_by',
            'blueprint'
        ).all()

        # Filtrar por status (admin pode ver inativos)
        from apps.accounts.permissions import is_admin_or_manager
        if not is_admin_or_manager(self.request.user):
            # Non-admin: see active templates OR own templates (even inactive)
            queryset = queryset.filter(
                Q(is_active=True) | Q(created_by=self.request.user)
            )
        else:
            # Admin pode filtrar por is_active
            is_active = self.request.query_params.get('is_active', None)
            if is_active is not None:
                queryset = queryset.filter(
                    is_active=is_active.lower() == 'true')

        return queryset.order_by('-created_at')

    def destroy(self, request, *args, **kwargs):
        """
        Deleta template com tratamento de ProtectedError
        Retorna mensagem amigável se o template estiver sendo usado
        """
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            # Extrair nomes dos objetos protegidos
            protected_objects = e.protected_objects
            Documents_names = [str(obj) for obj in protected_objects]

            return Response(
                {
                    'error': 'Este formulário não pode ser deletado porque está sendo usado.',
                    'detail': f'O formulário "{instance.name}" está sendo utilizado por: {", ".join(Documents_names)}.',
                    'suggestion': 'Para deletar este formulário, primeiro delete ou altere os Documents que o utilizam.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        summary="Duplicar template",
        description="Cria uma cópia do template com versão incrementada (apenas admin/manager)",
        tags=["Forms - Templates"],
        request=FormTemplateDuplicateSerializer,
        responses={201: FormTemplateDetailSerializer},
        examples=[
            OpenApiExample(
                name="Duplicar com novo nome",
                value={"name": "Petição Inicial Cível v2"},
                request_only=True
            )
        ]
    )
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplica um template existente"""
        template = self.get_object()
        serializer = FormTemplateDuplicateSerializer(data=request.data)

        if serializer.is_valid():
            new_template = template.duplicate(request.user)

            # Atualiza nome se fornecido
            if 'name' in serializer.validated_data:
                new_template.name = serializer.validated_data['name']
                new_template.save()

            response_serializer = FormTemplateDetailSerializer(new_template)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Ativar template",
        description="Ativa um template desativado (apenas admin/manager)",
        tags=["Forms - Templates"],
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
        tags=["Forms - Templates"],
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
        summary="Buscar campo específico",
        description="Retorna dados de um campo específico do template",
        tags=["Forms - Field Builder"],
        responses={
            200: OpenApiResponse(description="Dados do campo"),
            404: OpenApiResponse(description="Campo não encontrado")
        }
    )
    @action(detail=True, methods=['get'], url_path='fields/(?P<field_id>[^/.]+)')
    def get_field(self, request, pk=None, field_id=None):
        """Retorna campo específico do template"""
        template = self.get_object()
        field = template.get_field_by_id(field_id)

        if field:
            return Response(field, status=status.HTTP_200_OK)
        return Response(
            {'detail': f'Campo "{field_id}" não encontrado.'},
            status=status.HTTP_404_NOT_FOUND
        )

    @extend_schema(
        summary="Listar tipos de campo disponíveis",
        description="Retorna lista de todos os tipos de campo que podem ser usados no form builder",
        tags=["Forms - Field Builder"],
        responses={200: FieldTypeInfoSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='field-types')
    def field_types(self, request):
        """Retorna tipos de campo disponíveis para o form builder"""
        field_types = [
            {
                "type": "text",
                "label": "Texto Curto",
                "description": "Campo de texto simples (uma linha)",
                "icon": "📝",
                "default_config": {
                    "type": "text",
                    "required": False,
                    "placeholder": "",
                    "max_length": 255
                }
            },
            {
                "type": "textarea",
                "label": "Texto Longo",
                "description": "Campo de texto com múltiplas linhas",
                "icon": "📄",
                "default_config": {
                    "type": "textarea",
                    "required": False,
                    "placeholder": "",
                    "min_length": None,
                    "max_length": 5000,
                    "ai_assist": True
                }
            },
            {
                "type": "number",
                "label": "Número",
                "description": "Campo numérico",
                "icon": "🔢",
                "default_config": {
                    "type": "number",
                    "required": False,
                    "placeholder": "0"
                }
            },
            {
                "type": "email",
                "label": "E-mail",
                "description": "Campo de e-mail com validação",
                "icon": "📧",
                "default_config": {
                    "type": "email",
                    "required": False,
                    "placeholder": "email@exemplo.com"
                }
            },
            {
                "type": "date",
                "label": "Data",
                "description": "Seletor de data",
                "icon": "📅",
                "default_config": {
                    "type": "date",
                    "required": False
                }
            },
            {
                "type": "select",
                "label": "Seleção Única",
                "description": "Lista suspensa (dropdown)",
                "icon": "📋",
                "default_config": {
                    "type": "select",
                    "required": False,
                    "options": [
                        {"value": "opcao1", "label": "Opção 1"},
                        {"value": "opcao2", "label": "Opção 2"}
                    ]
                }
            },
            {
                "type": "checkbox",
                "label": "Múltipla Escolha",
                "description": "Checkboxes (múltipla seleção)",
                "icon": "☑️",
                "default_config": {
                    "type": "checkbox",
                    "required": False,
                    "options": [
                        {"value": "opcao1", "label": "Opção 1"},
                        {"value": "opcao2", "label": "Opção 2"}
                    ]
                }
            },
            {
                "type": "radio",
                "label": "Escolha Única",
                "description": "Radio buttons (seleção única)",
                "icon": "🔘",
                "default_config": {
                    "type": "radio",
                    "required": False,
                    "options": [
                        {"value": "opcao1", "label": "Opção 1"},
                        {"value": "opcao2", "label": "Opção 2"}
                    ]
                }
            },
            {
                "type": "file",
                "label": "Upload de Arquivo",
                "description": "Campo para upload de arquivos",
                "icon": "📎",
                "default_config": {
                    "type": "file",
                    "required": False,
                    "help_text": "Formatos aceitos: PDF, DOC, DOCX"
                }
            }
        ]
        serializer = FieldTypeInfoSerializer(field_types, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Adicionar campo ao template",
        description="Adiciona um novo campo ao template (apenas admin/manager)",
        tags=["Forms - Field Builder"],
        request=AddFieldSerializer,
        responses={200: FormTemplateDetailSerializer}
    )
    @action(detail=True, methods=['post'], url_path='fields/add')
    def add_field(self, request, pk=None):
        """Adiciona campo ao template"""
        template = self.get_object()
        serializer = AddFieldSerializer(data=request.data)

        if serializer.is_valid():
            field = serializer.validated_data['field']
            position = serializer.validated_data.get('position')

            # Verificar se ID já existe
            if template.get_field_by_id(field['id']):
                return Response(
                    {'detail': f'Já existe um campo com o ID "{field["id"]}".'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Adicionar campo
            if position is not None and 0 <= position <= len(template.fields):
                template.fields.insert(position, field)
            else:
                template.fields.append(field)

            template.save()

            response_serializer = FormTemplateDetailSerializer(template)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Atualizar campo do template",
        description="Atualiza um campo existente do template (apenas admin/manager)",
        tags=["Forms - Field Builder"],
        request=UpdateFieldSerializer,
        responses={200: FormTemplateDetailSerializer}
    )
    @action(detail=True, methods=['put'], url_path='fields/(?P<field_id>[^/.]+)/update')
    def update_field(self, request, pk=None, field_id=None):
        """Atualiza campo específico"""
        template = self.get_object()
        serializer = UpdateFieldSerializer(data=request.data)

        if serializer.is_valid():
            new_field = serializer.validated_data['field']

            # Encontrar e atualizar o campo
            for idx, field in enumerate(template.fields):
                if field.get('id') == field_id:
                    # Preservar o ID original se não fornecido no novo campo
                    if 'id' not in new_field:
                        new_field['id'] = field_id
                    template.fields[idx] = new_field
                    template.save()

                    response_serializer = FormTemplateDetailSerializer(
                        template)
                    return Response(response_serializer.data, status=status.HTTP_200_OK)

            return Response(
                {'detail': f'Campo "{field_id}" não encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Remover campo do template",
        description="Remove um campo do template (apenas admin/manager)",
        tags=["Forms - Field Builder"],
        responses={200: FormTemplateDetailSerializer}
    )
    @action(detail=True, methods=['delete'], url_path='fields/(?P<field_id>[^/.]+)/remove')
    def remove_field(self, request, pk=None, field_id=None):
        """Remove campo do template"""
        template = self.get_object()

        # Encontrar e remover o campo
        for idx, field in enumerate(template.fields):
            if field.get('id') == field_id:
                template.fields.pop(idx)
                template.save()

                response_serializer = FormTemplateDetailSerializer(template)
                return Response(response_serializer.data, status=status.HTTP_200_OK)

        return Response(
            {'detail': f'Campo "{field_id}" não encontrado.'},
            status=status.HTTP_404_NOT_FOUND
        )

    @extend_schema(
        summary="Reordenar campos do template",
        description="Reordena os campos do template (apenas admin/manager)",
        tags=["Forms - Field Builder"],
        request=ReorderFieldsSerializer,
        responses={200: FormTemplateDetailSerializer}
    )
    @action(detail=True, methods=['post'], url_path='fields/reorder')
    def reorder_fields(self, request, pk=None):
        """Reordena campos do template"""
        template = self.get_object()
        serializer = ReorderFieldsSerializer(data=request.data)

        if serializer.is_valid():
            field_ids = serializer.validated_data['field_ids']

            # Verificar se todos os IDs existem
            current_ids = [f['id'] for f in template.fields]
            if set(field_ids) != set(current_ids):
                return Response(
                    {'detail': 'A lista de IDs não corresponde aos campos do template.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Reordenar campos
            new_fields = []
            for field_id in field_ids:
                field = template.get_field_by_id(field_id)
                if field:
                    new_fields.append(field)

            template.fields = new_fields
            template.save()

            response_serializer = FormTemplateDetailSerializer(template)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Importar formulário de JSON",
        description="Importa um formulário completo a partir de um arquivo JSON (apenas admin/manager)",
        tags=["Forms - Templates"],
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Arquivo JSON com a estrutura do formulário'
                    },
                    'name': {
                        'type': 'string',
                        'description': 'Nome do formulário (opcional, usa o do JSON se não fornecido)'
                    },
                    'description': {
                        'type': 'string',
                        'description': 'Descrição do formulário (opcional)'
                    },
                },
                'required': ['file']
            }
        },
        responses={
            201: FormTemplateDetailSerializer,
            400: OpenApiResponse(description="Erro no formato do JSON ou dados inválidos")
        }
    )
    @action(detail=False, methods=['post'], url_path='import-json')
    def import_from_json(self, request):
        """Importa formulário de arquivo JSON"""
        import json
        from datetime import datetime

        # Verificar se o arquivo foi enviado
        if 'file' not in request.FILES:
            return Response(
                {'detail': 'Nenhum arquivo foi enviado. Envie um arquivo JSON.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        json_file = request.FILES['file']

        # Verificar extensão
        if not json_file.name.endswith('.json'):
            return Response(
                {'detail': 'O arquivo deve ser um JSON (.json).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Ler e parsear o JSON
            content = json_file.read().decode('utf-8')
            data = json.loads(content)

            # Extrair campos do JSON
            # Suporta dois formatos:
            # 1. Array flat direto: [{id, type, label, ...}, ...]
            # 2. Com sections: {sections: [{fields: [...]}]}
            fields = []

            if isinstance(data, list):
                # Formato 1: array flat
                fields = data
            elif isinstance(data, dict):
                if 'fields' in data:
                    # Tem um objeto com campo 'fields'
                    fields = data['fields']
                elif 'sections' in data:
                    # Formato 2: com sections - converter para flat
                    for section in data['sections']:
                        if 'fields' in section:
                            for field in section['fields']:
                                # Converter 'name' para 'id' se necessário
                                if 'name' in field and 'id' not in field:
                                    field['id'] = field.pop('name')
                                fields.append(field)
                else:
                    return Response(
                        {'detail': 'JSON deve conter "fields" ou "sections".'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            if not fields:
                return Response(
                    {'detail': 'Nenhum campo encontrado no JSON.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validar estrutura dos campos
            for idx, field in enumerate(fields):
                if 'id' not in field:
                    return Response(
                        {'detail': f'Campo na posição {idx} não possui "id".'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if 'type' not in field:
                    return Response(
                        {'detail': f'Campo "{field["id"]}" não possui "type".'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if 'label' not in field:
                    return Response(
                        {'detail': f'Campo "{field["id"]}" não possui "label".'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Obter metadados do request ou do JSON
            name = request.data.get('name') or data.get(
                'name', 'Formulário Importado')
            description = request.data.get('description') or data.get(
                'description', 'Formulário importado via JSON')
            # Verificar se já existe um formulário com esse nome
            if FormTemplate.objects.filter(name=name).exists():
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
                name = f"{name} (Importado em {timestamp})"

            # Criar o formulário
            template = FormTemplate.objects.create(
                name=name,
                description=description,
                fields=fields,
                is_active=True,
                created_by=request.user
            )

            response_serializer = FormTemplateDetailSerializer(template)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except json.JSONDecodeError as e:
            return Response(
                {'detail': f'Erro ao ler JSON: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'detail': f'Erro ao importar formulário: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


# ===== FORM ASSISTANT VIEWSET =====

from .models import FormAssistant
from .serializers import (
    FormAssistantListSerializer,
    FormAssistantDetailSerializer,
    FormAssistantCreateSerializer,
    FormAssistantUpdateSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="Listar assistentes de formulário",
        description="Retorna lista de todos os assistentes de formulário",
        tags=["Form Assistants"],
        responses={200: FormAssistantListSerializer(many=True)}
    ),
    retrieve=extend_schema(
        summary="Buscar assistente por ID",
        description="Retorna detalhes completos de um assistente",
        tags=["Form Assistants"],
        responses={200: FormAssistantDetailSerializer}
    ),
    create=extend_schema(
        summary="Criar assistente",
        description="Cria novo assistente de formulário",
        tags=["Form Assistants"],
        request=FormAssistantCreateSerializer,
        responses={201: FormAssistantDetailSerializer}
    ),
    update=extend_schema(
        summary="Atualizar assistente",
        description="Atualiza assistente",
        tags=["Form Assistants"],
        request=FormAssistantUpdateSerializer,
        responses={200: FormAssistantDetailSerializer}
    ),
    partial_update=extend_schema(
        summary="Atualizar parcialmente assistente",
        description="Atualiza campos específicos",
        tags=["Form Assistants"],
        request=FormAssistantUpdateSerializer,
        responses={200: FormAssistantDetailSerializer}
    ),
    destroy=extend_schema(
        summary="Deletar assistente",
        description="Remove assistente",
        tags=["Form Assistants"],
        responses={204: None}
    ),
)
class FormAssistantViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciamento de assistentes de formulário"""
    queryset = FormAssistant.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return FormAssistantListSerializer
        elif self.action == 'create':
            return FormAssistantCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return FormAssistantUpdateSerializer
        return FormAssistantDetailSerializer

    def get_queryset(self):
        from apps.accounts.permissions import is_admin_or_manager

        queryset = FormAssistant.objects.select_related('created_by')

        # Non-admin users only see their own assistants
        if not is_admin_or_manager(self.request.user):
            queryset = queryset.filter(created_by=self.request.user)

        # Filtro por assistant_type
        assistant_type = self.request.query_params.get('assistant_type')
        if assistant_type:
            queryset = queryset.filter(assistant_type=assistant_type)

        # Filtro por provider
        llm_provider = self.request.query_params.get('llm_provider')
        if llm_provider:
            queryset = queryset.filter(llm_provider=llm_provider)

        # Apenas ativos (padrão: true)
        if self.request.query_params.get('active_only', 'true').lower() == 'true':
            queryset = queryset.filter(is_active=True)

        return queryset.order_by('display_order', 'assistant_type')

    @extend_schema(
        summary="Estatísticas dos assistentes",
        description="Retorna estatísticas gerais",
        tags=["Form Assistants"],
        responses={200: OpenApiResponse(description="Estatísticas")}
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estatísticas dos assistentes"""
        from django.db.models import Count, Q

        queryset = FormAssistant.objects.all()

        aggregate_dict = {
            'total': Count('id'),
            'active': Count('id', filter=Q(is_active=True)),
        }

        # Por provider
        for provider_code, _ in FormAssistant.LLM_PROVIDER_CHOICES:
            aggregate_dict[f'prov_{provider_code}_count'] = Count('id', filter=Q(llm_provider=provider_code))

        result = queryset.aggregate(**aggregate_dict)

        stats = {
            'total': result['total'],
            'active': result['active'],
            'by_provider': {},
        }

        for provider_code, provider_name in FormAssistant.LLM_PROVIDER_CHOICES:
            stats['by_provider'][provider_code] = {
                'name': provider_name,
                'count': result[f'prov_{provider_code}_count']
            }

        return Response(stats)

    @extend_schema(
        summary="Executar assistente",
        description="Executa o assistente de formulário com chamada ao LLM",
        tags=["Form Assistants"],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'variables': {'type': 'object', 'description': 'Variáveis para substituir no template'},
                    'user_input': {'type': 'string', 'description': 'Input adicional do usuário'},
                },
            }
        },
        responses={200: OpenApiResponse(description="Resposta do assistente")}
    )
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Executa assistente de formulário com chamada real ao LLM"""
        from apps.agents.services import LLMService
        import time

        assistant = self.get_object()
        variables = request.data.get('variables', {})
        user_input = request.data.get('user_input', '')

        # Substituir variáveis no user_prompt_template
        user_prompt = assistant.user_prompt_template
        for key, value in variables.items():
            placeholder = f'{{{{{key}}}}}'
            user_prompt = user_prompt.replace(placeholder, str(value))

        # Adicionar user_input se fornecido
        if user_input:
            user_prompt = f"{user_prompt}\n\n{user_input}"

        try:
            # Chamar LLM
            start_time = time.time()

            result = LLMService.call(
                provider=assistant.llm_provider,
                model=assistant.model_name,
                system_prompt=assistant.system_prompt,
                user_prompt=user_prompt,
                temperature=assistant.temperature,
                max_tokens=assistant.max_tokens
            )

            execution_time = int((time.time() - start_time) * 1000)

            return Response({
                'assistant_name': assistant.name,
                'assistant_type': assistant.assistant_type,
                'response': result['response'],
                'llm_provider': result['provider'],
                'model': result['model'],
                'tokens_used': result['tokens_used'],
                'execution_time_ms': execution_time
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': str(e),
                'assistant_name': assistant.name
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
