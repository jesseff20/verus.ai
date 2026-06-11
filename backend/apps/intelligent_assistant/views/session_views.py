"""
Views para CRUD de sessões do Assistente Inteligente (sistema legado).
"""
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse

from ..models import IntelligentSession, DocumentBlueprint
from ..services.pgvector_service import PgVectorService
from apps.core.models import DocumentType
from ..utils import normalize_subsection_breaks

logger = logging.getLogger(__name__)


@extend_schema(
    summary="Criar Sessão do Assistente",
    description="""
    Cria uma nova sessão do assistente inteligente.

    Uma sessão é o contexto de trabalho onde:
    - Documentos são enviados e processados
    - Embeddings são gerados e armazenados
    - O ETP é gerado com base nos documentos da sessão
    """,
    tags=["Assistente Inteligente - Sessões"],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'objective': {
                    'type': 'string',
                    'description': 'Objetivo da contratação'
                },
                'document_type': {
                    'type': 'string',
                    'enum': ['etp', 'edital', 'contrato'],
                    'default': 'etp'
                }
            },
            'required': ['objective']
        }
    },
    responses={
        201: OpenApiResponse(description="Sessão criada com sucesso"),
        400: OpenApiResponse(description="Dados inválidos")
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_session(request):
    """
    Cria uma nova sessão do assistente inteligente.

    POST /api/v1/intelligent-assistant/sessions/
    """
    objective = request.data.get('objective', '').strip()
    document_type = request.data.get('document_type', '')
    blueprint_id = request.data.get('blueprint_id')
    parent_etp_session_id = request.data.get('parent_etp_session_id')

    if not objective:
        return Response({
            'error': 'O campo "objective" é obrigatório'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Buscar blueprint antes de validar document_type para poder derivá-lo automaticamente
    blueprint = None
    if blueprint_id:
        try:
            blueprint = DocumentBlueprint.objects.select_related('document_type').get(
                id=blueprint_id, is_active=True
            )
            # Deriva document_type do blueprint - evita divergência frontend/backend
            if blueprint.document_type:
                document_type = blueprint.document_type.code
        except DocumentBlueprint.DoesNotExist:
            return Response({
                'error': 'Blueprint não encontrado ou inativo'
            }, status=status.HTTP_400_BAD_REQUEST)

    # Validar document_type contra a tabela centralizada core.DocumentType
    # (fonte unica da verdade - adicionar tipo novo NAO requer migration nem
    # editar Python; basta inserir registro em DocumentType via admin/seed).
    valid_document_types = list(
        DocumentType.objects.filter(is_active=True).values_list('code', flat=True)
    )
    if document_type not in valid_document_types:
        return Response({
            'error': f'document_type deve ser um de: {", ".join(valid_document_types)}'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Sessão pai opcional — permite vincular peças que referenciam outro documento
    parent_etp = None
    if parent_etp_session_id:
        try:
            parent_etp = IntelligentSession.objects.get(
                id=parent_etp_session_id,
                user=request.user,
            )
        except IntelligentSession.DoesNotExist:
            return Response({
                'error': 'parent_etp_session_id não encontrado ou pertence a outro usuário'
            }, status=status.HTTP_400_BAD_REQUEST)

    try:
        session = IntelligentSession.objects.create(
            user=request.user,
            objective=objective,
            document_type=document_type,
            blueprint=blueprint,
            status='initialized',
            kb_collection_id='',  # Será usado para referência, mas não para ChromaDB
            parent_etp_session=parent_etp,
        )

        return Response({
            'id': str(session.id),
            'objective': session.objective,
            'document_type': session.document_type,
            'blueprint_id': str(blueprint.id) if blueprint else None,
            'blueprint_name': blueprint.name if blueprint else None,
            'status': session.status,
            'parent_etp_session_id': str(parent_etp.id) if parent_etp else None,
            'created_at': session.created_at.isoformat()
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'error': 'Erro ao criar sessão',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Listar Sessões do Usuário",
    description="Lista todas as sessões do usuário autenticado",
    tags=["Assistente Inteligente - Sessões"],
    responses={200: OpenApiResponse(description="Lista de sessões")}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_sessions(request):
    """
    Lista sessões do usuário.

    GET /api/v1/intelligent-assistant/sessions/
    """
    from django.db.models import Count
    document_type = request.query_params.get('document_type')
    qs = (
        IntelligentSession.objects
        .filter(user=request.user)
        .select_related('blueprint', 'blueprint__document_type')
        .annotate(documents_count=Count('uploaded_documents'))
        .order_by('-created_at')
    )
    if document_type:
        qs = qs.filter(document_type=document_type)
    sessions = qs[:20]

    return Response({
        'sessions': [
            {
                'id': str(s.id),
                'objective': s.objective[:100] + '...' if len(s.objective) > 100 else s.objective,
                'document_type': s.document_type,
                'status': s.status,
                'documents_count': s.documents_count,
                'created_at': s.created_at.isoformat()
            }
            for s in sessions
        ]
    })


@extend_schema(
    summary="Obter ou Atualizar Sessão",
    description="GET retorna detalhes, PATCH atualiza campos editáveis (objective)",
    tags=["Assistente Inteligente - Sessões"],
    responses={
        200: OpenApiResponse(description="Detalhes da sessão"),
        404: OpenApiResponse(description="Sessão não encontrada")
    }
)
@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def get_session(request, session_id):
    """
    GET: Obtém detalhes de uma sessão.
    PATCH: Atualiza campos editáveis (objective).

    /api/v1/intelligent-assistant/sessions/{session_id}/
    """
    try:
        session = IntelligentSession.objects.get(
            id=session_id,
            user=request.user
        )
    except IntelligentSession.DoesNotExist:
        return Response({
            'error': 'Sessão não encontrada'
        }, status=status.HTTP_404_NOT_FOUND)

    # PATCH: atualizar objetivo
    if request.method == 'PATCH':
        objective = request.data.get('objective')
        if objective is not None:
            objective = objective.strip()
            if not objective:
                return Response({
                    'error': 'O objetivo não pode ser vazio'
                }, status=status.HTTP_400_BAD_REQUEST)
            session.objective = objective
            session.save(update_fields=['objective', 'updated_at'])
        return Response({
            'id': str(session.id),
            'objective': session.objective,
            'updated_at': session.updated_at.isoformat(),
        })

    # GET: buscar estatísticas de embeddings
    pgvector_service = PgVectorService()
    stats = pgvector_service.get_session_stats(session)

    # Dados do blueprint
    blueprint_data = None
    if session.blueprint:
        blueprint_data = {
            'id': str(session.blueprint.id),
            'name': session.blueprint.name,
            'document_type': session.blueprint.document_type.code if session.blueprint.document_type else None,
            'document_type_display': session.blueprint.document_type.name if session.blueprint.document_type else None,
            'section_count': session.blueprint.section_count,
        }

    return Response({
        'id': str(session.id),
        'objective': session.objective,
        'document_type': session.document_type,
        'blueprint': blueprint_data,
        'blueprint_id': str(session.blueprint.id) if session.blueprint else None,
        'blueprint_name': session.blueprint.name if session.blueprint else None,
        'status': session.status,
        'error_message': session.error_message,
        'created_at': session.created_at.isoformat(),
        'updated_at': session.updated_at.isoformat(),
        'generation_session_id': str(latest_gs.id) if (latest_gs := session.generation_sessions.order_by('-created_at').first()) else None,
        'documents': [
            {
                'id': str(doc.id),
                'filename': doc.filename,
                'file_type': doc.file_type,
                'file_size': doc.file_size,
                'extraction_status': doc.extraction_status,
                'uploaded_at': doc.uploaded_at.isoformat()
            }
            for doc in session.uploaded_documents.all()
        ],
        'embedding_stats': stats,
        'sections': [
            {
                'section_number': sec.section_number,
                'section_name': sec.section_name,
                'is_valid': sec.is_valid,
                'created_at': sec.created_at.isoformat()
            }
            for sec in session.generated_sections.all()
        ],
        'generated_documents': [
            {
                'id': str(doc.id),
                'title': doc.title or f"Estudo Técnico Preliminar - {session.objective[:50]}",
                'pdf_url': doc.pdf_url,
                'markdown_content': normalize_subsection_breaks(doc.markdown_content),
                'created_at': doc.generated_at.isoformat() if doc.generated_at else None,
                'metadata': doc.metadata or {},
            }
            for doc in session.generated_documents.all().order_by('-generated_at')
        ]
    })


@extend_schema(
    summary="Deletar Sessão",
    description="Remove uma sessão e todos os seus dados (documentos, embeddings)",
    tags=["Assistente Inteligente - Sessões"],
    responses={
        204: OpenApiResponse(description="Sessão removida"),
        404: OpenApiResponse(description="Sessão não encontrada")
    }
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_session(request, session_id):
    """
    Remove uma sessão e todos os dados associados.

    DELETE /api/v1/intelligent-assistant/sessions/{session_id}/
    """
    try:
        session = IntelligentSession.objects.get(
            id=session_id,
            user=request.user
        )
    except IntelligentSession.DoesNotExist:
        return Response({
            'error': 'Sessão não encontrada'
        }, status=status.HTTP_404_NOT_FOUND)

    # Deletar embeddings primeiro
    pgvector_service = PgVectorService()
    embeddings_deleted = pgvector_service.delete_session_embeddings(session)

    # Deletar sessão (cascade deleta documentos)
    session.delete()

    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    summary="Listar documentos filhos vinculados a uma sessão",
    description="""
    Retorna lista paginada dos anexos (child_attachments) vinculados a um
    ETP ou TR especifico. Cada anexo e uma IntelligentSession cujo
    parent_etp_session aponta para esta sessao.

    Suporta paginacao via query params:
        ?page=N (1-indexed, default=1)
        ?page_size=M (default=10, max=50)
    """,
    tags=["Assistente Inteligente - Sessões"],
    responses={
        200: OpenApiResponse(description="Lista paginada de anexos"),
        404: OpenApiResponse(description="Session nao encontrada ou pertence a outro usuario"),
    },
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_session_attachments(request, session_id):
    """
    Lista anexos vinculados a um session (ETP ou TR), paginada.

    GET /api/v1/intelligent-assistant/sessions/<uuid:session_id>/attachments/
    """
    # Confere que o session pai existe e pertence ao user
    try:
        parent = IntelligentSession.objects.get(id=session_id, user=request.user)
    except IntelligentSession.DoesNotExist:
        return Response(
            {'error': 'Sessao nao encontrada ou pertence a outro usuario'},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Pega filhos diretos via parent_etp_session (campo aceita ETP ou TR
    # conforme tipo do filho - vide Roadmap_Controle_Sessoes.md, Fase A).
    qs = IntelligentSession.objects.filter(
        parent_etp_session=parent,
        user=request.user,
    ).select_related('blueprint', 'blueprint__document_type').order_by('-created_at')

    # Paginacao manual (segue padrao das listas existentes deste app)
    try:
        page = max(1, int(request.query_params.get('page', '1')))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = min(50, max(1, int(request.query_params.get('page_size', '10'))))
    except (TypeError, ValueError):
        page_size = 10

    total = qs.count()
    start = (page - 1) * page_size
    end = start + page_size
    items = qs[start:end]

    return Response({
        'parent_session_id': str(parent.id),
        'parent_document_type': parent.document_type,
        'attachments': [
            {
                'id': str(s.id),
                'objective': s.objective,
                'objective_preview': (s.objective[:200] + '...') if len(s.objective or '') > 200 else (s.objective or ''),
                'document_type': s.document_type,
                'document_type_display': (
                    s.blueprint.document_type.short_name
                    or s.blueprint.document_type.name
                ) if s.blueprint and s.blueprint.document_type else s.document_type,
                'blueprint_name': s.blueprint.name if s.blueprint else None,
                'status': s.status,
                'created_at': s.created_at.isoformat(),
            }
            for s in items
        ],
        'page': page,
        'page_size': page_size,
        'total': total,
        'total_pages': (total + page_size - 1) // page_size if page_size else 1,
        'has_next': end < total,
        'has_previous': page > 1,
    })


@extend_schema(
    summary="Preview consolidado de uma sessao",
    description="""
    Retorna tudo que o frontend precisa para abrir um modal de visualizacao
    de uma sessao (anexo, ETP, TR, etc.) sem precisar navegar de pagina:

      - markdown_content (HTML/Markdown ja sanitizado pelo gerador)
      - URLs publicas dos arquivos no R2 (PDF/DOCX) quando ja gerados
      - generated_doc_id para acionar regeracao on-the-fly de PDF/DOCX/ODT

    Pensado para o card "Anexos vinculados" do ResultPhase: clicar em um
    anexo abre modal com o conteudo do banco + downloads do R2, sem
    coreografia de URL params (session/phase/doc/generation_session).
    """,
    tags=["Assistente Inteligente - Sessões"],
    responses={
        200: OpenApiResponse(description="Preview consolidado"),
        404: OpenApiResponse(description="Sessao nao encontrada ou pertence a outro usuario"),
    },
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def preview_session(request, session_id):
    """
    GET /api/v1/intelligent-assistant/sessions/<uuid:session_id>/preview/
    """
    try:
        session = (
            IntelligentSession.objects
            .select_related('blueprint', 'blueprint__document_type')
            .get(id=session_id, user=request.user)
        )
    except IntelligentSession.DoesNotExist:
        return Response(
            {'error': 'Sessao nao encontrada ou pertence a outro usuario'},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Pega o GeneratedDocument mais recente (ordering = ['-generated_at'])
    latest_doc = session.generated_documents.order_by('-generated_at').first()

    document_type_display = session.document_type
    if session.blueprint and session.blueprint.document_type:
        document_type_display = (
            session.blueprint.document_type.short_name
            or session.blueprint.document_type.name
        )

    payload = {
        'session_id': str(session.id),
        'document_type': session.document_type,
        'document_type_display': document_type_display,
        'objective': session.objective or '',
        'status': session.status,
        'blueprint_name': session.blueprint.name if session.blueprint else None,
        'has_generated_doc': bool(latest_doc),
    }

    if latest_doc:
        # Sections vem da ultima GenerationSession da IntelligentSession -
        # mesmo lugar de onde o ResultPhase pega `generatedContent`. Sao
        # SectionGeneration.content (HTML formatado por secao), nao o
        # markdown_content concatenado (que mistura `## ` markdown + <p>
        # HTML e nao renderiza bem direto via DOMPurify).
        latest_gs = (
            session.generation_sessions
            .order_by('-created_at')
            .prefetch_related('section_generations__section')
            .first()
        )
        sections_data = []
        if latest_gs:
            for sg in latest_gs.section_generations.select_related('section').order_by(
                'section__section_number'
            ):
                if not sg.content:
                    continue
                sections_data.append({
                    'section_number': sg.section.section_number,
                    'section_name': sg.section.section_name,
                    'content': normalize_subsection_breaks(sg.content),
                })

        # Metadata do export atual (PDF/DOCX/ODT). pdf_url/docx_url so existem
        # quando o upload pra R2 (Celery task) terminou. Se ainda nao existem,
        # frontend mostra botao "Baixar" que aciona o endpoint de geracao
        # on-the-fly (/documents/<id>/generate-pdf/, etc.) - via POST.
        payload.update({
            'generated_doc_id': str(latest_doc.id),
            'title': latest_doc.title or '',
            'sections': sections_data,
            'pdf_url': latest_doc.pdf_url or None,
            'docx_url': latest_doc.docx_url or None,
            'pdf_generated': bool(latest_doc.pdf_generated),
            'docx_generated': bool(latest_doc.docx_generated),
            'generated_at': latest_doc.generated_at.isoformat(),
            'updated_at': latest_doc.updated_at.isoformat(),
        })
    else:
        payload.update({
            'generated_doc_id': None,
            'title': '',
            'sections': [],
            'pdf_url': None,
            'docx_url': None,
            'pdf_generated': False,
            'docx_generated': False,
            'generated_at': None,
            'updated_at': None,
        })

    return Response(payload)
