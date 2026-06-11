"""
Serializers para o Sistema de Blueprints Dinâmicos.
"""
from rest_framework import serializers
from django.db.models import Count, Sum
from .utils import normalize_subsection_breaks
from .models import (
    DocumentBlueprint,
    BlueprintSection,
    BlueprintSubSection,
    SectionAgentConfig,
    GenerationSession,
    SectionGeneration,
    KnowledgeBase,
    KnowledgeBaseEmbedding,
    AgentKnowledgeBaseLink,
    KBSourceFile,
)


class SectionAgentConfigListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listar agentes."""
    variable_count = serializers.ReadOnlyField()

    class Meta:
        model = SectionAgentConfig
        fields = [
            'id',
            'name',
            'agent_type',
            'llm_provider',
            'model_name',
            'use_rag',
            'is_active',
            'variable_count',
        ]


class SectionAgentConfigDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalhes do agente."""
    variable_count = serializers.ReadOnlyField()
    variables = serializers.SerializerMethodField()

    class Meta:
        model = SectionAgentConfig
        fields = [
            'id',
            'name',
            'description',
            'agent_type',
            'system_prompt',
            'user_prompt_template',
            'llm_provider',
            'model_name',
            'temperature',
            'max_tokens',
            'use_rag',
            'rag_query_template',
            'rag_top_k',
            'rag_similarity_threshold',
            'is_active',
            'is_default',
            'variable_count',
            'variables',
            'created_at',
            'updated_at',
        ]

    def get_variables(self, obj):
        return obj.extract_variables()


class SectionAgentConfigWriteSerializer(serializers.ModelSerializer):
    """Serializer de escrita para atualizar agentes de seção."""

    class Meta:
        model = SectionAgentConfig
        fields = [
            'name', 'description', 'agent_type',
            'system_prompt', 'user_prompt_template',
            'llm_provider', 'model_name', 'temperature', 'max_tokens',
            'use_rag', 'rag_query_template', 'rag_top_k', 'rag_similarity_threshold',
            'is_active',
        ]

    def validate_temperature(self, value):
        if not (0.0 <= value <= 2.0):
            raise serializers.ValidationError('Temperature deve estar entre 0.0 e 2.0')
        return value

    def validate_max_tokens(self, value):
        if not (1 <= value <= 32000):
            raise serializers.ValidationError('Max tokens deve estar entre 1 e 32000')
        return value

    def validate_rag_similarity_threshold(self, value):
        if not (0.0 <= value <= 1.0):
            raise serializers.ValidationError('Threshold deve estar entre 0.0 e 1.0')
        return value


class BlueprintSubSectionSerializer(serializers.ModelSerializer):
    """Serializer para sub-seções com lógica OU."""
    generator_agent_id = serializers.PrimaryKeyRelatedField(
        source='generator_agent',
        read_only=True,
        allow_null=True
    )
    generator_agent_name = serializers.CharField(
        source='generator_agent.name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = BlueprintSubSection
        fields = [
            'id',
            'sub_number',
            'sub_name',
            'sub_key',
            'description',
            'help_text',
            'default_text',
            'generator_agent_id',
            'generator_agent_name',
            'section_fields',
            'order',
            'is_required',
            'is_active',
        ]


class BlueprintSectionListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listar seções do blueprint."""
    sub_sections = BlueprintSubSectionSerializer(
        many=True,
        read_only=True,
        source='get_active_sub_sections'
    )
    generator_agent_id = serializers.PrimaryKeyRelatedField(
        source='generator_agent',
        read_only=True,
        allow_null=True
    )
    generator_agent_name = serializers.CharField(
        source='generator_agent.name',
        read_only=True,
        allow_null=True
    )
    validator_agent_id = serializers.PrimaryKeyRelatedField(
        source='validator_agent',
        read_only=True,
        allow_null=True
    )
    validator_agent_name = serializers.CharField(
        source='validator_agent.name',
        read_only=True,
        allow_null=True
    )
    depends_on_ids = serializers.PrimaryKeyRelatedField(
        source='depends_on',
        many=True,
        read_only=True
    )

    class Meta:
        model = BlueprintSection
        fields = [
            'id',
            'section_number',
            'section_name',
            'section_key',
            'description',
            'instructions',
            'legal_reference',
            'section_fields',
            'sub_sections',
            'order',
            'is_required',
            'allow_skip',
            'is_active',
            'generator_agent_id',
            'generator_agent_name',
            'validator_agent_id',
            'validator_agent_name',
            'depends_on_ids',
        ]


class BlueprintSectionDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalhes da seção."""
    generator_agent = SectionAgentConfigListSerializer(read_only=True)
    validator_agent = SectionAgentConfigListSerializer(read_only=True)
    sub_sections = BlueprintSubSectionSerializer(
        many=True,
        read_only=True,
        source='get_active_sub_sections'
    )
    depends_on_ids = serializers.PrimaryKeyRelatedField(
        source='depends_on',
        many=True,
        read_only=True
    )

    class Meta:
        model = BlueprintSection
        fields = [
            'id',
            'section_number',
            'section_name',
            'section_key',
            'description',
            'instructions',
            'legal_reference',
            'section_fields',
            'sub_sections',
            'order',
            'is_required',
            'allow_skip',
            'max_generation_attempts',
            'is_active',
            'generator_agent',
            'validator_agent',
            'depends_on_ids',
            'created_at',
            'updated_at',
        ]


class DocumentBlueprintListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listar blueprints."""
    section_count = serializers.ReadOnlyField()
    document_type_id = serializers.UUIDField(source='document_type.id', read_only=True)
    document_type_code = serializers.CharField(source='document_type.code', read_only=True)
    document_type_display = serializers.CharField(source='document_type.name', read_only=True)
    # Áreas jurídicas do blueprint: lista de {code, name} para uso no wizard
    areas = serializers.SerializerMethodField()

    def get_areas(self, obj):
        return [{'code': a.code, 'name': a.name} for a in obj.areas.all()]

    class Meta:
        model = DocumentBlueprint
        fields = [
            'id',
            'name',
            'description',
            'document_type',
            'document_type_id',
            'document_type_code',
            'document_type_display',
            'areas',
            'version',
            'section_count',
            'is_active',
            'is_default',
            'created_at',
        ]


class DocumentBlueprintDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalhes do blueprint."""
    section_count = serializers.ReadOnlyField()
    document_type_id = serializers.UUIDField(source='document_type.id', read_only=True)
    document_type_code = serializers.CharField(source='document_type.code', read_only=True)
    document_type_display = serializers.CharField(source='document_type.name', read_only=True)
    areas = serializers.SerializerMethodField()

    def get_areas(self, obj):
        return [{'code': a.code, 'name': a.name} for a in obj.areas.all()]

    sections = BlueprintSectionListSerializer(
        many=True,
        read_only=True,
        source='get_ordered_sections'
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = DocumentBlueprint
        fields = [
            'id',
            'name',
            'description',
            'document_type',
            'document_type_id',
            'document_type_code',
            'document_type_display',
            'areas',
            'version',
            'legal_basis',
            'metadata',
            'section_count',
            'is_active',
            'is_default',
            'sections',
            'created_by_name',
            'created_at',
            'updated_at',
            # Identidade visual / branding
            'organization_name',
            'organization_acronym',
            'logo',
            'cover_logo',
            'header_text',
            'footer_text',
            'primary_color',
            'secondary_color',
            'custom_css',
            # Capa
            'cover_page_enabled',
            'cover_title',
            'cover_subtitle',
            'cover_organization_text',
            'cover_footer_text',
            'cover_background_color',
            # PDF (tipografia)
            'pdf_font_family',
            'pdf_font_size',
            'pdf_line_height',
            'pdf_text_align',
            'pdf_paragraph_indent',
            'pdf_paragraph_spacing',
            # PDF (margens)
            'pdf_page_margin_top',
            'pdf_page_margin_bottom',
            'pdf_page_margin_left',
            'pdf_page_margin_right',
        ]


class SectionGenerationSerializer(serializers.ModelSerializer):
    """Serializer para geração de seção."""
    section_name = serializers.CharField(
        source='section.section_name',
        read_only=True
    )
    section_number = serializers.IntegerField(
        source='section.section_number',
        read_only=True
    )
    content = serializers.SerializerMethodField()

    def get_content(self, obj):
        return normalize_subsection_breaks(obj.content)

    class Meta:
        model = SectionGeneration
        fields = [
            'id',
            'section_number',
            'section_name',
            'status',
            'content',
            'is_valid',
            'validation_score',
            'validation_errors',
            'validation_warnings',
            'validation_feedback',
            'generation_attempts',
            'tokens_used',
            'generation_time_ms',
            'validation_time_ms',
            'error_message',
            'started_at',
            'completed_at',
        ]


class GenerationSessionListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listar sessões de geração."""
    blueprint_name = serializers.CharField(
        source='blueprint.name',
        read_only=True
    )
    progress_percentage = serializers.ReadOnlyField()
    completed_sections_count = serializers.ReadOnlyField()
    total_selected_sections = serializers.ReadOnlyField()

    class Meta:
        model = GenerationSession
        fields = [
            'id',
            'blueprint_name',
            'objective',
            'status',
            'progress_percentage',
            'completed_sections_count',
            'total_selected_sections',
            'created_at',
            'completed_at',
        ]


class GenerationSessionDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalhes da sessão de geração."""
    blueprint = DocumentBlueprintListSerializer(read_only=True)
    section_generations = SectionGenerationSerializer(many=True, read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    completed_sections_count = serializers.ReadOnlyField()
    total_selected_sections = serializers.ReadOnlyField()
    selected_section_ids = serializers.PrimaryKeyRelatedField(
        source='selected_sections',
        many=True,
        read_only=True
    )
    latest_document_id = serializers.SerializerMethodField()

    def get_latest_document_id(self, obj):
        """Retorna o ID do GeneratedDocument mais recente via IntelligentSession."""
        if obj.intelligent_session:
            doc = obj.intelligent_session.generated_documents.order_by('-generated_at').first()
            if doc:
                return str(doc.id)
        return None

    class Meta:
        model = GenerationSession
        fields = [
            'id',
            'blueprint',
            'objective',
            'status',
            'config',
            'progress_percentage',
            'completed_sections_count',
            'total_selected_sections',
            'selected_section_ids',
            'section_generations',
            'error_message',
            'pipeline_graph',
            'total_input_tokens',
            'total_output_tokens',
            'total_tokens',
            'estimated_cost_usd',
            'started_at',
            'completed_at',
            'created_at',
            'updated_at',
            'latest_document_id',
        ]


class GenerationSessionCreateSerializer(serializers.Serializer):
    """Serializer para criar sessão de geração com blueprint."""
    blueprint_id = serializers.UUIDField(required=False)
    blueprint_name = serializers.CharField(required=False)
    objective = serializers.CharField(required=True)
    section_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text='IDs das seções a gerar (opcional, default: todas)'
    )

    def validate(self, data):
        """Valida que blueprint_id ou blueprint_name foi fornecido."""
        if not data.get('blueprint_id') and not data.get('blueprint_name'):
            raise serializers.ValidationError(
                'Forneça blueprint_id ou blueprint_name'
            )
        return data


# ========== KNOWLEDGE BASE MANAGEMENT ==========


class KnowledgeBaseListSerializer(serializers.ModelSerializer):
    """Serializer para listar KBs com stats."""
    blueprint_name = serializers.CharField(
        source='blueprint.name', read_only=True, default=None
    )
    blueprint_id = serializers.UUIDField(
        source='blueprint.id', read_only=True, default=None
    )
    document_type_name = serializers.CharField(
        source='blueprint.document_type.name', read_only=True, default=None
    )
    agent_config_name = serializers.CharField(
        source='agent_config.name', read_only=True, default=None
    )
    sources_count = serializers.SerializerMethodField()
    total_chunks = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgeBase
        fields = [
            'id', 'name', 'description', 'kb_layer',
            'blueprint_id', 'blueprint_name', 'document_type_name',
            'agent_config_name',
            'sources_count', 'total_chunks',
            'is_active', 'created_by_name',
            'created_at', 'updated_at',
        ]

    def get_sources_count(self, obj):
        return obj.embeddings.values('source_name').distinct().count()

    def get_total_chunks(self, obj):
        return obj.embeddings.count()

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.email
        return None


class KnowledgeBaseCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar/atualizar KB."""

    class Meta:
        model = KnowledgeBase
        fields = ['name', 'description', 'kb_layer', 'blueprint', 'agent_config', 'is_active']

    def validate(self, data):
        kb_layer = data.get('kb_layer', 'blueprint')
        if kb_layer == 'blueprint' and not data.get('blueprint'):
            raise serializers.ValidationError(
                {'blueprint': 'Blueprint é obrigatório para camada blueprint.'}
            )
        if kb_layer == 'agent' and not data.get('agent_config'):
            raise serializers.ValidationError(
                {'agent_config': 'Agente é obrigatório para camada agent.'}
            )
        return data


class KBSourceSerializer(serializers.Serializer):
    """Serializer para fontes agrupadas de uma KB."""
    source_name = serializers.CharField()
    source_type = serializers.CharField()
    chunks_count = serializers.IntegerField()
    total_characters = serializers.IntegerField()
    created_at = serializers.DateTimeField()


class KBUploadSerializer(serializers.Serializer):
    """Serializer para validar upload de documento a uma KB."""
    file = serializers.FileField(required=True)
    source_name = serializers.CharField(required=False, allow_blank=True)


class KBSourceFileSerializer(serializers.ModelSerializer):
    """Serializer para arquivos-fonte de uma KB."""
    uploaded_by_name = serializers.SerializerMethodField()
    file_size_mb = serializers.FloatField(read_only=True)

    class Meta:
        model = KBSourceFile
        fields = [
            'id', 'file_name', 'file_size', 'file_size_mb', 'file_type',
            'category', 'tags', 'chunk_count', 'status', 'processing_error',
            'uploaded_by', 'uploaded_by_name', 'created_at',
        ]

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name() or obj.uploaded_by.email
        return None


# ========== AGENT ↔ KB LINKS ==========


class AgentKnowledgeBaseLinkSerializer(serializers.ModelSerializer):
    """Serializer de leitura para vínculos Agente ↔ KB."""
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    agent_type = serializers.CharField(source='agent.agent_type', read_only=True)
    purpose_display = serializers.CharField(source='get_purpose_display', read_only=True)

    class Meta:
        model = AgentKnowledgeBaseLink
        fields = [
            'id', 'agent', 'agent_name', 'agent_type',
            'priority', 'purpose', 'purpose_display', 'instruction',
            'top_k', 'min_similarity', 'include_summary',
            'selected_sources',
            'is_active', 'created_at', 'updated_at',
        ]


class AgentKnowledgeBaseLinkWriteSerializer(serializers.ModelSerializer):
    """Serializer de escrita para criar/atualizar vínculos Agente ↔ KB."""

    class Meta:
        model = AgentKnowledgeBaseLink
        fields = [
            'agent', 'priority', 'purpose', 'instruction',
            'top_k', 'min_similarity', 'include_summary',
            'selected_sources',
        ]

    def validate(self, data):
        # Na criação, knowledge_base vem da URL (view injeta)
        kb = self.context.get('knowledge_base')
        agent = data.get('agent')
        if kb and agent:
            qs = AgentKnowledgeBaseLink.objects.filter(
                agent=agent, knowledge_base=kb
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {'agent': 'Este agente já está vinculado a esta KB.'}
                )
        return data


# ========== BLUEPRINT CRUD (Write Serializers) ==========


class DocumentBlueprintWriteSerializer(serializers.ModelSerializer):
    """Serializer de escrita para criar/atualizar blueprints."""

    class Meta:
        model = DocumentBlueprint
        fields = [
            'name', 'description', 'document_type', 'version', 'legal_basis',
            'organization_name', 'organization_acronym', 'header_text', 'footer_text',
            'cover_page_enabled', 'cover_title', 'cover_subtitle',
            'cover_organization_text', 'cover_footer_text', 'cover_background_color',
            'pdf_font_family', 'pdf_font_size', 'pdf_line_height', 'pdf_text_align',
            'pdf_paragraph_indent', 'pdf_paragraph_spacing',
            'pdf_page_margin_top', 'pdf_page_margin_bottom',
            'pdf_page_margin_left', 'pdf_page_margin_right',
            'primary_color', 'secondary_color', 'custom_css',
            'is_active', 'is_default',
        ]


class BlueprintSectionWriteSerializer(serializers.ModelSerializer):
    """Serializer de escrita para criar/atualizar seções de blueprint."""

    class Meta:
        model = BlueprintSection
        fields = [
            'section_number', 'section_name', 'section_key', 'description',
            'instructions', 'legal_reference', 'generator_agent', 'validator_agent',
            'order', 'is_required', 'allow_skip', 'max_generation_attempts',
            'section_fields', 'is_active',
        ]


class BlueprintSubSectionWriteSerializer(serializers.ModelSerializer):
    """Serializer de escrita para criar/atualizar sub-seções."""

    class Meta:
        model = BlueprintSubSection
        fields = [
            'sub_number', 'sub_name', 'sub_key', 'description', 'help_text',
            'default_text', 'generator_agent', 'section_fields',
            'order', 'is_required', 'is_active',
        ]


class SectionAgentListSerializer(serializers.ModelSerializer):
    """Serializer resumido para popular selects de agentes."""
    blueprint_name = serializers.SerializerMethodField()
    context_label = serializers.SerializerMethodField()
    agent_scope = serializers.SerializerMethodField()

    class Meta:
        model = SectionAgentConfig
        fields = ['id', 'name', 'agent_type', 'is_active', 'blueprint_name', 'context_label', 'agent_scope']

    def get_blueprint_name(self, obj):
        # Verificar agentes de seção (generator ou validator)
        section = (
            obj.generator_for_sections.select_related('blueprint').first()
            or obj.validator_for_sections.select_related('blueprint').first()
        )
        if section:
            return section.blueprint.name

        # Verificar agentes de sub-seção (generator_for_sub_sections)
        sub_section = (
            obj.generator_for_sub_sections
            .select_related('section__blueprint')
            .first()
        )
        if sub_section:
            return sub_section.section.blueprint.name

        return None

    def get_agent_scope(self, obj):
        """Retorna 'section', 'sub_section' ou 'unlinked'."""
        section = (
            obj.generator_for_sections.first()
            or obj.validator_for_sections.first()
        )
        if section:
            return 'section'

        sub_section = obj.generator_for_sub_sections.first()
        if sub_section:
            return 'sub_section'

        return 'unlinked'

    def get_context_label(self, obj):
        """Label descritivo: 'Seção: 4 - Nome (Blueprint)' ou 'Sub-seção: 4.1 - Nome (Blueprint)'."""
        # Agentes de seção
        section = obj.generator_for_sections.select_related('blueprint').first()
        if section:
            return f"Seção: {section.section_number} - {section.section_name} ({section.blueprint.name})"

        section = obj.validator_for_sections.select_related('blueprint').first()
        if section:
            return f"Seção: {section.section_number} - {section.section_name} ({section.blueprint.name})"

        # Agentes de sub-seção
        sub_section = (
            obj.generator_for_sub_sections
            .select_related('section__blueprint')
            .first()
        )
        if sub_section:
            return f"Sub-seção: {sub_section.sub_number} - {sub_section.sub_name} ({sub_section.section.blueprint.name})"

        return None
