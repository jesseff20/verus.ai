from typing import Optional, Any
from django.db.models import Model
from django.contrib.auth import get_user_model

from apps.core.models import AuditLog
from apps.core.middleware import get_audit_context

User = get_user_model()


class AuditService:
    """
    Servico centralizado para registrar auditoria.

    Uso basico:
        AuditService.log(
            request=request,
            action='create',
            entity=document,
            description='Documento criado'
        )

    Ou usando o contexto automatico (sem request):
        AuditService.log_action(
            action='generate',
            entity_type='Document',
            entity_id=str(doc.id),
            entity_name=doc.title,
            description='PDF gerado'
        )
    """

    @classmethod
    def log(
        cls,
        request,
        action: str,
        entity: Model,
        description: str,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        severity: str = 'info',
        metadata: Optional[dict] = None
    ) -> AuditLog:
        """
        Registra uma acao de auditoria a partir de um request.

        Args:
            request: HttpRequest do Django
            action: Tipo da acao (create, update, delete, etc.)
            entity: Instancia do modelo afetado
            description: Descricao legivel da acao
            old_values: Valores anteriores (para updates)
            new_values: Novos valores (para updates)
            severity: info, warning, error, critical
            metadata: Dados adicionais

        Returns:
            AuditLog: Registro criado
        """
        user = getattr(request, 'user', None)
        if user and not user.is_authenticated:
            user = None

        user_email = ''
        user_role = ''
        if user:
            user_email = user.email
            # Pegar role do usuario se existir
            if hasattr(user, 'role'):
                user_role = user.role
            elif hasattr(user, 'roles') and user.roles.exists():
                user_role = user.roles.first().name

        return AuditLog.objects.create(
            user=user,
            user_email=user_email,
            user_role=user_role,
            action=action,
            severity=severity,
            entity_type=entity.__class__.__name__,
            entity_id=str(entity.pk),
            entity_name=cls._get_entity_name(entity),
            description=description,
            old_values=old_values,
            new_values=new_values,
            metadata=metadata or {},
            ip_address=getattr(request, 'audit_ip', None),
            user_agent=getattr(request, 'audit_user_agent', ''),
            request_id=getattr(request, 'audit_request_id', ''),
        )

    @classmethod
    def log_action(
        cls,
        action: str,
        entity_type: str,
        entity_id: str,
        description: str,
        entity_name: str = '',
        user: Optional[User] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        severity: str = 'info',
        metadata: Optional[dict] = None
    ) -> AuditLog:
        """
        Registra uma acao usando contexto automatico (sem request).

        Util para:
        - Celery tasks
        - Signals
        - Comandos de gerenciamento
        """
        context = get_audit_context()

        # Se user nao foi passado, tenta pegar do contexto
        if user is None:
            user = context.get('user')
            if user and not getattr(user, 'is_authenticated', False):
                user = None

        user_email = ''
        user_role = ''
        if user:
            user_email = user.email
            if hasattr(user, 'role'):
                user_role = user.role
            elif hasattr(user, 'roles') and user.roles.exists():
                user_role = user.roles.first().name

        return AuditLog.objects.create(
            user=user,
            user_email=user_email,
            user_role=user_role,
            action=action,
            severity=severity,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            description=description,
            old_values=old_values,
            new_values=new_values,
            metadata=metadata or {},
            ip_address=context.get('ip_address'),
            user_agent=context.get('user_agent', ''),
            request_id=context.get('request_id', ''),
        )

    @classmethod
    def log_document_action(
        cls,
        request,
        action: str,
        document,
        description: str = None,
        **kwargs
    ) -> AuditLog:
        """Atalho para acoes em documentos."""
        if description is None:
            action_descriptions = {
                'create': f'Documento "{document}" criado',
                'update': f'Documento "{document}" atualizado',
                'delete': f'Documento "{document}" excluido',
                'generate': f'PDF do documento "{document}" gerado',
                'download': f'Documento "{document}" baixado',
                'submit': f'Documento "{document}" submetido para revisao',
                'approve': f'Documento "{document}" aprovado',
                'reject': f'Documento "{document}" rejeitado',
                'publish': f'Documento "{document}" publicado',
            }
            description = action_descriptions.get(action, f'Acao "{action}" em "{document}"')

        return cls.log(
            request=request,
            action=action,
            entity=document,
            description=description,
            **kwargs
        )

    @classmethod
    def log_auth_action(
        cls,
        request,
        action: str,
        user,
        description: str = None,
        severity: str = 'info',
        **kwargs
    ) -> AuditLog:
        """Atalho para acoes de autenticacao."""
        if description is None:
            action_descriptions = {
                'login': f'Usuario {user.email} fez login',
                'logout': f'Usuario {user.email} fez logout',
                'login_failed': f'Tentativa de login falhou para {user.email}',
                'password_change': f'Usuario {user.email} alterou a senha',
            }
            description = action_descriptions.get(action, f'Acao de auth: {action}')

        if action == 'login_failed':
            severity = 'warning'

        return cls.log(
            request=request,
            action=action,
            entity=user,
            description=description,
            severity=severity,
            **kwargs
        )

    @classmethod
    def get_entity_history(cls, entity_type: str, entity_id: str, limit: int = 50):
        """Retorna historico completo de uma entidade."""
        return AuditLog.objects.filter(
            entity_type=entity_type,
            entity_id=entity_id
        ).order_by('-created_at')[:limit]

    @classmethod
    def get_user_activity(cls, user, days: int = 30, limit: int = 100):
        """Retorna atividade recente de um usuario."""
        from django.utils import timezone
        from datetime import timedelta

        since = timezone.now() - timedelta(days=days)

        return AuditLog.objects.filter(
            user=user,
            created_at__gte=since
        ).order_by('-created_at')[:limit]

    @classmethod
    def _get_entity_name(cls, entity: Model) -> str:
        """Tenta extrair um nome legivel da entidade."""
        # Tenta varios atributos comuns
        for attr in ['title', 'name', 'nome', 'email', 'numero', '__str__']:
            if attr == '__str__':
                return str(entity)[:255]
            if hasattr(entity, attr):
                value = getattr(entity, attr)
                if value:
                    return str(value)[:255]
        return str(entity.pk)
