"""
Serializers para Integração com Tribunais.
"""

from rest_framework import serializers
from .models import TribunalIntegration, ProcessSync, ProcessMovement, PetitionProtocol


class TribunalIntegrationSerializer(serializers.ModelSerializer):
    """Serializer para Integração com Tribunal"""
    system_type_display = serializers.CharField(
        source='get_system_type_display', read_only=True)
    connection_status_display = serializers.CharField(
        source='get_connection_status_display', read_only=True)

    class Meta:
        model = TribunalIntegration
        fields = [
            'id', 'name', 'code', 'system_type', 'system_type_display',
            'api_endpoint', 'requires_certificate',
            'is_active', 'connection_status', 'connection_status_display',
            'last_connection_test', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_connection_test']


class TribunalIntegrationCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar Integração"""
    class Meta:
        model = TribunalIntegration
        fields = [
            'name', 'code', 'system_type', 'api_endpoint',
            'requires_certificate', 'username', 'password', 'api_key',
            'is_active',
        ]


class ProcessSyncSerializer(serializers.ModelSerializer):
    """Serializer para Sincronização de Processo"""
    tribunal_name = serializers.CharField(
        source='tribunal.name', read_only=True)
    tribunal_code = serializers.CharField(
        source='tribunal.code', read_only=True)
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)

    class Meta:
        model = ProcessSync
        fields = [
            'id', 'tribunal', 'tribunal_name', 'tribunal_code',
            'process_number', 'case_id',
            'status', 'status_display',
            'last_sync_at', 'next_sync_at', 'sync_count',
            'last_error', 'last_error_at',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProcessMovementSerializer(serializers.ModelSerializer):
    """Serializer para Movimentação Processual"""
    class Meta:
        model = ProcessMovement
        fields = [
            'id', 'process_sync', 'movement_date', 'movement_code',
            'movement_description', 'complement', 'document_id',
            'source', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class PetitionProtocolSerializer(serializers.ModelSerializer):
    """Serializer para Protocolo de Petição"""
    tribunal_name = serializers.CharField(
        source='tribunal.name', read_only=True)
    petition_type_display = serializers.CharField(
        source='get_petition_type_display', read_only=True)
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', read_only=True)

    class Meta:
        model = PetitionProtocol
        fields = [
            'id', 'tribunal', 'tribunal_name',
            'process_number', 'petition_type', 'petition_type_display',
            'petition_title', 'petition_content', 'attachments',
            'protocol_number', 'protocol_date', 'protocol_receipt',
            'status', 'status_display',
            'last_error', 'last_error_at',
            'created_by', 'created_by_name',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'protocol_number', 'protocol_date']


class PetitionProtocolCreateSerializer(serializers.Serializer):
    """Serializer para criar Protocolo"""
    tribunal_id = serializers.UUIDField()
    process_number = serializers.CharField(required=False, allow_blank=True)
    petition_type = serializers.ChoiceField(choices=[
        ('inicial', 'Petição Inicial'),
        ('contestacao', 'Contestação'),
        ('replica', 'Réplica'),
        ('recurso', 'Recurso'),
        ('pedido', 'Pedido'),
        ('outro', 'Outro'),
    ])
    petition_title = serializers.CharField(max_length=500)
    petition_content = serializers.CharField()
    attachments = serializers.ListField(required=False, default=list)

    def create(self, validated_data):
        from .models import TribunalIntegration, PetitionProtocol
        tribunal = TribunalIntegration.objects.get(
            id=validated_data['tribunal_id']
        )
        return PetitionProtocol.objects.create(
            tribunal=tribunal,
            process_number=validated_data.get('process_number', ''),
            petition_type=validated_data['petition_type'],
            petition_title=validated_data['petition_title'],
            petition_content=validated_data['petition_content'],
            attachments=validated_data.get('attachments', []),
            created_by=self.context['request'].user,
        )


class SyncProcessRequestSerializer(serializers.Serializer):
    """Serializer para solicitar sincronização"""
    tribunal_id = serializers.UUIDField()
    process_number = serializers.CharField(max_length=50)
    case_id = serializers.UUIDField(required=False, allow_null=True)
