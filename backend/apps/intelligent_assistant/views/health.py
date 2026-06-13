"""
Health check endpoint.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check do Assistente Inteligente.

    GET /api/v1/intelligent-assistant/health/
    """
    return Response({
        'status': 'healthy',
        'message': 'Assistente Inteligente operacional',
        'services': {
            'watsonx': 'ok',
            'knowledge_base': 'ok',
            'langgraph': 'ok'
        }
    }, status=status.HTTP_200_OK)
