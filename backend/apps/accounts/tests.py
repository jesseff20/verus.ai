"""
Testes para o app Accounts (Autenticação e Usuários).
Cobre: CRUD de usuários, autenticação, roles, permissões, casos de erro.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.accounts.models import BrandSettings

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username='admin_test',
        email='admin@verus.ai',
        password='testpass123',
        first_name='Admin',
        last_name='Test',
        role='superadmin',
        is_superuser=True,
    )


@pytest.fixture
def manager_user(db):
    return User.objects.create_user(
        username='manager_test',
        email='manager@verus.ai',
        password='testpass123',
        first_name='Manager',
        last_name='Test',
        role='manager',
    )


@pytest.fixture
def analyst_user(db):
    return User.objects.create_user(
        username='analyst_test',
        email='analyst@verus.ai',
        password='testpass123',
        first_name='Analyst',
        last_name='Test',
        role='analyst',
    )


@pytest.fixture
def reviewer_user(db):
    return User.objects.create_user(
        username='reviewer_test',
        email='reviewer@verus.ai',
        password='testpass123',
        role='reviewer',
    )


@pytest.fixture
def viewer_user(db):
    return User.objects.create_user(
        username='viewer_test',
        email='viewer@verus.ai',
        password='testpass123',
        role='viewer',
    )


# =====================================================
# TESTES DE REGISTRO (POST /api/v1/auth/register/)
# =====================================================
@pytest.mark.django_db
class TestAuthRegister:
    """Testes de registro de usuário."""

    def test_register_success(self, api_client):
        """Registro bem-sucedido deve retornar 201 com tokens."""
        url = reverse('accounts:auth-register')
        data = {
            'username': 'novousuario',
            'email': 'novo@verus.ai',
            'password': 'SenhaForte123!',
            'password_confirm': 'SenhaForte123!',
            'first_name': 'Novo',
            'last_name': 'Usuário',
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert 'tokens' in response.data
        assert response.data['user']['username'] == 'novousuario'
        assert response.data['user']['role'] == 'analyst'  # default role

    def test_register_password_mismatch(self, api_client):
        """Senhas diferentes devem retornar 400."""
        url = reverse('accounts:auth-register')
        data = {
            'username': 'test_fail',
            'email': 'fail@verus.ai',
            'password': 'Senha123!',
            'password_confirm': 'SenhaDiferente!',
            'first_name': 'Fail',
            'last_name': 'User',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_missing_fields(self, api_client):
        """Campos obrigatórios ausentes devem retornar 400."""
        url = reverse('accounts:auth-register')
        response = api_client.post(url, {'username': 'incompleto'}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# =====================================================
# TESTES DE LOGIN (POST /api/v1/auth/login/)
# =====================================================
@pytest.mark.django_db
class TestAuthLogin:
    """Testes de login."""

    def test_login_success(self, api_client, analyst_user):
        """Login com credenciais corretas deve retornar 200 com tokens."""
        url = reverse('accounts:auth-login')
        data = {'username': 'analyst_test', 'password': 'testpass123'}
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'user' in response.data
        assert 'tokens' in response.data
        assert 'access' in response.data['tokens']
        assert 'refresh' in response.data['tokens']
        assert 'available_modules' in response.data

    def test_login_invalid_credentials(self, api_client):
        """Credenciais inválidas devem retornar 400."""
        url = reverse('accounts:auth-login')
        data = {'username': 'nao_existe', 'password': 'senha_errada'}
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_inactive_user(self, api_client, analyst_user):
        """Usuário inativo não deve conseguir logar."""
        analyst_user.is_active = False
        analyst_user.save()

        url = reverse('accounts:auth-login')
        data = {'username': 'analyst_test', 'password': 'testpass123'}
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_missing_fields(self, api_client):
        """Campos ausentes devem retornar 400."""
        url = reverse('accounts:auth-login')
        response = api_client.post(url, {'username': 'test'}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# =====================================================
# TESTES DE LOGOUT (POST /api/v1/auth/logout/)
# =====================================================
@pytest.mark.django_db
class TestAuthLogout:
    """Testes de logout."""

    def test_logout_success(self, api_client, analyst_user):
        """Logout com refresh token válido deve retornar 200."""
        api_client.force_authenticate(user=analyst_user)
        url = reverse('accounts:auth-logout')
        response = api_client.post(url, {'refresh': 'fake-refresh-token'}, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_logout_unauthenticated(self, api_client):
        """Logout sem autenticação deve retornar 401."""
        url = reverse('accounts:auth-logout')
        response = api_client.post(url, {'refresh': 'token'}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =====================================================
# TESTES DE USUÁRIOS - CRUD
# =====================================================
@pytest.mark.django_db
class TestUserCRUD:
    """Testes de CRUD de usuários."""

    def test_list_users_as_admin(self, api_client, admin_user, analyst_user):
        """Admin deve ver todos os usuários."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('accounts:user-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 2

    def test_list_users_as_analyst(self, api_client, analyst_user, admin_user):
        """Analyst deve ver apenas a si mesmo."""
        api_client.force_authenticate(user=analyst_user)
        url = reverse('accounts:user-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        for user_data in response.data['results']:
            assert user_data['id'] == str(analyst_user.id)

    def test_list_users_unauthenticated(self, api_client):
        """Não autenticado não deve listar usuários."""
        url = reverse('accounts:user-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_user_as_admin(self, api_client, admin_user):
        """Admin deve criar usuário com sucesso."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('accounts:user-list')
        data = {
            'username': 'newuser',
            'email': 'new@verus.ai',
            'password': 'SenhaForte123!',
            'password_confirm': 'SenhaForte123!',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'analyst',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['username'] == 'newuser'

    def test_create_user_as_analyst_forbidden(self, api_client, analyst_user):
        """Analyst não deve criar usuário."""
        api_client.force_authenticate(user=analyst_user)
        url = reverse('accounts:user-list')
        data = {
            'username': 'shouldfail',
            'email': 'fail@verus.ai',
            'password': 'Senha123!',
            'password_confirm': 'Senha123!',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_user(self, api_client, analyst_user):
        """Usuário pode ver seu próprio perfil."""
        api_client.force_authenticate(user=analyst_user)
        url = reverse('accounts:user-detail', kwargs={'pk': analyst_user.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'analyst_test'

    def test_retrieve_other_user_as_admin(self, api_client, admin_user, analyst_user):
        """Admin pode ver perfil de outro usuário."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('accounts:user-detail', kwargs={'pk': analyst_user.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'analyst_test'

    def test_retrieve_nonexistent_user(self, api_client, admin_user):
        """Usuário inexistente deve retornar 404."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('accounts:user-detail', kwargs={'pk': '00000000-0000-0000-0000-000000000000'})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_user(self, api_client, analyst_user):
        """Usuário pode atualizar seu próprio perfil."""
        api_client.force_authenticate(user=analyst_user)
        url = reverse('accounts:user-detail', kwargs={'pk': analyst_user.id})
        data = {'first_name': 'Updated', 'phone': '11999999999'}
        response = api_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'Updated'

    def test_delete_user_as_admin(self, api_client, admin_user, analyst_user):
        """Admin pode desativar (soft-delete) outro usuário."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('accounts:user-detail', kwargs={'pk': analyst_user.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['detail'] == 'Usuário desativado com sucesso.'

    def test_delete_self_not_allowed(self, api_client, admin_user):
        """Usuário não pode desativar a si mesmo."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('accounts:user-detail', kwargs={'pk': admin_user.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_unauthenticated(self, api_client, analyst_user):
        """Não autenticado não pode deletar."""
        url = reverse('accounts:user-detail', kwargs={'pk': analyst_user.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =====================================================
# TESTES DE MEU PERFIL
# =====================================================
@pytest.mark.django_db
class TestUserMe:
    """Testes do endpoint /me."""

    def test_me_authenticated(self, api_client, analyst_user):
        """Usuário autenticado deve ver seus dados."""
        api_client.force_authenticate(user=analyst_user)
        url = reverse('accounts:user-me')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'analyst_test'

    def test_me_unauthenticated(self, api_client):
        """Usuário não autenticado não deve ver perfil."""
        url = reverse('accounts:user-me')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_my_permissions(self, api_client, admin_user):
        """Endpoint de permissões do usuário."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('accounts:user-my-permissions')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['role'] == 'superadmin'
        assert 'permissions' in response.data

    def test_roles_endpoint(self, api_client, admin_user):
        """Endpoint de listagem de roles."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('accounts:user-roles')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)


# =====================================================
# TESTES DE CHANGE PASSWORD
# =====================================================
@pytest.mark.django_db
class TestChangePassword:
    """Testes de troca de senha."""

    def test_change_password_success(self, api_client, analyst_user):
        """Troca de senha com dados corretos."""
        api_client.force_authenticate(user=analyst_user)
        url = reverse('accounts:user-change-password')
        data = {
            'old_password': 'testpass123',
            'new_password': 'NovaSenha123!',
            'new_password_confirm': 'NovaSenha123!',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_change_password_wrong_old(self, api_client, analyst_user):
        """Senha antiga incorreta deve retornar 400."""
        api_client.force_authenticate(user=analyst_user)
        url = reverse('accounts:user-change-password')
        data = {
            'old_password': 'senha_errada',
            'new_password': 'NovaSenha123!',
            'new_password_confirm': 'NovaSenha123!',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_mismatch(self, api_client, analyst_user):
        """Confirmação diferente deve retornar 400."""
        api_client.force_authenticate(user=analyst_user)
        url = reverse('accounts:user-change-password')
        data = {
            'old_password': 'testpass123',
            'new_password': 'NovaSenha123!',
            'new_password_confirm': 'OutraSenha!',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# =====================================================
# TESTES DE ATIVAÇÃO/DESATIVAÇÃO
# =====================================================
@pytest.mark.django_db
class TestUserActivation:
    """Testes de ativar/desativar usuários."""

    def test_deactivate_user(self, api_client, admin_user, analyst_user):
        """Admin pode desativar usuário."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('accounts:user-deactivate', kwargs={'pk': analyst_user.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK

    def test_deactivate_as_analyst_forbidden(self, api_client, analyst_user, reviewer_user):
        """Analyst não pode desativar usuário."""
        api_client.force_authenticate(user=analyst_user)
        url = reverse('accounts:user-deactivate', kwargs={'pk': reviewer_user.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_activate_user(self, api_client, admin_user, analyst_user):
        """Admin pode ativar usuário."""
        analyst_user.is_active = False
        analyst_user.save()

        api_client.force_authenticate(user=admin_user)
        url = reverse('accounts:user-activate', kwargs={'pk': analyst_user.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK


# =====================================================
# TESTES DE BRAND SETTINGS
# =====================================================
@pytest.mark.django_db
class TestBrandSettings:
    """Testes de configurações de marca."""

    def test_get_brand_settings_public(self, api_client):
        """Qualquer um (inclusive não autenticado) pode ver brand settings."""
        url = reverse('accounts:brand-settings-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_update_brand_settings_as_admin(self, api_client, admin_user):
        """Admin pode atualizar brand settings."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('accounts:brand-settings-list')
        data = {'system_name': 'Novo Sistema', 'primary_color': '#ff0000'}
        response = api_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['system_name'] == 'Novo Sistema'

    def test_update_brand_settings_as_analyst_forbidden(self, api_client, analyst_user):
        """Analyst não pode atualizar brand settings."""
        api_client.force_authenticate(user=analyst_user)
        url = reverse('accounts:brand-settings-list')
        data = {'system_name': 'Hacked'}
        response = api_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_reset_brand_settings(self, api_client, admin_user):
        """Admin pode resetar brand settings."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('accounts:brand-settings-reset')
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['system_name'] == 'Verus.AI'
        assert response.data['primary_color'] == '#7030A0'

    def test_delete_not_allowed(self, api_client, admin_user):
        """DELETE não é permitido para brand settings."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('accounts:brand-settings-list')
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# =====================================================
# TESTES DE PERMISSÕES E ROLES
# =====================================================
@pytest.mark.django_db
class TestPermissionsMatrix:
    """Testes de matriz de permissões."""

    def test_permissions_matrix_as_admin(self, api_client, admin_user):
        """Admin pode ver matriz de permissões."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('accounts:user-permissions-matrix')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, dict)

    def test_permissions_matrix_as_analyst_forbidden(self, api_client, analyst_user):
        """Analyst não pode ver matriz de permissões."""
        api_client.force_authenticate(user=analyst_user)
        url = reverse('accounts:user-permissions-matrix')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


# =====================================================
# TESTES DE PROPRIEDADES DO MODEL USER
# =====================================================
@pytest.mark.django_db
class TestUserModelProperties:
    """Testes das propriedades do modelo User."""

    def test_is_superadmin(self, admin_user):
        assert admin_user.is_superadmin is True

    def test_is_manager(self, manager_user):
        assert manager_user.is_manager is True

    def test_is_reviewer(self, reviewer_user):
        assert reviewer_user.is_reviewer is True

    def test_is_viewer(self, viewer_user):
        assert viewer_user.is_viewer is True

    def test_can_manage_templates_admin(self, admin_user):
        assert admin_user.can_manage_templates is True

    def test_can_manage_templates_viewer(self, viewer_user):
        assert viewer_user.can_manage_templates is False

    def test_can_create_document_analyst(self, analyst_user):
        assert analyst_user.can_create_document is True

    def test_can_create_document_viewer(self, viewer_user):
        assert viewer_user.can_create_document is False

    def test_can_approve_document_reviewer(self, reviewer_user):
        assert reviewer_user.can_approve_document is True

    def test_can_approve_document_analyst(self, analyst_user):
        assert analyst_user.can_approve_document is False

    def test_get_full_name(self, analyst_user):
        assert analyst_user.get_full_name() == 'Analyst Test'

    def test_str_representation(self, analyst_user):
        assert str(analyst_user) == 'Analyst Test'


# =====================================================
# TESTES DO MODEL BRAND SETTINGS
# =====================================================
@pytest.mark.django_db
class TestBrandSettingsModel:
    """Testes do modelo BrandSettings."""

    def test_singleton_load(self):
        """load() deve criar ou retornar instância única."""
        instance = BrandSettings.load()
        assert instance.pk == 1
        assert instance.system_name == 'Verus.AI'

    def test_singleton_save_keeps_pk1(self):
        """save() deve sempre manter pk=1."""
        instance = BrandSettings.load()
        instance.pk = 999
        instance.save()
        assert BrandSettings.objects.count() == 1
        assert BrandSettings.objects.first().pk == 1

    def test_delete_is_noop(self):
        """delete() não deve fazer nada (singleton)."""
        instance = BrandSettings.load()
        instance.delete()
        assert BrandSettings.objects.count() == 1
