'use client';

import { Fragment } from 'react';
import { usePermissions, Permission } from '@/hooks/use-permissions';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Check, X, Shield, Loader2, Info } from 'lucide-react';
import { PermissionGuard } from '@/components/auth/permission-guard';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

// Labels para exibição das permissões
const permissionLabels: Record<string, string> = {
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
};

// Categorias de permissões para organização
const permissionCategories = [
  {
    name: 'Dashboard',
    permissions: ['dashboard.view'],
  },
  {
    name: 'Assistente Inteligente',
    permissions: ['assistant.use', 'assistant.configure'],
  },
  {
    name: 'Geradores de Documento',
    permissions: ['document_generators.use', 'document_generators.configure'],
  },
  {
    name: 'Assistentes de Formulário',
    permissions: ['form_assistants.use', 'form_assistants.configure'],
  },
  {
    name: 'Documentos',
    permissions: [
      'documents.create',
      'documents.view_own',
      'documents.view_all',
      'documents.edit_own',
      'documents.edit_all',
      'documents.delete_own',
      'documents.delete_all',
      'documents.approve',
      'documents.export',
    ],
  },
  {
    name: 'Templates',
    permissions: ['templates.view', 'templates.create', 'templates.edit', 'templates.delete'],
  },
  {
    name: 'Formulários',
    permissions: ['forms.view', 'forms.create', 'forms.edit', 'forms.delete'],
  },
  {
    name: 'Base de Conhecimento',
    permissions: ['knowledge_base.view', 'knowledge_base.create', 'knowledge_base.edit', 'knowledge_base.delete'],
  },
  {
    name: 'Agentes IA',
    permissions: ['agents.view', 'agents.create', 'agents.edit', 'agents.delete'],
  },
  {
    name: 'Usuários',
    permissions: ['users.view', 'users.create', 'users.edit', 'users.delete'],
  },
  {
    name: 'Configurações',
    permissions: ['settings.view', 'settings.edit'],
  },
  {
    name: 'Analytics',
    permissions: ['analytics.view', 'analytics.export'],
  },
];

export default function RolesPage() {
  const { roles, permissionsMatrix, isLoadingRoles, isLoadingMatrix, currentRole, currentRoleName, currentRoleColor } = usePermissions();

  if (isLoadingRoles || isLoadingMatrix) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <PermissionGuard permission="users.view">
      <div className="space-y-6">
        <div className="flex items-center justify-between" data-tour="st-roles">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Shield className="h-8 w-8" />
              Perfis e Permissões
            </h1>
            <p className="text-muted-foreground">
              Visualize os perfis do sistema e suas permissões
            </p>
          </div>
          <div className="flex items-center gap-2 bg-muted px-4 py-2 rounded-lg">
            <span className="text-sm text-muted-foreground">Seu perfil:</span>
            <Badge style={{ backgroundColor: currentRoleColor, color: 'white' }}>
              {currentRoleName}
            </Badge>
          </div>
        </div>

        {/* Cards dos Perfis */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {roles?.map((role) => (
            <Card
              key={role.key}
              className={currentRole === role.key ? 'ring-2 ring-primary' : ''}
            >
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <Badge
                    style={{ backgroundColor: role.color, color: 'white' }}
                    className="text-xs"
                  >
                    {role.name}
                  </Badge>
                  {currentRole === role.key && (
                    <Badge variant="outline" className="text-xs">
                      Você
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{role.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Matriz de Permissões */}
        <Card>
          <CardHeader>
            <CardTitle>Matriz de Permissões</CardTitle>
            <CardDescription>
              Visão geral das permissões por perfil
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="matrix" className="space-y-4">
              <TabsList>
                <TabsTrigger value="matrix">Matriz Completa</TabsTrigger>
                <TabsTrigger value="categories">Por Categoria</TabsTrigger>
              </TabsList>

              <TabsContent value="matrix" className="space-y-4">
                <div className="rounded-md border overflow-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-[300px] sticky left-0 bg-background">
                          Permissão
                        </TableHead>
                        {roles?.map((role) => (
                          <TableHead key={role.key} className="text-center min-w-[100px]">
                            <div className="flex flex-col items-center gap-1">
                              <Badge
                                style={{ backgroundColor: role.color, color: 'white' }}
                                className="text-xs"
                              >
                                {role.name}
                              </Badge>
                            </div>
                          </TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {permissionCategories.map((category) => (
                        <Fragment key={category.name}>
                          <TableRow className="bg-muted/50">
                            <TableCell
                              colSpan={(roles?.length || 0) + 1}
                              className="font-semibold sticky left-0 bg-muted/50"
                            >
                              {category.name}
                            </TableCell>
                          </TableRow>
                          {category.permissions.map((permission) => (
                            <TableRow key={permission}>
                              <TableCell className="sticky left-0 bg-background">
                                <TooltipProvider>
                                  <Tooltip>
                                    <TooltipTrigger className="flex items-center gap-2 text-left">
                                      <span className="text-sm">
                                        {permissionLabels[permission] || permission}
                                      </span>
                                      <Info className="h-3 w-3 text-muted-foreground" />
                                    </TooltipTrigger>
                                    <TooltipContent>
                                      <p className="text-xs font-mono">{permission}</p>
                                    </TooltipContent>
                                  </Tooltip>
                                </TooltipProvider>
                              </TableCell>
                              {roles?.map((role) => (
                                <TableCell key={`${role.key}-${permission}`} className="text-center">
                                  {role.permissions[permission as Permission] ? (
                                    <Check className="h-5 w-5 text-green-600 mx-auto" />
                                  ) : (
                                    <X className="h-5 w-5 text-red-400 mx-auto" />
                                  )}
                                </TableCell>
                              ))}
                            </TableRow>
                          ))}
                        </Fragment>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </TabsContent>

              <TabsContent value="categories" className="space-y-4">
                <div className="grid gap-4">
                  {permissionCategories.map((category) => (
                    <Card key={category.name}>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-lg">{category.name}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="rounded-md border">
                          <Table>
                            <TableHeader>
                              <TableRow>
                                <TableHead className="w-[250px]">Permissão</TableHead>
                                {roles?.map((role) => (
                                  <TableHead key={role.key} className="text-center">
                                    <Badge
                                      style={{ backgroundColor: role.color, color: 'white' }}
                                      className="text-xs"
                                    >
                                      {role.name.split(' ')[0]}
                                    </Badge>
                                  </TableHead>
                                ))}
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {category.permissions.map((permission) => (
                                <TableRow key={permission}>
                                  <TableCell className="text-sm">
                                    {permissionLabels[permission] || permission}
                                  </TableCell>
                                  {roles?.map((role) => (
                                    <TableCell key={`${role.key}-${permission}`} className="text-center">
                                      {role.permissions[permission as Permission] ? (
                                        <Check className="h-4 w-4 text-green-600 mx-auto" />
                                      ) : (
                                        <X className="h-4 w-4 text-red-400 mx-auto" />
                                      )}
                                    </TableCell>
                                  ))}
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Informações Adicionais */}
        <Card>
          <CardHeader>
            <CardTitle>Sobre os Perfis</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <h4 className="font-semibold flex items-center gap-2">
                  <Badge style={{ backgroundColor: '#dc2626', color: 'white' }}>Super Administrador</Badge>
                </h4>
                <p className="text-sm text-muted-foreground">
                  Acesso total ao sistema. Pode gerenciar todos os aspectos da aplicação, incluindo configurações avançadas.
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-semibold flex items-center gap-2">
                  <Badge style={{ backgroundColor: '#2563eb', color: 'white' }}>Gestor</Badge>
                </h4>
                <p className="text-sm text-muted-foreground">
                  Gestão de usuários, configurações, templates, formulários e agentes. Visualiza documentos e KBs.
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-semibold flex items-center gap-2">
                  <Badge style={{ backgroundColor: '#16a34a', color: 'white' }}>Analista</Badge>
                </h4>
                <p className="text-sm text-muted-foreground">
                  Usa assistentes IA, cria/edita documentos e cadastra bases de conhecimento.
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-semibold flex items-center gap-2">
                  <Badge style={{ backgroundColor: '#ea580c', color: 'white' }}>Revisor</Badge>
                </h4>
                <p className="text-sm text-muted-foreground">
                  Revisa e edita documentos de outros usuários, aprova ou rejeita.
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-semibold flex items-center gap-2">
                  <Badge style={{ backgroundColor: '#6b7280', color: 'white' }}>Visualizador</Badge>
                </h4>
                <p className="text-sm text-muted-foreground">
                  Visualiza dashboard e documentos próprios. Perfil mínimo.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </PermissionGuard>
  );
}
