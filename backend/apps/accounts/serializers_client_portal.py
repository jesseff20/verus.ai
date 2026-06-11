"""
Serializers para o Portal do Cliente — somente leitura, sem dados internos/financeiros.
"""
from rest_framework import serializers
from apps.cases.models import (
    Client, LegalCase, LegalDeadline, CasePhase, CaseDocument,
    LegalContract, MovimentacaoFinanceira, LegalNotification, Audiencia,
)
from apps.accounts.models import ConsentTerm, ConsentRecord, ClientMessage


class ClientPortalLoginSerializer(serializers.Serializer):
    """Login do cliente no portal via e-mail + senha."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ClientPortalProfileSerializer(serializers.ModelSerializer):
    """Perfil do cliente (somente leitura)."""
    client_type_display = serializers.CharField(source='get_client_type_display', read_only=True)

    class Meta:
        model = Client
        fields = [
            'id', 'name', 'client_type', 'client_type_display',
            'cpf_cnpj', 'email', 'phone',
            'address', 'city', 'state', 'zipcode',
            'company_name', 'contact_person',
        ]
        read_only_fields = fields


class ClientPortalDeadlineSerializer(serializers.ModelSerializer):
    """Prazos do caso — visao do cliente."""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    prioridade_display = serializers.CharField(source='get_prioridade_display', read_only=True)

    class Meta:
        model = LegalDeadline
        fields = [
            'id', 'titulo', 'descricao', 'tipo', 'tipo_display',
            'prioridade', 'prioridade_display', 'status', 'status_display',
            'data_prazo', 'data_conclusao',
        ]
        read_only_fields = fields


class ClientPortalPhaseSerializer(serializers.ModelSerializer):
    """Fases do caso — visao do cliente."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = CasePhase
        fields = [
            'id', 'order', 'name', 'description', 'status', 'status_display',
            'estimated_date', 'actual_date',
        ]
        read_only_fields = fields


class ClientPortalDocumentSerializer(serializers.ModelSerializer):
    """Documentos do caso — visao do cliente (sem observacoes internas)."""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = CaseDocument
        fields = [
            'id', 'titulo', 'tipo', 'tipo_display', 'descricao',
            'data_documento', 'created_at', 'file_url',
        ]
        read_only_fields = fields

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class ClientPortalCaseListSerializer(serializers.ModelSerializer):
    """Lista de casos do cliente — sem dados financeiros e internos."""
    especialidade_display = serializers.CharField(source='get_especialidade_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    fase_display = serializers.CharField(source='get_fase_display', read_only=True)

    class Meta:
        model = LegalCase
        fields = [
            'id', 'numero_processo', 'titulo',
            'especialidade', 'especialidade_display',
            'status', 'status_display',
            'fase', 'fase_display',
            'cliente_nome', 'parte_contraria',
            'tribunal', 'vara_juizo', 'comarca',
            'data_distribuicao',
            'created_at',
        ]
        read_only_fields = fields


class ClientPortalCaseDetailSerializer(serializers.ModelSerializer):
    """Detalhe do caso — com fases, prazos e documentos, sem dados financeiros/internos."""
    especialidade_display = serializers.CharField(source='get_especialidade_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    fase_display = serializers.CharField(source='get_fase_display', read_only=True)
    prazos = ClientPortalDeadlineSerializer(many=True, read_only=True)
    phases = ClientPortalPhaseSerializer(many=True, read_only=True)
    documentos = ClientPortalDocumentSerializer(source='documentos_caso', many=True, read_only=True)

    class Meta:
        model = LegalCase
        fields = [
            'id', 'numero_processo', 'titulo',
            'especialidade', 'especialidade_display',
            'status', 'status_display',
            'fase', 'fase_display',
            'cliente_nome', 'parte_contraria',
            'tribunal', 'vara_juizo', 'comarca',
            'data_distribuicao', 'descricao',
            'created_at',
            'prazos', 'phases', 'documentos',
        ]
        read_only_fields = fields


# ─── Novos serializers do Portal do Cliente ────────────────────────────────


class ClientPortalContractSerializer(serializers.ModelSerializer):
    """Contrato juridico — visao do cliente."""
    contract_type_display = serializers.CharField(source='get_contract_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    case_titulo = serializers.CharField(source='case.titulo', read_only=True, default=None)

    class Meta:
        model = LegalContract
        fields = [
            'id', 'title', 'contract_type', 'contract_type_display',
            'status', 'status_display', 'case_titulo',
            'content_html', 'signed_at', 'expires_at',
            'created_at',
        ]
        read_only_fields = fields


class ClientMessageSerializer(serializers.ModelSerializer):
    """Mensagem entre cliente e advogado."""
    attachment_url = serializers.SerializerMethodField()

    class Meta:
        model = ClientMessage
        fields = [
            'id', 'case', 'sender_type', 'sender_name',
            'content', 'is_read', 'attachment_url', 'created_at',
        ]
        read_only_fields = [
            'id', 'sender_type', 'sender_name', 'is_read',
            'attachment_url', 'created_at',
        ]

    def get_attachment_url(self, obj):
        if obj.attachment:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.attachment.url)
            return obj.attachment.url
        return None


class ClientPortalFinancialSerializer(serializers.ModelSerializer):
    """Movimentacao financeira — visao do cliente (sem observacoes internas)."""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    caso_titulo = serializers.CharField(source='caso.titulo', read_only=True, default=None)

    class Meta:
        model = MovimentacaoFinanceira
        fields = [
            'id', 'tipo', 'tipo_display', 'status', 'status_display',
            'descricao', 'valor', 'data_vencimento', 'data_pagamento',
            'caso_titulo', 'created_at',
        ]
        read_only_fields = fields


class ClientPortalNotificationSerializer(serializers.Serializer):
    """Notificacao/atualizacao para o cliente — agregada de varias fontes."""
    id = serializers.CharField()
    type = serializers.CharField()
    title = serializers.CharField()
    message = serializers.CharField()
    case_id = serializers.UUIDField(allow_null=True)
    case_titulo = serializers.CharField(allow_null=True)
    date = serializers.DateTimeField()


class ClientPortalConsentSerializer(serializers.ModelSerializer):
    """Termo de consentimento LGPD — visao do cliente."""
    purpose_display = serializers.CharField(source='get_purpose_display', read_only=True)

    class Meta:
        model = ConsentTerm
        fields = [
            'id', 'title', 'version', 'content', 'purpose', 'purpose_display',
            'created_at',
        ]
        read_only_fields = fields


class ClientPortalConsentRecordSerializer(serializers.ModelSerializer):
    """Registro de consentimento — visao do cliente."""
    term_title = serializers.CharField(source='consent_term.title', read_only=True)
    term_version = serializers.CharField(source='consent_term.version', read_only=True)

    class Meta:
        model = ConsentRecord
        fields = [
            'id', 'term_title', 'term_version', 'granted',
            'granted_at', 'revoked_at',
        ]
        read_only_fields = fields


class ClientPortalHearingSerializer(serializers.ModelSerializer):
    """Audiencia — visao do cliente."""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    caso_titulo = serializers.CharField(source='caso.titulo', read_only=True, default=None)
    caso_id = serializers.UUIDField(source='caso.id', read_only=True)

    class Meta:
        model = Audiencia
        fields = [
            'id', 'tipo', 'tipo_display', 'status', 'status_display',
            'data_hora', 'local', 'juiz',
            'caso_titulo', 'caso_id',
        ]
        read_only_fields = fields
