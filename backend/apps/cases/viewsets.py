"""
ViewSets DRF para funcionalidades novas — padrao DRY.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q

from .models import TimeEntry, LeadStage, Lead, LeadActivity, LawyerScore, InvoiceNFSe, RiskAssessment
from .serializers import (
    TimeEntrySerializer, LeadStageSerializer, LeadSerializer,
    LeadActivitySerializer, LawyerScoreSerializer, InvoiceNFSeSerializer,
    RiskAssessmentSerializer,
)


class TimeEntryViewSet(viewsets.ModelViewSet):
    """ViewSet para Timesheet / Controle de Horas."""
    serializer_class = TimeEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = TimeEntry.objects.select_related('advogado', 'caso', 'task').all()
        if not user.role in ('superadmin', 'admin', 'socio', 'gestor'):
            qs = qs.filter(Q(advogado=user) | Q(caso__advogado_responsavel=user))
        # Filters
        if self.request.query_params.get('year') and self.request.query_params.get('month'):
            qs = qs.filter(date__year=int(self.request.query_params['year']),
                          date__month=int(self.request.query_params['month']))
        caso = self.request.query_params.get('caso')
        if caso:
            qs = qs.filter(caso_id=caso)
        return qs

    def perform_create(self, serializer):
        serializer.save(advogado=self.request.user)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        entry = self.get_object()
        if not request.user.role in ('superadmin', 'admin', 'socio', 'gestor'):
            return Response({'error': 'Apenas gestores podem aprovar'}, status=status.HTTP_403_FORBIDDEN)
        from django.utils import timezone
        entry.is_approved = True
        entry.approved_by = request.user
        entry.approved_at = timezone.now()
        entry.save(update_fields=['is_approved', 'approved_by', 'approved_at'])
        return Response(TimeEntrySerializer(entry).data)


class LeadStageViewSet(viewsets.ModelViewSet):
    """ViewSet para etapas do funil CRM."""
    serializer_class = LeadStageSerializer
    permission_classes = [IsAuthenticated]
    queryset = LeadStage.objects.all()


class LeadViewSet(viewsets.ModelViewSet):
    """ViewSet para Leads CRM."""
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Lead.objects.select_related('stage', 'responsible').prefetch_related('activities').all()
        if not user.role in ('superadmin', 'admin', 'socio', 'gestor'):
            qs = qs.filter(Q(responsible=user) | Q(created_by=user))
        stage = self.request.query_params.get('stage')
        if stage:
            qs = qs.filter(stage_id=stage)
        temperature = self.request.query_params.get('temperature')
        if temperature:
            qs = qs.filter(temperature=temperature)
        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(email__icontains=search))
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def convert(self, request, pk=None):
        """Converte lead em cliente + caso."""
        from .models import Client, LegalCase
        from django.utils import timezone
        lead = self.get_object()
        client = Client.objects.create(
            name=lead.name, email=lead.email or '', phone=lead.phone or '',
            cpf_cnpj=lead.cpf_cnpj or '', responsible_lawyer=lead.responsible or request.user,
            created_by=request.user, notes=lead.notes or '',
        )
        caso = None
        if lead.description:
            caso = LegalCase.objects.create(
                titulo=f'Caso \u2014 {lead.name}', especialidade=lead.specialty or 'civel',
                client=client, cliente_nome=lead.name, descricao=lead.description,
                valor_causa=lead.estimated_value, advogado_responsavel=lead.responsible or request.user,
                created_by=request.user,
            )
        lead.converted_client = client
        lead.converted_case = caso
        lead.converted_at = timezone.now()
        lead.save(update_fields=['converted_client', 'converted_case', 'converted_at'])
        return Response({
            'lead': LeadSerializer(lead).data,
            'client_id': str(client.id), 'case_id': str(caso.id) if caso else None,
        })

    @action(detail=True, methods=['post'])
    def add_activity(self, request, pk=None):
        lead = self.get_object()
        data = {**request.data, 'lead': str(lead.id)}
        serializer = LeadActivitySerializer(data=data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RiskAssessmentViewSet(viewsets.ModelViewSet):
    """ViewSet para avaliacoes de risco."""
    serializer_class = RiskAssessmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        case_id = self.kwargs.get('case_id') or self.request.query_params.get('caso')
        if case_id:
            return RiskAssessment.objects.filter(caso_id=case_id).order_by('-created_at')
        return RiskAssessment.objects.none()

    def perform_create(self, serializer):
        last = RiskAssessment.objects.filter(caso_id=serializer.validated_data['caso'].id).order_by('-created_at').first()
        obj = serializer.save(assessed_by=self.request.user)
        if last:
            obj.previous_level = last.risk_level
            obj.level_changed = obj.risk_level != last.risk_level
            obj.save(update_fields=['previous_level', 'level_changed'])
