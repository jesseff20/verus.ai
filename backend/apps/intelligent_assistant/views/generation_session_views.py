"""
Views de sessões de geração dinâmica (listagem e detalhes).
"""
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse

from ..models import GenerationSession
from ..serializers import (
    GenerationSessionListSerializer,
    GenerationSessionDetailSerializer,
)

logger = logging.getLogger(__name__)


@extend_schema(
    summary="Listar Sessões de Geração do Usuário",
    description="Lista todas as sessões de geração dinâmica do usuário",
    tags=["Blueprints"],
    responses={
        200: OpenApiResponse(
            description="Lista de sessões",
            response=GenerationSessionListSerializer(many=True)
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_generation_sessions(request):
    """
    Lista sessões de geração do usuário.

    GET /api/v1/intelligent-assistant/generation-sessions/
    """
    qs = GenerationSession.objects.filter(
        user=request.user
    ).select_related('blueprint', 'blueprint__document_type').order_by('-created_at')

    total = qs.count()

    paginator = PageNumberPagination()
    paginator.page_size = 50
    paginator.page_size_query_param = 'page_size'
    paginator.max_page_size = 100
    page = paginator.paginate_queryset(qs, request)
    if page is not None:
        serializer = GenerationSessionListSerializer(page, many=True)
        return paginator.get_paginated_response({
            'sessions': serializer.data,
            'total': total,
        })
    sessions = list(qs)
    serializer = GenerationSessionListSerializer(sessions, many=True)
    return Response({
        'sessions': serializer.data,
        'total': total,
    })


@extend_schema(
    summary="Obter Detalhes da Sessão de Geração",
    description="Retorna detalhes completos de uma sessão de geração",
    tags=["Blueprints"],
    responses={
        200: OpenApiResponse(
            description="Detalhes da sessão",
            response=GenerationSessionDetailSerializer
        ),
        404: OpenApiResponse(description="Sessão não encontrada")
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_generation_session(request, session_id):
    """
    Obtém detalhes de uma sessão de geração.

    GET /api/v1/intelligent-assistant/generation-sessions/{id}/
    """
    try:
        session = GenerationSession.objects.get(
            id=session_id,
            user=request.user
        )
    except GenerationSession.DoesNotExist:
        return Response({
            'error': 'Sessão não encontrada'
        }, status=status.HTTP_404_NOT_FOUND)

    serializer = GenerationSessionDetailSerializer(session)
    return Response(serializer.data)
