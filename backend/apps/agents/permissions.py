"""
Permissions para Agents
"""
from rest_framework import permissions
from apps.accounts.permissions import is_admin_or_manager


class CanManageAgentPrompts(permissions.BasePermission):
    """
    Leitura: Todos autenticados
    Escrita: Admin/Manager
    Execução/Chat/Feedback: Todos autenticados
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Actions permitidas para todos os usuários autenticados
        if view.action in ['execute', 'chat', 'feedback']:
            return True

        # Leitura permitida para todos
        if request.method in permissions.SAFE_METHODS:
            return True

        # Escrita apenas admin/manager
        return is_admin_or_manager(request.user)
