"""
Models para Integração com Tribunais (e-SAJ/PJe).

Funcionalidades:
- Conexão com APIs de tribunais
- Consulta processual
- Protocolo de petições
- Sincronização de andamentos
"""

import uuid
from django.db import models
from django.conf import settings


class TribunalIntegration(models.Model):
    """
    Configuração de integração com um tribunal.

    Suporta:
    - e-SAJ (São Paulo, Minas Gerais, etc.)
    - PJe (Justiça do Trabalho, Federal, Eleitoral)
    - Outros sistemas (Eproc, Projudi, etc.)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Identificação
    name = models.CharField('Nome', max_length=200)
    code = models.CharField(
        'Código',
        max_length=20,
        unique=True,
        help_text='Ex: TJSP, TJMG, TRT-2, JFSP'
    )

    # Tipo de sistema
    system_type = models.CharField(
        'Tipo de Sistema',
        max_length=20,
        choices=[
            ('esaj', 'e-SAJ'),
            ('pje', 'PJe'),
            ('eproc', 'Eproc'),
            ('projudi', 'Projudi'),
            ('outro', 'Outro'),
        ],
        default='esaj'
    )

    # Configuração de conexão
    api_endpoint = models.URLField(
        'Endpoint da API',
        blank=True,
        help_text='URL base da API do tribunal'
    )
    requires_certificate = models.BooleanField(
        'Requer Certificado Digital',
        default=True
    )
    certificate_file = models.FileField(
        'Arquivo do Certificado',
        upload_to='integrations/certificates/',
        blank=True,
        null=True
    )
    certificate_password = models.CharField(
        'Senha do Certificado',
        max_length=500,
        blank=True
    )

    # Credenciais
    username = models.CharField('Usuário', max_length=200, blank=True)
    password = models.CharField('Senha', max_length=500, blank=True)
    api_key = models.CharField('API Key', max_length=500, blank=True)

    # Status
    is_active = models.BooleanField('Ativo', default=True)
    last_connection_test = models.DateTimeField(
        'Último teste de conexão',
        null=True,
        blank=True
    )
    connection_status = models.CharField(
        'Status da Conexão',
        max_length=20,
        choices=[
            ('connected', 'Conectado'),
            ('error', 'Erro'),
            ('testing', 'Testando'),
            ('unknown', 'Desconhecido'),
        ],
        default='unknown'
    )

    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Integração com Tribunal'
        verbose_name_plural = 'Integrações com Tribunais'
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['system_type']),
        ]

    def __str__(self):
        return f'{self.name} ({self.code})'


class ProcessSync(models.Model):
    """
    Sincronização de processo com tribunal.

    Armazena o histórico de sincronizações de um processo.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Tribunal
    tribunal = models.ForeignKey(
        TribunalIntegration,
        on_delete=models.CASCADE,
        related_name='process_syncs',
        verbose_name='Tribunal'
    )

    # Processo
    process_number = models.CharField(
        'Número do Processo',
        max_length=50,
        db_index=True
    )
    case_id = models.UUIDField(
        'ID do Caso (interno)',
        null=True,
        blank=True,
        help_text='ID do caso no Verus.AI'
    )

    # Status da sincronização
    status = models.CharField(
        'Status',
        max_length=20,
        choices=[
            ('pending', 'Pendente'),
            ('syncing', 'Sincronizando'),
            ('completed', 'Completo'),
            ('error', 'Erro'),
        ],
        default='pending'
    )

    # Dados sincronizados
    last_sync_at = models.DateTimeField('Última sincronização', null=True, blank=True)
    next_sync_at = models.DateTimeField('Próxima sincronização', null=True, blank=True)
    sync_count = models.IntegerField('Número de sincronizações', default=0)

    # Erros
    last_error = models.TextField('Último erro', blank=True)
    last_error_at = models.DateTimeField('Erro em', null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Sincronização de Processo'
        verbose_name_plural = 'Sincronizações de Processo'
        ordering = ['-last_sync_at']
        unique_together = [['tribunal', 'process_number']]
        indexes = [
            models.Index(fields=['process_number']),
            models.Index(fields=['case_id']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.process_number} - {self.tribunal.code}'


class ProcessMovement(models.Model):
    """
    Movimentação processual sincronizada do tribunal.

    Armazena andamentos, despachos, decisões, etc.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Processo
    process_sync = models.ForeignKey(
        ProcessSync,
        on_delete=models.CASCADE,
        related_name='movements',
        verbose_name='Sincronização'
    )

    # Dados da movimentação
    movement_date = models.DateTimeField('Data da Movimentação')
    movement_code = models.CharField(
        'Código da Movimentação',
        max_length=50,
        blank=True,
        help_text='Código CNM do tribunal'
    )
    movement_description = models.TextField('Descrição')

    # Complementos
    complement = models.TextField('Complemento', blank=True)
    document_id = models.CharField(
        'ID do Documento',
        max_length=100,
        blank=True,
        help_text='ID do documento no tribunal'
    )

    # Origem
    source = models.CharField(
        'Origem',
        max_length=50,
        default='tribunal',
        help_text='Fonte da movimentação'
    )

    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Movimentação Processual'
        verbose_name_plural = 'Movimentações Processuais'
        ordering = ['-movement_date']
        indexes = [
            models.Index(fields=['process_sync', '-movement_date']),
            models.Index(fields=['movement_code']),
        ]

    def __str__(self):
        return f'{self.movement_code} - {self.movement_date.strftime("%d/%m/%Y")}'


class PetitionProtocol(models.Model):
    """
    Protocolo de petição eletrônica.

    Registra petições protocoladas nos tribunais.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Tribunal
    tribunal = models.ForeignKey(
        TribunalIntegration,
        on_delete=models.CASCADE,
        related_name='petitions',
        verbose_name='Tribunal'
    )

    # Processo
    process_number = models.CharField(
        'Número do Processo',
        max_length=50,
        blank=True,
        help_text='Vazio para protocolo inicial'
    )

    # Petição
    petition_type = models.CharField(
        'Tipo de Petição',
        max_length=100,
        choices=[
            ('inicial', 'Petição Inicial'),
            ('contestacao', 'Contestação'),
            ('replica', 'Réplica'),
            ('recurso', 'Recurso'),
            ('pedido', 'Pedido'),
            ('outro', 'Outro'),
        ],
        default='outro'
    )
    petition_title = models.CharField('Título', max_length=500)
    petition_content = models.TextField('Conteúdo')

    # Documentos anexados
    attachments = models.JSONField(
        'Anexos',
        default=list,
        help_text='Lista de documentos anexados'
    )

    # Protocolo
    protocol_number = models.CharField(
        'Número do Protocolo',
        max_length=100,
        blank=True,
        help_text='Número gerado pelo tribunal'
    )
    protocol_date = models.DateTimeField('Data do Protocolo', null=True, blank=True)
    protocol_receipt = models.FileField(
        'Recibo do Protocolo',
        upload_to='integrations/protocols/',
        blank=True,
        null=True
    )

    # Status
    status = models.CharField(
        'Status',
        max_length=20,
        choices=[
            ('draft', 'Rascunho'),
            ('sending', 'Enviando'),
            ('sent', 'Enviada'),
            ('confirmed', 'Confirmada'),
            ('rejected', 'Rejeitada'),
            ('error', 'Erro'),
        ],
        default='draft'
    )

    # Erros
    last_error = models.TextField('Último erro', blank=True)
    last_error_at = models.DateTimeField('Erro em', null=True, blank=True)

    # Autoria
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='filed_petitions',
        verbose_name='Criado por'
    )

    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Protocolo de Petição'
        verbose_name_plural = 'Protocolos de Petição'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['process_number']),
            models.Index(fields=['protocol_number']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.petition_title} - {self.protocol_number or "Não protocolado"}'
