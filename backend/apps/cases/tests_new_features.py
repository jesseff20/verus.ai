"""
Tests para novas funcionalidades — Timesheet, CRM, KPIs, NFS-e, Conflito, Petição, Kanban, Risk, Permissions.
"""
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.cases.models import (
    Client, LegalCase, CaseTask, TimeEntry, LeadStage, Lead, LeadActivity,
    LawyerScore, InvoiceNFSe, RiskAssessment,
)

User = get_user_model()


# =====================================================
# HELPERS
# =====================================================

def _create_user(username, role='advogado_pleno', **extra):
    return User.objects.create_user(
        username=username,
        email=f'{username}@verus.ai',
        password='testpass123',
        first_name=username.capitalize(),
        last_name='Teste',
        role=role,
        **extra,
    )


def _create_case(user, titulo='Caso Teste', **extra):
    defaults = {
        'titulo': titulo,
        'cliente_nome': 'Cliente Teste',
        'especialidade': 'civel',
        'status': 'ativo',
        'advogado_responsavel': user,
        'created_by': user,
    }
    defaults.update(extra)
    return LegalCase.objects.create(**defaults)


def _create_client(user, name='Cliente Teste', **extra):
    defaults = {
        'name': name,
        'client_type': 'pessoa_fisica',
        'cpf_cnpj': '123.456.789-00',
        'responsible_lawyer': user,
        'created_by': user,
    }
    defaults.update(extra)
    return Client.objects.create(**defaults)


# =====================================================
# 1. PERMISSION TESTS (CRITICAL)
# =====================================================

class PermissionTests(APITestCase):
    """Testes de permissão por role e ownership."""

    def setUp(self):
        self.admin = _create_user('admin_perm', role='superadmin', is_staff=True)
        self.lawyer1 = _create_user('lawyer1', role='advogado_pleno')
        self.lawyer2 = _create_user('lawyer2', role='advogado_pleno')
        self.case1 = _create_case(self.lawyer1, titulo='Caso do Lawyer1')
        self.client1 = _create_client(self.lawyer1, name='Cliente do Lawyer1')

    def test_admin_can_access_any_case(self):
        """Admin should see all cases regardless of ownership."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('cases:case-detail', kwargs={'case_id': self.case1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['titulo'], 'Caso do Lawyer1')

    def test_lawyer_cannot_access_other_lawyer_case(self):
        """lawyer2 should get 403 on lawyer1's case."""
        self.client.force_authenticate(user=self.lawyer2)
        url = reverse('cases:case-detail', kwargs={'case_id': self.case1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lawyer_can_access_own_case(self):
        """lawyer1 should access their own case."""
        self.client.force_authenticate(user=self.lawyer1)
        url = reverse('cases:case-detail', kwargs={'case_id': self.case1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['titulo'], 'Caso do Lawyer1')

    def test_time_entry_approve_requires_privileged(self):
        """Only admin/socio can approve time entries."""
        entry = TimeEntry.objects.create(
            caso=self.case1,
            advogado=self.lawyer1,
            date=date.today(),
            hours=Decimal('2.00'),
            description='Revisão contratual',
        )
        # lawyer1 (non-privileged) tries to approve
        self.client.force_authenticate(user=self.lawyer1)
        url = reverse('cases:timesheet-approve', kwargs={'entry_id': entry.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # admin approves
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        entry.refresh_from_db()
        self.assertTrue(entry.is_approved)

    def test_nfse_detail_permission(self):
        """Can't access another lawyer's NFS-e."""
        nfse = InvoiceNFSe.objects.create(
            caso=self.case1,
            client=self.client1,
            descricao_servico='Consultoria jurídica',
            valor_servico=Decimal('5000.00'),
            data_competencia=date.today(),
            municipio_prestacao='São Paulo',
            created_by=self.lawyer1,
        )
        # lawyer2 should be denied
        self.client.force_authenticate(user=self.lawyer2)
        url = reverse('cases:nfse-detail', kwargs={'nfse_id': nfse.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # lawyer1 (owner) should access
        self.client.force_authenticate(user=self.lawyer1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_cannot_access_timesheet(self):
        """Unauthenticated user cannot access timesheet."""
        url = reverse('cases:timesheet-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_lead_detail_permission(self):
        """lawyer2 cannot access lawyer1's lead."""
        stage = LeadStage.objects.create(name='Novo', order=1)
        lead = Lead.objects.create(
            name='Lead Privado',
            stage=stage,
            responsible=self.lawyer1,
            created_by=self.lawyer1,
        )
        self.client.force_authenticate(user=self.lawyer2)
        url = reverse('cases:crm-lead-detail', kwargs={'lead_id': lead.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# =====================================================
# 2. TIMESHEET TESTS
# =====================================================

class TimesheetTests(APITestCase):
    """Testes do módulo Timesheet / Controle de Horas."""

    def setUp(self):
        self.user = _create_user('adv_timesheet')
        self.admin = _create_user('admin_ts', role='superadmin', is_staff=True)
        self.case = _create_case(self.user)
        self.client.force_authenticate(user=self.user)

    def test_create_time_entry(self):
        """POST /api/v1/processos/timesheet/ creates a time entry."""
        url = reverse('cases:timesheet-list')
        data = {
            'caso': str(self.case.id),
            'date': str(date.today()),
            'hours': '3.50',
            'description': 'Análise de contrato',
            'billing_type': 'billable',
            'hourly_rate': '250.00',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['description'], 'Análise de contrato')
        self.assertEqual(str(response.data['caso']), str(self.case.id))

    def test_time_entry_auto_calculates_total(self):
        """hours * hourly_rate = total_value on save."""
        entry = TimeEntry.objects.create(
            caso=self.case,
            advogado=self.user,
            date=date.today(),
            hours=Decimal('4.00'),
            hourly_rate=Decimal('300.00'),
            description='Audiência',
        )
        entry.refresh_from_db()
        self.assertEqual(entry.total_value, Decimal('1200.00'))

    def test_time_entry_list(self):
        """GET /api/v1/processos/timesheet/ lists entries for authenticated user."""
        TimeEntry.objects.create(
            caso=self.case, advogado=self.user,
            date=date.today(), hours=Decimal('2.00'),
            description='Revisão 1',
        )
        TimeEntry.objects.create(
            caso=self.case, advogado=self.user,
            date=date.today(), hours=Decimal('1.00'),
            description='Revisão 2',
        )
        url = reverse('cases:timesheet-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Paginated response
        results = response.data.get('results', response.data)
        self.assertGreaterEqual(len(results), 2)

    def test_approve_time_entry(self):
        """POST /api/v1/processos/timesheet/{id}/aprovar/ approves entry."""
        entry = TimeEntry.objects.create(
            caso=self.case, advogado=self.user,
            date=date.today(), hours=Decimal('1.50'),
            description='Despacho',
        )
        self.client.force_authenticate(user=self.admin)
        url = reverse('cases:timesheet-approve', kwargs={'entry_id': entry.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_approved'])
        entry.refresh_from_db()
        self.assertTrue(entry.is_approved)
        self.assertEqual(entry.approved_by, self.admin)

    def test_time_entry_detail_update_delete(self):
        """GET/PUT/DELETE of a specific time entry."""
        entry = TimeEntry.objects.create(
            caso=self.case, advogado=self.user,
            date=date.today(), hours=Decimal('1.00'),
            description='Original',
        )
        url = reverse('cases:timesheet-detail', kwargs={'entry_id': entry.id})

        # GET
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # PUT (partial update)
        response = self.client.put(url, {'description': 'Atualizado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Atualizado')

        # DELETE
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TimeEntry.objects.filter(id=entry.id).exists())


# =====================================================
# 3. CRM / LEAD TESTS
# =====================================================

class LeadTests(APITestCase):
    """Testes do módulo CRM / Pipeline de Leads."""

    def setUp(self):
        self.user = _create_user('adv_crm')
        self.stage_new = LeadStage.objects.create(name='Novo', order=1, color='#3B82F6')
        self.stage_qualified = LeadStage.objects.create(name='Qualificado', order=2, color='#10B981')
        self.stage_won = LeadStage.objects.create(name='Ganho', order=3, is_won=True)
        self.client.force_authenticate(user=self.user)

    def test_create_lead(self):
        """POST /api/v1/processos/crm/leads/ creates a lead."""
        url = reverse('cases:crm-leads')
        data = {
            'name': 'João Silva',
            'email': 'joao@example.com',
            'phone': '11999998888',
            'description': 'Precisa de assessoria trabalhista',
            'specialty': 'trabalhista',
            'source': 'indicacao',
            'temperature': 'hot',
            'stage': str(self.stage_new.id),
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'João Silva')
        self.assertIsNotNone(response.data['id'])

    def test_pipeline_view(self):
        """GET /api/v1/processos/crm/pipeline/ returns grouped data."""
        Lead.objects.create(
            name='Lead 1', stage=self.stage_new,
            responsible=self.user, created_by=self.user,
        )
        Lead.objects.create(
            name='Lead 2', stage=self.stage_qualified,
            responsible=self.user, created_by=self.user,
        )
        url = reverse('cases:crm-pipeline')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('stages', response.data)
        self.assertIn('leads_by_stage', response.data)
        self.assertIn('total_leads', response.data)
        self.assertEqual(response.data['total_leads'], 2)

    def test_convert_lead_creates_client_and_case(self):
        """POST /api/v1/processos/crm/leads/{id}/converter/ converts lead."""
        lead = Lead.objects.create(
            name='Maria Convertida',
            email='maria@test.com',
            phone='21988887777',
            cpf_cnpj='987.654.321-00',
            description='Divórcio consensual',
            specialty='familia',
            stage=self.stage_qualified,
            estimated_value=Decimal('15000.00'),
            responsible=self.user,
            created_by=self.user,
        )
        url = reverse('cases:crm-lead-convert', kwargs={'lead_id': lead.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('client_id', response.data)
        self.assertIn('case_id', response.data)
        self.assertIsNotNone(response.data['client_id'])
        self.assertIsNotNone(response.data['case_id'])

        # Verify client was created
        client = Client.objects.get(id=response.data['client_id'])
        self.assertEqual(client.name, 'Maria Convertida')

        # Verify case was created
        caso = LegalCase.objects.get(id=response.data['case_id'])
        self.assertEqual(caso.especialidade, 'familia')

        # Verify lead was marked as converted
        lead.refresh_from_db()
        self.assertIsNotNone(lead.converted_at)
        self.assertEqual(lead.converted_client_id, client.id)

    def test_lead_stage_change_creates_activity(self):
        """PATCH lead with new stage creates LeadActivity with type 'stage_change'."""
        lead = Lead.objects.create(
            name='Lead Movido',
            stage=self.stage_new,
            responsible=self.user,
            created_by=self.user,
        )
        url = reverse('cases:crm-lead-detail', kwargs={'lead_id': lead.id})
        response = self.client.patch(url, {'stage': str(self.stage_qualified.id)}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check activity was created
        activities = LeadActivity.objects.filter(lead=lead, activity_type='stage_change')
        self.assertEqual(activities.count(), 1)
        self.assertIn('Qualificado', activities.first().description)

    def test_lead_add_activity(self):
        """POST /api/v1/processos/crm/leads/{id}/atividade/ adds activity."""
        lead = Lead.objects.create(
            name='Lead Atividade',
            stage=self.stage_new,
            responsible=self.user,
            created_by=self.user,
        )
        url = reverse('cases:crm-lead-activity', kwargs={'lead_id': lead.id})
        data = {
            'activity_type': 'call',
            'description': 'Ligação de prospecção',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['activity_type'], 'call')

    def test_lead_delete(self):
        """DELETE /api/v1/processos/crm/leads/{id}/ removes lead."""
        lead = Lead.objects.create(
            name='Lead Deletável',
            stage=self.stage_new,
            responsible=self.user,
            created_by=self.user,
        )
        url = reverse('cases:crm-lead-detail', kwargs={'lead_id': lead.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Lead.objects.filter(id=lead.id).exists())


# =====================================================
# 4. CONFLICT CHECK TESTS
# =====================================================

class ConflictCheckTests(APITestCase):
    """Testes de verificação de conflito de interesses."""

    def setUp(self):
        self.user = _create_user('adv_conflict')
        self.client.force_authenticate(user=self.user)
        # Create case with adverse party
        self.case = _create_case(
            self.user,
            titulo='Caso com Parte Contrária',
            parte_contraria='Empresa XYZ Ltda',
            parte_contraria_cpf_cnpj='12.345.678/0001-99',
        )

    def test_conflict_by_cpf(self):
        """Exact CPF/CNPJ match with adverse party should return critical conflict."""
        url = reverse('cases:check-conflict')
        data = {
            'name': 'Empresa XYZ',
            'cpf_cnpj': '12.345.678/0001-99',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['has_conflicts'])
        self.assertEqual(response.data['severity'], 'critical')
        self.assertGreater(len(response.data['conflicts']), 0)
        cpf_conflicts = [c for c in response.data['conflicts'] if c['type'] == 'cpf_cnpj_match']
        self.assertGreater(len(cpf_conflicts), 0)

    def test_no_conflict(self):
        """Name/CPF that doesn't match should return no conflicts."""
        url = reverse('cases:check-conflict')
        data = {
            'name': 'Pessoa Totalmente Diferente',
            'cpf_cnpj': '999.888.777-66',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['has_conflicts'])
        self.assertEqual(response.data['severity'], 'none')
        self.assertEqual(len(response.data['conflicts']), 0)

    def test_conflict_by_name_similarity(self):
        """Similar name should trigger warning."""
        url = reverse('cases:check-conflict')
        data = {
            'name': 'Empresa XYZ Ltda',  # Same as adverse party
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['has_conflicts'])
        name_conflicts = [c for c in response.data['conflicts'] if c['type'] == 'name_similarity']
        self.assertGreater(len(name_conflicts), 0)

    def test_conflict_check_requires_name(self):
        """Missing name should return 400."""
        url = reverse('cases:check-conflict')
        data = {'cpf_cnpj': '111.222.333-44'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_conflict_check_returns_metadata(self):
        """Response should include OAB reference and search scope."""
        url = reverse('cases:check-conflict')
        data = {'name': 'Qualquer Nome'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('oab_reference', response.data)
        self.assertIn('criteria_used', response.data)
        self.assertIn('search_scope', response.data)


# =====================================================
# 5. KPI TESTS
# =====================================================

class KPITests(APITestCase):
    """Testes do módulo de KPIs gamificados."""

    def setUp(self):
        self.user = _create_user('adv_kpi')
        self.admin = _create_user('admin_kpi', role='superadmin', is_staff=True)
        self.client.force_authenticate(user=self.user)

    def test_score_calculation(self):
        """LawyerScore.calculate_score() returns correct value."""
        today = date.today()
        score = LawyerScore.objects.create(
            lawyer=self.user,
            period_start=today.replace(day=1),
            period_end=today,
            cases_won=2,        # 2 * 100 = 200
            cases_settled=1,    # 1 * 50 = 50
            deadlines_met=5,    # 5 * 20 = 100
            deadlines_missed=1, # 1 * -30 = -30
            tasks_completed=10, # 10 * 10 = 100
            hours_logged=Decimal('20.00'),  # 20 * 5 = 100
            documents_generated=3,  # 3 * 15 = 45
            client_satisfaction=Decimal('8.5'),  # int(8.5 * 10) = 85
        )
        result = score.calculate_score()
        # 200 + 50 + 100 - 30 + 100 + 100 + 45 + 85 = 650
        self.assertEqual(result, 650)
        self.assertEqual(score.total_score, 650)

    def test_score_never_negative(self):
        """Score should be clamped to 0 minimum."""
        today = date.today()
        score = LawyerScore.objects.create(
            lawyer=self.user,
            period_start=today.replace(day=1),
            period_end=today,
            deadlines_missed=100,  # -3000, everything else 0
        )
        result = score.calculate_score()
        self.assertEqual(result, 0)

    def test_kpi_my_scores(self):
        """GET /api/v1/processos/kpis/meus-scores/ returns user's scores."""
        today = date.today()
        LawyerScore.objects.create(
            lawyer=self.user,
            period_start=today.replace(day=1),
            period_end=today,
            total_score=500,
        )
        url = reverse('cases:kpi-my-scores')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)


# =====================================================
# 6. KANBAN TESTS
# =====================================================

class KanbanTests(APITestCase):
    """Testes do Kanban de Tarefas."""

    def setUp(self):
        self.user = _create_user('adv_kanban')
        self.case = _create_case(self.user)
        self.client.force_authenticate(user=self.user)

    def test_kanban_view(self):
        """GET /api/v1/processos/kanban/ returns columns with tasks."""
        CaseTask.objects.create(
            caso=self.case, titulo='Tarefa Pendente',
            status='pendente', responsavel=self.user, created_by=self.user,
        )
        CaseTask.objects.create(
            caso=self.case, titulo='Tarefa Em Andamento',
            status='em_andamento', responsavel=self.user, created_by=self.user,
        )
        url = reverse('cases:tasks-kanban')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)  # 4 columns

        # Find columns
        pendente_col = next(c for c in response.data if c['id'] == 'pendente')
        em_andamento_col = next(c for c in response.data if c['id'] == 'em_andamento')
        self.assertEqual(len(pendente_col['tasks']), 1)
        self.assertEqual(len(em_andamento_col['tasks']), 1)

    def test_kanban_filter_by_case(self):
        """GET /api/v1/processos/kanban/?case_id=... filters by case."""
        case2 = _create_case(self.user, titulo='Outro Caso')
        CaseTask.objects.create(
            caso=self.case, titulo='T1', status='pendente',
            responsavel=self.user, created_by=self.user,
        )
        CaseTask.objects.create(
            caso=case2, titulo='T2', status='pendente',
            responsavel=self.user, created_by=self.user,
        )
        url = reverse('cases:tasks-kanban')
        response = self.client.get(url, {'case_id': str(self.case.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pendente_col = next(c for c in response.data if c['id'] == 'pendente')
        self.assertEqual(len(pendente_col['tasks']), 1)
        self.assertEqual(pendente_col['tasks'][0]['titulo'], 'T1')

    def test_move_task(self):
        """PATCH /api/v1/processos/kanban/{id}/mover/ changes status."""
        task = CaseTask.objects.create(
            caso=self.case, titulo='Tarefa para mover',
            status='pendente', responsavel=self.user, created_by=self.user,
        )
        url = reverse('cases:task-move', kwargs={'task_id': task.id})
        response = self.client.patch(url, {'status': 'em_andamento'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'em_andamento')

    def test_move_to_concluida_sets_date(self):
        """Moving to 'concluida' sets data_conclusao."""
        task = CaseTask.objects.create(
            caso=self.case, titulo='Tarefa para concluir',
            status='em_andamento', responsavel=self.user, created_by=self.user,
        )
        url = reverse('cases:task-move', kwargs={'task_id': task.id})
        response = self.client.patch(url, {'status': 'concluida'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertIsNotNone(task.data_conclusao)
        self.assertEqual(task.data_conclusao, date.today())

    def test_move_task_invalid_status(self):
        """Moving to invalid status returns 400."""
        task = CaseTask.objects.create(
            caso=self.case, titulo='Tarefa inválida',
            status='pendente', responsavel=self.user, created_by=self.user,
        )
        url = reverse('cases:task-move', kwargs={'task_id': task.id})
        response = self.client.patch(url, {'status': 'inexistente'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# =====================================================
# 7. NFS-e TESTS
# =====================================================

class NFSeTests(APITestCase):
    """Testes do módulo NFS-e (Nota Fiscal de Serviço Eletrônica)."""

    def setUp(self):
        self.user = _create_user('adv_nfse')
        self.case = _create_case(self.user)
        self.client_obj = _create_client(self.user, name='Empresa Faturada')
        self.client.force_authenticate(user=self.user)

    def test_create_nfse(self):
        """POST /api/v1/processos/nfse/ creates an NFS-e draft."""
        url = reverse('cases:nfse-list')
        data = {
            'caso': str(self.case.id),
            'client': str(self.client_obj.id),
            'descricao_servico': 'Consultoria jurídica empresarial',
            'valor_servico': '10000.00',
            'data_competencia': str(date.today()),
            'municipio_prestacao': 'São Paulo',
            'aliquota_iss': '5.00',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'draft')

    def test_nfse_auto_calculates_taxes(self):
        """save() calculates base_calculo, valor_iss, valor_liquido."""
        nfse = InvoiceNFSe.objects.create(
            caso=self.case,
            client=self.client_obj,
            descricao_servico='Honorários advocatícios',
            valor_servico=Decimal('10000.00'),
            valor_deducoes=Decimal('1000.00'),
            aliquota_iss=Decimal('5.00'),
            irrf=Decimal('150.00'),
            pis=Decimal('65.00'),
            cofins=Decimal('300.00'),
            csll=Decimal('100.00'),
            inss=Decimal('0.00'),
            data_competencia=date.today(),
            municipio_prestacao='Rio de Janeiro',
            created_by=self.user,
        )
        nfse.refresh_from_db()
        # base_calculo = 10000 - 1000 = 9000
        self.assertEqual(nfse.base_calculo, Decimal('9000.00'))
        # valor_iss = 9000 * 5/100 = 450
        self.assertEqual(nfse.valor_iss, Decimal('450.00'))
        # total_retencoes = 150 + 65 + 300 + 100 + 0 = 615
        # valor_liquido = 10000 - 450 - 615 = 8935
        self.assertEqual(nfse.valor_liquido, Decimal('8935.00'))

    def test_nfse_list_filtered_by_client(self):
        """GET /api/v1/processos/nfse/?client=... filters by client."""
        InvoiceNFSe.objects.create(
            client=self.client_obj,
            descricao_servico='Serviço 1',
            valor_servico=Decimal('5000.00'),
            data_competencia=date.today(),
            municipio_prestacao='SP',
            created_by=self.user,
        )
        url = reverse('cases:nfse-list')
        response = self.client.get(url, {'client': str(self.client_obj.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertGreaterEqual(len(results), 1)

    def test_nfse_detail_get_update_delete(self):
        """GET/PUT/DELETE of NFS-e."""
        nfse = InvoiceNFSe.objects.create(
            caso=self.case,
            client=self.client_obj,
            descricao_servico='Serviço original',
            valor_servico=Decimal('3000.00'),
            data_competencia=date.today(),
            municipio_prestacao='SP',
            created_by=self.user,
        )
        url = reverse('cases:nfse-detail', kwargs={'nfse_id': nfse.id})

        # GET
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # PUT (partial)
        response = self.client.put(url, {'descricao_servico': 'Atualizado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # DELETE
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


# =====================================================
# 8. RISK ASSESSMENT TESTS
# =====================================================

class RiskAssessmentTests(APITestCase):
    """Testes do módulo de Avaliação de Risco."""

    def setUp(self):
        self.user = _create_user('adv_risk')
        self.case = _create_case(self.user)
        self.client.force_authenticate(user=self.user)

    def test_create_assessment(self):
        """POST /api/v1/processos/{case_id}/risco/historico/ creates assessment."""
        url = reverse('cases:risk-history', kwargs={'case_id': self.case.id})
        data = {
            'risk_level': 'medium',
            'risk_score': 55,
            'analysis': 'Risco moderado devido a fase inicial',
            'recommendation': 'Monitorar prazos de perto',
            'trigger': 'manual',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['risk_level'], 'medium')
        self.assertEqual(response.data['risk_score'], 55)

    def test_tracks_previous_level(self):
        """Second assessment stores previous_level and level_changed."""
        url = reverse('cases:risk-history', kwargs={'case_id': self.case.id})

        # First assessment
        data1 = {
            'risk_level': 'low',
            'risk_score': 25,
            'analysis': 'Risco baixo',
        }
        response1 = self.client.post(url, data1, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Second assessment with different level
        data2 = {
            'risk_level': 'high',
            'risk_score': 80,
            'analysis': 'Risco elevado após prazo perdido',
            'trigger': 'prazo_perdido',
        }
        response2 = self.client.post(url, data2, format='json')
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.data['previous_level'], 'low')
        self.assertTrue(response2.data['level_changed'])

    def test_tracks_same_level_no_change(self):
        """Same level should mark level_changed=False."""
        url = reverse('cases:risk-history', kwargs={'case_id': self.case.id})

        self.client.post(url, {
            'risk_level': 'medium', 'risk_score': 50, 'analysis': 'A'
        }, format='json')
        response = self.client.post(url, {
            'risk_level': 'medium', 'risk_score': 55, 'analysis': 'B'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['level_changed'])

    def test_list_assessments(self):
        """GET /api/v1/processos/{case_id}/risco/historico/ returns history."""
        RiskAssessment.objects.create(
            caso=self.case, risk_level='low', risk_score=20,
            analysis='Avaliação 1', assessed_by=self.user,
        )
        RiskAssessment.objects.create(
            caso=self.case, risk_level='high', risk_score=75,
            analysis='Avaliação 2', assessed_by=self.user,
        )
        url = reverse('cases:risk-history', kwargs={'case_id': self.case.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_risk_case_access_denied(self):
        """User without case access cannot view risk assessments."""
        other_user = _create_user('adv_risk_other')
        self.client.force_authenticate(user=other_user)
        url = reverse('cases:risk-history', kwargs={'case_id': self.case.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# =====================================================
# 9. PAGINATION TESTS
# =====================================================

class PaginationTests(APITestCase):
    """Testes de paginação em endpoints paginados."""

    def setUp(self):
        self.user = _create_user('adv_pag')
        self.case = _create_case(self.user)
        self.client.force_authenticate(user=self.user)

    def test_timesheet_paginated(self):
        """Create 25 entries, request page 1 should return 20 results + next link."""
        for i in range(25):
            TimeEntry.objects.create(
                caso=self.case,
                advogado=self.user,
                date=date.today() - timedelta(days=i),
                hours=Decimal('1.00'),
                description=f'Entry {i}',
            )
        url = reverse('cases:timesheet-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 20)
        self.assertIsNotNone(response.data['next'])
        self.assertEqual(response.data['count'], 25)

    def test_leads_paginated(self):
        """Create 25 leads, request page 1 should return 20 results + next link."""
        stage = LeadStage.objects.create(name='Test Stage', order=1)
        for i in range(25):
            Lead.objects.create(
                name=f'Lead {i}',
                stage=stage,
                responsible=self.user,
                created_by=self.user,
            )
        url = reverse('cases:crm-leads')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 20)
        self.assertIsNotNone(response.data['next'])
        self.assertEqual(response.data['count'], 25)

    def test_nfse_paginated(self):
        """Create 25 NFS-e, request page 1 should return 20 results."""
        client_obj = _create_client(self.user, name='Client Pag')
        for i in range(25):
            InvoiceNFSe.objects.create(
                client=client_obj,
                descricao_servico=f'Serviço {i}',
                valor_servico=Decimal('1000.00'),
                data_competencia=date.today(),
                municipio_prestacao='SP',
                created_by=self.user,
            )
        url = reverse('cases:nfse-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 20)
        self.assertEqual(response.data['count'], 25)

    def test_page_size_param(self):
        """page_size query param should control results per page."""
        for i in range(15):
            TimeEntry.objects.create(
                caso=self.case, advogado=self.user,
                date=date.today() - timedelta(days=i),
                hours=Decimal('1.00'), description=f'E {i}',
            )
        url = reverse('cases:timesheet-list')
        response = self.client.get(url, {'page_size': 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        self.assertEqual(response.data['count'], 15)


# =====================================================
# 10. MODEL UNIT TESTS
# =====================================================

class TimeEntryModelTests(TestCase):
    """Testes unitários do model TimeEntry."""

    def setUp(self):
        self.user = _create_user('model_user')
        self.case = _create_case(self.user)

    def test_str_representation(self):
        entry = TimeEntry.objects.create(
            caso=self.case, advogado=self.user,
            date=date(2026, 5, 30), hours=Decimal('2.50'),
            description='Teste',
        )
        s = str(entry)
        self.assertIn('2.50', s)
        self.assertIn('2026-05-30', s)

    def test_total_value_without_rate(self):
        """Without hourly_rate, total_value should remain None."""
        entry = TimeEntry.objects.create(
            caso=self.case, advogado=self.user,
            date=date.today(), hours=Decimal('3.00'),
            description='Sem rate',
        )
        self.assertIsNone(entry.total_value)


class InvoiceNFSeModelTests(TestCase):
    """Testes unitários do model InvoiceNFSe."""

    def setUp(self):
        self.user = _create_user('nfse_model_user')
        self.client_obj = _create_client(self.user)

    def test_str_representation(self):
        nfse = InvoiceNFSe.objects.create(
            client=self.client_obj,
            descricao_servico='Teste',
            valor_servico=Decimal('5000.00'),
            data_competencia=date.today(),
            municipio_prestacao='SP',
            created_by=self.user,
        )
        s = str(nfse)
        self.assertIn('RASCUNHO', s)
        self.assertIn('5000.00', s)

    def test_zero_deductions(self):
        """With zero deductions, base_calculo equals valor_servico."""
        nfse = InvoiceNFSe.objects.create(
            client=self.client_obj,
            descricao_servico='Sem deduções',
            valor_servico=Decimal('8000.00'),
            aliquota_iss=Decimal('2.00'),
            data_competencia=date.today(),
            municipio_prestacao='SP',
            created_by=self.user,
        )
        self.assertEqual(nfse.base_calculo, Decimal('8000.00'))
        self.assertEqual(nfse.valor_iss, Decimal('160.00'))
        # valor_liquido = 8000 - 160 - 0 = 7840
        self.assertEqual(nfse.valor_liquido, Decimal('7840.00'))


class LawyerScoreModelTests(TestCase):
    """Testes unitários do model LawyerScore."""

    def setUp(self):
        self.user = _create_user('score_model_user')

    def test_calculate_score_empty(self):
        """All zeros should give score 0."""
        score = LawyerScore.objects.create(
            lawyer=self.user,
            period_start=date(2026, 5, 1),
            period_end=date(2026, 5, 31),
        )
        result = score.calculate_score()
        self.assertEqual(result, 0)

    def test_calculate_score_with_satisfaction(self):
        """Client satisfaction contributes int(satisfaction * 10) points."""
        score = LawyerScore.objects.create(
            lawyer=self.user,
            period_start=date(2026, 5, 1),
            period_end=date(2026, 5, 31),
            client_satisfaction=Decimal('9.0'),
        )
        result = score.calculate_score()
        self.assertEqual(result, 90)  # int(9.0 * 10) = 90


class LeadStageModelTests(TestCase):
    """Testes unitários do model LeadStage."""

    def test_ordering(self):
        """Stages should be ordered by 'order' field."""
        s3 = LeadStage.objects.create(name='C', order=3)
        s1 = LeadStage.objects.create(name='A', order=1)
        s2 = LeadStage.objects.create(name='B', order=2)
        stages = list(LeadStage.objects.all())
        self.assertEqual(stages[0].name, 'A')
        self.assertEqual(stages[1].name, 'B')
        self.assertEqual(stages[2].name, 'C')
