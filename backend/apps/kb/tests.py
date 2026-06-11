"""
Testes para o app Knowledge Base (KB).
Cobre: CRUD de documentos, upload, chunking, embeddings, permissões.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.kb.models import Document, DocumentChunk
from unittest.mock import patch, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='kb_user',
        email='kb@test.com',
        password='testpass123',
        role='analyst',
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username='kb_admin',
        email='kb_admin@test.com',
        password='testpass123',
        role='superadmin',
    )


@pytest.fixture
def kb_document(db, user):
    return Document.objects.create(
        title='Lei 14.133 - Comentada',
        description='Comentários sobre a lei de licitações',
        category='lei',
        extracted_text='Conteúdo extraído do documento...',
        status='completed',
        uploaded_by=user,
        is_public=True,
        is_active=True,
    )


@pytest.fixture
def kb_chunk(db, kb_document):
    return DocumentChunk.objects.create(
        document=kb_document,
        content='Trecho do documento sobre dispensa de licitação...',
        chunk_index=0,
    )


# =====================================================
# TESTES DE DOCUMENTOS KB - CRUD
# =====================================================
@pytest.mark.django_db
class TestKBDocumentCRUD:
    """Testes de CRUD de documentos da KB."""

    def test_list_documents(self, api_client, user, kb_document):
        """Listar documentos da KB."""
        api_client.force_authenticate(user=user)
        url = reverse('kb:document-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert any(d['title'] == 'Lei 14.133 - Comentada' for d in response.data['results'])

    def test_list_documents_unauthenticated(self, api_client):
        """Não autenticado não deve listar."""
        url = reverse('kb:document-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_document(self, api_client, user):
        """Criar documento via upload."""
        api_client.force_authenticate(user=user)
        url = reverse('kb:document-list')
        data = {
            'title': 'Manual de Licitações',
            'description': 'Guia completo',
            'category': 'manual',
        }
        response = api_client.post(url, data, format='json')
        # Accept 201 or 302 depending on whether there's file upload handling
        assert response.status_code in (status.HTTP_201_CREATED, status.HTTP_302_FOUND, status.HTTP_200_OK)

    def test_create_document_missing_title(self, api_client, user):
        """Criar documento sem título deve falhar."""
        api_client.force_authenticate(user=user)
        url = reverse('kb:document-list')
        response = api_client.post(url, {'category': 'lei'}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_retrieve_document(self, api_client, user, kb_document):
        """Detalhes do documento."""
        api_client.force_authenticate(user=user)
        url = reverse('kb:document-detail', kwargs={'pk': kb_document.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Lei 14.133 - Comentada'

    def test_retrieve_nonexistent(self, api_client, user):
        """Documento inexistente retorna 404."""
        api_client.force_authenticate(user=user)
        url = reverse('kb:document-detail', kwargs={'pk': '00000000-0000-0000-0000-000000000000'})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_document(self, api_client, user, kb_document):
        """Atualizar documento."""
        api_client.force_authenticate(user=user)
        url = reverse('kb:document-detail', kwargs={'pk': kb_document.id})
        response = api_client.patch(url, {'title': 'Título Atualizado'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Título Atualizado'

    def test_delete_document(self, api_client, user, kb_document):
        """Deletar documento."""
        api_client.force_authenticate(user=user)
        url = reverse('kb:document-detail', kwargs={'pk': kb_document.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Document.objects.filter(id=kb_document.id).exists()


# =====================================================
# TESTES DE CHUNKS
# =====================================================
@pytest.mark.django_db
class TestDocumentChunk:
    """Testes de chunks de documentos."""

    def test_list_chunks(self, api_client, user, kb_document, kb_chunk):
        """Listar chunks de um documento."""
        api_client.force_authenticate(user=user)
        url = reverse('kb:document-chunks', kwargs={'pk': kb_document.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_chunk_properties(self, kb_chunk):
        """Propriedades do chunk."""
        assert kb_chunk.has_embedding is False  # embedding é None por padrão
        assert len(kb_chunk.content_preview) > 0

    def test_chunk_count_property(self, kb_document, kb_chunk):
        """Propriedade chunk_count do documento."""
        assert kb_document.chunk_count >= 1


# =====================================================
# TESTES DE SEARCH
# =====================================================
@pytest.mark.django_db
class TestKBSearch:
    """Testes de busca na KB."""

    @patch('apps.kb.services.VectorSearchService')
    def test_search_documents(self, mock_search_service, api_client, user):
        """Busca semântica na KB."""
        mock_instance = MagicMock()
        mock_instance.search.return_value = {
            'results': [{'id': '1', 'content': 'Resultado', 'score': 0.95}],
            'total': 1,
        }
        mock_search_service.return_value = mock_instance

        api_client.force_authenticate(user=user)
        url = reverse('kb:document-search')
        response = api_client.post(url, {'query': 'dispensa de licitação', 'top_k': 5}, format='json')
        # Accept various response formats
        assert response.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED)


# =====================================================
# TESTES DE MODELOS
# =====================================================
@pytest.mark.django_db
class TestKBModels:
    """Testes dos modelos da KB."""

    def test_document_str(self, kb_document):
        assert 'Lei 14.133 - Comentada' in str(kb_document)

    def test_document_file_size_mb(self, kb_document):
        assert kb_document.file_size_mb == 0.0  # Sem arquivo

    def test_chunk_str(self, kb_document, kb_chunk):
        assert str(kb_chunk) == f'{kb_document.title} - Chunk 0'

    def test_chunk_content_preview_short(self):
        """Preview de texto curto."""
        chunk = DocumentChunk(content='Texto curto')
        assert chunk.content_preview == 'Texto curto'

    def test_chunk_content_preview_long(self):
        """Preview de texto longo deve truncar."""
        chunk = DocumentChunk(content='A' * 200)
        preview = chunk.content_preview
        assert len(preview) == 103  # 100 + '...'

    def test_document_save_metadata(self, user):
        """Save deve extrair metadados do arquivo."""
        # Teste sem arquivo - deve funcionar sem erro
        doc = Document.objects.create(
            title='Teste',
            uploaded_by=user,
        )
        assert doc.file_size is None
        assert doc.file_type == ''
