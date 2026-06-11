"""
Modelos de sessão do assistente inteligente, documentos e embeddings.
"""
import uuid
from django.db import models
from django.db.models import Q
from django.contrib.auth import get_user_model
from pgvector.django import VectorField

User = get_user_model()


class IntelligentSession(models.Model):
    """
    Sessão de trabalho do assistente inteligente.
    Cada sessão representa uma tentativa de gerar um documento (ETP, Edital, etc).
    """

    STATUS_CHOICES = [
        ('initialized', 'Inicializada'),
        ('collecting_data', 'Coletando Dados'),
        ('uploading', 'Upload de Documentos'),
        ('processing', 'Processando Documentos'),
        ('generating', 'Gerando Seções'),
        ('validating', 'Validando'),
        ('formatting', 'Formatando'),
        ('completed', 'Concluída'),
        ('failed', 'Falhou'),
    ]

    # NOTA: a fonte de verdade para os tipos de documento eh core.DocumentType
    # (tabela centralizada). Para adicionar tipo novo, INSERT em DocumentType
    # via admin Django ou seed — sem mexer aqui, sem migration.

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='intelligent_sessions',
        verbose_name='Usuário'
    )
    blueprint = models.ForeignKey(
        'intelligent_assistant.DocumentBlueprint',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions',
        verbose_name='Blueprint',
        help_text='Modelo de documento selecionado para esta sessão'
    )
    objective = models.TextField(
        verbose_name='Objetivo da Contratação',
        help_text='Descrição do que o usuário deseja contratar/analisar'
    )
    document_type = models.CharField(
        max_length=50,
        default='peticao_inicial',
        verbose_name='Tipo de Documento',
        help_text='Code do core.DocumentType. Validação dinâmica via tabela centralizada.',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='initialized',
        verbose_name='Status'
    )
    kb_collection_id = models.CharField(
        max_length=255,
        verbose_name='ID da Coleção na KB',
        help_text='Identificador único da coleção no ChromaDB'
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name='Mensagem de Erro'
    )

    parent_etp_session = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_attachments',
        verbose_name='Sessão pai (anexo)',
        help_text='Quando esta sessão é um anexo de outra, aponta para a sessão principal a que pertence.',
    )

    # Campos de coleta de dados
    collected_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Dados Coletados',
        help_text='Dados coletados do usuário para geração'
    )
    validation_state = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Estado de Validação',
        help_text='Resultado da validação pré-geração'
    )

    # FK para o caso jurídico (opcional)
    case = models.ForeignKey(
        'cases.LegalCase',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='intelligent_sessions',
        verbose_name='Caso Jurídico',
        help_text='Caso jurídico associado a esta sessão de geração de documento',
    )

    # Campos de revisão humana (obrigatória)
    reviewer_oab = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='OAB do Revisor',
        help_text='OAB do advogado que revisou o documento'
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Revisado em',
        help_text='Timestamp da revisão humana'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        app_label = 'intelligent_assistant'
        verbose_name = 'Sessão do Assistente Inteligente'
        verbose_name_plural = 'Sessões do Assistente Inteligente'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['parent_etp_session']),
        ]
        constraints = [
            # Anexos: 1 sessao por (pai, tipo, user). Versoes ficam em
            # GeneratedDocument; nao em IntelligentSession duplicada.
            # Documentos principais (parent IS NULL) podem coexistir N por user.
            models.UniqueConstraint(
                fields=['parent_etp_session', 'document_type', 'user'],
                condition=Q(parent_etp_session__isnull=False),
                name='unique_attachment_per_parent_type_user',
            ),
        ]

    def __str__(self):
        return f"{self.document_type_display} - {self.user.username} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"

    @property
    def document_type_display(self):
        """Nome legível do tipo, lido de core.DocumentType (substitui get_FOO_display)."""
        from apps.core.models import DocumentType
        dt = DocumentType.objects.filter(code=self.document_type).only('name').first()
        return dt.name if dt else self.document_type


class UploadedDocument(models.Model):
    """
    Documentos enviados pelo usuário para análise.
    """

    FILE_TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('docx', 'Word Document'),
        ('odt', 'OpenDocument Text'),
        ('txt', 'Texto'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        IntelligentSession,
        on_delete=models.CASCADE,
        related_name='uploaded_documents',
        verbose_name='Sessão'
    )
    file = models.FileField(
        upload_to='intelligent_assistant/uploads/%Y/%m/%d/',
        verbose_name='Arquivo',
        blank=True,
        null=True,
    )
    filename = models.CharField(max_length=255, verbose_name='Nome do Arquivo')
    file_type = models.CharField(
        max_length=10,
        choices=FILE_TYPE_CHOICES,
        verbose_name='Tipo de Arquivo'
    )
    file_size = models.IntegerField(
        verbose_name='Tamanho do Arquivo (bytes)',
        help_text='Tamanho em bytes'
    )
    extracted_text = models.TextField(
        blank=True,
        verbose_name='Texto Extraído',
        help_text='Texto extraído do documento'
    )
    extraction_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendente'),
            ('processing', 'Processando'),
            ('completed', 'Concluído'),
            ('failed', 'Falhou'),
        ],
        default='pending',
        verbose_name='Status da Extração'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Enviado em')

    class Meta:
        app_label = 'intelligent_assistant'
        verbose_name = 'Documento Enviado'
        verbose_name_plural = 'Documentos Enviados'
        ordering = ['uploaded_at']

    def __str__(self):
        return f"{self.filename} ({self.get_file_type_display()})"


class GeneratedSection(models.Model):
    """
    Seção gerada do documento (ex: Seção 1 - Introdução do ETP).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        IntelligentSession,
        on_delete=models.CASCADE,
        related_name='generated_sections',
        verbose_name='Sessão'
    )
    section_number = models.IntegerField(
        verbose_name='Número da Seção',
        help_text='1-15 para ETP'
    )
    section_name = models.CharField(
        max_length=100,
        verbose_name='Nome da Seção'
    )
    content = models.TextField(
        verbose_name='Conteúdo',
        help_text='Conteúdo gerado pelo agente'
    )
    is_valid = models.BooleanField(
        default=False,
        verbose_name='É Válida?',
        help_text='Se passou na validação'
    )
    validation_errors = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Erros de Validação',
        help_text='Lista de erros encontrados pelo validador'
    )
    validation_warnings = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Avisos de Validação',
        help_text='Lista de avisos encontrados pelo validador'
    )
    agent_reasoning = models.TextField(
        blank=True,
        verbose_name='Raciocínio do Agente',
        help_text='Log do raciocínio usado pelo agente para gerar a seção'
    )
    generation_attempts = models.IntegerField(
        default=1,
        verbose_name='Tentativas de Geração',
        help_text='Número de vezes que o agente tentou gerar esta seção'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        app_label = 'intelligent_assistant'
        verbose_name = 'Seção Gerada'
        verbose_name_plural = 'Seções Geradas'
        ordering = ['session', 'section_number']
        unique_together = [['session', 'section_number']]
        indexes = [
            models.Index(fields=['session', 'section_number']),
        ]

    def __str__(self):
        return f"Seção {self.section_number}: {self.section_name}"


class GeneratedDocument(models.Model):
    """
    Documento final gerado (Markdown/DOCX/PDF).

    Armazena o ETP completo em múltiplos formatos:
    - markdown_content: Conteúdo bruto em Markdown (sempre salvo)
    - docx_file: Arquivo DOCX formatado (opcional)
    - pdf_file: Arquivo PDF para download (armazenado no R2)
    """

    FORMAT_CHOICES = [
        ('markdown', 'Markdown'),
        ('docx', 'Word Document'),
        ('pdf', 'PDF'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        IntelligentSession,
        on_delete=models.CASCADE,
        related_name='generated_documents',
        verbose_name='Sessão'
    )

    # Conteúdo em Markdown (sempre salvo)
    markdown_content = models.TextField(
        verbose_name='Conteúdo Markdown',
        help_text='Documento ETP completo em formato Markdown',
        blank=True,
        default=''
    )

    # Título do documento
    title = models.CharField(
        max_length=500,
        verbose_name='Título do Documento',
        blank=True,
        default=''
    )

    # Arquivos gerados
    docx_file = models.FileField(
        upload_to='intelligent_assistant/generated/%Y/%m/%d/',
        verbose_name='Arquivo DOCX',
        blank=True,
        null=True
    )
    pdf_file = models.FileField(
        upload_to='intelligent_assistant/generated/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name='Arquivo PDF'
    )

    # URLs do R2 (para acesso direto)
    pdf_url = models.URLField(
        max_length=1000,
        blank=True,
        null=True,
        verbose_name='URL do PDF no R2',
        help_text='URL pública do PDF armazenado no Cloudflare R2'
    )
    docx_url = models.URLField(
        max_length=1000,
        blank=True,
        null=True,
        verbose_name='URL do DOCX no R2'
    )

    # Metadados
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadados',
        help_text='Informações sobre o documento gerado'
    )

    # Tamanhos
    file_size_markdown = models.IntegerField(
        verbose_name='Tamanho Markdown (bytes)',
        null=True,
        blank=True
    )
    file_size_docx = models.IntegerField(
        verbose_name='Tamanho DOCX (bytes)',
        null=True,
        blank=True
    )
    file_size_pdf = models.IntegerField(
        verbose_name='Tamanho PDF (bytes)',
        null=True,
        blank=True
    )

    # Status de geração dos arquivos
    pdf_generated = models.BooleanField(
        default=False,
        verbose_name='PDF Gerado',
        help_text='Se o PDF foi gerado e enviado ao R2'
    )
    docx_generated = models.BooleanField(
        default=False,
        verbose_name='DOCX Gerado'
    )

    # Validação geral do documento
    overall_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Score Geral',
        help_text='Média das validações de todas as seções (0-100)'
    )
    valid_sections_count = models.IntegerField(
        default=0,
        verbose_name='Seções Válidas',
        help_text='Número de seções que passaram na validação'
    )
    total_sections = models.IntegerField(
        default=15,
        verbose_name='Total de Seções',
        help_text='Número total de seções do documento'
    )

    generated_at = models.DateTimeField(auto_now_add=True, verbose_name='Gerado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        app_label = 'intelligent_assistant'
        verbose_name = 'Documento Gerado'
        verbose_name_plural = 'Documentos Gerados'
        ordering = ['-generated_at']

    def __str__(self):
        return f"Documento {self.session.document_type_display} - {self.generated_at.strftime('%d/%m/%Y %H:%M')}"


class DocumentEmbedding(models.Model):
    """
    Embeddings de chunks de documentos para busca semântica via pgvector.

    Cada documento é dividido em chunks e cada chunk tem seu embedding.
    Isso permite busca semântica eficiente usando similaridade de cosseno.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relacionamentos
    document = models.ForeignKey(
        UploadedDocument,
        on_delete=models.CASCADE,
        related_name='embeddings',
        verbose_name='Documento'
    )
    session = models.ForeignKey(
        IntelligentSession,
        on_delete=models.CASCADE,
        related_name='embeddings',
        verbose_name='Sessão'
    )

    # Conteúdo do chunk
    chunk_index = models.IntegerField(
        verbose_name='Índice do Chunk',
        help_text='Posição do chunk no documento original'
    )
    chunk_text = models.TextField(
        verbose_name='Texto do Chunk',
        help_text='Conteúdo textual do chunk'
    )
    chunk_size = models.IntegerField(
        verbose_name='Tamanho do Chunk',
        help_text='Número de caracteres no chunk'
    )

    # Embedding vector (1024 dimensões para watsonx intfloat/multilingual-e5-large)
    embedding = VectorField(
        dimensions=1024,
        verbose_name='Embedding Vector',
        help_text='Vetor de embedding do chunk (1024 dimensões)'
    )

    # Metadados
    embedding_model = models.CharField(
        max_length=100,
        default='intfloat/multilingual-e5-large',
        verbose_name='Modelo de Embedding',
        help_text='Modelo usado para gerar o embedding'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadados',
        help_text='Informações adicionais sobre o chunk (página, seção, etc)'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')

    class Meta:
        app_label = 'intelligent_assistant'
        verbose_name = 'Embedding de Documento'
        verbose_name_plural = 'Embeddings de Documentos'
        ordering = ['document', 'chunk_index']
        indexes = [
            models.Index(fields=['session']),
            models.Index(fields=['document', 'chunk_index']),
        ]

    def __str__(self):
        return f"Chunk {self.chunk_index} - {self.document.filename}"


class SectionGenerationLog(models.Model):
    """Rastreabilidade completa de cada geração de seção jurídica."""

    session = models.ForeignKey(
        'IntelligentSession',
        on_delete=models.CASCADE,
        related_name='generation_logs'
    )
    section = models.ForeignKey(
        'intelligent_assistant.BlueprintSection',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='generation_logs'
    )
    agent = models.ForeignKey(
        'intelligent_assistant.SectionAgentConfig',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='generation_logs'
    )
    provider = models.CharField(max_length=50, blank=True)
    model_name = models.CharField(max_length=100, blank=True)
    prompt_hash = models.CharField(max_length=64, blank=True, help_text='SHA256 do prompt enviado')
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    generation_time_ms = models.IntegerField(default=0)
    output_hash = models.CharField(max_length=64, blank=True, help_text='SHA256 do conteúdo gerado')
    has_unresolved_placeholders = models.BooleanField(default=False)
    unresolved_count = models.IntegerField(default=0)
    placeholder_types = models.JSONField(default=list, help_text='Lista dos tipos de placeholder encontrados')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'intelligent_assistant'
        ordering = ['-created_at']
        verbose_name = 'Log de Geração de Seção'
        verbose_name_plural = 'Logs de Geração de Seção'

    def __str__(self):
        return f"Log {self.session_id} - {self.section} - {self.created_at}"
