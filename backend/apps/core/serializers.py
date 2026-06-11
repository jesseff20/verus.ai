"""
Serializers para o app Core.
"""
from rest_framework import serializers

from .models import DocumentType, ProcessType, ProcessStatus, AuditLog, SystemModule, LLMProvider, LLMModel, TokenUsageLog


class SystemModuleSerializer(serializers.ModelSerializer):
    """Serializer para SystemModule."""

    class Meta:
        model = SystemModule
        fields = [
            'key',
            'name',
            'description',
            'icon',
            'route',
            'display_order',
            'is_active',
        ]


class DocumentTypeSerializer(serializers.ModelSerializer):
    """Serializer para DocumentType."""

    # category é FK para DocumentCategory — retornamos o code (slug), não o UUID
    category = serializers.CharField(source='category.code', read_only=True)
    category_display = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = DocumentType
        fields = [
            'id',
            'code',
            'name',
            'short_name',
            'description',
            'category',
            'category_display',
            'icon',
            'color',
            'legal_basis',
            'display_order',
            'is_active',
        ]


class DocumentTypeListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem."""

    # category é FK para DocumentCategory — retornamos o code (slug), não o UUID
    category = serializers.CharField(source='category.code', read_only=True)
    category_display = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = DocumentType
        fields = [
            'id',
            'code',
            'name',
            'short_name',
            'category',
            'category_display',
            'icon',
            'color',
            'display_order',
        ]


class ProcessTypeSerializer(serializers.ModelSerializer):
    """Serializer para ProcessType."""

    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )

    class Meta:
        model = ProcessType
        fields = [
            'id',
            'code',
            'name',
            'short_name',
            'description',
            'category',
            'category_display',
            'legal_basis',
            'icon',
            'color',
            'display_order',
            'is_active',
        ]


class ProcessTypeListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de ProcessType."""

    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )

    class Meta:
        model = ProcessType
        fields = [
            'id',
            'code',
            'name',
            'short_name',
            'category',
            'category_display',
            'icon',
            'color',
            'display_order',
        ]


class ProcessStatusSerializer(serializers.ModelSerializer):
    """Serializer para ProcessStatus."""

    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )

    class Meta:
        model = ProcessStatus
        fields = [
            'id',
            'code',
            'name',
            'description',
            'category',
            'category_display',
            'icon',
            'color',
            'display_order',
            'is_active',
            'is_default',
            'is_final',
        ]


class ProcessStatusListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de ProcessStatus."""

    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )

    class Meta:
        model = ProcessStatus
        fields = [
            'id',
            'code',
            'name',
            'category',
            'category_display',
            'icon',
            'color',
            'display_order',
            'is_default',
            'is_final',
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer para AuditLog."""

    action_display = serializers.CharField(
        source='get_action_display',
        read_only=True
    )
    severity_display = serializers.CharField(
        source='get_severity_display',
        read_only=True
    )

    class Meta:
        model = AuditLog
        fields = [
            'id',
            'user',
            'user_email',
            'user_role',
            'action',
            'action_display',
            'severity',
            'severity_display',
            'entity_type',
            'entity_id',
            'entity_name',
            'description',
            'old_values',
            'new_values',
            'metadata',
            'ip_address',
            'created_at',
        ]
        read_only_fields = fields


class AuditLogListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de logs."""

    action_display = serializers.CharField(
        source='get_action_display',
        read_only=True
    )
    severity_display = serializers.CharField(
        source='get_severity_display',
        read_only=True
    )

    class Meta:
        model = AuditLog
        fields = [
            'id',
            'action',
            'action_display',
            'severity',
            'severity_display',
            'entity_type',
            'entity_name',
            'description',
            'user_email',
            'created_at',
        ]


# ── Token Usage ──────────────────────────────────────────────────


class TokenUsageLogSerializer(serializers.ModelSerializer):
    """Serializer para TokenUsageLog."""

    provider_display = serializers.CharField(
        source='get_model_provider_display',
        read_only=True
    )
    usage_type_display = serializers.CharField(
        source='get_usage_type_display',
        read_only=True
    )
    user_email = serializers.EmailField(
        source='user.email',
        read_only=True,
        default=''
    )

    class Meta:
        model = TokenUsageLog
        fields = [
            'id',
            'user',
            'user_email',
            'model_provider',
            'provider_display',
            'model_name',
            'usage_type',
            'usage_type_display',
            'input_tokens',
            'output_tokens',
            'total_tokens',
            'cost_estimate',
            'description',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class TokenUsageLogListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem."""

    provider_display = serializers.CharField(
        source='get_model_provider_display',
        read_only=True
    )
    usage_type_display = serializers.CharField(
        source='get_usage_type_display',
        read_only=True
    )
    user_email = serializers.EmailField(
        source='user.email',
        read_only=True,
        default=''
    )

    class Meta:
        model = TokenUsageLog
        fields = [
            'id',
            'user_email',
            'model_provider',
            'provider_display',
            'model_name',
            'usage_type',
            'usage_type_display',
            'input_tokens',
            'output_tokens',
            'total_tokens',
            'cost_estimate',
            'description',
            'created_at',
        ]


# ── LLM Providers & Models ──────────────────────────────────────


class LLMModelSerializer(serializers.ModelSerializer):
    """Serializer para modelos LLM."""

    class Meta:
        model = LLMModel
        fields = [
            'id',
            'model_id',
            'display_name',
            'description',
            'max_tokens_limit',
            'default_temperature',
            'display_order',
            'is_active',
        ]


class LLMProviderSerializer(serializers.ModelSerializer):
    """Serializer completo para provider LLM (com modelos aninhados)."""

    models = LLMModelSerializer(many=True, read_only=True, source='active_models')
    has_api_key = serializers.BooleanField(read_only=True)

    class Meta:
        model = LLMProvider
        fields = [
            'id',
            'code',
            'name',
            'description',
            'icon',
            'color',
            'has_api_key',
            'display_order',
            'is_active',
            'models',
        ]


class LLMProviderListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listagem de providers."""

    models_count = serializers.SerializerMethodField()
    has_api_key = serializers.BooleanField(read_only=True)

    class Meta:
        model = LLMProvider
        fields = [
            'id',
            'code',
            'name',
            'icon',
            'color',
            'has_api_key',
            'models_count',
            'display_order',
            'is_active',
        ]

    def get_models_count(self, obj):
        return obj.models.filter(is_active=True).count()
