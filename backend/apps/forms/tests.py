"""
Testes para o app Forms (Formulários Dinâmicos).
Cobre: CRUD de templates de formulário, validação de campos/seções, permissões.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.forms.models import FormTemplate, FormAssistant
from django.core.exceptions import ValidationError

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username='form_admin',
        email='form_admin@test.com',
        password='testpass123',
        role='superadmin',
    )


@pytest.fixture
def analyst_user(db):
    return User.objects.create_user(
        username='form_analyst',
        email='form_analyst@test.com',
        password='testpass123',
        role='analyst',
    )


@pytest.fixture
def form_template(db, admin_user):
    return FormTemplate.objects.create(
        name='ETP Padrão',
        description='Template padrão',
        fields=[
            {'id': 'descricao', 'type': 'textarea', 'label': 'Descrição', 'required': True},
            {'id': 'valor', 'type': 'number', 'label': 'Valor Estimado'},
        ],
        created_by=admin_user,
    )


# =====================================================
# TESTES DE FORM TEMPLATE - CRUD
# =====================================================
@pytest.mark.django_db
class TestFormTemplateCRUD:
    """Testes de CRUD de templates de formulário."""

    def test_list_templates(self, api_client, admin_user, form_template):
        """Listar templates de formulário."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('forms:formtemplate-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert any(t['name'] == 'ETP Padrão' for t in response.data)

    def test_list_templates_unauthenticated(self, api_client):
        """Não autenticado não deve listar."""
        url = reverse('forms:formtemplate-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_template(self, api_client, admin_user):
        """Criar template de formulário com campos flat."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('forms:formtemplate-list')
        data = {
            'name': 'Novo Template',
            'fields': [
                {'id': 'campo1', 'type': 'text', 'label': 'Campo 1', 'required': True},
            ],
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Novo Template'

    def test_create_template_with_sections(self, api_client, admin_user):
        """Criar template com seções."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('forms:formtemplate-list')
        data = {
            'name': 'Template com Seções',
            'sections': [
                {
                    'section_id': 'sec1',
                    'section_title': 'Seção 1',
                    'fields': [
                        {'field_id': 'f1', 'field_type': 'text', 'field_name': 'Nome'},
                    ],
                },
            ],
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Template com Seções'

    def test_create_template_missing_name(self, api_client, admin_user):
        """Criar template sem nome deve falhar."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('forms:formtemplate-list')
        response = api_client.post(url, {'fields': []}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_template_no_fields_no_sections(self, api_client, admin_user):
        """Template sem fields e sections deve falhar."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('forms:formtemplate-list')
        response = api_client.post(url, {'name': 'Vazio'}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_template_as_analyst_forbidden(self, api_client, analyst_user):
        """Analyst não pode criar template."""
        api_client.force_authenticate(user=analyst_user)
        url = reverse('forms:formtemplate-list')
        data = {'name': 'Test', 'fields': [{'id': 'x', 'type': 'text', 'label': 'X'}]}
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_template(self, api_client, admin_user, form_template):
        """Detalhes do template."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('forms:formtemplate-detail', kwargs={'pk': form_template.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'ETP Padrão'

    def test_retrieve_nonexistent(self, api_client, admin_user):
        """Template inexistente retorna 404."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('forms:formtemplate-detail', kwargs={'pk': '00000000-0000-0000-0000-000000000000'})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_template(self, api_client, admin_user, form_template):
        """Atualizar template."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('forms:formtemplate-detail', kwargs={'pk': form_template.id})
        response = api_client.patch(url, {'name': 'ETP Atualizado'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'ETP Atualizado'

    def test_delete_template(self, api_client, admin_user, form_template):
        """Deletar template."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('forms:formtemplate-detail', kwargs={'pk': form_template.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not FormTemplate.objects.filter(id=form_template.id).exists()

    def test_delete_protected(self, api_client, admin_user, form_template, analyst_user):
        """Deletar template com documentos vinculados deve proteger."""
        from apps.documents.models import Document
        Document.objects.create(
            user=analyst_user, form_template=form_template, title='Doc vinculado'
        )
        api_client.force_authenticate(user=admin_user)
        url = reverse('forms:formtemplate-detail', kwargs={'pk': form_template.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# =====================================================
# TESTES DE DUPLICAÇÃO
# =====================================================
@pytest.mark.django_db
class TestFormTemplateDuplicate:
    """Testes de duplicação de templates."""

    def test_duplicate_template(self, api_client, admin_user, form_template):
        """Duplicar template incrementa versão."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('forms:formtemplate-duplicate', kwargs={'pk': form_template.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['version'] == form_template.version + 1


# =====================================================
# TESTES DE VALIDAÇÃO DE CAMPOS
# =====================================================
@pytest.mark.django_db
class TestFormFieldValidation:
    """Testes de validação de campos do formulário."""

    def test_validate_invalid_field_type(self):
        """Tipo de campo inválido deve levantar ValidationError."""
        from django.core.exceptions import ValidationError
        with pytest.raises(ValidationError):
            form = FormTemplate(
                name='Test',
                fields=[{'id': 'x', 'type': 'invalid_type', 'label': 'X'}],
            )
            form.full_clean()

    def test_validate_missing_required_keys(self):
        """Campo sem id deve levantar ValidationError."""
        with pytest.raises(ValidationError):
            form = FormTemplate(
                name='Test',
                fields=[{'type': 'text', 'label': 'No ID'}],
            )
            form.full_clean()

    def test_validate_section_missing_keys(self):
        """Seção sem section_id deve levantar ValidationError."""
        with pytest.raises(ValidationError):
            form = FormTemplate(
                name='Test',
                sections=[{'section_title': 'Sem ID', 'fields': []}],
            )
            form.full_clean()

    def test_field_count_property(self, form_template):
        """Propriedade field_count."""
        assert form_template.field_count == 2

    def test_section_count_property(self):
        """Propriedade section_count."""
        form = FormTemplate(name='Test', sections=[
            {'section_id': 's1', 'section_title': 'S1', 'fields': [{'field_id': 'f1', 'field_type': 'text', 'field_name': 'F1'}]},
        ])
        assert form.section_count == 1

    def test_uses_sections(self):
        """Propriedade uses_sections."""
        flat = FormTemplate(name='Flat', fields=[{'id': 'x', 'type': 'text', 'label': 'X'}])
        assert flat.uses_sections is False
        sectioned = FormTemplate(name='Sec', sections=[
            {'section_id': 's1', 'section_title': 'S1', 'fields': []},
        ])
        assert sectioned.uses_sections is True

    def test_get_field_by_id(self, form_template):
        """Buscar campo por ID."""
        field = form_template.get_field_by_id('descricao')
        assert field is not None
        assert field['label'] == 'Descrição'

    def test_get_field_by_id_not_found(self, form_template):
        """Campo inexistente retorna None."""
        assert form_template.get_field_by_id('nao_existe') is None

    def test_get_all_fields(self, form_template):
        """Retornar todos os campos."""
        fields = form_template.get_all_fields()
        assert len(fields) == 2


# =====================================================
# TESTES DE FORM ASSISTANT
# =====================================================
@pytest.mark.django_db
class TestFormAssistant:
    """Testes do modelo FormAssistant."""

    def test_create_form_assistant(self, db, admin_user):
        """Criar assistente de formulário."""
        assistant = FormAssistant.objects.create(
            name='Corretor Automático',
            assistant_type='corretor',
            system_prompt='Você é um corretor.',
            user_prompt_template='Corrija: {{texto}}',
            llm_provider='openai',
            model_name='gpt-4o-mini',
            created_by=admin_user,
        )
        assert assistant.name == 'Corretor Automático'
        assert assistant.variable_count == 1  # {{texto}}

    def test_form_assistant_variables(self, db, admin_user):
        """Extrair variáveis do template."""
        assistant = FormAssistant.objects.create(
            name='Tradutor',
            assistant_type='tradutor',
            system_prompt='Tradutor.',
            user_prompt_template='Traduza {{texto}} para {{idioma}}',
            created_by=admin_user,
        )
        variables = assistant.extract_variables()
        assert 'texto' in variables
        assert 'idioma' in variables
        assert assistant.variable_count == 2
