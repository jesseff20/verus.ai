"""
Testes para o app Templates.
Cobre: CRUD de templates de documento, vinculação com blueprints, validação.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.templates.models import DocumentTemplate
from apps.forms.models import FormTemplate
from apps.core.models import DocumentType

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='tmpl_user',
        email='tmpl@verus.ai',
        password='testpass123',
        role='analyst',
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username='tmpl_admin',
        email='tmpl_admin@verus.ai',
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
def form_template(db, admin_user, doc_type):
    return FormTemplate.objects.create(
        name='Form ETP',
        fields=[{'id': 'descricao', 'type': 'textarea', 'label': 'Descrição'}],
        created_by=admin_user,
    )


@pytest.fixture
def document_template(db, admin_user, doc_type):
    return DocumentTemplate.objects.create(
        name='Template ETP Básico',
        description='Template HTML para ETP',
        template_type='html',
        content='<h1>{{titulo}}</h1><p>{{descricao}}</p>',
        created_by=admin_user,
        is_active=True,
    )


# =====================================================
# TESTES DE DOCUMENT TEMPLATE - CRUD
# =====================================================
@pytest.mark.django_db
class TestDocumentTemplateCRUD:
    """Testes de CRUD de templates de documento."""

    def test_list_templates(self, api_client, admin_user, document_template):
        """Listar templates."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('templates:documenttemplate-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert any(t['name'] == 'Template ETP Básico' for t in response.data['results'])

    def test_list_templates_unauthenticated(self, api_client):
        """Não autenticado não deve listar."""
        url = reverse('templates:documenttemplate-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_template(self, api_client, admin_user):
        """Criar template de documento."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('templates:documenttemplate-list')
        data = {
            'name': 'Template TR',
            'description': 'Template para Termo de Referência',
            'template_type': 'html',
            'content': '<html><body>{{conteudo}}</body></html>',
            'is_active': True,
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Template TR'

    def test_create_template_missing_content_and_file(self, api_client, admin_user):
        """Template sem conteúdo e sem arquivo deve falhar."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('templates:documenttemplate-list')
        data = {'name': 'Vazio', 'template_type': 'html'}
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_template_as_analyst_forbidden(self, api_client, user):
        """Analyst não pode criar template."""
        api_client.force_authenticate(user=user)
        url = reverse('templates:documenttemplate-list')
        data = {'name': 'Test', 'template_type': 'html', 'content': '<p>test</p>'}
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_template(self, api_client, admin_user, document_template):
        """Detalhes do template."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('templates:documenttemplate-detail', kwargs={'pk': document_template.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Template ETP Básico'

    def test_retrieve_nonexistent(self, api_client, admin_user):
        """Template inexistente retorna 404."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('templates:documenttemplate-detail', kwargs={'pk': '00000000-0000-0000-0000-000000000000'})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_template(self, api_client, admin_user, document_template):
        """Atualizar template."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('templates:documenttemplate-detail', kwargs={'pk': document_template.id})
        response = api_client.patch(url, {'description': 'Nova descrição'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['description'] == 'Nova descrição'

    def test_delete_template(self, api_client, admin_user, document_template):
        """Deletar template."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('templates:documenttemplate-detail', kwargs={'pk': document_template.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not DocumentTemplate.objects.filter(id=document_template.id).exists()


# =====================================================
# TESTES DE VINCULAÇÃO COM BLUEPRINT
# =====================================================
@pytest.mark.django_db
class TestTemplateBlueprintLink:
    """Testes de vinculação com blueprints."""

    def test_template_with_form_template(self, api_client, admin_user, document_template, form_template):
        """Vincular template com formulário."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('templates:documenttemplate-detail', kwargs={'pk': document_template.id})
        response = api_client.patch(url, {'form_template': str(form_template.id)}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['form_template'] == str(form_template.id)


# =====================================================
# TESTES DE DUPLICAÇÃO
# =====================================================
@pytest.mark.django_db
class TestTemplateDuplicate:
    """Testes de duplicação de templates."""

    def test_duplicate_template(self, api_client, admin_user, document_template):
        """Duplicar template incrementa versão e não é padrão."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('templates:documenttemplate-duplicate', kwargs={'pk': document_template.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['version'] == document_template.version + 1
        assert response.data['is_default'] is False


# =====================================================
# TESTES DE PLACEHOLDERS
# =====================================================
@pytest.mark.django_db
class TestTemplatePlaceholders:
    """Testes de extração de placeholders."""

    def test_extract_placeholders(self, document_template):
        """Extrair placeholders do conteúdo."""
        placeholders = document_template.extract_placeholders()
        assert 'titulo' in placeholders
        assert 'descricao' in placeholders
        assert document_template.placeholder_count == 2

    def test_no_placeholders(self, admin_user):
        """Template sem placeholders."""
        tmpl = DocumentTemplate.objects.create(
            name='Sem Placeholders',
            template_type='html',
            content='<p>Texto fixo sem variáveis</p>',
            created_by=admin_user,
        )
        assert tmpl.placeholder_count == 0


# =====================================================
# TESTES DE MODEL
# =====================================================
@pytest.mark.django_db
class TestDocumentTemplateModel:
    """Testes do modelo DocumentTemplate."""

    def test_str_representation(self, document_template):
        assert 'Template ETP Básico' in str(document_template)
        assert 'HTML' in str(document_template)

    def test_get_template_content(self, document_template):
        """get_template_content retorna conteúdo."""
        assert '<h1>{{titulo}}</h1>' in document_template.get_template_content()

    def test_has_file_property(self, document_template):
        """has_file property."""
        assert document_template.has_file is False

    def test_duplicate_method(self, admin_user, document_template):
        """Método duplicate cria cópia."""
        new_tmpl = document_template.duplicate(admin_user)
        assert new_tmpl.version == document_template.version + 1
        assert new_tmpl.is_default is False
        assert new_tmpl.content == document_template.content
