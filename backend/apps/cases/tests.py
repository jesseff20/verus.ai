"""
Testes para o app Cases (Gestão de Casos Jurídicos).
Cobre: CRUD de casos, prazos, tarefas, documentos, filtros, permissões.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.cases.models import LegalCase, LegalDeadline, CaseTask, CaseDocument

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='advogado',
        email='adv@verus.ai',
        password='testpass123',
        first_name='Advogado',
        last_name='Teste',
        role='analyst',
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username='admin_cases',
        email='admin_cases@verus.ai',
        password='testpass123',
        role='superadmin',
        is_staff=True,
    )


@pytest.fixture
def legal_case(db, user):
    return LegalCase.objects.create(
        titulo='Contratação de Serviço de TI',
        cliente_nome='Prefeitura Municipal',
        especialidade='administrativo',
        status='ativo',
        fase='inicial',
        tribunal='TCE',
        advogado_responsavel=user,
        created_by=user,
    )


# =====================================================
# TESTES DE CASOS - CRUD
# =====================================================
@pytest.mark.django_db
class TestLegalCaseCRUD:
    """Testes de CRUD de casos jurídicos."""

    def test_list_cases(self, api_client, user, legal_case):
        """Usuário autenticado deve listar casos."""
        api_client.force_authenticate(user=user)
        url = reverse('cases:cases-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1
        assert any(c['titulo'] == 'Contratação de Serviço de TI' for c in response.data['results'])

    def test_list_cases_unauthenticated(self, api_client):
        """Não autenticado não deve listar."""
        url = reverse('cases:cases-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_case(self, api_client, user):
        """Usuário autenticado deve criar caso."""
        api_client.force_authenticate(user=user)
        url = reverse('cases:cases-list')
        data = {
            'titulo': 'Novo Caso Teste',
            'cliente_nome': 'Cliente Teste',
            'especialidade': 'civel',
            'status': 'ativo',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['titulo'] == 'Novo Caso Teste'

    def test_create_case_missing_required(self, api_client, user):
        """Criar caso sem campos obrigatórios deve falhar."""
        api_client.force_authenticate(user=user)
        url = reverse('cases:cases-list')
        response = api_client.post(url, {'titulo': 'Incompleto'}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_retrieve_case(self, api_client, user, legal_case):
        """Usuário deve ver detalhes do caso."""
        api_client.force_authenticate(user=user)
        url = reverse('cases:case-detail', kwargs={'case_id': legal_case.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['titulo'] == 'Contratação de Serviço de TI'

    def test_retrieve_nonexistent_case(self, api_client, user):
        """Caso inexistente deve retornar 404."""
        api_client.force_authenticate(user=user)
        url = reverse('cases:case-detail', kwargs={'case_id': '00000000-0000-0000-0000-000000000000'})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_case(self, api_client, user, legal_case):
        """Usuário deve atualizar caso."""
        api_client.force_authenticate(user=user)
        url = reverse('cases:case-detail', kwargs={'case_id': legal_case.id})
        response = api_client.patch(url, {'status': 'suspenso'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'suspenso'

    def test_delete_case(self, api_client, user, legal_case):
        """Usuário deve deletar caso."""
        api_client.force_authenticate(user=user)
        url = reverse('cases:case-detail', kwargs={'case_id': legal_case.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not LegalCase.objects.filter(id=legal_case.id).exists()

    def test_filter_by_especialidade(self, api_client, user, legal_case):
        """Filtrar casos por especialidade."""
        api_client.force_authenticate(user=user)
        url = reverse('cases:cases-list')
        response = api_client.get(url, {'especialidade': 'administrativo'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1

        response = api_client.get(url, {'especialidade': 'criminal'})
        assert response.data['count'] == 0

    def test_filter_by_status(self, api_client, user, legal_case):
        """Filtrar casos por status."""
        api_client.force_authenticate(user=user)
        url = reverse('cases:cases-list')
        response = api_client.get(url, {'status': 'ativo'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1

        response = api_client.get(url, {'status': 'encerrado'})
        assert response.data['count'] == 0

    def test_search_cases(self, api_client, user, legal_case):
        """Buscar casos por texto."""
        api_client.force_authenticate(user=user)
        url = reverse('cases:cases-list')
        response = api_client.get(url, {'search': 'TI'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1

        response = api_client.get(url, {'search': 'Inexistente'})
        assert response.data['count'] == 0


# =====================================================
# TESTES DE PRAZOS
# =====================================================
@pytest.mark.django_db
class TestLegalDeadline:
    """Testes de prazos processuais."""

    def test_create_deadline(self, api_client, user, legal_case):
        """Criar prazo para um caso."""
        api_client.force_authenticate(user=user)
        url = reverse('cases:case-deadlines', kwargs={'case_id': legal_case.id})
        data = {
            'titulo': 'Prazo para Contestação',
            'tipo': 'processual',
            'data_prazo': '2026-06-15',
            'prioridade': 'alta',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['titulo'] == 'Prazo para Contestação'

    def test_list_deadlines(self, api_client, user, legal_case):
        """Listar prazos de um caso."""
        LegalDeadline.objects.create(
            caso=legal_case, titulo='Prazo 1', data_prazo='2026-06-15', created_by=user
        )
        api_client.force_authenticate(user=user)
        url = reverse('cases:case-deadlines', kwargs={'case_id': legal_case.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_all_deadlines_global(self, api_client, user, legal_case):
        """Listar todos os prazos do usuário."""
        LegalDeadline.objects.create(
            caso=legal_case, titulo='Prazo Global', data_prazo='2026-07-01', created_by=user
        )
        api_client.force_authenticate(user=user)
        url = reverse('cases:all-deadlines')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert any(p['titulo'] == 'Prazo Global' for p in response.data)

    def test_deadline_detail(self, api_client, user, legal_case):
        """Detalhes de um prazo específico."""
        deadline = LegalDeadline.objects.create(
            caso=legal_case, titulo='Prazo Detalhe', data_prazo='2026-06-15', created_by=user
        )
        api_client.force_authenticate(user=user)
        url = reverse('cases:deadline-detail', kwargs={'deadline_id': deadline.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['titulo'] == 'Prazo Detalhe'

    def test_deadline_not_found(self, api_client, user):
        """Prazo inexistente retorna 404."""
        api_client.force_authenticate(user=user)
        url = reverse('cases:deadline-detail', kwargs={'deadline_id': '00000000-0000-0000-0000-000000000000'})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# =====================================================
# TESTES DE TAREFAS
# =====================================================
@pytest.mark.django_db
class TestCaseTask:
    """Testes de tarefas de caso."""

    def test_create_task(self, api_client, user, legal_case):
        """Criar tarefa para um caso."""
        api_client.force_authenticate(user=user)
        url = reverse('cases:case-tasks', kwargs={'case_id': legal_case.id})
        data = {
            'titulo': 'Analisar documentos',
            'prioridade': 'alta',
            'status': 'pendente',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['titulo'] == 'Analisar documentos'

    def test_list_tasks(self, api_client, user, legal_case):
        """Listar tarefas de um caso."""
        CaseTask.objects.create(
            caso=legal_case, titulo='Tarefa 1', created_by=user
        )
        api_client.force_authenticate(user=user)
        url = reverse('cases:case-tasks', kwargs={'case_id': legal_case.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert any(t['titulo'] == 'Tarefa 1' for t in response.data)

    def test_task_detail(self, api_client, user, legal_case):
        """Detalhes de uma tarefa."""
        task = CaseTask.objects.create(
            caso=legal_case, titulo='Tarefa Detalhe', created_by=user
        )
        api_client.force_authenticate(user=user)
        url = reverse('cases:task-detail', kwargs={'task_id': task.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['titulo'] == 'Tarefa Detalhe'

    def test_task_update(self, api_client, user, legal_case):
        """Atualizar tarefa."""
        task = CaseTask.objects.create(
            caso=legal_case, titulo='Tarefa Original', created_by=user
        )
        api_client.force_authenticate(user=user)
        url = reverse('cases:task-detail', kwargs={'task_id': task.id})
        response = api_client.patch(url, {'status': 'concluida'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'concluida'


# =====================================================
# TESTES DE DOCUMENTOS DO CASO
# =====================================================
@pytest.mark.django_db
class TestCaseDocument:
    """Testes de documentos vinculados a caso."""

    def test_create_case_document(self, api_client, user, legal_case):
        """Criar documento vinculado ao caso."""
        api_client.force_authenticate(user=user)
        url = reverse('cases:case-documents', kwargs={'case_id': legal_case.id})
        data = {
            'titulo': 'Petição Inicial',
            'tipo': 'peticao',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['titulo'] == 'Petição Inicial'

    def test_list_case_documents(self, api_client, user, legal_case):
        """Listar documentos do caso."""
        CaseDocument.objects.create(
            caso=legal_case, titulo='Doc 1', tipo='peticao', created_by=user
        )
        api_client.force_authenticate(user=user)
        url = reverse('cases:case-documents', kwargs={'case_id': legal_case.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert any(d['titulo'] == 'Doc 1' for d in response.data)


# =====================================================
# TESTES DE STATS
# =====================================================
@pytest.mark.django_db
class TestCasesStats:
    """Testes de estatísticas de casos."""

    def test_cases_stats(self, api_client, user, legal_case):
        """Endpoint de stats deve retornar dados agregados."""
        api_client.force_authenticate(user=user)
        url = reverse('cases:cases-stats')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'total' in response.data
        assert 'por_especialidade' in response.data or 'by_especialidade' in response.data


# =====================================================
# TESTES DE PERMISSÕES
# =====================================================
@pytest.mark.django_db
class TestCasesPermissions:
    """Testes de permissões do app cases."""

    def test_unauthenticated_cannot_create(self, api_client):
        """Não autenticado não pode criar caso."""
        url = reverse('cases:cases-list')
        data = {'titulo': 'Test', 'cliente_nome': 'Test', 'especialidade': 'civel'}
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_cannot_list(self, api_client):
        """Não autenticado não pode listar casos."""
        url = reverse('cases:cases-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =====================================================
# TESTES DO MODEL LEGAL CASE
# =====================================================
@pytest.mark.django_db
class TestLegalCaseModel:
    """Testes do modelo LegalCase."""

    def test_str_representation(self, legal_case):
        assert str(legal_case) == 'Contratação de Serviço de TI (Administrativo)'

    def test_total_prazos_pendentes(self, legal_case, user):
        assert legal_case.total_prazos_pendentes == 0
        LegalDeadline.objects.create(
            caso=legal_case, titulo='Prazo', data_prazo='2026-06-15',
            status='pendente', created_by=user
        )
        assert legal_case.total_prazos_pendentes == 1

    def test_total_tarefas_pendentes(self, legal_case, user):
        assert legal_case.total_tarefas_pendentes == 0
        CaseTask.objects.create(
            caso=legal_case, titulo='Tarefa', status='pendente', created_by=user
        )
        assert legal_case.total_tarefas_pendentes == 1

    def test_model_indexes(self):
        """Verifica que os indexes existem."""
        indexes = [idx.name for idx in LegalCase._meta.indexes]
        assert any('status' in idx for idx in indexes)
        assert any('especialidade' in idx for idx in indexes)
        assert any('advogado_responsavel' in idx for idx in indexes)
