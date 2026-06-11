"""
Modelos de Knowledge Base e embeddings permanentes.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from pgvector.django import VectorField

User = get_user_model()


class KnowledgeBase(models.Model):
    """
    Base de conhecimento permanente (não vinculada a sessão).

    Hierarquia de 3 camadas:
    - global: Normas gerais acessíveis por todos os agentes
    - blueprint: Normas e exemplos específicos de um tipo de documento
    - agent: Melhores resultados gerados por um agente de seção
    """

    KB_LAYER_CHOICES = [
        ('global', 'Global (Normas Gerais)'),
        ('blueprint', 'Blueprint (Base do Documento)'),
        ('agent', 'Agente (Melhores Resultados)'),
        ('section_example', 'Exemplo Real de Seção'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Nome',
        help_text='Nome identificador da base de conhecimento'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descrição',
        help_text='Descrição do conteúdo da base de conhecimento'
    )
    kb_layer = models.CharField(
        max_length=20,
        choices=KB_LAYER_CHOICES,
        default='global',
        verbose_name='Camada',
        help_text='Camada na hierarquia: global (todos acessam), blueprint (por tipo de documento), agent (melhores resultados), section_example (exemplos reais por seção)'
    )
    blueprint = models.ForeignKey(
        'intelligent_assistant.DocumentBlueprint',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='knowledge_bases',
        verbose_name='Blueprint Associado',
        help_text='Blueprint ao qual esta KB pertence (apenas para camada blueprint)'
    )
    agent_config = models.ForeignKey(
        'intelligent_assistant.SectionAgentConfig',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='improvement_kbs',
        verbose_name='Agente Associado',
        help_text='Agente de seção ao qual esta KB pertence (apenas para camada agent)'
    )
    section = models.ForeignKey(
        'intelligent_assistant.BlueprintSection',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='example_kbs',
        verbose_name='Seção Associada',
        help_text='Seção específica (apenas para camada section_example)'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativa',
        help_text='Se a base está disponível para uso'
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='knowledge_bases_created',
        verbose_name='Criado por'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        app_label = 'intelligent_assistant'
        verbose_name = 'Base de Conhecimento'
        verbose_name_plural = 'Bases de Conhecimento'
        ordering = ['kb_layer', 'name']

    def __str__(self):
        layer_label = dict(self.KB_LAYER_CHOICES).get(self.kb_layer, self.kb_layer)
        return f"[{layer_label}] {self.name}"


class KnowledgeBaseEmbedding(models.Model):
    """
    Embeddings de chunks da base de conhecimento permanente.

    Similar ao DocumentEmbedding, mas para conteúdo permanente
    que não está vinculado a uma sessão específica.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    knowledge_base = models.ForeignKey(
        KnowledgeBase,
        on_delete=models.CASCADE,
        related_name='embeddings',
        verbose_name='Base de Conhecimento'
    )

    source_file = models.ForeignKey(
        'intelligent_assistant.KBSourceFile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='embeddings',
        verbose_name='Arquivo Fonte',
        help_text='Arquivo-fonte que gerou este embedding (rastreabilidade)'
    )

    # Identificação do conteúdo original
    source_name = models.CharField(
        max_length=255,
        verbose_name='Nome da Fonte',
        help_text='Nome do arquivo/documento original'
    )
    source_type = models.CharField(
        max_length=50,
        choices=[
            ('pdf', 'PDF'),
            ('docx', 'Word Document'),
            ('txt', 'Texto'),
            ('url', 'URL/Webpage'),
            ('manual', 'Entrada Manual'),
        ],
        verbose_name='Tipo da Fonte'
    )

    # Conteúdo do chunk
    chunk_index = models.IntegerField(
        verbose_name='Índice do Chunk'
    )
    chunk_text = models.TextField(
        verbose_name='Texto do Chunk'
    )
    chunk_size = models.IntegerField(
        verbose_name='Tamanho do Chunk'
    )

    # Embedding vector (1024 dimensões para watsonx intfloat/multilingual-e5-large)
    embedding = VectorField(
        dimensions=1024,
        verbose_name='Embedding Vector'
    )

    # Summary interpretativo (gerado por IA ao indexar)
    summary = models.TextField(
        blank=True,
        verbose_name='Resumo Interpretativo',
        help_text='Summary do chunk gerado por IA (estrutura, padrão de escrita, etc.)'
    )

    # Metadados
    embedding_model = models.CharField(
        max_length=100,
        default='intfloat/multilingual-e5-large',
        verbose_name='Modelo de Embedding'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadados'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')

    class Meta:
        app_label = 'intelligent_assistant'
        verbose_name = 'Embedding da Base de Conhecimento'
        verbose_name_plural = 'Embeddings da Base de Conhecimento'
        ordering = ['knowledge_base', 'source_name', 'chunk_index']
        indexes = [
            models.Index(fields=['knowledge_base']),
            models.Index(fields=['source_name']),
        ]

    def __str__(self):
        return f"{self.knowledge_base.name} - {self.source_name} - Chunk {self.chunk_index}"


class KBSourceFile(models.Model):
    """
    Arquivo-fonte de uma Knowledge Base.
    Rastreia arquivos originais enviados para cada KB (rastreabilidade + preview).
    Uma KB pode ter múltiplos arquivos-fonte (ex: KB "Legislação" com 10 PDFs).
    """

    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('completed', 'Processado'),
        ('failed', 'Falha'),
    ]

    CATEGORY_CHOICES = [
        ('lei', 'Lei / Norma'),
        ('decreto', 'Decreto'),
        ('manual', 'Manual / Guia'),
        ('referencia', 'Referência Técnica'),
        ('exemplo', 'Exemplo'),
        ('outros', 'Outros'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    knowledge_base = models.ForeignKey(
        KnowledgeBase,
        on_delete=models.CASCADE,
        related_name='source_files',
        verbose_name='Base de Conhecimento'
    )

    file = models.FileField(
        'Arquivo',
        upload_to='kb/sources/',
        blank=True,
        null=True,
        help_text='Arquivo original armazenado no R2'
    )
    file_name = models.CharField('Nome do Arquivo', max_length=255)
    file_size = models.BigIntegerField('Tamanho (bytes)', default=0)
    file_type = models.CharField('Tipo', max_length=10, help_text='pdf, docx, odt, txt...')

    category = models.CharField(
        'Categoria',
        max_length=50,
        choices=CATEGORY_CHOICES,
        blank=True,
        default='',
        help_text='Classificação do documento para organização'
    )
    tags = models.JSONField('Tags', default=list, blank=True)

    chunk_count = models.IntegerField('Chunks Gerados', default=0)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pending')
    processing_error = models.TextField('Erro', blank=True, default='')

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='kb_source_files',
        verbose_name='Enviado por'
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        app_label = 'intelligent_assistant'
        verbose_name = 'Arquivo-Fonte da KB'
        verbose_name_plural = 'Arquivos-Fonte da KB'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['knowledge_base', 'status']),
        ]

    def __str__(self):
        return f"{self.knowledge_base.name} - {self.file_name}"

    @property
    def file_size_mb(self):
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0


class AgentKnowledgeBaseLink(models.Model):
    """
    Vínculo configurável entre agente e KB.

    Substitui o M2M direto por um modelo intermediário com:
    - Ordem de consulta (priority)
    - Propósito/instrução por KB
    - Configuração RAG individual por vínculo
    """

    KB_PURPOSE_CHOICES = [
        ('examples', 'Exemplos Reais da Seção'),
        ('evaluation', 'Padrões Avaliados (4+ estrelas)'),
        ('normative', 'Normas e Legislação'),
        ('context', 'Contexto do Usuário (sessão)'),
        ('reference', 'Referência Geral'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    agent = models.ForeignKey(
        'intelligent_assistant.SectionAgentConfig',
        on_delete=models.CASCADE,
        related_name='kb_links',
        verbose_name='Agente'
    )
    knowledge_base = models.ForeignKey(
        KnowledgeBase,
        on_delete=models.CASCADE,
        related_name='agent_links',
        verbose_name='Base de Conhecimento'
    )

    # A) Ordem de consulta
    priority = models.IntegerField(
        default=0,
        verbose_name='Prioridade',
        help_text='Ordem de consulta (0 = primeiro). Menor = maior prioridade.'
    )

    # B) Propósito e instrução de uso
    purpose = models.CharField(
        max_length=20,
        choices=KB_PURPOSE_CHOICES,
        default='reference',
        verbose_name='Propósito',
        help_text='Como o agente deve interpretar os resultados desta KB'
    )
    instruction = models.TextField(
        blank=True,
        verbose_name='Instrução de Uso',
        help_text='Instrução para o agente sobre como usar os resultados desta KB. Ex: "Extraia o padrão de escrita destes exemplos reais"'
    )

    # Configuração RAG por vínculo
    top_k = models.IntegerField(
        default=5,
        verbose_name='Top K',
        help_text='Número de chunks a recuperar desta KB'
    )
    min_similarity = models.FloatField(
        default=0.6,
        verbose_name='Similaridade Mínima',
        help_text='Threshold de similaridade para incluir resultados (0.0 a 1.0)'
    )

    # E) Incluir summary interpretativo
    include_summary = models.BooleanField(
        default=False,
        verbose_name='Incluir Resumo',
        help_text='Se True, inclui o summary interpretativo junto com o chunk'
    )

    # F) Fontes selecionadas (filtra documentos específicos da KB)
    selected_sources = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Fontes Selecionadas',
        help_text='Lista de nomes de fontes (source_name) que o agente pode acessar. Vazio = todas as fontes.'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        app_label = 'intelligent_assistant'
        verbose_name = 'Vínculo Agente ↔ KB'
        verbose_name_plural = 'Vínculos Agente ↔ KB'
        ordering = ['agent', 'priority']
        unique_together = ['agent', 'knowledge_base']
        indexes = [
            models.Index(fields=['agent', 'priority']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        purpose_label = dict(self.KB_PURPOSE_CHOICES).get(self.purpose, self.purpose)
        return f"[P{self.priority}] {self.agent.name} → {self.knowledge_base.name} ({purpose_label})"
