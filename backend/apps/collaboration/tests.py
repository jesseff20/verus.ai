"""
Testes para o app Collaboration (Colaboração em Tempo Real).
Cobre: CRUD de sessões, heartbeat, presença, comentários, operações.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.collaboration.models import (
    CollaborationSession, CollaboratorPresence, OperationLog, Comment, Suggestion
)
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='collab_user',
        email='collab@verus.ai',
        password='testpass123',
        role='analyst',
    )


@pytest.fixture
def user2(db):
    return User.objects.create_user(
        username='collab_user2',
        email='collab2@verus.ai',
        password='testpass123',
        role='reviewer',
    )


@pytest.fixture
def session(db, user):
    return CollaborationSession.objects.create(
        document_id='12345678-1234-5678-1234-567812345678',
        document_type='legal',
        created_by=user,
        status='active',
    )


# =====================================================
# TESTES DE SESSÃO - CRUD
# =====================================================
@pytest.mark.django_db
class TestCollaborationSessionCRUD:
    """Testes de CRUD de sessões de colaboração."""

    def test_list_sessions(self, api_client, user, session):
        """Listar sessões do usuário."""
        api_client.force_authenticate(user=user)
        url = reverse('collaboration:collaborationsession-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_list_sessions_unauthenticated(self, api_client):
        """Não autenticado não deve listar."""
        url = reverse('collaboration:collaborationsession-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_session(self, api_client, user):
        """Criar sessão de colaboração."""
        api_client.force_authenticate(user=user)
        url = reverse('collaboration:collaborationsession-list')
        data = {
            'document_id': '87654321-4321-8765-4321-876543210000',
            'document_type': 'petition',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['document_type'] == 'petition'
        assert response.data['status'] == 'active'

    def test_retrieve_session(self, api_client, user, session):
        """Detalhes da sessão."""
        api_client.force_authenticate(user=user)
        url = reverse('collaboration:collaborationsession-detail', kwargs={'pk': session.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['document_type'] == 'legal'

    def test_update_session(self, api_client, user, session):
        """Atualizar sessão."""
        api_client.force_authenticate(user=user)
        url = reverse('collaboration:collaborationsession-detail', kwargs={'pk': session.id})
        response = api_client.patch(url, {'status': 'paused'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'paused'

    def test_delete_session(self, api_client, user, session):
        """Deletar sessão."""
        api_client.force_authenticate(user=user)
        url = reverse('collaboration:collaborationsession-detail', kwargs={'pk': session.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT


# =====================================================
# TESTES DE HEARTBEAT E PRESENÇA
# =====================================================
@pytest.mark.django_db
class TestCollaborationPresence:
    """Testes de presença e heartbeat."""

    def test_join_session(self, api_client, user, session):
        """Entrar na sessão."""
        api_client.force_authenticate(user=user)
        url = reverse('collaboration:collaborationsession-join', kwargs={'pk': session.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert CollaboratorPresence.objects.filter(session=session, user=user).exists()

    def test_heartbeat(self, api_client, user, session):
        """Enviar heartbeat."""
        CollaboratorPresence.objects.create(session=session, user=user)
        api_client.force_authenticate(user=user)
        url = reverse('collaboration:collaborationsession-heartbeat', kwargs={'pk': session.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK

    def test_leave_session(self, api_client, user, session):
        """Sair da sessão."""
        CollaboratorPresence.objects.create(session=session, user=user)
        api_client.force_authenticate(user=user)
        url = reverse('collaboration:collaborationsession-leave', kwargs={'pk': session.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK

    def test_is_active_property(self, user, session):
        """Verificar heartbeat ativo (últimos 30s)."""
        presence = CollaboratorPresence.objects.create(session=session, user=user)
        presence.last_heartbeat = timezone.now()
        presence.save()
        assert presence.is_active() is True

        presence.last_heartbeat = timezone.now() - timedelta(seconds=60)
        presence.save()
        assert presence.is_active() is False


# =====================================================
# TESTES DE OPERAÇÕES
# =====================================================
@pytest.mark.django_db
class TestOperationLog:
    """Testes de log de operações."""

    def test_register_operation(self, api_client, user, session):
        """Registrar operação de edição."""
        api_client.force_authenticate(user=user)
        url = reverse('collaboration:collaborationsession-operations', kwargs={'pk': session.id})
        data = {
            'operation_type': 'insert',
            'section_id': 'sec_1',
            'position': 0,
            'content': 'Texto inserido',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_list_operations(self, api_client, user, session):
        """Listar operações de uma sessão."""
        OperationLog.objects.create(
            session=session, user=user,
            operation_type='insert', content='Teste',
        )
        api_client.force_authenticate(user=user)
        url = reverse('collaboration:collaborationsession-operations', kwargs={'pk': session.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1


# =====================================================
# TESTES DE COMENTÁRIOS
# =====================================================
@pytest.mark.django_db
class TestComments:
    """Testes de comentários."""

    def test_create_comment(self, api_client, user, session):
        """Criar comentário."""
        api_client.force_authenticate(user=user)
        url = reverse('collaboration:collaborationsession-comments', kwargs={'pk': session.id})
        data = {'content': 'Comentário de teste'}
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['content'] == 'Comentário de teste'

    def test_list_comments(self, api_client, user, session):
        """Listar comentários."""
        Comment.objects.create(session=session, author=user, content='Comentário 1')
        api_client.force_authenticate(user=user)
        url = reverse('collaboration:collaborationsession-comments', kwargs={'pk': session.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert any(c['content'] == 'Comentário 1' for c in response.data)

    def test_resolve_comment(self, api_client, user, session, user2):
        """Resolver comentário."""
        comment = Comment.objects.create(session=session, author=user, content='Resolver-me')
        api_client.force_authenticate(user=user2)
        url = reverse('collaboration:collaborationsession-resolve-comment', kwargs={
            'pk': session.id, 'comment_id': comment.id
        })
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_resolved'] is True


# =====================================================
# TESTES DE SUGESTÕES
# =====================================================
@pytest.mark.django_db
class TestSuggestions:
    """Testes de sugestões."""

    def test_create_suggestion(self, api_client, user, session):
        """Criar sugestão."""
        api_client.force_authenticate(user=user)
        url = reverse('collaboration:collaborationsession-suggestions', kwargs={'pk': session.id})
        data = {
            'original_text': 'Texto antigo',
            'suggested_text': 'Texto novo sugerido',
            'section_id': 'sec_1',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['suggested_text'] == 'Texto novo sugerido'

    def test_review_suggestion_accept(self, api_client, user, session, user2):
        """Aceitar sugestão."""
        suggestion = Suggestion.objects.create(
            session=session, author=user,
            original_text='Antigo', suggested_text='Novo',
        )
        api_client.force_authenticate(user=user2)
        url = reverse('collaboration:collaborationsession-review-suggestion', kwargs={
            'pk': session.id, 'suggestion_id': suggestion.id
        })
        response = api_client.post(url, {'status': 'accepted'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'accepted'


# =====================================================
# TESTES DE MODELOS
# =====================================================
@pytest.mark.django_db
class TestCollaborationModels:
    """Testes dos modelos de colaboração."""

    def test_session_str(self, session):
        assert 'legal' in str(session)

    def test_session_is_active(self, session):
        assert session.is_active() is True
        session.status = 'completed'
        assert session.is_active() is False

    def test_presence_str(self, user, session):
        presence = CollaboratorPresence.objects.create(session=session, user=user)
        assert user.username in str(presence)

    def test_operation_str(self, user, session):
        op = OperationLog.objects.create(
            session=session, user=user, operation_type='insert', content='Test'
        )
        assert 'insert' in str(op)

    def test_comment_str(self, user, session):
        comment = Comment.objects.create(session=session, author=user, content='Teste')
        assert user.username in str(comment)

    def test_suggestion_str(self, user, session):
        sug = Suggestion.objects.create(
            session=session, author=user,
            original_text='A', suggested_text='B',
        )
        assert user.username in str(sug)
        assert 'pending' in str(sug)
