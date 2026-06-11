"""
Serializers para templates de documentos
"""
from rest_framework import serializers
from .models import DocumentTemplate


class DocumentTemplateListSerializer(serializers.ModelSerializer):
    """Serializer para listar templates (resumido)"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    blueprint_name = serializers.CharField(source='blueprint.name', read_only=True, allow_null=True)
    placeholder_count = serializers.IntegerField(read_only=True)
    has_file = serializers.BooleanField(read_only=True)
    form_template_id = serializers.UUIDField(source='form_template.id', read_only=True, allow_null=True)
    form_template_name = serializers.CharField(source='form_template.name', read_only=True, allow_null=True)

    class Meta:
        model = DocumentTemplate
        fields = [
            'id', 'name', 'description', 'blueprint', 'blueprint_name', 'template_type',
            'version', 'is_active', 'is_default', 'placeholder_count',
            'has_file', 'form_template_id', 'form_template_name',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DocumentTemplateDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalhes do template (completo)"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    created_by_id = serializers.IntegerField(source='created_by.id', read_only=True)
    blueprint_name = serializers.CharField(source='blueprint.name', read_only=True, allow_null=True)
    placeholder_count = serializers.IntegerField(read_only=True)
    has_file = serializers.BooleanField(read_only=True)
    form_template_id = serializers.UUIDField(source='form_template.id', read_only=True, allow_null=True)
    form_template_name = serializers.CharField(source='form_template.name', read_only=True, allow_null=True)
    extracted_placeholders = serializers.ListField(
        source='extract_placeholders',
        read_only=True,
        help_text='Placeholders extraídos automaticamente do template'
    )
    rendered_content = serializers.SerializerMethodField(
        help_text='Conteúdo renderizado do template (extraído do arquivo .docx se necessário)'
    )

    def get_rendered_content(self, obj):
        """Retorna o conteúdo do template, extraindo de arquivo .docx se necessário"""
        return obj.get_template_content()

    class Meta:
        model = DocumentTemplate
        fields = [
            'id', 'name', 'description', 'blueprint', 'blueprint_name', 'template_type',
            'content', 'file', 'custom_css', 'available_variables',
            'form_template', 'form_template_id', 'form_template_name',
            'version', 'is_active', 'is_default', 'placeholder_count', 'has_file',
            'extracted_placeholders', 'rendered_content', 'created_by_id', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by_id', 'created_by_name']


class DocumentTemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar template"""

    class Meta:
        model = DocumentTemplate
        fields = [
            'name', 'description', 'blueprint', 'template_type',
            'content', 'file', 'custom_css', 'available_variables',
            'form_template', 'is_active', 'is_default'
        ]

    def validate(self, attrs):
        """Validação: conteúdo OU arquivo, não ambos"""
        content = attrs.get('content')
        file = attrs.get('file')

        if not content and not file:
            raise serializers.ValidationError(
                'É necessário fornecer o conteúdo do template OU fazer upload de um arquivo.'
            )

        if content and file:
            raise serializers.ValidationError(
                'Forneça APENAS o conteúdo OU o arquivo, não ambos.'
            )

        return attrs

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class DocumentTemplateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualizar template"""

    class Meta:
        model = DocumentTemplate
        fields = [
            'name', 'description', 'blueprint', 'template_type',
            'content', 'file', 'custom_css', 'available_variables',
            'form_template', 'is_active', 'is_default'
        ]

    def validate(self, attrs):
        """Validação: conteúdo OU arquivo, não ambos"""
        instance = self.instance
        content = attrs.get('content', instance.content if instance else None)
        file = attrs.get('file', instance.file if instance else None)

        # Se está limpando os dois campos
        if content is None and file is None:
            raise serializers.ValidationError(
                'É necessário manter pelo menos o conteúdo OU o arquivo.'
            )

        return attrs


class DocumentTemplateDuplicateSerializer(serializers.Serializer):
    """Serializer para duplicar template"""
    name = serializers.CharField(
        max_length=255,
        required=False,
        help_text='Novo nome (opcional, mantém o nome original se não informado)'
    )


class TemplatePreviewSerializer(serializers.Serializer):
    """Serializer para preview do template com dados"""
    data = serializers.DictField(
        help_text='Dados para preencher os placeholders do template'
    )
