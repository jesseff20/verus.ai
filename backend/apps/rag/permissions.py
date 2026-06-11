"""
Permissions para RAG
"""
from rest_framework import permissions
from apps.accounts.permissions import is_admin_or_manager


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permissão: Usuário pode ver/editar apenas suas próprias queries/contextos
    Admin/Manager podem ver/editar todos
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Dono do objeto
        if obj.user == request.user:
            return True

        # Admin/Manager
        if request.user.is_superuser:
            return True
        return is_admin_or_manager(request.user)
