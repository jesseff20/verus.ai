"""
CopilotConfig — Configuração global do Copilot (singleton).

Um único registro no banco controla prompt, modelo, temperatura e
limites. Editável pelo admin sem necessidade de redeploy.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from apps.core.constants import LLM_PROVIDER_CHOICES


class CopilotConfig(models.Model):
    """
    Configuração singleton do Copilot.
    Só pode existir um registro (id=1). Admin bloqueia criação e deleção.
    """

    # ── Identidade ───────────────────────────────────────────────────────────
    name = models.CharField(
        max_length=100,
        default='Copilot Verus.AI',
        verbose_name='Nome do assistente',
        help_text='Nome exibido na interface do Copilot.',
    )

    # ── Prompt ───────────────────────────────────────────────────────────────
    system_prompt = models.TextField(
        verbose_name='System Prompt',
        help_text=(
            'Instruções de comportamento do assistente. '
            'Use linguagem direta: "Você é...", "Você deve...", "NÃO faça...". '
            'O contexto de KB é injetado automaticamente após este prompt.'
        ),
    )

    # ── Modelo LLM ───────────────────────────────────────────────────────────
    provider = models.CharField(
        max_length=20,
        choices=LLM_PROVIDER_CHOICES,
        default='watsonx',
        verbose_name='Provider',
        help_text='Provedor de IA. As credenciais são gerenciadas em Core › Provedores LLM.',
    )

    model = models.CharField(
        max_length=100,
        default='meta-llama/llama-3-3-70b-instruct',
        verbose_name='ID do modelo',
        help_text=(
            'Exemplos: meta-llama/llama-3-3-70b-instruct, '
            'ibm/granite-3-3-8b-instruct, gpt-4o.'
        ),
    )

    # ── Parâmetros de geração ─────────────────────────────────────────────────
    temperature = models.FloatField(
        default=0.7,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name='Temperatura',
        help_text='Criatividade das respostas. 0 = determinístico, 1 = mais criativo. Recomendado: 0.5–0.8.',
    )

    max_tokens = models.PositiveIntegerField(
        default=4096,
        validators=[MinValueValidator(256), MaxValueValidator(16384)],
        verbose_name='Máx. tokens de saída',
        help_text='Limite de tokens gerados por resposta. Padrão: 4096.',
    )

    max_kb_results = models.PositiveIntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        verbose_name='Resultados da KB',
        help_text='Quantidade de chunks buscados na Base de Conhecimento por mensagem. Padrão: 10.',
    )

    # ── Status ────────────────────────────────────────────────────────────────
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo',
        help_text='Se desativado, o Copilot retorna erro ao tentar conversar.',
    )

    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última atualização')

    class Meta:
        verbose_name = 'Configuração do Copilot'
        verbose_name_plural = 'Configuração do Copilot'

    def __str__(self):
        return f'{self.name} ({self.provider} / {self.model})'

    def clean(self):
        # Garante que só existe uma instância
        if not self.pk and CopilotConfig.objects.exists():
            raise ValidationError(
                'Já existe uma configuração do Copilot. Edite o registro existente.'
            )

    @classmethod
    def get_config(cls):
        """
        Retorna a configuração ativa.
        Cria o registro padrão automaticamente se não existir (first run).
        """
        config = cls.objects.first()
        if config is None:
            from .services.chat_service import COPILOT_SYSTEM_PROMPT, COPILOT_MODEL, COPILOT_PROVIDER
            config = cls.objects.create(
                system_prompt=COPILOT_SYSTEM_PROMPT,
                provider=COPILOT_PROVIDER,
                model=COPILOT_MODEL,
            )
        return config


class UserKnowledgeEntry(models.Model):
    """Per-user vectorized knowledge entry for Copilot context."""

    CATEGORY_CHOICES = [
        ('case', 'Caso Jurídico'),
        ('document', 'Documento'),
        ('deadline', 'Prazo'),
        ('client', 'Cliente'),
        ('session', 'Sessão de Geração'),
        ('simulation', 'Simulação'),
        ('reminder', 'Lembrete'),
        ('activity', 'Atividade'),
    ]

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='knowledge_entries',
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=500)
    content = models.TextField()  # The actual text content to embed

    # Context metadata
    source_model = models.CharField(max_length=100)  # e.g., 'cases.LegalCase'
    source_id = models.CharField(max_length=100)  # UUID of the source object
    context_date = models.DateField()  # When the source data was created/updated

    # Embedding (pgvector)
    embedding = models.JSONField(null=True, blank=True)  # Store as JSON array

    # Sync metadata
    last_synced = models.DateTimeField(auto_now=True)
    content_hash = models.CharField(max_length=64)  # SHA256 of content to detect changes

    class Meta:
        verbose_name = 'Entrada de Conhecimento do Usuário'
        verbose_name_plural = 'Entradas de Conhecimento dos Usuários'
        ordering = ['-context_date']
        indexes = [
            models.Index(fields=['user', 'category']),
            models.Index(fields=['user', 'source_model', 'source_id']),
        ]
        unique_together = ['user', 'source_model', 'source_id']

    def __str__(self):
        return f'{self.get_category_display()}: {self.title} ({self.user})'


class UserKnowledgeSyncLog(models.Model):
    """Tracks sync runs per user."""

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='knowledge_sync_logs',
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    entries_created = models.IntegerField(default=0)
    entries_updated = models.IntegerField(default=0)
    entries_unchanged = models.IntegerField(default=0)
    errors = models.JSONField(default=list)
    status = models.CharField(max_length=20, default='running')  # running, completed, failed

    class Meta:
        verbose_name = 'Log de Sincronização de Conhecimento'
        verbose_name_plural = 'Logs de Sincronização de Conhecimento'
        ordering = ['-started_at']

    def __str__(self):
        return f'Sync {self.user} - {self.started_at} ({self.status})'


class CopilotSessionShare(models.Model):
    """
    Compartilhamento de sessões do Copilot.
    Permite compartilhar conversas com outros usuários via link seguro.
    """
    session_id = models.CharField(max_length=36)  # UUID da sessão
    share_code = models.CharField(max_length=12, unique=True)  # Código curto para compartilhamento
    created_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='shared_sessions')
    shared_with_emails = models.JSONField(default=list, blank=True)  # Emails dos usuários com acesso
    is_public = models.BooleanField(default=False)  # Se True, qualquer um com o código pode acessar
    expires_at = models.DateTimeField(null=True, blank=True)  # Expiração opcional
    access_count = models.IntegerField(default=0)  # Contador de acessos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Sessão Compartilhada'
        verbose_name_plural = 'Sessões Compartilhadas'
        ordering = ['-created_at']

    def __str__(self):
        return f'Sessão {self.session_id[:8]}... compartilhada por {self.created_by.email}'

    @classmethod
    def generate_share_code(cls):
        """Gera código de compartilhamento único"""
        import secrets
        import string
        chars = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(chars) for _ in range(8))

    def is_expired(self):
        """Verifica se o compartilhamento expirou"""
        if not self.expires_at:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at
