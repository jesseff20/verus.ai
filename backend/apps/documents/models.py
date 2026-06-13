"""
Models para Documents
"""
import uuid
from django.db import models
from django.conf import settings
from apps.core.constants import LLM_PROVIDER_CHOICES


class DocumentGenerator(models.Model):
    """
    Gerador de Documento - configura prompts e parâmetros de IA para gerar
    documentos jurídicos de um determinado tipo.
    """

    SPECIALTY_CHOICES = [
        ('geral', 'Geral (Todas as Especialidades)'),
        ('civel', 'Direito Civil'),
        ('penal', 'Direito Penal'),
        ('trabalhista', 'Direito Trabalhista'),
        ('tributario', 'Direito Tributário'),
        ('previdenciario', 'Direito Previdenciário'),
        ('administrativo', 'Direito Administrativo'),
        ('constitucional', 'Direito Constitucional'),
        ('empresarial', 'Direito Empresarial'),
        ('consumidor', 'Direito do Consumidor'),
        ('familia', 'Direito de Família e Sucessões'),
        ('imobiliario', 'Direito Imobiliário'),
        ('ambiental', 'Direito Ambiental'),
        ('digital', 'Direito Digital e LGPD'),
        ('saude', 'Direito da Saúde'),
        ('eleitoral', 'Direito Eleitoral'),
        ('internacional', 'Direito Internacional'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Nome', max_length=255, help_text='Nome descritivo do gerador')
    description = models.TextField('Descrição', blank=True)
    document_type = models.CharField('Tipo de Documento', max_length=50,
                                     help_text='Ex: peticao_inicial, contestacao, parecer, recurso, contrato')
    specialty = models.CharField(
        'Especialidade', max_length=30, choices=SPECIALTY_CHOICES, default='geral',
        help_text='Especialidade jurídica principal deste gerador',
    )
    system_prompt = models.TextField('System Prompt',
                                     help_text='Instruções do sistema para o gerador de documentos')
    user_prompt_template = models.TextField('User Prompt Template',
                                            help_text='Template com {{placeholders}} para dados do formulário')
    llm_provider = models.CharField('Provedor LLM', max_length=20, choices=LLM_PROVIDER_CHOICES, default='openai')
    model_name = models.CharField('Nome do Modelo', max_length=100, default='gpt-4o',
                                  help_text='Ex: gpt-4o, mistralai/mistral-medium-2505')
    temperature = models.FloatField('Temperature', default=0.7,
                                    help_text='0.0 = mais determinístico, 2.0 = mais criativo')
    max_tokens = models.IntegerField('Max Tokens', default=4000)
    use_rag = models.BooleanField('Usar RAG', default=True,
                                  help_text='Buscar contexto na Knowledge Base')
    rag_query_template = models.TextField('Template de Query RAG', blank=True,
                                          help_text='Template para busca no RAG. Ex: {{document_type}} {{description}}')
    icon = models.CharField('Ícone', max_length=50, blank=True, default='file-text',
                            help_text='Nome do ícone Lucide para exibição')
    color = models.CharField('Cor', max_length=7, default='#10b981',
                              help_text='Cor em hexadecimal para identificação visual')
    display_order = models.IntegerField('Ordem de Exibição', default=0,
                                        help_text='Ordem de exibição na lista (menor = primeiro)')
    is_active = models.BooleanField('Ativo', default=True)
    is_default = models.BooleanField('Gerador Padrão', default=False,
                                     help_text='Gerador padrão para este tipo de documento')
    document_template = models.ForeignKey(
        'templates.DocumentTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generators',
        verbose_name='Template de Documento',
        help_text='Template que este gerador usa como base',
    )
    knowledge_bases = models.ManyToManyField(
        'kb.Document',
        blank=True,
        related_name='document_generators',
        verbose_name='Bases de Conhecimento',
        help_text='Documentos da KB que este gerador pode acessar',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_document_generators',
        verbose_name='Criado por',
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Gerador de Documento'
        verbose_name_plural = 'Geradores de Documento'
        ordering = ['document_type', 'display_order']
        indexes = [
            models.Index(fields=['document_type', 'is_active'], name='doc_dg_doctype_active_idx'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['document_type', 'is_default'],
                condition=models.Q(is_default=True),
                name='unique_default_generator_per_doc_type',
            )
        ]

    def __str__(self):
        return f'{self.name} ({self.document_type})'

    @property
    def variable_count(self):
        """Conta variáveis no user_prompt_template"""
        import re
        return len(re.findall(r'\{\{(\w+)\}\}', self.user_prompt_template))

    @property
    def provider_display(self):
        return dict(LLM_PROVIDER_CHOICES).get(self.llm_provider, self.llm_provider)


class Document(models.Model):
    """
    Documento jurídico gerado (Petição, Parecer, Contrato, Recurso, etc.)
    """
    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('in_review', 'Em Revisão'),
        ('completed', 'Completo'),
        ('archived', 'Arquivado'),
    ]

    SOURCE_CHOICES = [
        ('manual', 'Preenchimento Manual'),
        ('generator', 'Gerador de Documento'),
        ('assistant', 'Assistente Inteligente'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relações
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='Documents',
        verbose_name='Usuário'
    )
    form_template = models.ForeignKey(
        'forms.FormTemplate',
        on_delete=models.PROTECT,
        related_name='Documents',
        verbose_name='Template de Formulário'
    )
    document_template = models.ForeignKey(
        'templates.DocumentTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='Documents',
        verbose_name='Template de Documento'
    )

    # Dados do formulário preenchido (JSON)
    data = models.JSONField('Dados do Formulário', default=dict)

    # Documento final gerado
    generated_content = models.TextField('Conteúdo Gerado', blank=True)
    generated_html = models.TextField('HTML Gerado (TinyMCE)', blank=True)

    # Arquivo final exportado
    exported_file = models.FileField(
        'Arquivo Exportado',
        upload_to='Documents/exports/',
        blank=True,
        null=True,
        help_text='PDF ou DOCX exportado'
    )

    # Status
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    # Rastreabilidade de origem
    source = models.CharField(
        'Origem',
        max_length=20,
        choices=SOURCE_CHOICES,
        default='manual',
        help_text='Como o documento foi criado'
    )

    # Gerador usado (se origem = generator)
    document_generator = models.ForeignKey(
        'DocumentGenerator',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_documents',
        verbose_name='Gerador de Documento',
        help_text='Gerador usado para criar este documento (se aplicável)',
    )

    # Metadata
    title = models.CharField('Título', max_length=500, blank=True)
    numero_processo = models.CharField(
        'Número do Processo', max_length=100, blank=True)
    description = models.TextField('Descrição', blank=True)

    # Progresso de preenchimento (0-100%)
    progress = models.IntegerField(
        'Progresso',
        default=0,
        help_text='Percentual de preenchimento do formulário (0-100%)'
    )

    # Versionamento
    version = models.IntegerField('Versão', default=1)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Documento Original'
    )

    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    completed_at = models.DateTimeField('Completado em', null=True, blank=True)

    class Meta:
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.title or f"Documento {self.id}"

    @property
    def is_draft(self):
        return self.status == 'draft'

    @property
    def is_completed(self):
        return self.status == 'completed'

    def create_version(self, user):
        """Cria nova versão do documento"""
        new_document = Document.objects.create(
            user=user,
            form_template=self.form_template,
            document_template=self.document_template,
            data=self.data.copy(),
            generated_content=self.generated_content,
            generated_html=self.generated_html,
            title=self.title,
            description=self.description,
            version=self.version + 1,
            parent=self.parent or self,
            status='draft',
            source=self.source,
        )
        return new_document


class DocumentVersion(models.Model):
    """
    Versão de um documento para versionamento semântico.

    Armazena:
    - Snapshots das seções do documento
    - Hashes de conteúdo para detecção de mudanças
    - Metadados de versionamento (número, tipo, resumo)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relação com documento
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='versions',
        verbose_name='Documento'
    )

    # Versionamento
    version_number = models.CharField(
        'Número da Versão',
        max_length=20,
        help_text='Formato semântico: MAJOR.MINOR.PATCH (ex: 1.2.3)'
    )
    version_type = models.CharField(
        'Tipo de Versão',
        max_length=10,
        choices=[
            ('major', 'Major - Mudança substantiva'),
            ('minor', 'Minor - Alterações menores'),
            ('patch', 'Patch - Correções/ajustes'),
        ],
        default='minor'
    )

    # Dados das seções (JSON)
    sections_data = models.JSONField(
        'Dados das Seções',
        default=list,
        help_text='Lista de seções com id, título e conteúdo'
    )

    # Hashes por seção para detecção rápida de mudanças
    section_hashes = models.TextField(
        'Hashes das Seções (JSON)',
        blank=True,
        null=True,
        help_text='JSON com mapeamento section_id -> hash'
    )

    # Resumo da mudança
    change_summary = models.TextField(
        'Resumo da Alteração',
        blank=True,
        help_text='Descrição das mudanças feitas nesta versão'
    )

    # Autor
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='document_versions',
        verbose_name='Criado por'
    )

    # Versão pai (para histórico)
    parent_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_versions',
        verbose_name='Versão Pai'
    )

    # Tags
    tags = models.JSONField(
        'Tags',
        default=list,
        help_text='Lista de tags para categorização'
    )

    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Versão de Documento'
        verbose_name_plural = 'Versões de Documento'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document', '-created_at']),
            models.Index(fields=['document', 'version_number']),
        ]

    def __str__(self):
        return f'{self.document.title or "Documento"} - v{self.version_number}'
