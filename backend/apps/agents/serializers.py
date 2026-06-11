"""
Serializers para Prompts de Agentes
"""
from rest_framework import serializers
from .models import AgentPrompt


class AgentPromptListSerializer(serializers.ModelSerializer):
    """Serializer para listar prompts (resumido)"""
    provider_display = serializers.CharField(source='get_llm_provider_display', read_only=True)
    variable_count = serializers.IntegerField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True, allow_null=True)

    class Meta:
        model = AgentPrompt
        fields = [
            'id', 'name', 'description', 'agent_type', 'icon', 'color', 'display_order',
            'llm_provider', 'provider_display', 'model_name',
            'variable_count', 'use_rag', 'is_active', 'is_default',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AgentPromptDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalhes do prompt (completo)"""
    provider_display = serializers.CharField(source='get_llm_provider_display', read_only=True)
    variable_count = serializers.IntegerField(read_only=True)
    extracted_variables = serializers.ListField(source='extract_variables', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True, allow_null=True)
    created_by_id = serializers.IntegerField(source='created_by.id', read_only=True, allow_null=True)

    class Meta:
        model = AgentPrompt
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class AgentPromptCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar prompt"""
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    rag_query_template = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    icon = serializers.CharField(required=False, allow_blank=True, default='robot')
    color = serializers.CharField(required=False, allow_blank=True, default='#003366')

    class Meta:
        model = AgentPrompt
        fields = [
            'name', 'description', 'agent_type',
            'system_prompt', 'user_prompt_template', 'llm_provider',
            'model_name', 'temperature', 'max_tokens', 'use_rag',
            'rag_query_template', 'icon', 'color', 'display_order',
            'is_active', 'is_default'
        ]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class AgentPromptUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualizar prompt"""

    class Meta:
        model = AgentPrompt
        fields = [
            'name', 'description', 'agent_type', 'system_prompt',
            'user_prompt_template', 'llm_provider', 'model_name', 'temperature',
            'max_tokens', 'use_rag', 'rag_query_template', 'icon', 'color',
            'display_order', 'is_active', 'is_default'
        ]


class AgentExecuteSerializer(serializers.Serializer):
    """Serializer para executar agente"""
    variables = serializers.DictField(
        help_text='Dicionário com valores para as variáveis do prompt'
    )
    user_input = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Input do usuário (se aplicável)'
    )


# ===== ASSISTENTE - SERIALIZERS =====

from .models_assistant import (
    AssistantConversation,
    AssistantMessage,
    AssistantFeedback,
    AssistantAnalytics,
    AssistantKnowledgeQuery,
)


class AssistantMessageSerializer(serializers.ModelSerializer):
    """Serializer para mensagens do assistente"""
    class Meta:
        model = AssistantMessage
        fields = [
            'id', 'role', 'content', 'llm_provider', 'model_name',
            'tokens_used', 'response_time_ms', 'used_kb', 'kb_documents_used',
            'kb_relevance_scores', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AssistantConversationSerializer(serializers.ModelSerializer):
    """Serializer para conversas do assistente"""
    messages = AssistantMessageSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = AssistantConversation
        fields = [
            'id', 'user', 'user_name', 'session_id', 'document_type',
            'document_id', 'current_field', 'started_at', 'last_message_at',
            'total_messages', 'total_tokens_used', 'avg_response_time_ms',
            'user_satisfaction_score', 'messages'
        ]
        read_only_fields = ['id', 'started_at', 'last_message_at']


class AssistantChatRequestSerializer(serializers.Serializer):
    """Serializer para requisição de chat"""
    message = serializers.CharField(help_text='Mensagem do usuário')
    session_id = serializers.CharField(
        required=False,
        help_text='ID da sessão (navegador). Se não fornecido, será gerado automaticamente'
    )
    document_type = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text='Tipo do documento (ex: ETP, TR)'
    )
    document_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text='ID do documento sendo editado'
    )
    current_field = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text='Campo atual sendo preenchido'
    )
    conversation_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text='ID da conversa existente (para continuar conversa)'
    )


class AssistantChatResponseSerializer(serializers.Serializer):
    """Serializer para resposta de chat"""
    conversation_id = serializers.UUIDField(help_text='ID da conversa')
    message_id = serializers.UUIDField(help_text='ID da mensagem do assistente')
    response = serializers.CharField(help_text='Resposta do assistente')
    tokens_used = serializers.IntegerField(help_text='Tokens usados na resposta')
    response_time_ms = serializers.IntegerField(help_text='Tempo de resposta em ms')
    used_kb = serializers.BooleanField(help_text='Se consultou Base de Conhecimento')
    kb_sources = serializers.ListField(
        required=False,
        help_text='Documentos da KB usados como fonte'
    )


class AssistantFeedbackSerializer(serializers.ModelSerializer):
    """Serializer para feedback (RLHF)"""
    class Meta:
        model = AssistantFeedback
        fields = [
            'id', 'message', 'user', 'feedback_type', 'reason',
            'comment', 'suggested_response', 'created_at', 'processed'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'processed']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AssistantAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer para analytics do assistente"""
    class Meta:
        model = AssistantAnalytics
        fields = '__all__'
        read_only_fields = ['id', 'calculated_at']


class AssistantKnowledgeQuerySerializer(serializers.ModelSerializer):
    """Serializer para queries na KB"""
    class Meta:
        model = AssistantKnowledgeQuery
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
