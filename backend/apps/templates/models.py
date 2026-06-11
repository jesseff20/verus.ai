"""
Models para templates de documentos
"""
import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


def validate_template_file(value):
    """Valida extensão do arquivo de template"""
    valid_extensions = ['.html', '.docx', '.txt']
    import os
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError(
            f'Extensão inválida. Permitidas: {", ".join(valid_extensions)}')


class DocumentTemplate(models.Model):
    """
    Template de documento para geração de Documents
    Suporta templates HTML (com placeholders) e DOCX
    """
    TEMPLATE_TYPE_CHOICES = [
        ('html', 'HTML'),
        ('tinymce', 'TinyMCE'),
        ('docx', 'DOCX'),
        ('markdown', 'Markdown'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Nome', max_length=255)
    description = models.TextField('Descrição', blank=True)
    blueprint = models.ForeignKey(
        'intelligent_assistant.DocumentBlueprint',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='document_templates',
        verbose_name='Blueprint',
        help_text='Blueprint associado (ETP, DOD, etc.)'
    )
    template_type = models.CharField(
        'Tipo de Template', max_length=20, choices=TEMPLATE_TYPE_CHOICES, default='html')

    # Template content
    content = models.TextField(
        'Conteúdo do Template',
        help_text='Template com placeholders {{field_id}}. Ex: {{descricao_necessidade}}',
        blank=True
    )

    # Ou arquivo de template
    file = models.FileField(
        'Arquivo de Template',
        upload_to='templates/documents/',
        blank=True,
        null=True,
        validators=[validate_template_file],
        help_text='Upload de arquivo .html ou .docx'
    )

    # CSS customizado (para templates HTML)
    custom_css = models.TextField(
        'CSS Customizado',
        blank=True,
        help_text='CSS para estilização do documento HTML'
    )

    # Variáveis disponíveis (documentação)
    available_variables = models.JSONField(
        'Variáveis Disponíveis',
        default=list,
        blank=True,
        help_text='Lista de variáveis/placeholders disponíveis no template'
    )

    # Formulário associado (de onde vêm os dados para preencher o template)
    form_template = models.ForeignKey(
        'forms.FormTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='document_templates',
        verbose_name='Formulário Associado',
        help_text='Formulário que fornece os dados para preencher este template'
    )

    # Versioning
    version = models.IntegerField('Versão', default=1)
    is_active = models.BooleanField('Ativo', default=True)
    is_default = models.BooleanField(
        'Template Padrão',
        default=False,
        help_text='Template padrão para o tipo de documento'
    )

    # Audit
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_document_templates',
        verbose_name='Criado por'
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Template de Documento'
        verbose_name_plural = 'Templates de Documentos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['blueprint', 'is_active'], name='templates_d_bluepri_idx'),
            models.Index(fields=['is_default', 'blueprint'], name='templates_d_is_defa_bp_idx'),
        ]
        constraints = [
            # Apenas um template padrão por blueprint
            models.UniqueConstraint(
                fields=['blueprint', 'is_default'],
                condition=models.Q(is_default=True),
                name='unique_default_per_blueprint'
            )
        ]

    def __str__(self):
        return f"{self.name} (v{self.version}) - {self.get_template_type_display()}"

    def clean(self):
        """Validação customizada"""
        if not self.content and not self.file:
            raise ValidationError(
                'É necessário fornecer o conteúdo do template OU fazer upload de um arquivo.')

        if self.content and self.file:
            raise ValidationError(
                'Forneça APENAS o conteúdo OU o arquivo, não ambos.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_template_content(self):
        """Retorna conteúdo do template (do campo content ou do arquivo)"""
        if self.content:
            return self.content

        if self.file:
            try:
                # Para arquivos .docx, usar biblioteca python-docx
                if self.template_type == 'docx' or self.file.name.endswith('.docx'):
                    from .services import template_service
                    return template_service.extract_text_from_docx(self.file.path)

                # Para HTML/texto, ler normalmente
                with self.file.open('r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                # Se der erro ao ler arquivo, retornar vazio (não quebra a API)
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Erro ao ler arquivo do template {self.id}: {e}')
                return ''

        return ''

    def duplicate(self, user):
        """Cria uma nova versão do template"""
        new_template = DocumentTemplate.objects.create(
            name=self.name,
            description=self.description,
            blueprint=self.blueprint,
            template_type=self.template_type,
            content=self.content,
            custom_css=self.custom_css,
            available_variables=self.available_variables.copy(
            ) if self.available_variables else [],
            form_template=self.form_template,
            version=self.version + 1,
            is_default=False,  # Duplicata não é padrão
            created_by=user
        )
        return new_template

    def extract_placeholders(self):
        """Extrai placeholders do template ({{field_id}})"""
        import re
        content = self.get_template_content()
        placeholders = re.findall(r'\{\{(\w+)\}\}', content)
        return list(set(placeholders))

    @property
    def has_file(self):
        """Verifica se tem arquivo anexado"""
        return bool(self.file)

    @property
    def placeholder_count(self):
        """Retorna quantidade de placeholders"""
        return len(self.extract_placeholders())
