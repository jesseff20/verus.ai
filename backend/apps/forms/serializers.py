"""
Serializers para templates de formulários
"""
from rest_framework import serializers
from .models import FormTemplate


class FormFieldSerializer(serializers.Serializer):
    """Serializer para validar campos individuais do formulário"""
    id = serializers.CharField(max_length=100, help_text="ID único do campo")
    type = serializers.ChoiceField(
        choices=['text', 'textarea', 'number', 'email', 'date', 'select', 'checkbox', 'radio', 'file', 'array'],
        help_text="Tipo do campo"
    )
    label = serializers.CharField(max_length=255, help_text="Label exibido ao usuário")
    required = serializers.BooleanField(default=False, help_text="Campo obrigatório")
    help_text = serializers.CharField(max_length=500, required=False, allow_blank=True, help_text="Texto de ajuda")
    placeholder = serializers.CharField(max_length=255, required=False, allow_blank=True, help_text="Placeholder do input")
    default_value = serializers.CharField(max_length=500, required=False, allow_blank=True, help_text="Valor padrão")

    # Para campos tipo select/radio (aceita array de strings ou dicionários)
    options = serializers.ListField(
        child=serializers.JSONField(),
        required=False,
        help_text="Opções para campos select/radio. Ex: ['Op1', 'Op2'] ou [{'value': 'opt1', 'label': 'Opção 1'}]"
    )

    # Para campos tipo array
    min_items = serializers.IntegerField(required=False, allow_null=True, help_text="Número mínimo de itens no array")
    max_items = serializers.IntegerField(required=False, allow_null=True, help_text="Número máximo de itens no array")
    item_schema = serializers.JSONField(required=False, allow_null=True, help_text="Schema dos itens do array")

    # Assistência IA
    ai_assist = serializers.BooleanField(default=False, help_text="Habilita assistente de IA para este campo")
    ai_prompt_type = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="Tipo de assistência de IA (DEPRECATED - use ai_prompt_types)"
    )
    ai_prompt_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_null=True,
        allow_empty=True,
        help_text="Lista de tipos de assistência de IA para este campo"
    )

    # Validações
    min_length = serializers.IntegerField(required=False, allow_null=True, help_text="Tamanho mínimo")
    max_length = serializers.IntegerField(required=False, allow_null=True, help_text="Tamanho máximo")
    pattern = serializers.CharField(required=False, allow_blank=True, help_text="Regex para validação")


class FormTemplateListSerializer(serializers.ModelSerializer):
    """Serializer para listar templates (resumido)"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    field_count = serializers.IntegerField(read_only=True)
    blueprint_name = serializers.CharField(
        source='blueprint.name', read_only=True, allow_null=True
    )
    blueprint_agents = serializers.SerializerMethodField()
    fields = serializers.ListField(
        child=serializers.DictField(),
        help_text="Lista de campos do formulário"
    )
    sections = serializers.ListField(
        child=serializers.DictField(),
        help_text="Lista de seções do formulário (estruturado)",
        required=False
    )

    class Meta:
        model = FormTemplate
        fields = [
            'id', 'name', 'description', 'blueprint',
            'blueprint_name', 'blueprint_agents', 'fields', 'sections', 'version',
            'is_active', 'field_count', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_blueprint_agents(self, obj):
        """Retorna agentes disponíveis do blueprint selecionado"""
        if not obj.blueprint:
            return []

        agents = []
        for section in obj.blueprint.sections.filter(is_active=True):
            if section.generator_agent:
                agents.append({
                    'id': str(section.generator_agent.id),
                    'name': section.generator_agent.name,
                    'type': 'generator',
                    'section_name': section.section_name,
                    'section_key': section.section_key,
                    'section_number': section.section_number,
                })
            if section.validator_agent:
                agents.append({
                    'id': str(section.validator_agent.id),
                    'name': section.validator_agent.name,
                    'type': 'validator',
                    'section_name': section.section_name,
                    'section_key': section.section_key,
                    'section_number': section.section_number,
                })
        return agents


class FormTemplateDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalhes do template (completo)"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    created_by_id = serializers.IntegerField(source='created_by.id', read_only=True)
    field_count = serializers.IntegerField(read_only=True)
    blueprint_name = serializers.CharField(
        source='blueprint.name', read_only=True, allow_null=True
    )
    blueprint_agents = serializers.SerializerMethodField()
    fields = serializers.ListField(
        child=serializers.DictField(),
        help_text="Lista de campos do formulário"
    )
    sections = serializers.ListField(
        child=serializers.DictField(),
        help_text="Lista de seções do formulário (estruturado)",
        required=False
    )

    class Meta:
        model = FormTemplate
        fields = [
            'id', 'name', 'description', 'blueprint',
            'blueprint_name', 'blueprint_agents', 'fields', 'sections', 'version',
            'is_active', 'field_count', 'created_by_id', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by_id', 'created_by_name']

    def get_blueprint_agents(self, obj):
        """Retorna agentes disponíveis do blueprint selecionado"""
        if not obj.blueprint:
            return []

        agents = []
        for section in obj.blueprint.sections.filter(is_active=True):
            if section.generator_agent:
                agents.append({
                    'id': str(section.generator_agent.id),
                    'name': section.generator_agent.name,
                    'type': 'generator',
                    'section_name': section.section_name,
                    'section_key': section.section_key,
                    'section_number': section.section_number,
                })
            if section.validator_agent:
                agents.append({
                    'id': str(section.validator_agent.id),
                    'name': section.validator_agent.name,
                    'type': 'validator',
                    'section_name': section.section_name,
                    'section_key': section.section_key,
                    'section_number': section.section_number,
                })
        return agents


class FormTemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar template"""
    fields = serializers.ListField(
        child=serializers.DictField(),
        help_text="Lista de campos do formulário. Cada campo deve ter: id, type, label",
        required=False
    )
    sections = serializers.ListField(
        child=serializers.DictField(),
        help_text="Lista de seções do formulário (estruturado)",
        required=False
    )
    blueprint = serializers.PrimaryKeyRelatedField(
        queryset=__import__('apps.intelligent_assistant.models', fromlist=['DocumentBlueprint']).DocumentBlueprint.objects.filter(is_active=True),
        required=False,
        allow_null=True,
        help_text="Blueprint de documento para este formulário"
    )

    class Meta:
        model = FormTemplate
        fields = ['name', 'description', 'blueprint', 'fields', 'sections', 'is_active']

    def validate_fields(self, value):
        """Valida estrutura dos campos usando FormFieldSerializer"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Fields deve ser uma lista")

        for idx, field_data in enumerate(value):
            serializer = FormFieldSerializer(data=field_data)
            if not serializer.is_valid():
                raise serializers.ValidationError(
                    f"Campo {idx}: {serializer.errors}"
                )

        return value

    def create(self, validated_data):
        # created_by será setado pela view
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class FormTemplateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualizar template"""
    fields = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Lista de campos do formulário"
    )
    sections = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Lista de seções do formulário (estruturado)"
    )
    blueprint = serializers.PrimaryKeyRelatedField(
        queryset=__import__('apps.intelligent_assistant.models', fromlist=['DocumentBlueprint']).DocumentBlueprint.objects.filter(is_active=True),
        required=False,
        allow_null=True,
        help_text="Blueprint de documento para este formulário"
    )

    class Meta:
        model = FormTemplate
        fields = ['name', 'description', 'blueprint', 'fields', 'sections', 'is_active']

    def validate_fields(self, value):
        """Valida estrutura dos campos"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Fields deve ser uma lista")

        for idx, field_data in enumerate(value):
            serializer = FormFieldSerializer(data=field_data)
            if not serializer.is_valid():
                raise serializers.ValidationError(
                    f"Campo {idx} ({field_data.get('id', 'unknown')}): {serializer.errors}"
                )

        return value


class FormTemplateDuplicateSerializer(serializers.Serializer):
    """Serializer para duplicar template"""
    name = serializers.CharField(
        max_length=255,
        required=False,
        help_text="Novo nome (opcional, mantém o nome original se não informado)"
    )


class FieldTypeInfoSerializer(serializers.Serializer):
    """Serializer com informações sobre tipos de campo disponíveis"""
    type = serializers.CharField()
    label = serializers.CharField()
    description = serializers.CharField()
    icon = serializers.CharField()
    default_config = serializers.DictField()


class AddFieldSerializer(serializers.Serializer):
    """Serializer para adicionar campo ao template"""
    field = serializers.DictField(help_text="Configuração completa do campo")
    position = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Posição onde inserir (null = final)"
    )

    def validate_field(self, value):
        """Valida o campo usando FormFieldSerializer"""
        serializer = FormFieldSerializer(data=value)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)
        return value


class UpdateFieldSerializer(serializers.Serializer):
    """Serializer para atualizar campo específico"""
    field = serializers.DictField(help_text="Nova configuração do campo")

    def validate_field(self, value):
        """Valida o campo usando FormFieldSerializer"""
        serializer = FormFieldSerializer(data=value)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)
        return value


class ReorderFieldsSerializer(serializers.Serializer):
    """Serializer para reordenar campos"""
    field_ids = serializers.ListField(
        child=serializers.CharField(),
        help_text="Lista ordenada de IDs dos campos"
    )


# ===== FORM ASSISTANT SERIALIZERS =====

from .models import FormAssistant


class FormAssistantListSerializer(serializers.ModelSerializer):
    """Serializer para listar assistentes (resumido)"""
    provider_display = serializers.CharField(source='get_llm_provider_display', read_only=True)
    variable_count = serializers.IntegerField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True, allow_null=True)

    class Meta:
        model = FormAssistant
        fields = [
            'id', 'name', 'description', 'assistant_type', 'icon', 'color',
            'display_order', 'system_prompt', 'user_prompt_template',
            'llm_provider', 'provider_display', 'model_name', 'temperature', 'max_tokens',
            'variable_count', 'use_rag', 'rag_query_template', 'is_active', 'is_default',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FormAssistantDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalhes do assistente (completo)"""
    provider_display = serializers.CharField(source='get_llm_provider_display', read_only=True)
    variable_count = serializers.IntegerField(read_only=True)
    extracted_variables = serializers.ListField(source='extract_variables', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True, allow_null=True)
    created_by_id = serializers.IntegerField(source='created_by.id', read_only=True, allow_null=True)

    class Meta:
        model = FormAssistant
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class FormAssistantCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar assistente"""
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    rag_query_template = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    icon = serializers.CharField(required=False, allow_blank=True, default='wand-2')
    color = serializers.CharField(required=False, allow_blank=True, default='#3b82f6')

    class Meta:
        model = FormAssistant
        fields = [
            'name', 'description', 'assistant_type',
            'system_prompt', 'user_prompt_template', 'llm_provider',
            'model_name', 'temperature', 'max_tokens', 'use_rag',
            'rag_query_template', 'icon', 'color', 'display_order',
            'is_active', 'is_default'
        ]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class FormAssistantUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualizar assistente"""

    class Meta:
        model = FormAssistant
        fields = [
            'name', 'description', 'assistant_type', 'system_prompt',
            'user_prompt_template', 'llm_provider', 'model_name', 'temperature',
            'max_tokens', 'use_rag', 'rag_query_template', 'icon', 'color',
            'display_order', 'is_active', 'is_default'
        ]
