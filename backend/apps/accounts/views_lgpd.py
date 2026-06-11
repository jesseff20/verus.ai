"""
Views LGPD - CRUD para ConsentTerm, ConsentRecord, DataProcessingActivity, DataSubjectRequest.
Inclui endpoints de geracao com IA (privacy policy e consent term).
"""
import logging

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from .models import ConsentTerm, ConsentRecord, DataProcessingActivity, DataSubjectRequest
from .serializers_lgpd import (
    ConsentTermSerializer,
    ConsentRecordSerializer,
    DataProcessingActivitySerializer,
    DataSubjectRequestSerializer,
)

logger = logging.getLogger(__name__)


class IsAdminOrManager(permissions.BasePermission):
    """Permissao para admin ou manager"""
    def has_permission(self, request, view):
        from .permissions import is_admin_or_manager
        return is_admin_or_manager(request.user)


@extend_schema_view(
    list=extend_schema(summary="Listar termos de consentimento", tags=["LGPD"]),
    create=extend_schema(summary="Criar termo de consentimento", tags=["LGPD"]),
    retrieve=extend_schema(summary="Buscar termo de consentimento", tags=["LGPD"]),
    update=extend_schema(summary="Atualizar termo de consentimento", tags=["LGPD"]),
    partial_update=extend_schema(summary="Atualizar parcialmente termo", tags=["LGPD"]),
    destroy=extend_schema(summary="Excluir termo de consentimento", tags=["LGPD"]),
)
class ConsentTermViewSet(viewsets.ModelViewSet):
    """CRUD para Termos de Consentimento LGPD"""
    queryset = ConsentTerm.objects.select_related('created_by').all()
    serializer_class = ConsentTermSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


@extend_schema_view(
    list=extend_schema(summary="Listar registros de consentimento", tags=["LGPD"]),
    create=extend_schema(summary="Criar registro de consentimento", tags=["LGPD"]),
    retrieve=extend_schema(summary="Buscar registro de consentimento", tags=["LGPD"]),
    update=extend_schema(summary="Atualizar registro de consentimento", tags=["LGPD"]),
    partial_update=extend_schema(summary="Atualizar parcialmente registro", tags=["LGPD"]),
    destroy=extend_schema(summary="Excluir registro de consentimento", tags=["LGPD"]),
)
class ConsentRecordViewSet(viewsets.ModelViewSet):
    """CRUD para Registros de Consentimento"""
    queryset = ConsentRecord.objects.select_related('client', 'consent_term').all()
    serializer_class = ConsentRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="Revogar consentimento", tags=["LGPD"])
    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """Revoga um consentimento previamente concedido"""
        record = self.get_object()
        record.granted = False
        record.revoked_at = timezone.now()
        record.save(update_fields=['granted', 'revoked_at'])
        return Response(ConsentRecordSerializer(record).data)


@extend_schema_view(
    list=extend_schema(summary="Listar atividades de tratamento", tags=["LGPD"]),
    create=extend_schema(summary="Criar atividade de tratamento", tags=["LGPD"]),
    retrieve=extend_schema(summary="Buscar atividade de tratamento", tags=["LGPD"]),
    update=extend_schema(summary="Atualizar atividade de tratamento", tags=["LGPD"]),
    partial_update=extend_schema(summary="Atualizar parcialmente atividade", tags=["LGPD"]),
    destroy=extend_schema(summary="Excluir atividade de tratamento", tags=["LGPD"]),
)
class DataProcessingActivityViewSet(viewsets.ModelViewSet):
    """CRUD para Atividades de Tratamento de Dados"""
    queryset = DataProcessingActivity.objects.all()
    serializer_class = DataProcessingActivitySerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema_view(
    list=extend_schema(summary="Listar solicitacoes do titular", tags=["LGPD"]),
    create=extend_schema(summary="Criar solicitacao do titular", tags=["LGPD"]),
    retrieve=extend_schema(summary="Buscar solicitacao do titular", tags=["LGPD"]),
    update=extend_schema(summary="Atualizar solicitacao do titular", tags=["LGPD"]),
    partial_update=extend_schema(summary="Atualizar parcialmente solicitacao", tags=["LGPD"]),
    destroy=extend_schema(summary="Excluir solicitacao do titular", tags=["LGPD"]),
)
class DataSubjectRequestViewSet(viewsets.ModelViewSet):
    """CRUD para Solicitacoes do Titular de Dados"""
    queryset = DataSubjectRequest.objects.select_related('client').all()
    serializer_class = DataSubjectRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="Responder solicitacao do titular", tags=["LGPD"])
    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Responde uma solicitacao do titular de dados"""
        dsr = self.get_object()
        response_text = request.data.get('response', '')
        if not response_text:
            return Response(
                {'detail': 'O campo response e obrigatorio.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        dsr.response = response_text
        dsr.status = 'completed'
        dsr.responded_at = timezone.now()
        dsr.save(update_fields=['response', 'status', 'responded_at'])
        return Response(DataSubjectRequestSerializer(dsr).data)


class LGPDAIViewSet(viewsets.ViewSet):
    """Endpoints de geracao com IA para LGPD"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Gerar politica de privacidade com IA",
        description="Gera uma politica de privacidade baseada nas atividades de tratamento cadastradas",
        tags=["LGPD"],
        responses={200: OpenApiResponse(description="Politica de privacidade gerada")},
    )
    @action(detail=False, methods=['post'], url_path='generate-privacy-policy')
    def generate_privacy_policy(self, request):
        """Gera politica de privacidade usando LLM baseada nas DPAs cadastradas"""
        activities = DataProcessingActivity.objects.filter(is_active=True)
        if not activities.exists():
            return Response(
                {'detail': 'Cadastre ao menos uma atividade de tratamento antes de gerar.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Build context from DPAs
        dpa_context = []
        for act in activities:
            dpa_context.append(
                f"- {act.name}: {act.purpose} "
                f"(base legal: {act.get_legal_basis_display()}, "
                f"dados: {', '.join(act.data_categories)}, "
                f"retencao: {act.retention_period}, "
                f"compartilhamento: {', '.join(act.shared_with) if act.shared_with else 'nenhum'})"
            )

        company_name = request.data.get('company_name', 'Escritorio de Advocacia')

        system_prompt = (
            "Voce e um especialista em LGPD (Lei Geral de Protecao de Dados Pessoais - Lei 13.709/2018). "
            "Gere uma politica de privacidade completa e profissional em portugues brasileiro, "
            "seguindo as melhores praticas e exigencias da LGPD. "
            "A politica deve ser formatada em HTML semantico."
        )

        user_prompt = (
            f"Gere uma Politica de Privacidade completa para: {company_name}\n\n"
            f"Atividades de tratamento de dados cadastradas:\n"
            f"{chr(10).join(dpa_context)}\n\n"
            "Inclua: identificacao do controlador, categorias de dados tratados, "
            "finalidades, bases legais, periodo de retencao, compartilhamento, "
            "direitos dos titulares (acesso, retificacao, eliminacao, portabilidade, oposicao), "
            "medidas de seguranca, contato do encarregado (DPO), e disposicoes gerais."
        )

        try:
            from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService
            llm = UnifiedLLMService()
            result = llm.generate(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.4,
                max_tokens=8192,
                provider='watsonx',
                model='mistralai/mistral-medium-2505',
            )
            return Response({
                'content': result.get('content', ''),
                'model': result.get('model', ''),
            })
        except Exception as e:
            logger.exception("Erro ao gerar politica de privacidade com IA")
            return Response(
                {'detail': f'Erro ao gerar com IA: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        summary="Gerar termo de consentimento com IA",
        description="Gera texto de um termo de consentimento baseado na finalidade informada",
        tags=["LGPD"],
        responses={200: OpenApiResponse(description="Termo de consentimento gerado")},
    )
    @action(detail=False, methods=['post'], url_path='generate-consent-term')
    def generate_consent_term(self, request):
        """Gera texto de termo de consentimento usando LLM"""
        purpose = request.data.get('purpose', 'data_processing')
        title = request.data.get('title', 'Termo de Consentimento')
        company_name = request.data.get('company_name', 'Escritorio de Advocacia')

        purpose_labels = {
            'data_processing': 'tratamento de dados pessoais',
            'marketing': 'comunicacoes de marketing',
            'sharing': 'compartilhamento de dados com terceiros',
        }
        purpose_text = purpose_labels.get(purpose, purpose)

        system_prompt = (
            "Voce e um especialista em LGPD (Lei Geral de Protecao de Dados Pessoais - Lei 13.709/2018). "
            "Gere um termo de consentimento claro, objetivo e em conformidade com a LGPD. "
            "O termo deve ser formatado em HTML semantico."
        )

        user_prompt = (
            f"Gere um Termo de Consentimento para: {company_name}\n"
            f"Titulo: {title}\n"
            f"Finalidade: {purpose_text}\n\n"
            "O termo deve incluir: identificacao do controlador, finalidade especifica do tratamento, "
            "categorias de dados coletados, periodo de retencao, direitos do titular "
            "(incluindo revogacao do consentimento a qualquer momento), "
            "consequencias da recusa, e contato do encarregado."
        )

        try:
            from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService
            llm = UnifiedLLMService()
            result = llm.generate(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.4,
                max_tokens=4096,
                provider='watsonx',
                model='mistralai/mistral-medium-2505',
            )
            return Response({
                'content': result.get('content', ''),
                'model': result.get('model', ''),
            })
        except Exception as e:
            logger.exception("Erro ao gerar termo de consentimento com IA")
            return Response(
                {'detail': f'Erro ao gerar com IA: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
