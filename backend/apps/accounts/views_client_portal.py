"""
Views do Portal do Cliente — autenticacao e consulta de casos (somente leitura).

Usa JWT customizado com claim 'client_id' para separar da autenticacao de usuarios internos.
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password, make_password
from drf_spectacular.utils import extend_schema, OpenApiResponse

import hashlib
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

from apps.cases.models import (
    Client, LegalCase, CaseDocument, LegalContract, DigitalSignature,
    MovimentacaoFinanceira, LegalNotification, LegalDeadline, CasePhase,
    Audiencia,
)
from apps.accounts.models import ConsentTerm, ConsentRecord, ClientMessage
from apps.accounts.services.notification_bridge import NotificationBridge
from .serializers_client_portal import (
    ClientPortalLoginSerializer,
    ClientPortalProfileSerializer,
    ClientPortalCaseListSerializer,
    ClientPortalCaseDetailSerializer,
    ClientPortalDocumentSerializer,
    ClientPortalContractSerializer,
    ClientMessageSerializer,
    ClientPortalFinancialSerializer,
    ClientPortalNotificationSerializer,
    ClientPortalConsentSerializer,
    ClientPortalConsentRecordSerializer,
    ClientPortalHearingSerializer,
)


# ─── JWT helpers ────────────────────────────────────────────────────────────

class ClientPortalToken(RefreshToken):
    """RefreshToken customizado que carrega client_id em vez de user_id."""

    @classmethod
    def for_client(cls, client):
        token = cls()
        token['client_id'] = str(client.id)
        token['token_type'] = 'client_portal'
        return token


def _get_client_from_request(request):
    """Extrai client_id do JWT e retorna o Client, ou None.

    Usa decodificação manual do JWT (sem AccessToken do SimpleJWT)
    porque o token do portal não tem user_id — apenas client_id.
    O AccessToken do SimpleJWT exigiria user_id e falharia.
    """
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    import jwt
    from django.conf import settings
    try:
        payload = jwt.decode(
            auth.split(' ')[1],
            settings.SECRET_KEY,
            algorithms=['HS256'],
        )
    except Exception:
        logger.warning("Failed to decode client portal JWT token")
        return None
    client_id = payload.get('client_id')
    if not client_id:
        return None
    try:
        return Client.objects.get(id=client_id, portal_active=True, is_active=True)
    except Client.DoesNotExist:
        return None


# ─── Throttle ───────────────────────────────────────────────────────────────

class ClientPortalLoginThrottle(AnonRateThrottle):
    scope = 'login'


# ─── Views ──────────────────────────────────────────────────────────────────

@extend_schema(
    summary="Login do Portal do Cliente",
    description="Autentica cliente via e-mail + senha e retorna tokens JWT",
    tags=["Portal do Cliente"],
    request=ClientPortalLoginSerializer,
    responses={
        200: OpenApiResponse(description="Login realizado"),
        401: OpenApiResponse(description="Credenciais invalidas"),
    },
)
@api_view(['POST'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def client_portal_login(request):
    """POST /api/v1/auth/client-portal/login/"""
    serializer = ClientPortalLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']
    password = serializer.validated_data['password']

    try:
        client = Client.objects.get(email__iexact=email, portal_active=True, is_active=True)
    except Client.DoesNotExist:
        return Response(
            {'detail': 'Credenciais invalidas.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not client.portal_password or not check_password(password, client.portal_password):
        return Response(
            {'detail': 'Credenciais invalidas.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    refresh = ClientPortalToken.for_client(client)
    return Response({
        'client': ClientPortalProfileSerializer(client).data,
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        },
    })


@extend_schema(
    summary="Perfil do cliente autenticado",
    description="Retorna dados do cliente logado no portal",
    tags=["Portal do Cliente"],
    responses={200: ClientPortalProfileSerializer},
)
@api_view(['GET'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def client_portal_me(request):
    """GET /api/v1/auth/client-portal/me/"""
    client = _get_client_from_request(request)
    if not client:
        return Response(
            {'detail': 'Nao autenticado ou portal inativo.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    return Response(ClientPortalProfileSerializer(client).data)


@extend_schema(
    summary="Casos do cliente",
    description="Lista todos os casos vinculados ao cliente autenticado (somente leitura)",
    tags=["Portal do Cliente"],
    responses={200: ClientPortalCaseListSerializer(many=True)},
)
@api_view(['GET'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def client_portal_cases(request):
    """GET /api/v1/auth/client-portal/cases/"""
    client = _get_client_from_request(request)
    if not client:
        return Response(
            {'detail': 'Nao autenticado ou portal inativo.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    cases = LegalCase.objects.filter(client=client)
    serializer = ClientPortalCaseListSerializer(cases, many=True)
    return Response(serializer.data)


@extend_schema(
    summary="Detalhe do caso do cliente",
    description="Retorna caso com fases, prazos e documentos (sem dados financeiros)",
    tags=["Portal do Cliente"],
    responses={200: ClientPortalCaseDetailSerializer},
)
@api_view(['GET'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def client_portal_case_detail(request, case_id):
    """GET /api/v1/auth/client-portal/cases/<uuid:case_id>/"""
    client = _get_client_from_request(request)
    if not client:
        return Response(
            {'detail': 'Nao autenticado ou portal inativo.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    try:
        case = LegalCase.objects.prefetch_related(
            'prazos', 'phases', 'documentos_caso',
        ).get(id=case_id, client=client)
    except LegalCase.DoesNotExist:
        return Response(
            {'detail': 'Caso nao encontrado.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    serializer = ClientPortalCaseDetailSerializer(case)
    return Response(serializer.data)


# ─── Admin: Ativar Portal ───────────────────────────────────────────────────

@extend_schema(
    summary="Ativar/configurar portal do cliente",
    description="Define senha e ativa portal para um cliente (admin/manager)",
    tags=["Portal do Cliente - Admin"],
    request={
        "type": "object",
        "properties": {
            "password": {"type": "string", "description": "Nova senha do portal"},
            "active": {"type": "boolean", "description": "Ativar ou desativar portal"},
        },
        "required": ["password"],
    },
    responses={200: OpenApiResponse(description="Portal configurado")},
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def client_portal_activate(request, client_id):
    """POST /api/v1/auth/client-portal/activate/<uuid:client_id>/"""
    # Verificar permissao admin/manager
    from .permissions import is_admin_or_manager
    if not is_admin_or_manager(request.user):
        return Response(
            {'detail': 'Permissao negada.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        client = Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        return Response(
            {'detail': 'Cliente nao encontrado.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    password = request.data.get('password')
    active = request.data.get('active', True)

    if password:
        client.portal_password = make_password(password)
    client.portal_active = active
    client.save(update_fields=['portal_password', 'portal_active'])

    return Response({
        'detail': 'Portal do cliente configurado com sucesso.',
        'portal_active': client.portal_active,
        'client_id': str(client.id),
        'client_name': client.name,
    })


# ─── Helper para obter IP ──────────────────────────────────────────────────

def _get_client_ip(request):
    """Extrai IP do cliente do request."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


# ─── Consent Flow ──────────────────────────────────────────────────────────

@api_view(['GET'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def client_portal_pending_consents(request):
    """GET /api/v1/auth/client-portal/consents/pending/
    Retorna termos de consentimento ativos que o cliente ainda nao aceitou."""
    client = _get_client_from_request(request)
    if not client:
        return Response(
            {'detail': 'Nao autenticado ou portal inativo.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    accepted_term_ids = ConsentRecord.objects.filter(
        client=client, granted=True,
    ).values_list('consent_term_id', flat=True)
    pending = ConsentTerm.objects.filter(is_active=True).exclude(id__in=accepted_term_ids)
    serializer = ClientPortalConsentSerializer(pending, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def client_portal_accept_consent(request, term_id):
    """POST /api/v1/auth/client-portal/consents/<uuid:term_id>/accept/
    Cliente aceita um termo de consentimento. Registra IP e timestamp."""
    client = _get_client_from_request(request)
    if not client:
        return Response(
            {'detail': 'Nao autenticado ou portal inativo.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    try:
        term = ConsentTerm.objects.get(id=term_id, is_active=True)
    except ConsentTerm.DoesNotExist:
        return Response(
            {'detail': 'Termo de consentimento nao encontrado.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    # Evitar duplicata
    if ConsentRecord.objects.filter(client=client, consent_term=term, granted=True).exists():
        return Response({'detail': 'Consentimento ja registrado.'})

    ConsentRecord.objects.create(
        client=client,
        consent_term=term,
        granted=True,
        ip_address=_get_client_ip(request),
    )

    # Notificar admins/gestores sobre aceite de consentimento
    NotificationBridge.notify_lawyer_client_consent_accepted(client, term)

    return Response({'detail': 'Consentimento registrado com sucesso.'}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def client_portal_my_consents(request):
    """GET /api/v1/auth/client-portal/consents/
    Retorna todos os consentimentos dados pelo cliente."""
    client = _get_client_from_request(request)
    if not client:
        return Response(
            {'detail': 'Nao autenticado ou portal inativo.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    records = ConsentRecord.objects.filter(client=client).select_related('consent_term')
    serializer = ClientPortalConsentRecordSerializer(records, many=True)
    return Response(serializer.data)


# ─── Documents ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def client_portal_case_documents(request, case_id):
    """GET /api/v1/auth/client-portal/cases/<uuid>/documents/
    Retorna documentos de um caso do cliente. Inclui URL do arquivo para download."""
    client = _get_client_from_request(request)
    if not client:
        return Response(
            {'detail': 'Nao autenticado ou portal inativo.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    try:
        case = LegalCase.objects.get(id=case_id, client=client)
    except LegalCase.DoesNotExist:
        return Response(
            {'detail': 'Caso nao encontrado.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    documents = CaseDocument.objects.filter(caso=case)
    serializer = ClientPortalDocumentSerializer(
        documents, many=True, context={'request': request},
    )
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def client_portal_upload_document(request, case_id):
    """POST /api/v1/auth/client-portal/cases/<uuid>/documents/upload/
    Cliente envia um documento (PDF/imagem). Salva como CaseDocument com tipo='documento_cliente'."""
    client = _get_client_from_request(request)
    if not client:
        return Response(
            {'detail': 'Nao autenticado ou portal inativo.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    try:
        case = LegalCase.objects.get(id=case_id, client=client)
    except LegalCase.DoesNotExist:
        return Response(
            {'detail': 'Caso nao encontrado.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return Response(
            {'detail': 'Nenhum arquivo enviado. Use o campo "file".'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    titulo = request.data.get('titulo', uploaded_file.name)
    descricao = request.data.get('descricao', '')

    doc = CaseDocument.objects.create(
        caso=case,
        titulo=titulo,
        tipo='documento_cliente',
        descricao=descricao,
        file=uploaded_file,
        data_documento=timezone.now().date(),
    )

    # Notificar advogado responsavel sobre novo documento
    NotificationBridge.notify_lawyer_client_uploaded_document(client, doc, case)

    serializer = ClientPortalDocumentSerializer(doc, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)


# ─── Contracts & Signatures ───────────────────────────────────────────────

@api_view(['GET'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def client_portal_contracts(request):
    """GET /api/v1/auth/client-portal/contracts/
    Retorna contratos (honorarios, procuracao, substabelecimento) do cliente."""
    client = _get_client_from_request(request)
    if not client:
        return Response(
            {'detail': 'Nao autenticado ou portal inativo.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    contracts = LegalContract.objects.filter(client=client).select_related('case')
    serializer = ClientPortalContractSerializer(contracts, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def client_portal_contract_detail(request, contract_id):
    """GET /api/v1/auth/client-portal/contracts/<uuid>/
    Retorna detalhe completo do contrato com conteudo HTML."""
    client = _get_client_from_request(request)
    if not client:
        return Response(
            {'detail': 'Nao autenticado ou portal inativo.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    try:
        contract = LegalContract.objects.select_related('case').get(
            id=contract_id, client=client,
        )
    except LegalContract.DoesNotExist:
        return Response(
            {'detail': 'Contrato nao encontrado.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    serializer = ClientPortalContractSerializer(contract)
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def client_portal_sign_contract(request, contract_id):
    """POST /api/v1/auth/client-portal/contracts/<uuid>/sign/
    Cliente assina digitalmente um contrato. Cria DigitalSignature e atualiza status."""
    client = _get_client_from_request(request)
    if not client:
        return Response(
            {'detail': 'Nao autenticado ou portal inativo.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    try:
        contract = LegalContract.objects.get(id=contract_id, client=client)
    except LegalContract.DoesNotExist:
        return Response(
            {'detail': 'Contrato nao encontrado.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if contract.status == 'signed':
        return Response(
            {'detail': 'Contrato ja foi assinado.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if contract.status not in ('draft', 'pending_signature'):
        return Response(
            {'detail': 'Contrato nao esta disponivel para assinatura.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Gerar hash do conteudo
    content_to_hash = f"{contract.id}:{contract.content_html}:{client.id}:{timezone.now().isoformat()}"
    signature_hash = hashlib.sha256(content_to_hash.encode()).hexdigest()

    DigitalSignature.objects.create(
        user_id=None,  # cliente nao e User, registramos nos metadata
        contract=contract,
        signature_type='simple',
        signature_hash=signature_hash,
        ip_address=_get_client_ip(request),
        metadata={
            'client_id': str(client.id),
            'client_name': client.name,
            'signed_via': 'client_portal',
        },
    )

    contract.status = 'signed'
    contract.signed_at = timezone.now()
    contract.save(update_fields=['status', 'signed_at', 'updated_at'])

    # Notificar advogado responsavel sobre assinatura
    NotificationBridge.notify_lawyer_client_signed_contract(
        client, contract, case=contract.case,
    )

    return Response({
        'detail': 'Contrato assinado com sucesso.',
        'signature_hash': signature_hash,
        'signed_at': contract.signed_at.isoformat(),
    })


# ─── Messages ──────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def client_portal_messages(request):
    """GET: lista mensagens do cliente. POST: envia mensagem."""
    client = _get_client_from_request(request)
    if not client:
        return Response(
            {'detail': 'Nao autenticado ou portal inativo.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if request.method == 'GET':
        messages = ClientMessage.objects.filter(client=client).order_by('-created_at')
        serializer = ClientMessageSerializer(
            messages, many=True, context={'request': request},
        )
        return Response(serializer.data)

    # POST — enviar mensagem
    content = request.data.get('content', '').strip()
    if not content:
        return Response(
            {'detail': 'O campo "content" e obrigatorio.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    case_id = request.data.get('case')
    case = None
    if case_id:
        try:
            case = LegalCase.objects.get(id=case_id, client=client)
        except LegalCase.DoesNotExist:
            return Response(
                {'detail': 'Caso nao encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )

    attachment = request.FILES.get('attachment')
    msg = ClientMessage.objects.create(
        client=client,
        case=case,
        sender_type='client',
        sender_name=client.name,
        content=content,
        attachment=attachment,
    )

    # Notificar advogado responsavel sobre nova mensagem
    NotificationBridge.notify_lawyer_client_message(client, case=case)

    serializer = ClientMessageSerializer(msg, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def client_portal_mark_read(request, message_id):
    """POST: marca mensagem como lida."""
    client = _get_client_from_request(request)
    if not client:
        return Response(
            {'detail': 'Nao autenticado ou portal inativo.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    try:
        msg = ClientMessage.objects.get(id=message_id, client=client)
    except ClientMessage.DoesNotExist:
        return Response(
            {'detail': 'Mensagem nao encontrada.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    msg.is_read = True
    msg.save(update_fields=['is_read'])
    return Response({'detail': 'Mensagem marcada como lida.'})


# ─── Financial ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def client_portal_financial(request):
    """GET /api/v1/auth/client-portal/financial/
    Retorna faturas pendentes, historico de pagamentos e total devido."""
    client = _get_client_from_request(request)
    if not client:
        return Response(
            {'detail': 'Nao autenticado ou portal inativo.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    case_ids = LegalCase.objects.filter(client=client).values_list('id', flat=True)
    movimentacoes = MovimentacaoFinanceira.objects.filter(
        caso_id__in=case_ids,
    ).select_related('caso')

    pendentes = movimentacoes.filter(status='pendente')
    pagos = movimentacoes.filter(status='pago')

    total_pendente = sum(m.valor for m in pendentes)
    total_pago = sum(m.valor for m in pagos)

    return Response({
        'total_pendente': str(total_pendente),
        'total_pago': str(total_pago),
        'pendentes': ClientPortalFinancialSerializer(pendentes, many=True).data,
        'historico': ClientPortalFinancialSerializer(pagos, many=True).data,
    })


# ─── Notifications / Updates ──────────────────────────────────────────────

@api_view(['GET'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def client_portal_notifications(request):
    """GET /api/v1/auth/client-portal/notifications/
    Retorna atualizacoes recentes dos casos, prazos e solicitacoes de documentos."""
    client = _get_client_from_request(request)
    if not client:
        return Response(
            {'detail': 'Nao autenticado ou portal inativo.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    case_ids = list(LegalCase.objects.filter(client=client).values_list('id', flat=True))
    notifications = []

    # Notificacoes juridicas recentes (ultimos 30 dias)
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)

    legal_notifs = LegalNotification.objects.filter(
        caso_id__in=case_ids,
        created_at__gte=thirty_days_ago,
    ).select_related('caso')[:20]
    for n in legal_notifs:
        notifications.append({
            'id': str(n.id),
            'type': 'notificacao_juridica',
            'title': n.get_tipo_display(),
            'message': n.conteudo_resumo or n.get_tipo_display(),
            'case_id': n.caso_id,
            'case_titulo': n.caso.titulo if n.caso else None,
            'date': n.created_at,
        })

    # Prazos proximos (proximos 15 dias)
    fifteen_days_ahead = timezone.now().date() + timezone.timedelta(days=15)
    deadlines = LegalDeadline.objects.filter(
        caso_id__in=case_ids,
        status='pendente',
        data_prazo__lte=fifteen_days_ahead,
    ).select_related('caso')[:20]
    for d in deadlines:
        notifications.append({
            'id': str(d.id),
            'type': 'prazo',
            'title': f'Prazo: {d.titulo}',
            'message': f'Vence em {d.data_prazo.strftime("%d/%m/%Y")}',
            'case_id': d.caso_id,
            'case_titulo': d.caso.titulo if d.caso else None,
            'date': d.created_at,
        })

    # Mudancas de fase recentes
    phases = CasePhase.objects.filter(
        caso_id__in=case_ids,
        status='in_progress',
        created_at__gte=thirty_days_ago,
    ).select_related('caso')[:10]
    for p in phases:
        notifications.append({
            'id': str(p.id),
            'type': 'fase',
            'title': f'Fase atualizada: {p.name}',
            'message': f'O caso esta na fase "{p.name}"',
            'case_id': p.caso_id,
            'case_titulo': p.caso.titulo if p.caso else None,
            'date': p.created_at,
        })

    # Ordenar por data desc
    notifications.sort(key=lambda x: x['date'], reverse=True)

    paginator = PageNumberPagination()
    paginator.page_size = 50
    paginator.page_size_query_param = 'page_size'
    paginator.max_page_size = 100
    page = paginator.paginate_queryset(notifications, request)
    if page is not None:
        serializer = ClientPortalNotificationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    serializer = ClientPortalNotificationSerializer(notifications, many=True)
    return Response(serializer.data)


# ─── Profile ──────────────────────────────────────────────────────────────

@api_view(['GET', 'PATCH'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def client_portal_profile(request):
    """GET: retorna perfil do cliente. PATCH: atualiza telefone, email, endereco."""
    client = _get_client_from_request(request)
    if not client:
        return Response(
            {'detail': 'Nao autenticado ou portal inativo.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if request.method == 'GET':
        return Response(ClientPortalProfileSerializer(client).data)

    # PATCH — campos permitidos para atualizacao
    allowed_fields = ['phone', 'email', 'address', 'city', 'state', 'zipcode']
    updated = []
    for field in allowed_fields:
        if field in request.data:
            setattr(client, field, request.data[field])
            updated.append(field)

    if not updated:
        return Response(
            {'detail': 'Nenhum campo valido para atualizacao.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    client.save(update_fields=updated + ['updated_at'])
    return Response(ClientPortalProfileSerializer(client).data)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def client_portal_change_password(request):
    """POST: altera senha do portal. Body: {old_password, new_password}."""
    client = _get_client_from_request(request)
    if not client:
        return Response(
            {'detail': 'Nao autenticado ou portal inativo.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    old_password = request.data.get('old_password', '')
    new_password = request.data.get('new_password', '')

    if not old_password or not new_password:
        return Response(
            {'detail': 'Os campos "old_password" e "new_password" sao obrigatorios.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not check_password(old_password, client.portal_password):
        return Response(
            {'detail': 'Senha atual incorreta.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(new_password) < 6:
        return Response(
            {'detail': 'A nova senha deve ter pelo menos 6 caracteres.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    client.portal_password = make_password(new_password)
    client.save(update_fields=['portal_password'])
    return Response({'detail': 'Senha alterada com sucesso.'})


# ─── Hearings ──────────────────────────────────────────────────────────────

@api_view(['GET'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def client_portal_hearings(request):
    """GET /api/v1/auth/client-portal/hearings/
    Retorna audiencias futuras de todos os casos do cliente."""
    client = _get_client_from_request(request)
    if not client:
        return Response(
            {'detail': 'Nao autenticado ou portal inativo.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    case_ids = LegalCase.objects.filter(client=client).values_list('id', flat=True)
    audiencias = Audiencia.objects.filter(
        caso_id__in=case_ids,
        data_hora__gte=timezone.now(),
        status='agendada',
    ).select_related('caso').order_by('data_hora')

    serializer = ClientPortalHearingSerializer(audiencias, many=True)
    return Response(serializer.data)


# ─── Copilot (Client AI Assistant) ───────────────────────────────────────

@api_view(['POST'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def client_portal_copilot(request):
    """POST /api/v1/auth/client-portal/copilot/
    Client Copilot - limited AI assistant for clients.
    Body: {message: string}"""
    client = _get_client_from_request(request)
    if not client:
        return Response(
            {'detail': 'Nao autenticado ou portal inativo.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    message = request.data.get('message', '').strip()
    if not message:
        return Response(
            {'detail': 'O campo "message" e obrigatorio.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    from apps.copilot.services.client_copilot_service import ClientCopilotService
    response = ClientCopilotService.generate_response(client, message)

    return Response({
        'response': response,
        'disclaimer': 'Este assistente fornece informações gerais. Para orientação jurídica, consulte seu advogado.',
    })


@api_view(['GET'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def client_portal_copilot_suggestions(request):
    """GET /api/v1/auth/client-portal/copilot/sugestoes/
    Returns suggested questions/actions for the client based on their current state."""
    client = _get_client_from_request(request)
    if not client:
        return Response(
            {'detail': 'Nao autenticado ou portal inativo.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    suggestions = []

    # Check for upcoming deadlines
    upcoming = LegalDeadline.objects.filter(
        caso__client=client, status='pendente',
        data_prazo__gte=timezone.now().date()
    ).order_by('data_prazo').first()
    if upcoming:
        days = (upcoming.data_prazo - timezone.now().date()).days
        if days <= 7:
            suggestions.append({
                'icon': 'Clock',
                'text': f'Você tem um prazo em {days} dias: {upcoming.titulo}',
                'action': 'Qual o status dos meus prazos?',
                'priority': 'alta',
            })

    # Check for upcoming hearings
    hearing = Audiencia.objects.filter(
        caso__client=client, data_hora__gte=timezone.now()
    ).order_by('data_hora').first()
    if hearing:
        suggestions.append({
            'icon': 'Calendar',
            'text': f'Audiência marcada: {hearing.data_hora.strftime("%d/%m/%Y")}',
            'action': 'Tenho audiência marcada?',
            'priority': 'media',
        })

    # Check for unread messages
    unread = ClientMessage.objects.filter(
        client=client, sender_type='lawyer', is_read=False
    ).count()
    if unread > 0:
        suggestions.append({
            'icon': 'MessageSquare',
            'text': f'Você tem {unread} mensagem(ns) não lida(s) do advogado',
            'action': 'Ver mensagens',
            'priority': 'alta',
        })

    # Check pending contracts
    pending_contracts = LegalContract.objects.filter(
        client=client, status='pending_signature'
    ).count()
    if pending_contracts > 0:
        suggestions.append({
            'icon': 'PenTool',
            'text': f'{pending_contracts} contrato(s) aguardando sua assinatura',
            'action': 'Quais contratos preciso assinar?',
            'priority': 'alta',
        })

    # Default suggestions
    if not suggestions:
        suggestions = [
            {'icon': 'HelpCircle', 'text': 'Qual o status do meu processo?', 'action': 'Qual o status do meu processo?', 'priority': 'baixa'},
            {'icon': 'FileText', 'text': 'Preciso enviar algum documento?', 'action': 'Preciso enviar algum documento?', 'priority': 'baixa'},
            {'icon': 'MessageSquare', 'text': 'Quero falar com meu advogado', 'action': 'Quero falar com meu advogado', 'priority': 'baixa'},
        ]

    return Response({'suggestions': suggestions})
