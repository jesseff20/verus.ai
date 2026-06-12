"""
Models do app Cases — Gestão de Casos Jurídicos do Verus.AI.
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


# ─────────────────────────────────────────────────────────────────────────────
# CLIENT (Gestão de Clientes)
# ─────────────────────────────────────────────────────────────────────────────

class Client(models.Model):
    """Cliente do escritório — pessoa física ou jurídica."""

    TYPE_CHOICES = [
        ('pessoa_fisica', 'Pessoa Física'),
        ('pessoa_juridica', 'Pessoa Jurídica'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=300, verbose_name='Nome')
    client_type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default='pessoa_fisica',
        verbose_name='Tipo',
    )
    cpf_cnpj = models.CharField(max_length=20, blank=True, db_index=True, verbose_name='CPF/CNPJ')
    rg = models.CharField(max_length=20, blank=True, verbose_name='RG')
    email = models.EmailField(blank=True, verbose_name='E-mail')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Telefone')
    phone_secondary = models.CharField(max_length=20, blank=True, verbose_name='Telefone Secundário')

    # Endereço
    address = models.CharField(max_length=500, blank=True, verbose_name='Endereço')
    city = models.CharField(max_length=100, blank=True, verbose_name='Cidade')
    state = models.CharField(max_length=2, blank=True, verbose_name='UF')
    zipcode = models.CharField(max_length=10, blank=True, verbose_name='CEP')

    # Pessoa Jurídica
    company_name = models.CharField(max_length=300, blank=True, verbose_name='Razão Social')
    contact_person = models.CharField(max_length=200, blank=True, verbose_name='Pessoa de Contato')

    # Relacionamento
    responsible_lawyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='clients',
        verbose_name='Advogado Responsável',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='created_clients',
        verbose_name='Criado por',
    )

    # Portal do Cliente
    portal_password = models.CharField(
        max_length=128, blank=True,
        verbose_name='Senha do Portal',
        help_text='Senha hash para acesso ao portal do cliente',
    )
    portal_active = models.BooleanField(
        default=False,
        verbose_name='Portal Ativo',
        help_text='Habilita acesso do cliente ao portal',
    )

    # Meta
    notes = models.TextField(blank=True, verbose_name='Observações')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['responsible_lawyer']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['cpf_cnpj'],
                condition=models.Q(cpf_cnpj__gt=''),
                name='unique_cpf_cnpj_when_set',
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_client_type_display()})"


class LegalCaseManager(models.Manager):
    """Manager padrão que filtra casos com soft delete (deleted_at não nulo)."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class LegalCaseAllObjects(models.Manager):
    """Manager auxiliar que retorna todos os casos, incluindo deletados."""

    def get_queryset(self):
        return super().get_queryset()


class LegalCase(models.Model):
    """Caso jurídico (processo ou demanda extrajudicial)."""

    ESPECIALIDADE_CHOICES = [
        ('civel', 'Cível'),
        ('criminal', 'Criminal'),
        ('trabalhista', 'Trabalhista'),
        ('tributario', 'Tributário'),
        ('administrativo', 'Administrativo'),
        ('previdenciario', 'Previdenciário'),
        ('familia', 'Família e Sucessões'),
        ('empresarial', 'Empresarial'),
        ('ambiental', 'Ambiental'),
        ('consumidor', 'Direito do Consumidor'),
        ('imobiliario', 'Imobiliário'),
        ('outros', 'Outros'),
    ]

    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('aguardando', 'Aguardando'),
        ('suspenso', 'Suspenso'),
        ('encerrado', 'Encerrado'),
        ('arquivado', 'Arquivado'),
        ('ganho', 'Ganho'),
        ('perdido', 'Perdido'),
        ('acordo', 'Acordo'),
    ]

    FASE_CHOICES = [
        ('inicial', 'Fase Inicial'),
        ('instrucao', 'Instrução'),
        ('julgamento', 'Julgamento'),
        ('recursal', 'Recursal'),
        ('execucao', 'Execução'),
        ('transitado', 'Transitado em Julgado'),
        ('extrajudicial', 'Extrajudicial'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Identificação
    numero_processo = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Número do Processo',
        help_text='Formato CNJ: NNNNNNN-DD.AAAA.J.TT.OOOO',
    )
    titulo = models.CharField(
        max_length=255,
        verbose_name='Título / Assunto',
        help_text='Descrição resumida do caso',
    )
    especialidade = models.CharField(
        max_length=20,
        choices=ESPECIALIDADE_CHOICES,
        default='civel',
        verbose_name='Especialidade Jurídica',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ativo',
        verbose_name='Status',
    )
    fase = models.CharField(
        max_length=20,
        choices=FASE_CHOICES,
        default='inicial',
        verbose_name='Fase Processual',
    )

    # Cliente vinculado
    client = models.ForeignKey(
        Client, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='cases',
        verbose_name='Cliente',
    )

    # Partes
    cliente_nome = models.CharField(
        max_length=255,
        verbose_name='Cliente / Parte Representada',
    )
    cliente_cpf_cnpj = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='CPF/CNPJ do Cliente',
    )
    parte_contraria = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Parte Contrária',
    )
    parte_contraria_cpf_cnpj = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='CPF/CNPJ da Parte Contrária',
    )

    # Localização processual
    tribunal = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Tribunal',
        help_text='Ex: TJRJ, TRT-1, STJ',
    )
    vara_juizo = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Vara / Juízo',
        help_text='Ex: 3ª Vara Cível da Comarca do Rio de Janeiro',
    )
    comarca = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Comarca / Seção Judiciária',
    )

    # Financeiro
    valor_causa = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Valor da Causa (R$)',
    )
    honorarios_combinados = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Honorários Combinados (R$)',
    )

    # Responsável
    advogado_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='casos_responsavel',
        verbose_name='Procurador Responsável',
    )

    # Datas
    data_distribuicao = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Distribuição / Ajuizamento',
    )
    data_encerramento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Encerramento',
    )

    # Descrição
    descricao = models.TextField(
        blank=True,
        verbose_name='Descrição do Caso',
        help_text='Resumo dos fatos, tese jurídica e estratégia',
    )
    observacoes = models.TextField(
        blank=True,
        verbose_name='Observações Internas',
    )

    # Órgão (procuradoria responsável — multi-tenancy)
    organ = models.ForeignKey(
        'organization.Organ',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='legal_cases',
        verbose_name='Órgão (Procuradoria)',
        help_text='Procuradoria responsável pelo caso',
    )

    # Fluxo de trabalho ativo
    active_flow = models.OneToOneField(
        'workflow_execution.FlowInstance',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='linked_case',
        verbose_name='Fluxo ativo',
        help_text='Instância de fluxo de trabalho em andamento para este caso',
    )

    # Controle
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='casos_criados',
        verbose_name='Criado por',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name='Deletado em',
        help_text='Preenchido ao realizar soft delete do caso',
    )

    # Managers
    objects = LegalCaseManager()
    all_objects = LegalCaseAllObjects()

    class Meta:
        verbose_name = 'Caso Jurídico'
        verbose_name_plural = 'Casos Jurídicos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['especialidade']),
            models.Index(fields=['advogado_responsavel']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        ref = self.numero_processo or self.titulo
        return f"{ref} ({self.get_especialidade_display()})"

    def soft_delete(self):
        """Realiza soft delete do caso, preservando o registro no banco."""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def delete(self, *args, **kwargs):
        """Override delete to force soft-delete. Use hard_delete() for actual deletion."""
        self.soft_delete()

    def hard_delete(self, *args, **kwargs):
        """Actually delete from database. USE WITH CAUTION."""
        super().delete(*args, **kwargs)

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    @property
    def total_prazos_pendentes(self):
        return self.prazos.filter(status='pendente').count()

    @property
    def total_tarefas_pendentes(self):
        return self.tarefas.filter(status__in=['pendente', 'em_andamento']).count()


class LegalDeadline(models.Model):
    """Prazo processual ou legal vinculado a um caso."""

    TIPO_CHOICES = [
        ('processual', 'Processual'),
        ('recursal', 'Recursal'),
        ('extrajudicial', 'Extrajudicial'),
        ('contratual', 'Contratual'),
        ('administrativo', 'Administrativo'),
        ('prescricional', 'Prescricional'),
        ('decadencial', 'Decadencial'),
        ('outro', 'Outro'),
    ]

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em Andamento'),
        ('concluido', 'Concluído'),
        ('atrasado', 'Atrasado'),
        ('cancelado', 'Cancelado'),
    ]

    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    caso = models.ForeignKey(
        LegalCase,
        on_delete=models.CASCADE,
        related_name='prazos',
        verbose_name='Caso',
    )

    titulo = models.CharField(max_length=255, verbose_name='Título do Prazo')
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='processual', verbose_name='Tipo')
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default='media', verbose_name='Prioridade')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente', verbose_name='Status')

    data_prazo = models.DateField(verbose_name='Data do Prazo')
    data_conclusao = models.DateField(null=True, blank=True, verbose_name='Data de Conclusão')

    # Campos para prazos recursais (#6)
    appeal_type = models.CharField(
        max_length=40,
        blank=True,
        verbose_name='Tipo de Recurso',
        help_text='Chave do tipo de recurso (ex: apelacao, agravo_instrumento)',
    )
    base_legal = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Base Legal',
        help_text='Fundamentação legal do prazo (ex: CPC art. 1.003)',
    )
    auto_generated = models.BooleanField(
        default=False,
        verbose_name='Gerado Automaticamente',
        help_text='Indica se o prazo foi criado automaticamente pelo sistema',
    )

    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prazos_responsavel',
        verbose_name='Responsável',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='prazos_criados',
        verbose_name='Criado por',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Prazo Processual'
        verbose_name_plural = 'Prazos Processuais'
        ordering = ['data_prazo', 'prioridade']
        indexes = [
            models.Index(fields=['caso', 'status']),
            models.Index(fields=['data_prazo']),
            models.Index(fields=['responsavel']),
        ]

    def __str__(self):
        return f"{self.titulo} — {self.data_prazo} ({self.caso})"


class CaseTask(models.Model):
    """Tarefa vinculada a um caso jurídico."""

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em Andamento'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
    ]

    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    caso = models.ForeignKey(
        LegalCase,
        on_delete=models.CASCADE,
        related_name='tarefas',
        verbose_name='Caso',
    )

    titulo = models.CharField(max_length=255, verbose_name='Título da Tarefa')
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente', verbose_name='Status')
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default='media', verbose_name='Prioridade')

    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tarefas_responsavel',
        verbose_name='Responsável',
    )
    data_limite = models.DateField(null=True, blank=True, verbose_name='Data Limite')
    data_conclusao = models.DateField(null=True, blank=True, verbose_name='Data de Conclusão')

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='tarefas_criadas',
        verbose_name='Criado por',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Tarefa do Caso'
        verbose_name_plural = 'Tarefas do Caso'
        ordering = ['data_limite', 'prioridade', '-created_at']
        indexes = [
            models.Index(fields=['caso', 'status']),
            models.Index(fields=['responsavel']),
            models.Index(fields=['data_limite']),
        ]

    def __str__(self):
        return f"{self.titulo} — {self.caso}"


class Audiencia(models.Model):
    """Audiência judicial vinculada a um caso."""

    TIPO_CHOICES = [
        ('instrucao', 'Audiência de Instrução'),
        ('conciliacao', 'Audiência de Conciliação'),
        ('julgamento', 'Sessão de Julgamento'),
        ('depoimento', 'Depoimento Pessoal'),
        ('pericial', 'Audiência Pericial'),
        ('una', 'Audiência Una'),
        ('outro', 'Outro'),
    ]

    STATUS_CHOICES = [
        ('agendada', 'Agendada'),
        ('realizada', 'Realizada'),
        ('cancelada', 'Cancelada'),
        ('adiada', 'Adiada'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    caso = models.ForeignKey(
        LegalCase,
        on_delete=models.CASCADE,
        related_name='audiencias',
        verbose_name='Caso',
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='instrucao')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='agendada')
    data_hora = models.DateTimeField(verbose_name='Data e Hora')
    local = models.CharField(max_length=300, blank=True, verbose_name='Local / Sala')
    juiz = models.CharField(max_length=200, blank=True, verbose_name='Juiz')
    resultado = models.TextField(blank=True, verbose_name='Resultado / Ata')
    observacoes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Audiência'
        verbose_name_plural = 'Audiências'
        ordering = ['data_hora']
        indexes = [
            models.Index(fields=['caso', 'status']),
            models.Index(fields=['data_hora']),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.caso} ({self.data_hora.date()})"


class MovimentacaoFinanceira(models.Model):
    """Movimentação financeira vinculada a um caso."""

    TIPO_CHOICES = [
        ('honorario', 'Honorário Recebido'),
        ('despesa', 'Despesa'),
        ('reembolso', 'Reembolso'),
        ('custas', 'Custas Processuais'),
        ('pericia', 'Perícia'),
        ('outro', 'Outro'),
    ]

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
        ('cancelado', 'Cancelado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    caso = models.ForeignKey(
        LegalCase,
        on_delete=models.CASCADE,
        related_name='movimentacoes_financeiras',
        verbose_name='Caso',
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='honorario')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    descricao = models.CharField(max_length=300, verbose_name='Descrição')
    valor = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Valor (R$)')
    data_vencimento = models.DateField(null=True, blank=True, verbose_name='Data de Vencimento')
    data_pagamento = models.DateField(null=True, blank=True, verbose_name='Data de Pagamento')
    comprovante_url = models.URLField(blank=True, verbose_name='URL do Comprovante')
    observacoes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='movimentacoes_criadas',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Movimentação Financeira'
        verbose_name_plural = 'Movimentações Financeiras'
        ordering = ['-data_vencimento']
        indexes = [
            models.Index(fields=['caso', 'status']),
            models.Index(fields=['data_vencimento']),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} R$ {self.valor} — {self.caso}"


class CasePhase(models.Model):
    """Fase processual de um caso jurídico brasileiro."""

    STATUS_CHOICES = [
        ('completed', 'Concluída'),
        ('in_progress', 'Em Andamento'),
        ('pending', 'Pendente'),
        ('skipped', 'Não Aplicável'),
        ('overdue', 'Atrasada'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    caso = models.ForeignKey(
        LegalCase,
        on_delete=models.CASCADE,
        related_name='phases',
        verbose_name='Caso',
    )
    order = models.IntegerField(verbose_name='Ordem')
    name = models.CharField(max_length=200, verbose_name='Nome da Fase')
    description = models.TextField(blank=True, verbose_name='Descrição')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Status',
    )

    # Datas
    estimated_date = models.DateField(null=True, blank=True, verbose_name='Data Estimada')
    actual_date = models.DateField(null=True, blank=True, verbose_name='Data Real')

    # Reabertura
    reopened_at = models.DateTimeField(null=True, blank=True, verbose_name='Reaberta em')
    reopened_reason = models.TextField(blank=True, verbose_name='Motivo da Reabertura')

    # Atraso
    overdue_since = models.DateField(null=True, blank=True, verbose_name='Atrasada desde')

    # Ações
    copilot_prompt = models.TextField(blank=True, verbose_name='Prompt para Copilot')
    suggested_documents = models.JSONField(default=list, blank=True, verbose_name='Documentos Sugeridos')

    notes = models.TextField(blank=True, verbose_name='Observações')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')

    class Meta:
        verbose_name = 'Fase Processual'
        verbose_name_plural = 'Fases Processuais'
        ordering = ['order']
        unique_together = ['caso', 'order']
        indexes = [
            models.Index(fields=['caso', 'status']),
        ]

    def __str__(self):
        return f"{self.order}. {self.name} ({self.get_status_display()}) — {self.caso}"


class LegalNotification(models.Model):
    """Notificação/Citação/Intimação jurídica vinculada ao caso"""

    TIPO_CHOICES = [
        ('citacao_pessoal', 'Citação Pessoal'),
        ('citacao_hora_certa', 'Citação por Hora Certa'),
        ('citacao_edital', 'Citação por Edital'),
        ('citacao_eletronica', 'Citação Eletrônica'),
        ('intimacao_pessoal', 'Intimação Pessoal'),
        ('intimacao_dje', 'Intimação via DJe'),
        ('intimacao_eletronica', 'Intimação Eletrônica'),
        ('intimacao_publicacao', 'Intimação por Publicação'),
        ('notificacao_extrajudicial', 'Notificação Extrajudicial'),
        ('notificacao_judicial', 'Notificação Judicial'),
        ('carta_precatoria', 'Carta Precatória'),
        ('carta_rogatoria', 'Carta Rogatória'),
        ('mandado_citacao', 'Mandado de Citação'),
        ('mandado_intimacao', 'Mandado de Intimação'),
    ]
    DIRECAO_CHOICES = [
        ('recebida', 'Recebida'),
        ('enviada', 'Enviada'),
    ]
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('efetivada', 'Efetivada'),
        ('frustrada', 'Frustrada'),
        ('cancelada', 'Cancelada'),
    ]
    MEIO_CHOICES = [
        ('oficial_justica', 'Oficial de Justiça'),
        ('correio_ar', 'Correio (AR)'),
        ('dje', 'Diário de Justiça Eletrônico'),
        ('pje', 'PJe'),
        ('esaj', 'e-SAJ'),
        ('whatsapp', 'WhatsApp'),
        ('email', 'E-mail'),
        ('cartorio', 'Cartório de Títulos'),
        ('edital', 'Edital'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    caso = models.ForeignKey(LegalCase, on_delete=models.CASCADE, related_name='notificacoes')
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    direcao = models.CharField(max_length=10, choices=DIRECAO_CHOICES, default='recebida')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    meio = models.CharField(max_length=20, choices=MEIO_CHOICES, blank=True)

    destinatario_nome = models.CharField(max_length=300, blank=True)
    remetente = models.CharField(max_length=300, blank=True)

    data_expedicao = models.DateField(null=True, blank=True)
    data_ciencia = models.DateField(null=True, blank=True)
    data_publicacao_dje = models.DateField(null=True, blank=True)

    prazo_dias = models.IntegerField(null=True, blank=True)
    prazo_tipo = models.CharField(
        max_length=10,
        choices=[('uteis', 'Úteis'), ('corridos', 'Corridos')],
        default='uteis',
    )
    prazo_vencimento = models.DateField(null=True, blank=True)

    base_legal = models.CharField(max_length=200, blank=True)
    conteudo_resumo = models.TextField(blank=True)
    observacoes = models.TextField(blank=True)

    deadline_created = models.ForeignKey(
        'LegalDeadline', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='notification_source',
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notificação Jurídica'
        verbose_name_plural = 'Notificações Jurídicas'
        indexes = [
            models.Index(fields=['caso', 'status']),
            models.Index(fields=['tipo']),
            models.Index(fields=['prazo_vencimento']),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.get_status_display()} ({self.caso})"


class CaseDocument(models.Model):
    """Referência a documentos vinculados ao caso — vinculador universal."""

    TIPO_CHOICES = [
        ('peticao', 'Petição'),
        ('peca', 'Peça Processual'),
        ('decisao', 'Decisão / Sentença'),
        ('intimacao', 'Intimação'),
        ('contrato', 'Contrato'),
        ('procuracao', 'Procuração'),
        ('prova', 'Prova'),
        ('parecer', 'Parecer'),
        ('simulacao', 'Simulação'),
        ('copilot', 'Análise do Copilot'),
        ('documento_cliente', 'Documento do Cliente'),
        ('outros', 'Outros'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    caso = models.ForeignKey(
        LegalCase,
        on_delete=models.CASCADE,
        related_name='documentos_caso',
        verbose_name='Caso',
    )

    titulo = models.CharField(max_length=255, verbose_name='Título')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='outros', verbose_name='Tipo')
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    data_documento = models.DateField(null=True, blank=True, verbose_name='Data do Documento')

    # Referência a documento gerado pelo Verus.AI (opcional — legacy UUID field)
    generated_document_id = models.UUIDField(
        null=True, blank=True,
        verbose_name='ID do Documento Gerado',
        help_text='Referência a GeneratedDocument do intelligent_assistant',
    )

    # FK direta para documento gerado
    linked_document = models.ForeignKey(
        'intelligent_assistant.GeneratedDocument',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='case_documents',
        verbose_name='Documento Gerado (FK)',
    )

    # FK para simulação vinculada
    simulation = models.ForeignKey(
        'simulations.Simulation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='case_documents',
        verbose_name='Simulação',
    )

    # Arquivo enviado (upload direto, ex: portal do cliente)
    file = models.FileField(
        upload_to='case_documents/', null=True, blank=True,
        verbose_name='Arquivo',
    )

    # Observações adicionais
    observacoes = models.TextField(blank=True, verbose_name='Observações')

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='case_docs_criados',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Documento do Caso'
        verbose_name_plural = 'Documentos do Caso'
        ordering = ['-data_documento', '-created_at']

    def __str__(self):
        return f"{self.titulo} ({self.caso})"


class OABFeeTable(models.Model):
    """Tabela de honorários da OAB por estado."""

    STATE_CHOICES = [
        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AM', 'Amazonas'), ('AP', 'Amapá'),
        ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MG', 'Minas Gerais'), ('MS', 'Mato Grosso do Sul'),
        ('MT', 'Mato Grosso'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PE', 'Pernambuco'),
        ('PI', 'Piauí'), ('PR', 'Paraná'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
        ('RO', 'Rondônia'), ('RR', 'Roraima'), ('RS', 'Rio Grande do Sul'), ('SC', 'Santa Catarina'),
        ('SE', 'Sergipe'), ('SP', 'São Paulo'), ('TO', 'Tocantins'),
    ]

    CATEGORY_CHOICES = [
        ('civel', 'Cível'),
        ('criminal', 'Criminal'),
        ('trabalhista', 'Trabalhista'),
        ('tributario', 'Tributário'),
        ('familia', 'Família e Sucessões'),
        ('previdenciario', 'Previdenciário'),
        ('administrativo', 'Administrativo'),
        ('empresarial', 'Empresarial'),
        ('consumidor', 'Consumidor'),
        ('imobiliario', 'Imobiliário'),
        ('ambiental', 'Ambiental'),
        ('outros', 'Outros'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state = models.CharField(max_length=2, choices=STATE_CHOICES, verbose_name='Estado (UF)')
    service_category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, verbose_name='Categoria',
    )
    service_type = models.CharField(max_length=200, verbose_name='Tipo de Serviço')
    minimum_value = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        verbose_name='Valor Mínimo (R$)',
    )
    suggested_value = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        verbose_name='Valor Sugerido (R$)',
    )
    percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Percentual (%)',
        help_text='Percentual sobre o valor da causa, quando aplicável',
    )
    year = models.IntegerField(default=2024, verbose_name='Ano de Referência')

    class Meta:
        verbose_name = 'Tabela OAB de Honorários'
        verbose_name_plural = 'Tabelas OAB de Honorários'
        ordering = ['state', 'service_category', 'service_type']
        indexes = [
            models.Index(fields=['state', 'service_category']),
            models.Index(fields=['year']),
        ]

    def __str__(self):
        return f"{self.state} — {self.service_type} (R$ {self.minimum_value})"


# ─────────────────────────────────────────────────────────────────────────────
# PROTOCOLO ELETRÔNICO
# ─────────────────────────────────────────────────────────────────────────────

COURT_SYSTEM_CHOICES = [
    ('pje', 'PJe'),
    ('esaj', 'e-SAJ'),
    ('projudi', 'PROJUDI'),
    ('eproc', 'e-Proc'),
    ('sei', 'SEI'),
    ('manual', 'Manual'),
]


class ElectronicProtocol(models.Model):
    """Protocolo eletrônico (peticionamento eletrônico) vinculado a um caso."""

    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('pending', 'Pendente'),
        ('submitted', 'Protocolado'),
        ('accepted', 'Aceito'),
        ('rejected', 'Rejeitado'),
        ('error', 'Erro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    case = models.ForeignKey(
        LegalCase,
        on_delete=models.CASCADE,
        related_name='protocolos',
        verbose_name='Caso',
    )
    document = models.ForeignKey(
        CaseDocument,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='protocolos',
        verbose_name='Documento',
    )

    protocol_number = models.CharField(
        max_length=50, blank=True, verbose_name='Número do Protocolo',
    )
    court_system = models.CharField(
        max_length=10, choices=COURT_SYSTEM_CHOICES, verbose_name='Sistema do Tribunal',
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='draft', verbose_name='Status',
    )
    petition_type = models.CharField(
        max_length=100, verbose_name='Tipo de Petição',
        help_text='Ex: Petição Inicial, Contestação, Recurso',
    )

    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name='Submetido em')
    accepted_at = models.DateTimeField(null=True, blank=True, verbose_name='Aceito em')
    protocol_receipt = models.TextField(blank=True, verbose_name='Comprovante do Protocolo')
    error_message = models.TextField(blank=True, verbose_name='Mensagem de Erro')
    retry_count = models.IntegerField(default=0, verbose_name='Tentativas')

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='protocolos_criados',
        verbose_name='Criado por',
    )
    metadata = models.JSONField(default=dict, blank=True, verbose_name='Metadados')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Protocolo Eletrônico'
        verbose_name_plural = 'Protocolos Eletrônicos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['case', 'status']),
            models.Index(fields=['court_system']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return f"{self.petition_type} — {self.get_court_system_display()} ({self.get_status_display()})"


# ─────────────────────────────────────────────────────────────────────────────
# TRIBUNAL PUSH (ACOMPANHAMENTO)
# ─────────────────────────────────────────────────────────────────────────────

class TribunalPushConfig(models.Model):
    """Configuração de acompanhamento de tribunal por usuário."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tribunal_push_configs',
        verbose_name='Usuário',
    )
    court_system = models.CharField(
        max_length=10, choices=COURT_SYSTEM_CHOICES, verbose_name='Sistema do Tribunal',
    )
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    check_interval_hours = models.IntegerField(
        default=24, verbose_name='Intervalo de Verificação (horas)',
    )
    last_checked = models.DateTimeField(
        null=True, blank=True, verbose_name='Última Verificação',
    )
    notification_types = models.JSONField(
        default=list, blank=True, verbose_name='Tipos de Notificação',
        help_text='Lista de tipos de evento para monitorar',
    )
    credentials_encrypted = models.TextField(
        blank=True, verbose_name='Credenciais (criptografadas)',
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Configuração de Acompanhamento'
        verbose_name_plural = 'Configurações de Acompanhamento'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'court_system']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.get_court_system_display()} — {self.user}"


class TribunalPushEvent(models.Model):
    """Evento recebido de tribunal via push/monitoramento."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    config = models.ForeignKey(
        TribunalPushConfig,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name='Configuração',
    )
    case = models.ForeignKey(
        LegalCase,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tribunal_events',
        verbose_name='Caso',
    )
    event_type = models.CharField(
        max_length=50, verbose_name='Tipo de Evento',
        help_text='Ex: movimentacao, intimacao, publicacao, despacho',
    )
    event_date = models.DateTimeField(verbose_name='Data do Evento')
    description = models.TextField(verbose_name='Descrição')
    raw_data = models.JSONField(default=dict, blank=True, verbose_name='Dados Brutos')
    is_processed = models.BooleanField(default=False, verbose_name='Processado')
    notification_sent = models.BooleanField(default=False, verbose_name='Notificação Enviada')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Evento de Tribunal'
        verbose_name_plural = 'Eventos de Tribunal'
        ordering = ['-event_date']
        indexes = [
            models.Index(fields=['config', 'is_processed']),
            models.Index(fields=['event_type']),
            models.Index(fields=['event_date']),
        ]

    def __str__(self):
        return f"{self.event_type} — {self.event_date.date()} ({self.config})"


# ─────────────────────────────────────────────────────────────────────────────
# CONTRATOS JURÍDICOS (Honorários, Procuração, Substabelecimento)
# ─────────────────────────────────────────────────────────────────────────────

class LegalContract(models.Model):
    """Contrato jurídico — honorários, procuração ou substabelecimento."""

    CONTRACT_TYPE_CHOICES = [
        ('honorarios', 'Contrato de Honorários'),
        ('procuracao', 'Procuração'),
        ('substabelecimento', 'Substabelecimento'),
        ('prestacao_servicos', 'Contrato de Prestação de Serviços Jurídicos'),
        ('consultoria', 'Contrato de Consultoria Jurídica'),
        ('confidencialidade', 'Acordo de Confidencialidade / NDA'),
        ('parceria', 'Contrato de Parceria'),
        ('cessao_credito', 'Contrato de Cessão de Crédito'),
        ('acordo_extrajudicial', 'Acordo Extrajudicial'),
        ('distrato', 'Distrato / Rescisão Contratual'),
        ('compromisso_arbitragem', 'Compromisso Arbitral'),
        ('acordo_acionistas', 'Acordo de Acionistas'),
        ('contrato_social', 'Contrato Social'),
        ('termos_uso', 'Termos de Uso'),
        ('contrato_locacao', 'Contrato de Locação'),
        ('compra_venda', 'Contrato de Compra e Venda'),
        ('contrato_trabalho', 'Contrato de Trabalho'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('pending_signature', 'Aguardando Assinatura'),
        ('signed', 'Assinado'),
        ('cancelled', 'Cancelado'),
        ('expired', 'Expirado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    case = models.ForeignKey(
        LegalCase, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='contratos',
        verbose_name='Caso Jurídico',
    )
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE,
        related_name='contratos',
        verbose_name='Cliente',
    )
    contract_type = models.CharField(
        max_length=30, choices=CONTRACT_TYPE_CHOICES,
        verbose_name='Tipo de Contrato',
    )
    title = models.CharField(max_length=300, verbose_name='Título')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft',
        verbose_name='Status',
    )

    content_html = models.TextField(blank=True, verbose_name='Conteúdo HTML')
    generated_pdf = models.FileField(
        upload_to='contratos/pdfs/', null=True, blank=True,
        verbose_name='PDF Gerado',
    )
    uploaded_file = models.FileField(
        upload_to='contratos/uploads/', null=True, blank=True,
        verbose_name='Arquivo Uploadado',
        help_text='Arquivo PDF/DOCX uploadado para análise com IA',
    )

    signed_at = models.DateTimeField(null=True, blank=True, verbose_name='Assinado em')
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name='Expira em')

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='contratos_criados',
        verbose_name='Criado por',
    )

    metadata = models.JSONField(default=dict, blank=True, verbose_name='Metadados')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Contrato Jurídico'
        verbose_name_plural = 'Contratos Jurídicos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contract_type']),
            models.Index(fields=['status']),
            models.Index(fields=['client']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_contract_type_display()}) — {self.get_status_display()}"


class HonorariosDetail(models.Model):
    """Detalhes específicos de contrato de honorários."""

    FEE_TYPE_CHOICES = [
        ('fixed', 'Valor Fixo'),
        ('hourly', 'Por Hora'),
        ('success', 'Êxito'),
        ('mixed', 'Misto'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    contract = models.OneToOneField(
        LegalContract, on_delete=models.CASCADE,
        related_name='honorarios_detail',
        verbose_name='Contrato',
    )
    fee_type = models.CharField(
        max_length=10, choices=FEE_TYPE_CHOICES,
        verbose_name='Tipo de Honorário',
    )
    fixed_amount = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        verbose_name='Valor Fixo (R$)',
    )
    hourly_rate = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        verbose_name='Valor por Hora (R$)',
    )
    success_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Percentual de Êxito (%)',
    )
    estimated_hours = models.IntegerField(null=True, blank=True, verbose_name='Horas Estimadas')
    payment_terms = models.TextField(blank=True, verbose_name='Condições de Pagamento')
    installments = models.IntegerField(default=1, verbose_name='Parcelas')
    includes_expenses = models.BooleanField(default=False, verbose_name='Inclui Despesas')

    class Meta:
        verbose_name = 'Detalhe de Honorários'
        verbose_name_plural = 'Detalhes de Honorários'

    def __str__(self):
        return f"Honorários — {self.contract.title}"


class ProcuracaoDetail(models.Model):
    """Detalhes específicos de procuração."""

    POWERS_TYPE_CHOICES = [
        ('general', 'Poderes Gerais'),
        ('special', 'Poderes Especiais'),
        ('ad_judicia', 'Ad Judicia'),
        ('ad_judicia_extra', 'Ad Judicia et Extra'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    contract = models.OneToOneField(
        LegalContract, on_delete=models.CASCADE,
        related_name='procuracao_detail',
        verbose_name='Contrato',
    )
    powers_type = models.CharField(
        max_length=20, choices=POWERS_TYPE_CHOICES,
        verbose_name='Tipo de Poderes',
    )
    special_powers = models.TextField(blank=True, verbose_name='Poderes Especiais')
    court_scope = models.CharField(
        max_length=300, blank=True, default='Todos os foros e instâncias',
        verbose_name='Abrangência',
    )
    valid_until = models.DateField(null=True, blank=True, verbose_name='Válida até')
    is_irrevocable = models.BooleanField(default=False, verbose_name='Irrevogável')

    class Meta:
        verbose_name = 'Detalhe de Procuração'
        verbose_name_plural = 'Detalhes de Procuração'

    def __str__(self):
        return f"Procuração — {self.contract.title}"


class SubstabelecimentoDetail(models.Model):
    """Detalhes específicos de substabelecimento."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    contract = models.OneToOneField(
        LegalContract, on_delete=models.CASCADE,
        related_name='substabelecimento_detail',
        verbose_name='Contrato',
    )
    original_procuracao = models.ForeignKey(
        LegalContract, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='substabelecimentos',
        verbose_name='Procuração Original',
    )
    substabelecido_name = models.CharField(max_length=300, verbose_name='Nome do Substabelecido')
    substabelecido_oab = models.CharField(max_length=20, verbose_name='OAB do Substabelecido')
    substabelecido_oab_state = models.CharField(max_length=2, verbose_name='UF da OAB')
    with_reserve = models.BooleanField(default=True, verbose_name='Com Reserva de Poderes')
    powers_transferred = models.TextField(blank=True, verbose_name='Poderes Transferidos')
    reason = models.TextField(blank=True, verbose_name='Motivo')

    class Meta:
        verbose_name = 'Detalhe de Substabelecimento'
        verbose_name_plural = 'Detalhes de Substabelecimento'

    def __str__(self):
        return f"Substabelecimento — {self.contract.title}"


# ─────────────────────────────────────────────────────────────────────────────
# GUIA DE CUSTAS JUDICIAIS
# ─────────────────────────────────────────────────────────────────────────────

class CourtFeeGuide(models.Model):
    """Guia de custas judiciais vinculada a um caso."""

    FEE_TYPE_CHOICES = [
        ('custas_iniciais', 'Custas Iniciais'),
        ('custas_recursais', 'Custas Recursais'),
        ('custas_preparo', 'Preparo'),
        ('taxa_judiciaria', 'Taxa Judiciária'),
        ('porte_remessa', 'Porte de Remessa'),
        ('diligencia', 'Diligência'),
        ('pericia', 'Perícia'),
        ('outros', 'Outros'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('paid', 'Pago'),
        ('overdue', 'Vencido'),
        ('exempt', 'Isento'),
        ('waived', 'Justiça Gratuita'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    case = models.ForeignKey(
        LegalCase,
        on_delete=models.CASCADE,
        related_name='court_fees',
        verbose_name='Caso',
    )
    fee_type = models.CharField(
        max_length=20, choices=FEE_TYPE_CHOICES,
        verbose_name='Tipo de Custa',
    )
    court = models.CharField(max_length=100, verbose_name='Tribunal')
    state = models.CharField(max_length=2, verbose_name='UF')

    calculated_amount = models.DecimalField(
        max_digits=15, decimal_places=2,
        verbose_name='Valor Calculado (R$)',
    )
    case_value = models.DecimalField(
        max_digits=15, decimal_places=2,
        null=True, blank=True,
        verbose_name='Valor da Causa (R$)',
    )
    calculation_formula = models.TextField(
        blank=True,
        verbose_name='Fórmula de Cálculo',
    )

    due_date = models.DateField(verbose_name='Data de Vencimento')
    payment_status = models.CharField(
        max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending',
        verbose_name='Status do Pagamento',
    )
    payment_date = models.DateField(null=True, blank=True, verbose_name='Data do Pagamento')
    payment_proof = models.FileField(
        upload_to='court_fees/proofs/', null=True, blank=True,
        verbose_name='Comprovante de Pagamento',
    )
    barcode = models.CharField(
        max_length=100, blank=True,
        verbose_name='Código de Barras (Boleto)',
    )
    guide_pdf = models.FileField(
        upload_to='court_fees/guides/', null=True, blank=True,
        verbose_name='Guia PDF',
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='court_fees_created',
        verbose_name='Criado por',
    )
    notes = models.TextField(blank=True, verbose_name='Observações')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Guia de Custas'
        verbose_name_plural = 'Guias de Custas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['case', 'payment_status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['payment_status']),
        ]

    def __str__(self):
        return f"{self.get_fee_type_display()} — R$ {self.calculated_amount} ({self.case})"


# ─────────────────────────────────────────────────────────────────────────────
# ASSINATURA DIGITAL
# ─────────────────────────────────────────────────────────────────────────────

class DigitalSignature(models.Model):
    """Assinatura digital de documentos jurídicos."""

    SIGNATURE_TYPE_CHOICES = [
        ('simple', 'Assinatura Simples'),
        ('advanced', 'Assinatura Avançada'),
        ('qualified', 'Assinatura Qualificada ICP-Brasil'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='digital_signatures',
        verbose_name='Usuário',
    )
    document = models.ForeignKey(
        CaseDocument,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='signatures',
        verbose_name='Documento',
    )
    contract = models.ForeignKey(
        LegalContract,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='signatures',
        verbose_name='Contrato',
    )
    signature_type = models.CharField(
        max_length=10, choices=SIGNATURE_TYPE_CHOICES, default='simple',
        verbose_name='Tipo de Assinatura',
    )
    signature_hash = models.CharField(
        max_length=64,
        verbose_name='Hash SHA-256',
        help_text='Hash SHA-256 do conteúdo assinado',
    )
    certificate_info = models.JSONField(
        null=True, blank=True,
        verbose_name='Informações do Certificado',
    )
    ip_address = models.GenericIPAddressField(verbose_name='Endereço IP')
    signed_at = models.DateTimeField(auto_now_add=True, verbose_name='Assinado em')
    is_valid = models.BooleanField(default=True, verbose_name='Válida')
    verification_url = models.URLField(
        blank=True,
        verbose_name='URL de Verificação',
    )
    metadata = models.JSONField(default=dict, blank=True, verbose_name='Metadados')

    class Meta:
        verbose_name = 'Assinatura Digital'
        verbose_name_plural = 'Assinaturas Digitais'
        ordering = ['-signed_at']
        indexes = [
            models.Index(fields=['user', 'signed_at']),
            models.Index(fields=['signature_hash']),
            models.Index(fields=['document']),
        ]

    def __str__(self):
        doc_ref = self.document.titulo if self.document else 'Sem documento'
        return f"Assinatura {self.get_signature_type_display()} — {doc_ref} ({self.user})"


class SignatureVerification(models.Model):
    """Registro de verificação de assinatura digital."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    signature = models.ForeignKey(
        DigitalSignature,
        on_delete=models.CASCADE,
        related_name='verifications',
        verbose_name='Assinatura',
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='signature_verifications',
        verbose_name='Verificado por',
    )
    verified_at = models.DateTimeField(auto_now_add=True, verbose_name='Verificado em')
    is_valid = models.BooleanField(verbose_name='Válida')
    verification_details = models.JSONField(
        default=dict, blank=True,
        verbose_name='Detalhes da Verificação',
    )

    class Meta:
        verbose_name = 'Verificação de Assinatura'
        verbose_name_plural = 'Verificações de Assinatura'
        ordering = ['-verified_at']

    def __str__(self):
        status = 'Válida' if self.is_valid else 'Inválida'
        return f"Verificação {status} — {self.signature}"


# ─────────────────────────────────────────────────────────────────────────────
# WORKFLOW AUTOMATIZADO
# ─────────────────────────────────────────────────────────────────────────────

SPECIALTY_CHOICES = LegalCase.ESPECIALIDADE_CHOICES


class WorkflowTemplate(models.Model):
    """Template reutilizável de workflow para automação de etapas processuais."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name='Nome')
    description = models.TextField(blank=True, verbose_name='Descrição')
    specialty = models.CharField(
        max_length=50, choices=SPECIALTY_CHOICES, verbose_name='Especialidade',
    )
    steps = models.JSONField(
        default=list,
        help_text='Lista de etapas [{name, description, order, auto_advance, deadline_days}]',
    )
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='workflow_templates_created',
        verbose_name='Criado por',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Template de Workflow'
        verbose_name_plural = 'Templates de Workflow'
        ordering = ['specialty', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_specialty_display()})"


class WorkflowExecution(models.Model):
    """Execução de um workflow vinculada a um caso jurídico."""

    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('paused', 'Pausado'),
        ('completed', 'Concluído'),
        ('cancelled', 'Cancelado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        WorkflowTemplate, on_delete=models.CASCADE, related_name='executions',
        verbose_name='Template',
    )
    case = models.ForeignKey(
        LegalCase, on_delete=models.CASCADE, related_name='workflows',
        verbose_name='Caso',
    )
    current_step = models.IntegerField(default=0, verbose_name='Etapa Atual')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='active',
        verbose_name='Status',
    )
    step_history = models.JSONField(
        default=list,
        help_text='[{step, started_at, completed_at, notes}]',
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Iniciado em')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Concluído em')

    class Meta:
        verbose_name = 'Execução de Workflow'
        verbose_name_plural = 'Execuções de Workflow'
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.template.name} — {self.case} ({self.get_status_display()})"


# ─────────────────────────────────────────────────────────────────────────────
# TIMESHEET / CONTROLE DE HORAS
# ─────────────────────────────────────────────────────────────────────────────

class TimeEntry(models.Model):
    """Registro de horas trabalhadas por advogado em um caso."""

    BILLING_TYPE_CHOICES = [
        ('billable', 'Atividade Produtiva'),
        ('non_billable', 'Atividade Administrativa'),
        ('pro_bono', 'Capacitação / Formação'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    caso = models.ForeignKey(
        LegalCase, on_delete=models.CASCADE, related_name='time_entries',
    )
    advogado = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='time_entries',
    )
    date = models.DateField(verbose_name='Data')
    hours = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name='Horas',
    )
    description = models.TextField(verbose_name='Descrição da Atividade')
    billing_type = models.CharField(
        max_length=15, choices=BILLING_TYPE_CHOICES, default='billable',
    )
    hourly_rate = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name='Valor/Hora (R$)',
    )
    total_value = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        verbose_name='Valor Total (R$)',
    )
    task = models.ForeignKey(
        CaseTask, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='time_entries',
    )
    is_approved = models.BooleanField(default=False, verbose_name='Aprovado')
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='approved_time_entries',
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Registro de Horas'
        verbose_name_plural = 'Registros de Horas'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['caso', 'advogado']),
            models.Index(fields=['advogado', 'date']),
            models.Index(fields=['billing_type']),
            models.Index(fields=['is_approved']),
        ]

    def __str__(self):
        return f"{self.advogado} — {self.hours}h — {self.caso} ({self.date})"

    def save(self, *args, **kwargs):
        if self.hourly_rate and self.hours:
            self.total_value = self.hours * self.hourly_rate
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# CRM / PIPELINE DE LEADS
# ─────────────────────────────────────────────────────────────────────────────

class LeadStage(models.Model):
    """Etapa do funil de leads."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name='Nome da Etapa')
    order = models.IntegerField(verbose_name='Ordem')
    color = models.CharField(max_length=7, default='#3B82F6', verbose_name='Cor')
    is_won = models.BooleanField(default=False, verbose_name='Etapa de Ganho')
    is_lost = models.BooleanField(default=False, verbose_name='Etapa de Perda')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Etapa do Funil'
        verbose_name_plural = 'Etapas do Funil'
        ordering = ['order']

    def __str__(self):
        return self.name


class Lead(models.Model):
    """Lead / Oportunidade de negócio no funil do escritório."""

    SOURCE_CHOICES = [
        ('indicacao', 'Indicação'),
        ('site', 'Site'),
        ('google', 'Google'),
        ('instagram', 'Instagram'),
        ('whatsapp', 'WhatsApp'),
        ('telefone', 'Telefone'),
        ('evento', 'Evento'),
        ('outro', 'Outro'),
    ]
    TEMPERATURE_CHOICES = [
        ('cold', 'Frio'),
        ('warm', 'Morno'),
        ('hot', 'Quente'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=300, verbose_name='Nome')
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True, verbose_name='Telefone')
    cpf_cnpj = models.CharField(max_length=20, blank=True, verbose_name='CPF/CNPJ')
    description = models.TextField(blank=True, verbose_name='Descrição do Caso')
    specialty = models.CharField(
        max_length=20, choices=LegalCase.ESPECIALIDADE_CHOICES, blank=True,
    )
    source = models.CharField(
        max_length=15, choices=SOURCE_CHOICES, default='outro',
        verbose_name='Origem',
    )
    temperature = models.CharField(
        max_length=5, choices=TEMPERATURE_CHOICES, default='warm',
        verbose_name='Temperatura',
    )
    stage = models.ForeignKey(
        LeadStage, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='leads', verbose_name='Etapa',
    )
    estimated_value = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        verbose_name='Valor Estimado (R$)',
    )
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='leads_responsible',
        verbose_name='Responsável',
    )
    converted_client = models.ForeignKey(
        Client, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lead_origin',
    )
    converted_case = models.ForeignKey(
        LegalCase, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lead_origin',
    )
    converted_at = models.DateTimeField(
        null=True, blank=True, verbose_name='Convertido em',
    )
    next_contact_date = models.DateTimeField(
        null=True, blank=True, verbose_name='Próximo Contato',
    )
    notes = models.TextField(blank=True, verbose_name='Observações')
    intake_form_data = models.JSONField(
        default=dict, blank=True, verbose_name='Dados do Formulário',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='leads_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stage']),
            models.Index(fields=['responsible']),
            models.Index(fields=['temperature']),
            models.Index(fields=['source']),
            models.Index(fields=['next_contact_date']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_temperature_display()})"


class LeadActivity(models.Model):
    """Atividade/interação registrada em um lead."""

    ACTIVITY_TYPES = [
        ('call', 'Ligação'),
        ('email', 'E-mail'),
        ('meeting', 'Reunião'),
        ('whatsapp', 'WhatsApp'),
        ('proposal', 'Proposta Enviada'),
        ('note', 'Anotação'),
        ('stage_change', 'Mudança de Etapa'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lead = models.ForeignKey(
        Lead, on_delete=models.CASCADE, related_name='activities',
    )
    activity_type = models.CharField(max_length=15, choices=ACTIVITY_TYPES)
    description = models.TextField(verbose_name='Descrição')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Atividade do Lead'
        verbose_name_plural = 'Atividades do Lead'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_activity_type_display()} — {self.lead.name}"


# ─────────────────────────────────────────────────────────────────────────────
# KPIs GAMIFICADOS
# ─────────────────────────────────────────────────────────────────────────────

class LawyerScore(models.Model):
    """Pontuação gamificada do advogado — estilo ADVBOX Taskscore."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lawyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='scores',
    )
    period_start = models.DateField(verbose_name='Início do Período')
    period_end = models.DateField(verbose_name='Fim do Período')

    # Métricas
    cases_won = models.IntegerField(default=0, verbose_name='Casos Ganhos')
    cases_lost = models.IntegerField(default=0, verbose_name='Casos Perdidos')
    cases_settled = models.IntegerField(default=0, verbose_name='Acordos')
    deadlines_met = models.IntegerField(default=0, verbose_name='Prazos Cumpridos')
    deadlines_missed = models.IntegerField(default=0, verbose_name='Prazos Perdidos')
    tasks_completed = models.IntegerField(default=0, verbose_name='Tarefas Concluídas')
    hours_logged = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        verbose_name='Horas Registradas',
    )
    documents_generated = models.IntegerField(
        default=0, verbose_name='Documentos Gerados',
    )
    revenue_generated = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        verbose_name='Receita Gerada (R$)',
    )
    client_satisfaction = models.DecimalField(
        max_digits=3, decimal_places=1, null=True, blank=True,
        verbose_name='Satisfação do Cliente (0-10)',
    )

    # Score calculado
    total_score = models.IntegerField(default=0, verbose_name='Pontuação Total')
    rank_position = models.IntegerField(
        null=True, blank=True, verbose_name='Posição no Ranking',
    )

    # Badges/Conquistas
    badges = models.JSONField(
        default=list, blank=True, verbose_name='Conquistas',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pontuação do Advogado'
        verbose_name_plural = 'Pontuações dos Advogados'
        ordering = ['-total_score']
        unique_together = ['lawyer', 'period_start', 'period_end']
        indexes = [
            models.Index(fields=['lawyer', 'period_start']),
            models.Index(fields=['total_score']),
            models.Index(fields=['rank_position']),
        ]

    def __str__(self):
        return f"{self.lawyer} — {self.total_score} pts ({self.period_start} a {self.period_end})"

    def calculate_score(self):
        """Calcula pontuação total baseada nas métricas."""
        score = 0
        score += self.cases_won * 100
        score += self.cases_settled * 50
        score += self.deadlines_met * 20
        score -= self.deadlines_missed * 30
        score += self.tasks_completed * 10
        score += int(self.hours_logged) * 5
        score += self.documents_generated * 15
        if self.client_satisfaction:
            score += int(self.client_satisfaction * 10)
        self.total_score = max(0, score)
        return self.total_score


# ─────────────────────────────────────────────────────────────────────────────
# NFS-e (NOTA FISCAL DE SERVIÇO ELETRÔNICA)
# ─────────────────────────────────────────────────────────────────────────────

class InvoiceNFSe(models.Model):
    """Nota Fiscal de Serviço Eletrônica para honorários."""

    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('pending', 'Pendente de Envio'),
        ('processing', 'Processando'),
        ('authorized', 'Autorizada'),
        ('cancelled', 'Cancelada'),
        ('error', 'Erro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    caso = models.ForeignKey(
        LegalCase, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='notas_fiscais',
    )
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name='notas_fiscais',
    )
    contract = models.ForeignKey(
        LegalContract, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='notas_fiscais',
    )

    # Dados da NFS-e
    numero_nfse = models.CharField(
        max_length=50, blank=True, verbose_name='Número NFS-e',
    )
    codigo_verificacao = models.CharField(
        max_length=100, blank=True, verbose_name='Código de Verificação',
    )
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default='draft',
    )

    # Serviço
    descricao_servico = models.TextField(verbose_name='Descrição do Serviço')
    codigo_servico = models.CharField(
        max_length=20, default='6911-7/01',
        verbose_name='Código de Serviço CNAE',
        help_text='Atividades jurídicas: 6911-7/01',
    )
    codigo_tributacao = models.CharField(
        max_length=20, blank=True, verbose_name='Código de Tributação Municipal',
    )

    # Valores
    valor_servico = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name='Valor do Serviço (R$)',
    )
    valor_deducoes = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        verbose_name='Deduções (R$)',
    )
    base_calculo = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        verbose_name='Base de Cálculo',
    )
    aliquota_iss = models.DecimalField(
        max_digits=5, decimal_places=2, default=5.00,
        verbose_name='Alíquota ISS (%)',
    )
    valor_iss = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        verbose_name='Valor ISS (R$)',
    )
    valor_liquido = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        verbose_name='Valor Líquido (R$)',
    )

    # Retenções
    irrf = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        verbose_name='IRRF (R$)',
    )
    pis = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        verbose_name='PIS (R$)',
    )
    cofins = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        verbose_name='COFINS (R$)',
    )
    csll = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        verbose_name='CSLL (R$)',
    )
    inss = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        verbose_name='INSS (R$)',
    )

    # Datas
    data_emissao = models.DateTimeField(
        null=True, blank=True, verbose_name='Data de Emissão',
    )
    data_competencia = models.DateField(verbose_name='Competência')

    # Prefeitura
    municipio_prestacao = models.CharField(
        max_length=100, verbose_name='Município de Prestação',
    )

    # XML/PDF
    xml_envio = models.TextField(blank=True, verbose_name='XML de Envio')
    xml_retorno = models.TextField(blank=True, verbose_name='XML de Retorno')
    pdf_url = models.URLField(blank=True, verbose_name='URL do PDF')

    error_message = models.TextField(
        blank=True, verbose_name='Mensagem de Erro',
    )
    metadata = models.JSONField(default=dict, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='nfse_criadas',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Nota Fiscal de Serviço'
        verbose_name_plural = 'Notas Fiscais de Serviço'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['data_competencia']),
            models.Index(fields=['numero_nfse']),
        ]

    def __str__(self):
        return f"NFS-e {self.numero_nfse or 'RASCUNHO'} — R$ {self.valor_servico} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        self.base_calculo = self.valor_servico - self.valor_deducoes
        self.valor_iss = self.base_calculo * (self.aliquota_iss / 100)
        total_retencoes = self.irrf + self.pis + self.cofins + self.csll + self.inss
        self.valor_liquido = self.valor_servico - self.valor_iss - total_retencoes
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# HISTÓRICO DE AVALIAÇÃO DE RISCO
# ─────────────────────────────────────────────────────────────────────────────

class RiskAssessment(models.Model):
    """Avaliação de risco do caso com histórico temporal."""

    RISK_LEVEL_CHOICES = [
        ('very_low', 'Muito Baixo'),
        ('low', 'Baixo'),
        ('medium', 'Médio'),
        ('high', 'Alto'),
        ('very_high', 'Muito Alto'),
        ('critical', 'Crítico'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    caso = models.ForeignKey(
        LegalCase, on_delete=models.CASCADE,
        related_name='risk_assessments', verbose_name='Caso',
    )

    # Classificação
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, verbose_name='Nível de Risco')
    risk_score = models.IntegerField(default=50, verbose_name='Score de Risco (0-100)')

    # Fatores de risco
    factors = models.JSONField(default=list, blank=True, verbose_name='Fatores de Risco',
        help_text='Lista de fatores: [{name, weight, description}]')

    # Análise
    analysis = models.TextField(verbose_name='Análise Detalhada')
    recommendation = models.TextField(blank=True, verbose_name='Recomendações')

    # Contexto
    trigger = models.CharField(max_length=50, blank=True, verbose_name='Gatilho da Avaliação',
        help_text='O que motivou esta avaliação (nova_fase, prazo_perdido, manual, etc.)')
    previous_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, blank=True,
        verbose_name='Nível Anterior')
    level_changed = models.BooleanField(default=False, verbose_name='Nível Mudou')

    # IA
    ai_generated = models.BooleanField(default=False, verbose_name='Gerado por IA')
    ai_model = models.CharField(max_length=50, blank=True)
    tokens_used = models.IntegerField(default=0)

    # Metadados
    assessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='risk_assessments', verbose_name='Avaliado por',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data da Avaliação')

    class Meta:
        verbose_name = 'Avaliação de Risco'
        verbose_name_plural = 'Avaliações de Risco'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['caso', '-created_at']),
            models.Index(fields=['risk_level']),
        ]

    def __str__(self):
        return f"{self.get_risk_level_display()} ({self.risk_score}%) — {self.caso} ({self.created_at.date()})"
