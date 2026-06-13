"""
Permissions para Documents
"""
from rest_framework import permissions
from apps.accounts.permissions import resolve_role


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permissão: Usuário pode ver/editar apenas seus próprios Documents
    Admin/Manager/Reviewer podem ver/editar todos
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Dono do ETP
        if obj.user == request.user:
            return True

        # Admin/Manager/Reviewer
        if request.user.is_superuser:
            return True
        resolved = resolve_role(request.user.role)
        return resolved in [
            'superadmin', 'admin', 'gestor', 'socio', 'procurador',
            'procurador_geral', 'subprocurador_geral', 'gerente',
            'coordenador', 'revisor', 'auditor', 'advogado_senior',
            'defensor', 'promotor', 'assessor_gerencial',
        ]
