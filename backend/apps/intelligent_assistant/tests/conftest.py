"""
Fixtures compartilhadas para testes do Assistente Inteligente.
"""
import pytest
from django.contrib.auth import get_user_model
from apps.intelligent_assistant.models import (
    IntelligentSession,
    UploadedDocument,
    GeneratedSection,
    GeneratedDocument,
)

User = get_user_model()


@pytest.fixture
def user(db):
    """Cria um usuário para testes."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def intelligent_session(db, user):
    """Cria uma sessão do assistente inteligente."""
    return IntelligentSession.objects.create(
        user=user,
        objective='Contratar serviço de desenvolvimento de software',
        document_type='etp',
        status='initialized',
        kb_collection_id='test_collection_001'
    )


@pytest.fixture
def uploaded_document(db, intelligent_session):
    """Cria um documento enviado para teste."""
    return UploadedDocument.objects.create(
        session=intelligent_session,
        filename='documento_teste.pdf',
        file_type='pdf',
        file_size=1024000,
        extracted_text='Este é um texto de teste extraído do PDF.',
        extraction_status='completed'
    )


@pytest.fixture
def generated_section(db, intelligent_session):
    """Cria uma seção gerada para teste."""
    return GeneratedSection.objects.create(
        session=intelligent_session,
        section_number=1,
        section_name='Descrição da Necessidade da Contratação',
        content='Conteúdo de teste da seção 1.',
        is_valid=True,
        validation_errors=[],
        validation_warnings=[],
        agent_reasoning='Raciocínio do agente de teste.',
        generation_attempts=1
    )


@pytest.fixture
def mock_claude_response():
    """Mock de resposta do Claude."""
    return {
        'content': 'Resposta de teste do Claude',
        'usage': {
            'input_tokens': 100,
            'output_tokens': 50
        }
    }


@pytest.fixture
def sample_etp_text():
    """Texto de exemplo de um ETP."""
    return """
    ESTUDO TÉCNICO PRELIMINAR

    1. DESCRIÇÃO DA NECESSIDADE DA CONTRATAÇÃO
    O presente estudo visa fundamentar a contratação de serviços de
    desenvolvimento de software para atender às necessidades do município.

    2. OBJETO DA CONTRATAÇÃO
    Contratação de serviço de desenvolvimento de software.
    """


@pytest.fixture
def mock_chromadb_collection():
    """Mock de coleção do ChromaDB."""
    class MockCollection:
        def add(self, documents, ids, metadatas):
            pass

        def query(self, query_texts, n_results=5):
            return {
                'documents': [['Documento de teste 1', 'Documento de teste 2']],
                'metadatas': [[{'source': 'test1'}, {'source': 'test2'}]],
                'distances': [[0.1, 0.2]]
            }

    return MockCollection()


@pytest.fixture
def mock_claude_service():
    """Mock do ClaudeService para testes."""
    from unittest.mock import Mock
    service = Mock()
    service.generate.return_value = {
        'content': 'Resposta mockada do Claude',
        'usage': {'input_tokens': 100, 'output_tokens': 50},
        'model': 'claude-3-5-sonnet-20241022'
    }
    return service


@pytest.fixture
def mock_kb_service():
    """Mock do KnowledgeBaseService para testes."""
    from unittest.mock import Mock
    service = Mock()
    service.query.return_value = {
        'documents': ['Doc 1', 'Doc 2'],
        'metadatas': [{'source': 'test1'}, {'source': 'test2'}],
        'distances': [0.1, 0.2],
        'ids': ['id1', 'id2']
    }
    return service
