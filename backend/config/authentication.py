"""
Classes de autenticação customizadas
"""
from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    SessionAuthentication sem exigir CSRF token.
    Útil para permitir login via Session no Swagger sem conflitar com JWT.
    """
    def enforce_csrf(self, request):
        # Não força verificação de CSRF
        return
