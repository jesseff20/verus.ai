"""
Models para Colaboração em Tempo Real.

Funcionalidades:
- Sessões de edição colaborativa
- Presença de usuários em tempo real
- Histórico de operações (OT/CRDT)
- Comentários e discussões
"""

import uuid
from django.db import models
from django.conf import settings


class CollaborationSession(models.Model):
    """
    Sessão de edição colaborativa.

    Representa um documento sendo editado por múltiplos usuários
    em tempo real.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Documento associado
    document_id = models.UUIDField(
        'ID do Documento',
        help_text='ID do documento sendo editado'
    )
    document_type = models.CharField(
        'Tipo de Documento',
        max_length=50,
        choices=[
            ('legal', 'Documento Jurídico'),
            ('contract', 'Contrato'),
            ('petition', 'Petição'),
            ('brief', 'Memorando'),
        ],
        default='legal'
    )

    # Status
    status = models.CharField(
        'Status',
        max_length=20,
        choices=[
            ('active', 'Ativa'),
            ('paused', 'Pausada'),
            ('completed', 'Completa'),
            ('abandoned', 'Abandonada'),
        ],
        default='active'
    )

    # Criador/owner
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='collaboration_sessions',
        verbose_name='Criado por'
    )

    # Configurações
    allow_comments = models.BooleanField('Permitir Comentários', default=True)
    allow_suggestions = models.BooleanField('Permitir Sugestões', default=True)
    max_collaborators = models.IntegerField(
        'Máximo de Colaboradores',
        default=10,
        help_text='Limite de usuários simultâneos'
    )

    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    last_activity_at = models.DateTimeField('Última atividade em', null=True, blank=True)
    expires_at = models.DateTimeField('Expira em', null=True, blank=True)

    class Meta:
        verbose_name = 'Sessão de Colaboração'
        verbose_name_plural = 'Sessões de Colaboração'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document_id', 'status']),
            models.Index(fields=['-last_activity_at']),
        ]

    def __str__(self):
        return f'Sessão {str(self.id)[:8]} - {self.document_type}'

    def is_active(self):
        """Verifica se sessão está ativa"""
        return self.status == 'active'


class CollaboratorPresence(models.Model):
    """
    Presença de um usuário em uma sessão colaborativa.

    Atualizada via heartbeat para detectar usuários ativos.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Sessão
    session = models.ForeignKey(
        CollaborationSession,
        on_delete=models.CASCADE,
        related_name='presences',
        verbose_name='Sessão'
    )

    # Usuário
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='collaboration_presences',
        verbose_name='Usuário'
    )

    # Status
    status = models.CharField(
        'Status',
        max_length=20,
        choices=[
            ('editing', 'Editando'),
            ('viewing', 'Visualizando'),
            ('commenting', 'Comentando'),
            ('away', 'Ausente'),
        ],
        default='viewing'
    )

    # Cursor/posição
    cursor_position = models.IntegerField(
        'Posição do Cursor',
        default=0,
        help_text='Posição atual do cursor no documento'
    )
    selected_section = models.CharField(
        'Seção Selecionada',
        max_length=100,
        blank=True,
        help_text='ID da seção que o usuário está visualizando/editando'
    )

    # Heartbeat
    last_heartbeat = models.DateTimeField('Último heartbeat', auto_now=True)
    joined_at = models.DateTimeField('Entrou em', auto_now_add=True)
    left_at = models.DateTimeField('Saiu em', null=True, blank=True)

    class Meta:
        verbose_name = 'Presença de Colaborador'
        verbose_name_plural = 'Presenças de Colaboradores'
        ordering = ['-joined_at']
        unique_together = [['session', 'user']]
        indexes = [
            models.Index(fields=['session', 'status']),
            models.Index(fields=['last_heartbeat']),
        ]

    def __str__(self):
        return f'{self.user.username} em {self.session}'

    def is_active(self):
        """Verifica se usuário está ativo (heartbeat nos últimos 30s)"""
        from django.utils import timezone
        from datetime import timedelta
        return self.last_heartbeat > (timezone.now() - timedelta(seconds=30))


class OperationLog(models.Model):
    """
    Log de operações para Operational Transformation (OT).

    Armazena cada edição feita para sincronização e replay.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Sessão
    session = models.ForeignKey(
        CollaborationSession,
        on_delete=models.CASCADE,
        related_name='operations',
        verbose_name='Sessão'
    )

    # Usuário que fez a operação
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='collaboration_operations',
        verbose_name='Usuário'
    )

    # Tipo de operação
    operation_type = models.CharField(
        'Tipo de Operação',
        max_length=20,
        choices=[
            ('insert', 'Inserir'),
            ('delete', 'Deletar'),
            ('replace', 'Substituir'),
            ('format', 'Formatar'),
            ('move', 'Mover'),
        ],
        default='insert'
    )

    # Dados da operação
    section_id = models.CharField(
        'ID da Seção',
        max_length=100,
        blank=True,
        help_text='Seção onde a operação ocorreu'
    )
    position = models.IntegerField(
        'Posição',
        default=0,
        help_text='Posição onde a operação ocorreu'
    )
    length = models.IntegerField(
        'Tamanho',
        default=0,
        help_text='Tamanho do texto afetado'
    )
    content = models.TextField(
        'Conteúdo',
        blank=True,
        help_text='Conteúdo inserido/substituído'
    )

    # Versionamento para OT
    version = models.IntegerField(
        'Versão',
        default=1,
        help_text='Versão do documento após esta operação'
    )
    parent_version = models.IntegerField(
        'Versão Pai',
        default=0,
        help_text='Versão do documento antes desta operação'
    )

    # Timestamp
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Log de Operação'
        verbose_name_plural = 'Logs de Operações'
        ordering = ['version']
        indexes = [
            models.Index(fields=['session', 'version']),
            models.Index(fields=['session', '-created_at']),
        ]

    def __str__(self):
        return f'{self.operation_type} v{self.version} por {self.user.username}'


class Comment(models.Model):
    """
    Comentário em um documento colaborativo.

    Pode ser:
    - Comentário geral no documento
    - Comentário em uma seção específica
    - Resposta a outro comentário (thread)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Sessão/documento
    session = models.ForeignKey(
        CollaborationSession,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Sessão'
    )

    # Autor
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='collaboration_comments',
        verbose_name='Autor'
    )

    # Comentário pai (para threads)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='replies',
        null=True,
        blank=True,
        verbose_name='Comentário Pai'
    )

    # Localização
    section_id = models.CharField(
        'ID da Seção',
        max_length=100,
        blank=True,
        help_text='Seção onde o comentário foi feito'
    )
    position_start = models.IntegerField(
        'Posição Inicial',
        default=0,
        help_text='Posição inicial do texto comentado'
    )
    position_end = models.IntegerField(
        'Posição Final',
        default=0,
        help_text='Posição final do texto comentado'
    )
    quoted_text = models.TextField(
        'Texto Citado',
        blank=True,
        help_text='Trecho do documento sendo comentado'
    )

    # Conteúdo
    content = models.TextField('Conteúdo')
    is_resolved = models.BooleanField('Resolvido', default=False)

    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    resolved_at = models.DateTimeField('Resolvido em', null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_comments',
        verbose_name='Resolvido por'
    )

    class Meta:
        verbose_name = 'Comentário'
        verbose_name_plural = 'Comentários'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['session', 'is_resolved']),
            models.Index(fields=['parent', '-created_at']),
        ]

    def __str__(self):
        return f'Comentário por {self.author.username} em {self.created_at.strftime("%d/%m/%Y")}'


class Suggestion(models.Model):
    """
    Sugestão de alteração em um documento.

    Similar ao "modo de sugestão" do Google Docs.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Sessão
    session = models.ForeignKey(
        CollaborationSession,
        on_delete=models.CASCADE,
        related_name='suggestions',
        verbose_name='Sessão'
    )

    # Autor
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='collaboration_suggestions',
        verbose_name='Autor'
    )

    # Localização
    section_id = models.CharField(
        'ID da Seção',
        max_length=100,
        blank=True
    )

    # Conteúdo sugerido
    original_text = models.TextField('Texto Original')
    suggested_text = models.TextField('Texto Sugerido')

    # Status
    status = models.CharField(
        'Status',
        max_length=20,
        choices=[
            ('pending', 'Pendente'),
            ('accepted', 'Aceita'),
            ('rejected', 'Rejeitada'),
            ('modified', 'Modificada'),
        ],
        default='pending'
    )

    # Justificativa
    comment = models.TextField('Comentário/Justificativa', blank=True)

    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    reviewed_at = models.DateTimeField('Revisado em', null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_suggestions',
        verbose_name='Revisado por'
    )

    class Meta:
        verbose_name = 'Sugestão'
        verbose_name_plural = 'Sugestões'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session', 'status']),
        ]

    def __str__(self):
        return f'Sugestão por {self.author.username} - {self.status}'
