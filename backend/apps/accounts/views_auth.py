"""
Views para fluxo de autenticação com confirmação de e-mail.

Endpoints:
- POST /api/v1/auth/register-with-confirm/ — Registro com envio de e-mail
- POST /api/v1/auth/confirm-email/ — Confirmação de e-mail via token
"""
import logging

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from .serializers_auth import RegisterWithConfirmSerializer, ConfirmEmailSerializer
from .services.token_service import gerar_token_confirmacao, validar_token_confirmacao
from .services.email_service import enviar_email_confirmacao, enviar_email_boas_vindas
from .throttles import RegisterRateThrottle, ConfirmEmailRateThrottle

logger = logging.getLogger(__name__)
User = get_user_model()


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@throttle_classes([RegisterRateThrottle])
def register_with_confirm(request):
    """
    Registro de novo usuário com confirmação de e-mail.

    Fluxo:
    1. Valida dados do formulário
    2. Aplica rate limiting por IP
    3. Cria o usuário em estado 'pendente' (is_active=False)
    4. Gera token assinado com EMAIL_TOKEN_SECRET
    5. Envia e-mail com link de confirmação

    O usuário só poderá fazer login após confirmar o e-mail.
    """
    serializer = RegisterWithConfirmSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Cria o usuário pendente
    user = serializer.save()

    try:
        # Gera token assinado com userId, email e hash antifraude
        token = gerar_token_confirmacao(user, request)

        # Envia e-mail de confirmação
        nome_completo = user.get_full_name() or user.username
        enviar_email_confirmacao(
            destinatario=user.email,
            nome_usuario=nome_completo,
            token=token,
        )

        logger.info(
            'Registro com confirmação: usuário %s (email: %s) — token gerado e e-mail enviado',
            user.id, user.email
        )

        return Response(
            {
                'message': (
                    'Conta criada com sucesso! Enviamos um e-mail de confirmação para '
                    f'{user.email}. Verifique sua caixa de entrada e clique no link '
                    'para ativar sua conta. O link expira em 30 dias.'
                ),
                'user_id': user.id,
                'email': user.email,
            },
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        # Se falhar ao enviar e-mail, remove o usuário criado
        logger.error(
            'Erro ao processar registro de %s: %s. Removendo usuário...',
            user.email, str(e)
        )
        user.delete()
        return Response(
            {'error': 'Erro ao processar registro. Tente novamente mais tarde.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@throttle_classes([ConfirmEmailRateThrottle])
def confirm_email(request):
    """
    Confirmação de e-mail via token JWT.

    Fluxo:
    1. Recebe token do link clicado pelo usuário
    2. Valida assinatura do token (EMAIL_TOKEN_SECRET)
    3. Valida expiração (30 dias)
    4. Valida hash antifraude (user-agent + IP)
    5. Ativa o usuário (is_active=True)
    6. Envia e-mail de boas-vindas

    Requer o token como parâmetro POST.
    O link original é: ${APP_BASE_URL}/auth/confirm?token=<TOKEN>
    O frontend deve capturar o ?token= da URL e enviar para este endpoint.
    """
    serializer = ConfirmEmailSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    token = serializer.validated_data['token']

    # Valida o token (assinatura, expiração, hash antifraude)
    payload = validar_token_confirmacao(token, request=request)

    if payload is None:
        logger.warning(
            'Tentativa de confirmação com token inválido/expirado. IP: %s',
            request.META.get('REMOTE_ADDR', 'desconhecido')
        )
        return Response(
            {
                'error': (
                    'Token inválido ou expirado. Solicite um novo link de '
                    'confirmação.'
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Busca o usuário pelo ID contido no token
    user_id = payload.get('userId')
    email_token = payload.get('email')

    try:
        user = User.objects.get(id=user_id, email=email_token)
    except User.DoesNotExist:
        logger.warning(
            'Token válido, mas usuário não encontrado: id=%s, email=%s',
            user_id, email_token
        )
        return Response(
            {'error': 'Usuário não encontrado. Contate o suporte.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Verifica se o usuário já está ativo
    if user.is_active:
        logger.info(
            'Usuário %s já está ativo. Token reutilizado?', user.id
        )
        return Response(
            {
                'message': (
                    'Sua conta já está ativa. Faça login para acessar o '
                    'sistema.'
                ),
                'already_active': True,
            },
            status=status.HTTP_200_OK,
        )

    # Ativa o usuário
    user.is_active = True
    user.save(update_fields=['is_active'])

    logger.info(
        'Usuário %s ativado com sucesso via confirmação de e-mail.',
        user.id
    )

    # Envia e-mail de boas-vindas
    try:
        nome_completo = user.get_full_name() or user.username
        enviar_email_boas_vindas(
            destinatario=user.email,
            nome_usuario=nome_completo,
        )
    except Exception as e:
        # Falha no e-mail de boas-vindas não impede a ativação
        logger.warning(
            'Usuário %s ativado, mas falha ao enviar e-mail de boas-vindas: %s',
            user.id, str(e)
        )

    return Response(
        {
            'message': (
                'E-mail confirmado com sucesso! Sua conta está ativa. '
                'Você já pode fazer login no sistema.'
            ),
            'email': user.email,
        },
        status=status.HTTP_200_OK,
    )
