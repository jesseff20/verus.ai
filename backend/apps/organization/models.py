"""
Models de organização: Órgão e Unidade.

Estrutura:
  Organ  (Procuradoria/Órgão)
    └─ Unit  (Gerência/Unidade interna do órgão)
         └─ User  (FK organ + FK unit em accounts.User)
"""
import uuid
from django.db import models


UF_CHOICES = [
    ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
    ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'),
    ('ES', 'Espírito Santo'), ('GO', 'Goiás'), ('MA', 'Maranhão'),
    ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'), ('MG', 'Minas Gerais'),
    ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'), ('PE', 'Pernambuco'),
    ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
    ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'),
    ('SC', 'Santa Catarina'), ('SP', 'São Paulo'), ('SE', 'Sergipe'),
    ('TO', 'Tocantins'),
]


class Organ(models.Model):
    """
    Órgão público que utiliza a plataforma (ex: Procuradoria-Geral do Município de Serra/ES).
    Multi-tenancy: todos os modelos de negócio filtram por organ.
    """
    ORGAN_TYPE_CHOICES = [
        ('pgm', 'Procuradoria-Geral do Município'),
        ('pge', 'Procuradoria-Geral do Estado'),
        ('pgi', 'Procuradoria-Geral Instituto/Autarquia'),
        ('other', 'Outro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Nome do Órgão', max_length=200)
    short_name = models.CharField('Sigla', max_length=30)
    organ_type = models.CharField(
        'Tipo', max_length=10, choices=ORGAN_TYPE_CHOICES, default='pgm'
    )
    cnpj = models.CharField('CNPJ', max_length=18, blank=True)
    state = models.CharField('Estado (UF)', max_length=2, choices=UF_CHOICES)
    city = models.CharField('Município', max_length=100)
    address = models.CharField('Endereço', max_length=300, blank=True)
    phone = models.CharField('Telefone', max_length=20, blank=True)
    email = models.EmailField('E-mail institucional', blank=True)
    website = models.URLField('Site', blank=True)
    logo = models.ImageField('Logotipo', upload_to='organs/logos/', blank=True, null=True)

    # Configurações da plataforma para este órgão
    settings = models.JSONField('Configurações', default=dict, blank=True)

    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Órgão'
        verbose_name_plural = 'Órgãos'
        ordering = ['state', 'name']

    def __str__(self):
        return f'{self.short_name} — {self.city}/{self.state}'


class Unit(models.Model):
    """
    Unidade/Gerência interna de um Órgão (ex: Gerência Judicial 1º Grau).
    Corresponde às swim lanes do fluxo BPMN: cada unidade tem um conjunto de papéis.
    """
    UNIT_TYPE_CHOICES = [
        ('judicial_1', 'Gerência Judicial — 1º Grau'),
        ('judicial_2', 'Gerência Judicial — 2º Grau'),
        ('administrative', 'Gerência Administrativa'),
        ('gabinete', 'Gabinete da Procuradoria-Geral'),
        ('general', 'Geral / Sem distinção'),
        ('other', 'Outra'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organ = models.ForeignKey(
        Organ, on_delete=models.CASCADE,
        related_name='units', verbose_name='Órgão'
    )
    name = models.CharField('Nome da Unidade', max_length=200)
    short_name = models.CharField('Sigla', max_length=30, blank=True)
    unit_type = models.CharField(
        'Tipo', max_length=20, choices=UNIT_TYPE_CHOICES, default='general'
    )
    description = models.TextField('Descrição', blank=True)

    is_active = models.BooleanField('Ativa', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Unidade'
        verbose_name_plural = 'Unidades'
        ordering = ['organ', 'name']
        unique_together = [('organ', 'name')]

    def __str__(self):
        return f'{self.organ.short_name} › {self.name}'
