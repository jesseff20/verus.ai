from django.contrib import admin
from django.utils.html import format_html

from .models import AuditLog, DocumentType, ProcessType, LLMProvider, LLMModel, AIAnalysisConfig, TokenUsageLog


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = [
        'code',
        'short_name',
        'name',
        'category_badge',
        'icon',
        'display_order',
        'is_active',
    ]
    list_filter = [
        'category',
        'is_active',
    ]
    search_fields = [
        'code',
        'name',
        'short_name',
        'description',
    ]
    list_editable = ['display_order', 'is_active']
    ordering = ['category', 'display_order', 'name']

    fieldsets = (
        ('Identificação', {
            'fields': ('code', 'name', 'short_name', 'description')
        }),
        ('Classificação', {
            'fields': ('category', 'legal_basis')
        }),
        ('Visual', {
            'fields': ('icon', 'color', 'display_order')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

    def category_badge(self, obj):
        colors = {
            'fase_preparatoria': '#007bff',
            'fase_externa': '#28a745',
            'impugnacoes_recursos': '#ffc107',
            'pareceres': '#17a2b8',
            'pos_contratacao': '#6f42c1',
            'outros': '#6c757d',
        }
        cat_code = obj.category.code if obj.category_id else None
        color = colors.get(cat_code, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.category.name if obj.category_id else '-'
        )
    category_badge.short_description = 'Categoria'
    category_badge.admin_order_field = 'category__display_order'


@admin.register(ProcessType)
class ProcessTypeAdmin(admin.ModelAdmin):
    list_display = [
        'code',
        'short_name',
        'name',
        'category_badge',
        'legal_basis_short',
        'display_order',
        'is_active',
    ]
    list_filter = [
        'category',
        'is_active',
    ]
    search_fields = [
        'code',
        'name',
        'short_name',
        'description',
        'legal_basis',
    ]
    list_editable = ['display_order', 'is_active']
    ordering = ['category', 'display_order', 'name']

    fieldsets = (
        ('Identificação', {
            'fields': ('code', 'name', 'short_name', 'description')
        }),
        ('Classificação', {
            'fields': ('category', 'legal_basis')
        }),
        ('Visual', {
            'fields': ('icon', 'color', 'display_order')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

    def category_badge(self, obj):
        colors = {
            'pregao': '#007bff',
            'concorrencia': '#28a745',
            'dispensa': '#ffc107',
            'inexigibilidade': '#17a2b8',
            'chamamento': '#6f42c1',
            'concurso': '#fd7e14',
            'srp': '#20c997',
            'outros': '#6c757d',
        }
        color = colors.get(obj.category, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_category_display()
        )
    category_badge.short_description = 'Categoria'
    category_badge.admin_order_field = 'category'

    def legal_basis_short(self, obj):
        if obj.legal_basis and len(obj.legal_basis) > 30:
            return obj.legal_basis[:30] + '...'
        return obj.legal_basis or '-'
    legal_basis_short.short_description = 'Base Legal'


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'created_at',
        'action_badge',
        'severity_badge',
        'user_email',
        'entity_type',
        'entity_name_short',
        'description_short',
        'ip_address',
    ]
    list_filter = [
        'action',
        'severity',
        'entity_type',
        'created_at',
    ]
    search_fields = [
        'user_email',
        'entity_type',
        'entity_id',
        'entity_name',
        'description',
        'ip_address',
    ]
    readonly_fields = [
        'id',
        'user',
        'user_email',
        'user_role',
        'action',
        'severity',
        'entity_type',
        'entity_id',
        'entity_name',
        'description',
        'old_values',
        'new_values',
        'metadata',
        'ip_address',
        'user_agent',
        'request_id',
        'created_at',
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        ('Informacoes Basicas', {
            'fields': ('id', 'created_at', 'action', 'severity', 'description')
        }),
        ('Usuario', {
            'fields': ('user', 'user_email', 'user_role')
        }),
        ('Entidade Afetada', {
            'fields': ('entity_type', 'entity_id', 'entity_name')
        }),
        ('Valores', {
            'fields': ('old_values', 'new_values', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Contexto Tecnico', {
            'fields': ('ip_address', 'user_agent', 'request_id'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def action_badge(self, obj):
        colors = {
            'create': '#28a745',
            'update': '#17a2b8',
            'delete': '#dc3545',
            'login': '#6c757d',
            'logout': '#6c757d',
            'login_failed': '#ffc107',
            'generate': '#007bff',
            'download': '#6610f2',
            'submit': '#fd7e14',
            'approve': '#28a745',
            'reject': '#dc3545',
            'publish': '#20c997',
        }
        color = colors.get(obj.action, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_action_display()
        )
    action_badge.short_description = 'Acao'
    action_badge.admin_order_field = 'action'

    def severity_badge(self, obj):
        colors = {
            'info': '#17a2b8',
            'warning': '#ffc107',
            'error': '#dc3545',
            'critical': '#721c24',
        }
        text_colors = {
            'info': 'white',
            'warning': 'black',
            'error': 'white',
            'critical': 'white',
        }
        color = colors.get(obj.severity, '#6c757d')
        text_color = text_colors.get(obj.severity, 'white')
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            text_color,
            obj.get_severity_display()
        )
    severity_badge.short_description = 'Severidade'
    severity_badge.admin_order_field = 'severity'

    def entity_name_short(self, obj):
        if len(obj.entity_name) > 30:
            return obj.entity_name[:30] + '...'
        return obj.entity_name
    entity_name_short.short_description = 'Entidade'

    def description_short(self, obj):
        if len(obj.description) > 50:
            return obj.description[:50] + '...'
        return obj.description
    description_short.short_description = 'Descricao'


class LLMModelInline(admin.TabularInline):
    model = LLMModel
    extra = 1
    fields = ['model_id', 'display_name', 'max_tokens_limit', 'default_temperature', 'display_order', 'is_active']
    ordering = ['display_order', 'display_name']


@admin.register(LLMProvider)
class LLMProviderAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'code',
        'api_key_status',
        'models_count',
        'display_order',
        'is_active',
    ]
    list_filter = ['is_active']
    search_fields = ['code', 'name']
    list_editable = ['display_order', 'is_active']
    ordering = ['display_order', 'name']
    inlines = [LLMModelInline]

    fieldsets = (
        ('Identificação', {
            'fields': ('code', 'name', 'description')
        }),
        ('Credenciais', {
            'fields': ('api_key', 'api_url', 'extra_config'),
            'description': 'A API Key é armazenada no banco. Para watsonx, '
                           'preencha extra_config com {"project_id": "seu-id"}.'
        }),
        ('Visual', {
            'fields': ('icon', 'color', 'display_order')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

    def api_key_status(self, obj):
        if obj.has_api_key:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">Configurada ({})</span>',
                obj.masked_api_key
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">Não configurada</span>'
        )
    api_key_status.short_description = 'API Key'

    def models_count(self, obj):
        total = obj.models.count()
        active = obj.models.filter(is_active=True).count()
        return f"{active}/{total} ativos"
    models_count.short_description = 'Modelos'


@admin.register(LLMModel)
class LLMModelAdmin(admin.ModelAdmin):
    list_display = [
        'display_name',
        'model_id',
        'provider',
        'max_tokens_limit',
        'display_order',
        'is_active',
    ]
    list_filter = ['provider', 'is_active']
    search_fields = ['model_id', 'display_name']
    list_editable = ['display_order', 'is_active']
    ordering = ['provider', 'display_order', 'display_name']


@admin.register(TokenUsageLog)
class TokenUsageLogAdmin(admin.ModelAdmin):
    list_display = [
        'created_at',
        'user',
        'model_provider',
        'model_name',
        'usage_type',
        'total_tokens',
        'cost_estimate',
    ]
    list_filter = ['model_provider', 'usage_type', 'created_at']
    search_fields = ['description', 'model_name', 'user__email']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at']

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AIAnalysisConfig)
class AIAnalysisConfigAdmin(admin.ModelAdmin):
    """Admin para configurações de análise IA."""
    list_display = ['display_name', 'name', 'llm_provider', 'model_name', 'temperature', 'is_active']
    list_filter = ['llm_provider', 'is_active']
    search_fields = ['name', 'display_name']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Identificação', {
            'fields': ('id', 'name', 'display_name', 'description'),
        }),
        ('Prompt', {
            'fields': ('system_prompt', 'user_prompt_template', 'questions'),
            'description': 'Placeholders disponíveis no user_prompt_template: {{text}}, {{objeto}}, {{questions}}',
        }),
        ('LLM', {
            'fields': ('llm_provider', 'model_name', 'temperature', 'max_tokens'),
        }),
        ('Limites', {
            'fields': ('max_input_chars',),
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at'),
        }),
    )
