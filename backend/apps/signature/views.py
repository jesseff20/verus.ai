"""
Views REST para assinatura digital.
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import DigitalSignature
from .serializers import DigitalSignatureSerializer, SignDocumentSerializer, VerifySignatureSerializer
from . import service

logger = logging.getLogger(__name__)


class DigitalSignatureViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/signatures/          — lista assinaturas do órgão
    GET /api/v1/signatures/{id}/     — detalhe
    POST /api/v1/signatures/sign/    — assinar documento
    POST /api/v1/signatures/verify/  — verificar assinatura
    GET /api/v1/signatures/providers/ — listar providers disponíveis
    """
    permission_classes = [IsAuthenticated]
    serializer_class = DigitalSignatureSerializer

    def get_queryset(self):
        user = self.request.user
        organ = getattr(user, 'organ', None)
        if not organ:
            return DigitalSignature.objects.none()
        qs = DigitalSignature.objects.filter(organ=organ).select_related('signer')

        # Filtros
        doc_ref = self.request.query_params.get('document_ref')
        if doc_ref:
            qs = qs.filter(document_ref=doc_ref)

        doc_type = self.request.query_params.get('document_type')
        if doc_type:
            qs = qs.filter(document_type=doc_type)

        provider = self.request.query_params.get('provider')
        if provider:
            qs = qs.filter(provider=provider)

        return qs.order_by('-created_at')

    @action(detail=False, methods=['post'], url_path='sign')
    def sign(self, request):
        """POST /sign/ — assina um documento."""
        serializer = SignDocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user
        organ = getattr(user, 'organ', None)
        if not organ:
            return Response(
                {'detail': 'Usuário não vinculado a um órgão.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            sig = service.sign_document(
                signer=user,
                content=data['content'],
                document_type=data['document_type'],
                document_ref=data['document_ref'],
                document_title=data.get('document_title', ''),
                provider_name=data['provider'],
                organ=organ,
                request_ip=self._get_client_ip(request),
                request_ua=request.META.get('HTTP_USER_AGENT', ''),
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except NotImplementedError as exc:
            return Response(
                {'detail': f'Provider não implementado: {exc}'},
                status=status.HTTP_501_NOT_IMPLEMENTED
            )

        return Response(
            DigitalSignatureSerializer(sig).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['post'], url_path='verify')
    def verify(self, request):
        """POST /verify/ — verifica uma assinatura."""
        serializer = VerifySignatureSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = service.verify_signature(str(serializer.validated_data['signature_id']))
        sig = result.get('signature')
        return Response({
            'valid': result['valid'],
            'reason': result['reason'],
            'signature': DigitalSignatureSerializer(sig).data if sig else None,
        })

    @action(detail=False, methods=['get'], url_path='providers')
    def providers(self, request):
        """GET /providers/ — lista providers disponíveis."""
        return Response(service.available_providers())

    @staticmethod
    def _get_client_ip(request) -> str:
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
