"""
Seed de jornada demo de workflow — cria FlowInstances, TaskInstances e
progressão de tarefas para múltiplos usuários demo.

Depende de:
  - seed_production_demo (cria usuários e casos)
  - seed_judicial_flows (cria FlowTemplates publicados)

Idempotente: verifica existência antes de criar.

Uso: python manage.py seed_demo_workflow_journey
"""
from __future__ import annotations

import logging
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.cases.models import LegalCase
from apps.organization.models import Organ
from apps.workflow_definition.models import FlowTemplate, FlowEdge
from apps.workflow_execution import service as flow_service
from apps.workflow_execution.models import FlowInstance, TaskInstance

logger = logging.getLogger(__name__)

DEMO_ORGAN_NAME = 'Procuradoria Municipal Demo Verus'
DEMO_CID = 'CID-DEMO-WF-001'

# Casos exclusivos deste seed (para garantir pelo menos 3 processos demo)
DEMO_CASES = [
    {
        'key': 'start',
        'numero_processo': '1000001-11.2026.8.08.0048',
        'titulo': 'Mandado de Seguranca - Fornecimento de Medicamento',
        'especialidade': 'administrativo',
        'fase': 'inicial',
        'cliente_nome': 'Municipio Demo',
        'parte_contraria': 'Maria de Souza',
        'valor_causa': Decimal('18000.00'),
        'descricao': 'Processo para iniciar nova tarefa demonstrativa.',
    },
    {
        'key': 'active',
        'numero_processo': '1000002-26.2026.8.08.0048',
        'titulo': 'Acao Ordinaria - Concurso Publico Municipal',
        'especialidade': 'administrativo',
        'fase': 'instrucao',
        'cliente_nome': 'Municipio Demo',
        'parte_contraria': 'Joao Pereira',
        'valor_causa': Decimal('42000.00'),
        'descricao': 'Processo com fluxo em andamento e tarefa atribuida.',
    },
    {
        'key': 'related',
        'numero_processo': '1000003-41.2026.8.08.0048',
        'titulo': 'Execucao Fiscal - Debito de ISS',
        'especialidade': 'tributario',
        'fase': 'execucao',
        'cliente_nome': 'Municipio Demo',
        'parte_contraria': 'Empresa Alfa Ltda.',
        'valor_causa': Decimal('73500.00'),
        'descricao': 'Processo com fluxo avancado — tarefas concluidas e pendentes.',
    },
]


class Command(BaseCommand):
    help = 'Cria jornada demo de workflow com multiplos fluxos, tarefas e usuarios.'

    def handle(self, *args, **options):
        User = get_user_model()

        # 1. Garantir organ demo
        organ = self._ensure_organ()
        self.stdout.write(f'  Organ: {organ.short_name}')

        # 2. Garantir usuario_demo
        demo_user = self._ensure_demo_user(User, organ)
        self.stdout.write(f'  Demo user: {demo_user.username}')

        # 3. Vincular outros usuarios demo ao organ
        linked = self._link_demo_users_to_organ(User, organ)
        self.stdout.write(f'  Usuarios vinculados ao organ: {linked}')

        # 4. Buscar templates publicados
        templates = list(
            FlowTemplate.objects.filter(status='published')
            .order_by('category', 'created_at')
        )
        if not templates:
            self.stderr.write(self.style.WARNING(
                'Nenhum FlowTemplate publicado. Execute seed_judicial_flows primeiro.'
            ))
            return
        self.stdout.write(f'  Templates publicados: {len(templates)}')

        # 5. Garantir casos demo proprios
        own_cases = self._ensure_own_cases(demo_user, organ)
        self.stdout.write(f'  Casos proprios: {len(own_cases)}')

        # 6. Buscar casos do seed_production_demo (se existirem)
        prod_cases = list(
            LegalCase.objects.exclude(
                numero_processo__startswith='1000'
            ).order_by('created_at')[:5]
        )
        self.stdout.write(f'  Casos de producao encontrados: {len(prod_cases)}')

        # 7. Criar fluxos
        total_flows = 0
        total_tasks_created = 0

        # 7a. Fluxo ativo no caso "active" (usuario_demo)
        t1 = templates[0]
        inst_active = self._ensure_flow(own_cases['active'], t1, organ, demo_user)
        if inst_active:
            total_flows += 1
        self.stdout.write(f'  Fluxo ativo (demo): {inst_active.id if inst_active else "ja existe"}')

        # 7b. Fluxo no caso "related" — avançar tarefas
        inst_related = self._ensure_flow(own_cases['related'], t1, organ, demo_user)
        if inst_related:
            total_flows += 1
            completed = self._advance_flow(inst_related, demo_user, steps=2)
            total_tasks_created += completed
            self.stdout.write(f'  Fluxo avancado (related): {completed} tarefas concluidas')

        # 7c. Fluxos nos casos de producao (distribui entre templates e usuarios)
        demo_users = list(
            User.objects.filter(organ=organ, is_active=True)
            .exclude(pk=demo_user.pk)
            .order_by('username')[:4]
        )
        all_users = [demo_user] + demo_users

        for i, case in enumerate(prod_cases):
            if case.active_flow_id and FlowInstance.objects.filter(
                id=case.active_flow_id, status='running'
            ).exists():
                continue  # ja tem fluxo ativo

            tmpl = templates[i % len(templates)]
            user = all_users[i % len(all_users)]

            # Vincular caso ao organ se necessario
            if hasattr(case, 'organ_id') and not case.organ_id:
                case.organ = organ
                case.save(update_fields=['organ'])

            try:
                inst = self._start_flow_safe(case, tmpl, organ, user)
                if inst:
                    total_flows += 1
                    # Avançar algumas tarefas para variedade
                    if i % 3 == 0:
                        self._advance_flow(inst, user, steps=1)
                    self.stdout.write(f'  + Fluxo: {case.titulo[:50]} (user={user.username})')
            except Exception as exc:
                self.stderr.write(f'  ! Falha ao criar fluxo para {case.titulo[:50]}: {exc}')

        # 7d. Criar tarefas extras atribuidas a diferentes usuarios
        extra_tasks = self._assign_pending_tasks_to_users(organ, all_users)
        total_tasks_created += extra_tasks

        self.stdout.write(self.style.SUCCESS(
            f'\nJornada demo concluida: '
            f'{total_flows} fluxos criados, '
            f'{total_tasks_created} tarefas progredidas, '
            f'{len(all_users)} usuarios com tarefas.'
        ))

    # ── Helpers ────────────────────────────────────────────────────

    def _ensure_organ(self):
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

    def _ensure_demo_user(self, User, organ):
        user = (
            User.objects.filter(username='usuario_demo').first()
            or User.objects.filter(email='usuario_demo@bravonix.anon').first()
        )
        if not user:
            user = User.objects.create_user(
                username='usuario_demo',
                email='usuario_demo@bravonix.anon',
                password='demo123',
            )
            user.role = 'superadmin'
            user.first_name = 'Usuario'
            user.last_name = 'Demo'
            user.save(update_fields=['role', 'first_name', 'last_name'])

        if not user.organ_id:
            user.organ = organ
            user.save(update_fields=['organ'])
        return user

    def _link_demo_users_to_organ(self, User, organ):
        """Vincula usuarios demo (criados por seed_production_demo) ao organ."""
        demo_usernames = [
            'joao.silva', 'maria.santos', 'carlos.mendes',
            'ana.rodrigues', 'pedro.lima',
        ]
        linked = 0
        for username in demo_usernames:
            user = User.objects.filter(username=username, is_active=True).first()
            if user and not user.organ_id:
                user.organ = organ
                user.save(update_fields=['organ'])
                linked += 1
        return linked

    def _ensure_own_cases(self, user, organ):
        cases = {}
        for case_data in DEMO_CASES:
            number = case_data['numero_processo']
            case = LegalCase.all_objects.filter(numero_processo=number).first()
            defaults = {
                'titulo': case_data['titulo'],
                'especialidade': case_data['especialidade'],
                'status': 'ativo',
                'fase': case_data['fase'],
                'cliente_nome': case_data['cliente_nome'],
                'parte_contraria': case_data['parte_contraria'],
                'tribunal': 'TJES',
                'vara_juizo': '1a Vara da Fazenda Publica Municipal',
                'comarca': 'Serra',
                'valor_causa': case_data['valor_causa'],
                'advogado_responsavel': user,
                'created_by': user,
                'organ': organ,
                'descricao': case_data['descricao'],
                'deleted_at': None,
            }
            if case:
                for field, value in defaults.items():
                    setattr(case, field, value)
                case.save()
            else:
                case = LegalCase.objects.create(numero_processo=number, **defaults)
            cases[case_data['key']] = case
        return cases

    def _ensure_flow(self, case, template, organ, user):
        """Inicia um fluxo se o caso ainda não tiver um ativo."""
        if case.active_flow_id:
            existing = FlowInstance.objects.filter(
                id=case.active_flow_id, status='running'
            ).first()
            if existing:
                # Garantir tarefas atribuidas ao user
                TaskInstance.objects.filter(
                    instance=existing,
                    status__in=('pending', 'in_progress'),
                    assigned_to__isnull=True,
                ).update(assigned_to=user)
                return existing

        return self._start_flow_safe(case, template, organ, user)

    def _start_flow_safe(self, case, template, organ, user):
        """Inicia fluxo com tratamento de erro."""
        try:
            instance = flow_service.start_flow(
                template_id=str(template.id),
                organ=organ,
                started_by=user,
                case_id=str(case.id),
            )
            # Atribuir tarefas nao atribuidas ao usuario
            TaskInstance.objects.filter(
                instance=instance,
                status__in=('pending', 'in_progress'),
                assigned_to__isnull=True,
            ).update(assigned_to=user)
            return instance
        except Exception as exc:
            logger.warning('Falha ao iniciar fluxo: %s', exc)
            return None

    def _advance_flow(self, instance, user, steps=1):
        """Completa N tarefas pendentes do tipo user_task para avançar o fluxo."""
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

            # Para gateways, pegar a primeira opcao disponivel
            gateway_choice = ''
            if task.node_type in ('exclusive_gateway',):
                edges = FlowEdge.objects.filter(
                    template=instance.template,
                    source_node_id=task.node_id,
                ).first()
                if edges:
                    gateway_choice = edges.source_handle or edges.edge_id

            try:
                flow_service.complete_task(
                    task_id=str(task.id),
                    completed_by=user,
                    notes=f'[demo] Tarefa concluida automaticamente pelo seed.',
                    gateway_choice=gateway_choice,
                )
                completed += 1
            except Exception as exc:
                logger.warning('Falha ao completar task %s: %s', task.id, exc)
                break

        return completed

    def _assign_pending_tasks_to_users(self, organ, users):
        """Distribui tarefas pendentes sem assignee entre os usuarios demo."""
        unassigned = TaskInstance.objects.filter(
            instance__organ=organ,
            status__in=('pending', 'in_progress'),
            assigned_to__isnull=True,
        ).order_by('created_at')

        assigned = 0
        for i, task in enumerate(unassigned):
            user = users[i % len(users)]
            task.assigned_to = user
            task.save(update_fields=['assigned_to'])
            assigned += 1

        return assigned
