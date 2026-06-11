"""
Testes para o app Documents.
Cobre: CRUD de documentos, versionamento, status, permissões.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.documents.models import Document, DocumentVersion
from apps.forms.models import FormTemplate
from apps.templates.models import DocumentTemplate
from apps.core.models import DocumentType

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='doc_user',
        email='doc@test.com',
        password='testpass123',
        role='analyst',
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username='doc_admin',
        email='doc_admin@test.com',
        password='testpass123',
        role='superadmin',
    )


@pytest.fixture
def doc_type(db):
    return DocumentType.objects.create(
        name='ETP',
        slug='etp',
        display_order=1,
    )


@pytest.fixture
def form_template(db, user, doc_type):
    return FormTemplate.objects.create(
        name='Formulário ETP Teste',
        fields=[{"id": "descricao", "type": "textarea", "label": "Descrição"}],
        created_by=user,
    )


@pytest.fixture
def document(db, user, form_template):
    return Document.objects.create(
        user=user,
        form_template=form_template,
        title='Documento Teste',
        description='Descrição teste',
        status='draft',
        data={"descricao": "Conteúdo inicial"},
    )


# =====================================================
# TESTES DE DOCUMENTOS - CRUD
# =====================================================
@pytest.mark.django_db
class TestDocumentCRUD:
    """Testes de CRUD de documentos."""

    def test_list_documents(self, api_client, user, document):
        """Usuário autenticado deve listar documentos."""
        api_client.force_authenticate(user=user)
        url = reverse('documents:document-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1
        assert any(d['title'] == 'Documento Teste' for d in response.data['results'])

    def test_list_documents_unauthenticated(self, api_client):
        """Não autenticado não deve listar."""
        url = reverse('documents:document-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_document(self, api_client, user, form_template):
        """Criar documento com dados válidos."""
        api_client.force_authenticate(user=user)
        url = reverse('documents:document-list')
        data = {
            'title': 'Novo Documento',
            'form_template': str(form_template.id),
            'data': {'descricao': 'Teste'},
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'Novo Documento'
        assert response.data['status'] == 'draft'

    def test_create_document_missing_required(self, api_client, user):
        """Criar sem campos obrigatórios deve falhar."""
        api_client.force_authenticate(user=user)
        url = reverse('documents:document-list')
        response = api_client.post(url, {}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_retrieve_document(self, api_client, user, document):
        """Usuário deve ver detalhes do documento."""
        api_client.force_authenticate(user=user)
        url = reverse('documents:document-detail', kwargs={'pk': document.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Documento Teste'

    def test_retrieve_nonexistent(self, api_client, user):
        """Documento inexistente retorna 404."""
        api_client.force_authenticate(user=user)
        url = reverse('documents:document-detail', kwargs={'pk': '00000000-0000-0000-0000-000000000000'})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_document(self, api_client, user, document):
        """Atualizar documento."""
        api_client.force_authenticate(user=user)
        url = reverse('documents:document-detail', kwargs={'pk': document.id})
        response = api_client.patch(url, {'title': 'Título Atualizado', 'progress': 50}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Título Atualizado'
        assert response.data['progress'] == 50

    def test_delete_document(self, api_client, user, document):
        """Deletar documento."""
        api_client.force_authenticate(user=user)
        url = reverse('documents:document-detail', kwargs={'pk': document.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Document.objects.filter(id=document.id).exists()

    def test_delete_unauthenticated(self, api_client, document):
        """Não autenticado não pode deletar."""
        url = reverse('documents:document-detail', kwargs={'pk': document.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =====================================================
# TESTES DE VERSIONAMENTO
# =====================================================
@pytest.mark.django_db
class TestDocumentVersioning:
    """Testes de versionamento de documentos."""

    def test_create_version(self, api_client, user, document):
        """Criar nova versão de documento."""
        api_client.force_authenticate(user=user)
        url = reverse('documents:document-create-version', kwargs={'pk': document.id})
        response = api_client.post(url, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['version'] == document.version + 1
        assert response.data['status'] == 'draft'

    def test_create_version_with_parent(self, api_client, user, document):
        """Nova versão deve referenciar o documento original como parent."""
        api_client.force_authenticate(user=user)
        url = reverse('documents:document-create-version', kwargs={'pk': document.id})
        response = api_client.post(url, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['parent'] == str(document.id)

    def test_list_versions(self, api_client, user, document):
        """Listar versões de um documento."""
        DocumentVersion.objects.create(
            document=document,
            version_number='1.0.0',
            sections_data=[],
            created_by=user,
        )
        api_client.force_authenticate(user=user)
        url = reverse('documents:document-versions', kwargs={'pk': document.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_document_version_model(self, user, document):
        """Testar modelo DocumentVersion."""
        version = DocumentVersion.objects.create(
            document=document,
            version_number='1.0.0',
            version_type='major',
            sections_data=[{'id': 'sec1', 'title': 'Seção 1', 'content': 'Conteúdo'}],
            change_summary='Primeira versão',
            created_by=user,
        )
        assert version.document == document
        assert version.version_number == '1.0.0'
        assert str(version) == f'{document.title} - v1.0.0'


# =====================================================
# TESTES DE STATUS
# =====================================================
@pytest.mark.django_db
class TestDocumentStatus:
    """Testes de transições de status."""

    def test_document_default_status(self, user, form_template):
        """Documento novo deve ser draft."""
        doc = Document.objects.create(user=user, form_template=form_template, title='Status Test')
        assert doc.status == 'draft'
        assert doc.is_draft is True

    def test_document_completed_status(self, user, form_template):
        """Documento completo."""
        doc = Document.objects.create(
            user=user, form_template=form_template, title='Completo', status='completed'
        )
        assert doc.is_completed is True

    def test_update_status(self, api_client, user, document):
        """Atualizar status do documento."""
        api_client.force_authenticate(user=user)
        url = reverse('documents:document-detail', kwargs={'pk': document.id})
        response = api_client.patch(url, {'status': 'in_review'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'in_review'


# =====================================================
# TESTES DE MODEL DOCUMENT
# =====================================================
@pytest.mark.django_db
class TestDocumentModel:
    """Testes do modelo Document."""

    def test_str_representation(self, document):
        assert str(document) == 'Documento Teste'

    def test_create_version(self, user, document):
        """Método create_version do model."""
        new_doc = document.create_version(user)
        assert new_doc.version == document.version + 1
        assert new_doc.parent == document  # parent aponta para o original
        assert new_doc.status == 'draft'
        assert new_doc.data == document.data


# =====================================================
# TESTES DE PERMISSÕES
# =====================================================
@pytest.mark.django_db
class TestDocumentPermissions:
    """Testes de permissões."""

    def test_unauthenticated_cannot_create(self, api_client):
        """Não autenticado não pode criar documento."""
        url = reverse('documents:document-list')
        response = api_client.post(url, {'title': 'Test'}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_sees_own_documents(self, api_client, user, document, admin_user):
        """Usuário vê apenas seus documentos."""
        # Criar documento de outro usuário
        other_doc = Document.objects.create(
            user=admin_user, form_template=document.form_template, title='Outro Documento'
        )
        api_client.force_authenticate(user=user)
        url = reverse('documents:document-list')
        response = api_client.get(url)
        titles = [d['title'] for d in response.data['results']]
        assert 'Documento Teste' in titles
        assert 'Outro Documento' not in titles
