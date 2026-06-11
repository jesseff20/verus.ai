"""
Models para Knowledge Base (base de conhecimento)
"""
import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from pgvector.django import VectorField


def validate_document_file(value):
    """Valida extensão do arquivo de documento (suportados pelo Docling)"""
    valid_extensions = [
        '.pdf', '.doc', '.docx', '.xlsx', '.pptx',
        '.csv', '.txt', '.md', '.odt',
        '.html', '.xhtml',
        '.png', '.jpeg', '.jpg', '.tiff', '.bmp', '.webp',
    ]
    import os
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError(f'Extensão inválida. Permitidas: {", ".join(valid_extensions)}')


class Document(models.Model):
    """
    Documento da base de conhecimento
    Armazena PDFs, DOCs, etc que serão processados para RAG
    """
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('completed', 'Processado'),
        ('uploading', 'Enviando Arquivo'),
        ('ready', 'Finalizado'),
        ('failed', 'Falha no Processamento'),
    ]

    CATEGORY_CHOICES = [
        ('manual', 'Manual/Guia'),
        ('lei', 'Lei/Normativa'),
        ('exemplo', 'Exemplo de ETP'),
        ('referencia', 'Material de Referência'),
        ('template', 'Template'),
        ('outros', 'Outros'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField('Título', max_length=255)
    description = models.TextField('Descrição', blank=True)
    category = models.CharField('Categoria', max_length=50, choices=CATEGORY_CHOICES, default='outros')

    # Arquivo original (opcional - upload para R2 pode ocorrer em background)
    file = models.FileField(
        'Arquivo',
        upload_to='kb/documents/',
        validators=[validate_document_file],
        help_text='Upload de PDF, DOC, DOCX, TXT ou MD',
        blank=True,
        null=True,
    )
    file_size = models.BigIntegerField('Tamanho do Arquivo (bytes)', null=True, blank=True)
    file_type = models.CharField('Tipo de Arquivo', max_length=10, blank=True)

    # Texto extraído
    extracted_text = models.TextField('Texto Extraído', blank=True)

    # Processamento
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pending')
    processing_error = models.TextField('Erro no Processamento', blank=True)
    processed_at = models.DateTimeField('Processado em', null=True, blank=True)

    # Metadados
    metadata = models.JSONField(
        'Metadados',
        default=dict,
        blank=True,
        help_text='Metadados extraídos do documento (autor, data, etc)'
    )

    # Tags para categorização
    tags = models.JSONField(
        'Tags',
        default=list,
        blank=True,
        help_text='Lista de tags para facilitar busca'
    )

    # Controle de acesso
    is_public = models.BooleanField(
        'Público',
        default=True,
        help_text='Se falso, apenas o criador pode visualizar'
    )
    is_active = models.BooleanField('Ativo', default=True)

    # Audit
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_documents',
        verbose_name='Enviado por'
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        # Extrair tamanho e tipo do arquivo
        if self.file:
            self.file_size = self.file.size
            import os
            self.file_type = os.path.splitext(self.file.name)[1].lower().replace('.', '')
        super().save(*args, **kwargs)

    @property
    def chunk_count(self):
        """Retorna quantidade de chunks gerados"""
        return self.chunks.count()

    @property
    def file_size_mb(self):
        """Retorna tamanho do arquivo em MB"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0


class DocumentChunk(models.Model):
    """
    Chunk (pedaço) de documento com embedding vetorial
    Cada documento é dividido em chunks para melhorar a busca RAG
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='chunks',
        verbose_name='Documento'
    )

    # Conteúdo do chunk
    content = models.TextField('Conteúdo')
    chunk_index = models.IntegerField('Índice do Chunk', help_text='Posição no documento original')

    # Embedding vetorial para busca semântica
    embedding = VectorField(
        dimensions=1024,  # IBM watsonx intfloat/multilingual-e5-large
        null=True,
        blank=True
    )

    # Metadados do chunk
    metadata = models.JSONField(
        'Metadados',
        default=dict,
        blank=True,
        help_text='Metadados específicos do chunk (página, seção, etc)'
    )

    # Tokens (para controle de custo)
    token_count = models.IntegerField('Contagem de Tokens', null=True, blank=True)

    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Chunk de Documento'
        verbose_name_plural = 'Chunks de Documentos'
        ordering = ['document', 'chunk_index']
        indexes = [
            models.Index(fields=['document', 'chunk_index']),
        ]

    def __str__(self):
        return f"{self.document.title} - Chunk {self.chunk_index}"

    @property
    def has_embedding(self):
        """Verifica se tem embedding gerado"""
        return self.embedding is not None

    @property
    def content_preview(self):
        """Retorna preview do conteúdo (primeiros 100 caracteres)"""
        if len(self.content) > 100:
            return self.content[:100] + '...'
        return self.content
