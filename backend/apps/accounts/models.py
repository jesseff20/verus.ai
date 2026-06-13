"""
Models de usuários customizados
"""
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    """
    Usuário customizado com campos adicionais
    """
    ROLE_CHOICES = [
        # Plataforma
        ('superadmin', 'Super Administrador'),
        ('admin', 'Administrador'),

        # Chefia da Procuradoria
        ('procurador_geral', 'Procurador(a)-Geral'),
        ('subprocurador_geral', 'Subprocurador(a)-Geral'),

        # Gerência
        ('gerente', 'Gerente'),

        # Corpo de Procuradores
        ('procurador', 'Procurador(a)'),

        # Assessoria
        ('assessor_gerencial', 'Assessor(a) Gerencial'),
        ('assessor_gabinete', 'Assessor(a) de Gabinete'),

        # Distribuição / Protocolo
        ('distribuidor', 'Distribuidor(a)'),

        # Servidor genérico
        ('servidor', 'Servidor(a) Público(a)'),

        # Acesso Limitado
        ('visualizador', 'Visualizador'),
    ]

    # Hierarquia numérica de permissões
    # Nível define quem pode avocar, redistribuir, assinar, etc.
    # Mapeia diretamente para os swim lanes do fluxo BPMN.
    ROLE_HIERARCHY = {
        'superadmin': 100,
        'admin': 90,
        'procurador_geral': 85,
        'subprocurador_geral': 80,
        'gerente': 70,
        'procurador': 60,
        'assessor_gerencial': 50,
        'assessor_gabinete': 45,
        'distribuidor': 30,
        'servidor': 15,
        'visualizador': 1,
    }

    # Permissões específicas do fluxo de procuradoria
    # Quem pode executar cada ação-chave do BPMN
    ROLE_PERMISSIONS = {
        # Ações de distribuição
        'distribuir': ['superadmin', 'admin', 'distribuidor', 'gerente'],
        'redistribuir': ['superadmin', 'admin', 'distribuidor', 'gerente'],
        # Elaboração de peças
        'elaborar_peca': ['superadmin', 'admin', 'procurador', 'procurador_geral', 'subprocurador_geral'],
        'elaborar_minuta': ['superadmin', 'admin', 'assessor_gerencial', 'assessor_gabinete'],
        # Peticionamento (PJe/EPROC)
        'peticionar': ['superadmin', 'admin', 'procurador', 'procurador_geral', 'subprocurador_geral'],
        # Assinatura
        'assinar_despacho': ['superadmin', 'admin', 'gerente', 'procurador_geral', 'subprocurador_geral'],
        # Avocação
        'avocar': ['superadmin', 'admin', 'procurador_geral', 'subprocurador_geral'],
        # Aprovação de redistribuição
        'aprovar_redistribuicao': ['superadmin', 'admin', 'gerente', 'procurador_geral', 'subprocurador_geral'],
    }

    # Aliases para compatibilidade com dados legados do BravoJus
    ROLE_ALIASES = {
        'socio': 'procurador_geral',
        'advogado_senior': 'procurador',
        'advogado_pleno': 'procurador',
        'advogado_junior': 'procurador',
        'gestor': 'gerente',
        'coordenador': 'gerente',
        'assessor': 'assessor_gerencial',
        'analista': 'servidor',
        'assistente': 'servidor',
        'paralegal': 'servidor',
        'secretaria': 'distribuidor',
        'servidor': 'servidor',
        'revisor': 'servidor',
        'auditor': 'servidor',
        'estagiario': 'visualizador',
        'cliente': 'visualizador',
        # Aliases antigos em inglês
        'manager': 'gerente',
        'reviewer': 'servidor',
        'analyst': 'servidor',
        'viewer': 'visualizador',
    }

    role = models.CharField(
        'Perfil',
        max_length=25,
        choices=ROLE_CHOICES,
        default='servidor'
    )

    # Vínculo organizacional (multi-tenancy por órgão)
    organ = models.ForeignKey(
        'organization.Organ',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='users',
        verbose_name='Órgão',
        help_text='Órgão/Procuradoria ao qual o usuário pertence',
    )
    unit = models.ForeignKey(
        'organization.Unit',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='users',
        verbose_name='Unidade/Gerência',
        help_text='Unidade interna (ex: Gerência Judicial 1º Grau)',
    )

    # Campos adicionais
    phone = models.CharField('Telefone', max_length=20, blank=True)
    department = models.CharField('Departamento', max_length=100, blank=True)
    position = models.CharField('Cargo', max_length=100, blank=True)

    # Avatar
    avatar = models.ImageField(
        'Avatar', upload_to='avatars/', blank=True, null=True)

    # Perfil Profissional
    oab_number = models.CharField(
        'Registro Profissional', max_length=20, blank=True,
        help_text='Número de registro profissional (OAB, inscrição municipal, etc.)'
    )
    oab_state = models.CharField(
        'UF do Registro', max_length=2, blank=True,
        help_text='Estado do registro profissional (ex: SP, RJ)'
    )
    lawyer_specialties = models.JSONField(
        'Especializações', default=list, blank=True,
        help_text='Áreas de atuação do servidor (ex: ["Administrativo", "Tributário Municipal"])'
    )
    signature_image = models.ImageField(
        'Imagem de Assinatura', upload_to='signatures/', blank=True, null=True,
        help_text='Imagem da assinatura digitalizada'
    )
    signature_name = models.CharField(
        'Nome na Assinatura', max_length=200, blank=True,
        help_text='Nome como aparece na assinatura de documentos'
    )

    # Preferências
    preferred_llm_provider = models.CharField(
        'Provedor LLM Preferido',
        max_length=20,
        choices=[
            ('openai', 'OpenAI'),
            ('watsonx', 'IBM WatsonX'),
            ('anthropic', 'Anthropic (legado)'),
        ],
        blank=True,
        null=True
    )

    # Metadata
    metadata = models.JSONField('Metadados', default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    last_login_ip = models.GenericIPAddressField(
        'Último IP', null=True, blank=True)

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['-created_at']

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def resolved_role(self):
        """Retorna o role resolvido (aplica aliases de backwards compatibility)"""
        return self.ROLE_ALIASES.get(self.role, self.role)

    @property
    def role_level(self):
        """Retorna o nível hierárquico do role do usuário"""
        return self.ROLE_HIERARCHY.get(self.resolved_role, 0)

    def has_role_level(self, min_level):
        """Verifica se o usuário tem nível hierárquico >= min_level"""
        return self.role_level >= min_level

    @property
    def is_superadmin(self):
        """Verifica se é super administrador"""
        return self.resolved_role == 'superadmin'

    @property
    def is_admin(self):
        """Verifica se é administrador (superadmin ou admin)"""
        return self.resolved_role in ['superadmin', 'admin']

    # ──────────────────────────────────────────
    # Propriedades de role — procuradoria
    # ──────────────────────────────────────────
    @property
    def is_procurador_geral(self):
        return self.resolved_role in ('procurador_geral', 'subprocurador_geral')

    @property
    def is_gerente(self):
        return self.resolved_role == 'gerente'

    @property
    def is_procurador(self):
        return self.resolved_role == 'procurador'

    @property
    def is_assessor(self):
        return self.resolved_role in ('assessor_gerencial', 'assessor_gabinete')

    @property
    def is_distribuidor(self):
        return self.resolved_role == 'distribuidor'

    @property
    def is_viewer(self):
        return self.resolved_role == 'visualizador'

    # Alias de compatibilidade legado
    @property
    def is_manager(self):
        return self.is_gerente

    @property
    def is_reviewer(self):
        return self.role_level >= 50

    # ──────────────────────────────────────────
    # Permissões de workflow (BPMN)
    # ──────────────────────────────────────────
    def can_perform(self, action: str) -> bool:
        """Verifica se o usuário pode executar uma ação do fluxo de trabalho."""
        allowed_roles = self.ROLE_PERMISSIONS.get(action, [])
        return self.resolved_role in allowed_roles

    @property
    def can_distribuir(self):
        return self.can_perform('distribuir')

    @property
    def can_elaborar_peca(self):
        return self.can_perform('elaborar_peca')

    @property
    def can_assinar_despacho(self):
        return self.can_perform('assinar_despacho')

    @property
    def can_avocar(self):
        return self.can_perform('avocar')

    # ──────────────────────────────────────────
    # Permissões de plataforma
    # ──────────────────────────────────────────
    @property
    def can_manage_templates(self):
        """Pode gerenciar templates e prompts (nível >= gerente/70)"""
        return self.role_level >= 70

    @property
    def can_create_document(self):
        """Pode criar documentos (nível >= procurador/60)"""
        return self.role_level >= 60

    @property
    def can_approve_document(self):
        """Pode aprovar documentos (nível >= assessor_gerencial/50)"""
        return self.role_level >= 50

    def get_full_name(self):
        """Retorna nome completo"""
        return f"{self.first_name} {self.last_name}".strip()


class Notification(models.Model):
    """
    Notificações in-app para usuários
    """
    TYPE_CHOICES = [
        ('deadline', 'Prazo Judicial'),
        ('document', 'Documento'),
        ('case', 'Caso'),
        ('case_update', 'Atualização de Caso'),
        ('system', 'Sistema'),
        ('simulation', 'Simulação'),
        ('task', 'Tarefa'),
        ('contract', 'Contrato'),
        ('message', 'Mensagem'),
        ('compliance', 'Conformidade / LGPD'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Baixa'),
        ('medium', 'Média'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]
    ACTION_TYPE_CHOICES = [
        ('navigate', 'Navegar'),
        ('copilot', 'Abrir Copilot'),
        ('action', 'Ação'),
        ('info', 'Informativo'),
        ('action_required', 'Ação Necessária'),
    ]
    SOURCE_CHOICES = [
        ('system', 'Sistema'),
        ('copilot', 'Copilot'),
        ('user', 'Usuário'),
        ('cron', 'Tarefa Agendada'),
        ('portal', 'Portal do Cliente'),
        ('escritorio', 'Escritório'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Usuário',
    )
    type = models.CharField('Tipo', max_length=20, choices=TYPE_CHOICES)
    priority = models.CharField(
        'Prioridade', max_length=10, choices=PRIORITY_CHOICES, default='medium'
    )
    title = models.CharField('Título', max_length=300)
    message = models.TextField('Mensagem')
    link = models.CharField('Link', max_length=500, blank=True)
    is_read = models.BooleanField('Lida', default=False)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    # Copilot integration fields
    copilot_prompt = models.TextField(
        'Prompt do Copilot', blank=True, default='',
        help_text='Prompt pré-preenchido para o Copilot quando o usuário clicar',
    )
    action_type = models.CharField(
        'Tipo de Ação', max_length=20, choices=ACTION_TYPE_CHOICES,
        default='navigate',
        help_text='O que acontece quando o usuário clica na notificação',
    )
    source = models.CharField(
        'Origem', max_length=10, choices=SOURCE_CHOICES,
        default='system',
        help_text='Quem gerou a notificação',
    )
    metadata = models.JSONField(
        'Metadados', default=dict, blank=True,
        help_text='Dados extras de contexto',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'

    def __str__(self):
        return f'[{self.get_type_display()}] {self.title}'


class UserReminder(models.Model):
    """User-created reminders and recurring tasks"""
    FREQUENCY_CHOICES = [
        ('once', 'Uma vez'),
        ('daily', 'Diário'),
        ('weekly', 'Semanal'),
        ('biweekly', 'Quinzenal'),
        ('monthly', 'Mensal'),
        ('quarterly', 'Trimestral'),
        ('yearly', 'Anual'),
        ('custom', 'Personalizado'),
    ]
    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('paused', 'Pausado'),
        ('completed', 'Concluído'),
        ('cancelled', 'Cancelado'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Baixa'),
        ('medium', 'Média'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reminders',
        verbose_name='Usuário',
    )
    title = models.CharField('Título', max_length=300)
    description = models.TextField('Descrição', blank=True)

    # Scheduling
    frequency = models.CharField(
        'Frequência', max_length=20, choices=FREQUENCY_CHOICES, default='once',
    )
    scheduled_date = models.DateTimeField('Data agendada')
    end_date = models.DateTimeField('Data de término', null=True, blank=True)
    custom_interval_days = models.IntegerField(
        'Intervalo personalizado (dias)', null=True, blank=True,
    )

    # Context
    related_case = models.ForeignKey(
        'cases.LegalCase', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reminders', verbose_name='Caso relacionado',
    )
    copilot_prompt = models.TextField(
        'Prompt do Copilot', blank=True,
        help_text='Prompt pré-preenchido para o Copilot quando o lembrete disparar',
    )
    link = models.CharField('Link direto', max_length=500, blank=True)

    # Status
    status = models.CharField(
        'Status', max_length=20, choices=STATUS_CHOICES, default='active',
    )
    last_triggered = models.DateTimeField('Último disparo', null=True, blank=True)
    trigger_count = models.IntegerField('Disparos', default=0)

    # Notification preferences
    notify_before_minutes = models.IntegerField(
        'Notificar antes (minutos)', default=30,
    )
    priority = models.CharField(
        'Prioridade', max_length=10, choices=PRIORITY_CHOICES, default='medium',
    )

    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        ordering = ['scheduled_date']
        verbose_name = 'Lembrete'
        verbose_name_plural = 'Lembretes'

    def __str__(self):
        return f'[{self.get_frequency_display()}] {self.title}'


class BrandSettings(models.Model):
    """
    Configurações de identidade visual do sistema (Singleton)
    Apenas um registro deve existir
    """
    # Nome e descrição
    system_name = models.CharField(
        'Nome do Sistema',
        max_length=100,
        default='Verus.AI',
        help_text='Nome exibido no sistema'
    )
    system_tagline = models.CharField(
        'Tagline',
        max_length=255,
        blank=True,
        help_text='Descrição curta do sistema'
    )

    # Logos e ícones
    logo = models.ImageField(
        'Logo',
        upload_to='brand/',
        blank=True,
        null=True,
        help_text='Logo principal (PNG, SVG, JPG - recomendado 200x60px)'
    )
    logo_dark = models.ImageField(
        'Logo Dark Mode',
        upload_to='brand/',
        blank=True,
        null=True,
        help_text='Logo para tema escuro (opcional)'
    )
    favicon = models.ImageField(
        'Favicon',
        upload_to='brand/',
        blank=True,
        null=True,
        help_text='Ícone do navegador (.ico, .png - 32x32px ou 64x64px)'
    )

    # Cores
    primary_color = models.CharField(
        'Cor Primária',
        max_length=7,
        default='#7030A0',
        help_text='Cor principal em hexadecimal (ex: #7030A0)'
    )
    secondary_color = models.CharField(
        'Cor Secundária',
        max_length=7,
        default='#5B2EE0',
        help_text='Cor secundária em hexadecimal (ex: #5B2EE0)'
    )
    accent_color = models.CharField(
        'Cor de Destaque',
        max_length=7,
        default='#8B5CF6',
        help_text='Cor para destaques e ações (ex: #8B5CF6)'
    )

    # Metadata
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='brand_settings_updates',
        verbose_name='Atualizado por'
    )

    class Meta:
        verbose_name = 'Configuração de Marca'
        verbose_name_plural = 'Configurações de Marca'

    def __str__(self):
        return f"Configurações de Marca - {self.system_name}"

    def save(self, *args, **kwargs):
        """Garante que só existe um registro (Singleton)"""
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Previne deleção do registro singleton"""
        pass

    @classmethod
    def load(cls):
        """Retorna a instância única ou cria uma nova com valores padrão"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class NotificationChannel(models.Model):
    """User notification channel preferences"""
    CHANNEL_CHOICES = [
        ('email', 'E-mail'),
        ('whatsapp', 'WhatsApp'),
        ('app', 'Aplicação'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_channels',
        verbose_name='Usuário',
    )
    channel = models.CharField(
        'Canal', max_length=20, choices=CHANNEL_CHOICES,
    )
    is_active = models.BooleanField('Ativo', default=True)
    auto_send = models.BooleanField(
        'Envio Automático', default=False,
        help_text='Se ativado, notificações são enviadas automaticamente via Celery. '
                  'Se desativado, o usuário envia manualmente clicando no botão.',
    )

    # WhatsApp specific
    whatsapp_number = models.CharField(
        'Número WhatsApp', max_length=20, blank=True,
        help_text='Formato: +5521999998888',
    )
    whatsapp_verified = models.BooleanField('WhatsApp Verificado', default=False)

    # Email specific
    email_address = models.EmailField(
        'E-mail de Notificação', blank=True,
        help_text='Pode diferir do e-mail principal do usuário',
    )

    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        unique_together = ['user', 'channel']
        verbose_name = 'Canal de Notificação'
        verbose_name_plural = 'Canais de Notificação'

    def __str__(self):
        return f'{self.user} - {self.get_channel_display()}'


class NotificationMessage(models.Model):
    """Sent notification record"""
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('sent', 'Enviado'),
        ('failed', 'Falhou'),
        ('clicked', 'Clicado'),
    ]

    notification = models.ForeignKey(
        Notification, on_delete=models.CASCADE,
        related_name='messages', null=True, blank=True,
        verbose_name='Notificação',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_messages',
        verbose_name='Usuário',
    )
    channel = models.CharField('Canal', max_length=20)
    subject = models.CharField('Assunto', max_length=500, blank=True)
    body = models.TextField('Corpo da mensagem')
    whatsapp_link = models.URLField('Link WhatsApp', blank=True)
    status = models.CharField(
        'Status', max_length=20, choices=STATUS_CHOICES, default='pending',
    )
    sent_at = models.DateTimeField('Enviado em', null=True, blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Mensagem de Notificação'
        verbose_name_plural = 'Mensagens de Notificação'

    def __str__(self):
        return f'[{self.channel}] {self.subject or self.body[:50]}'


# ──────────────────────────────────────────────────────────────
# LGPD Models
# ──────────────────────────────────────────────────────────────

class ConsentTerm(models.Model):
    """Termo de consentimento LGPD"""
    PURPOSE_CHOICES = [
        ('data_processing', 'Tratamento de dados'),
        ('marketing', 'Marketing'),
        ('sharing', 'Compartilhamento de dados'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField('Titulo', max_length=300)
    version = models.CharField('Versao', max_length=20)
    content = models.TextField('Conteudo', help_text='HTML do termo')
    purpose = models.CharField(
        'Finalidade', max_length=100, choices=PURPOSE_CHOICES, default='data_processing',
    )
    is_active = models.BooleanField('Ativo', default=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='consent_terms_created', verbose_name='Criado por',
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Termo de Consentimento'
        verbose_name_plural = 'Termos de Consentimento'

    def __str__(self):
        return f'{self.title} v{self.version}'


class ConsentRecord(models.Model):
    """Registro de consentimento de um cliente"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(
        'cases.Client', on_delete=models.CASCADE, related_name='consents',
        verbose_name='Cliente',
    )
    consent_term = models.ForeignKey(
        ConsentTerm, on_delete=models.CASCADE, related_name='records',
        verbose_name='Termo de Consentimento',
    )
    granted = models.BooleanField('Concedido', default=True)
    ip_address = models.GenericIPAddressField('Endereco IP', null=True, blank=True)
    granted_at = models.DateTimeField('Concedido em', auto_now_add=True)
    revoked_at = models.DateTimeField('Revogado em', null=True, blank=True)

    class Meta:
        ordering = ['-granted_at']
        verbose_name = 'Registro de Consentimento'
        verbose_name_plural = 'Registros de Consentimento'

    def __str__(self):
        status = 'Concedido' if self.granted else 'Revogado'
        return f'{self.client} - {self.consent_term.title} ({status})'


class DataProcessingActivity(models.Model):
    """Atividade de tratamento de dados pessoais (RIPD)"""
    LEGAL_BASIS_CHOICES = [
        ('consent', 'Consentimento'),
        ('contract', 'Execucao de contrato'),
        ('legal_obligation', 'Obrigacao legal'),
        ('legitimate_interest', 'Interesse legitimo'),
        ('judicial_process', 'Exercicio regular de direito em processo'),
        ('life_protection', 'Protecao da vida'),
        ('public_policy', 'Politicas publicas'),
    ]
    RISK_CHOICES = [
        ('baixo', 'Baixo'),
        ('medio', 'Medio'),
        ('alto', 'Alto'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Nome', max_length=300)
    purpose = models.TextField('Finalidade')
    legal_basis = models.CharField(
        'Base legal', max_length=100, choices=LEGAL_BASIS_CHOICES,
    )
    data_categories = models.JSONField(
        'Categorias de dados', default=list, blank=True,
    )
    retention_period = models.CharField('Periodo de retencao', max_length=100)
    shared_with = models.JSONField(
        'Compartilhado com', default=list, blank=True,
    )
    risk_level = models.CharField(
        'Nivel de risco', max_length=20, choices=RISK_CHOICES, default='baixo',
    )
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Atividade de Tratamento de Dados'
        verbose_name_plural = 'Atividades de Tratamento de Dados'

    def __str__(self):
        return self.name


class DataSubjectRequest(models.Model):
    """Solicitacao do titular de dados (DSR)"""
    REQUEST_TYPE_CHOICES = [
        ('access', 'Acesso aos dados'),
        ('rectification', 'Retificacao'),
        ('deletion', 'Eliminacao'),
        ('portability', 'Portabilidade'),
        ('objection', 'Oposicao'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('in_progress', 'Em andamento'),
        ('completed', 'Concluida'),
        ('rejected', 'Rejeitada'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(
        'cases.Client', on_delete=models.CASCADE, related_name='dsr_requests',
        verbose_name='Cliente',
    )
    request_type = models.CharField(
        'Tipo de solicitacao', max_length=30, choices=REQUEST_TYPE_CHOICES,
    )
    description = models.TextField('Descricao')
    status = models.CharField(
        'Status', max_length=20, choices=STATUS_CHOICES, default='pending',
    )
    response = models.TextField('Resposta', blank=True)
    requested_at = models.DateTimeField('Solicitado em', auto_now_add=True)
    responded_at = models.DateTimeField('Respondido em', null=True, blank=True)

    class Meta:
        ordering = ['-requested_at']
        verbose_name = 'Solicitacao do Titular'
        verbose_name_plural = 'Solicitacoes do Titular'

    def __str__(self):
        return f'{self.client} - {self.get_request_type_display()} ({self.get_status_display()})'


# ──────────────────────────────────────────────────────────────
# GESTÃO DE EQUIPE
# ──────────────────────────────────────────────────────────────

class Team(models.Model):
    """Equipe de trabalho do escritório."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name='Nome da Equipe')
    description = models.TextField(blank=True, verbose_name='Descrição')
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='teams_leading',
        verbose_name='Líder',
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='teams', blank=True,
        verbose_name='Membros',
    )
    specialty = models.CharField(max_length=50, blank=True, verbose_name='Especialidade')
    is_active = models.BooleanField(default=True, verbose_name='Ativa')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Equipe'
        verbose_name_plural = 'Equipes'
        ordering = ['name']

    def __str__(self):
        return self.name


class TeamAssignment(models.Model):
    """Atribuição de equipe a um caso jurídico."""
    ROLE_CHOICES = [
        ('responsavel', 'Responsável'),
        ('auxiliar', 'Auxiliar'),
        ('membro', 'Membro'),
        ('revisor', 'Revisor'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name='assignments',
        verbose_name='Equipe',
    )
    case = models.ForeignKey(
        'cases.LegalCase', on_delete=models.CASCADE, related_name='team_assignments',
        verbose_name='Caso',
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        verbose_name='Atribuído por',
    )
    role_in_case = models.CharField(
        max_length=50, default='membro', choices=ROLE_CHOICES,
        verbose_name='Papel no Caso',
    )
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name='Atribuído em')

    class Meta:
        verbose_name = 'Atribuição de Equipe'
        verbose_name_plural = 'Atribuições de Equipe'
        unique_together = ['team', 'case']

    def __str__(self):
        return f'{self.team.name} → {self.case} ({self.get_role_in_case_display()})'


# ──────────────────────────────────────────────────────────────
# DASHBOARD CUSTOMIZÁVEL (#24)
# ──────────────────────────────────────────────────────────────

class DashboardConfig(models.Model):
    """Configuração personalizada do dashboard por usuário."""

    THEME_CHOICES = [
        ('default', 'Padrão'),
        ('compact', 'Compacto'),
        ('detailed', 'Detalhado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboard_config',
        verbose_name='Usuário',
    )
    layout = models.JSONField(
        default=list,
        help_text='Lista de widgets: [{id, type, position, size, config}]',
        verbose_name='Layout',
    )
    theme = models.CharField(
        max_length=20,
        default='default',
        choices=THEME_CHOICES,
        verbose_name='Tema',
    )
    auto_refresh = models.BooleanField(
        default=True,
        verbose_name='Auto-refresh',
    )
    refresh_interval = models.IntegerField(
        default=300,
        help_text='Intervalo em segundos',
        verbose_name='Intervalo de atualização',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Configuração do Dashboard'
        verbose_name_plural = 'Configurações do Dashboard'

    def __str__(self):
        return f'Dashboard de {self.user}'


# ──────────────────────────────────────────────────────────────
# TEMPLATES DE E-MAIL (#19)
# ──────────────────────────────────────────────────────────────

class EmailTemplate(models.Model):
    """Template de e-mail reutilizável com suporte a variáveis."""

    CATEGORY_CHOICES = [
        ('notification', 'Notificação'),
        ('deadline', 'Prazo'),
        ('client', 'Cliente'),
        ('billing', 'Cobrança'),
        ('general', 'Geral'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name='Nome')
    subject = models.CharField(max_length=300, verbose_name='Assunto')
    body_html = models.TextField(verbose_name='Corpo HTML')
    category = models.CharField(
        max_length=50, choices=CATEGORY_CHOICES, default='general',
        verbose_name='Categoria',
    )
    variables = models.JSONField(
        default=list,
        help_text='Lista de variáveis disponíveis: [{name, description}]',
    )
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='email_templates',
        verbose_name='Criado por',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Template de E-mail'
        verbose_name_plural = 'Templates de E-mail'
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class ClientMessage(models.Model):
    """Comunicação entre parte/interessado e servidor via portal."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(
        'cases.Client', on_delete=models.CASCADE, related_name='messages',
        verbose_name='Parte / Interessado',
    )
    case = models.ForeignKey(
        'cases.LegalCase', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='client_messages', verbose_name='Processo',
    )
    sender_type = models.CharField(
        'Tipo de Remetente', max_length=10,
        choices=[('client', 'Parte / Interessado'), ('lawyer', 'Servidor Público')],
    )
    sender_name = models.CharField('Nome do Remetente', max_length=200)
    content = models.TextField('Conteudo')
    is_read = models.BooleanField('Lida', default=False)
    attachment = models.FileField(
        'Anexo', upload_to='client_messages/', null=True, blank=True,
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Comunicação da Parte'
        verbose_name_plural = 'Comunicações das Partes'

    def __str__(self):
        return f'{self.sender_name} ({self.sender_type}) — {self.created_at}'
