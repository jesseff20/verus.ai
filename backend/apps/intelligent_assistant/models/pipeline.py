"""
Modelos de pipeline de geração e sessões de geração.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class SectionPipelineStep(models.Model):
    """
    Um passo no pipeline de geração de uma seção.

    Permite configurar N agentes em sequência para uma seção:
    Ex: analyze → generate → validate → refine

    Se vazio, o sistema usa o fluxo padrão (generator_agent → validator_agent).
    """

    STEP_TYPE_CHOICES = [
        ('analyze', 'Analisar Exemplos'),
        ('generate', 'Gerar Conteúdo'),
        ('validate', 'Validar Conteúdo'),
        ('refine', 'Refinar com Feedback'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    section = models.ForeignKey(
        'intelligent_assistant.BlueprintSection',
        on_delete=models.CASCADE,
        related_name='pipeline_steps',
        verbose_name='Seção'
    )
    agent = models.ForeignKey(
        'intelligent_assistant.SectionAgentConfig',
        on_delete=models.PROTECT,
        related_name='pipeline_steps',
        verbose_name='Agente'
    )

    step_order = models.IntegerField(
        verbose_name='Ordem do Passo',
        help_text='Ordem de execução (1, 2, 3...). Menor = primeiro.'
    )
    step_type = models.CharField(
        max_length=20,
        choices=STEP_TYPE_CHOICES,
        verbose_name='Tipo do Passo',
        help_text='Tipo de operação que este passo executa'
    )

    # O output deste step é passado como input do próximo
    output_variable = models.CharField(
        max_length=50,
        default='output',
        verbose_name='Variável de Saída',
        help_text='Nome da variável que recebe o output deste step (acessível pelo próximo step via {{variavel}})'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        app_label = 'intelligent_assistant'
        verbose_name = 'Passo do Pipeline'
        verbose_name_plural = 'Passos do Pipeline'
        ordering = ['section', 'step_order']
        unique_together = ['section', 'step_order']
        indexes = [
            models.Index(fields=['section', 'step_order']),
        ]

    def __str__(self):
        type_label = dict(self.STEP_TYPE_CHOICES).get(self.step_type, self.step_type)
        return f"{self.section} → Passo {self.step_order}: {type_label} ({self.agent.name})"


class GenerationSession(models.Model):
    """
    Sessão de geração de documento usando um blueprint.

    Compatível com o IntelligentSession existente através de
    relacionamento opcional OneToOne.
    """

    STATUS_CHOICES = [
        ('initialized', 'Inicializada'),
        ('sections_selected', 'Seções Selecionadas'),
        ('generating', 'Gerando'),
        ('validating', 'Validando'),
        ('completed', 'Concluída'),
        ('failed', 'Falhou'),
        ('cancelled', 'Cancelada'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Usuário e blueprint
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='generation_sessions',
        verbose_name='Usuário'
    )
    blueprint = models.ForeignKey(
        'intelligent_assistant.DocumentBlueprint',
        on_delete=models.PROTECT,
        related_name='generation_sessions',
        verbose_name='Blueprint'
    )

    # Compatibilidade com sistema existente
    # ForeignKey (em vez de OneToOneField) permite múltiplas GenerationSessions
    # por IntelligentSession (regenerações) e garante CASCADE em todas elas.
    intelligent_session = models.ForeignKey(
        'intelligent_assistant.IntelligentSession',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='generation_sessions',
        verbose_name='Sessão Inteligente',
        help_text='Sessão do sistema legado, se existir'
    )

    # Dados da sessão
    objective = models.TextField(
        verbose_name='Objetivo',
        help_text='Objetivo/contexto fornecido pelo usuário'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='initialized',
        verbose_name='Status'
    )

    # Seções selecionadas para geração
    selected_sections = models.ManyToManyField(
        'intelligent_assistant.BlueprintSection',
        blank=True,
        related_name='selected_in_sessions',
        verbose_name='Seções Selecionadas',
        help_text='Seções que o usuário escolheu gerar'
    )

    # Configurações da sessão
    config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Configurações',
        help_text='Configurações adicionais da sessão'
    )

    # Resultado
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name='Mensagem de Erro'
    )

    # Consumo de tokens
    total_input_tokens = models.IntegerField(
        default=0,
        verbose_name='Total Tokens de Entrada',
        help_text='Soma de input_tokens de todas as chamadas LLM desta sessão'
    )
    total_output_tokens = models.IntegerField(
        default=0,
        verbose_name='Total Tokens de Saída',
        help_text='Soma de output_tokens de todas as chamadas LLM desta sessão'
    )
    total_tokens = models.IntegerField(
        default=0,
        verbose_name='Total de Tokens',
        help_text='Soma total (input + output) de todas as chamadas LLM desta sessão'
    )
    estimated_cost_usd = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=0,
        verbose_name='Custo Estimado (USD)',
        help_text='Custo estimado baseado nos preços do provider/modelo'
    )

    # Dados do pipeline (visualização do grafo)
    pipeline_graph = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Pipeline Graph',
        help_text='Estado final do grafo de execução {nodes, edges, log} para visualização'
    )

    # Timestamps
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Iniciado em'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Concluído em'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        app_label = 'intelligent_assistant'
        verbose_name = 'Sessão de Geração'
        verbose_name_plural = 'Sessões de Geração'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['blueprint', 'status']),
        ]

    def __str__(self):
        return f"{self.blueprint.name} - {self.user.username} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"

    @property
    def progress_percentage(self):
        """Calcula porcentagem de progresso"""
        total = self.selected_sections.count()
        if total == 0:
            return 0
        completed = self.section_generations.filter(
            status__in=['completed', 'validated']
        ).count()
        return int((completed / total) * 100)

    @property
    def completed_sections_count(self):
        """Número de seções completadas"""
        return self.section_generations.filter(
            status__in=['completed', 'validated']
        ).count()

    @property
    def total_selected_sections(self):
        """Total de seções selecionadas"""
        return self.selected_sections.count()


class SectionGeneration(models.Model):
    """
    Registro de geração de uma seção específica.

    Guarda o conteúdo gerado, resultado da validação e métricas.
    """

    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('generating', 'Gerando'),
        ('generated', 'Gerado'),
        ('validating', 'Validando'),
        ('validated', 'Validado'),
        ('failed', 'Falhou'),
        ('skipped', 'Pulada'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relacionamentos
    session = models.ForeignKey(
        GenerationSession,
        on_delete=models.CASCADE,
        related_name='section_generations',
        verbose_name='Sessão'
    )
    section = models.ForeignKey(
        'intelligent_assistant.BlueprintSection',
        on_delete=models.PROTECT,
        related_name='generations',
        verbose_name='Seção'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Status'
    )

    # Conteúdo gerado
    content = models.TextField(
        blank=True,
        verbose_name='Conteúdo',
        help_text='Conteúdo gerado pelo agente'
    )

    # Validação
    is_valid = models.BooleanField(
        default=False,
        verbose_name='É Válido?'
    )
    validation_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Score de Validação',
        help_text='Score de 0 a 100'
    )
    validation_errors = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Erros de Validação'
    )
    validation_warnings = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Avisos de Validação'
    )
    validation_feedback = models.TextField(
        blank=True,
        verbose_name='Feedback da Validação',
        help_text='Feedback detalhado do validador'
    )

    # Métricas
    generation_attempts = models.IntegerField(
        default=0,
        verbose_name='Tentativas de Geração'
    )
    tokens_used = models.IntegerField(
        default=0,
        verbose_name='Tokens Usados',
        help_text='Total de tokens consumidos (input + output)'
    )
    generation_time_ms = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Tempo de Geração (ms)'
    )
    validation_time_ms = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Tempo de Validação (ms)'
    )

    # Raciocínio/Debug
    agent_reasoning = models.TextField(
        blank=True,
        verbose_name='Raciocínio do Agente',
        help_text='Log do processo de raciocínio do agente'
    )
    rag_context_used = models.TextField(
        blank=True,
        verbose_name='Contexto RAG Utilizado',
        help_text='Chunks de contexto recuperados pelo RAG'
    )

    # Erro
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name='Mensagem de Erro'
    )

    # Timestamps
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Iniciado em'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Concluído em'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        app_label = 'intelligent_assistant'
        verbose_name = 'Geração de Seção'
        verbose_name_plural = 'Gerações de Seções'
        ordering = ['session', 'section__order']
        unique_together = [['session', 'section']]
        indexes = [
            models.Index(fields=['session', 'status']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.session} - {self.section.section_name} ({self.get_status_display()})"
