"""
Models para RAG (Retrieval-Augmented Generation)
"""
import uuid
from django.db import models
from django.conf import settings


class RAGQuery(models.Model):
    """
    Registro de consultas RAG realizadas
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relações
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rag_queries',
        verbose_name='Usuário'
    )
    etp = models.ForeignKey(
        'documents.Document',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='rag_queries',
        verbose_name='ETP Relacionado'
    )

    # Query
    query_text = models.TextField('Texto da Consulta')
    query_embedding = models.JSONField(
        'Embedding da Consulta', null=True, blank=True)

    # Parâmetros da busca
    top_k = models.IntegerField('Top K Resultados', default=5)
    similarity_threshold = models.FloatField(
        'Threshold de Similaridade', default=0.7)

    # Filtros aplicados
    filter_categories = models.JSONField(
        'Categorias Filtradas', default=list, blank=True)
    filter_tags = models.JSONField('Tags Filtradas', default=list, blank=True)

    # Resultados
    retrieved_chunks = models.JSONField(
        'Chunks Recuperados', default=list, blank=True)
    chunk_count = models.IntegerField('Quantidade de Chunks', default=0)

    # Response do LLM
    llm_response = models.TextField('Resposta do LLM', blank=True)
    llm_provider = models.CharField('Provedor LLM', max_length=50, blank=True)
    llm_model = models.CharField('Modelo LLM', max_length=100, blank=True)

    # Métricas
    search_time_ms = models.IntegerField(
        'Tempo de Busca (ms)', null=True, blank=True)
    llm_time_ms = models.IntegerField('Tempo LLM (ms)', null=True, blank=True)
    total_tokens = models.IntegerField(
        'Total de Tokens', null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Consulta RAG'
        verbose_name_plural = 'Consultas RAG'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['etp']),
        ]

    def __str__(self):
        return f"RAG Query: {self.query_text[:50]}..."


class RAGContext(models.Model):
    """
    Contextos salvos para uso em futuras queries
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relações
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rag_contexts',
        verbose_name='Usuário'
    )
    etp = models.ForeignKey(
        'documents.Document',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='rag_contexts',
        verbose_name='ETP Relacionado'
    )

    # Context data
    name = models.CharField('Nome do Contexto', max_length=255)
    description = models.TextField('Descrição', blank=True)

    # Documentos relacionados
    documents = models.ManyToManyField(
        'kb.Document',
        related_name='rag_contexts',
        verbose_name='Documentos',
        blank=True
    )

    # Configurações de busca
    default_top_k = models.IntegerField('Top K Padrão', default=5)
    default_threshold = models.FloatField('Threshold Padrão', default=0.7)

    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Contexto RAG'
        verbose_name_plural = 'Contextos RAG'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return self.name
