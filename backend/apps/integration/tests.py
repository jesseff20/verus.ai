"""
Testes para o app Integration (Integração com Tribunais).
Cobre: CRUD de tribunais, teste de conexão, sincronização, protocolo de petições.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.integration.models import TribunalIntegration, ProcessSync, PetitionProtocol
from unittest.mock import patch, MagicMock

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='int_user',
        email='int@test.com',
        password='testpass123',
        role='analyst',
    )


@pytest.fixture
def tribunal(db):
    return TribunalIntegration.objects.create(
        name='Tribunal de Justiça de São Paulo',
        code='TJSP',
        system_type='esaj',
        api_endpoint='https://api.tjsp.jus.br',
        is_active=True,
    )


# =====================================================
# TESTES DE TRIBUNAL INTEGRATION - CRUD
# =====================================================
@pytest.mark.django_db
class TestTribunalIntegrationCRUD:
    """Testes de CRUD de integrações com tribunais."""

    def test_list_tribunais(self, api_client, user, tribunal):
        """Listar tribunais integrados."""
        api_client.force_authenticate(user=user)
        url = reverse('integration:tribunalintegration-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert any(t['name'] == 'Tribunal de Justiça de São Paulo' for t in response.data)

    def test_list_tribunais_unauthenticated(self, api_client):
        """Não autenticado não deve listar."""
        url = reverse('integration:tribunalintegration-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_tribunal(self, api_client, user):
        """Criar integração com tribunal."""
        api_client.force_authenticate(user=user)
        url = reverse('integration:tribunalintegration-list')
        data = {
            'name': 'TRT-1',
            'code': 'TRT1',
            'system_type': 'pje',
            'api_endpoint': 'https://pje.trt1.jus.br',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'TRT-1'
        assert response.data['code'] == 'TRT1'

    def test_create_tribunal_duplicate_code(self, api_client, user, tribunal):
        """Código duplicado deve falhar."""
        api_client.force_authenticate(user=user)
        url = reverse('integration:tribunalintegration-list')
        data = {
            'name': 'TJSP Cópia',
            'code': 'TJSP',  # Já existe
            'system_type': 'esaj',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_retrieve_tribunal(self, api_client, user, tribunal):
        """Detalhes do tribunal."""
        api_client.force_authenticate(user=user)
        url = reverse('integration:tribunalintegration-detail', kwargs={'pk': tribunal.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['code'] == 'TJSP'

    def test_update_tribunal(self, api_client, user, tribunal):
        """Atualizar tribunal."""
        api_client.force_authenticate(user=user)
        url = reverse('integration:tribunalintegration-detail', kwargs={'pk': tribunal.id})
        response = api_client.patch(url, {'is_active': False}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_active'] is False

    def test_delete_tribunal(self, api_client, user, tribunal):
        """Deletar tribunal."""
        api_client.force_authenticate(user=user)
        url = reverse('integration:tribunalintegration-detail', kwargs={'pk': tribunal.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not TribunalIntegration.objects.filter(id=tribunal.id).exists()


# =====================================================
# TESTES DE CONEXÃO
# =====================================================
@pytest.mark.django_db
class TestTribunalConnection:
    """Testes de conexão com tribunais."""

    @patch('apps.integration.services.esaj_service.get_tribunal_service')
    def test_test_connection_success(self, mock_get_service, api_client, user, tribunal):
        """Testar conexão com sucesso."""
        mock_service = MagicMock()
        mock_service.test_connection.return_value = {'status': 'connected', 'latency_ms': 150}
        mock_get_service.return_value = mock_service

        api_client.force_authenticate(user=user)
        url = reverse('integration:tribunalintegration-test-connection', kwargs={'pk': tribunal.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        mock_service.test_connection.assert_called_once()

    @patch('apps.integration.services.esaj_service.get_tribunal_service')
    def test_test_connection_failure(self, mock_get_service, api_client, user, tribunal):
        """Testar conexão com falha."""
        mock_get_service.return_value = None

        api_client.force_authenticate(user=user)
        url = reverse('integration:tribunalintegration-test-connection', kwargs={'pk': tribunal.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# =====================================================
# TESTES DE SYNCHRONIZATION
# =====================================================
@pytest.mark.django_db
class TestProcessSync:
    """Testes de sincronização de processos."""

    def test_create_process_sync(self, api_client, user, tribunal):
        """Criar sync de processo."""
        api_client.force_authenticate(user=user)
        url = reverse('integration:processsync-list')
        data = {
            'tribunal': str(tribunal.id),
            'process_number': '1234567-89.2026.8.26.0100',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['process_number'] == '1234567-89.2026.8.26.0100'

    def test_list_syncs(self, api_client, user, tribunal):
        """Listar sincronizações."""
        ProcessSync.objects.create(
            tribunal=tribunal,
            process_number='1234567-89.2026.8.26.0100',
        )
        api_client.force_authenticate(user=user)
        url = reverse('integration:processsync-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1


# =====================================================
# TESTES DE PETITION PROTOCOL
# =====================================================
@pytest.mark.django_db
class TestPetitionProtocol:
    """Testes de protocolo de petições."""

    def test_create_petition(self, api_client, user, tribunal):
        """Criar protocolo de petição."""
        api_client.force_authenticate(user=user)
        url = reverse('integration:petitionprotocol-list')
        data = {
            'tribunal': str(tribunal.id),
            'petition_type': 'inicial',
            'petition_title': 'Petição Inicial',
            'petition_content': 'Conteúdo da petição...',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['petition_title'] == 'Petição Inicial'
        assert response.data['status'] == 'draft'

    def test_list_petitions(self, api_client, user, tribunal):
        """Listar petições."""
        PetitionProtocol.objects.create(
            tribunal=tribunal,
            petition_type='inicial',
            petition_title='Minha Petição',
            petition_content='Conteúdo',
            created_by=user,
        )
        api_client.force_authenticate(user=user)
        url = reverse('integration:petitionprotocol-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert any(p['petition_title'] == 'Minha Petição' for p in response.data)

    @patch('apps.integration.views.get_tribunal_service')
    def test_send_petition(self, mock_get_service, api_client, user, tribunal):
        """Enviar petição para protocolo."""
        mock_service = MagicMock()
        mock_service.send_petition.return_value = {
            'protocol_number': 'PROT-2026-12345',
            'status': 'sent',
        }
        mock_get_service.return_value = mock_service

        petition = PetitionProtocol.objects.create(
            tribunal=tribunal,
            petition_type='inicial',
            petition_title='Petição para Envio',
            petition_content='Conteúdo',
            created_by=user,
            status='draft',
        )
        api_client.force_authenticate(user=user)
        url = reverse('integration:petitionprotocol-send', kwargs={'pk': petition.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        mock_service.send_petition.assert_called_once()


# =====================================================
# TESTES DE MODELOS
# =====================================================
@pytest.mark.django_db
class TestIntegrationModels:
    """Testes dos modelos de integração."""

    def test_tribunal_str(self, tribunal):
        assert str(tribunal) == 'Tribunal de Justiça de São Paulo (TJSP)'

    def test_process_sync_str(self, tribunal):
        sync = ProcessSync.objects.create(
            tribunal=tribunal, process_number='1234567-89.2026.8.26.0100'
        )
        assert str(sync) == '1234567-89.2026.8.26.0100 - TJSP'

    def test_petition_str(self, tribunal, user):
        pet = PetitionProtocol.objects.create(
            tribunal=tribunal,
            petition_type='inicial',
            petition_title='Teste',
            petition_content='Conteúdo',
            created_by=user,
        )
        assert str(pet) == 'Teste - Não protocolado'

    def test_petition_with_protocol(self, tribunal, user):
        pet = PetitionProtocol.objects.create(
            tribunal=tribunal,
            petition_type='inicial',
            petition_title='Teste',
            petition_content='Conteúdo',
            protocol_number='PROT-001',
            created_by=user,
        )
        assert 'PROT-001' in str(pet)
