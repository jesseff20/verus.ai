'use client';

import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { useAuth } from './use-auth';

// Tipos das permissões
export type Permission =
  | 'dashboard.view'
  | 'assistant.use'
  | 'assistant.configure'
  | 'document_generators.use'
  | 'document_generators.configure'
  | 'form_assistants.use'
  | 'form_assistants.configure'
  | 'documents.create'
  | 'documents.view_own'
  | 'documents.view_all'
  | 'documents.edit_own'
  | 'documents.edit_all'
  | 'documents.delete_own'
  | 'documents.delete_all'
  | 'documents.approve'
  | 'documents.export'
  | 'templates.view'
  | 'templates.create'
  | 'templates.edit'
  | 'templates.delete'
  | 'forms.view'
  | 'forms.create'
  | 'forms.edit'
  | 'forms.delete'
  | 'knowledge_base.view'
  | 'knowledge_base.create'
  | 'knowledge_base.edit'
  | 'knowledge_base.delete'
  | 'agents.view'
  | 'agents.create'
  | 'agents.edit'
  | 'agents.delete'
  | 'users.view'
  | 'users.create'
  | 'users.edit'
  | 'users.delete'
  | 'settings.view'
  | 'settings.edit'
  | 'analytics.view'
  | 'analytics.export';

export interface UserPermissions {
  role: string;
  role_name: string;
  role_description: string;
  role_color: string;
  permissions: Record<Permission, boolean>;
}

export interface Role {
  key: string;
  name: string;
  description: string;
  color: string;
  permissions: Record<Permission, boolean>;
}

export interface PermissionsMatrix {
  roles: string[];
  role_info: Record<string, { name: string; description: string; color: string }>;
  permission_labels: Record<Permission, string>;
  permissions: Record<string, Record<Permission, boolean>>;
}

export function usePermissions() {
  const { user, isAuthenticated } = useAuth();

  // Buscar permissões do usuário logado
  const {
    data: userPermissions,
    isLoading: isLoadingPermissions,
    refetch: refetchPermissions,
  } = useQuery<UserPermissions>({
    queryKey: ['user-permissions'],
    queryFn: async () => {
      const response = await api.get('/api/v1/auth/users/my_permissions/');
      return response.data;
    },
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000, // 5 minutos
    gcTime: 30 * 60 * 1000,
  });

  // Buscar lista de roles disponíveis
  const {
    data: roles,
    isLoading: isLoadingRoles,
  } = useQuery<Role[]>({
    queryKey: ['roles'],
    queryFn: async () => {
      const response = await api.get('/api/v1/auth/users/roles/');
      return response.data;
    },
    enabled: isAuthenticated,
    staleTime: 30 * 60 * 1000, // 30 minutos - roles não mudam frequentemente
  });

  // Buscar matriz de permissões (admin only)
  const {
    data: permissionsMatrix,
    isLoading: isLoadingMatrix,
  } = useQuery<PermissionsMatrix>({
    queryKey: ['permissions-matrix'],
    queryFn: async () => {
      const response = await api.get('/api/v1/auth/users/permissions_matrix/');
      return response.data;
    },
    enabled: isAuthenticated && ['superadmin', 'admin', 'gestor', 'manager', 'socio', 'procurador', 'coordenador'].includes(user?.role || ''),
    staleTime: 30 * 60 * 1000,
  });

  /**
   * Verifica se o usuário tem uma permissão específica
   */
  const hasPermission = (permission: Permission): boolean => {
    if (!userPermissions) return false;
    return userPermissions.permissions[permission] === true;
  };

  /**
   * Verifica se o usuário tem TODAS as permissões especificadas
   */
  const hasAllPermissions = (permissions: Permission[]): boolean => {
    return permissions.every((p) => hasPermission(p));
  };

  /**
   * Verifica se o usuário tem ALGUMA das permissões especificadas
   */
  const hasAnyPermission = (permissions: Permission[]): boolean => {
    return permissions.some((p) => hasPermission(p));
  };

  /**
   * Verifica se pode usar recursos de geração de documentos
   * (Assistente Inteligente OU Document Generators)
   */
  const canGenerateDocuments = (): boolean => {
    return hasAnyPermission(['assistant.use', 'document_generators.use']);
  };

  /**
   * Verifica se pode gerenciar configurações (admin)
   */
  const canManageSettings = (): boolean => {
    return hasAnyPermission(['settings.view', 'settings.edit']);
  };

  /**
   * Verifica se pode gerenciar usuários
   */
  const canManageUsers = (): boolean => {
    return hasAnyPermission(['users.view', 'users.create', 'users.edit']);
  };

  /**
   * Verifica se pode gerenciar agentes IA
   */
  const canConfigureAgents = (): boolean => {
    return hasAnyPermission(['agents.create', 'agents.edit', 'agents.delete']);
  };

  /**
   * Retorna a role atual do usuário
   */
  const currentRole = userPermissions?.role || user?.role || 'viewer';
  const currentRoleName = userPermissions?.role_name || 'Visualizador';
  const currentRoleColor = userPermissions?.role_color || '#6b7280';

  return {
    // Dados
    userPermissions,
    roles,
    permissionsMatrix,
    currentRole,
    currentRoleName,
    currentRoleColor,

    // Loading states
    isLoading: isLoadingPermissions || isLoadingRoles,
    isLoadingPermissions,
    isLoadingRoles,
    isLoadingMatrix,

    // Funções de verificação
    hasPermission,
    hasAllPermissions,
    hasAnyPermission,
    canGenerateDocuments,
    canManageSettings,
    canManageUsers,
    canConfigureAgents,

    // Refetch
    refetchPermissions,
  };
}

/**
 * Hook simplificado para verificar uma única permissão
 */
export function useHasPermission(permission: Permission): boolean {
  const { hasPermission, isLoadingPermissions } = usePermissions();

  if (isLoadingPermissions) return false;
  return hasPermission(permission);
}

/**
 * Hook para verificar múltiplas permissões (ANY)
 */
export function useHasAnyPermission(permissions: Permission[]): boolean {
  const { hasAnyPermission, isLoadingPermissions } = usePermissions();

  if (isLoadingPermissions) return false;
  return hasAnyPermission(permissions);
}

/**
 * Hook para verificar múltiplas permissões (ALL)
 */
export function useHasAllPermissions(permissions: Permission[]): boolean {
  const { hasAllPermissions, isLoadingPermissions } = usePermissions();

  if (isLoadingPermissions) return false;
  return hasAllPermissions(permissions);
}
