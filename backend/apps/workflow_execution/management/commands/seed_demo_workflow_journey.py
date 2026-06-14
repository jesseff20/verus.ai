from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.cases.models import LegalCase
from apps.organization.models import Organ
from apps.workflow_definition.models import FlowTemplate
from apps.workflow_execution import service as flow_service
from apps.workflow_execution.models import TaskInstance


DEMO_USERNAME = 'usuario_demo'
DEMO_EMAIL = 'usuario_demo@bravonix.anon'
DEMO_CID = 'CID-DEMO-WF-001'
DEMO_ORGAN_NAME = 'Procuradoria Municipal Demo Verus'
DEMO_FLOW_NAME = 'Fluxo Judicial - Processos Eletronicos (1o Grau)'


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
        'descricao': (
            'Processo base para iniciar uma nova tarefa demonstrativa. '
            'Contem dados suficientes para distribuicao e analise inicial.'
        ),
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
        'descricao': (
            'Processo com fluxo em andamento e tarefa atribuida ao usuario demo.'
        ),
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
        'descricao': (
            'Processo relacionado ao mesmo conjunto CID para demonstrar '
            'processos interconectados.'
        ),
    },
]


class Command(BaseCommand):
    help = 'Cria a jornada de demonstracao de workflow apenas para o usuario_demo.'

    def handle(self, *args, **options):
        with transaction.atomic():
            user = self._ensure_demo_user()
            organ = self._ensure_demo_organ(user)
            template = self._ensure_workflow_template()
            cases = self._ensure_demo_cases(user, organ)
            instance = self._ensure_active_demo_flow(cases['active'], template, organ, user)

        self.stdout.write(self.style.SUCCESS(
            'Jornada demo de workflow criada/atualizada: '
            f'user={user.username}, organ={organ.short_name}, cid={DEMO_CID}, '
            f'active_flow={instance.id}'
        ))

    def _ensure_demo_user(self):
        User = get_user_model()
        user = (
            User.objects.filter(username=DEMO_USERNAME).first()
            or User.objects.filter(email=DEMO_EMAIL).first()
        )
        if user:
            return user

        user = User.objects.create_user(
            username=DEMO_USERNAME,
            email=DEMO_EMAIL,
            password='demo123',
        )
        user.role = 'superadmin'
        user.first_name = 'Usuario'
        user.last_name = 'Demo'
        user.save(update_fields=['role', 'first_name', 'last_name'])
        return user

    def _ensure_demo_organ(self, user):
        if user.organ_id:
            return user.organ

        organ, _created = Organ.objects.get_or_create(
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
        user.organ = organ
        user.save(update_fields=['organ'])
        return organ

    def _ensure_workflow_template(self):
        template = (
            FlowTemplate.objects.filter(
                status='published',
                category='judicial_1',
                is_system_template=True,
                name__icontains='Processos Eletr',
            )
            .order_by('created_at')
            .first()
        )
        if template:
            return template

        try:
            from apps.workflow_definition.management.commands.seed_judicial_flows import (
                Command as JudicialFlowSeedCommand,
            )

            JudicialFlowSeedCommand().handle(force=False)
        except Exception as exc:
            raise CommandError(
                'Nao foi possivel criar o template judicial de demonstracao.'
            ) from exc

        template = (
            FlowTemplate.objects.filter(
                status='published',
                category='judicial_1',
                is_system_template=True,
                name__icontains='Processos Eletr',
            )
            .order_by('created_at')
            .first()
        )
        if not template:
            raise CommandError(f'Template "{DEMO_FLOW_NAME}" nao encontrado.')
        return template

    def _ensure_demo_cases(self, user, organ):
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
                'observacoes': (
                    f'{DEMO_CID} | Conjunto unico de processos demo '
                    'interligados para jornada de workflow.'
                ),
                'deleted_at': None,
            }
            if case:
                for field, value in defaults.items():
                    setattr(case, field, value)
                case.save(update_fields=[*defaults.keys(), 'updated_at'])
            else:
                case = LegalCase.objects.create(numero_processo=number, **defaults)
            cases[case_data['key']] = case
        return cases

    def _ensure_active_demo_flow(self, case, template, organ, user):
        if case.active_flow and case.active_flow.status == 'running':
            instance = case.active_flow
        else:
            instance = flow_service.start_flow(
                template_id=str(template.id),
                organ=organ,
                started_by=user,
                case_id=str(case.id),
            )

        TaskInstance.objects.filter(
            instance=instance,
            status__in=('pending', 'in_progress'),
        ).update(assigned_to=user)

        return instance
