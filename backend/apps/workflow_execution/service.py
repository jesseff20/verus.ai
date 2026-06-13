"""
Serviço de execução de fluxos BPMN.

Responsável por:
- Iniciar uma FlowInstance a partir de um FlowTemplate publicado
- Avançar o fluxo ao completar uma TaskInstance
- Avaliar gateways (exclusive / parallel)
- Reatribuir tarefas via TaskRequest
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone

from django.db import transaction

from apps.workflow_definition.models import FlowTemplate, FlowNode, FlowEdge
from .models import (
    FlowInstance, TaskInstance, TaskRequest, ExecutionEvent,
)

logger = logging.getLogger(__name__)


# ── Helpers internos ──────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _log(instance: FlowInstance, event_type: str, actor=None,
         node_id: str = '', node_label: str = '', **metadata):
    ExecutionEvent.objects.create(
        instance=instance,
        event_type=event_type,
        node_id=node_id,
        node_label=node_label,
        actor=actor,
        metadata=metadata,
    )


def _auto_assign(instance: FlowInstance, role_required: str):
    """
    Tenta atribuir automaticamente a task ao usuário mais adequado no órgão.
    Critérios (em ordem de prioridade):
    1. Usuário com role exato no mesmo órgão com menos tarefas pending
    2. Usuário com role equivalente via ROLE_ALIASES no mesmo órgão
    Retorna None se não encontrar nenhum candidato.
    """
    if not role_required:
        return None

    try:
        from django.contrib.auth import get_user_model
        from django.db.models import Count, Q
        User = get_user_model()
        aliases = getattr(User, 'ROLE_ALIASES', {})

        # Roles que correspondem ao role_required
        target_roles = {role_required}
        for alias, canonical in aliases.items():
            if canonical == role_required:
                target_roles.add(alias)

        candidates = User.objects.filter(
            organ=instance.organ,
            role__in=target_roles,
            is_active=True,
        ).annotate(
            pending_count=Count(
                'assigned_tasks',
                filter=Q(assigned_tasks__status__in=('pending', 'in_progress'),
                         assigned_tasks__instance__organ=instance.organ)
            )
        ).order_by('pending_count')

        return candidates.first()
    except Exception as exc:
        logger.warning('Falha na auto-atribuição (role=%s): %s', role_required, exc)
        return None


def _create_task(instance: FlowInstance, node: FlowNode,
                 actor=None) -> TaskInstance:
    """Cria uma TaskInstance para um nó, com auto-atribuição por role."""
    assigned = None
    if node.node_type in ('user_task', 'task'):
        assigned = _auto_assign(instance, node.role)

    with transaction.atomic():
        # select_for_update on the FlowInstance prevents two concurrent workers
        # from creating duplicate tasks for the same node.
        FlowInstance.objects.select_for_update().get(pk=instance.pk)

        # Bail out if a task for this node was already created by another worker.
        existing = TaskInstance.objects.filter(
            instance=instance,
            node_id=node.node_id,
            status__in=('pending', 'in_progress'),
        ).first()
        if existing:
            return existing

        task = TaskInstance.objects.create(
            instance=instance,
            node_id=node.node_id,
            node_type=node.node_type,
            label=node.label,
            role_required=node.role,
            instructions=node.description or '',
            assigned_to=assigned,
        )

    if assigned:
        _log(instance, 'task_started', actor=actor,
             node_id=node.node_id, node_label=node.label,
             task_id=str(task.id), assigned_to=str(assigned.id))
    else:
        _log(instance, 'task_created', actor=actor,
             node_id=node.node_id, node_label=node.label,
             task_id=str(task.id))

    return task


def _get_outgoing_edges(template: FlowTemplate,
                        node_id: str) -> list[FlowEdge]:
    return list(template.edges.filter(source_node_id=node_id))


def _get_node(template: FlowTemplate, node_id: str) -> FlowNode | None:
    return template.nodes.filter(node_id=node_id).first()


# ── API pública ───────────────────────────────────────────────────

@transaction.atomic
def start_flow(
    template_id: str,
    organ,
    started_by,
    case_ref: str = '',
    case_title: str = '',
    case_id: str | None = None,
) -> FlowInstance:
    """
    Inicia uma nova FlowInstance a partir de um template publicado.
    Cria automaticamente a TaskInstance do nó start_event.

    Raises:
        ValueError: se o template não existir, não pertencer ao órgão
                    ou não estiver publicado.
    """
    # Busca template — sistema (organ=null) ou do órgão
    try:
        template = FlowTemplate.objects.get(pk=template_id)
    except FlowTemplate.DoesNotExist:
        raise ValueError(f'Template {template_id} não encontrado.')

    if template.organ is not None and template.organ != organ:
        raise ValueError('Template não pertence ao órgão do usuário.')

    if template.status != 'published':
        raise ValueError('Apenas templates publicados podem ser instanciados.')

    # Se case_id fornecido, preenche case_ref/case_title do LegalCase
    legal_case = None
    if case_id:
        try:
            from apps.cases.models import LegalCase
            legal_case = LegalCase.objects.get(pk=case_id)
            if not case_ref:
                case_ref = legal_case.numero_processo or str(legal_case.id)
            if not case_title:
                case_title = legal_case.titulo
        except Exception:
            pass  # case_id inválido não bloqueia

    # Nó de início
    start_node = template.nodes.filter(node_type='start_event').first()
    if not start_node:
        raise ValueError('O template não possui nó start_event.')

    # Cria instância
    now = _now()
    instance = FlowInstance.objects.create(
        template=template,
        organ=organ,
        case_ref=case_ref,
        case_title=case_title,
        status='running',
        current_node_id=start_node.node_id,
        started_by=started_by,
        started_at=now,
        template_name_snapshot=template.name,
        template_version_snapshot=template.version,
    )

    _log(instance, 'flow_started', actor=started_by,
         node_id=start_node.node_id, node_label=start_node.label,
         template_id=str(template.id), template_version=template.version)

    # Vincula ao LegalCase, se fornecido
    if legal_case:
        try:
            legal_case.active_flow = instance
            legal_case.save(update_fields=['active_flow'])
        except Exception as exc:
            logger.warning('Não foi possível vincular FlowInstance ao LegalCase: %s', exc)

    # Cria task do nó de início (normalmente auto-complete, mas mantemos
    # para rastreabilidade de auditoria)
    _create_task(instance, start_node, actor=started_by)

    # Avança automaticamente do start_event para o próximo nó
    _advance_from_node(instance, template, start_node, actor=started_by)

    return instance


@transaction.atomic
def complete_task(
    task_id: str,
    completed_by,
    notes: str = '',
    gateway_choice: str = '',
) -> FlowInstance:
    """
    Marca uma TaskInstance como concluída e avança o fluxo para o próximo nó.

    Para gateways exclusivos, `gateway_choice` deve ser o handle de saída
    selecionado (ex: 'yes', 'no', ou o edge_id da branch escolhida).

    Raises:
        ValueError: se a task não existir, já estiver concluída ou o
                    gateway_choice for inválido.
    """
    try:
        task = TaskInstance.objects.select_for_update().select_related(
            'instance', 'instance__template'
        ).get(pk=task_id)
    except TaskInstance.DoesNotExist:
        raise ValueError(f'Tarefa {task_id} não encontrada.')

    if task.status in ('completed', 'skipped'):
        raise ValueError('Esta tarefa já foi concluída.')

    instance = task.instance
    if instance.is_terminal:
        raise ValueError('O fluxo já está encerrado.')

    now = _now()
    task.status = 'completed'
    task.notes = notes
    task.gateway_choice = gateway_choice
    task.completed_at = now
    task.completed_by = completed_by
    if not task.started_at:
        task.started_at = now
    task.save()

    _log(instance, 'task_completed', actor=completed_by,
         node_id=task.node_id, node_label=task.label,
         task_id=str(task.id), notes=notes)

    template = instance.template
    current_node = _get_node(template, task.node_id)
    if not current_node:
        logger.warning('Nó %s não encontrado no template %s', task.node_id, template.id)
        return instance

    # Avança para os próximos nós
    _advance_from_node(instance, template, current_node,
                       actor=completed_by, gateway_choice=gateway_choice)

    return instance


def _advance_from_node(
    instance: FlowInstance,
    template: FlowTemplate,
    node: FlowNode,
    actor=None,
    gateway_choice: str = '',
    _visited: frozenset | None = None,
):
    """
    Determina os próximos nós a partir de `node` e cria as tasks correspondentes.
    Chamada recursivamente para nós que não requerem interação humana
    (start_event, gateways, service_task).

    `_visited` rastreia node_ids já percorridos nesta chamada recursiva para
    prevenir loops infinitos em templates com ciclos.
    """
    if _visited is None:
        _visited = frozenset()

    if node.node_id in _visited:
        logger.warning(
            'Ciclo detectado no template %s: nó %s já visitado. Abortando avanço.',
            template.id, node.node_id,
        )
        return

    _visited = _visited | {node.node_id}

    outgoing = _get_outgoing_edges(template, node.node_id)

    if not outgoing:
        # Sem arestas de saída — fim do fluxo
        _finish_flow(instance, actor)
        return

    node_type = node.node_type

    # ── end_event ──────────────────────────────────────────────
    if node_type == 'end_event':
        _finish_flow(instance, actor)
        return

    # ── exclusive_gateway (XOR) ────────────────────────────────
    if node_type == 'exclusive_gateway':
        chosen_edge = _resolve_exclusive_gateway(
            template, node, outgoing, gateway_choice
        )
        if chosen_edge:
            _log(instance, 'gateway_evaluated', actor=actor,
                 node_id=node.node_id, node_label=node.label,
                 chosen_edge=chosen_edge.edge_id,
                 chosen_handle=chosen_edge.source_handle)
            next_node = _get_node(template, chosen_edge.target_node_id)
            if next_node:
                _proceed_to_node(instance, template, next_node, actor, _visited=_visited)
        return

    # ── parallel_gateway (AND) ─────────────────────────────────
    if node_type == 'parallel_gateway':
        _log(instance, 'gateway_evaluated', actor=actor,
             node_id=node.node_id, node_label=node.label,
             branches=[e.target_node_id for e in outgoing])
        for edge in outgoing:
            next_node = _get_node(template, edge.target_node_id)
            if next_node:
                _proceed_to_node(instance, template, next_node, actor, _visited=_visited)
        return

    # ── start_event / intermediate_event / service_task ────────
    # Avança automaticamente sem interação
    if node_type in ('start_event', 'intermediate_event', 'service_task'):
        for edge in outgoing:
            next_node = _get_node(template, edge.target_node_id)
            if next_node:
                _proceed_to_node(instance, template, next_node, actor, _visited=_visited)
        return

    # ── user_task / task (requer interação humana) ─────────────
    # Apenas atualiza current_node_id — a task já foi criada antes de chegar aqui
    # (ou será criada logo abaixo via _proceed_to_node)


def _proceed_to_node(
    instance: FlowInstance,
    template: FlowTemplate,
    node: FlowNode,
    actor=None,
    _visited: frozenset | None = None,
):
    """Cria task para o nó e, se automático, avança imediatamente."""
    instance.current_node_id = node.node_id
    instance.save(update_fields=['current_node_id', 'updated_at'])

    if node.node_type == 'end_event':
        _create_task(instance, node, actor=actor)
        _finish_flow(instance, actor)
        return

    # Nós automáticos: service_task, intermediate_event
    if node.node_type in ('service_task', 'intermediate_event'):
        task = _create_task(instance, node, actor=actor)
        task.status = 'completed'
        task.completed_at = _now()
        task.completed_by = actor
        task.save()
        _advance_from_node(instance, template, node, actor=actor, _visited=_visited)
        return

    # Gateways: não criam task, apenas avaliam
    if node.node_type in ('exclusive_gateway', 'parallel_gateway', 'inclusive_gateway'):
        _advance_from_node(instance, template, node, actor=actor, _visited=_visited)
        return

    # user_task / task: cria task e aguarda interação
    _create_task(instance, node, actor=actor)


def _resolve_exclusive_gateway(
    template: FlowTemplate,
    gateway_node: FlowNode,
    outgoing: list[FlowEdge],
    gateway_choice: str,
) -> FlowEdge | None:
    """
    Seleciona a aresta de saída de um gateway exclusivo.

    Prioridade:
    1. gateway_choice == source_handle da aresta
    2. gateway_choice == edge_id da aresta
    3. Primeira aresta disponível (fallback)
    """
    if gateway_choice:
        # Tenta pelo handle
        for edge in outgoing:
            if edge.source_handle == gateway_choice:
                return edge
        # Tenta pelo edge_id
        for edge in outgoing:
            if edge.edge_id == gateway_choice:
                return edge

        # gateway_choice fornecido mas nenhuma aresta correspondente encontrada
        logger.warning(
            'Gateway exclusivo "%s" (node %s): escolha "%s" nao corresponde a nenhuma aresta. '
            'Usando fallback para a primeira aresta disponivel.',
            gateway_node.label, gateway_node.node_id, gateway_choice,
        )

    # Fallback: primeira aresta
    return outgoing[0] if outgoing else None


def _finish_flow(instance: FlowInstance, actor=None):
    now = _now()
    instance.status = 'completed'
    instance.completed_at = now
    instance.current_node_id = ''
    instance.save(update_fields=['status', 'completed_at', 'current_node_id', 'updated_at'])
    _log(instance, 'flow_completed', actor=actor)


@transaction.atomic
def cancel_flow(instance_id: str, cancelled_by) -> FlowInstance:
    """Cancela uma FlowInstance em andamento."""
    try:
        instance = FlowInstance.objects.get(pk=instance_id)
    except FlowInstance.DoesNotExist:
        raise ValueError(f'Instância {instance_id} não encontrada.')

    if instance.is_terminal:
        raise ValueError('O fluxo já está encerrado.')

    instance.status = 'cancelled'
    instance.save(update_fields=['status', 'updated_at'])

    # Cancela tasks pendentes
    instance.tasks.filter(status__in=('pending', 'in_progress')).update(
        status='skipped'
    )

    _log(instance, 'flow_cancelled', actor=cancelled_by)
    return instance


@transaction.atomic
def approve_request(request_id: str, resolved_by,
                    resolution_note: str = '') -> TaskRequest:
    """
    Aprova uma TaskRequest de redistribuição, avocação ou assessoria.
    Para redistribuição: reatribui a task ao target_user.
    """
    try:
        req = TaskRequest.objects.select_related('task').get(pk=request_id)
    except TaskRequest.DoesNotExist:
        raise ValueError(f'Solicitação {request_id} não encontrada.')

    if req.status != 'pending':
        raise ValueError('Solicitação já foi resolvida.')

    now = _now()
    req.status = 'approved'
    req.resolved_by = resolved_by
    req.resolution_note = resolution_note
    req.resolved_at = now
    req.save()

    task = req.task
    instance = task.instance

    if req.request_type in ('redistribuicao', 'avocacao') and req.target_user:
        old_assignee = task.assigned_to
        task.assigned_to = req.target_user
        task.save(update_fields=['assigned_to'])

        _log(instance, 'task_reassigned', actor=resolved_by,
             node_id=task.node_id, node_label=task.label,
             task_id=str(task.id),
             from_user=str(old_assignee.id) if old_assignee else None,
             to_user=str(req.target_user.id),
             request_type=req.request_type)

    _log(instance, 'request_approved', actor=resolved_by,
         task_id=str(task.id), request_id=str(req.id),
         request_type=req.request_type)

    return req


@transaction.atomic
def reject_request(request_id: str, resolved_by,
                   resolution_note: str = '') -> TaskRequest:
    """Rejeita uma TaskRequest."""
    try:
        req = TaskRequest.objects.get(pk=request_id)
    except TaskRequest.DoesNotExist:
        raise ValueError(f'Solicitação {request_id} não encontrada.')

    if req.status != 'pending':
        raise ValueError('Solicitação já foi resolvida.')

    req.status = 'rejected'
    req.resolved_by = resolved_by
    req.resolution_note = resolution_note
    req.resolved_at = _now()
    req.save()

    _log(req.task.instance, 'request_rejected', actor=resolved_by,
         task_id=str(req.task.id), request_id=str(req.id),
         request_type=req.request_type)

    return req
