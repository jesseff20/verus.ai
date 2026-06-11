"""
Admin para o Assistente Inteligente de Documentos
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from django import forms

from apps.core.models import LLMProvider, LLMModel

from .models import (
    IntelligentSession,
    UploadedDocument,
    GeneratedSection,
    GeneratedDocument,
    DocumentEmbedding,
    KnowledgeBase,
    KnowledgeBaseEmbedding,
    KBSourceFile,
    SectionAgentConfig,
    DocumentBlueprint,
    BlueprintSection,
    SectionImportConfig,
    AgentKnowledgeBaseLink,
    SectionPipelineStep,
    BlueprintSubSection,
    GenerationSession,
    SectionGeneration,
    SectionFeedback,
    LLMAuditLog,
    AgentTool,
    AgentToolLink,
    SectionGenerationLog,
)


# =============================================================================
# FILTROS CUSTOMIZADOS
# =============================================================================


class BlueprintFilterForAgent(admin.SimpleListFilter):
    """Filtra agentes pelo blueprint ao qual estão vinculados (via BlueprintSection)."""
    title = 'Blueprint'
    parameter_name = 'blueprint'

    def lookups(self, request, model_admin):
        blueprints = DocumentBlueprint.objects.filter(is_active=True).order_by('name')
        return [(bp.id, bp.name) for bp in blueprints]

    def queryset(self, request, queryset):
        if self.value():
            agent_ids = BlueprintSection.objects.filter(
                blueprint_id=self.value()
            ).values_list('generator_agent_id', 'validator_agent_id')
            ids = set()
            for gen_id, val_id in agent_ids:
                if gen_id:
                    ids.add(gen_id)
                if val_id:
                    ids.add(val_id)
            return queryset.filter(id__in=ids)
        return queryset


# =============================================================================
# INLINES
# =============================================================================


class UploadedDocumentInline(admin.TabularInline):
    model = UploadedDocument
    extra = 0
    readonly_fields = ['id', 'filename', 'file_type', 'file_size', 'extraction_status', 'uploaded_at']
    fields = ['filename', 'file_type', 'file_size', 'extraction_status', 'uploaded_at']
    can_delete = False
    show_change_link = True


class GeneratedSectionInline(admin.TabularInline):
    model = GeneratedSection
    extra = 0
    readonly_fields = ['section_number', 'section_name', 'is_valid', 'generation_attempts', 'created_at']
    fields = ['section_number', 'section_name', 'is_valid', 'generation_attempts', 'created_at']
    can_delete = False
    show_change_link = True
    ordering = ['section_number']


class GeneratedDocumentInline(admin.TabularInline):
    model = GeneratedDocument
    extra = 0
    readonly_fields = ['id', 'title', 'pdf_generated', 'docx_generated', 'overall_score', 'generated_at']
    fields = ['title', 'pdf_generated', 'docx_generated', 'overall_score', 'generated_at']
    can_delete = False
    show_change_link = True


class BlueprintSectionInline(admin.TabularInline):
    model = BlueprintSection
    extra = 1
    ordering = ['order', 'section_number']
    fields = ['section_number', 'section_name', 'section_key', 'order', 'generator_agent', 'validator_agent', 'is_required', 'is_active']
    autocomplete_fields = ['generator_agent', 'validator_agent']
    show_change_link = True


class SectionGenerationInline(admin.TabularInline):
    model = SectionGeneration
    extra = 0
    readonly_fields = ['section', 'status', 'is_valid', 'validation_score', 'generation_attempts', 'tokens_used']
    fields = ['section', 'status', 'is_valid', 'validation_score', 'generation_attempts', 'tokens_used']
    can_delete = False
    show_change_link = True


class KnowledgeBaseEmbeddingInline(admin.TabularInline):
    """Inline de embeddings — usado dentro de KBSourceFileAdmin (via FK source_file)."""
    model = KnowledgeBaseEmbedding
    fk_name = 'source_file'
    extra = 0
    readonly_fields = ['chunk_index', 'chunk_text_preview', 'chunk_size', 'embedding_model', 'created_at']
    fields = ['chunk_index', 'chunk_text_preview', 'chunk_size', 'embedding_model', 'created_at']
    can_delete = True
    show_change_link = True
    max_num = 50

    def chunk_text_preview(self, obj):
        if obj.chunk_text and len(obj.chunk_text) > 100:
            return obj.chunk_text[:100] + '...'
        return obj.chunk_text or ''
    chunk_text_preview.short_description = 'Texto (preview)'


class KBSourceFileInline(admin.TabularInline):
    """Inline de documentos/fontes — usado dentro de KnowledgeBaseAdmin."""
    model = KBSourceFile
    extra = 0
    readonly_fields = ['file_name', 'file_type', 'file_size_display', 'chunk_count', 'status_badge', 'uploaded_by', 'created_at']
    fields = ['file_name', 'file_type', 'file_size_display', 'chunk_count', 'status_badge', 'uploaded_by', 'created_at']
    can_delete = True
    show_change_link = True

    def file_size_display(self, obj):
        if obj.file_size:
            return f"{round(obj.file_size / (1024 * 1024), 2)} MB"
        return '—'
    file_size_display.short_description = 'Tamanho'

    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'processing': '#17a2b8',
            'completed': '#28a745',
            'failed': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        label = obj.get_status_display()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, label
        )
    status_badge.short_description = 'Status'


# =============================================================================
# MODELOS EXISTENTES
# =============================================================================


@admin.register(IntelligentSession)
class IntelligentSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'document_type', 'status', 'status_badge', 'created_at']
    list_filter = ['status', 'document_type', 'created_at']
    search_fields = ['id', 'user__username', 'user__email', 'objective']
    readonly_fields = ['id', 'kb_collection_id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    inlines = [UploadedDocumentInline, GeneratedSectionInline, GeneratedDocumentInline]

    fieldsets = (
        ('Identificacao', {
            'fields': ('id', 'user', 'document_type')
        }),
        ('Conteudo', {
            'fields': ('objective',)
        }),
        ('Status', {
            'fields': ('status', 'error_message', 'kb_collection_id')
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'initialized': '#6c757d',
            'uploading': '#17a2b8',
            'processing': '#ffc107',
            'generating': '#007bff',
            'validating': '#6f42c1',
            'formatting': '#20c997',
            'completed': '#28a745',
            'failed': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(UploadedDocument)
class UploadedDocumentAdmin(admin.ModelAdmin):
    """Acessível como inline em IntelligentSession. Oculto do menu lateral."""
    list_display = ['filename', 'session', 'file_type', 'file_size_formatted', 'extraction_status', 'uploaded_at']
    list_filter = ['file_type', 'extraction_status', 'uploaded_at']
    search_fields = ['filename', 'session__id']
    readonly_fields = ['id', 'file_size', 'uploaded_at']
    raw_id_fields = ['session']

    def has_module_permission(self, request):
        return False

    def file_size_formatted(self, obj):
        if obj.file_size < 1024:
            return f"{obj.file_size} B"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.1f} KB"
        else:
            return f"{obj.file_size / (1024 * 1024):.1f} MB"
    file_size_formatted.short_description = 'Tamanho'


@admin.register(GeneratedSection)
class GeneratedSectionAdmin(admin.ModelAdmin):
    """Modelo legado. Acessível como inline em IntelligentSession. Oculto do menu lateral."""
    list_display = ['session', 'section_number', 'section_name', 'is_valid', 'generation_attempts', 'created_at']
    list_filter = ['is_valid', 'section_number', 'created_at']
    search_fields = ['session__id', 'section_name', 'content']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['session']

    fieldsets = (
        ('Identificacao', {
            'fields': ('id', 'session', 'section_number', 'section_name')
        }),
        ('Conteudo', {
            'fields': ('content', 'agent_reasoning'),
            'classes': ('wide',)
        }),
        ('Validacao', {
            'fields': ('is_valid', 'validation_errors', 'validation_warnings', 'generation_attempts')
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    """Modelo legado. Acessível como inline em IntelligentSession. Oculto do menu lateral."""
    list_display = ['id', 'session', 'title', 'pdf_generated', 'docx_generated', 'overall_score', 'generated_at']
    list_filter = ['pdf_generated', 'docx_generated', 'generated_at']
    search_fields = ['session__id', 'title']
    readonly_fields = ['id', 'file_size_markdown', 'file_size_docx', 'file_size_pdf', 'generated_at', 'updated_at']
    raw_id_fields = ['session']

    def has_module_permission(self, request):
        return False

    fieldsets = (
        ('Identificacao', {
            'fields': ('id', 'session', 'title')
        }),
        ('Conteudo', {
            'fields': ('markdown_content',),
            'classes': ('wide', 'collapse')
        }),
        ('Arquivos', {
            'fields': ('docx_file', 'pdf_file', 'docx_url', 'pdf_url', 'docx_generated', 'pdf_generated')
        }),
        ('Tamanhos', {
            'fields': ('file_size_markdown', 'file_size_docx', 'file_size_pdf'),
            'classes': ('collapse',)
        }),
        ('Validacao', {
            'fields': ('overall_score', 'valid_sections_count', 'total_sections', 'metadata')
        }),
        ('Datas', {
            'fields': ('generated_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DocumentEmbedding)
class DocumentEmbeddingAdmin(admin.ModelAdmin):
    """Embeddings dos documentos uploadados por sessão."""
    list_display = ['document', 'chunk_index', 'chunk_size', 'embedding_model', 'created_at']
    list_filter = ['embedding_model', 'created_at']
    search_fields = ['document__filename', 'chunk_text']
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['document', 'session']

    fieldsets = (
        ('Relacionamentos', {
            'fields': ('document', 'session')
        }),
        ('Chunk', {
            'fields': ('chunk_index', 'chunk_text', 'chunk_size')
        }),
        ('Embedding', {
            'fields': ('embedding_model', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Datas', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


class KBAgentLinkInline(admin.TabularInline):
    """Inline no KnowledgeBase: quais agentes consomem esta KB."""
    model = AgentKnowledgeBaseLink
    fk_name = 'knowledge_base'
    extra = 1
    fields = ['priority', 'agent', 'purpose', 'instruction', 'top_k', 'min_similarity', 'include_summary', 'is_active']
    autocomplete_fields = ['agent']
    ordering = ['priority']
    verbose_name = 'Agente vinculado'
    verbose_name_plural = 'Agentes vinculados (quem consome esta KB)'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('agent')


@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ['name', 'kb_layer_badge', 'blueprint', 'is_active', 'embeddings_count', 'created_at']
    list_filter = ['kb_layer', 'is_active', 'blueprint', 'created_at']
    search_fields = ['name', 'description']
    list_per_page = 30
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['blueprint', 'agent_config', 'section', 'created_by']
    inlines = [KBSourceFileInline, KBAgentLinkInline]

    fieldsets = (
        ('Identificacao', {
            'fields': ('id', 'name', 'description')
        }),
        ('Hierarquia de Camadas', {
            'fields': ('kb_layer', 'blueprint', 'agent_config', 'section'),
            'description': (
                'Global = todos os agentes acessam (normas gerais). '
                'Blueprint = específica de um tipo de documento. '
                'Agente = melhores resultados de um agente de seção. '
                'Exemplo Real de Seção = exemplos humanos por seção específica.'
            )
        }),
        ('Flags', {
            'fields': ('is_active',)
        }),
        ('Auditoria', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def embeddings_count(self, obj):
        return obj.embeddings.count()
    embeddings_count.short_description = 'Embeddings'

    def kb_layer_badge(self, obj):
        colors = {
            'global': '#17a2b8',
            'blueprint': '#007bff',
            'agent': '#28a745',
            'section_example': '#e83e8c',
        }
        color = colors.get(obj.kb_layer, '#6c757d')
        label = dict(KnowledgeBase.KB_LAYER_CHOICES).get(obj.kb_layer, obj.kb_layer)
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, label
        )
    kb_layer_badge.short_description = 'Camada'


@admin.register(KBSourceFile)
class KBSourceFileAdmin(admin.ModelAdmin):
    """Documentos/fontes das Bases de Conhecimento — com embeddings inline."""
    list_display = ['file_name', 'knowledge_base_link', 'file_type', 'file_size_display', 'chunk_count', 'status_badge', 'uploaded_by', 'created_at']
    list_filter = ['status', 'file_type', 'knowledge_base__kb_layer', 'knowledge_base']
    search_fields = ['file_name', 'knowledge_base__name']
    list_per_page = 30
    readonly_fields = ['id', 'created_at']
    autocomplete_fields = ['knowledge_base', 'uploaded_by']
    inlines = [KnowledgeBaseEmbeddingInline]

    fieldsets = (
        ('Documento', {
            'fields': ('id', 'knowledge_base', 'file_name', 'file_type', 'file_size', 'file')
        }),
        ('Processamento', {
            'fields': ('status', 'chunk_count', 'embeddings_count_display', 'processing_error')
        }),
        ('Categorização', {
            'fields': ('category', 'tags'),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('uploaded_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['id', 'created_at', 'embeddings_count_display']

    def embeddings_count_display(self, obj):
        if not obj.pk:
            return '—'
        count = obj.embeddings.count()
        return f"{count} embeddings"
    embeddings_count_display.short_description = 'Embeddings Gerados'

    def knowledge_base_link(self, obj):
        url = reverse('admin:intelligent_assistant_knowledgebase_change', args=[obj.knowledge_base.id])
        layer = dict(KnowledgeBase.KB_LAYER_CHOICES).get(obj.knowledge_base.kb_layer, '')
        return format_html('<a href="{}">{}</a> <small>({})</small>', url, obj.knowledge_base.name, layer)
    knowledge_base_link.short_description = 'Base de Conhecimento'

    def file_size_display(self, obj):
        if obj.file_size:
            return f"{round(obj.file_size / (1024 * 1024), 2)} MB"
        return '—'
    file_size_display.short_description = 'Tamanho'

    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'processing': '#17a2b8',
            'completed': '#28a745',
            'failed': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        label = obj.get_status_display()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, label
        )
    status_badge.short_description = 'Status'


@admin.register(KnowledgeBaseEmbedding)
class KnowledgeBaseEmbeddingAdmin(admin.ModelAdmin):
    """Embeddings individuais das Bases de Conhecimento."""
    list_display = ['id_short', 'source_name', 'knowledge_base_link', 'chunk_index', 'chunk_size', 'embedding_model', 'created_at']
    list_filter = ['source_type', 'embedding_model', 'knowledge_base']
    search_fields = ['source_name', 'chunk_text', 'knowledge_base__name']
    list_per_page = 50
    readonly_fields = ['id', 'created_at']

    fieldsets = (
        ('Identificação', {
            'fields': ('id', 'knowledge_base', 'source_file', 'source_name', 'source_type')
        }),
        ('Chunk', {
            'fields': ('chunk_index', 'chunk_text', 'chunk_size')
        }),
        ('Embedding', {
            'fields': ('embedding_model',),
            'description': 'O vetor de embedding não é exibido por ser muito grande.'
        }),
        ('Metadados', {
            'fields': ('summary', 'metadata', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def id_short(self, obj):
        return str(obj.id)[:8]
    id_short.short_description = 'ID'

    def knowledge_base_link(self, obj):
        url = reverse('admin:intelligent_assistant_knowledgebase_change', args=[obj.knowledge_base.id])
        return format_html('<a href="{}">{}</a>', url, obj.knowledge_base.name)
    knowledge_base_link.short_description = 'Base de Conhecimento'


# =============================================================================
# NOVOS MODELOS - SISTEMA DINAMICO DE AGENTES
# =============================================================================


class AgentKnowledgeBaseLinkInline(admin.TabularInline):
    """Inline no SectionAgentConfig: quais KBs este agente consome."""
    model = AgentKnowledgeBaseLink
    fk_name = 'agent'
    extra = 1
    fields = ['priority', 'knowledge_base', 'purpose', 'instruction', 'top_k', 'min_similarity', 'include_summary', 'is_active']
    autocomplete_fields = ['knowledge_base']
    ordering = ['priority']
    verbose_name = 'Vínculo KB'
    verbose_name_plural = 'Vínculos KB (fontes de dados deste agente)'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('knowledge_base')


class AgentToolLinkInline(admin.TabularInline):
    """Inline no SectionAgentConfig: quais Tools este agente usa durante geração."""
    model = AgentToolLink
    extra = 0
    fields = ['tool', 'priority', 'custom_config', 'enabled']
    ordering = ['priority']
    verbose_name = 'Tool'
    verbose_name_plural = 'Tools (ferramentas de busca deste agente)'


@admin.register(AgentTool)
class AgentToolAdmin(admin.ModelAdmin):
    """Admin para registro de tools disponíveis para agentes."""
    list_display = ['name', 'tool_type', 'service_path', 'method_name', 'is_active']
    list_filter = ['tool_type', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at']
    fieldsets = (
        ('Identificação', {
            'fields': ('id', 'name', 'tool_type', 'description'),
        }),
        ('Serviço', {
            'fields': ('service_path', 'method_name', 'default_config'),
            'description': 'Caminho do service Python e método a chamar.',
        }),
        ('Status', {
            'fields': ('is_active', 'created_at'),
        }),
    )


class SectionAgentConfigForm(forms.ModelForm):
    """Form customizado que transforma model_name em select dinâmico."""

    model_name = forms.ChoiceField(
        label='Modelo',
        help_text='Selecione o modelo do provider escolhido acima',
    )

    class Meta:
        model = SectionAgentConfig
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Montar choices agrupadas por provider
        choices = [('', '--- Selecione o modelo ---')]
        for provider in LLMProvider.objects.filter(is_active=True).prefetch_related('models'):
            provider_models = provider.models.filter(is_active=True).order_by('display_order')
            if provider_models.exists():
                group = [(m.model_id, f"{m.display_name}") for m in provider_models]
                choices.append((provider.name, group))
        self.fields['model_name'].choices = choices

        # Se o valor atual não está nos choices (modelo legado), adicionar
        current_value = self.initial.get('model_name') or (self.instance.model_name if self.instance.pk else '')
        if current_value:
            flat_values = []
            for item in choices:
                if isinstance(item[1], list):
                    flat_values.extend([v for v, _ in item[1]])
                else:
                    flat_values.append(item[0])
            if current_value not in flat_values:
                choices.append(('Legado', [(current_value, f"{current_value} (legado)")]))
                self.fields['model_name'].choices = choices

    class Media:
        js = ('admin/js/llm_model_filter.js',)


@admin.register(SectionAgentConfig)
class SectionAgentConfigAdmin(admin.ModelAdmin):
    form = SectionAgentConfigForm
    list_display = ['name', 'agent_type', 'agent_type_badge', 'blueprint_display', 'llm_provider', 'model_name', 'use_rag', 'kb_links_count', 'is_active', 'is_default', 'updated_at']
    list_filter = [BlueprintFilterForAgent, 'agent_type', 'llm_provider', 'is_active', 'is_default', 'use_rag', 'created_at']
    search_fields = ['name', 'description']
    list_per_page = 30
    readonly_fields = ['id', 'variable_count', 'section_location', 'effective_kbs_display', 'created_at', 'updated_at']
    autocomplete_fields = ['created_by']
    date_hierarchy = 'created_at'
    inlines = [AgentKnowledgeBaseLinkInline, AgentToolLinkInline]

    fieldsets = (
        ('Identificacao', {
            'fields': ('id', 'name', 'description', 'agent_type', 'section_location')
        }),
        ('Prompts', {
            'fields': ('system_prompt', 'user_prompt_template', 'variable_count'),
            'classes': ('wide',),
            'description': 'Use {{variavel}} para placeholders. Variaveis disponiveis: objective, context, previous_sections, current_content, section_name, section_number'
        }),
        ('Configuracoes LLM', {
            'fields': ('llm_provider', 'model_name', 'temperature', 'max_tokens')
        }),
        ('Configuracoes RAG', {
            'fields': ('use_rag', 'rag_query_template', 'rag_top_k', 'rag_similarity_threshold', 'effective_kbs_display'),
            'description': 'Vincule bases de conhecimento usando os "Vínculos KB" abaixo (inline AgentKnowledgeBaseLink).'
        }),
        ('Flags', {
            'fields': ('is_active', 'is_default')
        }),
        ('Auditoria', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('llm-models-json/', self.admin_site.admin_view(self.llm_models_json), name='llm-models-json'),
        ]
        return custom_urls + urls

    def llm_models_json(self, request):
        """Endpoint JSON que retorna modelos agrupados por provider code."""
        from django.http import JsonResponse
        data = {}
        for provider in LLMProvider.objects.filter(is_active=True).prefetch_related('models'):
            models = provider.models.filter(is_active=True).order_by('display_order')
            data[provider.code] = [
                {'id': m.model_id, 'name': m.display_name}
                for m in models
            ]
        return JsonResponse(data)

    def agent_type_badge(self, obj):
        colors = {
            'generator': '#007bff',
            'validator': '#28a745',
            'analyzer': '#e83e8c',
            'refiner': '#fd7e14',
        }
        color = colors.get(obj.agent_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_agent_type_display()
        )
    agent_type_badge.short_description = 'Tipo'

    def kb_links_count(self, obj):
        count = obj.kb_links.filter(is_active=True).count()
        if count > 0:
            return format_html('<span style="color: #007bff; font-weight: bold;">{} vínculo(s)</span>', count)
        return format_html('<span style="color: #999;">-</span>')
    kb_links_count.short_description = 'KBs (Links)'

    def blueprint_display(self, obj):
        """Mostra o blueprint vinculado ao agente (via seções)."""
        section = BlueprintSection.objects.filter(
            generator_agent=obj
        ).select_related('blueprint').first()
        if not section:
            section = BlueprintSection.objects.filter(
                validator_agent=obj
            ).select_related('blueprint').first()
        if section:
            url = reverse('admin:intelligent_assistant_documentblueprint_change', args=[section.blueprint.id])
            return format_html('<a href="{}">{}</a>', url, section.blueprint.name[:25])
        return '-'
    blueprint_display.short_description = 'Blueprint'

    def section_location(self, obj):
        """Mostra blueprint > secao > sub-secao onde este agente atua."""
        if not obj.pk:
            return '-'
        locations = []
        for sec in BlueprintSection.objects.filter(generator_agent=obj).select_related('blueprint'):
            url = reverse('admin:intelligent_assistant_blueprintsection_change', args=[sec.id])
            locations.append(
                '<tr style="background:#fff;">'
                '<td style="padding:4px 8px; color:#333; border:1px solid #ddd;">{}</td>'
                '<td style="padding:4px 8px; color:#333; border:1px solid #ddd;">'
                '<a href="{}" style="color:#417690; text-decoration:underline;">S{} - {}</a></td>'
                '<td style="padding:4px 8px; color:#333; border:1px solid #ddd;">'
                '<span style="background:#007bff; color:#fff; padding:2px 6px; border-radius:3px; font-size:11px;">Gerador</span></td>'
                '</tr>'.format(sec.blueprint.name[:30], url, sec.section_number, sec.section_name[:35])
            )
        for sec in BlueprintSection.objects.filter(validator_agent=obj).select_related('blueprint'):
            url = reverse('admin:intelligent_assistant_blueprintsection_change', args=[sec.id])
            locations.append(
                '<tr style="background:#fff;">'
                '<td style="padding:4px 8px; color:#333; border:1px solid #ddd;">{}</td>'
                '<td style="padding:4px 8px; color:#333; border:1px solid #ddd;">'
                '<a href="{}" style="color:#417690; text-decoration:underline;">S{} - {}</a></td>'
                '<td style="padding:4px 8px; color:#333; border:1px solid #ddd;">'
                '<span style="background:#28a745; color:#fff; padding:2px 6px; border-radius:3px; font-size:11px;">Validador</span></td>'
                '</tr>'.format(sec.blueprint.name[:30], url, sec.section_number, sec.section_name[:35])
            )
        for sub in BlueprintSubSection.objects.filter(generator_agent=obj).select_related('section__blueprint'):
            url = reverse('admin:intelligent_assistant_blueprintsubsection_change', args=[sub.id])
            locations.append(
                '<tr style="background:#fff;">'
                '<td style="padding:4px 8px; color:#333; border:1px solid #ddd;">{}</td>'
                '<td style="padding:4px 8px; color:#333; border:1px solid #ddd;">'
                '<a href="{}" style="color:#417690; text-decoration:underline;">{} - {}</a></td>'
                '<td style="padding:4px 8px; color:#333; border:1px solid #ddd;">'
                '<span style="background:#17a2b8; color:#fff; padding:2px 6px; border-radius:3px; font-size:11px;">Gerador Sub</span></td>'
                '</tr>'.format(sub.section.blueprint.name[:30], url, sub.sub_number, sub.sub_name[:35])
            )
        if not locations:
            return format_html('<em style="color:#999;">Agente nao vinculado a nenhuma secao.</em>')
        table = (
            '<table style="border-collapse:collapse; width:100%; font-size:12px; background:#fff;">'
            '<thead><tr style="background:#417690; color:#fff;">'
            '<th style="padding:5px 8px; text-align:left; border:1px solid #3a6b82;">Blueprint</th>'
            '<th style="padding:5px 8px; text-align:left; border:1px solid #3a6b82;">Secao/Sub-secao</th>'
            '<th style="padding:5px 8px; text-align:left; border:1px solid #3a6b82;">Papel</th>'
            '</tr></thead><tbody>{}</tbody></table>'
        ).format(''.join(locations))
        return format_html(table)
    section_location.short_description = 'Onde este agente e usado'

    def effective_kbs_display(self, obj):
        """Mostra todas as KBs efetivas: M2M diretos + fallback (global, blueprint)."""
        if not obj.pk:
            return '-'
        rows = []
        # KBs via M2M (AgentKnowledgeBaseLink)
        for link in obj.kb_links.filter(is_active=True).select_related('knowledge_base'):
            kb = link.knowledge_base
            url = reverse('admin:intelligent_assistant_knowledgebase_change', args=[kb.id])
            count = kb.embeddings.count()
            rows.append(
                '<tr style="background:#fff;">'
                '<td style="padding:4px 8px; color:#333; border:1px solid #ddd;">'
                '<a href="{}" style="color:#417690; text-decoration:underline;">{}</a></td>'
                '<td style="padding:4px 8px; color:#333; border:1px solid #ddd;">{}</td>'
                '<td style="padding:4px 8px; color:#333; border:1px solid #ddd;">{} embeddings</td>'
                '<td style="padding:4px 8px; color:#333; border:1px solid #ddd;">'
                '<span style="background:#28a745; color:#fff; padding:2px 6px; border-radius:3px; font-size:11px;">M2M direto</span></td>'
                '</tr>'.format(url, kb.name[:35], kb.get_kb_layer_display(), count)
            )
        # KBs de blueprint (fallback via FK)
        blueprint_ids = set()
        for sec_bp in BlueprintSection.objects.filter(generator_agent=obj).values_list('blueprint_id', flat=True):
            blueprint_ids.add(sec_bp)
        for sec_bp in BlueprintSection.objects.filter(validator_agent=obj).values_list('blueprint_id', flat=True):
            blueprint_ids.add(sec_bp)
        for sub_bp in BlueprintSubSection.objects.filter(generator_agent=obj).values_list('section__blueprint_id', flat=True):
            blueprint_ids.add(sub_bp)
        for kb in KnowledgeBase.objects.filter(blueprint_id__in=blueprint_ids, is_active=True):
            url = reverse('admin:intelligent_assistant_knowledgebase_change', args=[kb.id])
            count = kb.embeddings.count()
            rows.append(
                '<tr style="background:#fff;">'
                '<td style="padding:4px 8px; color:#333; border:1px solid #ddd;">'
                '<a href="{}" style="color:#417690; text-decoration:underline;">{}</a></td>'
                '<td style="padding:4px 8px; color:#333; border:1px solid #ddd;">{}</td>'
                '<td style="padding:4px 8px; color:#333; border:1px solid #ddd;">{} embeddings</td>'
                '<td style="padding:4px 8px; color:#333; border:1px solid #ddd;">'
                '<span style="background:#007bff; color:#fff; padding:2px 6px; border-radius:3px; font-size:11px;">Blueprint FK</span></td>'
                '</tr>'.format(url, kb.name[:35], kb.get_kb_layer_display(), count)
            )
        # KBs globais (fallback)
        for kb in KnowledgeBase.objects.filter(kb_layer='global', is_active=True):
            url = reverse('admin:intelligent_assistant_knowledgebase_change', args=[kb.id])
            count = kb.embeddings.count()
            rows.append(
                '<tr style="background:#fff;">'
                '<td style="padding:4px 8px; color:#333; border:1px solid #ddd;">'
                '<a href="{}" style="color:#417690; text-decoration:underline;">{}</a></td>'
                '<td style="padding:4px 8px; color:#333; border:1px solid #ddd;">{}</td>'
                '<td style="padding:4px 8px; color:#333; border:1px solid #ddd;">{} embeddings</td>'
                '<td style="padding:4px 8px; color:#333; border:1px solid #ddd;">'
                '<span style="background:#17a2b8; color:#fff; padding:2px 6px; border-radius:3px; font-size:11px;">Global (fallback)</span></td>'
                '</tr>'.format(url, kb.name[:35], kb.get_kb_layer_display(), count)
            )
        if not rows:
            return format_html('<em style="color:#999;">Nenhuma KB acessivel.</em>')
        table = (
            '<table style="border-collapse:collapse; width:100%; font-size:12px; background:#fff;">'
            '<thead><tr style="background:#417690; color:#fff;">'
            '<th style="padding:5px 8px; text-align:left; border:1px solid #3a6b82;">Base de Conhecimento</th>'
            '<th style="padding:5px 8px; text-align:left; border:1px solid #3a6b82;">Camada</th>'
            '<th style="padding:5px 8px; text-align:left; border:1px solid #3a6b82;">Tamanho</th>'
            '<th style="padding:5px 8px; text-align:left; border:1px solid #3a6b82;">Origem</th>'
            '</tr></thead><tbody>{}</tbody></table>'
        ).format(''.join(rows))
        return format_html(table)
    effective_kbs_display.short_description = 'KBs efetivas (todas as fontes)'

    def get_search_results(self, request, queryset, search_term):
        """Permite autocomplete em outros admins"""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        return queryset, use_distinct


class ColorPickerWidget(forms.TextInput):
    """Widget de seletor de cores com preview."""
    template_name = 'admin/widgets/color_picker.html'

    def __init__(self, attrs=None):
        default_attrs = {'type': 'color', 'style': 'width: 60px; height: 30px; padding: 0; cursor: pointer;'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)


class DocumentBlueprintForm(forms.ModelForm):
    """Formulário customizado com color pickers para campos de cor."""

    class Meta:
        model = DocumentBlueprint
        fields = '__all__'
        widgets = {
            'primary_color': forms.TextInput(attrs={
                'type': 'color',
                'style': 'width: 80px; height: 35px; padding: 2px; cursor: pointer; vertical-align: middle;'
            }),
            'secondary_color': forms.TextInput(attrs={
                'type': 'color',
                'style': 'width: 80px; height: 35px; padding: 2px; cursor: pointer; vertical-align: middle;'
            }),
            'cover_background_color': forms.TextInput(attrs={
                'type': 'color',
                'style': 'width: 80px; height: 35px; padding: 2px; cursor: pointer; vertical-align: middle;'
            }),
        }


class BlueprintKnowledgeBaseInline(admin.TabularInline):
    """KBs associadas a este blueprint (Camada 2)."""
    model = KnowledgeBase
    fk_name = 'blueprint'
    extra = 0
    fields = ['name', 'kb_layer', 'is_active', 'embeddings_count_display']
    readonly_fields = ['embeddings_count_display']
    show_change_link = True

    def embeddings_count_display(self, obj):
        if obj.pk:
            return obj.embeddings.count()
        return 0
    embeddings_count_display.short_description = 'Embeddings'


@admin.register(DocumentBlueprint)
class DocumentBlueprintAdmin(admin.ModelAdmin):
    form = DocumentBlueprintForm
    list_display = ['name', 'document_type', 'version', 'section_count', 'organization_acronym', 'cover_page_enabled', 'is_active', 'is_default', 'created_at']
    list_filter = ['document_type', 'is_active', 'is_default', 'cover_page_enabled', 'created_at']
    search_fields = ['name', 'description', 'legal_basis', 'organization_name', 'organization_acronym']
    readonly_fields = ['id', 'section_count', 'sections_agents_map', 'created_at', 'updated_at', 'logo_preview', 'cover_logo_preview']
    autocomplete_fields = ['created_by']
    inlines = [BlueprintKnowledgeBaseInline, BlueprintSectionInline]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Identificacao', {
            'fields': ('id', 'name', 'description', 'document_type')
        }),
        ('Versao e Base Legal', {
            'fields': ('version', 'legal_basis'),
            'classes': ('collapse',)
        }),
        ('Personalizacao do PDF', {
            'fields': ('organization_name', 'organization_acronym', 'logo', 'logo_preview', 'header_text', 'footer_text'),
            'description': 'Configure a aparencia do documento PDF gerado'
        }),
        ('Pagina de Rosto', {
            'fields': (
                'cover_page_enabled',
                'cover_logo', 'cover_logo_preview',
                'cover_title', 'cover_subtitle',
                'cover_organization_text',
                'cover_footer_text',
                'cover_background_color'
            ),
            'description': 'Configure a pagina de rosto (capa) do documento'
        }),
        ('Tipografia do PDF', {
            'fields': (
                'pdf_font_family', 'pdf_font_size',
                'pdf_line_height', 'pdf_text_align',
                'pdf_paragraph_indent', 'pdf_paragraph_spacing'
            ),
            'classes': ('collapse',),
            'description': 'Configure fonte, tamanho e espacamento do texto'
        }),
        ('Margens da Pagina', {
            'fields': (
                'pdf_page_margin_top', 'pdf_page_margin_bottom',
                'pdf_page_margin_left', 'pdf_page_margin_right'
            ),
            'classes': ('collapse',),
            'description': 'Configure as margens da pagina (ex: 2.5cm, 3cm)'
        }),
        ('Cores e Estilo', {
            'fields': ('primary_color', 'secondary_color', 'custom_css'),
            'classes': ('collapse',),
            'description': 'Cores em formato hexadecimal (ex: #7030A0)'
        }),
        ('Metadados', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Flags', {
            'fields': ('is_active', 'is_default')
        }),
        ('Mapa de Agentes por Secao', {
            'fields': ('sections_agents_map',),
        }),
        ('Estatisticas', {
            'fields': ('section_count',),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def sections_agents_map(self, obj):
        if not obj.pk:
            return '-'
        sections = obj.sections.prefetch_related(
            'sub_sections__generator_agent'
        ).select_related(
            'generator_agent', 'validator_agent'
        ).order_by('order', 'section_number')
        if not sections.exists():
            return format_html('<em>Nenhuma secao cadastrada.</em>')

        rows = []
        for sec in sections:
            gen_html = self._agent_link(sec.generator_agent)
            val_html = self._agent_link(sec.validator_agent)
            provider_model = '{}/{}'.format(
                sec.generator_agent.llm_provider, sec.generator_agent.model_name[:25]
            ) if sec.generator_agent else '-'
            rows.append(
                '<tr style="background:#eef2f7;">'
                '<td style="padding:5px 8px; font-weight:bold; color:#333; border:1px solid #ccc;">S{}</td>'
                '<td style="padding:5px 8px; font-weight:bold; color:#333; border:1px solid #ccc;">{}</td>'
                '<td style="padding:5px 8px; color:#333; border:1px solid #ccc;">{}</td>'
                '<td style="padding:5px 8px; color:#333; border:1px solid #ccc;">{}</td>'
                '<td style="padding:5px 8px; color:#333; border:1px solid #ccc; font-size:11px;">{}</td>'
                '</tr>'.format(
                    sec.section_number, sec.section_name[:45], gen_html, val_html, provider_model,
                )
            )
            for sub in sec.sub_sections.all().order_by('order', 'sub_number'):
                sub_gen = self._agent_link(sub.generator_agent)
                sub_provider = '{}/{}'.format(
                    sub.generator_agent.llm_provider, sub.generator_agent.model_name[:25]
                ) if sub.generator_agent else '-'
                rows.append(
                    '<tr style="background:#fff;">'
                    '<td style="padding:3px 8px 3px 24px; color:#555; border:1px solid #ddd;">&nbsp;&nbsp;{}</td>'
                    '<td style="padding:3px 8px; color:#555; border:1px solid #ddd;">{}</td>'
                    '<td style="padding:3px 8px; color:#333; border:1px solid #ddd;">{}</td>'
                    '<td style="padding:3px 8px; color:#333; border:1px solid #ddd;"></td>'
                    '<td style="padding:3px 8px; color:#555; border:1px solid #ddd; font-size:11px;">{}</td>'
                    '</tr>'.format(sub.sub_number, sub.sub_name[:40], sub_gen, sub_provider)
                )
        table = (
            '<table style="border-collapse:collapse; width:100%; font-size:12px; background:#fff;">'
            '<thead><tr style="background:#417690; color:#fff;">'
            '<th style="padding:6px 8px; text-align:left; border:1px solid #3a6b82;">N</th>'
            '<th style="padding:6px 8px; text-align:left; border:1px solid #3a6b82;">Nome</th>'
            '<th style="padding:6px 8px; text-align:left; border:1px solid #3a6b82;">Agente Gerador</th>'
            '<th style="padding:6px 8px; text-align:left; border:1px solid #3a6b82;">Validador</th>'
            '<th style="padding:6px 8px; text-align:left; border:1px solid #3a6b82;">Provider/Modelo</th>'
            '</tr></thead><tbody>{}</tbody></table>'
        ).format(''.join(rows))
        return format_html(table)
    sections_agents_map.short_description = 'Mapa de Secoes x Agentes'

    @staticmethod
    def _agent_link(agent):
        if agent:
            url = reverse('admin:intelligent_assistant_sectionagentconfig_change', args=[agent.id])
            return '<a href="{}" style="color:#417690; text-decoration:underline;">{}</a>'.format(url, agent.name[:45])
        return '<span style="color:#999;">—</span>'

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="max-height: 60px; max-width: 150px;" />', obj.logo.url)
        return '-'
    logo_preview.short_description = 'Preview Logo'

    def cover_logo_preview(self, obj):
        if obj.cover_logo:
            return format_html('<img src="{}" style="max-height: 80px; max-width: 180px;" />', obj.cover_logo.url)
        return '-'
    cover_logo_preview.short_description = 'Preview Logo Capa'


class SectionPipelineStepInline(admin.TabularInline):
    model = SectionPipelineStep
    extra = 0
    fields = ['step_order', 'step_type', 'agent', 'output_variable', 'is_active']
    autocomplete_fields = ['agent']
    ordering = ['step_order']


class SectionImportConfigInline(admin.StackedInline):
    model = SectionImportConfig
    extra = 0
    fields = ['import_type', 'label', 'source_sections', 'is_active']
    filter_horizontal = ['source_sections']
    verbose_name = 'Configuração de Importação'
    verbose_name_plural = 'Configuração de Importação'

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # NOTA N+1: BlueprintSection.__str__ lê blueprint.name;
        # Blueprint.__str__ lê document_type.name. Manter select_related aqui
        # quando adicionar FKs novas ao __str__ desses modelos.
        if db_field.name == 'source_sections':
            from apps.intelligent_assistant.models import BlueprintSection
            kwargs['queryset'] = (
                BlueprintSection.objects
                .select_related('blueprint', 'blueprint__document_type')
                .order_by('blueprint__name', 'order', 'section_number')
            )
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class BlueprintSubSectionInline(admin.StackedInline):
    model = BlueprintSubSection
    fk_name = 'section'
    extra = 0
    fields = [
        'sub_number', 'sub_name', 'sub_key', 'order',
        'description', 'help_text', 'default_text',
        'generator_agent', 'section_fields',
        'source_section', 'source_sub_section',
        'is_required', 'is_active',
    ]
    autocomplete_fields = ['generator_agent']
    ordering = ['order', 'sub_number']
    verbose_name = 'Sub-seção (OU)'
    verbose_name_plural = 'Sub-seções (OU)'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # NOTA N+1: preservar select_related se adicionar FKs novas ao __str__
        # de BlueprintSection / BlueprintSubSection / DocumentBlueprint.
        if db_field.name == 'source_section':
            from apps.intelligent_assistant.models import BlueprintSection
            kwargs['queryset'] = BlueprintSection.objects.select_related(
                'blueprint', 'blueprint__document_type'
            )
        elif db_field.name == 'source_sub_section':
            from apps.intelligent_assistant.models import BlueprintSubSection
            kwargs['queryset'] = BlueprintSubSection.objects.select_related(
                'section', 'section__blueprint', 'section__blueprint__document_type'
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# BlueprintSection — visível no menu admin para gestão completa de seções
class BlueprintListFilter(admin.SimpleListFilter):
    """
    Filtro lateral por Blueprint usando select_related para carregar
    o document_type junto — evita N+1 no __str__ do DocumentBlueprint.
    """
    title = 'blueprint'
    parameter_name = 'blueprint__id__exact'

    def lookups(self, request, model_admin):
        from apps.intelligent_assistant.models import DocumentBlueprint
        bps = DocumentBlueprint.objects.select_related('document_type').order_by('name')
        return [(str(bp.id), str(bp)) for bp in bps]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(blueprint__id=self.value())
        return queryset


@admin.register(BlueprintSection)
class BlueprintSectionAdmin(admin.ModelAdmin):
    """Admin para gestão de seções do blueprint (sub-seções, pipeline, agentes)."""
    list_display = ['section_number', 'section_name', 'blueprint', 'generator_agent', 'validator_agent', 'sub_sections_count', 'is_required', 'is_active', 'order']
    list_filter = [BlueprintListFilter, 'is_active', 'is_required', 'allow_skip']
    search_fields = ['section_name', 'section_key', 'blueprint__name']
    list_per_page = 30
    ordering = ['blueprint', 'order', 'section_number']
    list_select_related = ('blueprint', 'blueprint__document_type', 'generator_agent', 'validator_agent')
    inlines = [SectionImportConfigInline, BlueprintSubSectionInline, SectionPipelineStepInline]
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['blueprint', 'generator_agent', 'validator_agent']
    filter_horizontal = ['depends_on']

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # NOTA N+1: depends_on renderiza str(section) que acessa blueprint
        # e document_type. Preservar select_related aqui.
        if db_field.name == 'depends_on':
            from apps.intelligent_assistant.models import BlueprintSection
            kwargs['queryset'] = (
                BlueprintSection.objects
                .select_related('blueprint', 'blueprint__document_type')
                .order_by('blueprint__name', 'order', 'section_number')
            )
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    fieldsets = (
        ('Blueprint', {
            'fields': ('id', 'blueprint')
        }),
        ('Identificacao da Secao', {
            'fields': ('section_number', 'section_name', 'section_key', 'order')
        }),
        ('Descricao e Instrucoes', {
            'fields': ('description', 'instructions', 'legal_reference'),
            'classes': ('wide',)
        }),
        ('Agentes', {
            'fields': ('generator_agent', 'validator_agent'),
        }),
        ('Dependencias entre Secoes', {
            'fields': ('depends_on',),
            'description': 'Selecione as seções que devem ser geradas ANTES desta. '
                           'O agente receberá o conteúdo dessas seções via {{previous_sections}}.',
        }),
        ('Configuracoes de Geracao', {
            'fields': ('is_required', 'allow_skip', 'max_generation_attempts')
        }),
        ('Campos Estruturados', {
            'fields': ('section_fields',),
            'classes': ('collapse',),
        }),
        ('Flags', {
            'fields': ('is_active',)
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def sub_sections_count(self, obj):
        count = obj.sub_sections.count()
        if count > 0:
            return format_html('<span style="color: #007bff; font-weight: bold;">{}</span>', count)
        return format_html('<span style="color: #999;">0</span>')
    sub_sections_count.short_description = 'Sub-seções'

    def get_search_results(self, request, queryset, search_term):
        """Permite autocomplete em outros admins."""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        return queryset, use_distinct


# BlueprintSubSection — visível no menu admin para gestão de sub-seções e agentes
@admin.register(BlueprintSubSection)
class BlueprintSubSectionAdmin(admin.ModelAdmin):
    """Admin para gestão de sub-seções do blueprint (agentes, campos estruturados)."""
    list_display = ['sub_number', 'sub_name', 'section', 'generator_agent', 'is_required', 'is_active', 'order']
    list_filter = ['section__blueprint', 'is_active', 'is_required']
    search_fields = ['sub_name', 'sub_key', 'section__section_name', 'section__blueprint__name']
    list_per_page = 30
    ordering = ['section__blueprint', 'section__order', 'order', 'sub_number']
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['section', 'generator_agent']

    fieldsets = (
        ('Seção pai', {
            'fields': ('id', 'section')
        }),
        ('Identificação da Sub-seção', {
            'fields': ('sub_number', 'sub_name', 'sub_key', 'order')
        }),
        ('Descrição', {
            'fields': ('description', 'help_text', 'default_text'),
            'classes': ('wide',)
        }),
        ('Agente Gerador', {
            'fields': ('generator_agent',),
        }),
        ('Campos Estruturados', {
            'fields': ('section_fields',),
            'classes': ('collapse',),
        }),
        ('Flags', {
            'fields': ('is_required', 'is_active')
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_search_results(self, request, queryset, search_term):
        """Permite autocomplete em outros admins."""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        return queryset, use_distinct


# SectionImportConfig — gestão do mapeamento de importação entre blueprints
@admin.register(SectionImportConfig)
class SectionImportConfigAdmin(admin.ModelAdmin):
    """Admin para gestão do mapeamento de importação entre seções de blueprints."""
    list_display = ['target_section_number', 'target_section_name', 'target_blueprint', 'import_type', 'label', 'source_list', 'is_active']
    list_filter = ['import_type', 'is_active', 'target_section__blueprint']
    search_fields = ['label', 'target_section__section_name', 'target_section__blueprint__name']
    list_per_page = 50
    ordering = ['target_section__blueprint', 'target_section__section_number']
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['target_section']
    filter_horizontal = ['source_sections']

    fieldsets = (
        ('Seção Alvo', {
            'fields': ('id', 'target_section'),
        }),
        ('Importação', {
            'fields': ('import_type', 'label', 'source_sections'),
        }),
        ('Flags', {
            'fields': ('is_active',),
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def target_section_number(self, obj):
        return obj.target_section.section_number
    target_section_number.short_description = '§'
    target_section_number.admin_order_field = 'target_section__section_number'

    def target_section_name(self, obj):
        return obj.target_section.section_name
    target_section_name.short_description = 'Seção'

    def target_blueprint(self, obj):
        return obj.target_section.blueprint.name
    target_blueprint.short_description = 'Blueprint'

    def source_list(self, obj):
        nums = obj.source_section_numbers
        if not nums:
            return format_html('<span style="color: #999;">—</span>')
        return ', '.join(f'§{n}' for n in nums)
    source_list.short_description = 'Fontes'


# AgentKnowledgeBaseLink — acessível como inline em KnowledgeBase e SectionAgentConfig
# SectionPipelineStep — acessível como inline em BlueprintSection (via Blueprint)


@admin.action(description='Marcar selecionadas como "cancelled"')
def cancel_selected_sessions(modeladmin, request, queryset):
    updated = queryset.filter(status='generating').update(status='cancelled')
    modeladmin.message_user(request, f'{updated} sessão(ões) marcadas como canceladas.')


@admin.register(GenerationSession)
class GenerationSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'blueprint', 'status', 'status_badge', 'progress_bar', 'created_at']
    list_filter = ['status', 'blueprint', 'created_at']
    search_fields = ['id', 'user__username', 'user__email', 'objective', 'blueprint__name']
    list_per_page = 30
    readonly_fields = ['id', 'progress_percentage', 'completed_sections_count', 'total_selected_sections', 'created_at', 'updated_at']
    autocomplete_fields = ['user', 'blueprint', 'intelligent_session']
    filter_horizontal = ['selected_sections']
    inlines = [SectionGenerationInline]
    date_hierarchy = 'created_at'
    actions = [cancel_selected_sessions]

    fieldsets = (
        ('Identificacao', {
            'fields': ('id', 'user', 'blueprint', 'intelligent_session')
        }),
        ('Dados da Sessao', {
            'fields': ('objective', 'status', 'error_message')
        }),
        ('Secoes Selecionadas', {
            'fields': ('selected_sections',),
            'classes': ('wide',)
        }),
        ('Configuracoes', {
            'fields': ('config',),
            'classes': ('collapse',)
        }),
        ('Progresso', {
            'fields': ('progress_percentage', 'completed_sections_count', 'total_selected_sections'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'initialized': '#6c757d',
            'sections_selected': '#17a2b8',
            'generating': '#007bff',
            'validating': '#6f42c1',
            'completed': '#28a745',
            'failed': '#dc3545',
            'cancelled': '#ffc107',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def progress_bar(self, obj):
        percentage = obj.progress_percentage
        color = '#28a745' if percentage == 100 else '#007bff'
        return format_html(
            '<div style="width: 100px; background-color: #e9ecef; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; text-align: center; color: white; font-size: 12px; line-height: 20px;">'
            '{}%</div></div>',
            percentage, color, percentage
        )
    progress_bar.short_description = 'Progresso'


@admin.register(SectionGeneration)
class SectionGenerationAdmin(admin.ModelAdmin):
    list_display = ['section', 'session_link', 'status', 'status_badge', 'is_valid', 'validation_score', 'generation_attempts', 'tokens_used', 'created_at']
    list_display_links = ['section']
    list_filter = ['status', 'is_valid', 'created_at']
    search_fields = ['session__id', 'section__section_name', 'content']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['session', 'section']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Relacionamentos', {
            'fields': ('id', 'session', 'section')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Conteudo Gerado', {
            'fields': ('content',),
            'classes': ('wide',)
        }),
        ('Validacao', {
            'fields': ('is_valid', 'validation_score', 'validation_errors', 'validation_warnings', 'validation_feedback')
        }),
        ('Metricas', {
            'fields': ('generation_attempts', 'tokens_used', 'generation_time_ms', 'validation_time_ms'),
            'classes': ('collapse',)
        }),
        ('Debug', {
            'fields': ('agent_reasoning', 'rag_context_used', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def session_link(self, obj):
        url = reverse('admin:intelligent_assistant_generationsession_change', args=[obj.session.id])
        return format_html('<a href="{}">{}</a>', url, str(obj.session.id)[:8])
    session_link.short_description = 'Sessao'

    def status_badge(self, obj):
        colors = {
            'pending': '#6c757d',
            'generating': '#007bff',
            'generated': '#17a2b8',
            'validating': '#6f42c1',
            'validated': '#28a745',
            'failed': '#dc3545',
            'skipped': '#ffc107',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


# =============================================================================
# SECTION FEEDBACK - AUTO-APRENDIZAGEM
# =============================================================================


@admin.register(SectionFeedback)
class SectionFeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'section_name', 'user', 'rating_stars', 'ai_score',
        'is_improvement', 'is_approved', 'embedding_created', 'created_at'
    ]
    list_filter = ['user_rating', 'is_improvement', 'is_approved', 'embedding_created', 'created_at']
    search_fields = ['section_name', 'user__email', 'edit_reason']
    readonly_fields = ['id', 'is_improvement', 'embedding_created', 'created_at', 'updated_at']
    raw_id_fields = ['session', 'user']
    actions = ['approve_and_create_embeddings']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Identificacao', {
            'fields': ('id', 'session', 'user', 'section_number', 'section_name')
        }),
        ('Conteudo', {
            'fields': ('original_content', 'edited_content', 'edit_reason'),
            'classes': ('wide',)
        }),
        ('Avaliacao', {
            'fields': ('user_rating', 'ai_score')
        }),
        ('Status', {
            'fields': ('is_improvement', 'is_approved', 'embedding_created')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def rating_stars(self, obj):
        filled = '★' * obj.user_rating
        empty = '☆' * (5 - obj.user_rating)
        color = '#28a745' if obj.user_rating >= 4 else '#ffc107' if obj.user_rating >= 3 else '#dc3545'
        return format_html(
            '<span style="color: {}; font-size: 14px;">{}{}</span>',
            color, filled, empty
        )
    rating_stars.short_description = 'Rating'

    def approve_and_create_embeddings(self, request, queryset):
        """Aprova feedbacks selecionados e cria embeddings na KB de melhorias."""
        from .services.pgvector_service import PgVectorService

        pgvector_service = PgVectorService()
        approved_count = 0
        error_count = 0

        for feedback in queryset.filter(is_improvement=True, user_rating__gte=4):
            try:
                feedback.is_approved = True
                if not feedback.embedding_created:
                    pgvector_service.add_section_improvement(
                        section_name=feedback.section_name,
                        improvement_text=feedback.edited_content,
                        original_text=feedback.original_content,
                        metadata={
                            'user_id': str(feedback.user_id),
                            'session_id': str(feedback.session_id),
                            'ai_score': feedback.ai_score,
                            'user_rating': feedback.user_rating,
                            'approved_by': str(request.user.id),
                        }
                    )
                    feedback.embedding_created = True
                feedback.save()
                approved_count += 1
            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f'Erro ao processar feedback {feedback.id}: {e}',
                    level='error'
                )

        if approved_count:
            self.message_user(
                request,
                f'{approved_count} feedback(s) aprovado(s) e embedding(s) criado(s).'
            )
        if error_count:
            self.message_user(
                request,
                f'{error_count} erro(s) ao processar feedbacks.',
                level='warning'
            )
    approve_and_create_embeddings.short_description = 'Aprovar e criar embeddings (rating >= 4)'


# =============================================================================
# LLM AUDIT LOG
# =============================================================================


@admin.register(LLMAuditLog)
class LLMAuditLogAdmin(admin.ModelAdmin):
    """Admin para auditoria de chamadas LLM — somente leitura."""

    list_display = [
        'created_at',
        'call_type_badge',
        'user_display',
        'blueprint_display',
        'section_display',
        'provider_model',
        'input_tokens',
        'output_tokens',
        'total_tokens',
        'duration_display',
        'cost_display',
    ]

    list_filter = [
        'call_type',
        'provider',
        'model',
        ('user', admin.RelatedOnlyFieldListFilter),
        ('blueprint', admin.RelatedOnlyFieldListFilter),
        ('created_at', admin.DateFieldListFilter),
    ]

    search_fields = [
        'user__username',
        'user__email',
        'blueprint__name',
        'section_name',
        'model',
    ]

    date_hierarchy = 'created_at'

    readonly_fields = [
        'id', 'user', 'session', 'blueprint',
        'section_number', 'section_name',
        'call_type', 'attempt_number',
        'provider', 'model',
        'input_tokens', 'output_tokens', 'total_tokens',
        'duration_ms', 'estimated_cost_usd',
        'created_at',
    ]

    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def call_type_badge(self, obj):
        colors = {
            'generate': '#3b82f6',
            'validate': '#f59e0b',
            'regenerate': '#8b5cf6',
            'other': '#6b7280',
        }
        color = colors.get(obj.call_type, '#6b7280')
        return format_html(
            '<span style="background:{}; color:#fff; padding:2px 8px; '
            'border-radius:4px; font-size:11px; font-weight:600;">{}</span>',
            color, obj.get_call_type_display()
        )
    call_type_badge.short_description = 'Tipo'
    call_type_badge.admin_order_field = 'call_type'

    def user_display(self, obj):
        return obj.user.username if obj.user else '—'
    user_display.short_description = 'Usuário'
    user_display.admin_order_field = 'user__username'

    def blueprint_display(self, obj):
        return obj.blueprint.name if obj.blueprint else '—'
    blueprint_display.short_description = 'Blueprint'

    def section_display(self, obj):
        if obj.section_number:
            return f"S{obj.section_number}: {obj.section_name or ''}"
        return '—'
    section_display.short_description = 'Seção'

    def provider_model(self, obj):
        return f"{obj.provider}/{obj.model}"
    provider_model.short_description = 'Provider/Modelo'

    def duration_display(self, obj):
        if obj.duration_ms:
            if obj.duration_ms >= 1000:
                return f"{obj.duration_ms / 1000:.1f}s"
            return f"{obj.duration_ms}ms"
        return '—'
    duration_display.short_description = 'Duração'
    duration_display.admin_order_field = 'duration_ms'

    def cost_display(self, obj):
        if obj.estimated_cost_usd:
            return f"${obj.estimated_cost_usd:.4f}"
        return '—'
    cost_display.short_description = 'Custo (USD)'
    cost_display.admin_order_field = 'estimated_cost_usd'


# =============================================================================
# SECTION GENERATION LOG — RASTREABILIDADE
# =============================================================================


@admin.register(SectionGenerationLog)
class SectionGenerationLogAdmin(admin.ModelAdmin):
    """Admin para rastreabilidade de geração de seções jurídicas — somente leitura."""

    list_display = [
        'created_at',
        'session',
        'section',
        'agent',
        'provider',
        'model_name',
        'input_tokens',
        'output_tokens',
        'generation_time_ms',
        'has_unresolved_placeholders',
        'unresolved_count',
    ]

    list_filter = [
        'provider',
        'has_unresolved_placeholders',
        ('created_at', admin.DateFieldListFilter),
        ('session', admin.RelatedOnlyFieldListFilter),
    ]

    search_fields = [
        'session__id',
        'section__section_name',
        'agent__name',
        'provider',
        'model_name',
        'prompt_hash',
        'output_hash',
    ]

    date_hierarchy = 'created_at'

    readonly_fields = [
        'id',
        'session',
        'section',
        'agent',
        'provider',
        'model_name',
        'prompt_hash',
        'input_tokens',
        'output_tokens',
        'generation_time_ms',
        'output_hash',
        'has_unresolved_placeholders',
        'unresolved_count',
        'placeholder_types',
        'created_at',
    ]

    list_per_page = 50
    list_select_related = ('session', 'section', 'agent')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
