"""
Testes de integração do serviço de execução de fluxos.

Testa o caminho crítico: start → complete → advance → complete → finish.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.organization.models import Organ
from apps.workflow_definition.models import FlowTemplate, FlowNode, FlowEdge
from apps.workflow_execution.models import FlowInstance, TaskInstance, ExecutionEvent
from apps.workflow_execution import service

User = get_user_model()


def _make_organ(name='PGM Teste'):
    return Organ.objects.create(name=name, slug=name.lower().replace(' ', '-'))


def _make_user(organ, role='distribuidor', username=None):
    username = username or f'user_{role}_{organ.id}'
    user = User.objects.create_user(
        username=username,
        email=f'{username}@test.com',
        password='test123',
        role=role,
    )
    user.organ = organ
    user.save()
    return user


def _make_linear_template(organ=None):
    """
    Cria template: start → user_task(distribuidor) → user_task(procurador) → end
    """
    tpl = FlowTemplate.objects.create(
        name='Fluxo Teste Linear',
        status='published',
        organ=organ,
        category='judicial_1',
    )
    start = FlowNode.objects.create(template=tpl, node_id='start', node_type='start_event', label='Início', role='', order=0)
    t1 = FlowNode.objects.create(template=tpl, node_id='t1', node_type='user_task', label='Distribuição', role='distribuidor', order=1)
    t2 = FlowNode.objects.create(template=tpl, node_id='t2', node_type='user_task', label='Elaboração', role='procurador', order=2)
    end = FlowNode.objects.create(template=tpl, node_id='end', node_type='end_event', label='Fim', role='', order=3)
    FlowEdge.objects.create(template=tpl, edge_id='e1', source_node_id='start', target_node_id='t1')
    FlowEdge.objects.create(template=tpl, edge_id='e2', source_node_id='t1', target_node_id='t2')
    FlowEdge.objects.create(template=tpl, edge_id='e3', source_node_id='t2', target_node_id='end')
    return tpl


def _make_gateway_template(organ=None):
    """
    Cria template com gateway XOR: start → task → gateway → [branch_yes | branch_no] → end
    """
    tpl = FlowTemplate.objects.create(
        name='Fluxo Teste Gateway',
        status='published',
        organ=organ,
        category='judicial_1',
    )
    start = FlowNode.objects.create(template=tpl, node_id='start', node_type='start_event', label='Início', role='', order=0)
    t1 = FlowNode.objects.create(template=tpl, node_id='t1', node_type='user_task', label='Análise', role='procurador', order=1)
    gw = FlowNode.objects.create(template=tpl, node_id='gw', node_type='exclusive_gateway', label='Decisão', role='', order=2)
    t_yes = FlowNode.objects.create(template=tpl, node_id='t_yes', node_type='user_task', label='Favorável', role='procurador', order=3)
    t_no = FlowNode.objects.create(template=tpl, node_id='t_no', node_type='user_task', label='Desfavorável', role='procurador', order=4)
    end = FlowNode.objects.create(template=tpl, node_id='end', node_type='end_event', label='Fim', role='', order=5)
    FlowEdge.objects.create(template=tpl, edge_id='e1', source_node_id='start', target_node_id='t1')
    FlowEdge.objects.create(template=tpl, edge_id='e2', source_node_id='t1', target_node_id='gw')
    FlowEdge.objects.create(template=tpl, edge_id='e3', source_node_id='gw', target_node_id='t_yes', source_handle='yes')
    FlowEdge.objects.create(template=tpl, edge_id='e4', source_node_id='gw', target_node_id='t_no', source_handle='no')
    FlowEdge.objects.create(template=tpl, edge_id='e5', source_node_id='t_yes', target_node_id='end')
    FlowEdge.objects.create(template=tpl, edge_id='e6', source_node_id='t_no', target_node_id='end')
    return tpl


class StartFlowTests(TestCase):
    def setUp(self):
        self.organ = _make_organ()
        self.distribuidor = _make_user(self.organ, 'distribuidor')
        self.procurador = _make_user(self.organ, 'procurador')

    def test_start_flow_creates_instance(self):
        tpl = _make_linear_template(self.organ)
        instance = service.start_flow(
            template_id=str(tpl.id),
            organ=self.organ,
            started_by=self.distribuidor,
        )
        self.assertEqual(instance.status, 'running')
        self.assertEqual(instance.organ, self.organ)
        self.assertEqual(instance.started_by, self.distribuidor)

    def test_start_flow_creates_first_task(self):
        tpl = _make_linear_template(self.organ)
        instance = service.start_flow(
            template_id=str(tpl.id),
            organ=self.organ,
            started_by=self.distribuidor,
        )
        tasks = instance.tasks.filter(status='pending')
        self.assertTrue(tasks.exists(), 'Deve criar tarefa pendente após start')
        first_task = tasks.filter(node_id='t1').first()
        self.assertIsNotNone(first_task, 'Deve criar tarefa do nó t1')

    def test_start_flow_auto_assigns_by_role(self):
        tpl = _make_linear_template(self.organ)
        instance = service.start_flow(
            template_id=str(tpl.id),
            organ=self.organ,
            started_by=self.distribuidor,
        )
        task = instance.tasks.filter(node_id='t1').first()
        self.assertIsNotNone(task)
        self.assertEqual(task.assigned_to, self.distribuidor,
                         't1 (role=distribuidor) deve ser atribuída ao distribuidor')

    def test_start_flow_logs_events(self):
        tpl = _make_linear_template(self.organ)
        instance = service.start_flow(
            template_id=str(tpl.id),
            organ=self.organ,
            started_by=self.distribuidor,
        )
        events = instance.events.values_list('event_type', flat=True)
        self.assertIn('flow_started', events)
        # Com auto-atribuição, o evento pode ser task_started ou task_created
        self.assertTrue(
            'task_created' in events or 'task_started' in events,
            'Deve existir evento de criação/início de tarefa'
        )

    def test_start_flow_wrong_organ_raises(self):
        other_organ = _make_organ('Outra PG')
        tpl = FlowTemplate.objects.create(
            name='Privado', status='published', organ=other_organ, category='judicial_1'
        )
        with self.assertRaises(ValueError):
            service.start_flow(str(tpl.id), self.organ, self.distribuidor)

    def test_start_flow_draft_raises(self):
        tpl = FlowTemplate.objects.create(
            name='Rascunho', status='draft', organ=self.organ, category='judicial_1'
        )
        with self.assertRaises(ValueError):
            service.start_flow(str(tpl.id), self.organ, self.distribuidor)


class CompleteTaskTests(TestCase):
    def setUp(self):
        self.organ = _make_organ()
        self.distribuidor = _make_user(self.organ, 'distribuidor', 'dist1')
        self.procurador = _make_user(self.organ, 'procurador', 'proc1')
        self.template = _make_linear_template(self.organ)
        self.instance = service.start_flow(
            str(self.template.id), self.organ, self.distribuidor
        )

    def test_complete_first_task_advances_flow(self):
        t1 = self.instance.tasks.filter(node_id='t1', status='pending').first()
        self.assertIsNotNone(t1)
        result = service.complete_task(str(t1.id), self.distribuidor, notes='OK')
        t1.refresh_from_db()
        self.assertEqual(t1.status, 'completed')
        # Deve criar t2
        t2 = result.tasks.filter(node_id='t2', status='pending').first()
        self.assertIsNotNone(t2, 'Deve criar tarefa t2 após completar t1')

    def test_complete_last_task_finishes_flow(self):
        t1 = self.instance.tasks.filter(node_id='t1', status='pending').first()
        service.complete_task(str(t1.id), self.distribuidor)
        instance = service.complete_task(
            str(self.instance.tasks.filter(node_id='t2', status='pending').first().id),
            self.procurador
        )
        instance.refresh_from_db()
        self.assertEqual(instance.status, 'completed')

    def test_complete_already_completed_raises(self):
        t1 = self.instance.tasks.filter(node_id='t1', status='pending').first()
        service.complete_task(str(t1.id), self.distribuidor)
        t1.refresh_from_db()
        with self.assertRaises(ValueError):
            service.complete_task(str(t1.id), self.distribuidor)

    def test_complete_task_auto_assigns_next(self):
        t1 = self.instance.tasks.filter(node_id='t1', status='pending').first()
        service.complete_task(str(t1.id), self.distribuidor)
        t2 = self.instance.tasks.filter(node_id='t2', status='pending').first()
        self.assertIsNotNone(t2)
        self.assertEqual(t2.assigned_to, self.procurador,
                         't2 (role=procurador) deve ser atribuída ao procurador')


class GatewayTests(TestCase):
    def setUp(self):
        self.organ = _make_organ()
        self.procurador = _make_user(self.organ, 'procurador', 'proc_gw')
        self.template = _make_gateway_template(self.organ)
        self.instance = service.start_flow(
            str(self.template.id), self.organ, self.procurador
        )

    def test_gateway_yes_branch(self):
        t1 = self.instance.tasks.filter(node_id='t1', status='pending').first()
        instance = service.complete_task(str(t1.id), self.procurador, gateway_choice='yes')
        t_yes = instance.tasks.filter(node_id='t_yes', status='pending').first()
        t_no = instance.tasks.filter(node_id='t_no').first()
        self.assertIsNotNone(t_yes, 'Branch yes deve criar tarefa t_yes')
        self.assertIsNone(t_no, 'Branch no NÃO deve criar tarefa t_no')

    def test_gateway_no_branch(self):
        t1 = self.instance.tasks.filter(node_id='t1', status='pending').first()
        instance = service.complete_task(str(t1.id), self.procurador, gateway_choice='no')
        t_no = instance.tasks.filter(node_id='t_no', status='pending').first()
        t_yes = instance.tasks.filter(node_id='t_yes').first()
        self.assertIsNotNone(t_no, 'Branch no deve criar tarefa t_no')
        self.assertIsNone(t_yes, 'Branch yes NÃO deve criar tarefa t_yes')


class CancelFlowTests(TestCase):
    def setUp(self):
        self.organ = _make_organ()
        self.user = _make_user(self.organ, 'gerente', 'gerente1')
        self.template = _make_linear_template(self.organ)
        self.instance = service.start_flow(
            str(self.template.id), self.organ, self.user
        )

    def test_cancel_flow(self):
        instance = service.cancel_flow(str(self.instance.id), self.user)
        self.assertEqual(instance.status, 'cancelled')
        pending = instance.tasks.filter(status='pending').count()
        self.assertEqual(pending, 0, 'Tasks pendentes devem ser skipped')

    def test_cancel_already_finished_raises(self):
        service.cancel_flow(str(self.instance.id), self.user)
        with self.assertRaises(ValueError):
            service.cancel_flow(str(self.instance.id), self.user)


class ApproveRejectRequestTests(TestCase):
    def setUp(self):
        self.organ = _make_organ()
        self.distribuidor = _make_user(self.organ, 'distribuidor', 'dist_req')
        self.procurador = _make_user(self.organ, 'procurador', 'proc_req')
        self.gerente = _make_user(self.organ, 'gerente', 'ger_req')
        self.template = _make_linear_template(self.organ)
        self.instance = service.start_flow(
            str(self.template.id), self.organ, self.distribuidor
        )
        self.task = self.instance.tasks.filter(node_id='t1').first()

        from apps.workflow_execution.models import TaskRequest
        self.req = TaskRequest.objects.create(
            task=self.task,
            request_type='redistribuicao',
            requester=self.distribuidor,
            target_user=self.procurador,
            justification='Teste de redistribuição',
        )

    def test_approve_request_reassigns_task(self):
        service.approve_request(str(self.req.id), self.gerente, 'Aprovado')
        self.task.refresh_from_db()
        self.assertEqual(self.task.assigned_to, self.procurador)

    def test_reject_request(self):
        service.reject_request(str(self.req.id), self.gerente, 'Rejeitado')
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'rejected')

    def test_approve_already_resolved_raises(self):
        service.approve_request(str(self.req.id), self.gerente)
        with self.assertRaises(ValueError):
            service.approve_request(str(self.req.id), self.gerente)
