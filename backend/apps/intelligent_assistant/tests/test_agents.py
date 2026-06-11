"""
Testes para os agentes do Assistente Inteligente.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from apps.intelligent_assistant.agents.base_agent import BaseAgent
from apps.intelligent_assistant.agents.section_agents.section_01_agent import Section01Agent
from apps.intelligent_assistant.agents.validators.section_01_validator import Section01Validator


class ConcreteAgent(BaseAgent):
    """Agente concreto para testar BaseAgent."""

    def generate(self, **kwargs):
        return {"result": "test"}


@pytest.mark.unit
@pytest.mark.agent
class TestBaseAgent:
    """Testes para BaseAgent."""

    def test_init(self, mock_claude_service, mock_kb_service):
        """Testa inicialização do agente."""
        agent = ConcreteAgent(
            name="TestAgent",
            claude_service=mock_claude_service,
            kb_service=mock_kb_service
        )
        assert agent.name == "TestAgent"
        assert agent.claude_service == mock_claude_service
        assert agent.kb_service == mock_kb_service

    def test_log_reasoning(self, mock_claude_service, mock_kb_service):
        """Testa logging de raciocínio."""
        agent = ConcreteAgent(
            name="TestAgent",
            claude_service=mock_claude_service,
            kb_service=mock_kb_service
        )
        agent._log_reasoning("Etapa 1")
        agent._log_reasoning("Etapa 2")

        log = agent.get_reasoning_log()
        assert "Etapa 1" in log
        assert "Etapa 2" in log

    def test_clear_reasoning_log(self, mock_claude_service, mock_kb_service):
        """Testa limpeza do log."""
        agent = ConcreteAgent(
            name="TestAgent",
            claude_service=mock_claude_service,
            kb_service=mock_kb_service
        )
        agent._log_reasoning("Etapa 1")
        assert len(agent._reasoning_log) == 1

        agent.clear_reasoning_log()
        assert len(agent._reasoning_log) == 0

    def test_extract_thinking_from_response(self, mock_claude_service, mock_kb_service):
        """Testa extração de thinking."""
        agent = ConcreteAgent(
            name="TestAgent",
            claude_service=mock_claude_service,
            kb_service=mock_kb_service
        )

        content_with_thinking = "<thinking>Pensamento do modelo</thinking>Conteúdo final"
        thinking, clean_content = agent._extract_thinking_from_response(content_with_thinking)

        assert thinking == "Pensamento do modelo"
        assert clean_content.strip() == "Conteúdo final"

    def test_extract_thinking_no_tags(self, mock_claude_service, mock_kb_service):
        """Testa extração quando não há tags de thinking."""
        agent = ConcreteAgent(
            name="TestAgent",
            claude_service=mock_claude_service,
            kb_service=mock_kb_service
        )

        content = "Apenas conteúdo"
        thinking, clean_content = agent._extract_thinking_from_response(content)

        assert thinking == ""
        assert clean_content == "Apenas conteúdo"

    def test_str_representation(self, mock_claude_service, mock_kb_service):
        """Testa representação em string."""
        agent = ConcreteAgent(
            name="TestAgent",
            claude_service=mock_claude_service,
            kb_service=mock_kb_service
        )
        assert "ConcreteAgent" in str(agent)
        assert "TestAgent" in str(agent)


@pytest.mark.unit
@pytest.mark.agent
class TestSection01Agent:
    """Testes para Section01Agent."""

    def test_init(self, mock_claude_service, mock_kb_service):
        """Testa inicialização."""
        agent = Section01Agent(
            claude_service=mock_claude_service,
            kb_service=mock_kb_service
        )
        assert agent.name == "Section01Agent"
        assert hasattr(agent, 'SYSTEM_PROMPT')

    def test_build_user_prompt(self, mock_claude_service, mock_kb_service):
        """Testa construção do prompt do usuário."""
        agent = Section01Agent(
            claude_service=mock_claude_service,
            kb_service=mock_kb_service
        )
        prompt = agent._build_user_prompt(
            objective="Contratar serviço de TI",
            additional_context="Contexto adicional"
        )

        assert "Contratar serviço de TI" in prompt
        assert "Contexto adicional" in prompt
        assert "OBJETIVO DA CONTRATAÇÃO" in prompt

    def test_build_user_prompt_without_context(self, mock_claude_service, mock_kb_service):
        """Testa construção do prompt sem contexto adicional."""
        agent = Section01Agent(
            claude_service=mock_claude_service,
            kb_service=mock_kb_service
        )
        prompt = agent._build_user_prompt(
            objective="Contratar serviço de TI"
        )

        assert "Contratar serviço de TI" in prompt
        assert "OBJETIVO DA CONTRATAÇÃO" in prompt

    @patch.object(Section01Agent, '_call_claude')
    @patch.object(Section01Agent, '_get_context_from_kb')
    def test_generate(self, mock_get_context, mock_call_claude, mock_claude_service, mock_kb_service):
        """Testa geração da Seção 1."""
        # Setup mocks
        mock_get_context.return_value = ["Documento 1", "Documento 2"]
        mock_call_claude.return_value = {
            'content': 'Conteúdo gerado da Seção 1',
            'usage': {'input_tokens': 100, 'output_tokens': 50},
            'model': 'claude-3-5-sonnet-20241022'
        }

        agent = Section01Agent(
            claude_service=mock_claude_service,
            kb_service=mock_kb_service
        )
        result = agent.generate(
            objective="Contratar serviço de desenvolvimento",
            collection_name="test_collection"
        )

        assert result['content'] == 'Conteúdo gerado da Seção 1'
        assert result['metadata']['section_number'] == 1
        assert result['metadata']['section_name'] == 'Descrição da Necessidade da Contratação'
        assert 'usage' in result
        assert 'reasoning' in result

        # Verificar que métodos foram chamados
        mock_get_context.assert_called_once()
        mock_call_claude.assert_called_once()

    @patch.object(Section01Agent, '_call_claude')
    @patch.object(Section01Agent, '_get_context_from_kb')
    def test_refine(self, mock_get_context, mock_call_claude, mock_claude_service, mock_kb_service):
        """Testa refinamento da Seção 1."""
        # Setup mocks
        mock_get_context.return_value = ["Documento relevante"]
        mock_call_claude.return_value = {
            'content': 'Conteúdo refinado da Seção 1',
            'usage': {'input_tokens': 150, 'output_tokens': 60},
            'model': 'claude-3-5-sonnet-20241022'
        }

        agent = Section01Agent(
            claude_service=mock_claude_service,
            kb_service=mock_kb_service
        )
        result = agent.refine(
            previous_content="Versão anterior",
            feedback="Adicionar mais detalhes sobre o contexto",
            collection_name="test_collection"
        )

        assert result['content'] == 'Conteúdo refinado da Seção 1'
        assert result['metadata']['is_refinement'] is True
        assert result['metadata']['temperature'] == 0.6  # Temperatura mais baixa para refinamento

        mock_call_claude.assert_called_once()


@pytest.mark.unit
@pytest.mark.agent
class TestSection01Validator:
    """Testes para Section01Validator."""

    def test_init(self, mock_claude_service, mock_kb_service):
        """Testa inicialização."""
        validator = Section01Validator(
            claude_service=mock_claude_service,
            kb_service=mock_kb_service
        )
        assert validator.name == "Section01Validator"
        assert hasattr(validator, 'SYSTEM_PROMPT')

    def test_validate_structure_valid_content(self, mock_claude_service, mock_kb_service):
        """Testa validação estrutural de conteúdo válido."""
        validator = Section01Validator(
            claude_service=mock_claude_service,
            kb_service=mock_kb_service
        )
        content = " ".join(["palavra"] * 400)  # 400 palavras

        result = validator._validate_structure(content)

        assert result['is_valid'] is True
        assert len(result['errors']) == 0

    def test_validate_structure_too_short(self, mock_claude_service, mock_kb_service):
        """Testa validação de conteúdo muito curto."""
        validator = Section01Validator(
            claude_service=mock_claude_service,
            kb_service=mock_kb_service
        )
        content = "Texto muito curto"

        result = validator._validate_structure(content)

        assert result['is_valid'] is False
        assert len(result['errors']) > 0
        assert any('curto' in error.lower() for error in result['errors'])

    def test_validate_structure_empty(self, mock_claude_service, mock_kb_service):
        """Testa validação de conteúdo vazio."""
        validator = Section01Validator(
            claude_service=mock_claude_service,
            kb_service=mock_kb_service
        )
        content = ""

        result = validator._validate_structure(content)

        assert result['is_valid'] is False
        assert len(result['errors']) > 0
        assert result['score'] == 0

    def test_parse_validation_response(self, mock_claude_service, mock_kb_service):
        """Testa parsing da resposta de validação."""
        validator = Section01Validator(
            claude_service=mock_claude_service,
            kb_service=mock_kb_service
        )

        json_response = '''
        {
          "is_valid": true,
          "errors": [],
          "warnings": ["Aviso 1"],
          "suggestions": ["Sugestão 1"],
          "score": 85,
          "summary": "Seção aprovada com ressalvas"
        }
        '''

        result = validator._parse_validation_response(json_response)

        assert result['is_valid'] is True
        assert result['score'] == 85
        assert len(result['warnings']) == 1
        assert len(result['suggestions']) == 1

    def test_parse_validation_response_invalid_json(self, mock_claude_service, mock_kb_service):
        """Testa parsing de JSON inválido."""
        validator = Section01Validator(
            claude_service=mock_claude_service,
            kb_service=mock_kb_service
        )

        with pytest.raises(ValueError, match="JSON"):
            validator._parse_validation_response("não é json")

    def test_combine_validations(self, mock_claude_service, mock_kb_service):
        """Testa combinação de validações."""
        validator = Section01Validator(
            claude_service=mock_claude_service,
            kb_service=mock_kb_service
        )

        structural = {
            'is_valid': True,
            'errors': [],
            'warnings': ['Aviso estrutural'],
            'suggestions': [],
            'score': 90
        }

        semantic = {
            'is_valid': True,
            'errors': [],
            'warnings': ['Aviso semântico'],
            'suggestions': ['Sugestão semântica'],
            'score': 80,
            'summary': 'Validação OK'
        }

        result = validator._combine_validations(structural, semantic)

        assert result['is_valid'] is True
        assert result['structural_score'] == 90
        assert result['semantic_score'] == 80
        # Score final: 90 * 0.3 + 80 * 0.7 = 27 + 56 = 83
        assert result['score'] == 83
        assert len(result['warnings']) == 2

    def test_combine_validations_one_invalid(self, mock_claude_service, mock_kb_service):
        """Testa combinação quando uma validação falha."""
        validator = Section01Validator(
            claude_service=mock_claude_service,
            kb_service=mock_kb_service
        )

        structural = {
            'is_valid': False,
            'errors': ['Erro estrutural'],
            'warnings': [],
            'suggestions': [],
            'score': 30
        }

        semantic = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': [],
            'score': 90,
            'summary': 'Validação OK'
        }

        result = validator._combine_validations(structural, semantic)

        assert result['is_valid'] is False  # Falha se qualquer uma falhar
        assert len(result['errors']) == 1

    @patch.object(Section01Validator, '_validate_with_claude')
    def test_generate_with_structural_failure(self, mock_validate_claude, mock_claude_service, mock_kb_service):
        """Testa que validação para se estrutural falhar."""
        validator = Section01Validator(
            claude_service=mock_claude_service,
            kb_service=mock_kb_service
        )

        # Conteúdo vazio falha na validação estrutural
        result = validator.generate(
            content="",
            objective="Objetivo teste",
            collection_name="test_collection"
        )

        assert result['is_valid'] is False
        # Não deve chamar Claude se estrutural falhar
        mock_validate_claude.assert_not_called()

    @patch.object(Section01Validator, '_validate_with_claude')
    def test_generate_success(self, mock_validate_claude, mock_claude_service, mock_kb_service):
        """Testa validação completa bem-sucedida."""
        # Mock da validação semântica
        mock_validate_claude.return_value = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': ['Sugestão de melhoria'],
            'score': 85,
            'summary': 'Seção aprovada'
        }

        validator = Section01Validator(
            claude_service=mock_claude_service,
            kb_service=mock_kb_service
        )
        content = " ".join(["palavra"] * 400)  # Conteúdo válido

        result = validator.generate(
            content=content,
            objective="Contratar serviço",
            collection_name="test_collection"
        )

        assert result['is_valid'] is True
        assert 'reasoning' in result
        assert 'score' in result

        mock_validate_claude.assert_called_once()
