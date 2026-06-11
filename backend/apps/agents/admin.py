"""
Admin para Prompts de Agentes e Sistema de Assistente
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg
from .models import AgentPrompt
from .models_assistant import (
    AssistantConversation,
    AssistantMessage,
    AssistantFeedback,
    AssistantAnalytics,
    AssistantKnowledgeQuery,
)


class AgentPromptAdmin(admin.ModelAdmin):
    """Admin para Agentes de Chat"""
    list_display = [
        'name', 'agent_type', 'llm_provider',
        'model_name', 'variable_count_display', 'use_rag',
        'is_default_display', 'is_active', 'created_at'
    ]
    list_filter = ['agent_type', 'llm_provider', 'use_rag', 'is_active', 'is_default', 'created_at']
    search_fields = ['name', 'description', 'agent_type']
    readonly_fields = ['id', 'variable_count', 'variables_preview', 'created_at', 'updated_at']
    ordering = ['agent_type', 'name']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'name', 'description', 'agent_type')
        }),
        ('Prompts', {
            'fields': ('system_prompt', 'user_prompt_template', 'variables_preview')
        }),
        ('Configurações LLM', {
            'fields': ('llm_provider', 'model_name', 'temperature', 'max_tokens')
        }),
        ('RAG (Busca na Knowledge Base)', {
            'fields': ('use_rag', 'rag_query_template'),
            'classes': ('collapse',)
        }),
        ('Flags', {
            'fields': ('is_active', 'is_default')
        }),
        ('Auditoria', {
            'fields': ('created_by', 'created_at', 'updated_at', 'variable_count'),
            'classes': ('collapse',)
        }),
    )

    def variable_count_display(self, obj):
        """Exibe quantidade de variáveis"""
        count = obj.variable_count
        if count > 0:
            return format_html(
                '<span style="background-color: #17a2b8; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
                count
            )
        return '-'
    variable_count_display.short_description = 'Variáveis'

    def is_default_display(self, obj):
        """Exibe se é padrão"""
        if obj.is_default:
            return format_html(
                '<span style="background-color: #ffc107; color: #000; padding: 3px 8px; border-radius: 3px; font-weight: bold;">PADRÃO</span>'
            )
        return '-'
    is_default_display.short_description = 'Padrão'

    def variables_preview(self, obj):
        """Mostra preview das variáveis extraídas"""
        variables = obj.extract_variables()
        if variables:
            return format_html(
                '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;"><code>{}</code></div>',
                ', '.join([f'{{{{{v}}}}}' for v in variables])
            )
        return 'Nenhuma variável encontrada'
    variables_preview.short_description = 'Variáveis Extraídas'

    def save_model(self, request, obj, form, change):
        """Define created_by automaticamente"""
        if not change and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    actions = ['activate_prompts', 'deactivate_prompts']

    def activate_prompts(self, request, queryset):
        """Ativa prompts"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} prompt(s) ativado(s).')
    activate_prompts.short_description = 'Ativar prompts'

    def deactivate_prompts(self, request, queryset):
        """Desativa prompts"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} prompt(s) desativado(s).')
    deactivate_prompts.short_description = 'Desativar prompts'


# ===== ASSISTENTES DE CHAT =====

# Proxy model para permitir registro separado no admin
class ChatAssistantProxy(AgentPrompt):
    """Proxy model para permitir registro separado de Chat Assistants no admin"""
    class Meta:
        proxy = True
        verbose_name = 'Assistente de Chat'
        verbose_name_plural = 'Assistentes de Chat'


class ChatAssistantAdmin(admin.ModelAdmin):
    """Admin para Assistentes de Chat (chat_assistant)"""
    model = ChatAssistantProxy

    list_display = [
        'name', 'llm_provider', 'model_name', 'kb_count_display',
        'is_default_display', 'is_active', 'created_at'
    ]
    list_filter = ['llm_provider', 'is_active', 'is_default', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    filter_horizontal = ['knowledge_bases']  # Widget para M2M
    ordering = ['-is_default', 'name']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'name', 'description')
        }),
        ('Prompts', {
            'fields': ('system_prompt', 'user_prompt_template'),
            'description': 'System prompt define o comportamento do assistente. User prompt template pode usar {{message}} e {{kb_context}}'
        }),
        ('Configurações LLM', {
            'fields': ('llm_provider', 'model_name', 'temperature', 'max_tokens')
        }),
        ('Bases de Conhecimento', {
            'fields': ('knowledge_bases',),
            'description': 'Selecione quais documentos da KB este assistente pode acessar'
        }),
        ('Flags', {
            'fields': ('is_active', 'is_default')
        }),
        ('Auditoria', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Filtrar apenas assistentes de chat"""
        qs = super().get_queryset(request)
        return qs.filter(agent_type='chat_assistant')

    def kb_count_display(self, obj):
        """Exibe quantidade de KBs vinculadas"""
        count = obj.knowledge_bases.count()
        if count > 0:
            return format_html(
                '<span style="background-color: #17a2b8; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
                count
            )
        return format_html('<span style="color: #999;">Nenhuma</span>')
    kb_count_display.short_description = 'KBs'

    def is_default_display(self, obj):
        """Exibe se é padrão"""
        if obj.is_default:
            return format_html(
                '<span style="background-color: #ffc107; color: #000; padding: 3px 8px; border-radius: 3px; font-weight: bold;">PADRÃO</span>'
            )
        return '-'
    is_default_display.short_description = 'Padrão'

    def save_model(self, request, obj, form, change):
        """Define agent_type e created_by automaticamente"""
        obj.agent_type = 'chat_assistant'  # Forçar tipo
        if not change and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    actions = ['activate_assistants', 'deactivate_assistants']

    def activate_assistants(self, request, queryset):
        """Ativa assistentes"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} assistente(s) ativado(s).')
    activate_assistants.short_description = 'Ativar assistentes'

    def deactivate_assistants(self, request, queryset):
        """Desativa assistentes"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} assistente(s) desativado(s).')
    deactivate_assistants.short_description = 'Desativar assistentes'


# Registrar ambos os admins
admin.site.register(AgentPrompt, AgentPromptAdmin)
admin.site.register(ChatAssistantProxy, ChatAssistantAdmin)


# ===== ASSISTENTE - CONVERSAS =====

class AssistantMessageInline(admin.TabularInline):
    """Inline para mensagens da conversa"""
    model = AssistantMessage
    extra = 0
    readonly_fields = ['role', 'content_preview', 'tokens_used', 'response_time_ms', 'created_at']
    fields = ['role', 'content_preview', 'tokens_used', 'response_time_ms', 'used_kb', 'created_at']
    can_delete = False

    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Conteúdo'


@admin.register(AssistantConversation)
class AssistantConversationAdmin(admin.ModelAdmin):
    """Admin para conversas do assistente"""
    list_display = [
        'id', 'user', 'document_type', 'total_messages',
        'started_at', 'satisfaction_display'
    ]
    list_filter = ['document_type', 'started_at']
    search_fields = ['user__username', 'session_id', 'document_id']
    readonly_fields = [
        'id', 'started_at', 'last_message_at',
        'total_messages', 'total_tokens_used', 'avg_response_time_ms'
    ]
    inlines = [AssistantMessageInline]
    ordering = ['-started_at']

    fieldsets = (
        ('Conversa', {
            'fields': ('id', 'user', 'session_id')
        }),
        ('Contexto', {
            'fields': ('document_type', 'document_id', 'current_field')
        }),
        ('Métricas', {
            'fields': (
                'total_messages', 'total_tokens_used',
                'avg_response_time_ms', 'user_satisfaction_score'
            )
        }),
        ('Datas', {
            'fields': ('started_at', 'last_message_at')
        }),
    )

    def satisfaction_display(self, obj):
        if obj.user_satisfaction_score is not None:
            score = obj.user_satisfaction_score * 100
            color = '#28a745' if score >= 70 else '#ffc107' if score >= 50 else '#dc3545'
            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}%</span>',
                color, int(score)
            )
        return '-'
    satisfaction_display.short_description = 'Satisfação'


@admin.register(AssistantMessage)
class AssistantMessageAdmin(admin.ModelAdmin):
    """Admin para mensagens individuais"""
    list_display = [
        'id', 'conversation', 'role', 'content_preview',
        'tokens_used', 'used_kb', 'created_at'
    ]
    list_filter = ['role', 'used_kb', 'llm_provider', 'created_at']
    search_fields = ['content', 'conversation__user__username']
    readonly_fields = [
        'id', 'conversation', 'role', 'content',
        'llm_provider', 'model_name', 'tokens_used',
        'response_time_ms', 'used_kb', 'kb_documents_used',
        'kb_relevance_scores', 'created_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        ('Mensagem', {
            'fields': ('id', 'conversation', 'role', 'content')
        }),
        ('LLM (quando role=assistant)', {
            'fields': ('llm_provider', 'model_name', 'tokens_used', 'response_time_ms'),
            'classes': ('collapse',)
        }),
        ('Base de Conhecimento', {
            'fields': ('used_kb', 'kb_documents_used', 'kb_relevance_scores'),
            'classes': ('collapse',)
        }),
        ('Data', {
            'fields': ('created_at',)
        }),
    )

    def content_preview(self, obj):
        preview = obj.content[:80] + '...' if len(obj.content) > 80 else obj.content
        return format_html('<div style="max-width: 400px;">{}</div>', preview)
    content_preview.short_description = 'Conteúdo'


# ===== RLHF - FEEDBACK =====

@admin.register(AssistantFeedback)
class AssistantFeedbackAdmin(admin.ModelAdmin):
    """Admin para feedbacks (RLHF)"""
    list_display = [
        'id', 'message_preview', 'user', 'feedback_display',
        'reason', 'processed', 'created_at'
    ]
    list_filter = ['feedback_type', 'reason', 'processed', 'created_at']
    search_fields = ['message__content', 'user__username', 'comment']
    readonly_fields = ['id', 'message', 'user', 'created_at', 'processed_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Feedback', {
            'fields': ('id', 'message', 'user', 'feedback_type')
        }),
        ('Detalhamento', {
            'fields': ('reason', 'comment', 'suggested_response')
        }),
        ('Processamento', {
            'fields': ('processed', 'processed_at'),
            'classes': ('collapse',)
        }),
        ('Data', {
            'fields': ('created_at',)
        }),
    )

    actions = ['mark_as_processed', 'export_for_training']

    def message_preview(self, obj):
        preview = obj.message.content[:60] + '...' if len(obj.message.content) > 60 else obj.message.content
        return format_html('<div style="max-width: 300px;">{}</div>', preview)
    message_preview.short_description = 'Mensagem'

    def feedback_display(self, obj):
        if obj.feedback_type == 'positive':
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 3px;">👍 Positivo</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 3px;">👎 Negativo</span>'
            )
    feedback_display.short_description = 'Tipo'

    def mark_as_processed(self, request, queryset):
        """Marca feedbacks como processados"""
        from django.utils import timezone
        updated = queryset.update(processed=True, processed_at=timezone.now())
        self.message_user(request, f'{updated} feedback(s) marcado(s) como processado(s).')
    mark_as_processed.short_description = 'Marcar como processado'

    def export_for_training(self, request, queryset):
        """Exporta feedbacks para dataset de treino"""
        # TODO: Implementar exportação para formato de treino (JSONL, CSV, etc)
        self.message_user(request, 'Exportação ainda não implementada.')
    export_for_training.short_description = 'Exportar para treino'


# ===== ANALYTICS =====

@admin.register(AssistantAnalytics)
class AssistantAnalyticsAdmin(admin.ModelAdmin):
    """Admin para analytics agregados"""
    list_display = [
        'date', 'total_conversations', 'total_messages',
        'unique_users', 'satisfaction_display', 'calculated_at'
    ]
    list_filter = ['date']
    search_fields = []
    readonly_fields = [
        'id', 'date', 'total_conversations', 'total_messages',
        'unique_users', 'avg_messages_per_conversation',
        'avg_response_time_ms', 'total_tokens_used', 'total_kb_queries',
        'total_feedbacks', 'positive_feedbacks', 'negative_feedbacks',
        'satisfaction_rate', 'incorrect_count', 'incomplete_count',
        'irrelevant_count', 'unclear_count', 'outdated_count',
        'calculated_at'
    ]
    ordering = ['-date']
    actions = ['recalculate_analytics']

    fieldsets = (
        ('Data', {
            'fields': ('id', 'date', 'calculated_at')
        }),
        ('Métricas de Uso', {
            'fields': (
                'total_conversations', 'total_messages', 'unique_users',
                'avg_messages_per_conversation'
            )
        }),
        ('Performance', {
            'fields': ('avg_response_time_ms', 'total_tokens_used', 'total_kb_queries')
        }),
        ('Feedback (RLHF)', {
            'fields': (
                'total_feedbacks', 'positive_feedbacks', 'negative_feedbacks',
                'satisfaction_rate'
            )
        }),
        ('Breakdown de Problemas', {
            'fields': (
                'incorrect_count', 'incomplete_count', 'irrelevant_count',
                'unclear_count', 'outdated_count'
            ),
            'classes': ('collapse',)
        }),
    )

    def satisfaction_display(self, obj):
        rate = obj.satisfaction_rate
        if rate is None:
            return format_html('<span style="color: #999;">N/A</span>')
        color = '#28a745' if rate >= 70 else '#ffc107' if rate >= 50 else '#dc3545'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}%</span>',
            color, round(rate, 1)
        )
    satisfaction_display.short_description = 'Taxa de Satisfação'

    def recalculate_analytics(self, request, queryset):
        """Recalcula analytics para as datas selecionadas"""
        from django.core.management import call_command

        dates_recalculated = []
        for analytics in queryset:
            date_str = analytics.date.strftime('%Y-%m-%d')
            call_command('calculate_assistant_analytics', date=date_str, force=True, verbosity=0)
            dates_recalculated.append(date_str)

        self.message_user(
            request,
            f'Analytics recalculados para {len(dates_recalculated)} data(s): {", ".join(dates_recalculated)}'
        )
    recalculate_analytics.short_description = 'Recalcular analytics selecionados'

    def changelist_view(self, request, extra_context=None):
        """Adiciona cards de resumo no topo da lista"""
        from django.db.models import Sum, Avg
        from datetime import timedelta
        from django.utils import timezone

        # Últimos 30 dias
        thirty_days_ago = timezone.localtime().date() - timedelta(days=30)
        recent_analytics = AssistantAnalytics.objects.filter(date__gte=thirty_days_ago)

        # Totais dos últimos 30 dias
        totals = recent_analytics.aggregate(
            total_conversations=Sum('total_conversations'),
            total_messages=Sum('total_messages'),
            total_feedbacks=Sum('total_feedbacks'),
            avg_satisfaction=Avg('satisfaction_rate'),
        )

        extra_context = extra_context or {}
        extra_context['summary_cards'] = {
            'total_conversations': totals['total_conversations'] or 0,
            'total_messages': totals['total_messages'] or 0,
            'total_feedbacks': totals['total_feedbacks'] or 0,
            'avg_satisfaction': round(totals['avg_satisfaction'] or 0, 1),
        }

        return super().changelist_view(request, extra_context=extra_context)

    def has_add_permission(self, request):
        """Analytics são calculados automaticamente"""
        return False


# ===== KNOWLEDGE BASE QUERIES =====

@admin.register(AssistantKnowledgeQuery)
class AssistantKnowledgeQueryAdmin(admin.ModelAdmin):
    """Admin para queries na KB"""
    list_display = [
        'id', 'query_preview', 'results_count',
        'query_time_ms', 'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['query_text', 'message__content']
    readonly_fields = [
        'id', 'message', 'query_text', 'query_embedding',
        'results_count', 'top_results', 'query_time_ms', 'created_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        ('Query', {
            'fields': ('id', 'message', 'query_text')
        }),
        ('Resultados', {
            'fields': ('results_count', 'top_results')
        }),
        ('Performance', {
            'fields': ('query_time_ms',)
        }),
        ('Técnico', {
            'fields': ('query_embedding',),
            'classes': ('collapse',)
        }),
        ('Data', {
            'fields': ('created_at',)
        }),
    )

    def query_preview(self, obj):
        preview = obj.query_text[:80] + '...' if len(obj.query_text) > 80 else obj.query_text
        return format_html('<div style="max-width: 400px;">{}</div>', preview)
    query_preview.short_description = 'Query'
