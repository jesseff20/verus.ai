"""
Testes para o app Copilot.
Cobre: CRUD de sessões, mensagens, exportação, compartilhamento, configuração.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.copilot.models import CopilotConfig, CopilotSessionShare
from unittest.mock import patch, MagicMock

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='copilot_user',
        email='copilot@verus.ai',
        password='testpass123',
        role='analyst',
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username='copilot_admin',
        email='copilot_admin@verus.ai',
        password='testpass123',
        role='superadmin',
    )


@pytest.fixture
def copilot_config(db):
    """Cria ou obtém a configuração singleton do Copilot."""
    config = CopilotConfig.get_config()
    return config


# =====================================================
# TESTES DE COPILOT CONFIG
# =====================================================
@pytest.mark.django_db
class TestCopilotConfig:
    """Testes de configuração do Copilot."""

    def test_get_config_criates_default(self):
        """get_config() deve criar configuração padrão se não existir."""
        config = CopilotConfig.get_config()
        assert config.name == 'Copilot Verus.AI'
        assert config.is_active is True

    def test_get_config_returns_existing(self, copilot_config):
        """get_config() deve retornar configuração existente."""
        config = CopilotConfig.get_config()
        assert config == copilot_config

    def test_create_second_config_raises_error(self):
        """Criar segunda configuração deve falhar (singleton)."""
        CopilotConfig.get_config()  # Cria a primeira
        with pytest.raises(Exception):
            CopilotConfig.objects.create(name='Segundo')

    def test_config_str(self, copilot_config):
        """Representação em string."""
        assert 'Copilot' in str(copilot_config)
        assert copilot_config.provider in str(copilot_config)


# =====================================================
# TESTES DE SESSÃO (CRIAÇÃO VIA API)
# =====================================================
@pytest.mark.django_db
class TestCopilotSession:
    """Testes de criação de sessão do Copilot."""

    @patch('apps.copilot.views.session_views.session_service')
    def test_create_session(self, mock_service, api_client, user):
        """Criar sessão deve retornar session_id."""
        mock_service.create_session.return_value = 'mocked-session-uuid-12345'

        api_client.force_authenticate(user=user)
        url = reverse('copilot:session')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['session_id'] == 'mocked-session-uuid-12345'

    @patch('apps.copilot.views.session_views.session_service')
    def test_sync_session(self, mock_service, api_client, user):
        """Sincronizar histórico da sessão."""
        mock_service.set_history.return_value = True

        api_client.force_authenticate(user=user)
        url = reverse('copilot:session-sync')
        data = {
            'session_id': 'test-session-id',
            'messages': [
                {'role': 'user', 'content': 'Olá'},
                {'role': 'assistant', 'content': 'Olá! Como posso ajudar?'},
            ],
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'synced'
        assert response.data['count'] == 2

    @patch('apps.copilot.views.session_views.session_service')
    def test_sync_session_missing_id(self, mock_service, api_client, user):
        """Sincronizar sem session_id deve falhar."""
        api_client.force_authenticate(user=user)
        url = reverse('copilot:session-sync')
        response = api_client.post(url, {'messages': []}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch('apps.copilot.views.session_views.session_service')
    def test_sync_session_not_found(self, mock_service, api_client, user):
        """Sincronizar sessão inexistente deve falhar."""
        mock_service.set_history.return_value = False

        api_client.force_authenticate(user=user)
        url = reverse('copilot:session-sync')
        data = {'session_id': 'not-found', 'messages': []}
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch('apps.copilot.views.session_views.session_service')
    def test_clear_session(self, mock_service, api_client, user):
        """Limpar histórico da sessão."""
        mock_service.clear_history.return_value = True

        api_client.force_authenticate(user=user)
        url = reverse('copilot:session-clear')
        response = api_client.post(url, {'session_id': 'test-session'}, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_chat_endpoint_unauthenticated(self, api_client):
        """Chat sem autenticação deve falhar."""
        url = reverse('copilot:chat')
        response = api_client.post(url, {'message': 'Olá', 'session_id': 'test'}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =====================================================
# TESTES DE COMPARTILHAMENTO
# =====================================================
@pytest.mark.django_db
class TestCopilotSessionShare:
    """Testes de compartilhamento de sessões."""

    def test_create_share(self, api_client, user):
        """Criar link de compartilhamento."""
        api_client.force_authenticate(user=user)
        url = reverse('copilot:share-list')
        data = {
            'session_id': 'session-uuid-12345',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert 'share_code' in response.data
        assert len(response.data['share_code']) == 8

    def test_generate_share_code(self):
        """Gerar código de compartilhamento único."""
        code = CopilotSessionShare.generate_share_code()
        assert len(code) == 8
        assert code.isalnum()

    def test_is_expired_no_expiry(self, user):
        """Compartilhamento sem expiração não expira."""
        share = CopilotSessionShare.objects.create(
            session_id='session-1',
            share_code='ABCD1234',
            created_by=user,
        )
        assert share.is_expired() is False

    def test_is_expired(self, user):
        """Compartilhamento expirado."""
        from django.utils import timezone
        from datetime import timedelta
        share = CopilotSessionShare.objects.create(
            session_id='session-2',
            share_code='EFGH5678',
            created_by=user,
            expires_at=timezone.now() - timedelta(hours=1),
        )
        assert share.is_expired() is True

    def test_share_str(self, user):
        """Representação em string."""
        share = CopilotSessionShare.objects.create(
            session_id='my-session-id...',
            share_code='TEST1234',
            created_by=user,
        )
        assert user.email in str(share)


# =====================================================
# TESTES DE MODEL COPILOT CONFIG
# =====================================================
@pytest.mark.django_db
class TestCopilotConfigModel:
    """Testes do modelo CopilotConfig."""

    def test_singleton_clean_prevents_duplicate(self, copilot_config):
        """Validação impede criação de segunda instância."""
        config = CopilotConfig(
            name='Another Config',
            system_prompt='You are...',
        )
        with pytest.raises(Exception):
            config.full_clean()
