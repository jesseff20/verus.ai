"""
Views para o fluxo de reset de senha.

Endpoints:
- POST request-password-reset/ — Solicita reset (informa e-mail)
- POST reset-password/ — Executa reset (token + nova senha)

Fluxo completo:
1. Usuário informa e-mail → recebe link com token (se existir)
2. Usuário clica no link → frontend captura ?token= da URL
3. Usuário informa nova senha → backend valida token e altera senha
"""
import logging

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from .serializers_password import RequestResetSerializer, ResetPasswordSerializer
from .services.token_service import gerar_token_reset_senha, validar_token_reset_senha
from .services.email_service import enviar_email_reset_senha, enviar_email_senha_alterada
from .throttles import PasswordResetRateThrottle

logger = logging.getLogger(__name__)
User = get_user_model()


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@throttle_classes([PasswordResetRateThrottle])
def request_password_reset(request):
    """
    Solicitação de reset de senha.

    Fluxo:
    1. Recebe e-mail do formulário
    2. Aplica rate limiting por IP
    3. Busca usuário pelo e-mail (sem revelar se existe)
    4. Gera token assinado com PASSWORD_RESET_SECRET
    5. Envia e-mail HTML com link de reset

    Por segurança, a resposta é sempre a mesma independente
    de o e-mail existir ou não (proteção contra enumeração).
    """
    serializer = RequestResetSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data['email']

    # Busca o usuário pelo e-mail
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Não revela se o e-mail existe ou não
        logger.info(
            'Tentativa de reset para e-mail não cadastrado: %s', email
        )
        return Response(
            {
                'message': (
                    'Se este e-mail estiver cadastrado no sistema, '
                    'você receberá um link para redefinir sua senha '
                    'em instantes. Verifique sua caixa de entrada e '
                    'a pasta de spam.'
                ),
            },
            status=status.HTTP_200_OK,
        )

    # Verifica se o usuário está ativo
    if not user.is_active:
        logger.warning(
            'Tentativa de reset para usuário inativo: id=%s, email=%s',
            user.id, email
        )
        return Response(
            {
                'message': (
                    'Se este e-mail estiver cadastrado no sistema, '
                    'você receberá um link para redefinir sua senha '
                    'em instantes. Verifique sua caixa de entrada e '
                    'a pasta de spam.'
                ),
            },
            status=status.HTTP_200_OK,
        )

    try:
        # Gera token assinado com PASSWORD_RESET_SECRET
        token = gerar_token_reset_senha(user, request)

        # Envia e-mail de reset
        nome_completo = user.get_full_name() or user.username
        enviar_email_reset_senha(
            destinatario=user.email,
            nome_usuario=nome_completo,
            token=token,
        )

        logger.info(
            'Reset de senha solicitado para usuário %s (email: %s) — '
            'token gerado e e-mail enviado',
            user.id, user.email
        )

    except Exception as e:
        logger.error(
            'Erro ao processar reset de senha para %s: %s',
            email, str(e)
        )
        # Não revela o erro para não vazar informações
        return Response(
            {
                'message': (
                    'Se este e-mail estiver cadastrado no sistema, '
                    'você receberá um link para redefinir sua senha '
                    'em instantes. Verifique sua caixa de entrada e '
                    'a pasta de spam.'
                ),
            },
            status=status.HTTP_200_OK,
        )

    return Response(
        {
            'message': (
                'Se este e-mail estiver cadastrado no sistema, '
                'você receberá um link para redefinir sua senha '
                'em instantes. Verifique sua caixa de entrada e '
                'a pasta de spam.'
            ),
        },
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def reset_password(request):
    """
    Execução do reset de senha.

    O frontend deve:
    1. Capturar o parâmetro ?token= da URL
    2. Exibir formulário para nova senha
    3. Enviar token + nova senha para este endpoint

    Fluxo:
    1. Recebe token + nova senha + confirmação
    2. Valida token (assinatura com PASSWORD_RESET_SECRET)
    3. Valida expiração (1h por padrão)
    4. Valida hash antifraude (replay prevention)
    5. Busca usuário pelo ID do token
    6. Aplica hash seguro (HASH_COST=12) com set_password()
    7. Salva nova senha
    8. Invalida tokens anteriores (muda updated_at — rotating secret via timestamp)
    9. Envia e-mail de segurança informando alteração
    """
    serializer = ResetPasswordSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    token = serializer.validated_data['token']
    nova_senha = serializer.validated_data['password']

    # Valida o token (assinatura, expiração, hash antifraude)
    payload = validar_token_reset_senha(token, request=request)

    if payload is None:
        logger.warning(
            'Tentativa de reset com token inválido/expirado. IP: %s',
            request.META.get('REMOTE_ADDR', 'desconhecido')
        )
        return Response(
            {
                'error': (
                    'Link inválido ou expirado. Solicite um novo '
                    'reset de senha.'
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

    # Verifica se o usuário está ativo
    if not user.is_active:
        logger.warning(
            'Tentativa de reset para usuário inativo: id=%s', user.id
        )
        return Response(
            {
                'error': (
                    'Esta conta está desativada. '
                    'Contate o suporte para reativá-la.'
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Aplica hash seguro da nova senha (HASH_COST=12 via bcrypt)
        user.set_password(nova_senha)

        # Invalida tokens anteriores: atualiza updated_at para quebrar
        # qualquer token gerado antes desta alteração.
        # Isto funciona como "rotating secret via timestamp" — tokens
        # antigos continuam válidos em termos de assinatura, mas o
        # fluxo de validação no frontend + backend garante que apenas
        # tokens recentes sejam aceitos.
        user.save(update_fields=['password', 'updated_at'])

        logger.info(
            'Senha alterada com sucesso para usuário %s (email: %s)',
            user.id, user.email
        )

        # Envia e-mail de segurança informando que a senha foi alterada
        try:
            nome_completo = user.get_full_name() or user.username
            enviar_email_senha_alterada(
                destinatario=user.email,
                nome_usuario=nome_completo,
            )
        except Exception as e:
            # Falha no e-mail de confirmação não impede a alteração
            logger.warning(
                'Senha alterada para usuário %s, mas falha ao enviar '
                'e-mail de confirmação: %s',
                user.id, str(e)
            )

        return Response(
            {
                'message': (
                    'Senha redefinida com sucesso! '
                    'Você já pode fazer login com sua nova senha.'
                ),
                'email': user.email,
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(
            'Erro ao alterar senha do usuário %s: %s',
            user.id, str(e)
        )
        return Response(
            {'error': 'Erro ao redefinir senha. Tente novamente.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
