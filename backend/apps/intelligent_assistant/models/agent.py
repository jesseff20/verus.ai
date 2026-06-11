"""
Modelos de configuração de agentes de IA para geração de documentos.
"""
import uuid
import re
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class SectionAgentConfig(models.Model):
    """
    Configuração de um agente de IA para geração ou validação de seções de documentos.

    Este modelo é específico para o sistema dinâmico de geração de documentos
    (ETP, Termo de Referência, etc). Cada SectionAgentConfig representa um agente que pode ser:
    - Gerador: Cria conteúdo para uma seção do documento
    - Validador: Valida o conteúdo gerado por um gerador

    NOTA: Para agentes de chat/conversa, use AgentPrompt (apps.agents)
    NOTA: Para assistentes de formulário, use FormAssistant (apps.forms)

    Configurável via Django Admin/PgAdmin.
    """

    AGENT_TYPE_CHOICES = [
        ('generator', 'Gerador de Conteúdo'),
        ('validator', 'Validador de Conteúdo'),
        ('analyzer', 'Analisador de Exemplos'),
        ('refiner', 'Refinador com Feedback'),
    ]

    LLM_PROVIDER_CHOICES = [
        ('anthropic', 'Anthropic (Claude)'),
        ('openai', 'OpenAI (GPT)'),
        ('watsonx', 'IBM watsonx.ai'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Identificação
    name = models.CharField(
        max_length=255,
        verbose_name='Nome',
        help_text='Nome descritivo do agente (ex: "Gerador Seção 1 - Descrição da Necessidade")'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descrição',
        help_text='Descrição detalhada do propósito do agente'
    )

    # Tipo do agente
    agent_type = models.CharField(
        max_length=20,
        choices=AGENT_TYPE_CHOICES,
        default='generator',
        verbose_name='Tipo de Agente'
    )

    # Prompts
    system_prompt = models.TextField(
        verbose_name='System Prompt',
        help_text='Instruções do sistema para o agente. Define o papel e comportamento.'
    )
    user_prompt_template = models.TextField(
        verbose_name='User Prompt Template',
        help_text='Template do prompt do usuário. Use {{variavel}} para placeholders. '
                  'Variáveis disponíveis: {{objective}}, {{context}}, {{previous_sections}}, '
                  '{{current_content}}, {{section_name}}, {{section_number}}'
    )

    # Configurações do LLM
    llm_provider = models.CharField(
        max_length=20,
        choices=LLM_PROVIDER_CHOICES,
        default='anthropic',
        verbose_name='Provedor LLM'
    )
    model_name = models.CharField(
        max_length=100,
        default='claude-3-5-sonnet-20241022',
        verbose_name='Modelo',
        help_text='Nome do modelo (ex: claude-3-5-sonnet-20241022, gpt-4o)'
    )
    temperature = models.FloatField(
        default=0.7,
        verbose_name='Temperature',
        help_text='0.0 = determinístico, 2.0 = criativo'
    )
    max_tokens = models.IntegerField(
        default=4000,
        verbose_name='Max Tokens',
        help_text='Limite máximo de tokens na resposta'
    )

    # Configurações de RAG
    use_rag = models.BooleanField(
        default=True,
        verbose_name='Usar RAG',
        help_text='Buscar contexto relevante na base de conhecimento'
    )
    rag_query_template = models.TextField(
        blank=True,
        verbose_name='Template de Query RAG',
        help_text='Template para buscar contexto. Use {{variavel}} para placeholders.'
    )
    rag_top_k = models.IntegerField(
        default=5,
        verbose_name='RAG Top K',
        help_text='Número de chunks mais relevantes a recuperar'
    )
    rag_similarity_threshold = models.FloatField(
        default=0.7,
        verbose_name='RAG Threshold',
        help_text='Similaridade mínima para incluir um chunk (0.0 a 1.0)'
    )

    # Knowledge Bases específicas para este agente
    knowledge_bases = models.ManyToManyField(
        'intelligent_assistant.KnowledgeBase',
        blank=True,
        related_name='section_agent_configs',
        verbose_name='Bases de Conhecimento',
        help_text='Bases de conhecimento específicas para este agente'
    )

    # Flags
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo',
        help_text='Se o agente está disponível para uso'
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name='Padrão',
        help_text='Se é o agente padrão para seu tipo'
    )

    # Configurações de fallback
    fallback_provider = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Provider de Fallback',
        help_text='Provider de fallback se principal falhar'
    )
    fallback_model = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Modelo de Fallback',
        help_text='Modelo de fallback'
    )

    # Versionamento do prompt
    prompt_version = models.CharField(
        max_length=20,
        default='1.0',
        verbose_name='Versão do Prompt',
        help_text='Versão atual do prompt'
    )
    prompt_updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Prompt Atualizado em',
        help_text='Última atualização do prompt'
    )

    # Auditoria
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_section_agent_configs',
        verbose_name='Criado por'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        app_label = 'intelligent_assistant'
        verbose_name = 'Configuração de Agente de Seção'
        verbose_name_plural = 'Configurações de Agentes de Seção'
        ordering = ['agent_type', 'name']
        indexes = [
            models.Index(fields=['agent_type', 'is_active']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"[{self.get_agent_type_display()}] {self.name}"

    def extract_variables(self):
        """Extrai variáveis do user_prompt_template"""
        variables = re.findall(r'\{\{(\w+)\}\}', self.user_prompt_template)
        return list(set(variables))

    @property
    def variable_count(self):
        """Retorna quantidade de variáveis no template"""
        return len(self.extract_variables())
