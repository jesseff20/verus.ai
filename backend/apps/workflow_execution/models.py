"""
Models de execução de workflows (instâncias em runtime).

Hierarquia:
  FlowInstance    → uma execução de um FlowTemplate
    TaskInstance  → tarefa de um nó dentro da instância
    TaskRequest   → solicitação de redistribuição/avocação/assessoria
    ExecutionEvent → log imutável de auditoria
"""
import uuid
from django.db import models
from django.conf import settings


# ── Status choices ────────────────────────────────────────────────

INSTANCE_STATUS_CHOICES = [
    ('pending', 'Aguardando início'),
    ('running', 'Em andamento'),
    ('completed', 'Concluído'),
    ('cancelled', 'Cancelado'),
]

TASK_STATUS_CHOICES = [
    ('pending', 'Pendente'),
    ('in_progress', 'Em andamento'),
    ('completed', 'Concluído'),
    ('skipped', 'Pulado'),
]

REQUEST_TYPE_CHOICES = [
    ('redistribuicao', 'Redistribuição'),
    ('avocacao', 'Avocação'),
    ('assessoria', 'Pedido de Assessoria'),
]

REQUEST_STATUS_CHOICES = [
    ('pending', 'Aguardando aprovação'),
    ('approved', 'Aprovado'),
    ('rejected', 'Rejeitado'),
]

EVENT_TYPE_CHOICES = [
    ('flow_started', 'Fluxo iniciado'),
    ('flow_completed', 'Fluxo concluído'),
    ('flow_cancelled', 'Fluxo cancelado'),
    ('task_created', 'Tarefa criada'),
    ('task_started', 'Tarefa iniciada'),
    ('task_completed', 'Tarefa concluída'),
    ('task_skipped', 'Tarefa pulada'),
    ('task_reassigned', 'Tarefa reatribuída'),
    ('gateway_evaluated', 'Gateway avaliado'),
    ('request_created', 'Solicitação criada'),
    ('request_approved', 'Solicitação aprovada'),
    ('request_rejected', 'Solicitação rejeitada'),
]


# ── FlowInstance ──────────────────────────────────────────────────

class FlowInstance(models.Model):
    """
    Uma execução de um FlowTemplate vinculada a um processo ou caso.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    template = models.ForeignKey(
        'workflow_definition.FlowTemplate',
        on_delete=models.PROTECT,
        related_name='instances',
        verbose_name='Template de fluxo',
    )
    organ = models.ForeignKey(
        'organization.Organ',
        on_delete=models.CASCADE,
        related_name='flow_instances',
        verbose_name='Órgão',
    )

    # Referência livre ao processo/caso (UUID ou número do processo)
    case_ref = models.CharField(
        'Referência do processo', max_length=200, blank=True,
        help_text='UUID do caso, número do processo CNJ, etc.',
    )
    case_title = models.CharField(
        'Título do processo', max_length=300, blank=True,
        help_text='Nome ou ementa para exibição',
    )

    status = models.CharField(
        'Status', max_length=15,
        choices=INSTANCE_STATUS_CHOICES, default='pending',
    )

    # Nó corrente (pode ser vazio quando concluído)
    current_node_id = models.CharField(
        'Nó atual (node_id)', max_length=100, blank=True,
    )

    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='started_flow_instances',
        verbose_name='Iniciado por',
    )

    started_at = models.DateTimeField('Iniciado em', null=True, blank=True)
    completed_at = models.DateTimeField('Concluído em', null=True, blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    # Snapshot do template no momento da criação (nome e versão)
    template_name_snapshot = models.CharField(
        'Nome do template (snapshot)', max_length=200, blank=True,
    )
    template_version_snapshot = models.PositiveIntegerField(
        'Versão do template (snapshot)', default=1,
    )

    class Meta:
        verbose_name = 'Instância de Fluxo'
        verbose_name_plural = 'Instâncias de Fluxo'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.template_name_snapshot} — {self.case_ref or "sem ref"} [{self.get_status_display()}]'

    @property
    def is_running(self):
        return self.status == 'running'

    @property
    def is_terminal(self):
        return self.status in ('completed', 'cancelled')


# ── TaskInstance ──────────────────────────────────────────────────

class TaskInstance(models.Model):
    """
    Representa a execução de um nó específico dentro de uma FlowInstance.
    Criada automaticamente pelo serviço de execução ao avançar o fluxo.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    instance = models.ForeignKey(
        FlowInstance,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Instância do fluxo',
    )

    # Snapshot do nó no momento da criação
    node_id = models.CharField('ID do nó (node_id)', max_length=100)
    node_type = models.CharField('Tipo do nó', max_length=30)
    label = models.CharField('Rótulo', max_length=200)
    role_required = models.CharField(
        'Papel requerido', max_length=25, default='any',
    )
    instructions = models.TextField('Instruções', blank=True)

    # Atribuição
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_tasks',
        verbose_name='Atribuído a',
    )

    status = models.CharField(
        'Status', max_length=15,
        choices=TASK_STATUS_CHOICES, default='pending',
    )

    # Para gateways exclusivos: branch escolhido
    gateway_choice = models.CharField(
        'Branch escolhido (gateway)', max_length=100, blank=True,
        help_text='Handle de saída selecionado no gateway exclusivo',
    )

    due_date = models.DateField('Prazo', null=True, blank=True)
    notes = models.TextField('Observações ao concluir', blank=True)

    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    started_at = models.DateTimeField('Iniciado em', null=True, blank=True)
    completed_at = models.DateTimeField('Concluído em', null=True, blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='completed_tasks',
        verbose_name='Concluído por',
    )

    class Meta:
        verbose_name = 'Tarefa'
        verbose_name_plural = 'Tarefas'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.label} [{self.get_status_display()}] — {self.instance}'


# ── TaskRequest ───────────────────────────────────────────────────

class TaskRequest(models.Model):
    """
    Solicitação formal de redistribuição, avocação ou assessoria.
    Criada pelo usuário assignado à tarefa; aprovada/rejeitada por gerente.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    task = models.ForeignKey(
        TaskInstance,
        on_delete=models.CASCADE,
        related_name='requests',
        verbose_name='Tarefa',
    )
    request_type = models.CharField(
        'Tipo', max_length=20,
        choices=REQUEST_TYPE_CHOICES,
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='task_requests_made',
        verbose_name='Solicitante',
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='task_requests_received',
        verbose_name='Usuário destino',
        help_text='Para redistribuição: quem vai receber a tarefa',
    )
    justification = models.TextField('Justificativa')
    status = models.CharField(
        'Status', max_length=15,
        choices=REQUEST_STATUS_CHOICES, default='pending',
    )

    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='task_requests_resolved',
        verbose_name='Resolvido por',
    )
    resolution_note = models.TextField('Nota de resolução', blank=True)

    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    resolved_at = models.DateTimeField('Resolvido em', null=True, blank=True)

    class Meta:
        verbose_name = 'Solicitação de Tarefa'
        verbose_name_plural = 'Solicitações de Tarefas'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_request_type_display()} — {self.task.label} [{self.get_status_display()}]'


# ── ExecutionEvent ────────────────────────────────────────────────

class ExecutionEvent(models.Model):
    """
    Log imutável de todos os eventos em uma FlowInstance.
    Nunca deve ser alterado após criação — é auditoria.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    instance = models.ForeignKey(
        FlowInstance,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name='Instância do fluxo',
    )
    event_type = models.CharField(
        'Tipo de evento', max_length=30,
        choices=EVENT_TYPE_CHOICES,
    )

    node_id = models.CharField('Node ID', max_length=100, blank=True)
    node_label = models.CharField('Label do nó', max_length=200, blank=True)

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='execution_events',
        verbose_name='Ator',
    )

    metadata = models.JSONField('Metadados', default=dict, blank=True)
    created_at = models.DateTimeField('Data/hora', auto_now_add=True)

    class Meta:
        verbose_name = 'Evento de Execução'
        verbose_name_plural = 'Eventos de Execução'
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        # Imutável: não permite update
        if self.pk and ExecutionEvent.objects.filter(pk=self.pk).exists():
            raise ValueError('ExecutionEvent é imutável — não pode ser alterado após criação.')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'[{self.created_at:%Y-%m-%d %H:%M}] {self.get_event_type_display()} — {self.instance}'
