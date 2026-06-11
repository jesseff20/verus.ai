"""
Serializers para LGPD - Termos de Consentimento, Registros, Atividades e DSR.
"""
from rest_framework import serializers
from .models import ConsentTerm, ConsentRecord, DataProcessingActivity, DataSubjectRequest


class ConsentTermSerializer(serializers.ModelSerializer):
    purpose_display = serializers.CharField(source='get_purpose_display', read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ConsentTerm
        fields = [
            'id', 'title', 'version', 'content', 'purpose', 'purpose_display',
            'is_active', 'created_by', 'created_by_name', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'created_by']

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None


class ConsentRecordSerializer(serializers.ModelSerializer):
    client_name = serializers.SerializerMethodField()
    consent_term_title = serializers.SerializerMethodField()

    class Meta:
        model = ConsentRecord
        fields = [
            'id', 'client', 'client_name', 'consent_term', 'consent_term_title',
            'granted', 'ip_address', 'granted_at', 'revoked_at',
        ]
        read_only_fields = ['id', 'granted_at']

    def get_client_name(self, obj):
        return str(obj.client) if obj.client else None

    def get_consent_term_title(self, obj):
        return str(obj.consent_term) if obj.consent_term else None


class DataProcessingActivitySerializer(serializers.ModelSerializer):
    legal_basis_display = serializers.CharField(source='get_legal_basis_display', read_only=True)
    risk_level_display = serializers.CharField(source='get_risk_level_display', read_only=True)

    class Meta:
        model = DataProcessingActivity
        fields = [
            'id', 'name', 'purpose', 'legal_basis', 'legal_basis_display',
            'data_categories', 'retention_period', 'shared_with',
            'risk_level', 'risk_level_display', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class DataSubjectRequestSerializer(serializers.ModelSerializer):
    request_type_display = serializers.CharField(source='get_request_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    client_name = serializers.SerializerMethodField()

    class Meta:
        model = DataSubjectRequest
        fields = [
            'id', 'client', 'client_name', 'request_type', 'request_type_display',
            'description', 'status', 'status_display', 'response',
            'requested_at', 'responded_at',
        ]
        read_only_fields = ['id', 'requested_at']

    def get_client_name(self, obj):
        return str(obj.client) if obj.client else None
