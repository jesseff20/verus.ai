"""
URLs para Gestão de Equipe.
"""
from django.urls import path
from . import views_teams

urlpatterns = [
    path('', views_teams.teams_list_create, name='teams-list'),
    path('<uuid:team_id>/', views_teams.team_detail, name='team-detail'),
    path('<uuid:team_id>/membros/adicionar/', views_teams.team_add_member, name='team-add-member'),
    path('<uuid:team_id>/membros/remover/', views_teams.team_remove_member, name='team-remove-member'),
    path('<uuid:team_id>/atribuicoes/', views_teams.team_assignments_list_create, name='team-assignments'),
    path('<uuid:team_id>/atribuicoes/<uuid:assignment_id>/', views_teams.team_assignment_delete, name='team-assignment-delete'),
]
