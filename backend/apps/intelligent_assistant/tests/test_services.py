"""
Testes para os servicos do Assistente Inteligente.
Cobre: ClaudeService, DocumentProcessor, KnowledgeBase, DynamicGraphBuilder,
DocumentExportService, PDFService.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from pathlib import Path
from io import BytesIO
from apps.intelligent_assistant.services import (
    ClaudeService,
    DocumentProcessorService,
    KnowledgeBaseService,
)
from apps.intelligent_assistant.services.dynamic_graph_builder import (
    DynamicGraphBuilder, DynamicSectionStatus
)


@pytest.mark.unit
@pytest.mark.service
class TestClaudeService:
    """Testes para o ClaudeService."""

    def test_init_with_api_key(self):
        service = ClaudeService(api_key="test-key-123")
        assert service.api_key == "test-key-123"
        assert service.model == "claude-3-5-sonnet-20241022"

    def test_init_without_api_key_raises_error(self):
        with patch('apps.intelligent_assistant.services.claude_service.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = None
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY nao configurada"):
                ClaudeService()

    @patch('apps.intelligent_assistant.services.claude_service.Anthropic')
    def test_generate_success(self, mock_anthropic):
        mock_response = Mock()
        mock_response.content = [Mock(text="Texto gerado pelo Claude")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)
        mock_response.model = "claude-3-5-sonnet-20241022"

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        service = ClaudeService(api_key="test-key")
        result = service.generate(
            user_prompt="Test prompt",
            system_prompt="System prompt"
        )

        assert result['content'] == "Texto gerado pelo Claude"
        assert result['usage']['input_tokens'] == 100
        assert result['usage']['output_tokens'] == 50
        assert result['model'] == "claude-3-5-sonnet-20241022"

    def test_generate_empty_prompt_raises_error(self):
        service = ClaudeService(api_key="test-key")
        with pytest.raises(ValueError, match="user_prompt nao pode ser vazio"):
            service.generate(user_prompt="")

    def test_estimate_tokens(self):
        service = ClaudeService(api_key="test-key")
        text = "a" * 100
        estimated = service.estimate_tokens(text)
        assert estimated == 25

    def test_build_prompt_with_context(self):
        service = ClaudeService(api_key="test-key")
        prompt = service._build_prompt_with_context(
            user_prompt="Test",
            context_documents=["Doc 1", "Doc 2"]
        )
        assert "## DOCUMENTOS DE REFERENCIA" in prompt
        assert "Doc 1" in prompt
        assert "Doc 2" in prompt
        assert "Test" in prompt


@pytest.mark.unit
@pytest.mark.service
class TestDocumentProcessorService:
    """Testes para o DocumentProcessorService."""

    def test_init(self):
        service = DocumentProcessorService()
        assert service.SUPPORTED_EXTENSIONS == {'.pdf', '.docx', '.txt'}

    def test_extract_text_file_not_found(self):
        service = DocumentProcessorService()
        with pytest.raises(FileNotFoundError):
            service.extract_text("/caminho/inexistente.pdf")

    def test_extract_text_unsupported_extension(self, tmp_path):
        test_file = tmp_path / "test.xlsx"
        test_file.write_text("conteudo")
        service = DocumentProcessorService()
        with pytest.raises(ValueError, match="Tipo de arquivo nao suportado"):
            service.extract_text(str(test_file))

    def test_extract_from_txt(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_content = "Este e um teste de extracao de texto."
        test_file.write_text(test_content, encoding='utf-8')
        service = DocumentProcessorService()
        result = service.extract_text(str(test_file))
        assert result['text'] == test_content
        assert result['file_type'] == 'txt'
        assert result['char_count'] == len(test_content)
        assert result['metadata']['encoding'] == 'utf-8'

    def test_extract_from_empty_file(self, tmp_path):
        test_file = tmp_path / "empty.txt"
        test_file.write_text("", encoding='utf-8')
        service = DocumentProcessorService()
        result = service.extract_text(str(test_file))
        assert result['text'] == ''
        assert result['char_count'] == 0
        assert result['file_type'] == 'txt'

    def test_chunk_text(self):
        service = DocumentProcessorService()
        text = "a" * 2000
        chunks = service.chunk_text(text, chunk_size=500, overlap=100)
        assert len(chunks) > 1
        assert all(len(chunk) <= 600 for chunk in chunks)

    def test_chunk_text_default_params(self):
        service = DocumentProcessorService()
        text = "Palavra repetida " * 100
        chunks = service.chunk_text(text)
        assert len(chunks) >= 1

    def test_chunk_text_smaller_than_chunk_size(self):
        service = DocumentProcessorService()
        text = "Texto curto."
        chunks = service.chunk_text(text, chunk_size=1000)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_validate_extraction_empty_text(self):
        service = DocumentProcessorService()
        result = service.validate_extraction({'text': '', 'char_count': 0})
        assert result['is_valid'] is False
        assert len(result['issues']) > 0

    def test_validate_extraction_short_text(self):
        service = DocumentProcessorService()
        result = service.validate_extraction({'text': 'Texto curto', 'char_count': 11})
        assert result['is_valid'] is True
        assert len(result['warnings']) > 0

    def test_validate_extraction_good(self):
        service = DocumentProcessorService()
        result = service.validate_extraction({'text': 'A' * 500, 'char_count': 500})
        assert result['is_valid'] is True

    def test_supported_extensions(self):
        service = DocumentProcessorService()
        assert '.pdf' in service.SUPPORTED_EXTENSIONS
        assert '.docx' in service.SUPPORTED_EXTENSIONS
        assert '.txt' in service.SUPPORTED_EXTENSIONS


@pytest.mark.unit
@pytest.mark.service
class TestKnowledgeBaseService:
    """Testes para o KnowledgeBaseService."""

    def test_singleton_pattern(self):
        service1 = KnowledgeBaseService()
        service2 = KnowledgeBaseService()
        assert service1 is service2

    def test_get_instance(self):
        service = KnowledgeBaseService.get_instance()
        assert isinstance(service, KnowledgeBaseService)

    def test_create_collection(self):
        service = KnowledgeBaseService()
        session_id = "test-session-123"
        collection_name = service.create_collection(session_id)
        assert "session_" in collection_name
        assert collection_name in service.list_collections()
        service.delete_collection(collection_name)

    def test_add_documents(self):
        service = KnowledgeBaseService()
        session_id = "test-add-docs-123"
        collection_name = service.create_collection(session_id)
        documents = ["Documento 1", "Documento 2"]
        count = service.add_documents(collection_name, documents)
        assert count == 2
        info = service.get_collection_info(collection_name)
        assert info['count'] == 2
        service.delete_collection(collection_name)

    def test_add_documents_empty_list_raises_error(self):
        service = KnowledgeBaseService()
        session_id = "test-empty-123"
        collection_name = service.create_collection(session_id)
        with pytest.raises(ValueError, match="Lista de documentos nao pode ser vazia"):
            service.add_documents(collection_name, [])
        service.delete_collection(collection_name)

    def test_query_documents(self):
        service = KnowledgeBaseService()
        session_id = "test-query-123"
        collection_name = service.create_collection(session_id)
        documents = [
            "Python e uma linguagem de programacao",
            "JavaScript e usado para web",
            "Python e muito popular"
        ]
        service.add_documents(collection_name, documents)
        results = service.query(collection_name, "Python programacao", n_results=2)
        assert len(results['documents']) == 2
        assert any('Python' in doc for doc in results['documents'])
        service.delete_collection(collection_name)

    def test_delete_collection(self):
        service = KnowledgeBaseService()
        session_id = "test-delete-123"
        collection_name = service.create_collection(session_id)
        assert collection_name in service.list_collections()
        service.delete_collection(collection_name)
        assert collection_name not in service.list_collections()

    def test_list_collections(self):
        service = KnowledgeBaseService()
        session1 = "test-list-1"
        session2 = "test-list-2"
        col1 = service.create_collection(session1)
        col2 = service.create_collection(session2)
        collections = service.list_collections()
        assert col1 in collections
        assert col2 in collections
        service.delete_collection(col1)
        service.delete_collection(col2)


@pytest.mark.unit
class TestDynamicGraphBuilder:
    """Testes para o DynamicGraphBuilder."""

    def test_init_with_services(self):
        claude = MagicMock()
        kb = MagicMock()
        llm = MagicMock()
        builder = DynamicGraphBuilder(
            claude_service=claude, kb_service=kb, llm_service=llm,
        )
        assert builder.claude_service == claude
        assert builder.kb_service == kb
        assert builder.llm_service == llm

    def test_init_without_services(self):
        builder = DynamicGraphBuilder()
        assert builder.claude_service is None
        assert builder.kb_service is None
        assert builder.llm_service is None

    def test_dynamic_section_status_enum(self):
        assert DynamicSectionStatus.PENDING.value == 'pending'
        assert DynamicSectionStatus.GENERATING.value == 'generating'
        assert DynamicSectionStatus.VALIDATING.value == 'validating'
        assert DynamicSectionStatus.VALID.value == 'valid'
        assert DynamicSectionStatus.INVALID.value == 'invalid'
        assert DynamicSectionStatus.ERROR.value == 'error'
        assert DynamicSectionStatus.SKIPPED.value == 'skipped'

    @patch('apps.intelligent_assistant.services.dynamic_graph_builder.DocumentBlueprint')
    def test_create_runner_no_blueprint(self, mock_bp):
        mock_bp.objects.filter.return_value.first.return_value = None
        builder = DynamicGraphBuilder()
        with pytest.raises(Exception):
            builder.create_runner()

    @patch('apps.intelligent_assistant.services.dynamic_graph_builder.DocumentBlueprint')
    def test_create_runner_by_id_not_found(self, mock_bp):
        mock_bp.objects.filter.return_value.first.return_value = None
        builder = DynamicGraphBuilder()
        with pytest.raises(Exception):
            builder.create_runner(blueprint_id='00000000-0000-0000-0000-000000000000')


@pytest.mark.unit
class TestDocumentExportService:
    """Testes para o DocumentExportService."""

    def test_import_service(self):
        from apps.intelligent_assistant.services.document_export_service import DocumentExportService
        assert DocumentExportService is not None

    def test_parse_html_table(self):
        from apps.intelligent_assistant.services.document_export_service import DocumentExportService
        html = '<table><thead><tr><th>Nome</th><th>Valor</th></tr></thead><tbody><tr><td>Item 1</td><td>R$ 100</td></tr></tbody></table>'
        result = DocumentExportService._parse_html_table(html)
        assert result is not None
        assert result['type'] == 'table'
        assert result['cols'] == 2
        assert result['n_rows'] == 2

    def test_parse_html_table_invalid(self):
        from apps.intelligent_assistant.services.document_export_service import DocumentExportService
        result = DocumentExportService._parse_html_table('<p>Nao e tabela</p>')
        assert result is None

    def test_html_block_regex(self):
        from apps.intelligent_assistant.services.document_export_service import _HTML_BLOCK_OPEN_RE
        assert _HTML_BLOCK_OPEN_RE.match('<p>texto</p>')
        assert _HTML_BLOCK_OPEN_RE.match('<ul><li>item</li></ul>')
        assert not _HTML_BLOCK_OPEN_RE.match('texto puro')


@pytest.mark.unit
class TestPDFService:
    """Testes para o PDFService."""

    def test_import_service(self):
        from apps.intelligent_assistant.services.pdf_service import PDFService
        assert PDFService is not None

    def test_default_css_exists(self):
        from apps.intelligent_assistant.services.pdf_service import PDFService
        service = PDFService()
        css = service.DEFAULT_CSS
        assert '@page' in css
        assert 'size: A4' in css
        assert 'Times New Roman' in css
        assert 'margin' in css

    @patch('apps.intelligent_assistant.services.pdf_service.markdown.markdown')
    def test_markdown_to_html(self, mock_markdown):
        mock_markdown.return_value = '<p>HTML convertido</p>'
        from apps.intelligent_assistant.services.pdf_service import PDFService
        service = PDFService()
        html = service._markdown_to_html('# Titulo\n\nParagrafo.')
        assert '<p>HTML convertido</p>' in html

    @patch('apps.intelligent_assistant.services.pdf_service.PDFService._markdown_to_html')
    @patch('apps.intelligent_assistant.services.pdf_service.PDFService._render_pdf')
    def test_markdown_to_pdf(self, mock_render, mock_md_to_html):
        mock_md_to_html.return_value = '<html><body><h1>Test</h1></body></html>'
        mock_render.return_value = b'%PDF-1.4 simulated pdf content'
        from apps.intelligent_assistant.services.pdf_service import PDFService
        service = PDFService()
        result = service.markdown_to_pdf('# Teste', 'Documento Teste')
        assert result == b'%PDF-1.4 simulated pdf content'
        mock_md_to_html.assert_called_once()
        mock_render.assert_called_once()
