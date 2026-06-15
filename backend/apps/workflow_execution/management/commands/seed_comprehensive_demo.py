"""
Seed abrangente de dados demo interconectados para Verus.AI.

Cria:
  1. FlowInstances em TODOS os status (pending, running, completed, cancelled)
  2. TaskRequest em todos os tipos e status (redistribuicao, avocacao, assessoria)
  3. ExecutionEvent (logs de auditoria) para cada instancia
  4. LegalDeadline extras com distribuicao temporal realista

Depende de:
  - seed_production_demo    (usuarios e casos)
  - seed_judicial_flows     (FlowTemplates publicados)
  - seed_demo_workflow_journey (organ demo + vinculacao de usuarios)

Idempotente: usa get_or_create e verificacao de existencia antes de criar.
Resiliente: nao falha se dependencias parciais estiverem ausentes.

Uso: python manage.py seed_comprehensive_demo
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.cases.models import LegalCase, LegalDeadline
from apps.organization.models import Organ
from apps.workflow_definition.models import FlowTemplate, FlowEdge
from apps.workflow_execution import service as flow_service
from apps.workflow_execution.models import (
    FlowInstance, TaskInstance, TaskRequest, ExecutionEvent,
)

logger = logging.getLogger(__name__)
User = get_user_model()

# ── Constantes ────────────────────────────────────────────────────────────

DEMO_ORGAN_NAME = 'Procuradoria Municipal Demo Verus'

DEMO_USERNAMES = [
    'usuario_demo',
    'joao.silva',
    'maria.santos',
    'carlos.mendes',
    'ana.rodrigues',
    'pedro.lima',
]

# Identificador de metadado para rastrear registros criados por este seed
SEED_TAG = 'seed_comprehensive_demo'


class Command(BaseCommand):
    help = (
        'Cria dados demo abrangentes: execucoes em todos os status, '
        'solicitacoes, eventos de auditoria e prazos processuais.'
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n=== seed_comprehensive_demo ===\n'
        ))

        # ── 1. Lookup de usuarios demo ────────────────────────────
        users = self._load_users()
        if not users:
            self.stderr.write(self.style.WARNING(
                'Nenhum usuario demo encontrado. Execute seed_production_demo primeiro.'
            ))
            return
        self.stdout.write(f'  Usuarios carregados: {len(users)}')

        # ── 2. Lookup/ensure organ ────────────────────────────────
        organ = self._ensure_organ()
        self.stdout.write(f'  Organ: {organ.short_name}')

        # ── 3. Lookup templates publicados ────────────────────────
        templates = list(
            FlowTemplate.objects.filter(status='published')
            .order_by('created_at')
        )
        if not templates:
            self.stderr.write(self.style.WARNING(
                'Nenhum FlowTemplate publicado. Execute seed_judicial_flows primeiro.'
            ))
            return
        self.stdout.write(f'  Templates publicados: {len(templates)}')

        # ── 4. Lookup de casos existentes ─────────────────────────
        cases = list(
            LegalCase.objects.filter(organ=organ)
            .order_by('created_at')[:10]
        )
        if not cases:
            # Fallback: pegar qualquer caso
            cases = list(LegalCase.objects.order_by('created_at')[:10])
        self.stdout.write(f'  Casos encontrados: {len(cases)}')

        # ── 5. Criar FlowInstances em todos os status ─────────────
        summary = {
            'flows_running': 0,
            'flows_completed': 0,
            'flows_cancelled': 0,
            'flows_pending': 0,
            'task_requests': 0,
            'execution_events': 0,
            'deadlines': 0,
        }

        primary_user = users[0]

        # 5a. 2x Running instances
        running_instances = []
        for i in range(2):
            inst = self._create_running_instance(
                templates, organ, users, cases, index=i,
            )
            if inst:
                running_instances.append(inst)
                summary['flows_running'] += 1
                self.stdout.write(
                    f'  + FlowInstance running: {inst.id}'
                )

        # 5b. 1x Completed instance
        completed_inst = self._create_completed_instance(
            templates, organ, users, cases,
        )
        if completed_inst:
            summary['flows_completed'] += 1
            self.stdout.write(
                f'  + FlowInstance completed: {completed_inst.id}'
            )

        # 5c. 1x Cancelled instance
        cancelled_inst = self._create_cancelled_instance(
            templates, organ, users, cases,
        )
        if cancelled_inst:
            summary['flows_cancelled'] += 1
            self.stdout.write(
                f'  + FlowInstance cancelled: {cancelled_inst.id}'
            )

        # 5d. 1x Pending instance (manual creation, not via start_flow)
        pending_inst = self._create_pending_instance(
            templates, organ, users,
        )
        if pending_inst:
            summary['flows_pending'] += 1
            self.stdout.write(
                f'  + FlowInstance pending: {pending_inst.id}'
            )

        # ── 6. Criar TaskRequests ─────────────────────────────────
        created_requests = self._create_task_requests(
            running_instances, users,
        )
        summary['task_requests'] = created_requests
        self.stdout.write(f'  TaskRequests criados: {created_requests}')

        # ── 7. Criar ExecutionEvents extras ───────────────────────
        all_instances = running_instances.copy()
        if completed_inst:
            all_instances.append(completed_inst)
        if cancelled_inst:
            all_instances.append(cancelled_inst)
        if pending_inst:
            all_instances.append(pending_inst)

        created_events = self._create_execution_events(
            all_instances, users,
        )
        summary['execution_events'] = created_events
        self.stdout.write(f'  ExecutionEvents criados: {created_events}')

        # ── 8. Criar Prazos (LegalDeadline) extras ────────────────
        created_deadlines = self._create_extra_deadlines(
            cases, users,
        )
        summary['deadlines'] = created_deadlines
        self.stdout.write(f'  Prazos criados: {created_deadlines}')

        # ── 9. Resumo final ───────────────────────────────────────
        self.stdout.write(self.style.SUCCESS(
            f'\n  Seed concluido com sucesso!'
            f'\n    Fluxos running:   {summary["flows_running"]}'
            f'\n    Fluxos completed: {summary["flows_completed"]}'
            f'\n    Fluxos cancelled: {summary["flows_cancelled"]}'
            f'\n    Fluxos pending:   {summary["flows_pending"]}'
            f'\n    TaskRequests:     {summary["task_requests"]}'
            f'\n    ExecutionEvents:  {summary["execution_events"]}'
            f'\n    Prazos:           {summary["deadlines"]}'
            f'\n'
        ))

    # ══════════════════════════════════════════════════════════════════
    # HELPERS — usuarios e organ
    # ══════════════════════════════════════════════════════════════════

    def _load_users(self) -> list:
        """Carrega usuarios demo existentes (nao cria novos)."""
        users = []
        for username in DEMO_USERNAMES:
            user = User.objects.filter(username=username).first()
            if user:
                users.append(user)
        return users

    def _ensure_organ(self) -> Organ:
        organ, _ = Organ.objects.get_or_create(
            name=DEMO_ORGAN_NAME,
            defaults={
                'short_name': 'PGM-DEMO',
                'organ_type': 'pgm',
                'state': 'ES',
                'city': 'Serra',
                'email': 'demo@verus.ai',
                'is_active': True,
            },
        )
        return organ

    # ══════════════════════════════════════════════════════════════════
    # HELPERS — FlowInstance creation
    # ══════════════════════════════════════════════════════════════════

    def _find_available_case(self, cases: list, require_no_flow: bool = True):
        """Retorna um caso que nao tenha fluxo ativo, ou None."""
        for case in cases:
            if require_no_flow and case.active_flow_id:
                # Verifica se o fluxo ativo ainda esta realmente ativo
                active = FlowInstance.objects.filter(
                    id=case.active_flow_id,
                    status='running',
                ).exists()
                if active:
                    continue
            return case
        return None

    def _start_flow_safe(
        self, template, organ, user, case=None,
    ) -> FlowInstance | None:
        """Inicia um fluxo com tratamento de erro."""
        try:
            kwargs = {
                'template_id': str(template.id),
                'organ': organ,
                'started_by': user,
            }
            if case:
                kwargs['case_id'] = str(case.id)
            else:
                kwargs['case_ref'] = f'SEED-{SEED_TAG}'
                kwargs['case_title'] = f'Fluxo demo ({template.name})'

            return flow_service.start_flow(**kwargs)
        except Exception as exc:
            logger.warning(
                'Falha ao iniciar fluxo (template=%s): %s',
                template.name, exc,
            )
            self.stderr.write(f'    ! Falha start_flow: {exc}')
            return None

    def _advance_tasks(
        self, instance: FlowInstance, user, steps: int = 1,
    ) -> int:
        """Completa N tarefas user_task pendentes para avancar o fluxo."""
        completed = 0
        for _ in range(steps):
            task = (
                TaskInstance.objects.filter(
                    instance=instance,
                    status__in=('pending', 'in_progress'),
                    node_type__in=('user_task', 'task'),
                )
                .order_by('created_at')
                .first()
            )
            if not task:
                break

            # Para gateways exclusivos, pegar a primeira opcao
            gateway_choice = ''
            next_node = None
            if task.node_type in ('exclusive_gateway',):
                edge = FlowEdge.objects.filter(
                    template=instance.template,
                    source_node_id=task.node_id,
                ).first()
                if edge:
                    gateway_choice = edge.source_handle or edge.edge_id

            try:
                flow_service.complete_task(
                    task_id=str(task.id),
                    completed_by=user,
                    notes=f'[{SEED_TAG}] Tarefa concluida automaticamente.',
                    gateway_choice=gateway_choice,
                )
                completed += 1
            except Exception as exc:
                logger.warning('Falha ao completar task %s: %s', task.id, exc)
                break

        return completed

    def _check_existing_seed_instance(
        self, status: str, tag_suffix: str,
    ) -> FlowInstance | None:
        """Verifica se ja existe uma FlowInstance deste seed com o status dado."""
        return FlowInstance.objects.filter(
            case_ref__contains=SEED_TAG,
            status=status,
        ).first()

    def _create_running_instance(
        self, templates, organ, users, cases, index: int,
    ) -> FlowInstance | None:
        """Cria uma FlowInstance com status running, com algumas tarefas completadas."""
        tag = f'{SEED_TAG}-running-{index}'

        # Idempotencia: verifica se ja existe
        existing = FlowInstance.objects.filter(
            case_ref__contains=tag,
            status='running',
        ).first()
        if existing:
            self.stdout.write(f'    (ja existe running-{index}: {existing.id})')
            return existing

        template = templates[index % len(templates)]
        user = users[index % len(users)]

        # Tentar vincular a um caso, ou criar sem caso
        case = self._find_available_case(cases)
        if case:
            # Remover da lista para nao reutilizar
            cases.remove(case)

        try:
            instance = self._start_flow_safe(template, organ, user, case)
            if not instance:
                return None

            # Marcar com tag para idempotencia
            instance.case_ref = (
                instance.case_ref + f' [{tag}]'
                if instance.case_ref
                else tag
            )
            instance.save(update_fields=['case_ref'])

            # Avancar algumas tarefas (1 ou 2) para ter historico
            steps = index + 1  # running-0 = 1 step, running-1 = 2 steps
            self._advance_tasks(instance, user, steps=steps)

            # Atribuir tarefas pendentes a diferentes usuarios
            self._distribute_tasks(instance, users)

            return instance

        except Exception as exc:
            self.stderr.write(f'    ! Erro running-{index}: {exc}')
            return None

    def _create_completed_instance(
        self, templates, organ, users, cases,
    ) -> FlowInstance | None:
        """Cria uma FlowInstance completada (todas as tarefas concluidas)."""
        tag = f'{SEED_TAG}-completed'

        existing = FlowInstance.objects.filter(
            case_ref__contains=tag,
            status='completed',
        ).first()
        if existing:
            self.stdout.write(f'    (ja existe completed: {existing.id})')
            return existing

        template = templates[0]
        user = users[0]
        case = self._find_available_case(cases)
        if case:
            cases.remove(case)

        try:
            instance = self._start_flow_safe(template, organ, user, case)
            if not instance:
                return None

            instance.case_ref = (
                instance.case_ref + f' [{tag}]'
                if instance.case_ref
                else tag
            )
            instance.save(update_fields=['case_ref'])

            # Completar TODAS as tarefas user_task ate o fluxo terminar
            max_iterations = 50  # safety limit
            iteration = 0
            while instance.status == 'running' and iteration < max_iterations:
                instance.refresh_from_db()
                task = (
                    TaskInstance.objects.filter(
                        instance=instance,
                        status__in=('pending', 'in_progress'),
                        node_type__in=('user_task', 'task'),
                    )
                    .order_by('created_at')
                    .first()
                )
                if not task:
                    break

                # Resolver gateways: escolher primeira opcao
                gateway_choice = ''
                outgoing = FlowEdge.objects.filter(
                    template=instance.template,
                    source_node_id=task.node_id,
                )
                # Verificar se o proximo no e um gateway
                for edge in outgoing:
                    from apps.workflow_definition.models import FlowNode
                    next_node = FlowNode.objects.filter(
                        template=instance.template,
                        node_id=edge.target_node_id,
                        node_type='exclusive_gateway',
                    ).first()
                    if next_node:
                        gw_edge = FlowEdge.objects.filter(
                            template=instance.template,
                            source_node_id=next_node.node_id,
                        ).first()
                        if gw_edge:
                            gateway_choice = (
                                gw_edge.source_handle or gw_edge.edge_id
                            )

                try:
                    flow_service.complete_task(
                        task_id=str(task.id),
                        completed_by=user,
                        notes=f'[{SEED_TAG}] Tarefa concluida.',
                        gateway_choice=gateway_choice,
                    )
                except Exception as exc:
                    logger.warning('complete_task falhou: %s', exc)
                    break

                iteration += 1

            # Se o fluxo nao terminou naturalmente, forcar conclusao
            instance.refresh_from_db()
            if instance.status != 'completed':
                now = timezone.now()
                instance.status = 'completed'
                instance.completed_at = now
                instance.current_node_id = ''
                instance.save(update_fields=[
                    'status', 'completed_at', 'current_node_id',
                ])
                # Marcar tarefas restantes como skipped
                TaskInstance.objects.filter(
                    instance=instance,
                    status__in=('pending', 'in_progress'),
                ).update(status='completed', completed_at=now, completed_by=user)

            return instance

        except Exception as exc:
            self.stderr.write(f'    ! Erro completed: {exc}')
            return None

    def _create_cancelled_instance(
        self, templates, organ, users, cases,
    ) -> FlowInstance | None:
        """Cria uma FlowInstance cancelada."""
        tag = f'{SEED_TAG}-cancelled'

        existing = FlowInstance.objects.filter(
            case_ref__contains=tag,
            status='cancelled',
        ).first()
        if existing:
            self.stdout.write(f'    (ja existe cancelled: {existing.id})')
            return existing

        template = templates[min(1, len(templates) - 1)]
        user = users[0]
        case = self._find_available_case(cases)
        if case:
            cases.remove(case)

        try:
            instance = self._start_flow_safe(template, organ, user, case)
            if not instance:
                return None

            instance.case_ref = (
                instance.case_ref + f' [{tag}]'
                if instance.case_ref
                else tag
            )
            instance.save(update_fields=['case_ref'])

            # Avancar 1 tarefa (para ter historico antes de cancelar)
            self._advance_tasks(instance, user, steps=1)

            # Cancelar via service
            try:
                flow_service.cancel_flow(
                    instance_id=str(instance.id),
                    cancelled_by=user,
                )
            except Exception:
                # Fallback manual
                instance.status = 'cancelled'
                instance.save(update_fields=['status'])
                TaskInstance.objects.filter(
                    instance=instance,
                    status__in=('pending', 'in_progress'),
                ).update(status='skipped')

            return instance

        except Exception as exc:
            self.stderr.write(f'    ! Erro cancelled: {exc}')
            return None

    def _create_pending_instance(
        self, templates, organ, users,
    ) -> FlowInstance | None:
        """Cria uma FlowInstance com status pending (manualmente, sem start_flow)."""
        tag = f'{SEED_TAG}-pending'

        existing = FlowInstance.objects.filter(
            case_ref__contains=tag,
            status='pending',
        ).first()
        if existing:
            self.stdout.write(f'    (ja existe pending: {existing.id})')
            return existing

        template = templates[0]
        user = users[0]

        try:
            instance, created = FlowInstance.objects.get_or_create(
                case_ref=tag,
                status='pending',
                template=template,
                defaults={
                    'organ': organ,
                    'case_title': f'Fluxo pendente de inicio ({template.name})',
                    'current_node_id': '',
                    'started_by': user,
                    'template_name_snapshot': template.name,
                    'template_version_snapshot': template.version,
                },
            )
            if not created:
                self.stdout.write(f'    (ja existe pending: {instance.id})')
            return instance

        except Exception as exc:
            self.stderr.write(f'    ! Erro pending: {exc}')
            return None

    def _distribute_tasks(
        self, instance: FlowInstance, users: list,
    ):
        """Distribui tarefas pendentes sem assignee entre usuarios demo."""
        unassigned = TaskInstance.objects.filter(
            instance=instance,
            status__in=('pending', 'in_progress'),
            assigned_to__isnull=True,
        ).order_by('created_at')

        for i, task in enumerate(unassigned):
            task.assigned_to = users[i % len(users)]
            task.save(update_fields=['assigned_to'])

    # ══════════════════════════════════════════════════════════════════
    # HELPERS — TaskRequest
    # ══════════════════════════════════════════════════════════════════

    def _create_task_requests(
        self, running_instances: list, users: list,
    ) -> int:
        """Cria TaskRequests em todos os tipos e status."""
        if len(users) < 2:
            self.stderr.write(
                '    ! Precisa de pelo menos 2 usuarios para TaskRequests.'
            )
            return 0

        if not running_instances:
            self.stderr.write(
                '    ! Nenhuma instancia running para criar TaskRequests.'
            )
            return 0

        now = timezone.now()
        created_count = 0

        # Coleta tarefas pendentes/in_progress de instancias running
        available_tasks = list(
            TaskInstance.objects.filter(
                instance__in=running_instances,
                status__in=('pending', 'in_progress'),
                node_type__in=('user_task', 'task'),
            ).order_by('created_at')
        )

        if len(available_tasks) < 5:
            # Se nao tem tarefas suficientes, usar as que tiver
            # (e repetir se necessario — get_or_create garante idempotencia)
            while len(available_tasks) < 5 and available_tasks:
                available_tasks = available_tasks * 2

        # Definicao das 5 TaskRequests a criar
        request_specs = [
            {
                'request_type': 'redistribuicao',
                'status': 'pending',
                'justification': (
                    'Redistribuicao necessaria por acumulo de processos '
                    'no setor de divida ativa. Solicito transferencia para '
                    'procurador com menor carga de trabalho.'
                ),
            },
            {
                'request_type': 'redistribuicao',
                'status': 'approved',
                'justification': (
                    'Procurador responsavel em licenca medica. '
                    'Redistribuicao urgente para manter prazos.'
                ),
                'resolution_note': (
                    'Aprovado. Redistribuicao autorizada conforme '
                    'art. 7o do Regimento Interno.'
                ),
            },
            {
                'request_type': 'avocacao',
                'status': 'pending',
                'justification': (
                    'Avocacao pelo Procurador-Geral em razao da '
                    'complexidade e repercussao do caso.'
                ),
            },
            {
                'request_type': 'avocacao',
                'status': 'rejected',
                'justification': (
                    'Solicitacao de avocacao por motivo de especializacao '
                    'na materia tributaria.'
                ),
                'resolution_note': (
                    'Indeferido. O procurador atual possui plena competencia '
                    'para atuar no caso. Manter distribuicao original.'
                ),
            },
            {
                'request_type': 'assessoria',
                'status': 'approved',
                'justification': (
                    'Solicitacao de apoio de assessoria gerencial para '
                    'elaboracao de parecer tecnico sobre impacto orcamentario.'
                ),
                'resolution_note': (
                    'Aprovado. Assessoria designada para apoio na '
                    'elaboracao do parecer.'
                ),
            },
        ]

        for i, spec in enumerate(request_specs):
            if i >= len(available_tasks):
                break

            task = available_tasks[i]
            requester = users[i % len(users)]
            target = users[(i + 1) % len(users)]
            resolver = users[0]  # Geralmente o superadmin resolve

            # Evitar requester == target
            if requester == target and len(users) > 2:
                target = users[(i + 2) % len(users)]

            try:
                request_obj, was_created = TaskRequest.objects.get_or_create(
                    task=task,
                    request_type=spec['request_type'],
                    requester=requester,
                    defaults={
                        'target_user': target,
                        'justification': spec['justification'],
                        'status': spec['status'],
                    },
                )

                if was_created:
                    # Atualizar campos de resolucao se nao for pending
                    if spec['status'] in ('approved', 'rejected'):
                        request_obj.resolved_by = resolver
                        request_obj.resolution_note = spec.get(
                            'resolution_note', ''
                        )
                        request_obj.resolved_at = now - timedelta(hours=i + 1)
                        request_obj.save(update_fields=[
                            'resolved_by', 'resolution_note', 'resolved_at',
                            'status',
                        ])
                    created_count += 1
                else:
                    self.stdout.write(
                        f'    (TaskRequest ja existe: {spec["request_type"]}'
                        f'/{spec["status"]})'
                    )

            except Exception as exc:
                self.stderr.write(
                    f'    ! Erro TaskRequest {spec["request_type"]}: {exc}'
                )

        return created_count

    # ══════════════════════════════════════════════════════════════════
    # HELPERS — ExecutionEvent
    # ══════════════════════════════════════════════════════════════════

    def _create_execution_events(
        self, instances: list, users: list,
    ) -> int:
        """
        Cria ExecutionEvents extras para enriquecer a trilha de auditoria.

        Nota: o service.py ja cria eventos automaticamente (flow_started,
        task_created, task_completed, etc.). Aqui adicionamos eventos
        complementares que nao sao gerados automaticamente.
        """
        if not instances or not users:
            return 0

        created_count = 0

        # Eventos complementares por instancia
        event_templates = [
            {
                'event_type': 'task_reassigned',
                'node_label': 'Reatribuicao de tarefa',
                'metadata_extra': {
                    'reason': 'Redistribuicao por carga de trabalho',
                    'source': SEED_TAG,
                },
            },
            {
                'event_type': 'request_approved',
                'node_label': 'Solicitacao aprovada',
                'metadata_extra': {
                    'request_type': 'redistribuicao',
                    'source': SEED_TAG,
                },
            },
            {
                'event_type': 'request_rejected',
                'node_label': 'Solicitacao rejeitada',
                'metadata_extra': {
                    'request_type': 'avocacao',
                    'reason': 'Competencia mantida',
                    'source': SEED_TAG,
                },
            },
        ]

        for instance in instances:
            actor = users[0]

            # Buscar um node_id valido da instancia
            first_task = (
                TaskInstance.objects.filter(instance=instance)
                .order_by('created_at')
                .first()
            )
            node_id = first_task.node_id if first_task else 'start_1'

            for evt_spec in event_templates:
                # Idempotencia: verificar se ja existe evento do mesmo tipo
                # com metadata source == SEED_TAG para esta instancia
                existing = ExecutionEvent.objects.filter(
                    instance=instance,
                    event_type=evt_spec['event_type'],
                    metadata__source=SEED_TAG,
                ).exists()
                if existing:
                    continue

                try:
                    ExecutionEvent.objects.create(
                        instance=instance,
                        event_type=evt_spec['event_type'],
                        node_id=node_id,
                        node_label=evt_spec['node_label'],
                        actor=actor,
                        metadata=evt_spec['metadata_extra'],
                    )
                    created_count += 1
                except Exception as exc:
                    logger.warning(
                        'Falha ao criar ExecutionEvent %s: %s',
                        evt_spec['event_type'], exc,
                    )

        return created_count

    # ══════════════════════════════════════════════════════════════════
    # HELPERS — LegalDeadline (Prazos)
    # ══════════════════════════════════════════════════════════════════

    def _create_extra_deadlines(
        self, cases: list, users: list,
    ) -> int:
        """
        Cria LegalDeadlines com distribuicao temporal realista:
        - Prazos passados concluidos
        - Prazos de hoje (urgentes)
        - Prazos futuros (7, 14, 30 dias)
        - Prazos vencidos (data passada + status pendente)
        """
        if not cases or not users:
            return 0

        today = date.today()
        created_count = 0
        primary_user = users[0]
        secondary_user = users[1] if len(users) > 1 else users[0]

        deadline_specs = [
            # ── Prazos passados concluidos ──
            {
                'titulo': 'Contestacao — Acao Ordinaria',
                'tipo': 'processual',
                'prioridade': 'alta',
                'status': 'concluido',
                'data_prazo': today - timedelta(days=15),
                'data_conclusao': today - timedelta(days=16),
                'descricao': (
                    'Prazo para apresentacao de contestacao no '
                    'processo de acao ordinaria contra o municipio.'
                ),
                'responsavel': primary_user,
            },
            {
                'titulo': 'Recurso de Apelacao — Execucao Fiscal',
                'tipo': 'recursal',
                'prioridade': 'urgente',
                'status': 'concluido',
                'data_prazo': today - timedelta(days=7),
                'data_conclusao': today - timedelta(days=8),
                'descricao': (
                    'Prazo recursal de 15 dias para interposicao '
                    'de recurso de apelacao (CPC art. 1.003).'
                ),
                'responsavel': secondary_user,
                'appeal_type': 'apelacao',
                'base_legal': 'CPC art. 1.003, para. 5o',
            },
            {
                'titulo': 'Cumprimento de Diligencia — Mandado de Seguranca',
                'tipo': 'processual',
                'prioridade': 'media',
                'status': 'concluido',
                'data_prazo': today - timedelta(days=30),
                'data_conclusao': today - timedelta(days=31),
                'descricao': (
                    'Cumprimento de diligencia determinada pelo juizo '
                    'para juntada de documentos complementares.'
                ),
                'responsavel': primary_user,
            },

            # ── Prazos de HOJE (urgentes) ──
            {
                'titulo': 'Impugnacao ao Cumprimento de Sentenca',
                'tipo': 'processual',
                'prioridade': 'urgente',
                'status': 'pendente',
                'data_prazo': today,
                'descricao': (
                    'URGENTE: Prazo final hoje para impugnacao ao '
                    'cumprimento de sentenca. Valor em discussao: '
                    'R$ 187.000,00.'
                ),
                'responsavel': primary_user,
            },
            {
                'titulo': 'Manifestacao sobre Laudo Pericial',
                'tipo': 'processual',
                'prioridade': 'urgente',
                'status': 'em_andamento',
                'data_prazo': today,
                'descricao': (
                    'Prazo para manifestacao sobre laudo pericial '
                    'contabil apresentado pela parte contraria.'
                ),
                'responsavel': secondary_user,
            },

            # ── Prazos futuros (proximos dias) ──
            {
                'titulo': 'Alegacoes Finais — Processo Administrativo',
                'tipo': 'administrativo',
                'prioridade': 'alta',
                'status': 'pendente',
                'data_prazo': today + timedelta(days=3),
                'descricao': (
                    'Prazo para apresentacao de alegacoes finais '
                    'no processo administrativo disciplinar.'
                ),
                'responsavel': primary_user,
            },
            {
                'titulo': 'Agravo de Instrumento — Tutela Antecipada',
                'tipo': 'recursal',
                'prioridade': 'alta',
                'status': 'pendente',
                'data_prazo': today + timedelta(days=7),
                'descricao': (
                    'Prazo de 15 dias para interposicao de agravo '
                    'de instrumento contra decisao que deferiu tutela '
                    'antecipada.'
                ),
                'responsavel': secondary_user,
                'appeal_type': 'agravo_instrumento',
                'base_legal': 'CPC art. 1.015, I',
            },
            {
                'titulo': 'Resposta a Notificacao Extrajudicial',
                'tipo': 'administrativo',
                'prioridade': 'media',
                'status': 'pendente',
                'data_prazo': today + timedelta(days=14),
                'descricao': (
                    'Prazo para resposta a notificacao extrajudicial '
                    'recebida de empresa contratada.'
                ),
                'responsavel': primary_user,
            },
            {
                'titulo': 'Audiencia de Conciliacao — Preparacao',
                'tipo': 'processual',
                'prioridade': 'media',
                'status': 'pendente',
                'data_prazo': today + timedelta(days=21),
                'descricao': (
                    'Preparacao de documentos e estrategia para '
                    'audiencia de conciliacao agendada.'
                ),
                'responsavel': secondary_user,
            },
            {
                'titulo': 'Renovacao de Procuracao',
                'tipo': 'administrativo',
                'prioridade': 'baixa',
                'status': 'pendente',
                'data_prazo': today + timedelta(days=30),
                'descricao': (
                    'Renovacao de procuracao ad judicia com poderes '
                    'especiais para 3 processos em andamento.'
                ),
                'responsavel': primary_user,
            },

            # ── Prazos VENCIDOS (passado + pendente) ──
            {
                'titulo': 'Embargos de Declaracao — Omissao em Sentenca',
                'tipo': 'recursal',
                'prioridade': 'urgente',
                'status': 'atrasado',
                'data_prazo': today - timedelta(days=3),
                'descricao': (
                    'ATRASADO: Prazo de 5 dias para oposicao de '
                    'embargos de declaracao ja vencido. Necessario '
                    'justificativa para eventual intempestividade.'
                ),
                'responsavel': secondary_user,
                'appeal_type': 'embargos_declaracao',
                'base_legal': 'CPC art. 1.023',
            },
            {
                'titulo': 'Juntada de Comprovante de Pagamento de Custas',
                'tipo': 'processual',
                'prioridade': 'alta',
                'status': 'atrasado',
                'data_prazo': today - timedelta(days=5),
                'descricao': (
                    'ATRASADO: Prazo para juntada de comprovante de '
                    'pagamento das custas processuais. Risco de '
                    'arquivamento do feito.'
                ),
                'responsavel': primary_user,
            },
        ]

        for i, spec in enumerate(deadline_specs):
            # Distribuir entre casos disponiveis
            case = cases[i % len(cases)]

            # Idempotencia: verificar se ja existe prazo com mesmo titulo+caso
            existing = LegalDeadline.objects.filter(
                caso=case,
                titulo=spec['titulo'],
            ).exists()
            if existing:
                continue

            try:
                LegalDeadline.objects.create(
                    caso=case,
                    titulo=spec['titulo'],
                    tipo=spec['tipo'],
                    prioridade=spec['prioridade'],
                    status=spec['status'],
                    data_prazo=spec['data_prazo'],
                    data_conclusao=spec.get('data_conclusao'),
                    descricao=spec['descricao'],
                    responsavel=spec['responsavel'],
                    created_by=primary_user,
                    appeal_type=spec.get('appeal_type', ''),
                    base_legal=spec.get('base_legal', ''),
                )
                created_count += 1
            except Exception as exc:
                self.stderr.write(
                    f'    ! Erro prazo "{spec["titulo"][:40]}": {exc}'
                )

        return created_count
