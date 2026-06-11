import uuid
from django.db import models
from django.conf import settings


class SystemModule(models.Model):
    """
    Módulos do sistema.

    Define quais módulos existem e estão ativos baseado no INSTALLED_APPS.
    O frontend consulta esses dados para saber o que exibir no sidebar.
    O controle de acesso é feito pelo sistema de roles do usuário.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Identificação
    key = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Chave',
        help_text='Identificador único (ex: forms, documents, intelligent_assistant)'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Nome',
        help_text='Nome de exibição (ex: Formulários, Documentos)'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )

    # Visual
    icon = models.CharField(
        max_length=50,
        default='Box',
        verbose_name='Ícone',
        help_text='Nome do ícone Lucide'
    )

    # Permissão Django associada
    permission_codename = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Permissão',
        help_text='Codename da permissão Django (ex: can_access_forms)'
    )

    # Rota no frontend
    route = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Rota',
        help_text='Rota no frontend (ex: /dashboard/forms)'
    )

    # Ordenação e Status
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name='Ordem de Exibição'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo',
        help_text='Se o módulo está habilitado no sistema'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Módulo do Sistema'
        verbose_name_plural = 'Módulos do Sistema'
        ordering = ['display_order', 'name']

    def __str__(self):
        return f"{self.name} ({self.key})"

    @classmethod
    def get_active_modules(cls):
        """Retorna módulos ativos no sistema."""
        return cls.objects.filter(is_active=True).order_by('display_order')

    @classmethod
    def get_user_modules(cls, user):
        """
        Retorna módulos ativos no sistema.

        O controle de acesso é feito pelo sistema de roles do usuário,
        não por permissões de módulos. Aqui apenas retornamos quais
        módulos estão habilitados no settings (INSTALLED_APPS).
        """
        active_modules = cls.get_active_modules()

        return [
            {
                'key': m.key,
                'name': m.name,
                'icon': m.icon,
                'route': m.route,
                'enabled': True,
            }
            for m in active_modules
        ]


class DocumentCategory(models.Model):
    """
    Categoria de documento jurídico (ex: Petições, Contratos, Pareceres).

    Substitui CATEGORY_CHOICES hardcoded em DocumentType, permitindo
    criar/desativar categorias via admin do sistema, sem deploy.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Código',
        help_text='Identificador único (slug, ex: fase_preparatoria)'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Nome',
        help_text='Nome de exibição (ex: Fase Preparatória)'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descrição',
        help_text='Descrição da categoria'
    )
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name='Ordem de Exibição'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        app_label = 'core'
        verbose_name = 'Categoria de Documento'
        verbose_name_plural = 'Categorias de Documento'
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active', 'display_order']),
        ]

    def __str__(self):
        return self.name


class DocumentType(models.Model):
    """
    Tipos de documento normalizados - fonte unica da verdade.

    Substitui o hardcode de DOCUMENT_TYPE_CHOICES em varios models.
    Permite adicionar novos tipos via admin sem alterar codigo.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Identificacao
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Código',
        help_text='Identificador único (ex: peticao_inicial, contrato, parecer)'
    )
    name = models.CharField(
        max_length=150,
        verbose_name='Nome',
        help_text='Nome completo (ex: Petição Inicial)'
    )
    short_name = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Nome Curto',
        help_text='Abreviação (ex: PI, CTR, PAR)'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descrição',
        help_text='Descrição do tipo de documento'
    )

    # Classificacao
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.PROTECT,
        related_name='document_types',
        verbose_name='Categoria',
        help_text='Categoria do documento jurídico'
    )

    # Visual
    icon = models.CharField(
        max_length=50,
        default='FileText',
        verbose_name='Ícone',
        help_text='Nome do ícone Lucide (ex: FileText, Scale, ClipboardList)'
    )
    color = models.CharField(
        max_length=20,
        default='primary',
        verbose_name='Cor',
        help_text='Cor para exibição (ex: primary, blue, green)'
    )

    # Base Legal
    legal_basis = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Base Legal',
        help_text='Legislação base (ex: Lei 14.133/2021, Art. 18)'
    )

    # Ordenacao e Status
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name='Ordem de Exibição'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo',
        help_text='Se False, não aparece nas opções de seleção'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Tipo de Documento'
        verbose_name_plural = 'Tipos de Documento'
        ordering = ['category', 'display_order', 'name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        if self.short_name:
            return f"{self.short_name} - {self.name}"
        return self.name

    @classmethod
    def get_active_choices(cls):
        """Retorna lista de tuplas (code, name) para uso em forms/serializers."""
        return list(cls.objects.filter(is_active=True).values_list('code', 'name'))

    @classmethod
    def get_by_code(cls, code):
        """Busca tipo por código."""
        return cls.objects.filter(code=code, is_active=True).first()


class ProcessType(models.Model):
    """
    Tipos de caso/processo jurídico normalizados.

    Fonte unica da verdade para tipos de caso jurídico.
    Permite adicionar novos tipos via admin sem alterar código.
    """

    CATEGORY_CHOICES = [
        ('civel', 'Cível'),
        ('criminal', 'Criminal'),
        ('trabalhista', 'Trabalhista'),
        ('tributario', 'Tributário'),
        ('administrativo', 'Administrativo'),
        ('previdenciario', 'Previdenciário'),
        ('familia', 'Família e Sucessões'),
        ('empresarial', 'Empresarial'),
        ('outros', 'Outros'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Identificacao
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Código',
        help_text='Identificador único (ex: acao_civil, habeas_corpus)'
    )
    name = models.CharField(
        max_length=150,
        verbose_name='Nome',
        help_text='Nome completo (ex: Ação Civil Pública)'
    )
    short_name = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Nome Curto',
        help_text='Abreviação (ex: ACP, HC, MS)'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descrição',
        help_text='Descrição do tipo de processo'
    )

    # Classificacao
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='outros',
        verbose_name='Categoria',
        help_text='Categoria principal do tipo de processo'
    )

    # Base Legal
    legal_basis = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Base Legal',
        help_text='Legislação base (ex: Lei 14.133/2021, Art. 28)'
    )

    # Visual
    icon = models.CharField(
        max_length=50,
        default='FileText',
        verbose_name='Ícone',
        help_text='Nome do ícone Lucide'
    )
    color = models.CharField(
        max_length=20,
        default='primary',
        verbose_name='Cor',
        help_text='Cor para exibição'
    )

    # Ordenacao e Status
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name='Ordem de Exibição'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo',
        help_text='Se False, não aparece nas opções de seleção'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Tipo de Processo'
        verbose_name_plural = 'Tipos de Processo'
        ordering = ['category', 'display_order', 'name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        if self.short_name:
            return f"{self.short_name} - {self.name}"
        return self.name

    @classmethod
    def get_active_choices(cls):
        """Retorna lista de tuplas (code, name) para uso em forms/serializers."""
        return list(cls.objects.filter(is_active=True).values_list('code', 'name'))

    @classmethod
    def get_by_code(cls, code):
        """Busca tipo por código."""
        return cls.objects.filter(code=code, is_active=True).first()

    @classmethod
    def get_by_category(cls, category):
        """Busca tipos por categoria. Aceita string (code) ou instância de DocumentCategory."""
        if isinstance(category, str):
            return cls.objects.filter(category__code=category, is_active=True)
        return cls.objects.filter(category=category, is_active=True)


class ProcessStatus(models.Model):
    """
    Status de caso/processo jurídico normalizado.

    Fonte unica da verdade para status de casos jurídicos.
    Permite adicionar novos status via admin sem alterar codigo.
    """

    CATEGORY_CHOICES = [
        ('inicial', 'Inicial'),
        ('andamento', 'Em Andamento'),
        ('finalizado', 'Finalizado'),
        ('suspenso', 'Suspenso/Cancelado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Identificacao
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Código',
        help_text='Identificador único (ex: em_andamento, aguardando_sentenca, concluido)'
    )
    name = models.CharField(
        max_length=150,
        verbose_name='Nome',
        help_text='Nome completo (ex: Em Planejamento)'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descrição',
        help_text='Descrição do status'
    )

    # Classificacao
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='andamento',
        verbose_name='Categoria',
        help_text='Categoria do status para agrupamento'
    )

    # Visual
    icon = models.CharField(
        max_length=50,
        default='Clock',
        verbose_name='Ícone',
        help_text='Nome do ícone Lucide (ex: Clock, Loader2, CheckCircle2)'
    )
    color = models.CharField(
        max_length=50,
        default='bg-blue-100 text-blue-800',
        verbose_name='Cor',
        help_text='Classes CSS para cor (ex: bg-blue-100 text-blue-800)'
    )

    # Ordenacao e Status
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name='Ordem de Exibição'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo',
        help_text='Se False, não aparece nas opções de seleção'
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name='Padrão',
        help_text='Se True, é o status inicial de novos processos'
    )
    is_final = models.BooleanField(
        default=False,
        verbose_name='Final',
        help_text='Se True, indica que o processo foi finalizado'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Status de Processo'
        verbose_name_plural = 'Status de Processo'
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

    @classmethod
    def get_active_choices(cls):
        """Retorna lista de tuplas (code, name) para uso em forms/serializers."""
        return list(cls.objects.filter(is_active=True).values_list('code', 'name'))

    @classmethod
    def get_by_code(cls, code):
        """Busca status por código."""
        return cls.objects.filter(code=code, is_active=True).first()

    @classmethod
    def get_default(cls):
        """Retorna o status padrão para novos processos."""
        return cls.objects.filter(is_default=True, is_active=True).first()


class LegalSource(models.Model):
    """Fonte legal para referência em documentos."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'core'
        verbose_name = 'Fonte Legal'
        verbose_name_plural = 'Fontes Legais'


class AuditLog(models.Model):
    """
    Log de auditoria generico para qualquer entidade do sistema.
    Registra todas as acoes relevantes para compliance e rastreabilidade.
    """

    ACTION_CHOICES = [
        # CRUD basico
        ('create', 'Criacao'),
        ('read', 'Leitura'),
        ('update', 'Atualizacao'),
        ('delete', 'Exclusao'),

        # Workflow
        ('submit', 'Submissao'),
        ('approve', 'Aprovacao'),
        ('reject', 'Rejeicao'),
        ('publish', 'Publicacao'),
        ('archive', 'Arquivamento'),

        # Autenticacao
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('login_failed', 'Falha de Login'),
        ('password_change', 'Alteracao de Senha'),

        # Documentos
        ('generate', 'Geracao'),
        ('download', 'Download'),
        ('print', 'Impressao'),
        ('sign', 'Assinatura'),

        # Sistema
        ('config_change', 'Alteracao de Configuracao'),
        ('permission_change', 'Alteracao de Permissao'),
        ('export', 'Exportacao'),
        ('import', 'Importacao'),
    ]

    SEVERITY_CHOICES = [
        ('info', 'Informativo'),
        ('warning', 'Aviso'),
        ('error', 'Erro'),
        ('critical', 'Critico'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Quem
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name='Usuario'
    )
    user_email = models.EmailField(
        blank=True,
        help_text='Email no momento da acao'
    )
    user_role = models.CharField(
        max_length=50,
        blank=True,
        help_text='Role no momento da acao'
    )

    # O que
    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
        verbose_name='Acao'
    )
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='info',
        verbose_name='Severidade'
    )

    # Onde (entidade afetada)
    entity_type = models.CharField(
        max_length=100,
        help_text='Ex: Document, User, Blueprint',
        verbose_name='Tipo de Entidade'
    )
    entity_id = models.CharField(
        max_length=100,
        help_text='ID da entidade',
        verbose_name='ID da Entidade'
    )
    entity_name = models.CharField(
        max_length=255,
        blank=True,
        help_text='Nome/titulo para exibicao',
        verbose_name='Nome da Entidade'
    )

    # Detalhes
    description = models.TextField(
        help_text='Descricao legivel da acao',
        verbose_name='Descricao'
    )
    old_values = models.JSONField(
        null=True,
        blank=True,
        help_text='Valores anteriores',
        verbose_name='Valores Anteriores'
    )
    new_values = models.JSONField(
        null=True,
        blank=True,
        help_text='Novos valores',
        verbose_name='Novos Valores'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Dados adicionais',
        verbose_name='Metadados'
    )

    # Contexto tecnico
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Endereco IP'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    request_id = models.CharField(
        max_length=100,
        blank=True,
        help_text='ID para correlacao de requests',
        verbose_name='Request ID'
    )

    # Timestamp
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )

    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['action']),
            models.Index(fields=['severity']),
        ]

    def __str__(self):
        return f"[{self.action}] {self.entity_type}:{self.entity_id} - {self.user_email or 'anonymous'}"


class LLMProvider(models.Model):
    """
    Provedores de LLM cadastrados no sistema.

    Gerenciado pelo admin. Cada provider tem sua API key e configurações.
    Os agentes de IA consomem apenas providers/modelos ativos cadastrados aqui.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Identificação
    code = models.CharField(
        max_length=30,
        unique=True,
        verbose_name='Código',
        help_text='Identificador único (ex: anthropic, openai, watsonx)'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Nome',
        help_text='Nome de exibição (ex: Anthropic (Claude))'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )

    # Credenciais
    api_key = models.TextField(
        blank=True,
        verbose_name='API Key',
        help_text='Chave de autenticação da API'
    )
    api_url = models.URLField(
        blank=True,
        verbose_name='URL da API',
        help_text='URL base da API (obrigatório para watsonx)'
    )
    extra_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Configurações extras',
        help_text='Ex: {"project_id": "xxx"} para watsonx'
    )

    # Visual
    icon = models.CharField(
        max_length=50,
        default='Cpu',
        verbose_name='Ícone',
        help_text='Nome do ícone Lucide'
    )
    color = models.CharField(
        max_length=20,
        default='#6c757d',
        verbose_name='Cor',
        help_text='Cor hex para exibição'
    )

    # Ordenação e Status
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name='Ordem de Exibição'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo',
        help_text='Se False, não aparece nas opções de seleção'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Provedor LLM'
        verbose_name_plural = 'Provedores LLM'
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['code'], name='core_llmprov_code_idx'),
            models.Index(fields=['is_active'], name='core_llmprov_active_idx'),
        ]

    def __str__(self):
        status = '✓' if self.is_active else '✗'
        return f"{self.name} ({self.code}) [{status}]"

    @property
    def has_api_key(self):
        """Retorna se tem API key configurada (sem expor a chave)."""
        return bool(self.api_key)

    @property
    def masked_api_key(self):
        """Retorna a chave mascarada para exibição."""
        if not self.api_key:
            return ''
        key = self.api_key
        if len(key) <= 8:
            return '****'
        return f"{key[:4]}...{key[-4:]}"

    @property
    def active_models(self):
        """Retorna modelos ativos deste provider."""
        return self.models.filter(is_active=True).order_by('display_order', 'display_name')

    @classmethod
    def get_by_code(cls, code):
        """Busca provider ativo por código."""
        return cls.objects.filter(code=code, is_active=True).first()


class LLMModel(models.Model):
    """
    Modelos de IA disponíveis por provider.

    Cadastrados pelo admin. Apenas modelos ativos aparecem
    nas opções de seleção dos agentes.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relação
    provider = models.ForeignKey(
        LLMProvider,
        on_delete=models.CASCADE,
        related_name='models',
        verbose_name='Provedor'
    )

    # Identificação
    model_id = models.CharField(
        max_length=100,
        verbose_name='ID do Modelo',
        help_text='Identificador da API (ex: claude-sonnet-4-5-20250514, gpt-4o)'
    )
    display_name = models.CharField(
        max_length=100,
        verbose_name='Nome de Exibição',
        help_text='Nome amigável (ex: Claude Sonnet 4.5, GPT-4o)'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descrição',
        help_text='Descrição do modelo e seus pontos fortes'
    )

    # Configurações
    max_tokens_limit = models.PositiveIntegerField(
        default=4096,
        verbose_name='Limite de Tokens',
        help_text='Máximo de tokens de saída suportado'
    )
    default_temperature = models.FloatField(
        default=0.7,
        verbose_name='Temperature Padrão',
        help_text='Valor padrão de temperature para este modelo'
    )

    # Ordenação e Status
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name='Ordem de Exibição'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo',
        help_text='Se False, não aparece nas opções de seleção'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Modelo LLM'
        verbose_name_plural = 'Modelos LLM'
        ordering = ['provider', 'display_order', 'display_name']
        unique_together = [['provider', 'model_id']]
        indexes = [
            models.Index(fields=['provider', 'is_active'], name='core_llmmodel_prov_active_idx'),
            models.Index(fields=['model_id'], name='core_llmmodel_modelid_idx'),
        ]

    def __str__(self):
        return f"{self.display_name} ({self.provider.code})"


class TokenUsageLog(models.Model):
    """
    Log de uso de tokens de IA.

    Registra cada chamada a provedores de LLM para auditoria,
    controle de custos e analytics do sistema.
    """

    PROVIDER_CHOICES = [
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),
        ('watsonx', 'WatsonX'),
        ('other', 'Outro'),
    ]

    USAGE_TYPE_CHOICES = [
        ('copilot', 'Copilot'),
        ('agent', 'Agente IA'),
        ('document_gen', 'Geração de Documento'),
        ('user_request', 'Solicitação do Usuário'),
        ('analysis', 'Análise'),
        ('other', 'Outro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='token_usage_logs',
        verbose_name='Usuário'
    )

    model_provider = models.CharField(
        max_length=30,
        choices=PROVIDER_CHOICES,
        verbose_name='Provedor',
        help_text='Provedor do modelo de IA'
    )
    model_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Modelo',
        help_text='Nome do modelo utilizado (ex: claude-sonnet-4-5-20250514)'
    )

    usage_type = models.CharField(
        max_length=30,
        choices=USAGE_TYPE_CHOICES,
        default='other',
        verbose_name='Tipo de Uso'
    )

    input_tokens = models.PositiveIntegerField(
        default=0,
        verbose_name='Tokens de Entrada'
    )
    output_tokens = models.PositiveIntegerField(
        default=0,
        verbose_name='Tokens de Saída'
    )
    total_tokens = models.PositiveIntegerField(
        default=0,
        verbose_name='Total de Tokens'
    )

    cost_estimate = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=0,
        verbose_name='Custo Estimado (USD)',
        help_text='Custo estimado em dólares'
    )

    description = models.TextField(
        blank=True,
        verbose_name='Descrição',
        help_text='Descrição da operação realizada'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )

    class Meta:
        verbose_name = 'Log de Uso de Tokens'
        verbose_name_plural = 'Logs de Uso de Tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['model_provider']),
            models.Index(fields=['usage_type']),
        ]

    def __str__(self):
        return f"[{self.model_provider}] {self.total_tokens} tokens - {self.get_usage_type_display()}"

    def save(self, *args, **kwargs):
        if not self.total_tokens:
            self.total_tokens = self.input_tokens + self.output_tokens
        super().save(*args, **kwargs)


class AIAnalysisConfig(models.Model):
    """
    Configuração de agentes de análise de IA.

    Permite configurar via admin: prompt, personalidade, perguntas,
    provider/model e parâmetros para cada tipo de análise no sistema.
    Ex: análise de editais na pesquisa de preço, análise de documentos, etc.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nome',
        help_text='Identificador único (ex: edital_analysis, document_review)',
    )
    display_name = models.CharField(
        max_length=200,
        verbose_name='Nome de Exibição',
        help_text='Nome amigável (ex: Análise de Editais)',
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descrição',
        help_text='Descrição do que este agente faz',
    )

    # Prompt
    system_prompt = models.TextField(
        verbose_name='System Prompt',
        help_text='Personalidade e instruções base do agente',
    )
    user_prompt_template = models.TextField(
        verbose_name='Template do User Prompt',
        help_text='Template com placeholders: {{text}}, {{objeto}}, {{questions}}',
    )
    questions = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Perguntas',
        help_text='Lista de perguntas que o agente deve responder. Ex: ["Objeto da contratação", "Valor estimado"]',
    )

    # LLM
    llm_provider = models.CharField(
        max_length=30,
        default='watsonx',
        verbose_name='Provider LLM',
        help_text='anthropic, openai, watsonx',
    )
    model_name = models.CharField(
        max_length=100,
        default='mistralai/mistral-medium-2505',
        verbose_name='Modelo',
    )
    temperature = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.3,
        verbose_name='Temperatura',
    )
    max_tokens = models.IntegerField(
        default=2048,
        verbose_name='Max Tokens',
    )

    # Limites
    max_input_chars = models.IntegerField(
        default=15000,
        verbose_name='Max Chars Input',
        help_text='Limite de caracteres do texto de entrada antes de truncar',
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo',
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Configuração de Análise IA'
        verbose_name_plural = 'Configurações de Análise IA'
        ordering = ['name']

    def __str__(self):
        return f"{self.display_name} ({self.llm_provider}/{self.model_name})"

    def build_questions_text(self):
        """Formata as perguntas como texto numerado para o prompt."""
        if not self.questions:
            return ''
        return '\n'.join(f"{i+1}. **{q}**" for i, q in enumerate(self.questions))
