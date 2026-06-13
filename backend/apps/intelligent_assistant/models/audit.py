"""
Modelos de auditoria de chamadas LLM.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class LLMAuditLog(models.Model):
    """
    Registro de auditoria para CADA chamada individual ao LLM.

    Registra consumo de tokens, provider/modelo, duração e custo estimado
    para qualquer chamada — geração, validação, regeneração ou avulsa.
    """

    CALL_TYPE_CHOICES = [
        ('generate', 'Geração'),
        ('validate', 'Validação'),
        ('regenerate', 'Regeneração'),
        ('other', 'Outro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Quem
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='llm_audit_logs',
        verbose_name='Usuário'
    )

    # Contexto (todos opcionais — permite chamadas avulsas)
    session = models.ForeignKey(
        'intelligent_assistant.GenerationSession',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='llm_audit_logs',
        verbose_name='Sessão de Geração'
    )
    blueprint = models.ForeignKey(
        'intelligent_assistant.DocumentBlueprint',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='llm_audit_logs',
        verbose_name='Blueprint'
    )
    section_number = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Número da Seção'
    )
    section_name = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='Nome da Seção'
    )

    # Tipo da chamada
    call_type = models.CharField(
        max_length=20,
        choices=CALL_TYPE_CHOICES,
        default='generate',
        verbose_name='Tipo de Chamada'
    )
    attempt_number = models.IntegerField(
        default=1,
        verbose_name='Número da Tentativa'
    )

    # Provider e modelo
    provider = models.CharField(
        max_length=50,
        verbose_name='Provider',
        help_text='watsonx, openai'
    )
    model = models.CharField(
        max_length=100,
        verbose_name='Modelo',
        help_text='Ex: ibm/granite-3-3-8b-instruct, gpt-4o-mini'
    )

    # Tokens
    input_tokens = models.IntegerField(
        default=0,
        verbose_name='Tokens de Entrada'
    )
    output_tokens = models.IntegerField(
        default=0,
        verbose_name='Tokens de Saída'
    )
    total_tokens = models.IntegerField(
        default=0,
        verbose_name='Total de Tokens',
        help_text='input_tokens + output_tokens'
    )

    # Performance
    duration_ms = models.IntegerField(
        default=0,
        verbose_name='Duração (ms)',
        help_text='Tempo de execução da chamada em milissegundos'
    )

    # Custo estimado
    estimated_cost_usd = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=0,
        verbose_name='Custo Estimado (USD)',
        help_text='Custo estimado baseado nos preços do provider/modelo'
    )

    # Timestamp
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data/Hora'
    )

    class Meta:
        app_label = 'intelligent_assistant'
        verbose_name = 'Log de Auditoria LLM'
        verbose_name_plural = 'Logs de Auditoria LLM'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['session']),
            models.Index(fields=['blueprint', '-created_at']),
            models.Index(fields=['provider', 'model']),
            models.Index(fields=['call_type', '-created_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        section_info = f" S{self.section_number}" if self.section_number else ""
        return (
            f"[{self.get_call_type_display()}]{section_info} "
            f"{self.provider}/{self.model} — "
            f"{self.total_tokens} tokens — "
            f"{self.created_at.strftime('%d/%m/%Y %H:%M:%S')}"
        )

    def save(self, *args, **kwargs):
        self.total_tokens = self.input_tokens + self.output_tokens
        self.estimated_cost_usd = self._calculate_cost()
        super().save(*args, **kwargs)

    def _calculate_cost(self):
        """
        Calcula custo estimado baseado nos preços por 1M tokens.
        Preços atualizados em fev/2025 (aproximados).
        """
        PRICING = {
            # provider: {model_prefix: (input_per_1M, output_per_1M)}
            'anthropic': {
                'claude-haiku': (0.25, 1.25),
                'claude-sonnet': (3.00, 15.00),
                'claude-opus': (15.00, 75.00),
                'claude-3-5-haiku': (1.00, 5.00),
                'claude-3-5-sonnet': (3.00, 15.00),
            },
            'openai': {
                'gpt-4o-mini': (0.15, 0.60),
                'gpt-4o': (2.50, 10.00),
                'gpt-4-turbo': (10.00, 30.00),
                'gpt-3.5': (0.50, 1.50),
            },
            'watsonx': {
                'default': (0.50, 1.50),  # Estimativa genérica
            },
        }

        provider_pricing = PRICING.get(self.provider, {})

        # Encontrar preço pelo prefixo do modelo
        input_price = 0.50  # default
        output_price = 1.50
        for prefix, (inp, outp) in provider_pricing.items():
            if self.model.startswith(prefix) or prefix == 'default':
                input_price = inp
                output_price = outp
                break

        cost = (
            (self.input_tokens / 1_000_000) * input_price
            + (self.output_tokens / 1_000_000) * output_price
        )
        return round(cost, 6)
