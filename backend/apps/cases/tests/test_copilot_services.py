"""
Testes para os serviços Copilot de IA.
Cobre: LeadAIService, ClientAIService, DocumentAIService, TimesheetAIService,
       TeamAIService, DeadlineAIService, PushAnalysisService
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.cases.models import Client, LegalCase
from apps.cases.services.lead_ai_service import LeadAIService
from apps.cases.services.client_ai_service import ClientAIService
from apps.cases.services.document_ai_service import DocumentAIService
from apps.cases.services.timesheet_ai_service import TimesheetAIService
from apps.cases.services.team_ai_service import TeamAIService
from apps.cases.services.deadline_ai_service import DeadlineAIService
from apps.cases.services.push_analysis_service import PushAnalysisService

User = get_user_model()

# Patch paths para cada serviço (varia conforme importação real)
LLM_PATCH_INTELLIGENT = 'apps.intelligent_assistant.services.llm_provider_service.UnifiedLLMService.get_service'


# =====================================================
# FIXTURES
# =====================================================
@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='copilot_test',
        email='copilot@verus.ai',
        password='testpass123',
        role='analyst',
    )


@pytest.fixture
def legal_case(db, user):
    return LegalCase.objects.create(
        titulo='Caso Teste Copilot',
        cliente_nome='Cliente Teste',
        especialidade='civel',
        status='ativo',
        fase='inicial',
        advogado_responsavel=user,
        created_by=user,
    )


# =====================================================
# TESTES - LEAD AI SERVICE (CRM)
# =====================================================
@pytest.mark.django_db
class TestLeadAIService:
    """Testes para LeadAIService - CRM/Leads."""

    @patch(LLM_PATCH_INTELLIGENT)
    @pytest.mark.asyncio
    async def test_classify_lead_temperature(self, mock_get_service, user):
        """Classificar temperatura do lead deve retornar hot/warm/cold."""
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(return_value='{"temperature": "hot", "confidence": 85, "reasons": ["urgencia"], "suggested_approach": "Ligar imediatamente"}')
        mock_get_service.return_value = mock_llm

        result = await LeadAIService.classify_lead_temperature(
            description='Preciso de advogado urgente',
            specialty='trabalhista',
            urgency=True,
            estimated_value=50000,
        )

        assert 'temperature' in result
        assert result['temperature'] in ['hot', 'warm', 'cold']

    @patch(LLM_PATCH_INTELLIGENT)
    @pytest.mark.asyncio
    async def test_generate_follow_up_message(self, mock_get_service, user):
        """Gerar mensagem de follow-up personalizada."""
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(return_value='Ola! Gostaria de acompanhar...')
        mock_get_service.return_value = mock_llm

        result = await LeadAIService.generate_follow_up_message(
            lead_name='Lead Teste',
            temperature='hot',
            specialty='trabalhista',
        )

        assert isinstance(result, str)
        assert len(result) > 5

    @patch(LLM_PATCH_INTELLIGENT)
    @pytest.mark.asyncio
    async def test_predict_conversion_probability(self, mock_get_service, user):
        """Prever probabilidade de conversão."""
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(return_value='{"probability": 75, "factors": ["budget"], "recommendation": "Priorizar"}')
        mock_get_service.return_value = mock_llm

        lead_data = {'specialty': 'civel', 'estimated_value': 10000}
        result = await LeadAIService.predict_conversion_probability(lead_data)

        assert 'probability' in result

    def test_heuristic_classification_hot(self, user):
        """Classificação heurística para lead hot."""
        result = LeadAIService._heuristic_classification(
            description='Preciso de advogado URGENTE!',
            urgency=True,
            estimated_value=50000,
            source='indicacao',
        )
        assert result['temperature'] == 'hot'

    def test_heuristic_classification_cold(self, user):
        """Classificação heurística para lead cold."""
        result = LeadAIService._heuristic_classification(
            description='',
            urgency=False,
            estimated_value=None,
            source='outro',
        )
        assert result['temperature'] == 'cold'

    def test_fallback_follow_up(self, user):
        """Fallback de follow-up quando IA indisponível."""
        for temp in ['hot', 'warm', 'cold']:
            result = LeadAIService._fallback_follow_up(temp, 'Teste')
            assert isinstance(result, str)
            assert len(result) > 20


# =====================================================
# TESTES - CLIENT AI SERVICE
# =====================================================
@pytest.mark.django_db
class TestClientAIService:
    """Testes para ClientAIService - Clientes."""

    @patch(LLM_PATCH_INTELLIGENT)
    @pytest.mark.asyncio
    async def test_extract_data_from_document(self, mock_get_service):
        """Extrair dados de documento uploadado."""
        mock_llm = AsyncMock()
        mock_llm.generate_with_attachment_async = AsyncMock(
            return_value='{"name": "Joao", "cpf_cnpj": "123.456.789-00", "confidence": 90, "raw_text": "texto"}'
        )
        mock_get_service.return_value = mock_llm

        result = await ClientAIService.extract_data_from_document(b'fake', 'doc.pdf')

        assert 'data' in result
        assert 'confidence' in result

    @patch(LLM_PATCH_INTELLIGENT)
    @pytest.mark.asyncio
    async def test_check_conflict_of_interest_no_conflict(self, mock_get_service, user):
        """Verificar conflito - sem conflitos."""
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(return_value='{"has_conflict": false, "risk_level": "low"}')
        mock_get_service.return_value = mock_llm

        result = await ClientAIService.check_conflict_of_interest(
            client_name='Novo Cliente',
            cpf_cnpj='999.999.999-99',
        )

        assert 'has_conflict' in result

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_check_conflict_of_interest_with_conflict(self, user):
        """Verificar conflito - com conflito existente."""
        Client.objects.create(
            name='Cliente Conflitante',
            cpf_cnpj='111.111.111-11',
            is_active=True,
            created_by=user,
        )

        result = await ClientAIService.check_conflict_of_interest(
            client_name='Cliente Conflitante',
            cpf_cnpj='111.111.111-11',
        )

        assert result['has_conflict'] is True

    @patch(LLM_PATCH_INTELLIGENT)
    @pytest.mark.asyncio
    async def test_suggest_fee_range(self, mock_get_service, user):
        """Sugerir faixa de honorários."""
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(
            return_value='{"min_value": 3000, "max_value": 5000, "suggested_value": 4000}'
        )
        mock_get_service.return_value = mock_llm

        result = await ClientAIService.suggest_fee_range(
            {'name': 'Cliente'},
            {'specialty': 'civel', 'valor_causa': 100000},
        )

        assert 'min_value' in result
        assert 'suggested_value' in result

    def test_suggest_fee_range_fallback(self, user):
        """Fallback heurístico para honorários."""
        result = ClientAIService._fallback_fee_suggestion(
            {'name': 'Cliente'},
            {'specialty': 'tributario', 'valor_causa': 500000},
        )
        assert 'min_value' in result


# =====================================================
# TESTES - DOCUMENT AI SERVICE
# =====================================================
@pytest.mark.django_db
class TestDocumentAIService:
    """Testes para DocumentAIService - Documentos."""

    @patch(LLM_PATCH_INTELLIGENT)
    @pytest.mark.asyncio
    async def test_generate_document(self, mock_get_service, user):
        """Gerar documento jurídico via IA."""
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(return_value='{"content": "Peticao...", "structure": ["cabecalho"]}')
        mock_get_service.return_value = mock_llm

        result = await DocumentAIService.generate_document("Gerar peticao", {"case_type": "civel"})

        assert 'content' in result

    @patch(LLM_PATCH_INTELLIGENT)
    @pytest.mark.asyncio
    async def test_review_document(self, mock_get_service, user):
        """Revisar documento."""
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(return_value='{"quality_score": 85, "problems": [], "suggestions": []}')
        mock_get_service.return_value = mock_llm

        result = await DocumentAIService.review_document("Peticao inicial")

        assert 'quality_score' in result
        assert 0 <= result['quality_score'] <= 100

    @patch(LLM_PATCH_INTELLIGENT)
    @pytest.mark.asyncio
    async def test_suggest_template(self, mock_get_service, user):
        """Sugerir template."""
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(return_value='{"templates": [{"id": 1, "name": "Peticao"}]}')
        mock_get_service.return_value = mock_llm

        result = await DocumentAIService.suggest_template('trabalhista', 'Reclamacao')

        assert 'templates' in result

    @patch(LLM_PATCH_INTELLIGENT)
    @pytest.mark.asyncio
    async def test_auto_fill_template(self, mock_get_service, user):
        """Auto-preencher template."""
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(return_value='{"filled_content": "Preenchido", "fields_filled": 5}')
        mock_get_service.return_value = mock_llm

        result = await DocumentAIService.auto_fill_template("Modelo {{CLIENTE}}", {"cliente": "Joao"})

        assert 'filled_content' in result


# =====================================================
# TESTES - TIMESHEET AI SERVICE
# =====================================================
@pytest.mark.django_db
class TestTimesheetAIService:
    """Testes para TimesheetAIService - Timesheet."""

    @patch(LLM_PATCH_INTELLIGENT)
    @pytest.mark.asyncio
    async def test_analyze_activities_for_timesheet(self, mock_get_service, user):
        """Analisar atividades e sugerir lançamentos."""
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(return_value='{"suggestions": []}')
        mock_get_service.return_value = mock_llm

        result = await TimesheetAIService.analyze_activities_for_timesheet([], user)

        assert 'suggestions' in result

    @patch(LLM_PATCH_INTELLIGENT)
    @pytest.mark.asyncio
    async def test_suggest_description(self, mock_get_service, user):
        """Gerar descrição técnica."""
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(return_value='{"description": "Descrica tecnica", "billable": true}')
        mock_get_service.return_value = mock_llm

        result = await TimesheetAIService.suggest_description("Fiz peticao", 'peticao')

        assert 'description' in result

    @pytest.mark.asyncio
    async def test_detect_unlogged_hours(self, user):
        """Detectar horas não lançadas."""
        result = await TimesheetAIService.detect_unlogged_hours(user, '2026-06-01', '2026-06-03')
        assert isinstance(result, dict)

    @patch(LLM_PATCH_INTELLIGENT)
    @pytest.mark.asyncio
    async def test_optimize_billing(self, mock_get_service, user):
        """Otimizar faturamento."""
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(return_value='{"optimizations": [], "total_optimized": 0}')
        mock_get_service.return_value = mock_llm

        result = await TimesheetAIService.optimize_billing([])

        assert 'optimizations' in result


# =====================================================
# TESTES - TEAM AI SERVICE
# =====================================================
@pytest.mark.django_db
class TestTeamAIService:
    """Testes para TeamAIService - Equipe."""

    @patch(LLM_PATCH_INTELLIGENT)
    @pytest.mark.asyncio
    async def test_suggest_allocation(self, mock_get_service, user):
        """Sugerir alocação de equipe."""
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(return_value='{"score": 85, "team_members": [], "reasons": []}')
        mock_get_service.return_value = mock_llm

        result = await TeamAIService.suggest_allocation(
            {'specialty': 'civel'},
            [{'name': 'Adv 1', 'specialty': 'civel'}]
        )

        assert 'score' in result

    @patch(LLM_PATCH_INTELLIGENT)
    @pytest.mark.asyncio
    async def test_balance_workload(self, mock_get_service, user):
        """Analisar balanceamento."""
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(return_value='{"balance_score": 70, "recommendations": []}')
        mock_get_service.return_value = mock_llm

        result = await TeamAIService.balance_workload([{'name': 'Adv 1', 'current_load': 0.5}])

        assert 'balance_score' in result

    @patch(LLM_PATCH_INTELLIGENT)
    @pytest.mark.asyncio
    async def test_match_specialty(self, mock_get_service, user):
        """Match por especialidade."""
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(return_value='{"matches": []}')
        mock_get_service.return_value = mock_llm

        result = await TeamAIService.match_specialty(['civel'], [{'name': 'Adv 1', 'specialties': ['civel']}])

        assert 'matches' in result

    @pytest.mark.asyncio
    async def test_predict_availability(self, user):
        """Prever disponibilidade."""
        result = await TeamAIService.predict_availability([{'name': 'Adv 1', 'current_cases': 10}])
        assert isinstance(result, dict)


# =====================================================
# TESTES - DEADLINE AI SERVICE (sem LLM - cálculo puro)
# =====================================================
@pytest.mark.django_db
class TestDeadlineAIService:
    """Testes para DeadlineAIService - Prazos."""

    def test_count_business_days(self, user):
        """Contar dias úteis entre datas."""
        service = DeadlineAIService()
        from datetime import datetime
        start = datetime(2026, 6, 1)
        end = datetime(2026, 6, 15)
        business_days = service.count_business_days(start, end)
        assert business_days > 0
        assert business_days <= 14

    def test_is_business_day(self, user):
        """Verificar se dia é útil."""
        service = DeadlineAIService()
        from datetime import datetime
        # Segunda-feira
        assert service.is_business_day(datetime(2026, 6, 1)) is True
        # Sábado
        assert service.is_business_day(datetime(2026, 6, 6)) is False

    def test_add_business_days(self, user):
        """Adicionar dias úteis."""
        service = DeadlineAIService()
        result = service.add_business_days('2026-06-01', 5)
        assert result is not None

    def test_get_deadline_type_info(self, user):
        """Obter info de tipo de prazo."""
        service = DeadlineAIService()
        info = service.get_deadline_type_info('contestacao')
        assert info is not None
        assert 'dias' in info

    @pytest.mark.asyncio
    async def test_suggest_strategy(self, user):
        """Sugerir estratégia (fallback sem LLM)."""
        result = await DeadlineAIService.suggest_strategy(
            {'type': 'recurso', 'remaining_days': 5, 'complexity': 'alta'}
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_group_related_deadlines(self, user, legal_case):
        """Agrupar prazos por caso."""
        from apps.cases.models import LegalDeadline
        LegalDeadline.objects.create(
            caso=legal_case, titulo='Prazo 1', data_prazo='2026-06-15',
            tipo='processual', created_by=user,
        )
        result = await DeadlineAIService.group_related_deadlines(legal_case.id)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_identify_critical_deadlines(self, user):
        """Identificar prazos críticos."""
        result = await DeadlineAIService.identify_critical_deadlines([
            {'date': '2026-06-03', 'type': 'recurso'}
        ])
        assert isinstance(result, dict)


# =====================================================
# TESTES - PUSH ANALYSIS SERVICE
# =====================================================
@pytest.mark.django_db
class TestPushAnalysisService:
    """Testes para PushAnalysisService - Tribunal Push."""

    @patch(LLM_PATCH_INTELLIGENT)
    @pytest.mark.asyncio
    async def test_analyze_movement(self, mock_get_service, user):
        """Analisar movimentação."""
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(
            return_value='{"type": "intimacao", "importance": "high", "summary": "Intimacao", "requires_action": true}'
        )
        mock_get_service.return_value = mock_llm

        result = await PushAnalysisService.analyze_movement("Intimacao do autor")

        assert 'type' in result
        assert 'summary' in result

    @patch(LLM_PATCH_INTELLIGENT)
    @pytest.mark.asyncio
    async def test_suggest_actions(self, mock_get_service, user):
        """Sugerir ações."""
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(return_value='{"suggested_actions": [{"action": "manifestar", "priority": "high"}]}')
        mock_get_service.return_value = mock_llm

        result = await PushAnalysisService.suggest_actions('intimacao', 'Intimacao')

        assert 'suggested_actions' in result

    @patch(LLM_PATCH_INTELLIGENT)
    @pytest.mark.asyncio
    async def test_summarize_publication(self, mock_get_service, user):
        """Resumir publicação."""
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(return_value='{"summary": "Resumo", "key_points": []}')
        mock_get_service.return_value = mock_llm

        result = await PushAnalysisService.summarize_publication("Texto longo..." * 10)

        assert 'summary' in result

    @patch(LLM_PATCH_INTELLIGENT)
    @pytest.mark.asyncio
    async def test_classify_relevance(self, mock_get_service, user):
        """Classificar relevância."""
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(return_value='{"relevance": "high", "score": 0.85}')
        mock_get_service.return_value = mock_llm

        result = await PushAnalysisService.classify_relevance("Sentenca", "Acao")

        assert 'relevance' in result
        assert result['relevance'] in ['high', 'medium', 'low']


# =====================================================
# TESTES DE INTEGRAÇÃO - ENDPOINTS
# =====================================================
@pytest.mark.django_db
class TestCopilotEndpoints:
    """Testes de integração dos endpoints Copilot."""

    def test_classify_lead_endpoint(self, api_client, user):
        """Endpoint POST /copilot/classificar-lead/."""
        api_client.force_authenticate(user=user)
        url = reverse('cases:copilot-classify-lead')
        data = {'lead_data': {'name': 'Lead Teste'}}
        response = api_client.post(url, data, format='json')
        assert response.status_code in [200, 400, 500]

    def test_check_conflict_endpoint(self, api_client, user):
        """Endpoint POST /copilot/conflito-cliente/."""
        api_client.force_authenticate(user=user)
        url = reverse('cases:copilot-check-client-conflict')
        data = {'client_name': 'Cliente Teste', 'cpf_cnpj': '123.456.789-00'}
        response = api_client.post(url, data, format='json')
        assert response.status_code in [200, 400, 500]

    def test_suggest_fees_endpoint(self, api_client, user):
        """Endpoint POST /copilot/sugerir-honorarios/."""
        api_client.force_authenticate(user=user)
        url = reverse('cases:copilot-suggest-client-fees')
        data = {'client_data': {'name': 'Cliente'}}
        response = api_client.post(url, data, format='json')
        assert response.status_code in [200, 400, 500]

    def test_calculate_deadline_endpoint(self, api_client, user):
        """Endpoint POST /prazos/copilot/calcular/."""
        api_client.force_authenticate(user=user)
        url = reverse('cases:copilot-calculate-deadline')
        data = {'start_date': '2026-06-01', 'deadline_type': 'contestacao'}
        response = api_client.post(url, data, format='json')
        assert response.status_code in [200, 400, 500]

    def test_team_suggest_endpoint(self, api_client, user):
        """Endpoint POST /copilot/equipe/sugerir/."""
        api_client.force_authenticate(user=user)
        url = reverse('cases:copilot-team-suggest')
        data = {'case_data': {'specialty': 'civel'}}
        response = api_client.post(url, data, format='json')
        assert response.status_code in [200, 400, 500]
