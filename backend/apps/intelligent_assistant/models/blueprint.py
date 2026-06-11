"""
Modelos de Blueprint e seções de documentos.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class DocumentBlueprint(models.Model):
    """
    Blueprint (modelo) de documento.

    Define a estrutura de um tipo de documento (ex: ETP com 15 seções,
    ETP RJ com 29 seções). Cada blueprint pode ter múltiplas seções
    configuráveis.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Identificação
    name = models.CharField(
        max_length=255,
        verbose_name='Nome',
        help_text='Nome do blueprint (ex: "ETP - Lei 14.133", "ETP Rio de Janeiro")'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descrição',
        help_text='Descrição detalhada do blueprint e seu propósito'
    )

    # Tipo de documento - ForeignKey para tabela centralizada
    document_type = models.ForeignKey(
        'core.DocumentType',
        on_delete=models.PROTECT,
        related_name='blueprints',
        verbose_name='Tipo de Documento',
        help_text='Tipo de documento conforme tabela centralizada'
    )

    # Versão e base legal
    version = models.CharField(
        max_length=50,
        default='1.0',
        verbose_name='Versão',
        help_text='Versão do blueprint'
    )
    legal_basis = models.TextField(
        blank=True,
        verbose_name='Base Legal',
        help_text='Legislação base (ex: Lei 14.133/2021, Decreto 10.024/2019)'
    )

    # Metadados adicionais
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadados',
        help_text='Configurações adicionais em JSON'
    )

    # ========================================
    # PERSONALIZAÇÃO DO PDF
    # ========================================
    organization_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Nome da Organização',
        help_text='Nome do órgão/entidade (ex: "Tribunal de Justiça")'
    )
    organization_acronym = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Sigla',
        help_text='Sigla da organização (ex: "TJRJ", "PRODERJ")'
    )
    logo = models.ImageField(
        upload_to='blueprints/logos/',
        blank=True,
        null=True,
        verbose_name='Logo',
        help_text='Logo do órgão para o cabeçalho do documento'
    )
    header_text = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Texto do Cabeçalho',
        help_text='Texto exibido no topo de cada página (ex: "GOVERNO DO ESTADO DO RIO DE JANEIRO")'
    )
    footer_text = models.TextField(
        blank=True,
        verbose_name='Texto do Rodapé',
        help_text='Texto do rodapé com legislação aplicável'
    )
    primary_color = models.CharField(
        max_length=7,
        default='#7030A0',
        verbose_name='Cor Primária',
        help_text='Cor principal dos títulos (formato hex: #RRGGBB)'
    )
    secondary_color = models.CharField(
        max_length=7,
        default='#5B2EE0',
        verbose_name='Cor Secundária',
        help_text='Cor dos subtítulos e destaques (formato hex: #RRGGBB)'
    )
    custom_css = models.TextField(
        blank=True,
        verbose_name='CSS Customizado',
        help_text='CSS adicional para personalização avançada do PDF'
    )

    # ========================================
    # PÁGINA DE ROSTO
    # ========================================
    cover_page_enabled = models.BooleanField(
        default=True,
        verbose_name='Habilitar Página de Rosto',
        help_text='Se deve gerar página de rosto no PDF'
    )
    cover_logo = models.ImageField(
        upload_to='blueprints/covers/',
        blank=True,
        null=True,
        verbose_name='Logo da Capa',
        help_text='Logo específica para a página de rosto (se diferente da logo principal)'
    )
    cover_title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Título da Capa',
        help_text='Título principal da capa (ex: "ESTUDO TÉCNICO PRELIMINAR")'
    )
    cover_subtitle = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Subtítulo da Capa',
        help_text='Subtítulo da capa (ex: "Lei 14.133/2021")'
    )
    cover_organization_text = models.TextField(
        blank=True,
        verbose_name='Texto da Organização na Capa',
        help_text='Texto completo da organização para a capa (pode ter várias linhas)'
    )
    cover_footer_text = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Rodapé da Capa',
        help_text='Texto do rodapé da capa (ex: "Rio de Janeiro - 2026")'
    )
    cover_background_color = models.CharField(
        max_length=7,
        default='#FFFFFF',
        verbose_name='Cor de Fundo da Capa',
        help_text='Cor de fundo da página de rosto (formato hex: #RRGGBB)'
    )

    # ========================================
    # TIPOGRAFIA DO PDF
    # ========================================
    pdf_font_family = models.CharField(
        max_length=100,
        default='Times New Roman',
        verbose_name='Fonte do PDF',
        help_text='Família de fonte (ex: "Times New Roman", "Arial", "Calibri")'
    )
    pdf_font_size = models.CharField(
        max_length=10,
        default='12pt',
        verbose_name='Tamanho da Fonte',
        help_text='Tamanho da fonte do corpo (ex: "12pt", "11pt")'
    )
    pdf_line_height = models.CharField(
        max_length=10,
        default='1.5',
        verbose_name='Altura da Linha',
        help_text='Espaçamento entre linhas (ex: "1.5", "1.8", "2.0")'
    )
    pdf_text_align = models.CharField(
        max_length=20,
        default='justify',
        choices=[
            ('justify', 'Justificado'),
            ('left', 'Esquerda'),
            ('right', 'Direita'),
            ('center', 'Centralizado'),
        ],
        verbose_name='Alinhamento do Texto',
        help_text='Alinhamento do texto do corpo'
    )
    pdf_paragraph_indent = models.CharField(
        max_length=10,
        default='1.5cm',
        verbose_name='Recuo do Parágrafo',
        help_text='Recuo da primeira linha do parágrafo (ex: "1.5cm", "0")'
    )
    pdf_paragraph_spacing = models.CharField(
        max_length=10,
        default='12pt',
        verbose_name='Espaçamento entre Parágrafos',
        help_text='Espaço entre parágrafos (ex: "12pt", "6pt")'
    )
    pdf_page_margin_top = models.CharField(
        max_length=10,
        default='2.5cm',
        verbose_name='Margem Superior',
        help_text='Margem superior da página'
    )
    pdf_page_margin_bottom = models.CharField(
        max_length=10,
        default='2.5cm',
        verbose_name='Margem Inferior',
        help_text='Margem inferior da página'
    )
    pdf_page_margin_left = models.CharField(
        max_length=10,
        default='3cm',
        verbose_name='Margem Esquerda',
        help_text='Margem esquerda da página'
    )
    pdf_page_margin_right = models.CharField(
        max_length=10,
        default='2cm',
        verbose_name='Margem Direita',
        help_text='Margem direita da página'
    )

    # ========================================
    # TAGS DE ÁREA JURÍDICA (M2M)
    # ========================================
    areas = models.ManyToManyField(
        'core.DocumentCategory',
        blank=True,
        verbose_name='Áreas Jurídicas',
        help_text='Áreas do direito onde este blueprint pode ser utilizado (permite multi-seleção)',
        related_name='blueprints',
    )

    # Flags
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo',
        help_text='Se o blueprint está disponível para uso'
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name='Padrão',
        help_text='Se é o blueprint padrão para seu tipo de documento'
    )

    # Auditoria
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_blueprints',
        verbose_name='Criado por'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        app_label = 'intelligent_assistant'
        verbose_name = 'Blueprint de Documento'
        verbose_name_plural = 'Blueprints de Documentos'
        ordering = ['document_type__display_order', 'document_type__name', 'name']
        indexes = [
            models.Index(fields=['document_type', 'is_active']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        doc_type_name = self.document_type.name if self.document_type else 'Sem tipo'
        return f"{self.name} ({doc_type_name})"

    @property
    def section_count(self):
        """Retorna o número de seções do blueprint"""
        return self.sections.count()

    def get_ordered_sections(self):
        """Retorna as seções ordenadas por ordem"""
        return self.sections.filter(is_active=True).order_by('order')


class BlueprintSection(models.Model):
    """
    Seção de um blueprint de documento.

    Cada seção tem um agente gerador e um validador associados.
    As seções são independentes entre si (sem dependências),
    apenas ordenadas para exibição.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relacionamento com blueprint
    blueprint = models.ForeignKey(
        DocumentBlueprint,
        on_delete=models.CASCADE,
        related_name='sections',
        verbose_name='Blueprint'
    )

    # Identificação da seção
    section_number = models.IntegerField(
        verbose_name='Número da Seção',
        help_text='Número identificador da seção (ex: 1, 2, 3...)'
    )
    section_name = models.CharField(
        max_length=255,
        verbose_name='Nome da Seção',
        help_text='Nome da seção (ex: "Descrição da Necessidade da Contratação")'
    )
    section_key = models.CharField(
        max_length=100,
        verbose_name='Chave da Seção',
        help_text='Identificador único dentro do blueprint (ex: "section_01", "descricao_necessidade")'
    )

    # Descrição e instruções
    description = models.TextField(
        blank=True,
        verbose_name='Descrição',
        help_text='Descrição detalhada do que deve conter esta seção'
    )
    instructions = models.TextField(
        blank=True,
        verbose_name='Instruções',
        help_text='Instruções específicas para o preenchimento desta seção'
    )

    # Base legal específica da seção
    legal_reference = models.TextField(
        blank=True,
        verbose_name='Referência Legal',
        help_text='Artigos e incisos que fundamentam esta seção'
    )

    # Agentes associados
    generator_agent = models.ForeignKey(
        'intelligent_assistant.SectionAgentConfig',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generator_for_sections',
        verbose_name='Agente Gerador',
        help_text='Agente responsável por gerar o conteúdo desta seção',
        limit_choices_to={'agent_type': 'generator', 'is_active': True}
    )
    validator_agent = models.ForeignKey(
        'intelligent_assistant.SectionAgentConfig',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validator_for_sections',
        verbose_name='Agente Validador',
        help_text='Agente responsável por validar o conteúdo gerado',
        limit_choices_to={'agent_type': 'validator', 'is_active': True}
    )

    # Dependências entre seções
    depends_on = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='required_by',
        verbose_name='Depende de',
        help_text='Seções que devem ser concluídas antes desta'
    )

    # Ordenação
    order = models.IntegerField(
        default=0,
        verbose_name='Ordem',
        help_text='Ordem de exibição/geração (menor = primeiro)'
    )

    # Configurações de geração
    is_required = models.BooleanField(
        default=True,
        verbose_name='Obrigatória',
        help_text='Se a seção é obrigatória no documento final'
    )
    allow_skip = models.BooleanField(
        default=True,
        verbose_name='Permitir Pular',
        help_text='Se o usuário pode optar por não gerar esta seção'
    )
    max_generation_attempts = models.IntegerField(
        default=3,
        verbose_name='Máximo de Tentativas',
        help_text='Número máximo de tentativas de geração em caso de falha'
    )

    # Campos estruturados da seção (formulário)
    section_fields = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Campos da Seção',
        help_text='''Campos estruturados para preenchimento. Exemplo:
        [
            {"name": "nome", "label": "Nome", "type": "text", "required": true},
            {"name": "email", "label": "E-mail", "type": "email", "required": true}
        ]
        Tipos suportados: text, email, tel, number, date, select, textarea, array'''
    )

    # Flags
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativa',
        help_text='Se a seção está disponível'
    )

    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        app_label = 'intelligent_assistant'
        verbose_name = 'Seção do Blueprint'
        verbose_name_plural = 'Seções do Blueprint'
        ordering = ['blueprint', 'order', 'section_number']
        unique_together = [
            ['blueprint', 'section_number'],
            ['blueprint', 'section_key'],
        ]
        indexes = [
            models.Index(fields=['blueprint', 'order']),
            models.Index(fields=['is_active']),
        ]

    def get_active_sub_sections(self):
        """Retorna sub-seções ativas ordenadas."""
        return self.sub_sections.filter(is_active=True).order_by('order', 'sub_number')

    def __str__(self):
        return f"{self.blueprint.name} - {self.section_number}. {self.section_name}"


class SectionImportConfig(models.Model):
    """
    Configuração de importação entre seções de blueprints diferentes.

    Define de quais seções de um blueprint-fonte (ex: ETP) cada seção
    do blueprint-alvo (ex: TR) importa conteúdo, e como esse conteúdo
    é tratado (cópia, transformação IA, texto fixo, etc.).

    Editável via Django Admin. Substitui mapeamento hardcoded.
    """

    class ImportType(models.TextChoices):
        COPY = "copy", "Cópia direta"
        TRANSFORM = "transform", "Transformação IA"
        FIXED = "fixed", "Texto padrão"
        FIXED_IA = "fixed_ia", "Padrão + IA"
        INPUT = "input", "Manual"
        OU = "ou", "OU (alternativas)"
        MIXED = "mixed", "Misto (ETP + Padrão)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    target_section = models.OneToOneField(
        BlueprintSection,
        on_delete=models.CASCADE,
        related_name='import_config',
        verbose_name='Seção Alvo',
        help_text='Seção do blueprint que recebe o conteúdo importado'
    )

    source_sections = models.ManyToManyField(
        BlueprintSection,
        related_name='export_targets',
        blank=True,
        verbose_name='Seções Fonte',
        help_text='Seções do blueprint fonte de onde importar conteúdo'
    )

    import_type = models.CharField(
        max_length=20,
        choices=ImportType.choices,
        verbose_name='Tipo de Importação',
        help_text='Como o conteúdo será tratado na importação',
        db_index=True,
    )

    label = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Rótulo',
        help_text='Descrição legível do mapeamento (ex: "ETP §1 + §9")'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo',
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        app_label = 'intelligent_assistant'
        verbose_name = 'Configuração de Importação'
        verbose_name_plural = 'Configurações de Importação'
        ordering = ['target_section__section_number']

    def __str__(self):
        return f"{self.target_section} ← {self.label} ({self.get_import_type_display()})"

    @property
    def source_section_numbers(self):
        """Retorna lista de section_numbers das seções fonte."""
        return list(
            self.source_sections.values_list('section_number', flat=True).order_by('section_number')
        )


class BlueprintSubSection(models.Model):
    """
    Sub-seção de uma BlueprintSection com lógica condicional (OU).

    Cada sub-seção representa um sub-item dentro de uma seção principal.
    O usuário decide para cada uma: "Sim, detalhar" (IA gera) ou
    "Não se aplica" (texto padrão do campo default_text é usado).

    Exemplo: Seção 4 do ETP tem sub-itens 4.1 a 4.17, cada um com OU.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Seção pai
    section = models.ForeignKey(
        BlueprintSection,
        on_delete=models.CASCADE,
        related_name='sub_sections',
        verbose_name='Seção Pai'
    )

    # Identificação
    sub_number = models.CharField(
        max_length=20,
        verbose_name='Numeração',
        help_text='Numeração do sub-item (ex: "4.1", "4.2", "3.1")'
    )
    sub_name = models.CharField(
        max_length=255,
        verbose_name='Nome',
        help_text='Nome do sub-item (ex: "Requisitos de Negócio")'
    )
    sub_key = models.CharField(
        max_length=100,
        verbose_name='Chave',
        help_text='Identificador único dentro do blueprint (ex: "requisitos_negocio")'
    )

    # Conteúdo e orientação
    description = models.TextField(
        blank=True,
        verbose_name='Descrição',
        help_text='Descrição detalhada do que deve conter este sub-item'
    )
    help_text = models.TextField(
        blank=True,
        verbose_name='Texto de Ajuda',
        help_text='Orientação ao usuário sobre o que preencher quando escolher "Sim, detalhar"'
    )

    # Texto padrão do "OU" (quando usuário escolhe "Não se aplica")
    default_text = models.TextField(
        blank=True,
        verbose_name='Texto Padrão (OU)',
        help_text='Texto inserido automaticamente quando o usuário escolhe "Não se aplica". '
                  'Ex: "Não foi identificada necessidade de capacitação/treinamento específico."'
    )

    # Agente gerador (usado quando usuário escolhe "Sim, detalhar")
    generator_agent = models.ForeignKey(
        'intelligent_assistant.SectionAgentConfig',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generator_for_sub_sections',
        verbose_name='Agente Gerador',
        help_text='Agente que gera o conteúdo quando o usuário escolhe "Sim, detalhar"',
        limit_choices_to={'agent_type': 'generator', 'is_active': True}
    )

    # Campos estruturados para input do usuário
    section_fields = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Campos de Input',
        help_text='Campos que o usuário preenche antes da geração por IA. '
                  'Mesma estrutura de BlueprintSection.section_fields.'
    )

    # Fonte de importação (usado na Minuta e documentos com import de outro blueprint)
    source_section = models.ForeignKey(
        'intelligent_assistant.BlueprintSection',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='imported_by_sub_sections',
        verbose_name='Seção Fonte (import)',
        help_text='Seção de outro blueprint (ex: TR) de onde importar conteúdo para esta sub-seção'
    )
    source_sub_section = models.ForeignKey(
        'intelligent_assistant.BlueprintSubSection',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='imported_by_sub_sections',
        verbose_name='Sub-seção Fonte (import)',
        help_text='Sub-seção de outro blueprint (ex: TR §4.1) de onde importar conteúdo'
    )

    # Ordenação e flags
    order = models.IntegerField(
        default=0,
        verbose_name='Ordem',
        help_text='Ordem de exibição dentro da seção pai'
    )
    is_required = models.BooleanField(
        default=False,
        verbose_name='Obrigatório',
        help_text='Se True, o usuário não pode escolher "Não se aplica"'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )

    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        app_label = 'intelligent_assistant'
        verbose_name = 'Sub-seção do Blueprint'
        verbose_name_plural = 'Sub-seções do Blueprint'
        ordering = ['section', 'order', 'sub_number']
        unique_together = [
            ['section', 'sub_key'],
        ]
        indexes = [
            models.Index(fields=['section', 'order']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.section.section_name} → {self.sub_number}. {self.sub_name}"
