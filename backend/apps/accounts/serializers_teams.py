"""
Serializers para Gestão de Equipe.
"""
from rest_framework import serializers
from .models import Team, TeamAssignment


class TeamMemberSerializer(serializers.Serializer):
    """Serializer resumido para membros da equipe."""
    id = serializers.IntegerField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.CharField()
    full_name = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class TeamSerializer(serializers.ModelSerializer):
    leader_name = serializers.SerializerMethodField()
    members_count = serializers.SerializerMethodField()
    members_detail = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = [
            'id', 'name', 'description', 'leader', 'leader_name',
            'members', 'members_count', 'members_detail',
            'specialty', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_leader_name(self, obj):
        if obj.leader:
            return obj.leader.get_full_name() or obj.leader.username
        return None

    def get_members_count(self, obj):
        return obj.members.count()

    def get_members_detail(self, obj):
        return TeamMemberSerializer(obj.members.all(), many=True).data


class TeamAssignmentSerializer(serializers.ModelSerializer):
    team_name = serializers.SerializerMethodField()
    case_titulo = serializers.SerializerMethodField()
    role_in_case_display = serializers.CharField(source='get_role_in_case_display', read_only=True)
    assigned_by_name = serializers.SerializerMethodField()

    class Meta:
        model = TeamAssignment
        fields = [
            'id', 'team', 'team_name', 'case', 'case_titulo',
            'assigned_by', 'assigned_by_name',
            'role_in_case', 'role_in_case_display',
            'assigned_at',
        ]
        read_only_fields = ['id', 'assigned_by', 'assigned_at']

    def get_team_name(self, obj):
        return obj.team.name

    def get_case_titulo(self, obj):
        return obj.case.titulo if obj.case else None

    def get_assigned_by_name(self, obj):
        if obj.assigned_by:
            return obj.assigned_by.get_full_name() or obj.assigned_by.username
        return None
