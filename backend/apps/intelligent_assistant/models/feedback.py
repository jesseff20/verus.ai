"""
Modelos de feedback do usuário sobre seções geradas.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class SectionFeedback(models.Model):
    """
    Feedback do usuário sobre seções geradas.

    Permite:
    - Avaliar seções com nota de 1 a 5 estrelas
    - Editar conteúdo de seções
    - Salvar melhorias para KB de auto-aprendizagem
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relacionamentos
    session = models.ForeignKey(
        'intelligent_assistant.IntelligentSession',
        on_delete=models.CASCADE,
        related_name='section_feedbacks',
        verbose_name='Sessão'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='section_feedbacks',
        verbose_name='Usuário'
    )

    # Identificação da seção
    section_number = models.IntegerField(verbose_name='Número da Seção')
    section_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Nome da Seção'
    )

    # Conteúdo
    original_content = models.TextField(
        verbose_name='Conteúdo Original',
        help_text='Conteúdo gerado pela IA'
    )
    edited_content = models.TextField(
        verbose_name='Conteúdo Editado',
        help_text='Conteúdo após edição do usuário'
    )

    # Avaliação
    user_rating = models.IntegerField(
        verbose_name='Avaliação do Usuário',
        help_text='Nota de 1 a 5 estrelas'
    )
    ai_score = models.FloatField(
        verbose_name='Score da IA',
        help_text='Score original da validação da IA (0-100)'
    )

    # Metadados
    edit_reason = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Motivo da Edição'
    )
    is_improvement = models.BooleanField(
        default=False,
        verbose_name='É Melhoria',
        help_text='True se o conteúdo editado é diferente do original'
    )
    is_approved = models.BooleanField(
        default=False,
        verbose_name='Aprovado para KB',
        help_text='Admin aprovou para usar em KB de melhorias'
    )
    embedding_created = models.BooleanField(
        default=False,
        verbose_name='Embedding Criado',
        help_text='Indica se o embedding foi criado na KB'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        app_label = 'intelligent_assistant'
        verbose_name = 'Feedback de Seção'
        verbose_name_plural = 'Feedbacks de Seções'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session', 'section_number']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['is_approved']),
        ]

    def __str__(self):
        return f"Feedback: Seção {self.section_number} - {self.user.email} ({self.user_rating}★)"

    def save(self, *args, **kwargs):
        # Detectar se é uma melhoria (conteúdo foi editado)
        self.is_improvement = self.original_content != self.edited_content
        super().save(*args, **kwargs)
