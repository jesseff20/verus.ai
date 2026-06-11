from rest_framework import serializers
from .models import (
    Simulation, SimulationDocument, JuryMember,
    JuryDebateMessage, JudgeProfile, Court,
    MinisterProfile, CourtVote,
)


class SimulationDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimulationDocument
        fields = '__all__'
        read_only_fields = ['id', 'uploaded_at']


class JuryMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = JuryMember
        fields = '__all__'
        read_only_fields = ['id']


class JuryDebateMessageSerializer(serializers.ModelSerializer):
    jury_member_name = serializers.CharField(
        source='jury_member.name', read_only=True, default=None,
    )

    class Meta:
        model = JuryDebateMessage
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class SimulationSerializer(serializers.ModelSerializer):
    documents = SimulationDocumentSerializer(many=True, read_only=True)
    jury_members = JuryMemberSerializer(many=True, read_only=True)
    debate_messages = JuryDebateMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Simulation
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class SimulationListSerializer(serializers.ModelSerializer):
    """Serializer enxuto para listagem"""
    documents_count = serializers.IntegerField(source='documents.count', read_only=True)
    jury_members_count = serializers.IntegerField(source='jury_members.count', read_only=True)
    case_title = serializers.SerializerMethodField()
    result_summary = serializers.SerializerMethodField()

    class Meta:
        model = Simulation
        fields = [
            'id', 'simulation_type', 'title', 'description', 'status', 'case',
            'case_title', 'result_summary',
            'documents_count', 'jury_members_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_case_title(self, obj) -> str | None:
        if obj.case:
            return getattr(obj.case, 'titulo', str(obj.case))
        return None

    def get_result_summary(self, obj) -> dict | None:
        """Extract a lightweight summary from the result JSONField."""
        if not obj.result:
            return None
        result = obj.result
        summary = {}
        # Judge simulation
        if 'dispositivo' in result:
            summary['dispositivo'] = result['dispositivo']
        if 'judge_name' in result:
            summary['judge_name'] = result['judge_name']
        # Jury simulation
        if 'verdict' in result:
            summary['verdict'] = result['verdict']
        if 'deliberation_votes' in result:
            summary['deliberation_votes'] = result['deliberation_votes']
        if 'confidence_level' in result:
            summary['confidence_level'] = result['confidence_level']
        if 'probabilities' in result:
            summary['probabilities'] = result['probabilities']
        return summary or None


class JudgeProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = JudgeProfile
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class CourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Court
        fields = '__all__'
        read_only_fields = ['id']


class MinisterProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MinisterProfile
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class CourtVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourtVote
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
