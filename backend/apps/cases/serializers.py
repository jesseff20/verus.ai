"""
Serializers do app Cases — Gestão de Casos Jurídicos.
"""
import logging

from rest_framework import serializers
from .models import (
    Client, LegalCase, LegalDeadline, CaseTask, CaseDocument, CasePhase,
    Audiencia, MovimentacaoFinanceira, LegalNotification,
    ElectronicProtocol, TribunalPushConfig, TribunalPushEvent,
    LegalContract, HonorariosDetail, ProcuracaoDetail, SubstabelecimentoDetail,
    CourtFeeGuide, DigitalSignature, SignatureVerification,
    WorkflowTemplate, WorkflowExecution,
    TimeEntry, LeadStage, Lead, LeadActivity, LawyerScore, InvoiceNFSe,
    RiskAssessment,
)
from .utils import dias_uteis_entre

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# CLIENT
# ─────────────────────────────────────────────────────────────────────────────

class ClientSerializer(serializers.ModelSerializer):
    client_type_display = serializers.CharField(source='get_client_type_display', read_only=True)
    responsible_lawyer_name = serializers.SerializerMethodField()
    total_cases = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            'id', 'name', 'client_type', 'client_type_display',
            'cpf_cnpj', 'rg', 'email', 'phone', 'phone_secondary',
            'address', 'city', 'state', 'zipcode',
            'company_name', 'contact_person',
            'responsible_lawyer', 'responsible_lawyer_name',
            'created_by', 'notes', 'is_active', 'portal_active',
            'total_cases', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'portal_active']

    def get_responsible_lawyer_name(self, obj):
        if obj.responsible_lawyer:
            return obj.responsible_lawyer.get_full_name() or obj.responsible_lawyer.username
        return None

    def get_total_cases(self, obj):
        return obj.cases.count()


class LegalDeadlineSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    prioridade_display = serializers.CharField(source='get_prioridade_display', read_only=True)
    responsavel_nome = serializers.SerializerMethodField()
    dias_restantes = serializers.SerializerMethodField()
    dias_uteis_restantes = serializers.SerializerMethodField()

    class Meta:
        model = LegalDeadline
        fields = [
            'id', 'caso', 'titulo', 'descricao', 'tipo', 'tipo_display',
            'prioridade', 'prioridade_display', 'status', 'status_display',
            'data_prazo', 'data_conclusao',
            'appeal_type', 'base_legal', 'auto_generated',
            'responsavel', 'responsavel_nome',
            'dias_restantes', 'dias_uteis_restantes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_responsavel_nome(self, obj):
        if obj.responsavel:
            return obj.responsavel.get_full_name() or obj.responsavel.username
        return None

    def get_dias_restantes(self, obj):
        from django.utils import timezone
        if obj.status in ('concluido', 'cancelado'):
            return None
        today = timezone.now().date()
        return (obj.data_prazo - today).days

    def get_dias_uteis_restantes(self, obj):
        """Retorna quantos dias úteis (CNJ) restam até o vencimento do prazo."""
        from django.utils import timezone
        if obj.status in ('concluido', 'cancelado'):
            return None
        today = timezone.now().date()
        if obj.data_prazo <= today:
            return 0
        return dias_uteis_entre(today, obj.data_prazo)


class CaseTaskSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    prioridade_display = serializers.CharField(source='get_prioridade_display', read_only=True)
    responsavel_nome = serializers.SerializerMethodField()
    caso_titulo = serializers.SerializerMethodField()

    class Meta:
        model = CaseTask
        fields = [
            'id', 'caso', 'caso_titulo', 'titulo', 'descricao', 'status', 'status_display',
            'prioridade', 'prioridade_display', 'responsavel', 'responsavel_nome',
            'data_limite', 'data_conclusao', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_responsavel_nome(self, obj):
        if obj.responsavel:
            return obj.responsavel.get_full_name() or obj.responsavel.username
        return None

    def get_caso_titulo(self, obj):
        return obj.caso.titulo if obj.caso else None


class CasePhaseSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.SerializerMethodField()
    days_overdue = serializers.SerializerMethodField()

    class Meta:
        model = CasePhase
        fields = [
            'id', 'caso', 'order', 'name', 'description',
            'status', 'status_display',
            'estimated_date', 'actual_date',
            'reopened_at', 'reopened_reason', 'overdue_since',
            'is_overdue', 'days_overdue',
            'copilot_prompt', 'suggested_documents',
            'notes', 'created_at',
        ]
        read_only_fields = ['id', 'caso', 'order', 'name', 'description', 'created_at',
                            'reopened_at', 'overdue_since', 'is_overdue', 'days_overdue']

    def get_is_overdue(self, obj):
        from django.utils import timezone
        if obj.status in ('completed', 'skipped'):
            return False
        if obj.estimated_date and obj.estimated_date < timezone.now().date():
            return True
        return False

    def get_days_overdue(self, obj):
        from django.utils import timezone
        if obj.status in ('completed', 'skipped'):
            return 0
        if obj.estimated_date and obj.estimated_date < timezone.now().date():
            return (timezone.now().date() - obj.estimated_date).days
        return 0


class CaseDocumentSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = CaseDocument
        fields = [
            'id', 'caso', 'titulo', 'tipo', 'tipo_display', 'descricao',
            'data_documento', 'generated_document_id', 'linked_document',
            'simulation', 'file', 'observacoes', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class AudienciaSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Audiencia
        fields = ['id', 'caso', 'tipo', 'tipo_display', 'status', 'status_display',
                  'data_hora', 'local', 'juiz', 'resultado', 'observacoes',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class MovimentacaoFinanceiraSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MovimentacaoFinanceira
        fields = ['id', 'caso', 'tipo', 'tipo_display', 'status', 'status_display',
                  'descricao', 'valor', 'data_vencimento', 'data_pagamento',
                  'comprovante_url', 'observacoes', 'created_by',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class LegalNotificationSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    direcao_display = serializers.CharField(source='get_direcao_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    meio_display = serializers.SerializerMethodField()
    prazo_tipo_display = serializers.SerializerMethodField()
    prazo_default = serializers.SerializerMethodField()

    class Meta:
        model = LegalNotification
        fields = [
            'id', 'caso', 'tipo', 'tipo_display',
            'direcao', 'direcao_display', 'status', 'status_display',
            'meio', 'meio_display',
            'destinatario_nome', 'remetente',
            'data_expedicao', 'data_ciencia', 'data_publicacao_dje',
            'prazo_dias', 'prazo_tipo', 'prazo_tipo_display', 'prazo_vencimento',
            'prazo_default',
            'base_legal', 'conteudo_resumo', 'observacoes',
            'deadline_created',
            'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'prazo_vencimento', 'deadline_created']

    def get_meio_display(self, obj):
        if obj.meio:
            return obj.get_meio_display()
        return ''

    def get_prazo_tipo_display(self, obj):
        return obj.get_prazo_tipo_display()

    def get_prazo_default(self, obj):
        """Retorna o prazo padrão para o tipo de notificação (para preview no frontend)."""
        from apps.cases.services.notification_service import NotificationService
        default = NotificationService.get_default_prazo_for_tipo(obj.tipo)
        if default:
            return {'dias': default[0], 'tipo': default[1], 'descricao': default[2]}
        return None


class LegalCaseListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listagem."""
    especialidade_display = serializers.CharField(source='get_especialidade_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    fase_display = serializers.CharField(source='get_fase_display', read_only=True)
    advogado_nome = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()
    client_id = serializers.SerializerMethodField()
    prazos_pendentes_count = serializers.IntegerField(read_only=True, default=0)
    tarefas_pendentes_count = serializers.IntegerField(read_only=True, default=0)
    # Fluxo ativo
    active_flow_id = serializers.SerializerMethodField()
    active_flow_status = serializers.SerializerMethodField()
    active_flow_node = serializers.SerializerMethodField()

    class Meta:
        model = LegalCase
        fields = [
            'id', 'numero_processo', 'titulo', 'especialidade', 'especialidade_display',
            'status', 'status_display', 'fase', 'fase_display',
            'client_id', 'client_name', 'cliente_nome', 'parte_contraria', 'tribunal', 'vara_juizo',
            'valor_causa', 'advogado_responsavel', 'advogado_nome',
            'data_distribuicao', 'prazos_pendentes_count', 'tarefas_pendentes_count',
            'active_flow_id', 'active_flow_status', 'active_flow_node',
            'created_at', 'updated_at',
        ]

    def get_active_flow_id(self, obj):
        if obj.active_flow_id:
            return str(obj.active_flow_id)
        return None

    def get_active_flow_status(self, obj):
        try:
            if obj.active_flow:
                return obj.active_flow.status
        except Exception:
            pass
        return None

    def get_active_flow_node(self, obj):
        try:
            if obj.active_flow and obj.active_flow.current_node_id:
                return obj.active_flow.current_node_id
        except Exception:
            pass
        return None

    def get_advogado_nome(self, obj):
        if obj.advogado_responsavel:
            return obj.advogado_responsavel.get_full_name() or obj.advogado_responsavel.username
        return None

    def get_client_id(self, obj):
        try:
            if hasattr(obj, 'client') and obj.client:
                return str(obj.client.id)
        except Exception:
            logger.warning("Error accessing client.id for case %s", getattr(obj, 'id', None), exc_info=True)
        return None

    def get_client_name(self, obj):
        try:
            if hasattr(obj, 'client') and obj.client:
                return obj.client.name
        except Exception:
            logger.warning("Error accessing client.name for case %s", getattr(obj, 'id', None), exc_info=True)
        return obj.cliente_nome or None


class LegalCaseDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalhe/criação/edição."""
    especialidade_display = serializers.CharField(source='get_especialidade_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    fase_display = serializers.CharField(source='get_fase_display', read_only=True)
    advogado_nome = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()
    client_id = serializers.SerializerMethodField()
    prazos = LegalDeadlineSerializer(many=True, read_only=True)
    tarefas = CaseTaskSerializer(many=True, read_only=True)
    documentos_caso = CaseDocumentSerializer(many=True, read_only=True)
    phases = CasePhaseSerializer(many=True, read_only=True)
    notificacoes = LegalNotificationSerializer(many=True, read_only=True)
    # Fluxo ativo
    active_flow_id = serializers.SerializerMethodField()
    active_flow_status = serializers.SerializerMethodField()
    active_flow_node = serializers.SerializerMethodField()
    active_flow_pending_tasks = serializers.SerializerMethodField()
    active_flow_template_name = serializers.SerializerMethodField()

    class Meta:
        model = LegalCase
        fields = [
            'id', 'numero_processo', 'titulo', 'especialidade', 'especialidade_display',
            'status', 'status_display', 'fase', 'fase_display',
            'client', 'client_id', 'client_name', 'cliente_nome', 'cliente_cpf_cnpj',
            'parte_contraria', 'parte_contraria_cpf_cnpj',
            'tribunal', 'vara_juizo', 'comarca', 'valor_causa', 'honorarios_combinados',
            'advogado_responsavel', 'advogado_nome',
            'data_distribuicao', 'data_encerramento',
            'descricao', 'observacoes',
            'active_flow_id', 'active_flow_status', 'active_flow_node',
            'active_flow_pending_tasks', 'active_flow_template_name',
            'prazos', 'tarefas', 'documentos_caso', 'phases', 'notificacoes',
            'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at',
                            'active_flow_id', 'active_flow_status', 'active_flow_node',
                            'active_flow_pending_tasks', 'active_flow_template_name']

    def get_active_flow_id(self, obj):
        if obj.active_flow_id:
            return str(obj.active_flow_id)
        return None

    def get_active_flow_status(self, obj):
        try:
            if obj.active_flow:
                return obj.active_flow.status
        except Exception:
            pass
        return None

    def get_active_flow_node(self, obj):
        try:
            if obj.active_flow and obj.active_flow.current_node_id:
                return obj.active_flow.current_node_id
        except Exception:
            pass
        return None

    def get_active_flow_pending_tasks(self, obj):
        try:
            if obj.active_flow:
                return obj.active_flow.tasks.filter(status__in=('pending', 'in_progress')).count()
        except Exception:
            pass
        return 0

    def get_active_flow_template_name(self, obj):
        try:
            if obj.active_flow:
                return obj.active_flow.template_name_snapshot
        except Exception:
            pass
        return None

    def get_advogado_nome(self, obj):
        if obj.advogado_responsavel:
            return obj.advogado_responsavel.get_full_name() or obj.advogado_responsavel.username
        return None

    def get_client_id(self, obj):
        try:
            if hasattr(obj, 'client') and obj.client:
                return str(obj.client.id)
        except Exception:
            logger.warning("Error accessing client.id in detail serializer for case %s", getattr(obj, 'id', None), exc_info=True)
        return None

    def get_client_name(self, obj):
        try:
            if hasattr(obj, 'client') and obj.client:
                return obj.client.name
        except Exception:
            logger.warning("Error accessing client.name in detail serializer for case %s", getattr(obj, 'id', None), exc_info=True)
        return obj.cliente_nome or None


# ─────────────────────────────────────────────────────────────────────────────
# PROTOCOLO ELETRÔNICO
# ─────────────────────────────────────────────────────────────────────────────

class ElectronicProtocolSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    court_system_display = serializers.CharField(source='get_court_system_display', read_only=True)
    case_titulo = serializers.SerializerMethodField()
    case_numero_processo = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ElectronicProtocol
        fields = [
            'id', 'case', 'document', 'protocol_number',
            'court_system', 'court_system_display',
            'status', 'status_display', 'petition_type',
            'submitted_at', 'accepted_at', 'protocol_receipt',
            'error_message', 'retry_count',
            'created_by', 'created_by_name', 'metadata',
            'case_titulo', 'case_numero_processo',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'protocol_number', 'submitted_at', 'accepted_at',
            'protocol_receipt', 'error_message', 'retry_count',
            'created_by', 'created_at', 'updated_at',
        ]

    def get_case_titulo(self, obj):
        return obj.case.titulo if obj.case else None

    def get_case_numero_processo(self, obj):
        return obj.case.numero_processo if obj.case else None

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None


# ─────────────────────────────────────────────────────────────────────────────
# TRIBUNAL PUSH
# ─────────────────────────────────────────────────────────────────────────────

class TribunalPushConfigSerializer(serializers.ModelSerializer):
    court_system_display = serializers.CharField(source='get_court_system_display', read_only=True)
    events_count = serializers.SerializerMethodField()

    class Meta:
        model = TribunalPushConfig
        fields = [
            'id', 'user', 'court_system', 'court_system_display',
            'is_active', 'check_interval_hours', 'last_checked',
            'notification_types', 'events_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'last_checked', 'created_at', 'updated_at']

    def get_events_count(self, obj):
        return obj.events.count()


class TribunalPushEventSerializer(serializers.ModelSerializer):
    config_court_system = serializers.CharField(source='config.court_system', read_only=True)
    config_court_system_display = serializers.CharField(source='config.get_court_system_display', read_only=True)
    case_titulo = serializers.SerializerMethodField()
    case_numero_processo = serializers.SerializerMethodField()

    class Meta:
        model = TribunalPushEvent
        fields = [
            'id', 'config', 'case', 'event_type', 'event_date',
            'description', 'raw_data', 'is_processed', 'notification_sent',
            'config_court_system', 'config_court_system_display',
            'case_titulo', 'case_numero_processo',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_case_titulo(self, obj):
        return obj.case.titulo if obj.case else None

    def get_case_numero_processo(self, obj):
        return obj.case.numero_processo if obj.case else None


# ─────────────────────────────────────────────────────────────────────────────
# CONTRATOS JURÍDICOS
# ─────────────────────────────────────────────────────────────────────────────

class HonorariosDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = HonorariosDetail
        fields = [
            'fee_type', 'fixed_amount', 'hourly_rate', 'success_percentage',
            'estimated_hours', 'payment_terms', 'installments', 'includes_expenses',
        ]


class ProcuracaoDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcuracaoDetail
        fields = [
            'powers_type', 'special_powers', 'court_scope',
            'valid_until', 'is_irrevocable',
        ]


class SubstabelecimentoDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubstabelecimentoDetail
        fields = [
            'original_procuracao', 'substabelecido_name', 'substabelecido_oab',
            'substabelecido_oab_state', 'with_reserve', 'powers_transferred', 'reason',
        ]


class LegalContractSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    contract_type_display = serializers.CharField(source='get_contract_type_display', read_only=True)
    client_name = serializers.SerializerMethodField()
    case_titulo = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    honorarios_detail = HonorariosDetailSerializer(read_only=True)
    procuracao_detail = ProcuracaoDetailSerializer(read_only=True)
    substabelecimento_detail = SubstabelecimentoDetailSerializer(read_only=True)
    uploaded_file_url = serializers.SerializerMethodField()

    class Meta:
        model = LegalContract
        fields = [
            'id', 'case', 'client', 'contract_type', 'contract_type_display',
            'title', 'status', 'status_display', 'content_html',
            'signed_at', 'expires_at',
            'created_by', 'created_by_name', 'client_name', 'case_titulo',
            'metadata', 'created_at', 'updated_at',
            'honorarios_detail', 'procuracao_detail', 'substabelecimento_detail',
            'uploaded_file', 'uploaded_file_url',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_uploaded_file_url(self, obj):
        if obj.uploaded_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.uploaded_file.url)
            return obj.uploaded_file.url
        return None

    def get_client_name(self, obj):
        return obj.client.name if obj.client else None

    def get_case_titulo(self, obj):
        return obj.case.titulo if obj.case else None

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None


# ─────────────────────────────────────────────────────────────────────────────
# GUIAS DE CUSTAS
# ─────────────────────────────────────────────────────────────────────────────

class CourtFeeGuideSerializer(serializers.ModelSerializer):
    fee_type_display = serializers.CharField(source='get_fee_type_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    case_titulo = serializers.SerializerMethodField()

    class Meta:
        model = CourtFeeGuide
        fields = [
            'id', 'case', 'case_titulo', 'fee_type', 'fee_type_display',
            'court', 'state', 'calculated_amount', 'case_value',
            'calculation_formula', 'due_date',
            'payment_status', 'payment_status_display',
            'payment_date', 'barcode', 'notes',
            'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_case_titulo(self, obj):
        return obj.case.titulo if obj.case else None


# ─────────────────────────────────────────────────────────────────────────────
# ASSINATURA DIGITAL
# ─────────────────────────────────────────────────────────────────────────────

class DigitalSignatureSerializer(serializers.ModelSerializer):
    signature_type_display = serializers.CharField(source='get_signature_type_display', read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = DigitalSignature
        fields = [
            'id', 'user', 'user_name', 'document', 'contract',
            'signature_type', 'signature_type_display',
            'signature_hash', 'certificate_info', 'ip_address',
            'signed_at', 'is_valid', 'verification_url', 'metadata',
        ]
        read_only_fields = ['id', 'signature_hash', 'signed_at', 'verification_url']

    def get_user_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return None


class SignatureVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignatureVerification
        fields = [
            'id', 'signature', 'verified_by', 'verified_at',
            'is_valid', 'verification_details',
        ]
        read_only_fields = ['id', 'verified_at']


# ─────────────────────────────────────────────────────────────────────────────
# CALENDÁRIO / RELATÓRIOS
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# WORKFLOW AUTOMATIZADO
# ─────────────────────────────────────────────────────────────────────────────

class WorkflowTemplateSerializer(serializers.ModelSerializer):
    specialty_display = serializers.CharField(source='get_specialty_display', read_only=True)
    steps_count = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = WorkflowTemplate
        fields = [
            'id', 'name', 'description', 'specialty', 'specialty_display',
            'steps', 'steps_count', 'is_active',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_steps_count(self, obj):
        return len(obj.steps) if obj.steps else 0

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None


class WorkflowExecutionSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    template_name = serializers.SerializerMethodField()
    case_titulo = serializers.SerializerMethodField()
    total_steps = serializers.SerializerMethodField()

    class Meta:
        model = WorkflowExecution
        fields = [
            'id', 'template', 'template_name', 'case', 'case_titulo',
            'current_step', 'total_steps', 'status', 'status_display',
            'step_history', 'started_at', 'completed_at',
        ]
        read_only_fields = ['id', 'current_step', 'step_history', 'started_at', 'completed_at']

    def get_template_name(self, obj):
        return obj.template.name if obj.template else None

    def get_case_titulo(self, obj):
        return obj.case.titulo if obj.case else None

    def get_total_steps(self, obj):
        return len(obj.template.steps) if obj.template and obj.template.steps else 0


class CalendarEventSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField(allow_null=True)
    type = serializers.CharField()
    case_id = serializers.UUIDField(allow_null=True)
    case_title = serializers.CharField(allow_null=True)
    color = serializers.CharField()
    priority = serializers.IntegerField()
    status = serializers.CharField()
    description = serializers.CharField(allow_blank=True)


# ─────────────────────────────────────────────────────────────────────────────
# TIMESHEET
# ─────────────────────────────────────────────────────────────────────────────

class TimeEntrySerializer(serializers.ModelSerializer):
    billing_type_display = serializers.CharField(source='get_billing_type_display', read_only=True)
    advogado_nome = serializers.SerializerMethodField()
    caso_titulo = serializers.SerializerMethodField()
    caso_numero_processo = serializers.SerializerMethodField()
    task_titulo = serializers.SerializerMethodField()

    class Meta:
        model = TimeEntry
        fields = [
            'id', 'caso', 'caso_titulo', 'caso_numero_processo', 'advogado', 'advogado_nome',
            'date', 'hours', 'description', 'billing_type', 'billing_type_display',
            'hourly_rate', 'total_value', 'task', 'task_titulo',
            'is_approved', 'approved_by', 'approved_at', 'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'total_value', 'approved_by', 'approved_at', 'created_at', 'updated_at']

    def get_advogado_nome(self, obj):
        return obj.advogado.get_full_name() or obj.advogado.username if obj.advogado else None

    def get_caso_titulo(self, obj):
        return obj.caso.titulo if obj.caso else None

    def get_caso_numero_processo(self, obj):
        return obj.caso.numero_processo if obj.caso else None

    def get_task_titulo(self, obj):
        return obj.task.titulo if obj.task else None


# ─────────────────────────────────────────────────────────────────────────────
# CRM / LEADS
# ─────────────────────────────────────────────────────────────────────────────

class LeadStageSerializer(serializers.ModelSerializer):
    leads_count = serializers.SerializerMethodField()

    class Meta:
        model = LeadStage
        fields = ['id', 'name', 'order', 'color', 'is_won', 'is_lost', 'leads_count', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_leads_count(self, obj):
        return obj.leads.count()


class LeadActivitySerializer(serializers.ModelSerializer):
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = LeadActivity
        fields = ['id', 'lead', 'activity_type', 'activity_type_display', 'description', 'created_by', 'created_by_name', 'created_at']
        read_only_fields = ['id', 'created_by', 'created_at']

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None


class LeadSerializer(serializers.ModelSerializer):
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    temperature_display = serializers.CharField(source='get_temperature_display', read_only=True)
    specialty_display = serializers.SerializerMethodField()
    stage_name = serializers.SerializerMethodField()
    stage_color = serializers.SerializerMethodField()
    responsible_name = serializers.SerializerMethodField()
    activities = LeadActivitySerializer(many=True, read_only=True)

    class Meta:
        model = Lead
        fields = [
            'id', 'name', 'email', 'phone', 'cpf_cnpj', 'description',
            'specialty', 'specialty_display', 'source', 'source_display',
            'temperature', 'temperature_display',
            'stage', 'stage_name', 'stage_color',
            'estimated_value', 'responsible', 'responsible_name',
            'converted_client', 'converted_case', 'converted_at',
            'next_contact_date', 'notes', 'intake_form_data',
            'activities', 'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'converted_at']

    def get_specialty_display(self, obj):
        if obj.specialty:
            choices_dict = dict(LegalCase.ESPECIALIDADE_CHOICES)
            return choices_dict.get(obj.specialty, obj.specialty)
        return None

    def get_stage_name(self, obj):
        return obj.stage.name if obj.stage else None

    def get_stage_color(self, obj):
        return obj.stage.color if obj.stage else None

    def get_responsible_name(self, obj):
        if obj.responsible:
            return obj.responsible.get_full_name() or obj.responsible.username
        return None


# ─────────────────────────────────────────────────────────────────────────────
# KPIs GAMIFICADOS
# ─────────────────────────────────────────────────────────────────────────────

class LawyerScoreSerializer(serializers.ModelSerializer):
    lawyer_name = serializers.SerializerMethodField()

    class Meta:
        model = LawyerScore
        fields = [
            'id', 'lawyer', 'lawyer_name', 'period_start', 'period_end',
            'cases_won', 'cases_lost', 'cases_settled',
            'deadlines_met', 'deadlines_missed', 'tasks_completed',
            'hours_logged', 'documents_generated', 'revenue_generated',
            'client_satisfaction', 'total_score', 'rank_position', 'badges',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'total_score', 'rank_position', 'badges', 'created_at', 'updated_at']

    def get_lawyer_name(self, obj):
        return obj.lawyer.get_full_name() or obj.lawyer.username


# ─────────────────────────────────────────────────────────────────────────────
# NFS-e
# ─────────────────────────────────────────────────────────────────────────────

class InvoiceNFSeSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    client_name = serializers.SerializerMethodField()
    caso_titulo = serializers.SerializerMethodField()

    class Meta:
        model = InvoiceNFSe
        fields = [
            'id', 'caso', 'caso_titulo', 'client', 'client_name', 'contract',
            'numero_nfse', 'codigo_verificacao', 'status', 'status_display',
            'descricao_servico', 'codigo_servico', 'codigo_tributacao',
            'valor_servico', 'valor_deducoes', 'base_calculo',
            'aliquota_iss', 'valor_iss', 'valor_liquido',
            'irrf', 'pis', 'cofins', 'csll', 'inss',
            'data_emissao', 'data_competencia', 'municipio_prestacao',
            'pdf_url', 'error_message',
            'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero_nfse', 'codigo_verificacao', 'base_calculo',
            'valor_iss', 'valor_liquido', 'data_emissao', 'pdf_url',
            'error_message', 'created_by', 'created_at', 'updated_at',
        ]

    def get_client_name(self, obj):
        return obj.client.name if obj.client else None

    def get_caso_titulo(self, obj):
        return obj.caso.titulo if obj.caso else None


# ─────────────────────────────────────────────────────────────────────────────
# HISTÓRICO DE AVALIAÇÃO DE RISCO
# ─────────────────────────────────────────────────────────────────────────────

class RiskAssessmentSerializer(serializers.ModelSerializer):
    risk_level_display = serializers.CharField(source='get_risk_level_display', read_only=True)
    previous_level_display = serializers.SerializerMethodField()
    assessed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = RiskAssessment
        fields = [
            'id', 'caso', 'risk_level', 'risk_level_display',
            'risk_score', 'factors', 'analysis', 'recommendation',
            'trigger', 'previous_level', 'previous_level_display', 'level_changed',
            'ai_generated', 'ai_model', 'tokens_used',
            'assessed_by', 'assessed_by_name', 'created_at',
        ]
        read_only_fields = ['id', 'previous_level', 'level_changed', 'assessed_by', 'created_at']

    def get_previous_level_display(self, obj):
        if obj.previous_level:
            return dict(RiskAssessment.RISK_LEVEL_CHOICES).get(obj.previous_level, '')
        return None

    def get_assessed_by_name(self, obj):
        if obj.assessed_by:
            return obj.assessed_by.get_full_name() or obj.assessed_by.username
        return None
