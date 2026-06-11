"""
Testes para os models do Assistente Inteligente.
"""
import pytest
from apps.intelligent_assistant.models import (
    IntelligentSession,
    UploadedDocument,
    GeneratedSection,
    GeneratedDocument,
)


@pytest.mark.unit
@pytest.mark.django_db
class TestIntelligentSession:
    """Testes para o modelo IntelligentSession."""

    def test_create_session(self, user):
        """Testa a criação de uma sessão."""
        session = IntelligentSession.objects.create(
            user=user,
            objective='Testar criação de sessão',
            document_type='etp',
            status='initialized',
            kb_collection_id='test_001'
        )

        assert session.id is not None
        assert session.user == user
        assert session.objective == 'Testar criação de sessão'
        assert session.document_type == 'etp'
        assert session.status == 'initialized'
        assert session.kb_collection_id == 'test_001'

    def test_session_str_representation(self, intelligent_session):
        """Testa a representação em string da sessão."""
        str_repr = str(intelligent_session)
        assert 'Estudo Técnico Preliminar' in str_repr
        assert intelligent_session.user.username in str_repr

    def test_session_ordering(self, user):
        """Testa a ordenação das sessões por data de criação."""
        session1 = IntelligentSession.objects.create(
            user=user,
            objective='Primeira sessão',
            kb_collection_id='test_001'
        )
        session2 = IntelligentSession.objects.create(
            user=user,
            objective='Segunda sessão',
            kb_collection_id='test_002'
        )

        sessions = IntelligentSession.objects.all()
        assert sessions[0] == session2  # Mais recente primeiro
        assert sessions[1] == session1


@pytest.mark.unit
@pytest.mark.django_db
class TestUploadedDocument:
    """Testes para o modelo UploadedDocument."""

    def test_create_uploaded_document(self, intelligent_session):
        """Testa a criação de um documento enviado."""
        doc = UploadedDocument.objects.create(
            session=intelligent_session,
            filename='test.pdf',
            file_type='pdf',
            file_size=1024,
            extracted_text='Texto teste',
            extraction_status='completed'
        )

        assert doc.id is not None
        assert doc.session == intelligent_session
        assert doc.filename == 'test.pdf'
        assert doc.file_type == 'pdf'
        assert doc.extraction_status == 'completed'

    def test_document_str_representation(self, uploaded_document):
        """Testa a representação em string do documento."""
        str_repr = str(uploaded_document)
        assert uploaded_document.filename in str_repr


@pytest.mark.unit
@pytest.mark.django_db
class TestGeneratedSection:
    """Testes para o modelo GeneratedSection."""

    def test_create_generated_section(self, intelligent_session):
        """Testa a criação de uma seção gerada."""
        section = GeneratedSection.objects.create(
            session=intelligent_session,
            section_number=1,
            section_name='Teste',
            content='Conteúdo de teste',
            is_valid=True,
            validation_errors=[],
            validation_warnings=[],
            generation_attempts=1
        )

        assert section.id is not None
        assert section.session == intelligent_session
        assert section.section_number == 1
        assert section.is_valid is True

    def test_section_unique_constraint(self, intelligent_session):
        """Testa que não é possível criar duas seções com mesmo número na mesma sessão."""
        GeneratedSection.objects.create(
            session=intelligent_session,
            section_number=1,
            section_name='Primeira',
            content='Conteúdo 1',
            generation_attempts=1
        )

        with pytest.raises(Exception):  # IntegrityError
            GeneratedSection.objects.create(
                session=intelligent_session,
                section_number=1,
                section_name='Duplicada',
                content='Conteúdo 2',
                generation_attempts=1
            )

    def test_section_ordering(self, intelligent_session):
        """Testa a ordenação das seções por número."""
        section2 = GeneratedSection.objects.create(
            session=intelligent_session,
            section_number=2,
            section_name='Segunda',
            content='Conteúdo 2',
            generation_attempts=1
        )
        section1 = GeneratedSection.objects.create(
            session=intelligent_session,
            section_number=1,
            section_name='Primeira',
            content='Conteúdo 1',
            generation_attempts=1
        )

        sections = GeneratedSection.objects.filter(session=intelligent_session)
        assert sections[0] == section1  # Ordenado por section_number
        assert sections[1] == section2


@pytest.mark.unit
@pytest.mark.django_db
class TestGeneratedDocument:
    """Testes para o modelo GeneratedDocument."""

    def test_create_generated_document(self, intelligent_session):
        """Testa a criação de um documento gerado."""
        doc = GeneratedDocument.objects.create(
            session=intelligent_session,
            metadata={'version': '1.0'},
            file_size_docx=2048
        )

        assert doc.id is not None
        assert doc.session == intelligent_session
        assert doc.metadata == {'version': '1.0'}
        assert doc.file_size_docx == 2048
