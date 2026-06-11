"""
Views para Integração com Tribunais.

Endpoints:
  GET/POST /api/v1/integration/tribunais/
    - Listar/criar integrações com tribunais

  GET /api/v1/integration/tribunais/{id}/test-connection/
    - Testar conexão com tribunal

  POST /api/v1/integration/processes/sync/
    - Solicitar sincronização de processo

  GET /api/v1/integration/processes/{id}/movements/
    - Listar movimentações de processo sincronizado

  GET/POST /api/v1/integration/petitions/
    - Listar/criar protocolos de petição

  POST /api/v1/integration/petitions/{id}/send/
    - Enviar petição para protocolo
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from .models import TribunalIntegration, ProcessSync, ProcessMovement, PetitionProtocol
from .serializers import (
    TribunalIntegrationSerializer,
    TribunalIntegrationCreateSerializer,
    ProcessSyncSerializer,
    ProcessMovementSerializer,
    PetitionProtocolSerializer,
    PetitionProtocolCreateSerializer,
    SyncProcessRequestSerializer,
)
from .services.esaj_service import get_tribunal_service


@extend_schema_view(
    list=extend_schema(
        summary="Listar tribunais integrados",
        description="Retorna lista de tribunais configurados",
        tags=["Integration"],
    ),
    create=extend_schema(
        summary="Criar integração com tribunal",
        description="Configura nova integração com tribunal",
        tags=["Integration"],
        request=TribunalIntegrationCreateSerializer,
    ),
)
class TribunalIntegrationViewSet(viewsets.ModelViewSet):
    """ViewSet para Integrações com Tribunais"""
    queryset = TribunalIntegration.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return TribunalIntegrationCreateSerializer
        return TribunalIntegrationSerializer

    @extend_schema(
        summary="Testar conexão",
        description="Testa conexão com o tribunal",
        tags=["Integration"],
        responses={200: OpenApiResponse(description='Resultado do teste')},
    )
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Testar conexão com tribunal"""
        tribunal = self.get_object()

        service = get_tribunal_service(tribunal)
        if not service:
            return Response(
                {'detail': f'Serviço para {tribunal.system_type} não implementado'},
                status=status.HTTP_501_NOT_IMPLEMENTED
            )

        try:
            connected = service.connect()
            service.disconnect()

            if connected:
                return Response({
                    'detail': 'Conexão estabelecida com sucesso',
                    'tribunal': tribunal.name,
                    'system': tribunal.system_type,
                })
            else:
                return Response({
                    'detail': 'Falha ao conectar',
                    'tribunal': tribunal.name,
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        except Exception as e:
            return Response({
                'detail': f'Erro: {str(e)}',
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        summary="Sincronizar processos",
        description="Dispara sincronização de processos vinculados",
        tags=["Integration"],
        responses={200: OpenApiResponse(description='Sincronização iniciada')},
    )
    @action(detail=True, methods=['post'])
    def sync_processes(self, request, pk=None):
        """Sincronizar processos do tribunal"""
        tribunal = self.get_object()

        # Buscar processos pendentes de sincronização
        syncs = ProcessSync.objects.filter(
            tribunal=tribunal,
            status__in=['pending', 'syncing']
        )[:10]

        count = syncs.count()

        return Response({
            'detail': f'Sincronização de {count} processos iniciada',
            'processes_count': count,
        })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def sync_process(request):
    """
    POST /api/v1/integration/processes/sync/

    Solicita sincronização de um processo.

    Request:
    {
        "tribunal_id": "uuid",
        "process_number": "0000000-00.2024.8.26.0000",
        "case_id": "uuid"  // opcional, vincula com caso interno
    }
    """
    serializer = SyncProcessRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    tribunal_id = serializer.validated_data['tribunal_id']
    process_number = serializer.validated_data['process_number']
    case_id = serializer.validated_data.get('case_id')

    tribunal = get_object_or_404(TribunalIntegration, id=tribunal_id)

    # Criar ou atualizar sincronização
    sync, created = ProcessSync.objects.get_or_create(
        tribunal=tribunal,
        process_number=process_number,
        defaults={'case_id': case_id, 'status': 'pending'}
    )

    if not created:
        sync.status = 'pending'
        sync.case_id = case_id
        sync.save()

    # Disparar sincronização assíncrona (em produção usaria Celery)
    from .services.esaj_service import get_tribunal_service
    service = get_tribunal_service(tribunal)

    if service and service.connect():
        try:
            # Consultar processo
            process_data = service.consult_process(process_number)

            if process_data:
                # Atualizar sincronização
                sync.status = 'completed'
                sync.last_sync_at = timezone.now()
                sync.sync_count += 1

                # Criar movimentações
                for mov in process_data.movements:
                    ProcessMovement.objects.create(
                        process_sync=sync,
                        movement_date=mov.get('date'),
                        movement_code=mov.get('code', ''),
                        movement_description=mov.get('description', ''),
                        complement=mov.get('complement', ''),
                        document_id=mov.get('document_id'),
                    )

                sync.save()

                service.disconnect()

                return Response({
                    'detail': 'Sincronização completada',
                    'process_number': process_number,
                    'movements_count': len(process_data.movements),
                })

        except Exception as e:
            sync.status = 'error'
            sync.last_error = str(e)
            sync.last_error_at = timezone.now()
            sync.save()

    return Response({
        'detail': 'Sincronização pendente',
        'process_number': process_number,
        'sync_id': str(sync.id),
    }, status=status.HTTP_202_ACCEPTED)


class ProcessSyncViewSet(viewsets.ModelViewSet):
    """ViewSet para Sincronizações de Processo"""
    queryset = ProcessSync.objects.all()
    serializer_class = ProcessSyncSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ProcessSync.objects.select_related('tribunal')

        # Filtros
        tribunal = self.request.query_params.get('tribunal')
        if tribunal:
            queryset = queryset.filter(tribunal_id=tribunal)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset.order_by('-last_sync_at')

    @extend_schema(
        summary="Listar movimentações",
        description="Retorna movimentações de um processo sincronizado",
        tags=["Integration"],
        responses={200: ProcessMovementSerializer(many=True)},
    )
    @action(detail=True, methods=['get'])
    def movements(self, request, pk=None):
        """Listar movimentações"""
        sync = self.get_object()
        movements = sync.movements.all().order_by('-movement_date')
        serializer = ProcessMovementSerializer(movements, many=True)
        return Response({
            'movements': serializer.data,
            'count': movements.count(),
        })


class PetitionProtocolViewSet(viewsets.ModelViewSet):
    """ViewSet para Protocolos de Petição"""
    queryset = PetitionProtocol.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return PetitionProtocolCreateSerializer
        return PetitionProtocolSerializer

    def get_queryset(self):
        queryset = PetitionProtocol.objects.select_related('tribunal', 'created_by')

        # Filtro por usuário
        if not self.request.user.is_staff:
            queryset = queryset.filter(created_by=self.request.user)

        # Filtros
        tribunal = self.request.query_params.get('tribunal')
        if tribunal:
            queryset = queryset.filter(tribunal_id=tribunal)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        process_number = self.request.query_params.get('process_number')
        if process_number:
            queryset = queryset.filter(process_number=process_number)

        return queryset.order_by('-created_at')

    @extend_schema(
        summary="Enviar petição",
        description="Envia petição para protocolo no tribunal",
        tags=["Integration"],
        responses={200: OpenApiResponse(description='Petição enviada')},
    )
    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Enviar petição para protocolo"""
        petition = self.get_object()

        if petition.status != 'draft':
            return Response(
                {'detail': 'Petição já foi enviada'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Atualizar status
        petition.status = 'sending'
        petition.save()

        # Obter serviço do tribunal
        service = get_tribunal_service(petition.tribunal)

        if not service:
            petition.status = 'error'
            petition.last_error = f'Serviço {petition.tribunal.system_type} não implementado'
            petition.last_error_at = timezone.now()
            petition.save()

            return Response({
                'detail': 'Serviço não implementado para este tribunal',
            }, status=status.HTTP_501_NOT_IMPLEMENTED)

        try:
            if not service.connect():
                raise Exception('Falha ao conectar com tribunal')

            # Preparar dados da petição
            petition_data = {
                'process_number': petition.process_number,
                'petition_type': petition.petition_type,
                'content': petition.petition_content,
                'attachments': petition.attachments,
            }

            # Protocolar
            protocol_number = service.file_petition(petition_data)
            service.disconnect()

            if protocol_number:
                petition.status = 'confirmed'
                petition.protocol_number = protocol_number
                petition.protocol_date = timezone.now()
                petition.save()

                return Response({
                    'detail': 'Petição protocolada com sucesso',
                    'protocol_number': protocol_number,
                })
            else:
                petition.status = 'error'
                petition.last_error = 'Falha ao obter número do protocolo'
                petition.last_error_at = timezone.now()
                petition.save()

                return Response({
                    'detail': 'Falha ao protocolar',
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            petition.status = 'error'
            petition.last_error = str(e)
            petition.last_error_at = timezone.now()
            petition.save()

            return Response({
                'detail': f'Erro: {str(e)}',
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
