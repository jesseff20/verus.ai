from django import forms
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path
from django.utils.html import format_html

from apps.core.models import LLMProvider
from .models import CopilotConfig, UserKnowledgeEntry, UserKnowledgeSyncLog


class CopilotConfigForm(forms.ModelForm):
    """Form com select dinâmico de modelo filtrado por provider."""

    model = forms.ChoiceField(
        label='Modelo',
        help_text='Selecione o modelo do provider escolhido acima.',
    )

    class Meta:
        model_ = CopilotConfig
        model = CopilotConfig
        fields = '__all__'
        widgets = {
            'system_prompt': forms.Textarea(attrs={'rows': 18, 'style': 'font-family: monospace; font-size: 13px;'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Montar choices agrupadas por provider (igual ao SectionAgentConfig)
        choices = [('', '--- Selecione o modelo ---')]
        for provider in LLMProvider.objects.filter(is_active=True).prefetch_related('models'):
            provider_models = provider.models.filter(is_active=True).order_by('display_order')
            if provider_models.exists():
                group = [(m.model_id, m.display_name) for m in provider_models]
                choices.append((provider.name, group))
        self.fields['model'].choices = choices

        # Preservar valor salvo mesmo se não está nos choices (modelo legado)
        current_value = (
            self.initial.get('model')
            or (self.instance.model if self.instance.pk else '')
        )
        if current_value:
            flat_values = []
            for item in choices:
                if isinstance(item[1], list):
                    flat_values.extend([v for v, _ in item[1]])
                else:
                    flat_values.append(item[0])
            if current_value not in flat_values:
                choices.append(('Legado', [(current_value, f'{current_value} (legado)')]))
                self.fields['model'].choices = choices

    class Media:
        js = ('admin/js/copilot_model_filter.js',)


@admin.register(CopilotConfig)
class CopilotConfigAdmin(admin.ModelAdmin):
    form = CopilotConfigForm

    list_display = ['name', 'provider_badge', 'model', 'temperature', 'max_tokens', 'is_active', 'updated_at']
    readonly_fields = ['updated_at']

    fieldsets = (
        ('Identidade', {
            'fields': ('name', 'is_active'),
            'description': 'Nome exibido na interface do Copilot e status de ativação.',
        }),
        ('System Prompt', {
            'fields': ('system_prompt',),
            'description': (
                'Instrução base de comportamento do assistente. '
                'O contexto da Base de Conhecimento é injetado automaticamente após este texto.'
            ),
        }),
        ('Modelo LLM', {
            'fields': ('provider', 'model'),
            'description': (
                'Credenciais configuradas em <strong>Core › Provedores LLM</strong>. '
                'Ao trocar o provider, a lista de modelos é atualizada automaticamente.'
            ),
        }),
        ('Parâmetros de Geração', {
            'fields': ('temperature', 'max_tokens', 'max_kb_results'),
            'description': (
                '<strong>Temperatura:</strong> 0 = determinístico, 1 = mais criativo. '
                '<strong>Máx. tokens:</strong> limite de tokens por resposta. '
                '<strong>Resultados KB:</strong> chunks buscados na base de conhecimento por mensagem.'
            ),
        }),
        ('Auditoria', {
            'fields': ('updated_at',),
            'classes': ('collapse',),
        }),
    )

    # ── Singleton ────────────────────────────────────────────────────────────

    def has_add_permission(self, request):
        return not CopilotConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        config = CopilotConfig.get_config()
        return HttpResponseRedirect(
            reverse('admin:copilot_copilotconfig_change', args=[config.pk])
        )

    # ── Endpoint JSON para o JS dinâmico ─────────────────────────────────────

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                '<path:object_id>/llm-models-json/',
                self.admin_site.admin_view(self.llm_models_json),
                name='copilot-llm-models-json',
            ),
        ]
        return custom + urls

    def llm_models_json(self, request, object_id=None):
        data = {}
        for provider in LLMProvider.objects.filter(is_active=True).prefetch_related('models'):
            models = provider.models.filter(is_active=True).order_by('display_order')
            data[provider.code] = [
                {'id': m.model_id, 'name': m.display_name}
                for m in models
            ]
        return JsonResponse(data)

    # ── Badge visual ─────────────────────────────────────────────────────────

    def provider_badge(self, obj):
        colors = {
            'watsonx': '#0f62fe',
            'anthropic': '#c96442',
            'openai': '#10a37f',
        }
        labels = {
            'watsonx': 'IBM watsonx',
            'anthropic': 'Anthropic',
            'openai': 'OpenAI',
        }
        color = colors.get(obj.provider, '#6c757d')
        label = labels.get(obj.provider, obj.provider)
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 4px; font-size: 11px; font-weight: bold;">{}</span>',
            color, label,
        )
    provider_badge.short_description = 'Provider'


@admin.register(UserKnowledgeEntry)
class UserKnowledgeEntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'title_short', 'source_model', 'context_date', 'last_synced']
    list_filter = ['category', 'source_model', 'context_date']
    search_fields = ['title', 'content', 'user__username']
    readonly_fields = ['content_hash', 'last_synced', 'embedding']
    raw_id_fields = ['user']

    def title_short(self, obj):
        return obj.title[:80] + '...' if len(obj.title) > 80 else obj.title
    title_short.short_description = 'Título'


@admin.register(UserKnowledgeSyncLog)
class UserKnowledgeSyncLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'entries_created', 'entries_updated', 'entries_unchanged', 'started_at', 'completed_at']
    list_filter = ['status', 'started_at']
    search_fields = ['user__username']
    readonly_fields = ['user', 'started_at', 'completed_at', 'entries_created', 'entries_updated', 'entries_unchanged', 'errors', 'status']

    def has_add_permission(self, request):
        return False
