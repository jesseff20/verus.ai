"""
Models para Agent Tools — ferramentas que agentes podem usar durante a geração.
"""
import uuid

from django.db import models


class AgentTool(models.Model):
    """
    Tool disponível para uso por agentes durante geração de documentos.

    Cada tool encapsula um serviço externo (Serper, PNCP, etc.) que o agente
    pode chamar automaticamente antes da geração para obter dados reais.
    Configurável via Django Admin.
    """

    class ToolType(models.TextChoices):
        WEB_SEARCH = 'web_search', 'Busca Web (Serper/Google)'
        PNCP_SEARCH = 'pncp_search', 'Busca PNCP (contratos/editais)'
        CUSTOM = 'custom', 'Custom (serviço externo)'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nome',
        help_text='Nome único do tool (ex: Web Search (Serper))',
    )
    tool_type = models.CharField(
        max_length=20,
        choices=ToolType.choices,
        verbose_name='Tipo',
        db_index=True,
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descrição',
        help_text='O que este tool faz e quando usar',
    )
    service_path = models.CharField(
        max_length=200,
        verbose_name='Caminho do Service',
        help_text='Ex: apps.intelligent_assistant.services.tools.web_search_tool.WebSearchTool',
    )
    method_name = models.CharField(
        max_length=50,
        default='search',
        verbose_name='Método',
        help_text='Método a chamar no service (ex: search, _search_pncp)',
    )
    default_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Configuração Padrão',
        help_text='Config padrão em JSON: {"max_results": 10, "timeout": 25}',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo',
        db_index=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em',
    )

    class Meta:
        app_label = 'intelligent_assistant'
        verbose_name = 'Agent Tool'
        verbose_name_plural = 'Agent Tools'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_tool_type_display()})"


class AgentToolLink(models.Model):
    """
    Vínculo entre um agente (SectionAgentConfig) e um tool (AgentTool).

    Define quais tools um agente pode usar, em que ordem e com que configuração.
    Gerenciado como inline no admin do SectionAgentConfig.
    """

    agent = models.ForeignKey(
        'intelligent_assistant.SectionAgentConfig',
        on_delete=models.CASCADE,
        related_name='tool_links',
        verbose_name='Agente',
    )
    tool = models.ForeignKey(
        AgentTool,
        on_delete=models.CASCADE,
        related_name='agent_links',
        verbose_name='Tool',
    )
    priority = models.IntegerField(
        default=1,
        verbose_name='Prioridade',
        help_text='Ordem de execução (menor = primeiro)',
    )
    custom_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Config Customizada',
        help_text='Override da config padrão do tool (ex: {"max_results": 5})',
    )
    enabled = models.BooleanField(
        default=True,
        verbose_name='Habilitado',
    )

    class Meta:
        app_label = 'intelligent_assistant'
        unique_together = ('agent', 'tool')
        ordering = ['priority']
        verbose_name = 'Vínculo Agente ↔ Tool'
        verbose_name_plural = 'Vínculos Agente ↔ Tool'

    def __str__(self):
        status = '✓' if self.enabled else '✗'
        return f"{status} {self.agent.name[:30]} → {self.tool.name}"
