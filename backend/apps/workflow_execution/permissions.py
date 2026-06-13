"""
Permissões baseadas em role para execução de fluxos.

Hierarquia (accounts/models.py):
  superadmin=100, admin=90, procurador_geral=85, subprocurador_geral=80,
  gerente=70, procurador=60, assessor_gerencial=50, assessor_gabinete=45,
  distribuidor=30, servidor=15, visualizador=1
"""
from rest_framework.permissions import BasePermission
from apps.accounts.models import User as CustomUser  # ajuste se nome diferente


def _role_level(user) -> int:
    """Retorna nível hierárquico do role do usuário."""
    from apps.accounts.models import User as CustomUser
    hierarchy = getattr(CustomUser, 'ROLE_HIERARCHY', {})
    role = getattr(user, 'role', 'visualizador')
    # Aplica aliases antes de buscar o nível
    aliases = getattr(CustomUser, 'ROLE_ALIASES', {})
    role = aliases.get(role, role)
    return hierarchy.get(role, 0)


def _is_admin(user) -> bool:
    """Verifica se o usuário é superadmin ou admin (acesso total)."""
    role = getattr(user, 'role', 'visualizador')
    aliases = getattr(CustomUser, 'ROLE_ALIASES', {})
    resolved = aliases.get(role, role)
    return resolved in ('superadmin', 'admin') or getattr(user, 'is_superuser', False)


def _has_permission(user, action: str) -> bool:
    """Verifica se usuário tem permissão para a ação específica."""
    from apps.accounts.models import User as CustomUser
    perms = getattr(CustomUser, 'ROLE_PERMISSIONS', {})
    allowed_roles = perms.get(action, [])
    role = getattr(user, 'role', 'visualizador')
    # Normaliza alias
    aliases = getattr(CustomUser, 'ROLE_ALIASES', {})
    role = aliases.get(role, role)
    return role in allowed_roles


class BelongsToOrgan(BasePermission):
    """Usuário deve estar vinculado a um órgão (superadmin/admin bypass)."""
    message = 'Usuário não está vinculado a um órgão.'

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        # Superadmin e admin sempre passam — podem não ter órgão
        if _is_admin(request.user):
            return True
        return bool(getattr(request.user, 'organ', None))


class CanStartFlow(BelongsToOrgan):
    """Pode iniciar fluxo: distribuidor ou superior."""
    message = 'Apenas distribuidores e superiores podem iniciar fluxos.'

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        # Superadmin/admin já passaram no super() — acesso total
        if _is_admin(request.user):
            return True
        return _role_level(request.user) >= 30  # distribuidor


class CanApproveRequests(BelongsToOrgan):
    """Pode aprovar/rejeitar redistribuições: gerente ou superior."""
    message = 'Apenas gerentes e superiores podem aprovar solicitações.'

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        # Superadmin/admin já passaram no super() — acesso total
        if _is_admin(request.user):
            return True
        return _role_level(request.user) >= 70  # gerente


class IsTaskAssigneeOrManager(BasePermission):
    """
    Pode completar uma task se:
    - É superadmin ou admin (acesso total)
    - É o usuário atribuído à task
    - OU tem nível de gerente ou superior no mesmo órgão
    """
    message = 'Apenas o responsável pela tarefa ou um gerente pode concluí-la.'

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False
        # Superadmin/admin — acesso total
        if _is_admin(user):
            return True
        # Assignee direto
        if obj.assigned_to and obj.assigned_to == user:
            return True
        # Gerente ou superior no mesmo órgão
        if (getattr(user, 'organ', None) and
                obj.instance.organ == user.organ and
                _role_level(user) >= 70):
            return True
        return False
