'use client';

import { ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { usePermissions, Permission } from '@/hooks/use-permissions';
import { Loader2, ShieldX } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface PermissionGuardProps {
  children: ReactNode;
  /** Permissão única necessária */
  permission?: Permission;
  /** Lista de permissões - usuário precisa ter TODAS */
  permissions?: Permission[];
  /** Lista de permissões - usuário precisa ter ALGUMA */
  anyPermission?: Permission[];
  /** Componente a ser renderizado enquanto verifica permissões */
  fallback?: ReactNode;
  /** Componente a ser renderizado se não tiver permissão */
  accessDenied?: ReactNode;
  /** Se true, redireciona para /dashboard ao invés de mostrar mensagem */
  redirectOnDeny?: boolean;
  /** URL para redirecionar se não tiver permissão */
  redirectTo?: string;
}

/**
 * Componente que protege rotas/componentes baseado em permissões.
 *
 * Exemplos de uso:
 *
 * ```tsx
 * // Permissão única
 * <PermissionGuard permission="users.view">
 *   <UsersList />
 * </PermissionGuard>
 *
 * // Qualquer uma das permissões
 * <PermissionGuard anyPermission={['assistant.use', 'document_generators.use']}>
 *   <DocumentCreator />
 * </PermissionGuard>
 *
 * // Todas as permissões
 * <PermissionGuard permissions={['templates.view', 'templates.create']}>
 *   <TemplateEditor />
 * </PermissionGuard>
 *
 * // Com redirect
 * <PermissionGuard permission="settings.view" redirectOnDeny redirectTo="/dashboard">
 *   <SettingsPage />
 * </PermissionGuard>
 * ```
 */
export function PermissionGuard({
  children,
  permission,
  permissions,
  anyPermission,
  fallback,
  accessDenied,
  redirectOnDeny = false,
  redirectTo = '/dashboard',
}: PermissionGuardProps) {
  const router = useRouter();
  const {
    hasPermission,
    hasAllPermissions,
    hasAnyPermission,
    isLoadingPermissions,
    currentRoleName,
  } = usePermissions();

  // Enquanto carrega
  if (isLoadingPermissions) {
    return (
      fallback || (
        <div className="flex items-center justify-center min-h-[200px]">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )
    );
  }

  // Verifica permissões
  let hasAccess = true;

  if (permission) {
    hasAccess = hasPermission(permission);
  } else if (permissions && permissions.length > 0) {
    hasAccess = hasAllPermissions(permissions);
  } else if (anyPermission && anyPermission.length > 0) {
    hasAccess = hasAnyPermission(anyPermission);
  }

  // Se tem acesso, renderiza children
  if (hasAccess) {
    return <>{children}</>;
  }

  // Se não tem acesso e deve redirecionar
  if (redirectOnDeny) {
    router.push(redirectTo);
    return (
      <div className="flex items-center justify-center min-h-[200px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // Se não tem acesso, mostra mensagem de acesso negado
  return (
    accessDenied || (
      <AccessDeniedCard
        roleName={currentRoleName}
        onGoBack={() => router.back()}
        onGoHome={() => router.push('/dashboard')}
      />
    )
  );
}

interface AccessDeniedCardProps {
  roleName: string;
  onGoBack: () => void;
  onGoHome: () => void;
}

function AccessDeniedCard({ roleName, onGoBack, onGoHome }: AccessDeniedCardProps) {
  return (
    <div className="flex items-center justify-center min-h-[400px] p-6">
      <Card className="max-w-md w-full">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
            <ShieldX className="h-8 w-8 text-red-600" />
          </div>
          <CardTitle className="text-xl">Acesso Negado</CardTitle>
          <CardDescription>
            Você não tem permissão para acessar este recurso.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-lg bg-muted p-3 text-center text-sm">
            <p className="text-muted-foreground">Seu perfil atual:</p>
            <p className="font-medium">{roleName}</p>
          </div>
          <p className="text-sm text-muted-foreground text-center">
            Se você acredita que deveria ter acesso, entre em contato com o administrador do sistema.
          </p>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onGoBack} className="flex-1">
              Voltar
            </Button>
            <Button onClick={onGoHome} className="flex-1">
              Ir para Dashboard
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Componente para esconder elementos sem permissão (sem mensagem de erro)
 */
export function PermissionHide({
  children,
  permission,
  permissions,
  anyPermission,
}: Omit<PermissionGuardProps, 'fallback' | 'accessDenied' | 'redirectOnDeny' | 'redirectTo'>) {
  const { hasPermission, hasAllPermissions, hasAnyPermission, isLoadingPermissions } = usePermissions();

  if (isLoadingPermissions) return null;

  let hasAccess = true;

  if (permission) {
    hasAccess = hasPermission(permission);
  } else if (permissions && permissions.length > 0) {
    hasAccess = hasAllPermissions(permissions);
  } else if (anyPermission && anyPermission.length > 0) {
    hasAccess = hasAnyPermission(anyPermission);
  }

  if (!hasAccess) return null;

  return <>{children}</>;
}
