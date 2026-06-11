"""
Views de feedback de seções (auto-aprendizagem).
"""
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse

from ..models import IntelligentSession, SectionFeedback
from ..services.pgvector_service import PgVectorService

logger = logging.getLogger(__name__)


@extend_schema(
    summary="Salvar Feedback de Seção",
    description="Salva avaliação e edição de uma seção gerada para auto-aprendizagem",
    tags=["Assistente Inteligente - Feedback"],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'session_id': {'type': 'string', 'format': 'uuid'},
                'section_number': {'type': 'integer'},
                'section_name': {'type': 'string'},
                'original_content': {'type': 'string'},
                'edited_content': {'type': 'string'},
                'rating': {'type': 'integer', 'minimum': 1, 'maximum': 5},
                'ai_score': {'type': 'number'},
                'edit_reason': {'type': 'string'}
            },
            'required': ['session_id', 'section_number', 'original_content', 'edited_content', 'rating', 'ai_score']
        }
    },
    responses={
        201: OpenApiResponse(description="Feedback salvo com sucesso"),
        400: OpenApiResponse(description="Dados inválidos"),
        404: OpenApiResponse(description="Sessão não encontrada")
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_section_feedback(request):
    """
    POST /api/v1/intelligent-assistant/section-feedback/

    Salva feedback/edição de uma seção para KB de melhorias.
    """
    data = request.data

    # Validar campos obrigatórios
    required_fields = ['session_id', 'section_number', 'original_content', 'edited_content', 'rating', 'ai_score']
    for field in required_fields:
        if field not in data:
            return Response({
                'error': f'Campo obrigatório ausente: {field}'
            }, status=status.HTTP_400_BAD_REQUEST)

    # Validar sessão
    try:
        session = IntelligentSession.objects.get(
            id=data['session_id'],
            user=request.user
        )
    except IntelligentSession.DoesNotExist:
        return Response({
            'error': 'Sessão não encontrada'
        }, status=status.HTTP_404_NOT_FOUND)

    # Validar rating
    rating = int(data['rating'])
    if rating < 1 or rating > 5:
        return Response({
            'error': 'Rating deve ser entre 1 e 5'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Determinar se é uma melhoria (conteúdo foi editado)
    is_improvement = data['original_content'].strip() != data['edited_content'].strip()

    # Criar feedback
    feedback = SectionFeedback.objects.create(
        session=session,
        user=request.user,
        section_number=data['section_number'],
        section_name=data.get('section_name', ''),
        original_content=data['original_content'],
        edited_content=data['edited_content'],
        user_rating=rating,
        ai_score=float(data['ai_score']),
        edit_reason=data.get('edit_reason', ''),
        is_improvement=is_improvement,
        embedding_created=False
    )

    logger.info(f"Feedback salvo para seção {data['section_number']} da sessão {session.id}, is_improvement={is_improvement}")

    # Se nota alta (>= 4), criar embedding na KB de auto-aprendizagem
    embedding_created = False
    feedback_type = 'improvement' if is_improvement else 'approved'

    # Resolver agente de seção via blueprint
    agent_config = None
    if session.blueprint:
        try:
            from ..models import BlueprintSection
            blueprint_section = BlueprintSection.objects.select_related('generator_agent').get(
                blueprint=session.blueprint,
                section_number=data['section_number']
            )
            agent_config = blueprint_section.generator_agent
        except BlueprintSection.DoesNotExist:
            logger.warning(f"BlueprintSection não encontrada: blueprint={session.blueprint.id}, section={data['section_number']}")

    if data.get('section_name') and rating >= 4:
        try:
            pgvector_service = PgVectorService()
            base_metadata = {
                'user_id': str(request.user.id),
                'session_id': str(session.id),
                'ai_score': float(data['ai_score']),
                'user_rating': rating,
                'feedback_type': feedback_type,
            }

            if is_improvement:
                # Conteúdo editado pelo usuário → salvar como melhoria
                base_metadata['edit_reason'] = data.get('edit_reason', '')
                pgvector_service.add_section_improvement(
                    section_name=data['section_name'],
                    improvement_text=data['edited_content'],
                    original_text=data['original_content'],
                    metadata=base_metadata,
                    agent_config=agent_config,
                )
                logger.info(f"Embedding de melhoria criado para seção '{data['section_name']}'")
            else:
                # Conteúdo original aprovado sem edição → salvar como exemplo aprovado
                pgvector_service.add_section_improvement(
                    section_name=data['section_name'],
                    improvement_text=data['original_content'],
                    original_text=None,
                    metadata=base_metadata,
                    agent_config=agent_config,
                )
                logger.info(f"Embedding de conteúdo aprovado criado para seção '{data['section_name']}'")

            feedback.embedding_created = True
            feedback.save(update_fields=['embedding_created'])
            embedding_created = True
        except Exception as e:
            logger.error(f"Erro ao criar embedding: {str(e)}")

    return Response({
        'id': str(feedback.id),
        'is_improvement': is_improvement,
        'embedding_created': embedding_created,
        'feedback_type': feedback_type,
        'message': 'Feedback salvo com sucesso'
    }, status=status.HTTP_201_CREATED)
