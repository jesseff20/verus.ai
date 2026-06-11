"""
Permissions customizadas para Knowledge Base
"""
from rest_framework import permissions
from apps.accounts.permissions import is_admin_or_manager


class CanManageDocuments(permissions.BasePermission):
    """
    Permissão para gerenciar documentos da KB
    - Leitura: Todos autenticados (apenas documentos públicos ou próprios)
    - Upload: Todos autenticados
    - Edição/Exclusão: Apenas criador, admin ou manager
    """
    def has_permission(self, request, view):
        # Todos autenticados podem ler e criar
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Leitura: público OU criador OU admin/manager
        if request.method in permissions.SAFE_METHODS:
            if obj.is_public:
                return True
            if obj.uploaded_by == request.user:
                return True
            if request.user.is_superuser:
                return True
            return is_admin_or_manager(request.user)

        # Escrita: apenas criador OU admin/manager
        if obj.uploaded_by == request.user:
            return True
        if request.user.is_superuser:
            return True
        return is_admin_or_manager(request.user)
