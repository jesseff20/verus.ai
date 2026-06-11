"""
Views de busca semântica (sessão e knowledge base).
"""
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse

from ..models import IntelligentSession, KnowledgeBase
from ..services.pgvector_service import PgVectorService

logger = logging.getLogger(__name__)


@extend_schema(
    summary="Busca Semântica na Sessão",
    description="""
    Busca documentos similares na sessão usando similaridade de cosseno.

    Útil para:
    - Testar se os documentos foram indexados corretamente
    - Verificar quais trechos serão usados para gerar o ETP
    """,
    tags=["Assistente Inteligente - Busca"],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'query': {'type': 'string', 'description': 'Texto para buscar'},
                'n_results': {'type': 'integer', 'default': 5},
                'min_similarity': {'type': 'number', 'default': 0.7}
            },
            'required': ['query']
        }
    },
    responses={
        200: OpenApiResponse(description="Resultados da busca"),
        404: OpenApiResponse(description="Sessão não encontrada")
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_session(request, session_id):
    """
    Busca semântica nos documentos da sessão.

    POST /api/v1/intelligent-assistant/sessions/{session_id}/search/
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

    query = request.data.get('query', '').strip()
    n_results = request.data.get('n_results', 5)
    min_similarity = request.data.get('min_similarity', 0.7)

    if not query:
        return Response({
            'error': 'O campo "query" é obrigatório'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        pgvector_service = PgVectorService()
        results = pgvector_service.search_session_documents(
            session=session,
            query=query,
            n_results=n_results,
            min_similarity=min_similarity
        )

        return Response({
            'query': query,
            'results': results,
            'total_results': len(results)
        })

    except Exception as e:
        return Response({
            'error': 'Erro na busca',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Listar Bases de Conhecimento",
    description="Lista todas as bases de conhecimento disponíveis",
    tags=["Assistente Inteligente - Knowledge Base"],
    responses={200: OpenApiResponse(description="Lista de KBs")}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_knowledge_bases(request):
    """
    Lista bases de conhecimento.

    GET /api/v1/intelligent-assistant/knowledge-bases/
    """
    kbs = KnowledgeBase.objects.filter(is_active=True)
    pgvector_service = PgVectorService()

    return Response({
        'knowledge_bases': [
            {
                'id': str(kb.id),
                'name': kb.name,
                'description': kb.description,
                'stats': pgvector_service.get_knowledge_base_stats(kb),
                'created_at': kb.created_at.isoformat()
            }
            for kb in kbs
        ]
    })


@extend_schema(
    summary="Busca na Base de Conhecimento",
    description="Busca semântica nas bases de conhecimento permanentes",
    tags=["Assistente Inteligente - Knowledge Base"],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'query': {'type': 'string'},
                'knowledge_base': {'type': 'string', 'default': 'all'},
                'n_results': {'type': 'integer', 'default': 5}
            },
            'required': ['query']
        }
    },
    responses={200: OpenApiResponse(description="Resultados da busca")}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_knowledge_base(request):
    """
    Busca semântica nas bases de conhecimento.

    POST /api/v1/intelligent-assistant/knowledge-bases/search/
    """
    query = request.data.get('query', '').strip()
    kb_name = request.data.get('knowledge_base', 'all')
    n_results = request.data.get('n_results', 5)

    if not query:
        return Response({
            'error': 'O campo "query" é obrigatório'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        pgvector_service = PgVectorService()
        results = pgvector_service.search_knowledge_base(
            knowledge_base_name=kb_name,
            query=query,
            n_results=n_results
        )

        return Response({
            'query': query,
            'knowledge_base': kb_name,
            'results': results,
            'total_results': len(results)
        })

    except Exception as e:
        return Response({
            'error': 'Erro na busca',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
