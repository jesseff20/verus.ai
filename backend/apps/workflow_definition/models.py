"""
Models de definição de workflows (templates BPMN).

Hierarquia:
  FlowTemplate   → template editável de um fluxo
    FlowNode     → nó do fluxo (task, gateway, event, swimlane)
    FlowEdge     → conexão entre nós
    FlowVersion  → snapshot publicado (imutável)
"""
import uuid
from django.db import models
from django.conf import settings


# ── Constantes de tipo ────────────────────────────────────────

NODE_TYPE_CHOICES = [
    # Swim lane container
    ('swimlane', 'Swim Lane (Papel)'),
    # Eventos BPMN
    ('start_event', 'Evento de Início'),
    ('end_event', 'Evento de Fim'),
    ('intermediate_event', 'Evento Intermediário'),
    # Tarefas
    ('task', 'Tarefa'),
    ('user_task', 'Tarefa de Usuário'),
    ('service_task', 'Tarefa de Serviço'),
    # Gateways
    ('exclusive_gateway', 'Gateway Exclusivo (XOR)'),
    ('parallel_gateway', 'Gateway Paralelo (AND)'),
    ('inclusive_gateway', 'Gateway Inclusivo (OR)'),
]

ROLE_CHOICES = [
    ('distribuidor', 'Distribuidor(a)'),
    ('procurador', 'Procurador(a)'),
    ('gerente', 'Gerente'),
    ('assessor_gerencial', 'Assessor(a) Gerencial'),
    ('assessor_gabinete', 'Assessor(a) de Gabinete'),
    ('procurador_geral', 'Procurador(a)-Geral'),
    ('subprocurador_geral', 'Subprocurador(a)-Geral'),
    ('any', 'Qualquer papel'),
]

TEMPLATE_STATUS_CHOICES = [
    ('draft', 'Rascunho'),
    ('published', 'Publicado'),
    ('archived', 'Arquivado'),
]

FLOW_CATEGORY_CHOICES = [
    ('judicial_1', 'Judicial — 1º Grau'),
    ('judicial_2', 'Judicial — 2º Grau'),
    ('administrative', 'Administrativo'),
    ('other', 'Outro'),
]


# ── Modelos ────────────────────────────────────────────────────

class FlowTemplate(models.Model):
    """
    Template de fluxo de trabalho. Pode estar em rascunho ou publicado.
    Apenas templates publicados podem ser instanciados (FlowInstance).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organ = models.ForeignKey(
        'organization.Organ',
        on_delete=models.CASCADE,
        related_name='flow_templates',
        verbose_name='Órgão',
        null=True, blank=True,
        help_text='Nulo = template de sistema (disponível para todos os órgãos)',
    )
    name = models.CharField('Nome do Fluxo', max_length=200)
    description = models.TextField('Descrição', blank=True)
    category = models.CharField(
        'Categoria', max_length=20,
        choices=FLOW_CATEGORY_CHOICES, default='judicial_1',
    )
    status = models.CharField(
        'Status', max_length=15,
        choices=TEMPLATE_STATUS_CHOICES, default='draft',
    )
    version = models.PositiveIntegerField('Versão atual', default=1)
    is_system_template = models.BooleanField(
        'Template de sistema', default=False,
        help_text='Templates de sistema são pré-carregados e não podem ser editados',
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_flow_templates',
        verbose_name='Criado por',
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    published_at = models.DateTimeField('Publicado em', null=True, blank=True)

    class Meta:
        verbose_name = 'Template de Fluxo'
        verbose_name_plural = 'Templates de Fluxo'
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.name} v{self.version} [{self.get_status_display()}]'

    @property
    def is_published(self):
        return self.status == 'published'

    @property
    def node_count(self):
        return self.nodes.count()

    @property
    def swimlane_count(self):
        return self.nodes.filter(node_type='swimlane').count()


class FlowNode(models.Model):
    """
    Nó dentro de um FlowTemplate. Inclui swim lanes (containers),
    tarefas, gateways e eventos.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        FlowTemplate, on_delete=models.CASCADE,
        related_name='nodes', verbose_name='Template',
    )
    # Identificador único dentro do template (usado pelo frontend @xyflow/react)
    node_id = models.CharField('ID do nó (xyflow)', max_length=100)
    node_type = models.CharField('Tipo', max_length=30, choices=NODE_TYPE_CHOICES)

    # Conteúdo
    label = models.CharField('Rótulo', max_length=200)
    description = models.TextField('Descrição/Instruções', blank=True)
    role = models.CharField(
        'Papel responsável', max_length=25,
        choices=ROLE_CHOICES, default='any',
    )

    # Hierarquia (swim lane containers)
    parent_node_id = models.CharField(
        'ID do nó pai (swim lane)', max_length=100, blank=True,
        help_text='Para nós dentro de uma swim lane',
    )

    # Posição e dimensão no canvas (JSON: {x, y, width, height})
    position = models.JSONField('Posição', default=dict)

    # Dados adicionais específicos por tipo de nó
    data = models.JSONField('Dados extras', default=dict, blank=True)

    # Ordem de exibição dentro da swim lane
    order = models.PositiveIntegerField('Ordem', default=0)

    class Meta:
        verbose_name = 'Nó de Fluxo'
        verbose_name_plural = 'Nós de Fluxo'
        ordering = ['template', 'order']
        unique_together = [('template', 'node_id')]

    def __str__(self):
        return f'{self.template.name} › {self.label} ({self.node_type})'


class FlowEdge(models.Model):
    """
    Conexão direcional entre dois nós de um FlowTemplate.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        FlowTemplate, on_delete=models.CASCADE,
        related_name='edges', verbose_name='Template',
    )
    # Identificador único dentro do template
    edge_id = models.CharField('ID da edge (xyflow)', max_length=100)
    source_node_id = models.CharField('Nó de origem', max_length=100)
    target_node_id = models.CharField('Nó de destino', max_length=100)

    # Handle de conexão (ex: "yes", "no", "default")
    source_handle = models.CharField('Handle de origem', max_length=50, blank=True)
    target_handle = models.CharField('Handle de destino', max_length=50, blank=True)

    # Rótulo da seta (ex: "Sim", "Não", "Aceita")
    label = models.CharField('Rótulo', max_length=100, blank=True)

    # Condição para gateways (expressão ou chave de decisão)
    condition = models.CharField('Condição', max_length=200, blank=True)

    # Dados extras (animated, style, etc.)
    data = models.JSONField('Dados extras', default=dict, blank=True)

    class Meta:
        verbose_name = 'Conexão de Fluxo'
        verbose_name_plural = 'Conexões de Fluxo'
        unique_together = [('template', 'edge_id')]

    def __str__(self):
        return f'{self.template.name} › {self.source_node_id} → {self.target_node_id}'


class FlowVersion(models.Model):
    """
    Snapshot imutável de um FlowTemplate no momento da publicação.
    Usado para auditoria e para que instâncias de execução
    sempre refiram à versão exata que estava publicada quando foram criadas.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        FlowTemplate, on_delete=models.CASCADE,
        related_name='versions', verbose_name='Template',
    )
    version_number = models.PositiveIntegerField('Número da versão')
    # Snapshot completo do template: {nodes: [...], edges: [...]}
    snapshot = models.JSONField('Snapshot completo')

    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='published_flow_versions',
        verbose_name='Publicado por',
    )
    published_at = models.DateTimeField('Publicado em', auto_now_add=True)
    notes = models.TextField('Notas da versão', blank=True)

    class Meta:
        verbose_name = 'Versão do Fluxo'
        verbose_name_plural = 'Versões do Fluxo'
        ordering = ['-published_at']
        unique_together = [('template', 'version_number')]

    def __str__(self):
        return f'{self.template.name} v{self.version_number}'
