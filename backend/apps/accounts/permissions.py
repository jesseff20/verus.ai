"""
Sistema de Permissões Granular do Verus.AI

Define permissões específicas por funcionalidade e role.
"""
from rest_framework import permissions


# =============================================================================
# DEFINIÇÃO DAS PERMISSÕES POR ROLE
# =============================================================================

# Mapeamento de roles antigos para novos (backwards compatibility)
ROLE_ALIASES = {
    'manager': 'gestor',
    'reviewer': 'revisor',
    'analyst': 'analista',
    'viewer': 'visualizador',
}

# Permissões completas para acesso total (superadmin/admin)
_FULL_ACCESS = {
    'dashboard.view': True,
    'assistant.use': True,
    'assistant.configure': True,
    'document_generators.use': True,
    'document_generators.configure': True,
    'form_assistants.use': True,
    'form_assistants.configure': True,
    'documents.create': True,
    'documents.view_own': True,
    'documents.view_all': True,
    'documents.edit_own': True,
    'documents.edit_all': True,
    'documents.delete_own': True,
    'documents.delete_all': True,
    'documents.approve': True,
    'documents.export': True,
    'templates.view': True,
    'templates.create': True,
    'templates.edit': True,
    'templates.delete': True,
    'forms.view': True,
    'forms.create': True,
    'forms.edit': True,
    'forms.delete': True,
    'knowledge_base.view': True,
    'knowledge_base.create': True,
    'knowledge_base.edit': True,
    'knowledge_base.delete': True,
    'agents.view': True,
    'agents.create': True,
    'agents.edit': True,
    'agents.delete': True,
    'users.view': True,
    'users.create': True,
    'users.edit': True,
    'users.delete': True,
    'settings.view': True,
    'settings.edit': True,
    'analytics.view': True,
    'analytics.export': True,
}

# Permissões de gestão (gestor/coordenador)
_MANAGEMENT_ACCESS = {
    'dashboard.view': True,
    'assistant.use': False,
    'assistant.configure': True,
    'document_generators.use': False,
    'document_generators.configure': True,
    'form_assistants.use': False,
    'form_assistants.configure': True,
    'documents.create': False,
    'documents.view_own': True,
    'documents.view_all': True,
    'documents.edit_own': False,
    'documents.edit_all': False,
    'documents.delete_own': False,
    'documents.delete_all': False,
    'documents.approve': False,
    'documents.export': True,
    'templates.view': False,
    'templates.create': False,
    'templates.edit': False,
    'templates.delete': False,
    'forms.view': False,
    'forms.create': False,
    'forms.edit': False,
    'forms.delete': False,
    'knowledge_base.view': True,
    'knowledge_base.create': False,
    'knowledge_base.edit': False,
    'knowledge_base.delete': False,
    'agents.view': True,
    'agents.create': True,
    'agents.edit': True,
    'agents.delete': True,
    'users.view': True,
    'users.create': True,
    'users.edit': True,
    'users.delete': True,
    'settings.view': True,
    'settings.edit': True,
    'analytics.view': True,
    'analytics.export': True,
}

# Permissões de advogado/operador (cria e edita documentos, usa IA)
_OPERATOR_ACCESS = {
    'dashboard.view': True,
    'assistant.use': True,
    'assistant.configure': False,
    'document_generators.use': True,
    'document_generators.configure': False,
    'form_assistants.use': True,
    'form_assistants.configure': False,
    'documents.create': True,
    'documents.view_own': True,
    'documents.view_all': False,
    'documents.edit_own': True,
    'documents.edit_all': False,
    'documents.delete_own': True,
    'documents.delete_all': False,
    'documents.approve': False,
    'documents.export': True,
    'templates.view': True,
    'templates.create': False,
    'templates.edit': False,
    'templates.delete': False,
    'forms.view': True,
    'forms.create': False,
    'forms.edit': False,
    'forms.delete': False,
    'knowledge_base.view': True,
    'knowledge_base.create': True,
    'knowledge_base.edit': True,
    'knowledge_base.delete': False,
    'agents.view': False,
    'agents.create': False,
    'agents.edit': False,
    'agents.delete': False,
    'users.view': False,
    'users.create': False,
    'users.edit': False,
    'users.delete': False,
    'settings.view': False,
    'settings.edit': False,
    'analytics.view': False,
    'analytics.export': False,
}

# Permissões de revisor (revisa e aprova documentos)
_REVIEWER_ACCESS = {
    'dashboard.view': True,
    'assistant.use': False,
    'assistant.configure': False,
    'document_generators.use': False,
    'document_generators.configure': False,
    'form_assistants.use': False,
    'form_assistants.configure': False,
    'documents.create': False,
    'documents.view_own': True,
    'documents.view_all': True,
    'documents.edit_own': True,
    'documents.edit_all': True,
    'documents.delete_own': False,
    'documents.delete_all': False,
    'documents.approve': True,
    'documents.export': True,
    'templates.view': False,
    'templates.create': False,
    'templates.edit': False,
    'templates.delete': False,
    'forms.view': False,
    'forms.create': False,
    'forms.edit': False,
    'forms.delete': False,
    'knowledge_base.view': False,
    'knowledge_base.create': False,
    'knowledge_base.edit': False,
    'knowledge_base.delete': False,
    'agents.view': False,
    'agents.create': False,
    'agents.edit': False,
    'agents.delete': False,
    'users.view': False,
    'users.create': False,
    'users.edit': False,
    'users.delete': False,
    'settings.view': False,
    'settings.edit': False,
    'analytics.view': False,
    'analytics.export': False,
}

# Permissões mínimas (visualizador/cliente)
_VIEWER_ACCESS = {
    'dashboard.view': True,
    'assistant.use': False,
    'assistant.configure': False,
    'document_generators.use': False,
    'document_generators.configure': False,
    'form_assistants.use': False,
    'form_assistants.configure': False,
    'documents.create': False,
    'documents.view_own': True,
    'documents.view_all': False,
    'documents.edit_own': False,
    'documents.edit_all': False,
    'documents.delete_own': False,
    'documents.delete_all': False,
    'documents.approve': False,
    'documents.export': True,
    'templates.view': False,
    'templates.create': False,
    'templates.edit': False,
    'templates.delete': False,
    'forms.view': False,
    'forms.create': False,
    'forms.edit': False,
    'forms.delete': False,
    'knowledge_base.view': False,
    'knowledge_base.create': False,
    'knowledge_base.edit': False,
    'knowledge_base.delete': False,
    'agents.view': False,
    'agents.create': False,
    'agents.edit': False,
    'agents.delete': False,
    'users.view': False,
    'users.create': False,
    'users.edit': False,
    'users.delete': False,
    'settings.view': False,
    'settings.edit': False,
    'analytics.view': False,
    'analytics.export': False,
}

# Permissões de assistente (cria documentos, sem deletar)
_ASSISTANT_ACCESS = {
    **_VIEWER_ACCESS,
    'assistant.use': True,
    'documents.create': True,
    'documents.edit_own': True,
    'documents.view_own': True,
    'documents.export': True,
    'templates.view': True,
    'forms.view': True,
    'knowledge_base.view': True,
}

ROLE_PERMISSIONS = {
    # Administração
    'superadmin': _FULL_ACCESS,
    'admin': _FULL_ACCESS,

    # Advocacia Privada
    'socio': {
        **_FULL_ACCESS,
        # Sócio tem acesso total mas é distinto de admin para auditoria
    },
    'advogado_senior': {
        **_OPERATOR_ACCESS,
        'documents.view_all': True,
        'documents.approve': True,
        'analytics.view': True,
        'agents.view': True,
    },
    'advogado_pleno': _OPERATOR_ACCESS,
    'advogado_junior': {
        **_OPERATOR_ACCESS,
        'documents.delete_own': False,
    },
    'estagiario': {
        **_ASSISTANT_ACCESS,
        'form_assistants.use': True,
        'document_generators.use': True,
    },

    # Gestão do Escritório
    'gestor': _MANAGEMENT_ACCESS,
    'coordenador': {
        **_MANAGEMENT_ACCESS,
        'users.create': False,
        'users.delete': False,
        'settings.edit': False,
    },
    'supervisor': {
        **_MANAGEMENT_ACCESS,
        'users.create': False,
        'users.edit': False,
        'users.delete': False,
        'settings.edit': False,
        'agents.create': False,
        'agents.edit': False,
        'agents.delete': False,
    },

    # Operacional
    'analista': _OPERATOR_ACCESS,
    'assistente': _ASSISTANT_ACCESS,
    'paralegal': {
        **_ASSISTANT_ACCESS,
        'form_assistants.use': True,
        'document_generators.use': True,
        'knowledge_base.create': True,
    },
    'secretaria': {
        **_VIEWER_ACCESS,
        'documents.create': True,
        'documents.edit_own': True,
        'documents.export': True,
    },

    # Setor Público
    'procurador': {
        **_FULL_ACCESS,
        # Procurador tem acesso total no contexto público
    },
    'defensor': {
        **_OPERATOR_ACCESS,
        'documents.view_all': True,
        'documents.approve': True,
        'analytics.view': True,
    },
    'promotor': {
        **_OPERATOR_ACCESS,
        'documents.view_all': True,
        'documents.approve': True,
        'analytics.view': True,
    },
    'assessor': _OPERATOR_ACCESS,
    'servidor': {
        **_VIEWER_ACCESS,
        'documents.create': True,
        'documents.edit_own': True,
    },

    # Revisão e Controle
    'revisor': _REVIEWER_ACCESS,
    'auditor': {
        **_REVIEWER_ACCESS,
        'analytics.view': True,
        'analytics.export': True,
        'documents.view_all': True,
    },

    # Acesso Limitado
    'cliente': {
        **_VIEWER_ACCESS,
        'documents.export': False,
    },
    'visualizador': _VIEWER_ACCESS,

    # Aliases (backwards compatibility) - mapeiam para o mesmo conjunto de permissões
    'manager': _MANAGEMENT_ACCESS,
    'reviewer': _REVIEWER_ACCESS,
    'analyst': _OPERATOR_ACCESS,
    'viewer': _VIEWER_ACCESS,
}

ROLE_DESCRIPTIONS = {
    # Administração
    'superadmin': {
        'name': 'Super Administrador',
        'description': 'Acesso total ao sistema.',
        'color': '#dc2626',
    },
    'admin': {
        'name': 'Administrador',
        'description': 'Acesso administrativo completo.',
        'color': '#b91c1c',
    },

    # Advocacia Privada
    'socio': {
        'name': 'Sócio / Partner',
        'description': 'Sócio do escritório com acesso total.',
        'color': '#7c3aed',
    },
    'advogado_senior': {
        'name': 'Advogado Sênior',
        'description': 'Advogado sênior. Cria documentos, aprova peças e visualiza analytics.',
        'color': '#2563eb',
    },
    'advogado_pleno': {
        'name': 'Advogado Pleno',
        'description': 'Advogado pleno. Cria e edita documentos, usa assistentes IA.',
        'color': '#3b82f6',
    },
    'advogado_junior': {
        'name': 'Advogado Júnior',
        'description': 'Advogado júnior. Cria documentos, sem permissão de exclusão.',
        'color': '#60a5fa',
    },
    'estagiario': {
        'name': 'Estagiário de Direito',
        'description': 'Estagiário. Usa assistentes IA e cria documentos básicos.',
        'color': '#93c5fd',
    },

    # Gestão do Escritório
    'gestor': {
        'name': 'Gestor / Manager',
        'description': 'Gestão de usuários, configurações, agentes e analytics.',
        'color': '#0891b2',
    },
    'coordenador': {
        'name': 'Coordenador Jurídico',
        'description': 'Coordena equipes jurídicas. Gerencia agentes e visualiza analytics.',
        'color': '#0e7490',
    },
    'supervisor': {
        'name': 'Supervisor',
        'description': 'Supervisiona operações. Visualiza documentos e analytics.',
        'color': '#155e75',
    },

    # Operacional
    'analista': {
        'name': 'Analista Jurídico',
        'description': 'Usa assistentes IA, cria/edita documentos e cadastra bases de conhecimento.',
        'color': '#16a34a',
    },
    'assistente': {
        'name': 'Assistente Jurídico',
        'description': 'Cria documentos e usa assistentes IA com acesso limitado.',
        'color': '#22c55e',
    },
    'paralegal': {
        'name': 'Paralegal / Técnico Jurídico',
        'description': 'Suporte jurídico. Cria documentos e gerencia bases de conhecimento.',
        'color': '#4ade80',
    },
    'secretaria': {
        'name': 'Secretária Jurídica',
        'description': 'Apoio administrativo. Cria e exporta documentos.',
        'color': '#86efac',
    },

    # Setor Público
    'procurador': {
        'name': 'Procurador',
        'description': 'Procurador público com acesso total ao sistema.',
        'color': '#9333ea',
    },
    'defensor': {
        'name': 'Defensor Público',
        'description': 'Defensor público. Cria documentos, aprova peças e visualiza analytics.',
        'color': '#a855f7',
    },
    'promotor': {
        'name': 'Promotor de Justiça',
        'description': 'Promotor de justiça. Cria documentos, aprova peças e visualiza analytics.',
        'color': '#c084fc',
    },
    'assessor': {
        'name': 'Assessor Jurídico',
        'description': 'Assessor jurídico. Cria e edita documentos, usa assistentes IA.',
        'color': '#d8b4fe',
    },
    'servidor': {
        'name': 'Servidor Público',
        'description': 'Servidor público. Cria e edita documentos próprios.',
        'color': '#e9d5ff',
    },

    # Revisão e Controle
    'revisor': {
        'name': 'Revisor',
        'description': 'Revisa e edita documentos de outros usuários, aprova ou rejeita.',
        'color': '#ea580c',
    },
    'auditor': {
        'name': 'Auditor Jurídico',
        'description': 'Audita documentos e processos. Visualiza analytics e relatórios.',
        'color': '#f97316',
    },

    # Acesso Limitado
    'cliente': {
        'name': 'Cliente',
        'description': 'Visualiza documentos próprios. Sem permissão de exportação.',
        'color': '#a3a3a3',
    },
    'visualizador': {
        'name': 'Visualizador',
        'description': 'Visualiza dashboard e documentos próprios. Perfil mínimo.',
        'color': '#6b7280',
    },

    # Aliases (backwards compatibility)
    'manager': {
        'name': 'Gestor',
        'description': 'Gestão de usuários, configurações, agentes e analytics.',
        'color': '#0891b2',
    },
    'reviewer': {
        'name': 'Revisor',
        'description': 'Revisa e edita documentos de outros usuários, aprova ou rejeita.',
        'color': '#ea580c',
    },
    'analyst': {
        'name': 'Analista',
        'description': 'Usa assistentes IA, cria/edita documentos e cadastra bases de conhecimento.',
        'color': '#16a34a',
    },
    'viewer': {
        'name': 'Visualizador',
        'description': 'Visualiza dashboard e documentos próprios. Perfil mínimo.',
        'color': '#6b7280',
    },
}

PERMISSION_LABELS = {
    'dashboard.view': 'Visualizar Dashboard',
    'assistant.use': 'Usar Assistente Inteligente',
    'assistant.configure': 'Configurar Assistente',
    'document_generators.use': 'Usar Geradores de Documento',
    'document_generators.configure': 'Configurar Geradores',
    'form_assistants.use': 'Usar Assistentes de Formulário',
    'form_assistants.configure': 'Configurar Assistentes',
    'documents.create': 'Criar Documentos',
    'documents.view_own': 'Ver Documentos Próprios',
    'documents.view_all': 'Ver Todos os Documentos',
    'documents.edit_own': 'Editar Documentos Próprios',
    'documents.edit_all': 'Editar Todos os Documentos',
    'documents.delete_own': 'Excluir Documentos Próprios',
    'documents.delete_all': 'Excluir Todos os Documentos',
    'documents.approve': 'Aprovar Documentos',
    'documents.export': 'Exportar Documentos',
    'templates.view': 'Visualizar Templates',
    'templates.create': 'Criar Templates',
    'templates.edit': 'Editar Templates',
    'templates.delete': 'Excluir Templates',
    'forms.view': 'Visualizar Formulários',
    'forms.create': 'Criar Formulários',
    'forms.edit': 'Editar Formulários',
    'forms.delete': 'Excluir Formulários',
    'knowledge_base.view': 'Visualizar Base de Conhecimento',
    'knowledge_base.create': 'Adicionar à Base de Conhecimento',
    'knowledge_base.edit': 'Editar Base de Conhecimento',
    'knowledge_base.delete': 'Excluir da Base de Conhecimento',
    'agents.view': 'Visualizar Agentes',
    'agents.create': 'Criar Agentes',
    'agents.edit': 'Editar Agentes',
    'agents.delete': 'Excluir Agentes',
    'users.view': 'Visualizar Usuários',
    'users.create': 'Criar Usuários',
    'users.edit': 'Editar Usuários',
    'users.delete': 'Excluir Usuários',
    'settings.view': 'Visualizar Configurações',
    'settings.edit': 'Editar Configurações',
    'analytics.view': 'Visualizar Analytics',
    'analytics.export': 'Exportar Analytics',
}


def resolve_role(role):
    """Resolve alias de role antigo para o novo equivalente."""
    return ROLE_ALIASES.get(role, role)


def is_admin_or_manager(user):
    """Verifica se o usuário é admin ou gestor (inclui roles equivalentes)."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    resolved = resolve_role(user.role)
    return resolved in ['superadmin', 'admin', 'gestor', 'socio', 'procurador', 'coordenador']


def get_user_permissions(user):
    """Retorna permissões do usuário baseado na role."""
    if not user or not user.is_authenticated:
        return {}
    role = getattr(user, 'role', 'visualizador')
    # Resolve aliases de backwards compatibility
    resolved = ROLE_ALIASES.get(role, role)
    return ROLE_PERMISSIONS.get(resolved, ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS['visualizador']))


def has_permission(user, permission):
    """Verifica se usuário tem uma permissão específica."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    perms = get_user_permissions(user)
    return perms.get(permission, False)


def get_all_roles():
    """Retorna todas as roles com suas informações."""
    roles = []
    for role_key, role_info in ROLE_DESCRIPTIONS.items():
        roles.append({
            'key': role_key,
            'name': role_info['name'],
            'description': role_info['description'],
            'color': role_info['color'],
            'permissions': ROLE_PERMISSIONS.get(role_key, {}),
        })
    return roles


def get_permissions_matrix():
    """Retorna matriz de permissões para UI."""
    return {
        'roles': list(ROLE_DESCRIPTIONS.keys()),
        'role_info': ROLE_DESCRIPTIONS,
        'permission_labels': PERMISSION_LABELS,
        'permissions': ROLE_PERMISSIONS,
    }


# =============================================================================
# CLASSES DE PERMISSÃO DRF
# =============================================================================

class CanUseAssistant(permissions.BasePermission):
    message = 'Você não tem permissão para usar o Assistente Inteligente.'

    def has_permission(self, request, view):
        return has_permission(request.user, 'assistant.use')


class CanUseFormAssistants(permissions.BasePermission):
    message = 'Você não tem permissão para usar os Assistentes de Formulário.'

    def has_permission(self, request, view):
        return has_permission(request.user, 'form_assistants.use')


class CanCreateDocuments(permissions.BasePermission):
    message = 'Você não tem permissão para criar documentos.'

    def has_permission(self, request, view):
        return has_permission(request.user, 'documents.create')


class CanViewAllDocuments(permissions.BasePermission):
    message = 'Você não tem permissão para ver todos os documentos.'

    def has_permission(self, request, view):
        return has_permission(request.user, 'documents.view_all')


class CanApproveDocuments(permissions.BasePermission):
    message = 'Você não tem permissão para aprovar documentos.'

    def has_permission(self, request, view):
        return has_permission(request.user, 'documents.approve')


class CanManageTemplates(permissions.BasePermission):
    message = 'Você não tem permissão para gerenciar templates.'

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return has_permission(request.user, 'templates.view')
        return has_permission(request.user, 'templates.create')


class CanManageForms(permissions.BasePermission):
    message = 'Você não tem permissão para gerenciar formulários.'

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return has_permission(request.user, 'forms.view')
        return has_permission(request.user, 'forms.create')


class CanManageKnowledgeBase(permissions.BasePermission):
    message = 'Você não tem permissão para gerenciar a base de conhecimento.'

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return has_permission(request.user, 'knowledge_base.view')
        return has_permission(request.user, 'knowledge_base.create')


class CanManageAgents(permissions.BasePermission):
    message = 'Você não tem permissão para gerenciar agentes.'

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return has_permission(request.user, 'agents.view')
        return has_permission(request.user, 'agents.create')


class CanManageUsers(permissions.BasePermission):
    message = 'Você não tem permissão para gerenciar usuários.'

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return has_permission(request.user, 'users.view')
        return has_permission(request.user, 'users.create')


class CanManageSettings(permissions.BasePermission):
    message = 'Você não tem permissão para gerenciar configurações.'

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return has_permission(request.user, 'settings.view')
        return has_permission(request.user, 'settings.edit')


class CanViewAnalytics(permissions.BasePermission):
    message = 'Você não tem permissão para ver analytics.'

    def has_permission(self, request, view):
        return has_permission(request.user, 'analytics.view')


class IsOwnerOrHasViewAll(permissions.BasePermission):
    """Acesso se for dono OU tiver view_all."""

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        owner_field = getattr(view, 'owner_field', 'user')
        obj_owner = getattr(obj, owner_field, None)
        if obj_owner == request.user:
            return True
        return has_permission(request.user, 'documents.view_all')
