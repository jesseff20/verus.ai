"""
Serviço de geração e validação de tokens assinados.

Usa EMAIL_TOKEN_SECRET para tokens de confirmação de e-mail e
PASSWORD_RESET_SECRET para tokens de reset de senha.

Tokens JWT contêm:
- userId: ID do usuário
- email: e-mail associado
- hash: hash antifraude (user-agent + IP)
- exp: expiração configurável
- type: tipo do token (email_confirm | password_reset)
"""
import hashlib
import logging
from datetime import datetime, timedelta

import jwt
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def _get_env(name, default=None):
    """Retorna variável de ambiente do settings ou default."""
    return getattr(settings, name, default) or default


def gerar_token_confirmacao(user, request):
    """
    Gera token JWT assinado para confirmação de e-mail.

    Args:
        user: Instância do User recém-criado
        request: Objeto HttpRequest (para extrair IP e User-Agent)

    Returns:
        String do token JWT
    """
    # Lê segredo do .env (configurado em settings via env())
    secret = _get_env('EMAIL_TOKEN_SECRET', 'fallback-dev-secret')
    expiracao_dias = 30  # TOKEN_EXPIRATION_CONFIRM=30d

    # Gera hash antifraude: combinação de user-agent + IP
    user_agent = request.META.get('HTTP_USER_AGENT', '') or ''
    ip = obter_ip(request)
    hash_antifraude = hashlib.sha256(
        f"{user_agent}|{ip}".encode('utf-8')
    ).hexdigest()

    # Payload do token
    payload = {
        'userId': user.id,
        'email': user.email,
        'hash': hash_antifraude,
        'type': 'email_confirm',
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(days=expiracao_dias),
    }

    token = jwt.encode(payload, secret, algorithm='HS256')
    logger.info(
        'Token de confirmação gerado para usuário %s (email: %s)',
        user.id, user.email
    )
    return token


def validar_token_confirmacao(token, request=None):
    """
    Valida token de confirmação de e-mail.

    Verifica:
    1. Assinatura → integridade do token
    2. Expiração → token não venceu
    3. Hash antifraude → replay prevention (se request for fornecido)

    Args:
        token: String do token JWT
        request: Opcional — HttpRequest para validar hash antifraude

    Returns:
        dict com 'userId', 'email' se válido
        None se inválido/expirado
    """
    secret = _get_env('EMAIL_TOKEN_SECRET', 'fallback-dev-secret')

    try:
        payload = jwt.decode(token, secret, algorithms=['HS256'])

        # Verifica se é um token de confirmação de e-mail
        if payload.get('type') != 'email_confirm':
            logger.warning('Token inválido: type não é email_confirm')
            return None

        # Verifica expiração
        exp = payload.get('exp')
        if exp:
            exp_dt = datetime.utcfromtimestamp(exp)
            if exp_dt < datetime.utcnow():
                logger.warning('Token expirado para userId=%s', payload.get('userId'))
                return None

        # Se request foi fornecido, valida hash antifraude (replay prevention)
        if request is not None:
            user_agent = request.META.get('HTTP_USER_AGENT', '') or ''
            ip = obter_ip(request)
            hash_esperado = hashlib.sha256(
                f"{user_agent}|{ip}".encode('utf-8')
            ).hexdigest()

            if payload.get('hash') != hash_esperado:
                logger.warning(
                    'Hash antifraude não corresponde para userId=%s. '
                    'Possível tentativa de replay.',
                    payload.get('userId')
                )
                return None

        logger.info(
            'Token validado com sucesso para userId=%s, email=%s',
            payload.get('userId'), payload.get('email')
        )
        return {
            'userId': payload.get('userId'),
            'email': payload.get('email'),
        }

    except jwt.ExpiredSignatureError:
        logger.warning('Token expirado (ExpiredSignatureError)')
        return None
    except jwt.InvalidTokenError as e:
        logger.warning('Token inválido: %s', str(e))
        return None


def obter_ip(request):
    """
    Extrai o IP real do cliente, considerando proxies reversos.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Pega o primeiro IP da lista (cliente original)
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


# =============================================================================
# FUNÇÕES PARA RESET DE SENHA
# =============================================================================


def _calcular_expiracao_reset():
    """
    Calcula o timedelta de expiração para tokens de reset de senha.
    Lê TOKEN_EXPIRATION_RESET do settings ou usa 1 hora como padrão.
    """
    exp_str = getattr(settings, 'TOKEN_EXPIRATION_RESET', '1h')
    exp_str = str(exp_str).strip().lower()

    if exp_str.endswith('d'):
        return timedelta(days=int(exp_str.replace('d', '')))
    elif exp_str.endswith('h'):
        return timedelta(hours=int(exp_str.replace('h', '')))
    elif exp_str.endswith('m'):
        return timedelta(minutes=int(exp_str.replace('m', '')))
    else:
        return timedelta(hours=1)


def gerar_token_reset_senha(user, request):
    """
    Gera token JWT assinado para reset de senha.

    Usa PASSWORD_RESET_SECRET (separado do EMAIL_TOKEN_SECRET,
    permitindo rotating secrets independentemente).

    Args:
        user: Instância do User que solicitou reset
        request: Objeto HttpRequest (para extrair IP e User-Agent)

    Returns:
        String do token JWT
    """
    secret = _get_env('PASSWORD_RESET_SECRET', 'fallback-reset-dev-secret')
    expiracao = _calcular_expiracao_reset()

    # Gera hash antifraude: combinação de user-agent + IP
    user_agent = request.META.get('HTTP_USER_AGENT', '') or ''
    ip = obter_ip(request)
    hash_antifraude = hashlib.sha256(
        f"{user_agent}|{ip}".encode('utf-8')
    ).hexdigest()

    # Payload do token
    payload = {
        'userId': user.id,
        'email': user.email,
        'hash': hash_antifraude,
        'type': 'password_reset',
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + expiracao,
    }

    token = jwt.encode(payload, secret, algorithm='HS256')
    logger.info(
        'Token de reset de senha gerado para usuário %s (email: %s)',
        user.id, user.email
    )
    return token


def validar_token_reset_senha(token, request=None):
    """
    Valida token de reset de senha.

    Usa PASSWORD_RESET_SECRET (separado do EMAIL_TOKEN_SECRET).

    Verifica:
    1. Assinatura com PASSWORD_RESET_SECRET → integridade do token
    2. type == 'password_reset' → token correto para este fluxo
    3. Expiração → token não venceu
    4. Hash antifraude → replay prevention (se request for fornecido)

    Args:
        token: String do token JWT
        request: Opcional — HttpRequest para validar hash antifraude

    Returns:
        dict com 'userId', 'email' se válido
        None se inválido/expirado
    """
    secret = _get_env('PASSWORD_RESET_SECRET', 'fallback-reset-dev-secret')

    try:
        payload = jwt.decode(token, secret, algorithms=['HS256'])

        # Verifica se é um token de reset de senha
        if payload.get('type') != 'password_reset':
            logger.warning('Token inválido: type não é password_reset')
            return None

        # Verifica expiração
        exp = payload.get('exp')
        if exp:
            exp_dt = datetime.utcfromtimestamp(exp)
            if exp_dt < datetime.utcnow():
                logger.warning(
                    'Token de reset expirado para userId=%s',
                    payload.get('userId')
                )
                return None

        # Se request foi fornecido, valida hash antifraude
        if request is not None:
            user_agent = request.META.get('HTTP_USER_AGENT', '') or ''
            ip = obter_ip(request)
            hash_esperado = hashlib.sha256(
                f"{user_agent}|{ip}".encode('utf-8')
            ).hexdigest()

            if payload.get('hash') != hash_esperado:
                logger.warning(
                    'Hash antifraude não corresponde para userId=%s. '
                    'Possível tentativa de replay no reset de senha.',
                    payload.get('userId')
                )
                return None

        logger.info(
            'Token de reset validado com sucesso para userId=%s, email=%s',
            payload.get('userId'), payload.get('email')
        )
        return {
            'userId': payload.get('userId'),
            'email': payload.get('email'),
        }

    except jwt.ExpiredSignatureError:
        logger.warning('Token de reset expirado (ExpiredSignatureError)')
        return None
    except jwt.InvalidTokenError as e:
        logger.warning('Token de reset inválido: %s', str(e))
        return None
