import uuid
import threading

# Thread-local storage para contexto de auditoria
_audit_context = threading.local()


def get_audit_context():
    """Retorna o contexto de auditoria da thread atual."""
    return getattr(_audit_context, 'data', {})


def set_audit_context(**kwargs):
    """Define o contexto de auditoria para a thread atual."""
    if not hasattr(_audit_context, 'data'):
        _audit_context.data = {}
    _audit_context.data.update(kwargs)


def clear_audit_context():
    """Limpa o contexto de auditoria da thread atual."""
    _audit_context.data = {}


class AuditMiddleware:
    """
    Middleware que captura automaticamente contexto para auditoria.

    Adiciona ao request:
    - audit_request_id: ID unico para correlacao
    - audit_ip: IP do cliente
    - audit_user_agent: User agent do cliente
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Gerar request_id unico
        request_id = str(uuid.uuid4())[:8]

        # Capturar IP do cliente
        ip_address = self._get_client_ip(request)

        # Capturar user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Adicionar ao request
        request.audit_request_id = request_id
        request.audit_ip = ip_address
        request.audit_user_agent = user_agent

        # Definir contexto thread-local para uso em services
        set_audit_context(
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            user=getattr(request, 'user', None)
        )

        response = self.get_response(request)

        # Limpar contexto apos a resposta
        clear_audit_context()

        return response

    def _get_client_ip(self, request):
        """Extrai o IP real do cliente, considerando proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
