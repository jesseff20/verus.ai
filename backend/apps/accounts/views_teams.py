"""
Views para Gestão de Equipe.
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Team, TeamAssignment, User
from .serializers_teams import TeamSerializer, TeamAssignmentSerializer

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# EQUIPES — CRUD
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def teams_list_create(request):
    """
    GET  /api/v1/auth/equipes/  — Lista equipes
    POST /api/v1/auth/equipes/  — Cria nova equipe
    """
    if request.method == 'GET':
        qs = Team.objects.select_related('leader').prefetch_related('members').all()

        search = request.query_params.get('search', '').strip()
        if search:
            from django.db.models import Q
            qs = qs.filter(Q(name__icontains=search) | Q(specialty__icontains=search))

        is_active = request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active in ('true', '1', 'True'))

        serializer = TeamSerializer(qs, many=True)
        return Response(serializer.data)

    # POST
    serializer = TeamSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def team_detail(request, team_id):
    """
    GET/PUT/PATCH/DELETE /api/v1/auth/equipes/<team_id>/
    """
    try:
        team = Team.objects.select_related('leader').prefetch_related('members').get(pk=team_id)
    except Team.DoesNotExist:
        return Response({'error': 'Equipe não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(TeamSerializer(team).data)

    if request.method in ('PUT', 'PATCH'):
        partial = request.method == 'PATCH'
        serializer = TeamSerializer(team, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # DELETE
    team.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────────────────────────────────────
# MEMBROS — Adicionar / Remover
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def team_add_member(request, team_id):
    """
    POST /api/v1/auth/equipes/<team_id>/membros/adicionar/
    Body: { "user_id": <int> }
    """
    try:
        team = Team.objects.get(pk=team_id)
    except Team.DoesNotExist:
        return Response({'error': 'Equipe não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

    user_id = request.data.get('user_id')
    if not user_id:
        return Response({'error': 'user_id é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({'error': 'Usuário não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    team.members.add(user)
    return Response({'message': f'{user.get_full_name() or user.username} adicionado à equipe.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def team_remove_member(request, team_id):
    """
    POST /api/v1/auth/equipes/<team_id>/membros/remover/
    Body: { "user_id": <int> }
    """
    try:
        team = Team.objects.get(pk=team_id)
    except Team.DoesNotExist:
        return Response({'error': 'Equipe não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

    user_id = request.data.get('user_id')
    if not user_id:
        return Response({'error': 'user_id é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({'error': 'Usuário não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    team.members.remove(user)
    return Response({'message': f'{user.get_full_name() or user.username} removido da equipe.'})


# ─────────────────────────────────────────────────────────────────────────────
# ATRIBUIÇÃO A CASO
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def team_assignments_list_create(request, team_id):
    """
    GET  /api/v1/auth/equipes/<team_id>/atribuicoes/
    POST /api/v1/auth/equipes/<team_id>/atribuicoes/
    Body: { "case": "<uuid>", "role_in_case": "membro" }
    """
    try:
        team = Team.objects.get(pk=team_id)
    except Team.DoesNotExist:
        return Response({'error': 'Equipe não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        assignments = TeamAssignment.objects.filter(team=team).select_related('team', 'case', 'assigned_by')
        serializer = TeamAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)

    # POST
    data = request.data.copy()
    data['team'] = str(team.id)
    serializer = TeamAssignmentSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    serializer.save(assigned_by=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def team_assignment_delete(request, team_id, assignment_id):
    """
    DELETE /api/v1/auth/equipes/<team_id>/atribuicoes/<assignment_id>/
    """
    try:
        assignment = TeamAssignment.objects.get(pk=assignment_id, team_id=team_id)
    except TeamAssignment.DoesNotExist:
        return Response({'error': 'Atribuição não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

    assignment.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
