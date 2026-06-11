"""
Copilot Jurídico - Sugestões em tempo real para redação jurídica.

Endpoints:
  POST /api/v1/intelligent-assistant/copilot/suggest/
    - Recebe contexto atual do documento
    - Retorna sugestões de: citações, jurisprudência, cláusulas, argumentos
"""

from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from apps.intelligent_assistant.services.copilot_service import (
    LegalCopilotService,
    CopilotSuggestionType,
)


class CopilotThrottle(UserRateThrottle):
    """
    Throttle para Copilot - limitação mais branda para UX fluída.
    Limite: 30 sugestões por minuto por usuário.
    """
    scope = 'copilot_suggest'


@api_view(['POST'])
@throttle_classes([CopilotThrottle])
@permission_classes([permissions.IsAuthenticated])
def suggest_copilot(request):
    """
    POST /api/v1/intelligent-assistant/copilot/suggest/

    Gera sugestões contextuais para o usuário enquanto digita.

    Request:
    {
        "current_text": "texto atual do documento...",
        "cursor_position": 150,
        "current_fragment": "responsabilidade civi",
        "document_type": "peticao_inicial",
        "specialty": "CIV",
        "extra_context": {},
        "enabled_types": ["citation", "jurisprudence", "clause"],
        "max_suggestions": 5
    }

    Response:
    {
        "suggestions": [
            {
                "id": "uuid",
                "type": "citation",
                "title": "Citação sugerida",
                "content": "Texto da citação...",
                "source": "STJ - REsp 1.234.567",
                "relevance_score": 0.95,
                "metadata": {}
            }
        ]
    }
    """
    # Extrair dados do request
    current_text = request.data.get('current_text', '')
    cursor_position = request.data.get('cursor_position', 0)
    current_fragment = request.data.get('current_fragment', '')
    document_type = request.data.get('document_type')
    specialty = request.data.get('specialty')
    extra_context = request.data.get('extra_context', {})
    enabled_types = request.data.get('enabled_types', None)
    max_suggestions = request.data.get('max_suggestions', 5)

    # Validar texto mínimo para sugestões
    if len(current_fragment) < 3 and not current_text.strip():
        return Response({
            'suggestions': [],
            'reason': 'Fragmento muito curto para gerar sugestões'
        })

    # Parse enabled_types
    parsed_types = None
    if enabled_types:
        parsed_types = []
        for t in enabled_types:
            try:
                parsed_types.append(CopilotSuggestionType(t))
            except ValueError:
                pass  # Ignorar tipos inválidos

    try:
        # Gerar sugestões
        service = LegalCopilotService()
        suggestions = service.generate_suggestions(
            current_text=current_text,
            cursor_position=cursor_position,
            current_fragment=current_fragment,
            document_type=document_type,
            specialty=specialty,
            extra_context=extra_context,
            enabled_types=parsed_types,
            max_suggestions=max_suggestions,
            user=request.user,
        )

        # Serializar sugestões
        serialized = [
            {
                'id': s.id,
                'type': s.type.value,
                'title': s.title,
                'content': s.content,
                'source': s.source,
                'relevance_score': s.relevance_score,
                'metadata': s.metadata,
            }
            for s in suggestions
        ]

        return Response({'suggestions': serialized}, status=status.HTTP_200_OK)

    except Exception as e:
        # Em caso de erro, retornar vazio sem quebrar a UX
        return Response({
            'suggestions': [],
            'error': str(e)
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_copilot_commands(request):
    """
    GET /api/v1/intelligent-assistant/copilot/commands/

    Retorna lista de comandos slash disponíveis.
    """
    commands = [
        {
            'command': 'citacao',
            'description': 'Inserir citação jurídica',
            'type': 'citation',
            'shortcut': '/',
        },
        {
            'command': 'juris',
            'description': 'Buscar jurisprudência',
            'type': 'jurisprudence',
            'shortcut': '@',
        },
        {
            'command': 'prazo',
            'description': 'Calcular prazo processual',
            'type': 'deadline',
        },
        {
            'command': 'modelo',
            'description': 'Inserir modelo/cláusula',
            'type': 'clause',
        },
        {
            'command': 'argumento',
            'description': 'Sugerir argumento',
            'type': 'argument',
        },
        {
            'command': 'definicao',
            'description': 'Definir termo técnico',
            'type': 'definition',
        },
        {
            'command': 'lei',
            'description': 'Buscar legislação',
            'type': 'statute',
            'shortcut': '#',
        },
        {
            'command': 'corrigir',
            'description': 'Corrigir texto',
            'type': 'correction',
        },
    ]

    return Response({'commands': commands})


# ─────────────────────────────────────────────────────────────────────────────
# BLUEPRINT COPILOT (CRIAÇÃO POR LINGUAGEM NATURAL)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def blueprint_copilot_chat(request):
    """
    POST — Interage com o Blueprint Copilot via linguagem natural.
    Body: { "user_request": "...", "conversation_history": [...] }
    """
    from ..services.blueprint_copilot_service import BlueprintCopilotService

    user_request = request.data.get('user_request', '')
    conversation_history = request.data.get('conversation_history', [])

    if not user_request:
        return Response({'error': 'user_request é obrigatório'}, status=400)

    result = BlueprintCopilotService.process_natural_language_request(
        user_request, request.user, conversation_history
    )

    return Response(result)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def blueprint_copilot_create(request):
    """
    POST — Cria blueprint a partir dos dados gerados pelo Copilot.
    Body: { "blueprint": { ... } }
    """
    from ..services.blueprint_copilot_service import BlueprintCopilotService

    blueprint_data = request.data.get('blueprint')
    if not blueprint_data:
        return Response({'error': 'blueprint é obrigatório'}, status=400)

    result = BlueprintCopilotService.create_blueprint_from_copilot(blueprint_data, request.user)

    if result['success']:
        return Response(result, status=201)
    return Response(result, status=400)
