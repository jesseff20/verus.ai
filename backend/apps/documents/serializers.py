"""
Serializers para Documents
"""
from rest_framework import serializers
from .models import Document, DocumentVersion, DocumentGenerator


class DocumentListSerializer(serializers.ModelSerializer):
    """Serializer para listar Documents"""
    user_name = serializers.CharField(
        source='user.get_full_name', read_only=True)
    form_template_name = serializers.CharField(
        source='form_template.name', read_only=True)
    source_display = serializers.CharField(
        source='get_source_display', read_only=True)

    class Meta:
        model = Document
        fields = [
            'id', 'title', 'numero_processo', 'description', 'user_name', 'form_template_name',
            'source', 'source_display',
            'status', 'progress', 'version', 'created_at', 'updated_at'
        ]


class DocumentDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalhes do ETP"""
    user_name = serializers.CharField(
        source='user.get_full_name', read_only=True)
    form_template_name = serializers.CharField(
        source='form_template.name', read_only=True)
    document_template_name = serializers.CharField(
        source='document_template.name', read_only=True, allow_null=True)
    source_display = serializers.CharField(
        source='get_source_display', read_only=True)

    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ['id', 'user',
                            'created_at', 'updated_at', 'completed_at']


class DocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar ETP"""
    numero_processo = serializers.CharField(
        required=False, allow_blank=True, max_length=100)
    progress = serializers.IntegerField(required=False, default=0)
    document_template = serializers.PrimaryKeyRelatedField(
        queryset=__import__('apps.templates.models', fromlist=['DocumentTemplate']).DocumentTemplate.objects.all(),
        required=False,
        allow_null=True,
        help_text='Template de documento'
    )

    class Meta:
        model = Document
        fields = ['title', 'numero_processo', 'description',
                  'form_template', 'document_template', 'data', 'progress']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class DocumentUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualizar ETP"""
    numero_processo = serializers.CharField(
        required=False, allow_blank=True, max_length=100)
    progress = serializers.IntegerField(required=False)
    document_template = serializers.PrimaryKeyRelatedField(
        queryset=__import__('apps.templates.models', fromlist=['DocumentTemplate']).DocumentTemplate.objects.all(),
        required=False,
        allow_null=True,
        help_text='Template de documento'
    )

    class Meta:
        model = Document
        fields = ['title', 'numero_processo', 'description', 'data',
                  'progress', 'generated_content', 'generated_html', 'status', 'document_template']


class DocumentVersionSerializer(serializers.ModelSerializer):
    """Serializer para Versão de Documento"""
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', read_only=True)
    version_type_display = serializers.CharField(
        source='get_version_type_display', read_only=True)

    class Meta:
        model = DocumentVersion
        fields = [
            'id', 'document', 'version_number', 'version_type', 'version_type_display',
            'sections_data', 'section_hashes', 'change_summary', 'created_by', 'created_by_name',
            'parent_version', 'tags', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'section_hashes']


class DocumentGeneratorSerializer(serializers.ModelSerializer):
    """Serializer para DocumentGenerator"""
    created_by_name = serializers.SerializerMethodField()
    document_template_name = serializers.SerializerMethodField()
    provider_display = serializers.CharField(read_only=True)
    variable_count = serializers.IntegerField(read_only=True)
    specialty_display = serializers.CharField(source='get_specialty_display', read_only=True)

    class Meta:
        model = DocumentGenerator
        fields = [
            'id', 'name', 'description', 'document_type', 'specialty', 'specialty_display',
            'document_template', 'document_template_name',
            'icon', 'color', 'display_order',
            'llm_provider', 'provider_display', 'model_name', 'temperature', 'max_tokens',
            'variable_count', 'use_rag', 'rag_query_template',
            'is_active', 'is_default',
            'system_prompt', 'user_prompt_template',
            'knowledge_bases',
            'created_by_name', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None

    def get_document_template_name(self, obj):
        if obj.document_template:
            return obj.document_template.name
        return None

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class DocumentGeneratorStatsSerializer(serializers.Serializer):
    """Serializer para estatísticas de DocumentGenerators"""
    total = serializers.IntegerField()
    active = serializers.IntegerField()
    by_provider = serializers.DictField()


class VersionDiffSerializer(serializers.Serializer):
    """Serializer para Diff entre Versões"""
    old_version_id = serializers.CharField()
    new_version_id = serializers.CharField()
    summary = serializers.DictField()
    similarity_score = serializers.FloatField()
    changes = serializers.ListField()
    semantic_changes = serializers.ListField()
