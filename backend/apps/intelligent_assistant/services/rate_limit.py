"""
Utilitário de rate limiting para endpoints do Assistente Inteligente.

Implementa controle de taxa simples baseado em cache do Django (memória/redis).
Limita requisições por usuário por minuto para endpoints de geração.
"""
import logging
import time
from functools import wraps

from django.core.cache import cache as django_cache
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def rate_limit(key_prefix: str = 'rl', max_requests: int = 10, window_seconds: int = 60):
    """
    Decorator para limitar taxa de requisições por usuário.

    Args:
        key_prefix: Prefixo da chave no cache
        max_requests: Número máximo de requisições na janela
        window_seconds: Tamanho da janela em segundos

    Uso:
        @api_view(['POST'])
        @rate_limit('generate', max_requests=6, window_seconds=60)
        def my_endpoint(request):
            ...

    Retorna 429 Too Many Requests se excedido.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user_id = None
            if hasattr(request, 'user') and request.user.is_authenticated:
                user_id = str(request.user.id)
            else:
                # Fallback: usar IP
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
                user_id = x_forwarded_for.split(',')[0].strip() or request.META.get('REMOTE_ADDR', 'unknown')

            cache_key = f'{key_prefix}:{user_id}:{int(time.time() / window_seconds)}'

            try:
                count = django_cache.get(cache_key, 0)
            except Exception:
                logger.warning("Cache read failed for rate limit key %s", cache_key, exc_info=True)
                count = 0

            if count >= max_requests:
                retry_after = window_seconds - (int(time.time()) % window_seconds)
                logger.warning(
                    f"Rate limit excedido para {user_id} em {key_prefix}: "
                    f"{count}/{max_requests} em {window_seconds}s"
                )
                return JsonResponse(
                    {
                        'error': f'Limite de requisições excedido. '
                                 f'Máximo de {max_requests} requisições a cada {window_seconds}s. '
                                 f'Tente novamente em {retry_after}s.',
                        'retry_after_seconds': retry_after,
                    },
                    status=429,
                )

            django_cache.set(cache_key, count + 1, timeout=window_seconds)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def check_rate_limit(request, key_prefix: str = 'rl', max_requests: int = 10, window_seconds: int = 60) -> dict:
    """
    Função utilitária para verificação de rate limit em streaming endpoints.

    Retorna dict com {'allowed': True/False, 'retry_after': N} em vez de retornar
    a resposta HTTP diretamente, para uso em endpoints SSE/streaming.

    Uso:
        check = check_rate_limit(request, 'generate-stream', max_requests=6)
        if not check['allowed']:
            yield f"data: {json.dumps({'error': 'rate limit', ...})}\\n\\n"
            return
    """
    user_id = None
    if hasattr(request, 'user') and request.user.is_authenticated:
        user_id = str(request.user.id)
    else:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
        user_id = x_forwarded_for.split(',')[0].strip() or request.META.get('REMOTE_ADDR', 'unknown')

    cache_key = f'{key_prefix}:{user_id}:{int(time.time() / window_seconds)}'

    try:
        count = django_cache.get(cache_key, 0)
    except Exception:
        logger.warning("Cache read failed for stream rate limit key %s", cache_key, exc_info=True)
        count = 0

    if count >= max_requests:
        retry_after = window_seconds - (int(time.time()) % window_seconds)
        logger.warning(
            f"Rate limit excedido (stream) para {user_id} em {key_prefix}: "
            f"{count}/{max_requests} em {window_seconds}s"
        )
        return {'allowed': False, 'retry_after': retry_after}

    django_cache.set(cache_key, count + 1, timeout=window_seconds)
    return {'allowed': True, 'retry_after': 0}
