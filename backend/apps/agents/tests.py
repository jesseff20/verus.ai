"""
Testes para AgentPrompt API
Testa todos os endpoints: CRUD, dashboard, filtros, ordenação, duplicate
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.agents.models import AgentPrompt
from apps.accounts.models import User


@pytest.fixture
def api_client():
    """Cliente API para testes"""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Cria usuário admin para testes"""
    user = User.objects.create_user(
        username='admin_test',
        email='admin@verus.ai',
        password='testpass123',
        role='superadmin'
    )
    return user


@pytest.fixture
def regular_user(db):
    """Cria usuário comum para testes"""
    user = User.objects.create_user(
        username='user_test',
        email='user@verus.ai',
        password='testpass123',
        role='user'
    )
    return user


@pytest.fixture
def sample_agent_form_assistant(db, admin_user):
    """Cria um agente de formulário para testes"""
    return AgentPrompt.objects.create(
        name='Corretor de Texto',
        description='Corrige erros gramaticais',
        category='form_assistant',
        agent_type='corretor',
        field_id='descricao',
        system_prompt='Você é um corretor de textos.',
        user_prompt_template='Corrija o seguinte texto: {{text}}',
        llm_provider='openai',
        model_name='gpt-4o-mini',
        temperature=0.7,
        max_tokens=500,
        icon='edit',
        color='#3b82f6',
        display_order=1,
        is_active=True,
        is_default=True,
        created_by=admin_user
    )


@pytest.fixture
def sample_agent_document_generator(db, admin_user):
    """Cria um gerador de documento para testes"""
    return AgentPrompt.objects.create(
        name='Gerador de ETP',
        description='Gera Estudos Técnicos Preliminares',
        category='document_generator',
        agent_type='etp',
        field_id='etp',
        system_prompt='Você é especialista em Documents.',
        user_prompt_template='Gere ETP: {{content}}',
        llm_provider='openai',
        model_name='gpt-4o-mini',
        temperature=0.3,
        max_tokens=4000,
        icon='file-text',
        color='#1e40af',
        display_order=1,
        is_active=True,
        is_default=False,
        created_by=admin_user
    )


@pytest.fixture
def sample_agent_chat_assistant(db, admin_user):
    """Cria um assistente de chat para testes"""
    return AgentPrompt.objects.create(
        name='Assistente de Chat',
        description='Responde dúvidas sobre licitações',
        category='chat_assistant',
        agent_type='kb_search',
        field_id=None,
        system_prompt='Você é um assistente especializado.',
        user_prompt_template='Responda: {{question}}',
        llm_provider='anthropic',
        model_name='claude-3-5-sonnet-20241022',
        temperature=0.7,
        max_tokens=1000,
        use_rag=True,
        icon='message-square',
        color='#10b981',
        display_order=1,
        is_active=True,
        is_default=True,
        created_by=admin_user
    )


# =====================================================
# TESTES DE LISTAGEM (GET /api/v1/agents/)
# =====================================================

@pytest.mark.django_db
class TestAgentPromptList:
    """Testes de listagem de agentes"""

    def test_list_agents_authenticated(self, api_client, admin_user, sample_agent_form_assistant):
        """Admin autenticado consegue listar agentes"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('agents:agent-list')

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Verificar que temos pelo menos um agente (os 5 da migration + fixture)
        agent_names = [a['name'] for a in response.data['results']]
        assert 'Corretor de Texto' in agent_names
        corretor = [a for a in response.data['results']
                    if a['name'] == 'Corretor de Texto'][0]
        assert corretor['category'] == 'form_assistant'
        assert 'icon' in corretor
        assert 'color' in corretor

    def test_list_agents_unauthenticated(self, api_client):
        """Usuário não autenticado não consegue listar"""
        url = reverse('agents:agent-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_agents_filter_by_category(self, api_client, admin_user,
                                            sample_agent_form_assistant,
                                            sample_agent_document_generator):
        """Filtrar agentes por categoria"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('agents:agent-list')

        # Filtrar form_assistant
        response = api_client.get(url, {'category': 'form_assistant'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
        assert all(a['category'] ==
                   'form_assistant' for a in response.data['results'])

        # Filtrar document_generator
        response = api_client.get(url, {'category': 'document_generator'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
        assert all(a['category'] ==
                   'document_generator' for a in response.data['results'])

    def test_list_agents_filter_by_agent_type(self, api_client, admin_user, sample_agent_form_assistant):
        """Filtrar agentes por agent_type"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('agents:agent-list')

        response = api_client.get(url, {'agent_type': 'corretor'})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['agent_type'] == 'corretor'

    def test_list_agents_filter_active_only(self, api_client, admin_user, sample_agent_form_assistant):
        """Filtrar apenas agentes ativos"""
        # Criar agente inativo
        AgentPrompt.objects.create(
            name='Agente Inativo',
            category='form_assistant',
            agent_type='teste',
            system_prompt='test',
            user_prompt_template='test',
            is_active=False,
            created_by=admin_user
        )

        api_client.force_authenticate(user=admin_user)
        url = reverse('agents:agent-list')

        # Com active_only=true (padrão)
        response = api_client.get(url)
        assert all(agent['is_active'] for agent in response.data['results'])

        # Com active_only=false
        response = api_client.get(url, {'active_only': 'false'})
        assert any(not agent['is_active']
                   for agent in response.data['results'])


# =====================================================
# TESTES DE DETALHES (GET /api/v1/agents/{id}/)
# =====================================================

@pytest.mark.django_db
class TestAgentPromptDetail:
    """Testes de detalhes de agente"""

    def test_retrieve_agent(self, api_client, admin_user, sample_agent_form_assistant):
        """Recuperar detalhes de um agente"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('agents:agent-detail',
                      kwargs={'pk': sample_agent_form_assistant.id})

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Corretor de Texto'
        assert response.data['system_prompt'] == 'Você é um corretor de textos.'
        assert 'extracted_variables' in response.data
        assert 'text' in response.data['extracted_variables']

    def test_retrieve_nonexistent_agent(self, api_client, admin_user):
        """Tentar recuperar agente inexistente"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('agents:agent-detail',
                      kwargs={'pk': '00000000-0000-0000-0000-000000000000'})

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


# =====================================================
# TESTES DE CRIAÇÃO (POST /api/v1/agents/)
# =====================================================

@pytest.mark.django_db
class TestAgentPromptCreate:
    """Testes de criação de agentes"""

    def test_create_agent_as_admin(self, api_client, admin_user):
        """Admin pode criar agente"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('agents:agent-list')

        data = {
            'name': 'Novo Agente',
            'description': 'Descrição teste',
            'category': 'form_assistant',
            'agent_type': 'tradutor',
            'field_id': 'titulo',
            'system_prompt': 'Você é um tradutor.',
            'user_prompt_template': 'Traduza: {{text}}',
            'llm_provider': 'openai',
            'model_name': 'gpt-4o-mini',
            'temperature': 0.5,
            'max_tokens': 800,
            'icon': 'globe',
            'color': '#ef4444',
            'display_order': 10,
            'is_active': True,
            'is_default': False
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Novo Agente'
        assert response.data['category'] == 'form_assistant'
        assert response.data['icon'] == 'globe'
        assert response.data['color'] == '#ef4444'

    def test_create_agent_missing_required_fields(self, api_client, admin_user):
        """Criar agente sem campos obrigatórios deve falhar"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('agents:agent-list')

        data = {
            'name': 'Agente Incompleto',
            # Faltam campos obrigatórios
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# =====================================================
# TESTES DE ATUALIZAÇÃO (PUT/PATCH /api/v1/agents/{id}/)
# =====================================================

@pytest.mark.django_db
class TestAgentPromptUpdate:
    """Testes de atualização de agentes"""

    def test_update_agent(self, api_client, admin_user, sample_agent_form_assistant):
        """Admin pode atualizar agente"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('agents:agent-detail',
                      kwargs={'pk': sample_agent_form_assistant.id})

        data = {
            'name': 'Corretor Atualizado',
            'description': 'Nova descrição',
            'category': 'form_assistant',
            'agent_type': 'corretor',
            'system_prompt': 'Prompt atualizado',
            'user_prompt_template': 'Template atualizado: {{text}}',
            'llm_provider': 'anthropic',
            'model_name': 'claude-3-5-sonnet-20241022',
            'temperature': 0.8,
            'max_tokens': 1000,
            'icon': 'edit-2',
            'color': '#8b5cf6',
            'display_order': 5,
            'is_active': False,
            'is_default': False
        }

        response = api_client.put(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Corretor Atualizado'
        assert response.data['llm_provider'] == 'anthropic'
        assert response.data['is_active'] == False

    def test_partial_update_agent(self, api_client, admin_user, sample_agent_form_assistant):
        """Admin pode fazer atualização parcial"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('agents:agent-detail',
                      kwargs={'pk': sample_agent_form_assistant.id})

        data = {
            'temperature': 0.9,
            'color': '#f59e0b'
        }

        response = api_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['temperature'] == 0.9
        assert response.data['color'] == '#f59e0b'
        # Mantém valor original
        assert response.data['name'] == 'Corretor de Texto'


# =====================================================
# TESTES DE DELEÇÃO (DELETE /api/v1/agents/{id}/)
# =====================================================

@pytest.mark.django_db
class TestAgentPromptDelete:
    """Testes de deleção de agentes"""

    def test_delete_agent(self, api_client, admin_user, sample_agent_form_assistant):
        """Admin pode deletar agente"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('agents:agent-detail',
                      kwargs={'pk': sample_agent_form_assistant.id})

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not AgentPrompt.objects.filter(
            id=sample_agent_form_assistant.id).exists()


# =====================================================
# TESTES DE ENDPOINTS DE DASHBOARD
# =====================================================

@pytest.mark.django_db
class TestAgentPromptDashboard:
    """Testes de endpoints do dashboard"""

    def test_by_category_endpoint(self, api_client, admin_user,
                                  sample_agent_form_assistant,
                                  sample_agent_document_generator,
                                  sample_agent_chat_assistant):
        """Endpoint by_category agrupa corretamente"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('agents:agent-by-category')

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'form_assistant' in response.data
        assert 'document_generator' in response.data
        assert 'chat_assistant' in response.data

        # Verificar estrutura
        assert response.data['form_assistant']['count'] >= 1
        assert len(response.data['form_assistant']['agents']) >= 1
        assert response.data['document_generator']['count'] >= 1
        assert response.data['chat_assistant']['count'] >= 0

    def test_stats_endpoint(self, api_client, admin_user,
                            sample_agent_form_assistant,
                            sample_agent_document_generator):
        """Endpoint stats retorna estatísticas corretas"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('agents:agent-stats')

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total'] >= 2
        assert response.data['active'] >= 2
        assert 'by_category' in response.data
        assert 'by_provider' in response.data
        assert response.data['by_category']['form_assistant']['count'] >= 1
        assert response.data['by_provider']['openai']['count'] >= 2

    def test_form_assistants_endpoint(self, api_client, admin_user,
                                      sample_agent_form_assistant,
                                      sample_agent_document_generator):
        """Endpoint form_assistants retorna apenas form_assistants"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('agents:agent-form-assistants')

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert all(agent['category'] ==
                   'form_assistant' for agent in response.data)

    def test_chat_assistants_endpoint(self, api_client, admin_user, sample_agent_chat_assistant):
        """Endpoint chat_assistants retorna apenas chat_assistants"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('agents:agent-chat-assistants')

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert all(agent['category'] ==
                   'chat_assistant' for agent in response.data)

    def test_document_generators_endpoint(self, api_client, admin_user, sample_agent_document_generator):
        """Endpoint document_generators retorna apenas document_generators"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('agents:agent-document-generators')

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert all(agent['category'] ==
                   'document_generator' for agent in response.data)


# =====================================================
# TESTES DE DUPLICAÇÃO
# =====================================================

@pytest.mark.django_db
class TestAgentPromptDuplicate:
    """Testes de duplicação de agentes"""

    def test_duplicate_agent(self, api_client, admin_user, sample_agent_form_assistant):
        """Admin pode duplicar agente"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('agents:agent-duplicate',
                      kwargs={'pk': sample_agent_form_assistant.id})

        response = api_client.post(url)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Corretor de Texto (cópia)'
        assert response.data['is_active'] == False
        assert response.data['is_default'] == False
        assert response.data['display_order'] == sample_agent_form_assistant.display_order + 1

        # Verificar que original não foi alterado
        original = AgentPrompt.objects.get(id=sample_agent_form_assistant.id)
        assert original.name == 'Corretor de Texto'
        assert original.is_active == True


# =====================================================
# TESTES DE ORDENAÇÃO
# =====================================================

@pytest.mark.django_db
class TestAgentPromptOrdering:
    """Testes de ordenação de agentes"""

    def test_default_ordering(self, api_client, admin_user):
        """Ordenação padrão: category > display_order > is_default > name"""
        # Criar agentes em ordem específica
        AgentPrompt.objects.create(
            name='Z Agent',
            category='form_assistant',
            agent_type='test',
            display_order=2,
            system_prompt='test',
            user_prompt_template='test',
            created_by=admin_user
        )
        AgentPrompt.objects.create(
            name='A Agent',
            category='form_assistant',
            agent_type='test',
            display_order=1,
            system_prompt='test',
            user_prompt_template='test',
            created_by=admin_user
        )

        api_client.force_authenticate(user=admin_user)
        url = reverse('agents:agent-list')

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Primeiro deve vir o com display_order=1
        assert response.data['results'][0]['display_order'] == 1

    def test_ordering_by_name(self, api_client, admin_user):
        """Ordenação por nome"""
        AgentPrompt.objects.create(
            name='Zebra',
            category='form_assistant',
            agent_type='test',
            system_prompt='test',
            user_prompt_template='test',
            created_by=admin_user
        )
        AgentPrompt.objects.create(
            name='Alpha',
            category='form_assistant',
            agent_type='test',
            system_prompt='test',
            user_prompt_template='test',
            created_by=admin_user
        )

        api_client.force_authenticate(user=admin_user)
        url = reverse('agents:agent-list')

        response = api_client.get(url, {'ordering': 'name'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'][0]['name'] == 'Alpha'


# =====================================================
# TESTES DE VARIÁVEIS NO TEMPLATE
# =====================================================

@pytest.mark.django_db
class TestAgentPromptVariables:
    """Testes de extração de variáveis do template"""

    def test_extract_variables(self, sample_agent_form_assistant):
        """Extrai variáveis do user_prompt_template"""
        variables = sample_agent_form_assistant.extract_variables()

        assert 'text' in variables
        assert len(variables) == 1

    def test_variable_count_property(self, sample_agent_form_assistant):
        """Propriedade variable_count retorna contagem correta"""
        assert sample_agent_form_assistant.variable_count == 1

    def test_extract_multiple_variables(self, db, admin_user):
        """Extrai múltiplas variáveis"""
        agent = AgentPrompt.objects.create(
            name='Multi Vars',
            category='form_assistant',
            agent_type='test',
            system_prompt='test',
            user_prompt_template='Vars: {{var1}}, {{var2}}, {{var3}}',
            created_by=admin_user
        )

        variables = agent.extract_variables()

        assert len(variables) == 3
        assert 'var1' in variables
        assert 'var2' in variables
        assert 'var3' in variables
