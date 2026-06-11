"""
Rate limiting customizado para endpoints de autenticação.

Usa as variáveis RATE_LIMIT_MAX e RATE_LIMIT_WINDOW do .env.
Aplica limites por IP e por e-mail para prevenir abuso nos endpoints
de registro e confirmação.
"""
from django.conf import settings
from rest_framework.throttling import SimpleRateThrottle


def _get_env(name, default=None):
    """Retorna variável de ambiente do settings ou default."""
    return getattr(settings, name, default) or default


class RegisterRateThrottle(SimpleRateThrottle):
    """
    Limita requisições de registro por IP.

    Previne cadastro em massa e brute force.
    Taxa configurável via RATE_LIMIT_MAX e RATE_LIMIT_WINDOW no .env.
    """
    scope = 'register'

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)  # IP do cliente
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident,
        }

    def parse_rate(self, rate):
        """
        Taxa customizada baseada nas variáveis de ambiente.
        Default: 5 requisições a cada 60000ms (1 minuto).
        """
        rate_limit_max = int(_get_env('RATE_LIMIT_MAX', 5))
        rate_limit_window_ms = int(_get_env('RATE_LIMIT_WINDOW', 60000))

        # Converte ms para segundos
        rate_limit_window_sec = max(1, rate_limit_window_ms // 1000)

        return (rate_limit_max, rate_limit_window_sec)


class ConfirmEmailRateThrottle(SimpleRateThrottle):
    """
    Limita tentativas de confirmação de e-mail por IP.

    Previne força bruta no token de confirmação.
    """
    scope = 'confirm_email'

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident,
        }

    def parse_rate(self, rate):
        """10 tentativas por minuto."""
        return (10, 60)


class PasswordResetRateThrottle(SimpleRateThrottle):
    """
    Limita solicitações de reset de senha por IP.

    Previne abuso no endpoint de solicitação de reset.
    Usa a mesma configuração de RATE_LIMIT_MAX e RATE_LIMIT_WINDOW
    do registro (padrão: 5 requisições a cada 60s).
    """
    scope = 'password_reset'

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident,
        }

    def parse_rate(self, rate):
        """Taxa configurável via .env, igual ao register."""
        rate_limit_max = int(_get_env('RATE_LIMIT_MAX', 5))
        rate_limit_window_ms = int(_get_env('RATE_LIMIT_WINDOW', 60000))
        rate_limit_window_sec = max(1, rate_limit_window_ms // 1000)
        return (rate_limit_max, rate_limit_window_sec)
