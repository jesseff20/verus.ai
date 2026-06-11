"""
Models de Jurisprudência — Radar de Precedentes.

Models:
  - JurisprudenceSearch: Pesquisa de jurisprudência feita pelo usuário
  - JurisprudenceResult: Resultado individual de pesquisa (precedente)
"""
from django.db import models
from django.conf import settings
import uuid


class JurisprudenceSearch(models.Model):
    """
    Pesquisa de jurisprudência realizada pelo usuário.
    Cada busca pode gerar múltiplos resultados (JurisprudenceResult).
    """
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('completed', 'Concluída'),
        ('failed', 'Falhou'),
    ]

    SPECIALTY_CHOICES = [
        ('CIV', 'Cível'),
        ('PEN', 'Penal'),
        ('TRB', 'Trabalhista'),
        ('ADM', 'Administrativo'),
        ('CON', 'Constitucional'),
        ('TRI', 'Tributário'),
        ('FAM', 'Família'),
        ('EMP', 'Empresarial'),
        ('AMB', 'Ambiental'),
        ('OUT', 'Outros'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='jurisprudence_searches',
        verbose_name='Usuário',
    )
    query = models.TextField(verbose_name='Consulta')
    specialty = models.CharField(
        max_length=3,
        choices=SPECIALTY_CHOICES,
        blank=True,
        null=True,
        verbose_name='Especialidade',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Status',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        app_label = 'jurisprudence'
        verbose_name = 'Pesquisa de Jurisprudência'
        verbose_name_plural = 'Pesquisas de Jurisprudência'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — {self.query[:60]}'


class JurisprudenceResult(models.Model):
    """
    Resultado individual de pesquisa de jurisprudência (um precedente).
    Relacionado a uma JurisprudenceSearch.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    search = models.ForeignKey(
        JurisprudenceSearch,
        on_delete=models.CASCADE,
        related_name='results',
        verbose_name='Pesquisa',
        null=True,
        blank=True,
    )

    # Identificação do precedente
    tribunal = models.CharField(max_length=50, verbose_name='Tribunal')
    case_number = models.CharField(
        max_length=100, blank=True, null=True, verbose_name='Número do processo'
    )
    relator = models.CharField(
        max_length=200, blank=True, null=True, verbose_name='Relator'
    )
    organ = models.CharField(
        max_length=200, blank=True, null=True, verbose_name='Órgão julgador'
    )

    # Conteúdo
    summary = models.TextField(default='', verbose_name='Ementa/Resumo')
    full_text_url = models.URLField(
        max_length=500, blank=True, null=True, verbose_name='URL do inteiro teor'
    )

    # Metadados de relevância
    relevance_score = models.FloatField(default=0.0, verbose_name='Score de relevância')
    judgment_date = models.DateTimeField(
        null=True, blank=True, verbose_name='Data do julgamento'
    )

    # Dados legados (mantidos para compatibilidade)
    source = models.CharField(max_length=100, blank=True, verbose_name='Fonte')
    content = models.JSONField(default=dict, blank=True, verbose_name='Dados brutos')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')

    class Meta:
        app_label = 'jurisprudence'
        verbose_name = 'Resultado de Jurisprudência'
        verbose_name_plural = 'Resultados de Jurisprudência'
        ordering = ['-relevance_score', '-judgment_date']

    def __str__(self):
        return f'{self.tribunal} — {self.case_number or "s/n"}'
