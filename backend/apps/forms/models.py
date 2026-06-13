"""
Models para formulários dinâmicos
"""
import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from apps.core.constants import LLM_PROVIDER_CHOICES


def validate_form_fields(value):
    """Valida estrutura dos campos do formulário"""
    if not isinstance(value, list):
        raise ValidationError('Fields deve ser uma lista')

    for field in value:
        if not isinstance(field, dict):
            raise ValidationError('Cada campo deve ser um objeto')

        required_keys = ['id', 'type', 'label']
        for key in required_keys:
            if key not in field:
                raise ValidationError(f'Campo obrigatório ausente: {key}')

        # Validar tipos permitidos
        valid_types = ['text', 'textarea', 'number', 'email',
                       'date', 'select', 'checkbox', 'radio', 'file', 'array']
        if field['type'] not in valid_types:
            raise ValidationError(f'Tipo de campo inválido: {field["type"]}')


def validate_form_sections(value):
    """Valida estrutura de seções do formulário"""
    if not isinstance(value, list):
        raise ValidationError('Sections deve ser uma lista')

    for section in value:
        if not isinstance(section, dict):
            raise ValidationError('Cada seção deve ser um objeto')

        # Validar keys obrigatórias da seção
        if 'section_id' not in section:
            raise ValidationError('Seção deve ter section_id')
        if 'section_title' not in section:
            raise ValidationError('Seção deve ter section_title')
        if 'fields' not in section:
            raise ValidationError('Seção deve ter fields')

        # Validar campos dentro da seção
        if not isinstance(section['fields'], list):
            raise ValidationError(
                f'Fields da seção {section.get("section_id")} deve ser uma lista')

        for field in section['fields']:
            if not isinstance(field, dict):
                raise ValidationError(
                    f'Cada campo da seção {section.get("section_id")} deve ser um objeto')

            required_keys = ['field_id', 'field_type', 'field_name']
            for key in required_keys:
                if key not in field:
                    raise ValidationError(
                        f'Campo obrigatório ausente na seção {section.get("section_id")}: {key}')

            # Validar tipos permitidos
            valid_types = ['text', 'textarea', 'number', 'email',
                           'date', 'select', 'checkbox', 'radio', 'file', 'array']
            if field['field_type'] not in valid_types:
                raise ValidationError(
                    f'Tipo de campo inválido na seção {section.get("section_id")}: {field["field_type"]}')


class FormTemplate(models.Model):
    """
    Template de formulário configurável pelo admin
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Nome', max_length=255)
    description = models.TextField('Descrição', blank=True)

    # Campos dinâmicos em JSON (formato flat - para formulários simples)
    # Exemplo: [{"id": "descricao_necessidade", "type": "textarea", "label": "Descrição da Necessidade", "required": true, "help_text": "...", "ai_assist": true}]
    fields = models.JSONField('Campos', default=list,
                              blank=True, validators=[validate_form_fields])

    # Seções de formulário (formato estruturado - para formulários complexos como ETP)
    # Exemplo: [{"section_id": "secao_1", "section_title": "1 - Descrição da Necessidade", "legal_basis": "...", "fields": [...]}]
    sections = models.JSONField('Seções', default=list, blank=True, validators=[
                                validate_form_sections])

    # Blueprint de documento associado
    # Define os agentes de IA disponíveis para os campos deste formulário
    blueprint = models.ForeignKey(
        'intelligent_assistant.DocumentBlueprint',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='form_templates',
        verbose_name='Blueprint',
        help_text='Blueprint de documento que define os agentes disponíveis para este formulário'
    )

    # Versioning
    version = models.IntegerField('Versão', default=1)
    is_active = models.BooleanField('Ativo', default=True)

    # Audit
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_form_templates',
        verbose_name='Criado por'
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Template de Formulário'
        verbose_name_plural = 'Templates de Formulários'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', '-created_at']),
        ]

    def __str__(self):
        return f"{self.name} (v{self.version})"

    def clean(self):
        """Validação customizada"""
        super().clean()

        # Garantir que fields e sections não sejam vazios simultaneamente
        has_fields = bool(self.fields)
        has_sections = bool(self.sections)

        if not has_fields and not has_sections:
            raise ValidationError(
                'É necessário fornecer campos (fields) OU seções (sections).')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def duplicate(self, user):
        """Cria uma nova versão do template"""
        new_template = FormTemplate.objects.create(
            name=self.name,
            description=self.description,
            blueprint=self.blueprint,
            fields=self.fields.copy() if self.fields else [],
            sections=self.sections.copy() if self.sections else [],
            version=self.version + 1,
            created_by=user
        )
        return new_template

    @property
    def field_count(self):
        """Retorna quantidade total de campos"""
        if self.sections:
            # Contar campos dentro de todas as seções
            total = 0
            for section in self.sections:
                total += len(section.get('fields', []))
            return total
        return len(self.fields)

    @property
    def section_count(self):
        """Retorna quantidade de seções"""
        return len(self.sections) if self.sections else 0

    @property
    def uses_sections(self):
        """Verifica se usa formato de seções"""
        return bool(self.sections)


    def get_field_by_id(self, field_id):
        """Busca campo específico por ID"""
        if self.uses_sections:
            # Buscar em seções
            for section in self.sections:
                for field in section.get('fields', []):
                    if field.get('field_id') == field_id:
                        return field
        else:
            # Buscar em campos flat
            for field in self.fields:
                if field.get('id') == field_id:
                    return field
        return None

    def get_all_fields(self):
        """Retorna todos os campos (flat ou de seções)"""
        if self.uses_sections:
            all_fields = []
            for section in self.sections:
                all_fields.extend(section.get('fields', []))
            return all_fields
        return self.fields


class FormAssistant(models.Model):
    """
    Agente de IA específico para assistir no preenchimento de campos de formulário.
    Estes agentes são vinculados a campos específicos e fornecem:
    - Sugestões contextuais
    - Validação inteligente
    - Correções automáticas
    - Expansão de conteúdo
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Metadados
    name = models.CharField('Nome', max_length=255, help_text='Nome descritivo do assistente')
    description = models.TextField('Descrição', blank=True)

    # Tipo de assistente (subcategoria/ação)
    assistant_type = models.CharField(
        'Tipo de Assistente',
        max_length=50,
        help_text='Ex: tradutor, corretor, expansor, validador'
    )

    # Prompts
    system_prompt = models.TextField(
        'System Prompt',
        help_text='Instruções do sistema para o assistente'
    )
    user_prompt_template = models.TextField(
        'User Prompt Template',
        help_text='Template com {{placeholders}} para variáveis do campo'
    )

    # Configurações LLM
    llm_provider = models.CharField(
        'Provedor LLM',
        max_length=20,
        choices=LLM_PROVIDER_CHOICES,
        default='openai'
    )
    model_name = models.CharField(
        'Nome do Modelo',
        max_length=100,
        default='gpt-4o-mini',
        help_text='Ex: gpt-4o-mini, mistralai/mistral-medium-2505'
    )
    temperature = models.FloatField(
        'Temperature',
        default=0.7,
        help_text='0.0 = mais determinístico, 2.0 = mais criativo'
    )
    max_tokens = models.IntegerField('Max Tokens', default=500)

    # Contexto RAG (opcional)
    use_rag = models.BooleanField(
        'Usar RAG',
        default=False,
        help_text='Buscar contexto na Knowledge Base'
    )
    rag_query_template = models.TextField(
        'Template de Query RAG',
        blank=True,
        help_text='Template para busca no RAG. Ex: {{field_value}}'
    )

    # UI/UX
    icon = models.CharField(
        'Ícone',
        max_length=50,
        blank=True,
        default='wand-2',
        help_text='Nome do ícone Lucide para exibição'
    )
    color = models.CharField(
        'Cor',
        max_length=7,
        default='#3b82f6',
        help_text='Cor em hexadecimal para identificação visual'
    )
    display_order = models.IntegerField(
        'Ordem de Exibição',
        default=0,
        help_text='Ordem de exibição no campo (menor = primeiro)'
    )

    # Flags
    is_active = models.BooleanField('Ativo', default=True)
    is_default = models.BooleanField(
        'Assistente Padrão',
        default=False,
        help_text='Assistente padrão para este campo'
    )

    # Audit
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_form_assistants',
        verbose_name='Criado por'
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Assistente de Formulário'
        verbose_name_plural = 'Assistentes de Formulário'
        ordering = ['display_order', 'assistant_type']
        indexes = [
            models.Index(fields=['assistant_type']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.assistant_type})"

    def extract_variables(self):
        """Extrai variáveis do user_prompt_template"""
        import re
        variables = re.findall(r'\{\{(\w+)\}\}', self.user_prompt_template)
        return list(set(variables))

    @property
    def variable_count(self):
        """Retorna quantidade de variáveis"""
        return len(self.extract_variables())
