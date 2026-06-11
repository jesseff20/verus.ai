"""
Modelos para sistema de RLHF e Analytics do Assistente
"""
from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class AssistantConversation(models.Model):
    """Armazena conversas completas com o assistente"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assistant_conversations')
    session_id = models.CharField(max_length=255, db_index=True, help_text="ID da sessão do navegador")

    # Contexto da conversa
    document_type = models.CharField(max_length=100, blank=True, null=True)
    document_id = models.UUIDField(blank=True, null=True, help_text="ID do documento sendo editado")
    current_field = models.CharField(max_length=255, blank=True, null=True)

    # Metadados
    started_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(auto_now=True)
    total_messages = models.IntegerField(default=0)
    total_tokens_used = models.IntegerField(default=0)

    # Analytics
    avg_response_time_ms = models.IntegerField(default=0, help_text="Tempo médio de resposta em ms")
    user_satisfaction_score = models.FloatField(null=True, blank=True, help_text="Score 0-1 baseado em feedbacks")

    class Meta:
        db_table = 'assistant_conversations'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', '-started_at']),
            models.Index(fields=['session_id']),
        ]

    def __str__(self):
        return f"Conversa {self.id} - {self.user.username} - {self.started_at}"


class AssistantMessage(models.Model):
    """Armazena cada mensagem individual da conversa"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        AssistantConversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )

    # Conteúdo da mensagem
    role = models.CharField(
        max_length=20,
        choices=[
            ('user', 'Usuário'),
            ('assistant', 'Assistente'),
            ('system', 'Sistema'),
        ]
    )
    content = models.TextField()

    # Metadados da resposta (quando role=assistant)
    llm_provider = models.CharField(max_length=50, blank=True, null=True)
    model_name = models.CharField(max_length=100, blank=True, null=True)
    tokens_used = models.IntegerField(default=0)
    response_time_ms = models.IntegerField(default=0)

    # RAG (quando usa Base de Conhecimento)
    used_kb = models.BooleanField(default=False, help_text="Se consultou Base de Conhecimento")
    kb_documents_used = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de IDs de documentos da KB usados"
    )
    kb_relevance_scores = models.JSONField(
        default=list,
        blank=True,
        help_text="Scores de relevância dos documentos"
    )

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'assistant_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class AssistantFeedback(models.Model):
    """RLHF - Feedback do usuário sobre respostas do assistente"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(
        AssistantMessage,
        on_delete=models.CASCADE,
        related_name='feedbacks'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Feedback principal
    feedback_type = models.CharField(
        max_length=20,
        choices=[
            ('positive', 'Positivo (👍)'),
            ('negative', 'Negativo (👎)'),
        ]
    )

    # Detalhamento (quando negativo)
    reason = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=[
            ('incorrect', 'Informação incorreta'),
            ('incomplete', 'Resposta incompleta'),
            ('irrelevant', 'Não respondeu a pergunta'),
            ('unclear', 'Resposta confusa'),
            ('outdated', 'Informação desatualizada'),
            ('formatting', 'Formatação ruim'),
            ('other', 'Outro'),
        ]
    )

    # Comentário adicional
    comment = models.TextField(blank=True, null=True)

    # Sugestão de melhoria
    suggested_response = models.TextField(
        blank=True,
        null=True,
        help_text="Resposta sugerida pelo usuário (para fine-tuning)"
    )

    # Metadados
    created_at = models.DateTimeField(auto_now_add=True)

    # Processamento
    processed = models.BooleanField(
        default=False,
        help_text="Se o feedback foi processado para treino"
    )
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'assistant_feedbacks'
        ordering = ['-created_at']
        unique_together = ['message', 'user']  # Um feedback por usuário por mensagem
        indexes = [
            models.Index(fields=['feedback_type', '-created_at']),
            models.Index(fields=['processed', '-created_at']),
        ]

    def __str__(self):
        return f"{self.feedback_type} - {self.message.content[:30]}..."


class AssistantAnalytics(models.Model):
    """Analytics agregados do assistente (daily snapshot)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(unique=True, db_index=True)

    # Métricas de uso
    total_conversations = models.IntegerField(default=0)
    total_messages = models.IntegerField(default=0)
    unique_users = models.IntegerField(default=0)
    avg_messages_per_conversation = models.FloatField(default=0)

    # Métricas de performance
    avg_response_time_ms = models.IntegerField(default=0)
    total_tokens_used = models.IntegerField(default=0)
    total_kb_queries = models.IntegerField(default=0)

    # Métricas de feedback (RLHF)
    total_feedbacks = models.IntegerField(default=0)
    positive_feedbacks = models.IntegerField(default=0)
    negative_feedbacks = models.IntegerField(default=0)
    satisfaction_rate = models.FloatField(
        null=True,
        blank=True,
        help_text="% de feedbacks positivos (null se não houver feedbacks)"
    )

    # Breakdown por tipo de problema (negativos)
    incorrect_count = models.IntegerField(default=0)
    incomplete_count = models.IntegerField(default=0)
    irrelevant_count = models.IntegerField(default=0)
    unclear_count = models.IntegerField(default=0)
    outdated_count = models.IntegerField(default=0)

    # Metadados
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'assistant_analytics'
        ordering = ['-date']

    def __str__(self):
        return f"Analytics {self.date} - {self.total_conversations} conversas"


class AssistantKnowledgeQuery(models.Model):
    """Log de queries na Base de Conhecimento feitas pelo assistente"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(
        AssistantMessage,
        on_delete=models.CASCADE,
        related_name='kb_queries'
    )

    # Query
    query_text = models.TextField()
    query_embedding = models.JSONField(help_text="Embedding da query (opcional)")

    # Resultados
    results_count = models.IntegerField(default=0)
    top_results = models.JSONField(
        default=list,
        help_text="Top 5 documentos retornados com scores"
    )

    # Performance
    query_time_ms = models.IntegerField(default=0)

    # Metadados
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'assistant_kb_queries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['message', '-created_at']),
        ]

    def __str__(self):
        return f"KB Query: {self.query_text[:50]}..."
