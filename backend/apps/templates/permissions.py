"""
Permissions customizadas para templates
"""
from rest_framework import permissions
from apps.accounts.permissions import is_admin_or_manager


class CanManageDocumentTemplates(permissions.BasePermission):
    """
    Permissão para gerenciar templates de documentos
    - Leitura: Todos autenticados
    - Escrita: Apenas superadmin, admin e manager
    """
    def has_permission(self, request, view):
        # Leitura permitida para todos autenticados
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        # Escrita apenas para superadmin, admin e manager
        if request.user.is_authenticated and request.user.is_superuser:
            return True

        return (
            request.user.is_authenticated and
            is_admin_or_manager(request.user)
        )

    def has_object_permission(self, request, view, obj):
        # Leitura permitida para todos autenticados
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        # Escrita apenas para superadmin, admin e manager
        if request.user.is_authenticated and request.user.is_superuser:
            return True

        return (
            request.user.is_authenticated and
            is_admin_or_manager(request.user)
        )
