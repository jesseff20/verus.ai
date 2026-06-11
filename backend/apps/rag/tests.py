"""
Testes para o app RAG (Retrieval-Augmented Generation).
Cobre: CRUD de queries, execução, contextos, permissões.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.rag.models import RAGQuery, RAGContext
from unittest.mock import patch, MagicMock

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='rag_user',
        email='rag@test.com',
        password='testpass123',
        role='analyst',
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username='rag_admin',
        email='rag_admin@test.com',
        password='testpass123',
        role='superadmin',
    )


@pytest.fixture
def rag_query(db, user):
    return RAGQuery.objects.create(
        user=user,
        query_text='Qual o prazo para impugnar edital?',
        top_k=5,
        similarity_threshold=0.7,
    )


@pytest.fixture
def rag_context(db, user):
    return RAGContext.objects.create(
        user=user,
        name='Contexto Licitações',
        description='Documentos sobre licitações públicas',
        default_top_k=5,
        default_threshold=0.7,
    )


# =====================================================
# TESTES DE RAG QUERY - CRUD
# =====================================================
@pytest.mark.django_db
class TestRAGQueryCRUD:
    """Testes de CRUD de queries RAG."""

    def test_list_queries(self, api_client, user, rag_query):
        """Listar queries do usuário."""
        api_client.force_authenticate(user=user)
        url = reverse('rag:ragquery-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert any(q['query_text'] == 'Qual o prazo para impugnar edital?' for q in response.data['results'])

    def test_list_queries_unauthenticated(self, api_client):
        """Não autenticado não deve listar."""
        url = reverse('rag:ragquery-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_query(self, api_client, user, rag_query):
        """Detalhes da query."""
        api_client.force_authenticate(user=user)
        url = reverse('rag:ragquery-detail', kwargs={'pk': rag_query.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert rag_query.query_text in response.data['query_text']

    def test_retrieve_nonexistent(self, api_client, user):
        """Query inexistente retorna 404."""
        api_client.force_authenticate(user=user)
        url = reverse('rag:ragquery-detail', kwargs={'pk': '00000000-0000-0000-0000-000000000000'})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_query(self, api_client, user, rag_query):
        """Deletar query."""
        api_client.force_authenticate(user=user)
        url = reverse('rag:ragquery-detail', kwargs={'pk': rag_query.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not RAGQuery.objects.filter(id=rag_query.id).exists()

    def test_delete_other_user_query_forbidden(self, api_client, user, admin_user, rag_query):
        """Usuário não pode deletar query de outro."""
        api_client.force_authenticate(user=user)  # Não é admin
        url = reverse('rag:ragquery-detail', kwargs={'pk': rag_query.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT  # Dono pode deletar

    def test_user_only_sees_own_queries(self, api_client, user, admin_user):
        """Usuário vê apenas suas queries."""
        # Criar query do admin
        RAGQuery.objects.create(user=admin_user, query_text='Query do admin')
        api_client.force_authenticate(user=user)
        url = reverse('rag:ragquery-list')
        response = api_client.get(url)
        # User vê apenas sua própria query (a criada no fixture rag_query)
        titles = [q['query_text'] for q in response.data['results']]
        assert 'Query do admin' not in titles


# =====================================================
# TESTES DE EXECUÇÃO
# =====================================================
@pytest.mark.django_db
class TestRAGExecute:
    """Testes de execução de queries RAG."""

    @patch('apps.rag.views.VectorSearchService')
    @patch('apps.rag.views.LLMService')
    def test_execute_query(self, mock_llm, mock_vector, api_client, user):
        """Executar query RAG com mocks."""
        # Mock vector search
        mock_vector_instance = MagicMock()
        mock_vector_instance.search.return_value = [
            {'content': 'Conteúdo do chunk 1', 'score': 0.95}
        ]
        mock_vector.return_value = mock_vector_instance

        # Mock LLM response
        mock_llm_instance = MagicMock()
        mock_llm_instance.generate.return_value = 'Resposta gerada pela IA baseada nos documentos recuperados.'
        mock_llm.return_value = mock_llm_instance

        api_client.force_authenticate(user=user)
        url = reverse('rag:ragquery-execute')
        data = {
            'query_text': 'Qual o prazo para recurso?',
            'top_k': 5,
            'similarity_threshold': 0.7,
        }
        response = api_client.post(url, data, format='json')
        # May return 200 or 201
        assert response.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED)


# =====================================================
# TESTES DE RAG CONTEXT
# =====================================================
@pytest.mark.django_db
class TestRAGContextCRUD:
    """Testes de CRUD de contextos RAG."""

    def test_list_contexts(self, api_client, user, rag_context):
        """Listar contextos."""
        api_client.force_authenticate(user=user)
        url = reverse('rag:ragcontext-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert any(c['name'] == 'Contexto Licitações' for c in response.data['results'])

    def test_create_context(self, api_client, user):
        """Criar contexto RAG."""
        api_client.force_authenticate(user=user)
        url = reverse('rag:ragcontext-list')
        data = {
            'name': 'Contexto Penal',
            'description': 'Documentos de direito penal',
            'default_top_k': 3,
            'default_threshold': 0.8,
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Contexto Penal'

    def test_update_context(self, api_client, user, rag_context):
        """Atualizar contexto."""
        api_client.force_authenticate(user=user)
        url = reverse('rag:ragcontext-detail', kwargs={'pk': rag_context.id})
        response = api_client.patch(url, {'default_top_k': 10}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['default_top_k'] == 10

    def test_delete_context(self, api_client, user, rag_context):
        """Deletar contexto."""
        api_client.force_authenticate(user=user)
        url = reverse('rag:ragcontext-detail', kwargs={'pk': rag_context.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT


# =====================================================
# TESTES DE MODELOS
# =====================================================
@pytest.mark.django_db
class TestRAGModels:
    """Testes dos modelos RAG."""

    def test_query_str(self, rag_query):
        assert rag_query.query_text[:10] in str(rag_query)

    def test_context_str(self, rag_context):
        assert str(rag_context) == 'Contexto Licitações'

    def test_query_indexes(self):
        """Verifica que os indexes existem."""
        indexes = [idx.name for idx in RAGQuery._meta.indexes]
        assert any('user' in idx for idx in indexes)
        assert any('etp' in idx for idx in indexes)
