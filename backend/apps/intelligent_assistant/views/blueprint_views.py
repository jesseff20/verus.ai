"""
Views CRUD de Blueprints, Seções e Sub-seções.
"""
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from django.db import transaction

from ..models import (
    DocumentBlueprint,
    BlueprintSection,
    BlueprintSubSection,
)
from ..serializers import (
    DocumentBlueprintListSerializer,
    DocumentBlueprintDetailSerializer,
    DocumentBlueprintWriteSerializer,
    BlueprintSectionListSerializer,
    BlueprintSectionDetailSerializer,
    BlueprintSectionWriteSerializer,
    BlueprintSubSectionWriteSerializer,
    BlueprintSubSectionSerializer,
)

logger = logging.getLogger(__name__)


# ========== BLUEPRINTS DINÂMICOS ==========

@extend_schema(
    summary="Listar Blueprints Disponíveis",
    description="""
    Lista todos os blueprints de documentos jurídicos disponíveis para geração.

    Cada blueprint define a estrutura de um tipo de documento (petições, recursos,
    contratos, defesas, etc.) com seções, agentes de IA e base legal.

    Use o ID ou nome do blueprint para gerar documentos.
    """,
    tags=["Blueprints"],
    parameters=[
        OpenApiParameter(
            name='document_type',
            type=str,
            description='Filtrar por tipo de documento (etp, termo_referencia, edital, etc)',
            required=False
        ),
        OpenApiParameter(
            name='active_only',
            type=bool,
            description='Apenas blueprints ativos (default: true)',
            required=False
        ),
    ],
    responses={
        200: OpenApiResponse(
            description="Lista de blueprints",
            response=DocumentBlueprintListSerializer(many=True)
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_blueprints(request):
    """
    Lista blueprints de documentos disponíveis.

    GET /api/v1/intelligent-assistant/blueprints/

    Visibilidade:
    - Admin/SuperAdmin/Manager: vê todos os blueprints
    - Analyst: vê apenas seus próprios + blueprints padrão (is_default=True)
    """
    # Filtros
    document_type = request.query_params.get('document_type')
    active_only = request.query_params.get('active_only', 'true').lower() == 'true'

    user = request.user
    queryset = DocumentBlueprint.objects.select_related(
        'document_type',
        'document_type__category',
        'created_by',
    ).prefetch_related('areas')

    # Filtro de visibilidade baseado na role
    from apps.accounts.permissions import resolve_role
    _bp_role = resolve_role(user.role)
    _bp_limited = [
        'analista', 'visualizador', 'assistente', 'paralegal', 'estagiario',
        'secretaria', 'assessor', 'servidor', 'cliente',
        'advogado_junior', 'advogado_pleno',
    ]
    if _bp_role in _bp_limited:
        # Operadores vêem: seus próprios blueprints + blueprints padrão
        from django.db.models import Q
        queryset = queryset.filter(
            Q(created_by=user) | Q(is_default=True)
        )

    if active_only:
        queryset = queryset.filter(is_active=True)

    if document_type:
        # Aceita UUID (FK direto) OU code (string como 'etp', 'ordem_servico', etc).
        # Frontend passa code via useBlueprints(code) - manter retro-compat com UUID.
        import uuid as _uuid
        try:
            _uuid.UUID(str(document_type))
            queryset = queryset.filter(document_type=document_type)
        except (ValueError, TypeError):
            queryset = queryset.filter(document_type__code=document_type)

    queryset = queryset.order_by('-is_default', 'document_type', 'name')

    results = list(queryset)
    serializer = DocumentBlueprintListSerializer(results, many=True)

    return Response({
        'blueprints': serializer.data,
        'total': len(results)
    })


@extend_schema(
    summary="Obter Detalhes do Blueprint",
    description="""
    Retorna detalhes completos de um blueprint, incluindo todas as suas seções.

    Pode ser acessado por ID (UUID) ou por nome.
    """,
    tags=["Blueprints"],
    responses={
        200: OpenApiResponse(
            description="Detalhes do blueprint",
            response=DocumentBlueprintDetailSerializer
        ),
        404: OpenApiResponse(description="Blueprint não encontrado")
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_blueprint(request, blueprint_id=None, blueprint_name=None):
    """
    Obtém detalhes de um blueprint.

    GET /api/v1/intelligent-assistant/blueprints/{id}/
    GET /api/v1/intelligent-assistant/blueprints/by-name/{name}/
    """
    try:
        if blueprint_id:
            blueprint = DocumentBlueprint.objects.get(id=blueprint_id)
        elif blueprint_name:
            blueprint = DocumentBlueprint.objects.get(name__iexact=blueprint_name)
        else:
            return Response({
                'error': 'Forneça blueprint_id ou blueprint_name'
            }, status=status.HTTP_400_BAD_REQUEST)

    except DocumentBlueprint.DoesNotExist:
        return Response({
            'error': 'Blueprint não encontrado'
        }, status=status.HTTP_404_NOT_FOUND)

    serializer = DocumentBlueprintDetailSerializer(blueprint)
    return Response(serializer.data)


@extend_schema(
    summary="Listar Seções do Blueprint",
    description="Lista todas as seções de um blueprint específico",
    tags=["Blueprints"],
    responses={
        200: OpenApiResponse(
            description="Lista de seções",
            response=BlueprintSectionListSerializer(many=True)
        ),
        404: OpenApiResponse(description="Blueprint não encontrado")
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_blueprint_sections(request, blueprint_id):
    """
    Lista seções de um blueprint.

    GET /api/v1/intelligent-assistant/blueprints/{id}/sections/
    """
    try:
        blueprint = DocumentBlueprint.objects.get(id=blueprint_id)
    except DocumentBlueprint.DoesNotExist:
        return Response({
            'error': 'Blueprint não encontrado'
        }, status=status.HTTP_404_NOT_FOUND)

    sections = blueprint.get_ordered_sections()
    serializer = BlueprintSectionListSerializer(sections, many=True)

    return Response({
        'blueprint_id': str(blueprint.id),
        'blueprint_name': blueprint.name,
        'sections': serializer.data,
        'total': sections.count()
    })


# ========== BLUEPRINT CRUD ==========


@extend_schema(
    summary="Criar Blueprint",
    tags=["Blueprint Management"],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_blueprint(request):
    """
    POST /api/v1/intelligent-assistant/blueprints/
    """
    serializer = DocumentBlueprintWriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    bp = serializer.save(created_by=request.user)
    return Response(
        DocumentBlueprintDetailSerializer(bp).data,
        status=status.HTTP_201_CREATED
    )


@extend_schema(
    summary="Atualizar Blueprint",
    tags=["Blueprint Management"],
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_blueprint(request, blueprint_id):
    """
    PUT/PATCH /api/v1/intelligent-assistant/blueprints/{id}/update/
    """
    try:
        bp = DocumentBlueprint.objects.get(id=blueprint_id)
    except DocumentBlueprint.DoesNotExist:
        return Response({'error': 'Blueprint não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    partial = request.method == 'PATCH'
    serializer = DocumentBlueprintWriteSerializer(bp, data=request.data, partial=partial)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(DocumentBlueprintDetailSerializer(bp).data)


@extend_schema(
    summary="Deletar Blueprint",
    tags=["Blueprint Management"],
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_blueprint(request, blueprint_id):
    """
    DELETE /api/v1/intelligent-assistant/blueprints/{id}/delete/
    """
    try:
        bp = DocumentBlueprint.objects.get(id=blueprint_id)
    except DocumentBlueprint.DoesNotExist:
        return Response({'error': 'Blueprint não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    bp.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    summary="Duplicar Blueprint",
    description="Cria uma cópia completa do blueprint (com todas as seções e sub-seções)",
    tags=["Blueprint Management"],
    responses={201: DocumentBlueprintDetailSerializer},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def duplicate_blueprint(request, blueprint_id):
    """
    POST /api/v1/intelligent-assistant/blueprints/{id}/duplicate/
    Cria cópia completa: blueprint + seções + sub-seções (vínculos de agente mantidos).
    """
    try:
        original = DocumentBlueprint.objects.prefetch_related(
            'sections__sub_sections'
        ).get(id=blueprint_id)
    except DocumentBlueprint.DoesNotExist:
        return Response({'error': 'Blueprint não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    with transaction.atomic():
        # Duplicar o blueprint principal
        original_id = original.id
        original.pk = None
        original.id = None
        original.name = f'{original.name} (cópia)'
        original.is_default = False
        original.created_by = request.user
        original.save()
        new_bp = original

        # Duplicar seções e sub-seções do original
        sections = BlueprintSection.objects.filter(
            blueprint_id=original_id
        ).prefetch_related('sub_sections')

        for section in sections:
            sub_sections = list(section.sub_sections.all())
            section.pk = None
            section.id = None
            section.blueprint = new_bp
            section.save()
            for sub in sub_sections:
                sub.pk = None
                sub.id = None
                sub.section = section
                sub.save()

    serializer = DocumentBlueprintDetailSerializer(new_bp)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


# ========== BLUEPRINT SECTION CRUD ==========


@extend_schema(
    summary="Criar Seção de Blueprint",
    tags=["Blueprint Management"],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_blueprint_section(request, blueprint_id):
    """
    POST /api/v1/intelligent-assistant/blueprints/{id}/sections/
    """
    try:
        bp = DocumentBlueprint.objects.get(id=blueprint_id)
    except DocumentBlueprint.DoesNotExist:
        return Response({'error': 'Blueprint não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    serializer = BlueprintSectionWriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    section = serializer.save(blueprint=bp)
    return Response(
        BlueprintSectionDetailSerializer(section).data,
        status=status.HTTP_201_CREATED
    )


@extend_schema(
    summary="Atualizar Seção de Blueprint",
    tags=["Blueprint Management"],
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_blueprint_section(request, blueprint_id, section_id):
    """
    PUT/PATCH /api/v1/intelligent-assistant/blueprints/{id}/sections/{sec_id}/
    """
    try:
        section = BlueprintSection.objects.get(id=section_id, blueprint_id=blueprint_id)
    except BlueprintSection.DoesNotExist:
        return Response({'error': 'Seção não encontrada'}, status=status.HTTP_404_NOT_FOUND)

    partial = request.method == 'PATCH'
    serializer = BlueprintSectionWriteSerializer(section, data=request.data, partial=partial)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(BlueprintSectionDetailSerializer(section).data)


@extend_schema(
    summary="Deletar Seção de Blueprint",
    tags=["Blueprint Management"],
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_blueprint_section(request, blueprint_id, section_id):
    """
    DELETE /api/v1/intelligent-assistant/blueprints/{id}/sections/{sec_id}/
    """
    try:
        section = BlueprintSection.objects.get(id=section_id, blueprint_id=blueprint_id)
    except BlueprintSection.DoesNotExist:
        return Response({'error': 'Seção não encontrada'}, status=status.HTTP_404_NOT_FOUND)

    section.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    summary="Reordenar Seções de Blueprint",
    tags=["Blueprint Management"],
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def reorder_blueprint_sections(request, blueprint_id):
    """
    PUT /api/v1/intelligent-assistant/blueprints/{id}/sections/reorder/
    Espera body: {"section_ids": ["uuid1", "uuid2", ...]} na nova ordem.
    """
    try:
        bp = DocumentBlueprint.objects.get(id=blueprint_id)
    except DocumentBlueprint.DoesNotExist:
        return Response({'error': 'Blueprint não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    section_ids = request.data.get('section_ids', [])
    if not section_ids:
        return Response({'error': 'section_ids é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        for order, section_id in enumerate(section_ids):
            BlueprintSection.objects.filter(
                id=section_id, blueprint=bp
            ).update(order=order)

    sections = bp.get_ordered_sections()
    return Response({
        'sections': BlueprintSectionListSerializer(sections, many=True).data,
    })


# ========== SUB-SECTION CRUD ==========


@extend_schema(
    summary="Criar Sub-seção",
    tags=["Blueprint Management"],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_sub_section(request, section_id):
    """
    POST /api/v1/intelligent-assistant/sections/{sec_id}/sub-sections/
    """
    try:
        section = BlueprintSection.objects.get(id=section_id)
    except BlueprintSection.DoesNotExist:
        return Response({'error': 'Seção não encontrada'}, status=status.HTTP_404_NOT_FOUND)

    serializer = BlueprintSubSectionWriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    sub = serializer.save(section=section)
    return Response(
        BlueprintSubSectionSerializer(sub).data,
        status=status.HTTP_201_CREATED
    )


@extend_schema(
    summary="Atualizar Sub-seção",
    tags=["Blueprint Management"],
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_sub_section(request, sub_id):
    """
    PUT/PATCH /api/v1/intelligent-assistant/sub-sections/{sub_id}/
    """
    try:
        sub = BlueprintSubSection.objects.get(id=sub_id)
    except BlueprintSubSection.DoesNotExist:
        return Response({'error': 'Sub-seção não encontrada'}, status=status.HTTP_404_NOT_FOUND)

    partial = request.method == 'PATCH'
    serializer = BlueprintSubSectionWriteSerializer(sub, data=request.data, partial=partial)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(BlueprintSubSectionSerializer(sub).data)


@extend_schema(
    summary="Deletar Sub-seção",
    tags=["Blueprint Management"],
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_sub_section(request, sub_id):
    """
    DELETE /api/v1/intelligent-assistant/sub-sections/{sub_id}/
    """
    try:
        sub = BlueprintSubSection.objects.get(id=sub_id)
    except BlueprintSubSection.DoesNotExist:
        return Response({'error': 'Sub-seção não encontrada'}, status=status.HTTP_404_NOT_FOUND)

    sub.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
