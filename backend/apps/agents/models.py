"""
Models para Agentes de IA (prompts editáveis)
"""
import uuid
from django.db import models
from django.conf import settings
from apps.core.constants import LLM_PROVIDER_CHOICES


class AgentPrompt(models.Model):
    """
    Agente de IA para chat/assistente pessoal.
    Estes agentes conversam com o usuário e buscam informações na Knowledge Base.
    Não são vinculados a campos específicos nem geram documentos completos.

    NOTA: Para assistentes de formulário, use FormAssistant (apps.forms)
    NOTA: Para agentes de seção/documento, use SectionAgentConfig (apps.intelligent_assistant)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Metadados
    name = models.CharField('Nome', max_length=255, help_text='Nome descritivo do prompt')
    description = models.TextField('Descrição', blank=True)

    # Tipo de agente chat (subtipo específico)
    agent_type = models.CharField(
        'Tipo/Subtipo',
        max_length=50,
        help_text='Subtipo específico do chat (ex: advogado_civil, advogado_criminal, analista_juridico)'
    )

    # Prompts
    system_prompt = models.TextField(
        'System Prompt',
        help_text='Instruções do sistema para o agente'
    )
    user_prompt_template = models.TextField(
        'User Prompt Template',
        help_text='Template com {{placeholders}} para variáveis'
    )

    # Configurações LLM
    llm_provider = models.CharField(
        'Provedor LLM',
        max_length=20,
        choices=LLM_PROVIDER_CHOICES,
        default='openai'
    )
    model_name = models.CharField(
        'Nome do Modelo',
        max_length=100,
        default='gpt-4o-mini',
        help_text='Ex: gpt-4o-mini, mistralai/mistral-medium-2505'
    )
    temperature = models.FloatField(
        'Temperature',
        default=0.7,
        help_text='0.0 = mais determinístico, 2.0 = mais criativo'
    )
    max_tokens = models.IntegerField('Max Tokens', default=500)

    # Contexto RAG
    use_rag = models.BooleanField(
        'Usar RAG',
        default=False,
        help_text='Buscar contexto na Knowledge Base'
    )
    rag_query_template = models.TextField(
        'Template de Query RAG',
        blank=True,
        help_text='Template para busca no RAG. Ex: {{user_input}}'
    )

    # Knowledge Bases (para assistentes de chat)
    knowledge_bases = models.ManyToManyField(
        'kb.Document',
        blank=True,
        related_name='agent_prompts',
        verbose_name='Bases de Conhecimento',
        help_text='Documentos da KB que este agente pode acessar (usado principalmente para chat_assistant)'
    )

    # UI/UX
    icon = models.CharField(
        'Ícone',
        max_length=50,
        blank=True,
        default='robot',
        help_text='Nome do ícone para exibição (ex: translate, edit, file-text)'
    )
    color = models.CharField(
        'Cor',
        max_length=7,
        default='#003366',
        help_text='Cor em hexadecimal para identificação visual'
    )
    display_order = models.IntegerField(
        'Ordem de Exibição',
        default=0,
        help_text='Ordem de exibição na lista (menor = primeiro)'
    )

    # Flags
    is_active = models.BooleanField('Ativo', default=True)
    is_default = models.BooleanField(
        'Prompt Padrão',
        default=False,
        help_text='Prompt padrão para este tipo de agente'
    )

    # Audit
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_agent_prompts',
        verbose_name='Criado por'
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Agente de Chat'
        verbose_name_plural = 'Agentes de Chat'
        ordering = ['display_order', 'agent_type']
        indexes = [
            models.Index(fields=['agent_type', 'is_active']),
        ]

    def __str__(self):
        return self.name

    def extract_variables(self):
        """Extrai variáveis do user_prompt_template"""
        import re
        variables = re.findall(r'\{\{(\w+)\}\}', self.user_prompt_template)
        return list(set(variables))

    @property
    def variable_count(self):
        """Retorna quantidade de variáveis"""
        return len(self.extract_variables())
