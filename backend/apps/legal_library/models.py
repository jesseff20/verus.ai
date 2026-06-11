"""
Models para Biblioteca Viva de Argumentos Jurídicos.

Armazena:
- Argumentos jurídicos reutilizáveis
- Classificação por tema, tribunal e tipo
- Métricas de eficácia (taxa de sucesso em julgamentos)
- Vinculação com jurisprudência
"""

import uuid
from django.db import models
from django.conf import settings


class LegalArgument(models.Model):
    """
    Argumento jurídico reutilizável.

    Um argumento pode ser:
    - Tese jurídica completa
    - Fundamentação para um tipo de pedido
    - Resposta a uma objeção comum
    - Citação de doutrina ou jurisprudência
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Conteúdo
    title = models.CharField('Título', max_length=500)
    content = models.TextField('Conteúdo do Argumento')
    summary = models.TextField('Resumo', blank=True, help_text='Síntese do argumento em 1-2 frases')

    # Classificação
    category = models.CharField(
        'Categoria',
        max_length=100,
        choices=[
            ('preliminar', 'Preliminar'),
            ('merito', 'Mérito'),
            ('pedido', 'Pedido'),
            ('fundamentacao', 'Fundamentação'),
            ('recurso', 'Recurso'),
            ('contrarrazoes', 'Contrarrazões'),
        ],
        default='merito'
    )

    specialty = models.CharField(
        'Especialidade',
        max_length=50,
        choices=[
            ('CIV', 'Cível'),
            ('PEN', 'Criminal'),
            ('TRB', 'Trabalhista'),
            ('FAM', 'Família'),
            ('PRE', 'Previdenciário'),
            ('ADM', 'Administrativo'),
            ('TRI', 'Tributário'),
            ('EMP', 'Empresarial'),
        ],
        default='CIV'
    )

    subcategories = models.JSONField(
        'Subcategorias',
        default=list,
        help_text='Lista de tags para classificação fina'
    )

    # Tribunal e órgão
    tribunal = models.CharField(
        'Tribunal',
        max_length=100,
        blank=True,
        help_text='Ex: STF, STJ, TJSP, TRT-2'
    )

    # Eficácia
    effectiveness_score = models.FloatField(
        'Score de Eficácia',
        default=0.0,
        help_text='Nota 0-1 baseada em resultados'
    )
    usage_count = models.IntegerField('Número de Usos', default=0)
    success_count = models.IntegerField('Casos de Sucesso', default=0)

    # Jurisprudência vinculada
    related_precedents = models.JSONField(
        'Precedentes Relacionados',
        default=list,
        help_text='IDs de jurisprudências que apoiam este argumento'
    )

    # Autoria
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='legal_arguments',
        verbose_name='Criado por'
    )

    # Status
    status = models.CharField(
        'Status',
        max_length=20,
        choices=[
            ('draft', 'Rascunho'),
            ('review', 'Em Revisão'),
            ('approved', 'Aprovado'),
            ('archived', 'Arquivado'),
        ],
        default='draft'
    )

    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    last_used_at = models.DateTimeField('Usado pela última vez em', null=True, blank=True)

    class Meta:
        verbose_name = 'Argumento Jurídico'
        verbose_name_plural = 'Argumentos Jurídicos'
        ordering = ['-effectiveness_score', '-usage_count']
        indexes = [
            models.Index(fields=['specialty', 'category']),
            models.Index(fields=['tribunal']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.title

    def increment_usage(self):
        """Incrementa contador de uso"""
        self.usage_count += 1
        from django.utils import timezone
        self.last_used_at = timezone.now()
        self.save(update_fields=['usage_count', 'last_used_at'])

    def record_success(self):
        """Registra sucesso"""
        self.success_count += 1
        self._update_effectiveness()
        self.save(update_fields=['success_count', 'effectiveness_score'])

    def _update_effectiveness(self):
        """Atualiza score de eficácia"""
        if self.usage_count > 0:
            self.effectiveness_score = self.success_count / self.usage_count


class ArgumentCollection(models.Model):
    """
    Coleção de argumentos organizados por tema.

    Exemplos:
    - "Argumentos para Danos Morais"
    - "Teses Previdenciárias"
    - "Fundamentações Trabalhistas"
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField('Nome', max_length=500)
    description = models.TextField('Descrição', blank=True)

    # Argumentos na coleção
    arguments = models.ManyToManyField(
        LegalArgument,
        related_name='collections',
        blank=True,
        verbose_name='Argumentos'
    )

    # Autoria
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='argument_collections',
        verbose_name='Criado por'
    )

    # Visibilidade
    is_public = models.BooleanField(
        'Pública',
        default=False,
        help_text='Se true, visível para todos os usuários'
    )

    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Coleção de Argumentos'
        verbose_name_plural = 'Coleções de Argumentos'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class ArgumentUsage(models.Model):
    """
    Registro de uso de um argumento em um documento/caso.

    Permite:
    - Rastrear onde cada argumento foi usado
    - Medir eficácia real
    - Sugerir argumentos similares
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Argumento usado
    argument = models.ForeignKey(
        LegalArgument,
        on_delete=models.CASCADE,
        related_name='usages',
        verbose_name='Argumento'
    )

    # Contexto de uso
    document_id = models.UUIDField(
        'ID do Documento',
        null=True,
        blank=True,
        help_text='ID do documento onde foi usado'
    )
    case_id = models.UUIDField(
        'ID do Caso',
        null=True,
        blank=True,
        help_text='ID do caso onde foi usado'
    )

    # Seção do documento
    section_title = models.CharField(
        'Seção',
        max_length=200,
        blank=True,
        help_text='Título da seção onde foi inserido'
    )

    # Resultado (preenchido após julgamento)
    outcome = models.CharField(
        'Resultado',
        max_length=50,
        choices=[
            ('favorable', 'Favorável'),
            ('unfavorable', 'Desfavorável'),
            ('mixed', 'Misto'),
            ('pending', 'Pendente'),
        ],
        default='pending'
    )

    # Timestamps
    used_at = models.DateTimeField('Usado em', auto_now_add=True)
    outcome_recorded_at = models.DateTimeField('Resultado registrado em', null=True, blank=True)

    class Meta:
        verbose_name = 'Uso de Argumento'
        verbose_name_plural = 'Usos de Argumentos'
        ordering = ['-used_at']
        indexes = [
            models.Index(fields=['argument', '-used_at']),
        ]

    def __str__(self):
        return f'{self.argument.title} - {self.used_at.strftime("%d/%m/%Y")}'
