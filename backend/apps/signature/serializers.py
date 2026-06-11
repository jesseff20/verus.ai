from rest_framework import serializers
from .models import DigitalSignature, SignatureProvider, SignatureStatus


class DigitalSignatureSerializer(serializers.ModelSerializer):
    signer_name = serializers.SerializerMethodField()
    provider_label = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()

    class Meta:
        model = DigitalSignature
        fields = [
            'id', 'signer', 'signer_name',
            'document_type', 'document_ref', 'document_title',
            'content_hash', 'provider', 'provider_label',
            'status', 'status_label',
            'public_key_fingerprint',
            'signed_at', 'expires_at',
            'signer_ip', 'created_at',
        ]
        read_only_fields = fields

    def get_signer_name(self, obj):
        return obj.signer.get_full_name() or obj.signer.email

    def get_provider_label(self, obj):
        return obj.get_provider_display()

    def get_status_label(self, obj):
        return obj.get_status_display()


class SignDocumentSerializer(serializers.Serializer):
    content = serializers.CharField(
        help_text='Conteúdo a assinar (texto do documento, despacho, etc.)'
    )
    document_type = serializers.ChoiceField(
        choices=['despacho', 'parecer', 'peticao', 'ata', 'contrato', 'outro'],
        default='despacho',
    )
    document_ref = serializers.CharField(
        help_text='UUID do objeto assinado (ex: ID da tarefa, do despacho)'
    )
    document_title = serializers.CharField(required=False, default='')
    provider = serializers.ChoiceField(
        choices=[p[0] for p in DigitalSignature._meta.get_field('provider').choices],
        default='internal',
    )


class VerifySignatureSerializer(serializers.Serializer):
    signature_id = serializers.UUIDField()
