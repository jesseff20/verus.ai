"""
Admin para templates de formulários e assistentes
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import FormTemplate, FormAssistant


@admin.register(FormTemplate)
class FormTemplateAdmin(admin.ModelAdmin):
    """Admin para FormTemplate"""
    list_display = ['name', 'version', 'field_count_display', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'field_count']
    ordering = ['-created_at']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'name', 'description')
        }),
        ('Configuração de Campos', {
            'fields': ('fields',),
            'description': 'JSON com definição dos campos do formulário'
        }),
        ('Versionamento', {
            'fields': ('version', 'is_active')
        }),
        ('Auditoria', {
            'fields': ('created_by', 'created_at', 'updated_at', 'field_count'),
            'classes': ('collapse',)
        }),
    )

    def field_count_display(self, obj):
        """Exibe quantidade de campos"""
        return format_html(
            '<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            obj.field_count
        )
    field_count_display.short_description = 'Campos'

    def save_model(self, request, obj, form, change):
        """Define created_by automaticamente"""
        if not change:  # Novo objeto
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    actions = ['duplicate_template', 'activate_templates', 'deactivate_templates']

    def duplicate_template(self, request, queryset):
        """Duplica templates selecionados"""
        count = 0
        for template in queryset:
            template.duplicate(request.user)
            count += 1
        self.message_user(request, f'{count} template(s) duplicado(s) com sucesso.')
    duplicate_template.short_description = 'Duplicar templates selecionados'

    def activate_templates(self, request, queryset):
        """Ativa templates"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} template(s) ativado(s).')
    activate_templates.short_description = 'Ativar templates'

    def deactivate_templates(self, request, queryset):
        """Desativa templates"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} template(s) desativado(s).')
    deactivate_templates.short_description = 'Desativar templates'


@admin.register(FormAssistant)
class FormAssistantAdmin(admin.ModelAdmin):
    """Admin para FormAssistant"""
    list_display = ['name', 'assistant_type', 'llm_provider_badge', 'model_name',
                    'is_active', 'is_default', 'display_order', 'created_at']
    list_filter = ['assistant_type', 'llm_provider', 'is_active', 'is_default', 'use_rag', 'created_at']
    search_fields = ['name', 'description', 'assistant_type']
    readonly_fields = ['id', 'created_at', 'updated_at', 'variable_count', 'extract_variables']
    ordering = ['display_order', 'assistant_type']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'name', 'description', 'assistant_type')
        }),
        ('Configuração de Prompts', {
            'fields': ('system_prompt', 'user_prompt_template'),
            'description': 'System prompt e template do user prompt com {{variáveis}}'
        }),
        ('Configuração LLM', {
            'fields': ('llm_provider', 'model_name', 'temperature', 'max_tokens'),
            'classes': ('wide',)
        }),
        ('Contexto RAG', {
            'fields': ('use_rag', 'rag_query_template'),
            'classes': ('collapse',)
        }),
        ('Interface', {
            'fields': ('icon', 'color', 'display_order'),
            'classes': ('collapse',)
        }),
        ('Flags', {
            'fields': ('is_active', 'is_default')
        }),
        ('Auditoria', {
            'fields': ('created_by', 'created_at', 'updated_at', 'variable_count', 'extract_variables'),
            'classes': ('collapse',)
        }),
    )

    def llm_provider_badge(self, obj):
        """Badge colorido para provider"""
        colors = {
            'openai': '#10a37f',
            'watsonx': '#0f62fe'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.llm_provider, '#6c757d'),
            obj.get_llm_provider_display()
        )
    llm_provider_badge.short_description = 'Provider'

    def save_model(self, request, obj, form, change):
        """Define created_by automaticamente"""
        if not change:
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
