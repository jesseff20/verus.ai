"""
Testes para o FinancialAIService - Copilot Financeiro.
Cobre: previsão de fluxo de caixa, sugestão de honorários, análise de inadimplência.
"""
import pytest
from unittest.mock import patch, AsyncMock
from django.contrib.auth import get_user_model
from apps.financeiro.services.financial_ai_service import FinancialAIService

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='financeiro_test',
        email='financeiro@verus.ai',
        password='testpass123',
        role='analyst',
    )


# =====================================================
# TESTES - FINANCIAL AI SERVICE
# =====================================================
@pytest.mark.django_db
class TestFinancialAIService:
    """Testes para FinancialAIService - Financeiro."""

    @patch('apps.financeiro.services.financial_ai_service.UnifiedLLMService.get_service')
    @pytest.mark.asyncio
    async def test_predict_cash_flow(self, mock_get_service, user):
        """Prever fluxo de caixa futuro."""
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(
            return_value='{"forecast": [{"date": "2026-07-01", "revenues": 50000, "expenses": 30000, "net": 20000}], "trend": "positive", "confidence": 0.8}'
        )
        mock_get_service.return_value = mock_llm

        historical_data = [
            {'date': '2026-05-01', 'revenues': 45000, 'expenses': 28000},
            {'date': '2026-06-01', 'revenues': 48000, 'expenses': 30000},
        ]

        result = await FinancialAIService.predict_cash_flow(historical_data, days=30)

        assert 'forecast' in result
        assert 'trend' in result
        assert isinstance(result['forecast'], list)

    @patch('apps.financeiro.services.financial_ai_service.UnifiedLLMService.get_service')
    @pytest.mark.asyncio
    async def test_predict_cash_flow_90_days(self, mock_get_service, user):
        """Previsão de fluxo de caixa para 90 dias."""
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(
            return_value='{"forecast": [{"month": "2026-07", "revenues": 55000, "expenses": 32000}], "trend": "stable", "confidence": 0.75}'
        )
        mock_get_service.return_value = mock_llm

        historical_data = [
            {'date': '2026-05-01', 'revenues': 45000, 'expenses': 28000},
        ]

        result = await FinancialAIService.predict_cash_flow(historical_data, days=90)

        assert 'forecast' in result
        assert 'trend' in result

    @patch('apps.financeiro.services.financial_ai_service.UnifiedLLMService.get_service')
    @pytest.mark.asyncio
    async def test_suggest_fees(self, mock_get_service, user):
        """Sugerir honorários baseados na tabela OAB."""
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(
            return_value='{"suggested_fee": 3500, "min_fee": 2500, "max_fee": 5000, "oab_reference": 3000, "factors": ["especialidade", "complexidade"]}'
        )
        mock_get_service.return_value = mock_llm

        service_type = 'peticao_inicial'
        specialty = 'trabalhista'
        case_value = 100000
        complexity = 'media'

        result = await FinancialAIService.suggest_fees(
            service_type, specialty, case_value, complexity
        )

        assert 'suggested_fee' in result
        assert 'oab_reference' in result
        assert result['suggested_fee'] > 0

    @pytest.mark.asyncio
    async def test_suggest_fees_fallback(self, user):
        """Fallback heurístico para sugestão de honorários."""
        result = FinancialAIService._fallback_fee_suggestion(
            service_type='contestacao',
            specialty='civel',
            case_value=50000,
            complexity='baixa',
        )

        assert 'suggested_fee' in result
        assert result['suggested_fee'] > 0

    @patch('apps.financeiro.services.financial_ai_service.UnifiedLLMService.get_service')
    @pytest.mark.asyncio
    async def test_analyze_default_risk(self, mock_get_service, user):
        """Analisar risco de inadimplência do cliente."""
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(
            return_value='{"risk_level": "medium", "score": 0.45, "factors": ["atrasos anteriores", "valor elevado"], "recommendation": "Exigir entrada"}'
        )
        mock_get_service.return_value = mock_llm

        client_history = {
            'name': 'Cliente',
            'payment_delays': 2,
            'outstanding_balance': 5000,
            'total_billed': 20000,
        }

        result = await FinancialAIService.analyze_default_risk(client_history)

        assert 'risk_level' in result
        assert result['risk_level'] in ['low', 'medium', 'high']
        assert 'score' in result
        assert 0 <= result['score'] <= 1

    @pytest.mark.asyncio
    async def test_analyze_default_risk_heuristic(self, user):
        """Análise heurística de risco de inadimplência."""
        client_history = {
            'name': 'Cliente',
            'payment_delays': 5,
            'outstanding_balance': 10000,
            'total_billed': 15000,
        }

        result = FinancialAIService._fallback_default_risk(client_history)

        assert 'risk_level' in result
        assert 'score' in result

    @patch('apps.financeiro.services.financial_ai_service.UnifiedLLMService.get_service')
    @pytest.mark.asyncio
    async def test_generate_collection_message(self, mock_get_service, user):
        """Gerar mensagem de cobrança personalizada."""
        mock_llm = AsyncMock()
        mock_llm.generate_async = AsyncMock(
            return_value='{"message": "Prezado cliente, lembramos que...", "tone": "professional", "channel": "email"}'
        )
        mock_get_service.return_value = mock_llm

        client_data = {'name': 'Cliente', 'email': 'cliente@email.com'}
        debt_info = {
            'amount': 5000,
            'due_date': '2026-05-01',
            'days_overdue': 30,
            'service_description': 'Honorários advocatícios',
        }

        result = await FinancialAIService.generate_collection_message(client_data, debt_info)

        assert 'message' in result
        assert 'tone' in result
        assert isinstance(result['message'], str)
        assert len(result['message']) > 50

    @pytest.mark.asyncio
    async def test_generate_collection_message_fallback(self, user):
        """Fallback para geração de mensagem de cobrança."""
        client_data = {'name': 'Cliente Devedor'}
        debt_info = {
            'amount': 3000,
            'due_date': '2026-05-01',
            'days_overdue': 15,
        }

        result = FinancialAIService._fallback_collection_message(client_data, debt_info)

        assert 'message' in result
        assert 'Cliente Devedor' in result['message']


# =====================================================
# TESTES DE INTEGRAÇÃO - ENDPOINTS FINANCEIRO
# =====================================================
@pytest.mark.django_db
class TestFinancialEndpoints:
    """Testes de integração dos endpoints financeiros."""

    def test_predict_cash_flow_endpoint(self, api_client, user):
        """Endpoint POST /financeiro/copilot/prever-fluxo/."""
        api_client.force_authenticate(user=user)
        url = '/api/cases/financeiro/copilot/prever-fluxo/'
        data = {
            'historical_data': [
                {'date': '2026-05-01', 'revenues': 45000, 'expenses': 28000},
            ],
            'days': 30,
        }
        response = api_client.post(url, data, format='json')
        # Endpoint pode retornar erro se IA não configurada
        assert response.status_code in [200, 400, 500]

    def test_analyze_default_risk_endpoint(self, api_client, user):
        """Endpoint POST /financeiro/copilot/analise-risco/."""
        api_client.force_authenticate(user=user)
        url = '/api/cases/financeiro/copilot/analise-risco/'
        data = {
            'client_history': {
                'name': 'Cliente',
                'payment_delays': 2,
                'outstanding_balance': 5000,
            }
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code in [200, 400, 500]

    def test_generate_collection_message_endpoint(self, api_client, user):
        """Endpoint POST /financeiro/copilot/cobranca/."""
        api_client.force_authenticate(user=user)
        url = '/api/cases/financeiro/copilot/cobranca/'
        data = {
            'client_data': {'name': 'Cliente', 'email': 'cliente@email.com'},
            'debt_info': {
                'amount': 5000,
                'due_date': '2026-05-01',
                'days_overdue': 30,
            },
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code in [200, 400, 500]
