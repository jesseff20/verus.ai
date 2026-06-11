"""
Serializers para Colaboração em Tempo Real.
"""

from rest_framework import serializers
from .models import CollaborationSession, CollaboratorPresence, OperationLog, Comment, Suggestion


class CollaborationSessionSerializer(serializers.ModelSerializer):
    """Serializer para Sessão de Colaboração"""
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', read_only=True)
    active_collaborators_count = serializers.IntegerField(
        source='presences.filter', read_only=True,
        help_text='Número de colaboradores ativos'
    )

    class Meta:
        model = CollaborationSession
        fields = [
            'id', 'document_id', 'document_type', 'status',
            'created_by', 'created_by_name',
            'allow_comments', 'allow_suggestions', 'max_collaborators',
            'active_collaborators_count',
            'created_at', 'updated_at', 'last_activity_at', 'expires_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class CollaborationSessionCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar Sessão de Colaboração"""
    class Meta:
        model = CollaborationSession
        fields = [
            'document_id', 'document_type',
            'allow_comments', 'allow_suggestions', 'max_collaborators',
        ]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class CollaboratorPresenceSerializer(serializers.ModelSerializer):
    """Serializer para Presença de Colaborador"""
    user_name = serializers.CharField(
        source='user.get_full_name', read_only=True)
    user_avatar = serializers.CharField(
        source='user.email', read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = CollaboratorPresence
        fields = [
            'id', 'session', 'user', 'user_name', 'user_avatar',
            'status', 'cursor_position', 'selected_section',
            'is_active', 'last_heartbeat', 'joined_at', 'left_at',
        ]
        read_only_fields = ['id', 'last_heartbeat', 'joined_at']


class OperationLogSerializer(serializers.ModelSerializer):
    """Serializer para Log de Operação"""
    user_name = serializers.CharField(
        source='user.get_full_name', read_only=True)

    class Meta:
        model = OperationLog
        fields = [
            'id', 'session', 'user', 'user_name',
            'operation_type', 'section_id', 'position', 'length', 'content',
            'version', 'parent_version', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'version']


class CommentSerializer(serializers.ModelSerializer):
    """Serializer para Comentário"""
    author_name = serializers.CharField(
        source='author.get_full_name', read_only=True)
    author_avatar = serializers.CharField(
        source='author.email', read_only=True)
    replies_count = serializers.IntegerField(
        source='replies.count', read_only=True)
    is_author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'session', 'author', 'author_name', 'author_avatar',
            'parent', 'section_id', 'position_start', 'position_end',
            'quoted_text', 'content', 'is_resolved',
            'replies_count', 'is_author',
            'created_at', 'updated_at', 'resolved_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_is_author(self, obj) -> bool:
        request = self.context.get('request')
        return request and obj.author == request.user


class CommentCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar Comentário"""
    class Meta:
        model = Comment
        fields = [
            'parent', 'section_id', 'position_start', 'position_end',
            'quoted_text', 'content',
        ]

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class SuggestionSerializer(serializers.ModelSerializer):
    """Serializer para Sugestão"""
    author_name = serializers.CharField(
        source='author.get_full_name', read_only=True)
    reviewer_name = serializers.CharField(
        source='reviewed_by.get_full_name', read_only=True)
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)

    class Meta:
        model = Suggestion
        fields = [
            'id', 'session', 'section_id',
            'original_text', 'suggested_text', 'comment',
            'status', 'status_display',
            'author', 'author_name',
            'reviewed_by', 'reviewer_name',
            'created_at', 'reviewed_at',
        ]
        read_only_fields = ['id', 'created_at', 'reviewed_at', 'reviewed_by']


class SuggestionCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar Sugestão"""
    class Meta:
        model = Suggestion
        fields = [
            'section_id', 'original_text', 'suggested_text', 'comment',
        ]

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class SuggestionReviewSerializer(serializers.Serializer):
    """Serializer para revisar Sugestão"""
    status = serializers.ChoiceField(choices=['accepted', 'rejected', 'modified'])
    comment = serializers.CharField(required=False, allow_blank=True)
