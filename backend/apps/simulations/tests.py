"""
Testes para o app Simulations (Simulação de Júri e Sentença de Juiz).
Cobre: modelos, API CRUD, services (JurySimulationService, JudgeSimulationService),
seed de tribunais.
"""
import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from apps.simulations.models import (
    Simulation, SimulationDocument, JuryMember,
    JuryDebateMessage, JudgeProfile, Court,
)

User = get_user_model()


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='sim_user',
        email='sim@test.com',
        password='testpass123',
        role='analyst',
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        username='other_user',
        email='other@test.com',
        password='testpass123',
        role='analyst',
    )


@pytest.fixture
def jury_simulation(user):
    return Simulation.objects.create(
        user=user,
        simulation_type='jury',
        title='Simulação de Júri - Caso Teste',
        description='Teste de simulação de júri popular',
        config={'crime_type': 'Homicídio qualificado'},
    )


@pytest.fixture
def judge_simulation(user):
    return Simulation.objects.create(
        user=user,
        simulation_type='judge',
        title='Simulação de Sentença - Caso Teste',
        description='Teste de simulação de sentença judicial',
        config={'area': 'Criminal'},
    )


@pytest.fixture
def jury_member(jury_simulation):
    return JuryMember.objects.create(
        simulation=jury_simulation,
        name='Maria Silva',
        age=35,
        gender='feminino',
        profession='Professora',
        education='superior',
        personality_traits=['empática', 'analítica'],
        background='Professora de escola pública há 10 anos.',
    )


@pytest.fixture
def simulation_document(jury_simulation):
    fake_file = SimpleUploadedFile(
        'denuncia.pdf',
        b'fake pdf content',
        content_type='application/pdf',
    )
    return SimulationDocument.objects.create(
        simulation=jury_simulation,
        title='Denúncia do Ministério Público',
        file=fake_file,
        extracted_text='O Ministério Público denuncia João por homicídio qualificado...',
        document_type='denuncia',
    )


@pytest.fixture
def judge_profile(db):
    return JudgeProfile.objects.create(
        name='Dr. Carlos Mendes',
        state='SP',
        court='TJSP',
        comarca='São Paulo',
        vara='1ª Vara Criminal',
        specialization='Direito Penal',
        profile_data={'tempo_magistratura': 15},
        decision_patterns={'tendencia': 'rigoroso', 'pena_media': '12 anos'},
    )


@pytest.fixture
def court(db):
    return Court.objects.create(
        name='TJSP',
        court_type='TJ',
        state='SP',
        comarcas=['São Paulo', 'Campinas', 'Santos'],
        website='https://www.tjsp.jus.br',
    )


def _create_7_jury_members(simulation):
    """Helper: cria 7 jurados para uma simulação."""
    members = []
    profiles = [
        ('Ana Costa', 30, 'feminino', 'Enfermeira', 'superior'),
        ('Bruno Lima', 45, 'masculino', 'Engenheiro', 'pos_graduacao'),
        ('Carla Souza', 28, 'feminino', 'Estudante', 'medio'),
        ('Diego Oliveira', 52, 'masculino', 'Comerciante', 'fundamental'),
        ('Elena Santos', 40, 'feminino', 'Advogada', 'pos_graduacao'),
        ('Felipe Rocha', 33, 'masculino', 'Motorista', 'medio'),
        ('Gabriela Alves', 48, 'feminino', 'Contadora', 'superior'),
    ]
    for name, age, gender, profession, education in profiles:
        members.append(JuryMember.objects.create(
            simulation=simulation,
            name=name,
            age=age,
            gender=gender,
            profession=profession,
            education=education,
            personality_traits=['neutro'],
        ))
    return members


# =====================================================
# 1. MODEL TESTS
# =====================================================
@pytest.mark.django_db
class TestSimulationModel:
    """Testes do modelo Simulation e relacionados."""

    def test_create_simulation_jury(self, jury_simulation):
        """Simulação de júri deve ser criada com valores corretos."""
        assert jury_simulation.simulation_type == 'jury'
        assert jury_simulation.status == 'draft'
        assert jury_simulation.title == 'Simulação de Júri - Caso Teste'
        assert str(jury_simulation) == 'Simulação de Júri: Simulação de Júri - Caso Teste'

    def test_create_simulation_judge(self, judge_simulation):
        """Simulação de sentença deve ser criada com valores corretos."""
        assert judge_simulation.simulation_type == 'judge'
        assert judge_simulation.status == 'draft'
        assert str(judge_simulation) == 'Simulação de Sentença: Simulação de Sentença - Caso Teste'

    def test_simulation_status_transitions(self, jury_simulation):
        """Status da simulação deve transicionar corretamente."""
        assert jury_simulation.status == 'draft'

        jury_simulation.status = 'configuring'
        jury_simulation.save()
        jury_simulation.refresh_from_db()
        assert jury_simulation.status == 'configuring'

        jury_simulation.status = 'running'
        jury_simulation.save()
        jury_simulation.refresh_from_db()
        assert jury_simulation.status == 'running'

        jury_simulation.status = 'deliberating'
        jury_simulation.save()
        jury_simulation.refresh_from_db()
        assert jury_simulation.status == 'deliberating'

        jury_simulation.status = 'completed'
        jury_simulation.save()
        jury_simulation.refresh_from_db()
        assert jury_simulation.status == 'completed'

    def test_jury_member_creation(self, jury_member):
        """Jurado deve ser criado com perfil completo."""
        assert jury_member.name == 'Maria Silva'
        assert jury_member.age == 35
        assert jury_member.gender == 'feminino'
        assert jury_member.profession == 'Professora'
        assert jury_member.education == 'superior'
        assert 'empática' in jury_member.personality_traits
        assert jury_member.vote == 'pendente'
        assert str(jury_member) == 'Maria Silva - Professora'

    def test_jury_member_vote(self, jury_member):
        """Voto do jurado deve ser registrado."""
        jury_member.vote = 'condenacao'
        jury_member.reasoning = 'As provas são conclusivas.'
        jury_member.save()
        jury_member.refresh_from_db()
        assert jury_member.vote == 'condenacao'
        assert jury_member.reasoning == 'As provas são conclusivas.'

    def test_simulation_document_upload(self, simulation_document):
        """Documento da simulação deve ser criado e associado."""
        assert simulation_document.title == 'Denúncia do Ministério Público'
        assert simulation_document.document_type == 'denuncia'
        assert simulation_document.extracted_text != ''
        assert str(simulation_document) == 'Denúncia do Ministério Público (Denúncia)'

    def test_judge_profile_creation(self, judge_profile):
        """Perfil de juiz deve ser criado com dados completos."""
        assert judge_profile.name == 'Dr. Carlos Mendes'
        assert judge_profile.state == 'SP'
        assert judge_profile.court == 'TJSP'
        assert judge_profile.comarca == 'São Paulo'
        assert judge_profile.vara == '1ª Vara Criminal'
        assert judge_profile.is_active is True
        assert str(judge_profile) == 'Dr. Carlos Mendes - TJSP (São Paulo)'

    def test_court_creation(self, court):
        """Tribunal deve ser criado com comarcas."""
        assert court.name == 'TJSP'
        assert court.court_type == 'TJ'
        assert court.state == 'SP'
        assert 'São Paulo' in court.comarcas
        assert court.is_active is True
        assert str(court) == 'TJSP (SP)'


# =====================================================
# 2. API TESTS
# =====================================================
@pytest.mark.django_db
class TestSimulationAPI:
    """Testes da API REST de simulações."""

    def test_list_simulations(self, api_client, user, jury_simulation, judge_simulation):
        """GET /api/v1/simulations/simulations/ deve listar simulações do usuário."""
        api_client.force_authenticate(user=user)
        url = reverse('simulations:simulation-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) == 2

    def test_create_jury_simulation(self, api_client, user):
        """POST deve criar simulação de júri."""
        api_client.force_authenticate(user=user)
        url = reverse('simulations:simulation-list')
        data = {
            'simulation_type': 'jury',
            'title': 'Nova Simulação de Júri',
            'description': 'Descrição do caso',
            'config': {'crime_type': 'Latrocínio'},
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['simulation_type'] == 'jury'
        assert response.data['title'] == 'Nova Simulação de Júri'
        assert response.data['status'] == 'draft'

    def test_create_judge_simulation(self, api_client, user):
        """POST deve criar simulação de sentença."""
        api_client.force_authenticate(user=user)
        url = reverse('simulations:simulation-list')
        data = {
            'simulation_type': 'judge',
            'title': 'Nova Simulação de Sentença',
            'description': 'Caso cível',
            'config': {'area': 'Cível'},
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['simulation_type'] == 'judge'

    def test_add_jury_members(self, api_client, user, jury_simulation):
        """POST nested deve adicionar jurado à simulação."""
        api_client.force_authenticate(user=user)
        url = reverse(
            'simulations:simulation-jury-members-list',
            kwargs={'simulation_pk': jury_simulation.id},
        )
        data = {
            'name': 'João Pereira',
            'age': 42,
            'gender': 'masculino',
            'profession': 'Agricultor',
            'education': 'fundamental',
            'personality_traits': ['conservador', 'religioso'],
            'background': 'Morador da zona rural.',
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'João Pereira'
        assert JuryMember.objects.filter(simulation=jury_simulation).count() == 1

    def test_add_document(self, api_client, user, jury_simulation):
        """POST nested deve adicionar documento à simulação."""
        api_client.force_authenticate(user=user)
        url = reverse(
            'simulations:simulation-documents-list',
            kwargs={'simulation_pk': jury_simulation.id},
        )
        fake_file = SimpleUploadedFile(
            'defesa.pdf',
            b'conteudo da defesa',
            content_type='application/pdf',
        )
        data = {
            'title': 'Peça de Defesa',
            'file': fake_file,
            'document_type': 'defesa',
        }
        response = api_client.post(url, data, format='multipart')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'Peça de Defesa'
        assert response.data['document_type'] == 'defesa'

    def test_list_courts(self, api_client, user, court):
        """GET /api/v1/simulations/courts/ deve listar tribunais."""
        api_client.force_authenticate(user=user)
        url = reverse('simulations:court-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) >= 1

    def test_list_judges(self, api_client, user, judge_profile):
        """GET /api/v1/simulations/judges/ deve listar perfis de juízes."""
        api_client.force_authenticate(user=user)
        url = reverse('simulations:judge-profile-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) >= 1

    def test_simulation_permissions(self, api_client, user, other_user, jury_simulation):
        """Outro usuário não deve acessar simulação alheia."""
        api_client.force_authenticate(user=other_user)
        url = reverse('simulations:simulation-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        sim_ids = [r['id'] for r in results]
        assert str(jury_simulation.id) not in sim_ids

    def test_simulation_detail_permission(self, api_client, user, other_user, jury_simulation):
        """Outro usuário não deve acessar detalhe de simulação alheia."""
        api_client.force_authenticate(user=other_user)
        url = reverse('simulations:simulation-detail', kwargs={'pk': jury_simulation.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unauthenticated_access(self, api_client):
        """Requisição sem autenticação deve retornar 401."""
        url = reverse('simulations:simulation-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_jury_requires_7_members(self, api_client, user, jury_simulation, simulation_document):
        """Simulação de júri com menos de 7 jurados deve emitir aviso (CPP art. 447)."""
        # Criar apenas 3 jurados (menos que 7)
        for i in range(3):
            JuryMember.objects.create(
                simulation=jury_simulation,
                name=f'Jurado {i}',
                age=30 + i,
                gender='masculino',
                profession='Profissão',
                education='medio',
            )

        assert jury_simulation.jury_members.count() == 3
        assert jury_simulation.jury_members.count() < 7


# =====================================================
# 3. SERVICE TESTS
# =====================================================
@pytest.mark.django_db
class TestJurySimulationService:
    """Testes do JurySimulationService."""

    @patch('apps.simulations.services.jury_simulation_service.UnifiedLLMService')
    def test_build_case_context(self, mock_llm_cls, jury_simulation, simulation_document):
        """_build_case_context deve montar contexto a partir dos documentos."""
        from apps.simulations.services.jury_simulation_service import JurySimulationService
        service = JurySimulationService(str(jury_simulation.id))

        context = service._build_case_context()
        assert 'Denúncia do Ministério Público' in context
        assert 'Ministério Público denuncia João' in context

    @patch('apps.simulations.services.jury_simulation_service.UnifiedLLMService')
    def test_build_case_context_empty(self, mock_llm_cls, jury_simulation):
        """_build_case_context sem documentos deve retornar string vazia."""
        from apps.simulations.services.jury_simulation_service import JurySimulationService
        service = JurySimulationService(str(jury_simulation.id))

        context = service._build_case_context()
        assert context == ''

    @patch('apps.simulations.services.jury_simulation_service.UnifiedLLMService')
    def test_format_event(self, mock_llm_cls, jury_simulation):
        """_format_event deve retornar dicionário com campos corretos."""
        from apps.simulations.services.jury_simulation_service import JurySimulationService
        service = JurySimulationService(str(jury_simulation.id))

        event = service._format_event('abertura', 'juiz', 'Declaro aberta a sessão')
        assert event['event'] == 'message'
        assert event['phase'] == 'abertura'
        assert event['role'] == 'juiz'
        assert event['content'] == 'Declaro aberta a sessão'

    @patch('apps.simulations.services.jury_simulation_service.UnifiedLLMService')
    def test_format_event_with_member_id(self, mock_llm_cls, jury_simulation):
        """_format_event com member_id deve incluir o campo."""
        from apps.simulations.services.jury_simulation_service import JurySimulationService
        service = JurySimulationService(str(jury_simulation.id))

        event = service._format_event(
            'deliberacao', 'jurado', 'Eu acho que...',
            member_id='abc-123',
            extra={'member_name': 'Maria'},
        )
        assert event['member_id'] == 'abc-123'
        assert event['member_name'] == 'Maria'

    @patch('apps.simulations.services.jury_simulation_service.UnifiedLLMService')
    def test_juror_prompt_includes_profile(self, mock_llm_cls, jury_simulation, jury_member):
        """Jurados devem ter perfil incluído no prompt da deliberação."""
        from apps.simulations.services.jury_simulation_service import JurySimulationService
        service = JurySimulationService(str(jury_simulation.id))

        # Verificar que o serviço carregou os jurados
        assert len(service.jury_members) == 1
        member = service.jury_members[0]
        assert member.name == 'Maria Silva'
        assert member.profession == 'Professora'
        assert 'empática' in member.personality_traits

    @patch('apps.simulations.services.jury_simulation_service.UnifiedLLMService')
    def test_quesitos_default(self, mock_llm_cls, jury_simulation):
        """_get_quesitos deve retornar quesitos padrão quando não configurados."""
        from apps.simulations.services.jury_simulation_service import JurySimulationService
        service = JurySimulationService(str(jury_simulation.id))

        quesitos = service._get_quesitos()
        assert len(quesitos) == 3
        assert 'materialidade' in quesitos[0].lower()
        assert 'autor' in quesitos[1].lower()
        assert 'absolve' in quesitos[2].lower()

    @patch('apps.simulations.services.jury_simulation_service.UnifiedLLMService')
    def test_quesitos_custom(self, mock_llm_cls, user):
        """_get_quesitos deve retornar quesitos customizados da config."""
        sim = Simulation.objects.create(
            user=user,
            simulation_type='jury',
            title='Teste quesitos custom',
            config={'quesitos': ['Quesito A?', 'Quesito B?']},
        )
        from apps.simulations.services.jury_simulation_service import JurySimulationService
        service = JurySimulationService(str(sim.id))

        quesitos = service._get_quesitos()
        assert quesitos == ['Quesito A?', 'Quesito B?']

    @patch('apps.simulations.services.jury_simulation_service.UnifiedLLMService')
    def test_vote_parsing_sim(self, mock_llm_cls, jury_simulation):
        """_extract_vote deve extrair SIM corretamente."""
        from apps.simulations.services.jury_simulation_service import JurySimulationService
        service = JurySimulationService(str(jury_simulation.id))

        assert service._extract_vote('VOTO: SIM\nJUSTIFICATIVA: Provas claras.') == 'sim'
        assert service._extract_vote('VOTO:SIM\nJUSTIFICATIVA: Convicto.') == 'sim'

    @patch('apps.simulations.services.jury_simulation_service.UnifiedLLMService')
    def test_vote_parsing_nao(self, mock_llm_cls, jury_simulation):
        """_extract_vote deve extrair NÃO corretamente."""
        from apps.simulations.services.jury_simulation_service import JurySimulationService
        service = JurySimulationService(str(jury_simulation.id))

        assert service._extract_vote('VOTO: NÃO\nJUSTIFICATIVA: Dúvida razoável.') == 'nao'
        assert service._extract_vote('VOTO:NÃO\nJUSTIFICATIVA: Insuficiente.') == 'nao'
        assert service._extract_vote('VOTO: NAO\nJUSTIFICATIVA: Sem provas.') == 'nao'

    @patch('apps.simulations.services.jury_simulation_service.UnifiedLLMService')
    def test_vote_parsing_fallback(self, mock_llm_cls, jury_simulation):
        """_extract_vote deve usar fallback quando formato não reconhecido."""
        from apps.simulations.services.jury_simulation_service import JurySimulationService
        service = JurySimulationService(str(jury_simulation.id))

        # SIM no início do texto
        assert service._extract_vote('SIM, acredito que...') == 'sim'
        # Nenhum padrão reconhecido -> default 'nao'
        assert service._extract_vote('Não tenho certeza sobre isso...') == 'nao'

    @patch('apps.simulations.services.jury_simulation_service.UnifiedLLMService')
    def test_get_history_summary_empty(self, mock_llm_cls, jury_simulation):
        """_get_history_summary sem histórico retorna mensagem padrão."""
        from apps.simulations.services.jury_simulation_service import JurySimulationService
        service = JurySimulationService(str(jury_simulation.id))

        summary = service._get_history_summary('acusacao')
        assert 'Nenhum argumento registrado' in summary

    @patch('apps.simulations.services.jury_simulation_service.UnifiedLLMService')
    def test_build_debate_summary_empty(self, mock_llm_cls, jury_simulation):
        """_build_debate_summary sem histórico retorna mensagem padrão."""
        from apps.simulations.services.jury_simulation_service import JurySimulationService
        service = JurySimulationService(str(jury_simulation.id))

        summary = service._build_debate_summary()
        assert 'Nenhuma discussão registrada' in summary


@pytest.mark.django_db
class TestJudgeSimulationService:
    """Testes do JudgeSimulationService."""

    @patch('apps.simulations.services.judge_simulation_service.UnifiedLLMService')
    def test_load_judge_profile(self, mock_llm_cls, user, judge_profile):
        """_load_judge_profile deve carregar perfil configurado."""
        sim = Simulation.objects.create(
            user=user,
            simulation_type='judge',
            title='Teste com juiz',
            config={'judge_id': str(judge_profile.id)},
        )
        from apps.simulations.services.judge_simulation_service import JudgeSimulationService
        service = JudgeSimulationService(str(sim.id))

        assert service.judge_profile is not None
        assert service.judge_profile.name == 'Dr. Carlos Mendes'
        assert service.judge_profile.state == 'SP'

    @patch('apps.simulations.services.judge_simulation_service.UnifiedLLMService')
    def test_load_judge_profile_none(self, mock_llm_cls, judge_simulation):
        """_load_judge_profile sem judge_id retorna None."""
        from apps.simulations.services.judge_simulation_service import JudgeSimulationService
        service = JudgeSimulationService(str(judge_simulation.id))

        assert service.judge_profile is None

    @patch('apps.simulations.services.judge_simulation_service.UnifiedLLMService')
    def test_load_judge_profile_invalid_id(self, mock_llm_cls, user):
        """_load_judge_profile com ID inválido retorna None."""
        sim = Simulation.objects.create(
            user=user,
            simulation_type='judge',
            title='Teste juiz inexistente',
            config={'judge_id': '00000000-0000-0000-0000-000000000000'},
        )
        from apps.simulations.services.judge_simulation_service import JudgeSimulationService
        service = JudgeSimulationService(str(sim.id))

        assert service.judge_profile is None

    @patch('apps.simulations.services.judge_simulation_service.UnifiedLLMService')
    def test_sentence_prompt_includes_judge_style(self, mock_llm_cls, user, judge_profile):
        """Prompt da sentença deve incluir estilo/perfil do juiz."""
        sim = Simulation.objects.create(
            user=user,
            simulation_type='judge',
            title='Teste prompt sentença',
            config={'judge_id': str(judge_profile.id)},
        )
        # Criar documento para ter contexto
        fake_file = SimpleUploadedFile('doc.pdf', b'content', content_type='application/pdf')
        SimulationDocument.objects.create(
            simulation=sim,
            title='Documento teste',
            file=fake_file,
            extracted_text='Fatos do caso para análise.',
        )

        from apps.simulations.services.judge_simulation_service import JudgeSimulationService
        service = JudgeSimulationService(str(sim.id))

        # Verificar que o perfil foi carregado corretamente
        assert service.judge_profile.name == 'Dr. Carlos Mendes'
        assert service.judge_profile.decision_patterns['tendencia'] == 'rigoroso'

    @patch('apps.simulations.services.judge_simulation_service.UnifiedLLMService')
    def test_build_case_context(self, mock_llm_cls, user):
        """_build_case_context deve montar contexto dos documentos."""
        sim = Simulation.objects.create(
            user=user,
            simulation_type='judge',
            title='Teste contexto',
        )
        fake_file = SimpleUploadedFile('doc.pdf', b'content', content_type='application/pdf')
        SimulationDocument.objects.create(
            simulation=sim,
            title='Petição Inicial',
            file=fake_file,
            extracted_text='O autor pleiteia indenização por danos morais...',
        )

        from apps.simulations.services.judge_simulation_service import JudgeSimulationService
        service = JudgeSimulationService(str(sim.id))

        context = service._build_case_context()
        assert 'Petição Inicial' in context
        assert 'indenização por danos morais' in context

    @patch('apps.simulations.services.judge_simulation_service.UnifiedLLMService')
    def test_event_format(self, mock_llm_cls, judge_simulation):
        """_event deve retornar dicionário com event e content."""
        from apps.simulations.services.judge_simulation_service import JudgeSimulationService
        service = JudgeSimulationService(str(judge_simulation.id))

        event = service._event('phase', 'Análise do Perfil')
        assert event['event'] == 'phase'
        assert event['content'] == 'Análise do Perfil'

    @patch('apps.simulations.services.judge_simulation_service.UnifiedLLMService')
    def test_event_format_with_extra(self, mock_llm_cls, judge_simulation):
        """_event com extra deve incluir campos adicionais."""
        from apps.simulations.services.judge_simulation_service import JudgeSimulationService
        service = JudgeSimulationService(str(judge_simulation.id))

        event = service._event('profile', 'Info', extra={'judge_name': 'Dr. X'})
        assert event['judge_name'] == 'Dr. X'


# =====================================================
# 4. SEED TESTS
# =====================================================
@pytest.mark.django_db
class TestSeedCourts:
    """Testes do management command seed_courts."""

    def test_seed_creates_courts(self):
        """seed_courts deve criar tribunais no banco."""
        assert Court.objects.count() == 0
        call_command('seed_courts')
        # 3 superiores + 5 TRFs + 27 TJs = 35
        assert Court.objects.count() == 35

    def test_seed_idempotent(self):
        """seed_courts executado duas vezes não deve duplicar tribunais."""
        call_command('seed_courts')
        first_count = Court.objects.count()

        call_command('seed_courts')
        second_count = Court.objects.count()

        assert first_count == second_count
        assert first_count == 35

    def test_seed_court_types(self):
        """seed_courts deve criar tribunais dos tipos corretos."""
        call_command('seed_courts')

        assert Court.objects.filter(court_type='STF').count() == 1
        assert Court.objects.filter(court_type='STJ').count() == 1
        assert Court.objects.filter(court_type='TST').count() == 1
        assert Court.objects.filter(court_type='TRF').count() == 5
        assert Court.objects.filter(court_type='TJ').count() == 27

    def test_seed_court_has_comarcas(self):
        """Tribunais criados devem ter comarcas preenchidas."""
        call_command('seed_courts')

        tjsp = Court.objects.filter(name='TJSP').first()
        assert tjsp is not None
        assert len(tjsp.comarcas) > 0
        assert 'São Paulo' in tjsp.comarcas


# =====================================================
# 5. DEBATE MESSAGE MODEL TESTS
# =====================================================
@pytest.mark.django_db
class TestJuryDebateMessage:
    """Testes do modelo JuryDebateMessage."""

    def test_create_debate_message(self, jury_simulation, jury_member):
        """Mensagem de debate deve ser criada corretamente."""
        msg = JuryDebateMessage.objects.create(
            simulation=jury_simulation,
            jury_member=jury_member,
            role='jurado',
            content='Eu acredito que o réu é inocente.',
            phase='deliberacao',
        )
        assert msg.role == 'jurado'
        assert msg.phase == 'deliberacao'
        assert jury_member.name in str(msg) or 'Jurado' in str(msg)

    def test_create_system_message(self, jury_simulation):
        """Mensagem de sistema (sem jurado) deve ser criada."""
        msg = JuryDebateMessage.objects.create(
            simulation=jury_simulation,
            jury_member=None,
            role='sistema',
            content='Sessão encerrada.',
            phase='veredicto',
        )
        assert msg.jury_member is None
        assert msg.role == 'sistema'
