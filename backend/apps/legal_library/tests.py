"""
Testes para o app LegalLibrary (Biblioteca Viva de Argumentos Jurídicos).
Cobre: CRUD de argumentos, coleções, métricas, sugestão, permissões.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.legal_library.models import LegalArgument, ArgumentCollection, ArgumentUsage

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='legal_user',
        email='legal@test.com',
        password='testpass123',
        role='analyst',
    )


@pytest.fixture
def argument(db, user):
    return LegalArgument.objects.create(
        title='Dano Moral - Pessoa Jurídica',
        content='A pessoa jurídica pode sofrer dano moral...',
        summary='Súmula 227 STJ',
        category='fundamentacao',
        specialty='CIV',
        tribunal='STJ',
        created_by=user,
        status='approved',
    )


# =====================================================
# TESTES DE ARGUMENTOS - CRUD
# =====================================================
@pytest.mark.django_db
class TestLegalArgumentCRUD:
    """Testes de CRUD de argumentos jurídicos."""

    def test_list_arguments(self, api_client, user, argument):
        """Listar argumentos."""
        api_client.force_authenticate(user=user)
        url = reverse('legal_library:legalargument-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert any(a['title'] == 'Dano Moral - Pessoa Jurídica' for a in response.data['results'])

    def test_list_unauthenticated(self, api_client):
        """Não autenticado não deve listar."""
        url = reverse('legal_library:legalargument-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_argument(self, api_client, user):
        """Criar argumento jurídico."""
        api_client.force_authenticate(user=user)
        url = reverse('legal_library:legalargument-list')
        data = {
            'title': 'Novo Argumento - Súmula Vinculante',
            'content': 'Conteúdo do argumento detalhado...',
            'category': 'merito',
            'specialty': 'CIV',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'Novo Argumento - Súmula Vinculante'

    def test_create_argument_missing_required(self, api_client, user):
        """Criar argumento sem campos obrigatórios deve falhar."""
        api_client.force_authenticate(user=user)
        url = reverse('legal_library:legalargument-list')
        response = api_client.post(url, {'title': 'Incompleto'}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_retrieve_argument(self, api_client, user, argument):
        """Detalhes do argumento."""
        api_client.force_authenticate(user=user)
        url = reverse('legal_library:legalargument-detail', kwargs={'pk': argument.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Dano Moral - Pessoa Jurídica'

    def test_retrieve_nonexistent(self, api_client, user):
        """Argumento inexistente retorna 404."""
        api_client.force_authenticate(user=user)
        url = reverse('legal_library:legalargument-detail', kwargs={'pk': '00000000-0000-0000-0000-000000000000'})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_argument(self, api_client, user, argument):
        """Atualizar argumento."""
        api_client.force_authenticate(user=user)
        url = reverse('legal_library:legalargument-detail', kwargs={'pk': argument.id})
        response = api_client.patch(url, {'status': 'archived'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'archived'

    def test_delete_argument(self, api_client, user, argument):
        """Deletar argumento."""
        api_client.force_authenticate(user=user)
        url = reverse('legal_library:legalargument-detail', kwargs={'pk': argument.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not LegalArgument.objects.filter(id=argument.id).exists()


# =====================================================
# TESTES DE USO E EFICÁCIA
# =====================================================
@pytest.mark.django_db
class TestArgumentUsageMetrics:
    """Testes de registro de uso e métricas de eficácia."""

    def test_increment_usage(self, argument):
        """Incrementar contador de uso."""
        assert argument.usage_count == 0
        argument.increment_usage()
        argument.refresh_from_db()
        assert argument.usage_count == 1
        assert argument.last_used_at is not None

    def test_record_success(self, argument):
        """Registrar sucesso atualiza score."""
        argument.usage_count = 5
        argument.success_count = 3
        argument.save()
        argument.record_success()
        argument.refresh_from_db()
        assert argument.success_count == 4
        assert argument.effectiveness_score == 0.8  # 4/5

    def test_effectiveness_calculation(self):
        """Eficácia = sucessos / usos."""
        arg = LegalArgument(title='Test', content='X', created_by_id=1)
        arg.usage_count = 10
        arg.success_count = 7
        arg._update_effectiveness()
        assert arg.effectiveness_score == 0.7

    def test_zero_usage_effectiveness(self):
        """Eficácia deve ser 0 quando não houver usos."""
        arg = LegalArgument(title='Test', content='X', created_by_id=1)
        arg._update_effectiveness()
        assert arg.effectiveness_score == 0.0


# =====================================================
# TESTES DE SUGESTÃO
# =====================================================
@pytest.mark.django_db
class TestArgumentSuggestion:
    """Testes de endpoint de sugestão."""

    def test_suggest_arguments(self, api_client, user, argument):
        """Endpoint de sugestão deve retornar argumentos."""
        api_client.force_authenticate(user=user)
        url = reverse('legal_library:suggest-arguments')
        response = api_client.get(url, {'query': 'dano moral', 'specialty': 'CIV'})
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)


# =====================================================
# TESTES DE COLEÇÕES
# =====================================================
@pytest.mark.django_db
class TestArgumentCollection:
    """Testes de coleções de argumentos."""

    def test_create_collection(self, api_client, user):
        """Criar coleção de argumentos."""
        api_client.force_authenticate(user=user)
        url = reverse('legal_library:argumentcollection-list')
        data = {'name': 'Danos Morais', 'description': 'Coleção completa'}
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Danos Morais'

    def test_list_collections(self, api_client, user):
        """Listar coleções."""
        ArgumentCollection.objects.create(name='Coleção Teste', created_by=user)
        api_client.force_authenticate(user=user)
        url = reverse('legal_library:argumentcollection-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert any(c['name'] == 'Coleção Teste' for c in response.data)

    def test_add_argument_to_collection(self, api_client, user, argument):
        """Adicionar argumento à coleção."""
        collection = ArgumentCollection.objects.create(name='Minha Coleção', created_by=user)
        collection.arguments.add(argument)
        assert argument in collection.arguments.all()


# =====================================================
# TESTES DE REGISTRO DE USO
# =====================================================
@pytest.mark.django_db
class TestArgumentUsageRecord:
    """Testes de registro de uso de argumento."""

    def test_register_usage(self, api_client, user, argument):
        """Registrar uso de argumento em documento."""
        api_client.force_authenticate(user=user)
        url = reverse('legal_library:legalargument-use', kwargs={'pk': argument.id})
        data = {'document_id': '12345678-1234-5678-1234-567812345678'}
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_register_success(self, api_client, user, argument):
        """Registrar sucesso de argumento."""
        api_client.force_authenticate(user=user)
        url = reverse('legal_library:legalargument-record-success', kwargs={'pk': argument.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK


# =====================================================
# TESTES DE MODELOS
# =====================================================
@pytest.mark.django_db
class TestLegalLibraryModels:
    """Testes dos modelos da biblioteca jurídica."""

    def test_argument_str(self, argument):
        assert str(argument) == 'Dano Moral - Pessoa Jurídica'

    def test_collection_str(self, user):
        collection = ArgumentCollection.objects.create(name='Test Collection', created_by=user)
        assert str(collection) == 'Test Collection'

    def test_usage_str(self, user, argument):
        usage = ArgumentUsage.objects.create(argument=argument)
        assert argument.title in str(usage)
