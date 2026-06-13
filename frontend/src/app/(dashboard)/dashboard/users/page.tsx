'use client';

import { useState } from 'react';
import { useUsers, type CreateUserData, type UpdateUserData } from '@/hooks/use-users';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { AIInput } from '@/components/ui/ai-input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Users, Plus, Loader2, UserCheck, UserX, Edit, Trash2 } from 'lucide-react';
import type { User } from '@/types';

const roleLabels: Record<string, string> = {
  // Administração
  superadmin: 'Super Administrador',
  admin: 'Administrador',
  // Advocacia Privada
  socio: 'Sócio / Partner',
  advogado_senior: 'Procurador Sênior',
  advogado_pleno: 'Procurador Pleno',
  advogado_junior: 'Procurador Júnior',
  estagiario: 'Estagiário de Direito',
  // Gestão
  gestor: 'Gestor / Manager',
  coordenador: 'Coordenador Jurídico',
  supervisor: 'Supervisor',
  // Operacional
  analista: 'Analista Jurídico',
  assistente: 'Assistente de Procuradoria',
  paralegal: 'Paralegal / Técnico Jurídico',
  secretaria: 'Secretária Jurídica',
  // Setor Público
  procurador: 'Procurador',
  defensor: 'Defensor Público',
  promotor: 'Promotor de Justiça',
  assessor: 'Assessor Jurídico',
  servidor: 'Servidor Público',
  // Revisão e Controle
  revisor: 'Revisor',
  auditor: 'Auditor Jurídico',
  // Acesso Limitado
  cliente: 'Parte',
  visualizador: 'Visualizador',
  // Legacy aliases
  manager: 'Gestor',
  analyst: 'Analista',
  reviewer: 'Revisor',
  viewer: 'Visualizador',
};

const roleColors: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  superadmin: 'destructive',
  admin: 'destructive',
  socio: 'destructive',
  procurador: 'destructive',
  defensor: 'default',
  promotor: 'default',
  gestor: 'default',
  coordenador: 'default',
  advogado_senior: 'secondary',
  supervisor: 'secondary',
  advogado_pleno: 'secondary',
  auditor: 'secondary',
  revisor: 'secondary',
  advogado_junior: 'secondary',
  analista: 'secondary',
  assessor: 'secondary',
  assistente: 'outline',
  paralegal: 'outline',
  estagiario: 'outline',
  secretaria: 'outline',
  servidor: 'outline',
  cliente: 'outline',
  visualizador: 'outline',
  // Legacy aliases
  manager: 'default',
  analyst: 'secondary',
  reviewer: 'secondary',
  viewer: 'outline',
};

export default function UsersPage() {
  const { users, count, isLoading, createUser, isCreating, updateUser, isUpdating, deleteUser, isDeleting } = useUsers();
  const { toast } = useToast();

  // Dialogs state
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  // Forms data
  const [createFormData, setCreateFormData] = useState<CreateUserData>({
    username: '',
    email: '',
    password: '',
    password_confirm: '',
    first_name: '',
    last_name: '',
    role: 'analista',
    phone: '',
    department: '',
    position: '',
  });

  const [editFormData, setEditFormData] = useState<UpdateUserData & { id: string }>({
    id: '',
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    department: '',
    position: '',
    role: 'analista',
    is_active: true,
  });

  const [userToDelete, setUserToDelete] = useState<User | null>(null);

  const handleCreateClick = () => {
    setCreateFormData({
      username: '',
      email: '',
      password: '',
      password_confirm: '',
      first_name: '',
      last_name: '',
      role: 'analista',
      phone: '',
      department: '',
      position: '',
    });
    setCreateDialogOpen(true);
  };

  const handleCreateSubmit = () => {
    if (!createFormData.username || !createFormData.email || !createFormData.password || !createFormData.first_name || !createFormData.last_name) {
      toast({
        title: "Campos obrigatórios",
        description: "Preencha username, email, senha, nome e sobrenome.",
        variant: "destructive",
      });
      return;
    }

    if (createFormData.password !== createFormData.password_confirm) {
      toast({
        title: "Senhas não coincidem",
        description: "As senhas digitadas não são iguais.",
        variant: "destructive",
      });
      return;
    }

    createUser(createFormData, {
      onSuccess: () => {
        toast({
          title: "Usuário criado",
          description: "O usuário foi criado com sucesso.",
        });
        setCreateDialogOpen(false);
      },
      onError: (error: any) => {
        const errorData = error.response?.data;
        let errorMessage = "Ocorreu um erro ao criar o usuário.";

        if (errorData) {
          // Extrair todas as mensagens de erro
          const errors: string[] = [];
          if (typeof errorData === 'object') {
            Object.keys(errorData).forEach(key => {
              if (Array.isArray(errorData[key])) {
                errors.push(`${key}: ${errorData[key].join(', ')}`);
              } else if (typeof errorData[key] === 'string') {
                errors.push(`${key}: ${errorData[key]}`);
              }
            });
          }
          if (errors.length > 0) {
            errorMessage = errors.join('\n');
          } else if (typeof errorData === 'string') {
            errorMessage = errorData;
          } else if (errorData.detail) {
            errorMessage = errorData.detail;
          }
        }

        toast({
          title: "Erro ao criar usuário",
          description: errorMessage,
          variant: "destructive",
        });
      },
    });
  };

  const handleEditClick = (user: User) => {
    setEditFormData({
      id: user.id,
      first_name: user.first_name,
      last_name: user.last_name,
      email: user.email,
      phone: user.phone || '',
      department: user.department || '',
      position: user.position || '',
      role: user.role,
      is_active: user.is_active,
    });
    setEditDialogOpen(true);
  };

  const handleEditSubmit = () => {
    const { id, ...data } = editFormData;

    updateUser({ id, data }, {
      onSuccess: () => {
        toast({
          title: "Usuário atualizado",
          description: "Os dados do usuário foram atualizados com sucesso.",
        });
        setEditDialogOpen(false);
      },
      onError: (error: any) => {
        toast({
          title: "Erro ao atualizar usuário",
          description: error.response?.data?.detail || "Ocorreu um erro ao atualizar o usuário.",
          variant: "destructive",
        });
      },
    });
  };

  const handleDeleteClick = (user: User) => {
    setUserToDelete(user);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = () => {
    if (!userToDelete) return;

    deleteUser(userToDelete.id, {
      onSuccess: () => {
        toast({
          title: "Usuário excluído",
          description: "O usuário foi removido do sistema.",
        });
        setDeleteDialogOpen(false);
        setUserToDelete(null);
      },
      onError: (error: any) => {
        toast({
          title: "Erro ao excluir usuário",
          description: error.response?.data?.detail || "Ocorreu um erro ao excluir o usuário.",
          variant: "destructive",
        });
      },
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Usuários</h1>
          <p className="text-muted-foreground">Gerenciar usuários do sistema</p>
        </div>
        <Button onClick={handleCreateClick}>
          <Plus className="mr-2 h-4 w-4" />
          Novo Usuário
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Lista de Usuários ({count})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nome</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Departamento</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Criado em</TableHead>
                  <TableHead className="text-right">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell className="font-medium">{user.full_name}</TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      <Badge variant={roleColors[user.role]}>
                        {roleLabels[user.role]}
                      </Badge>
                    </TableCell>
                    <TableCell>{user.department || '-'}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {user.is_active ? (
                          <>
                            <UserCheck className="h-4 w-4 text-green-600" />
                            <span className="text-sm">Ativo</span>
                          </>
                        ) : (
                          <>
                            <UserX className="h-4 w-4 text-red-600" />
                            <span className="text-sm">Inativo</span>
                          </>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      {new Date(user.created_at).toLocaleDateString('pt-BR')}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEditClick(user)}
                          disabled={isUpdating || isDeleting}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteClick(user)}
                          disabled={isUpdating || isDeleting}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Create User Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Criar Novo Usuário</DialogTitle>
            <DialogDescription>
              Preencha os dados do novo usuário
            </DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="create-username">Username *</Label>
              <Input
                id="create-username"
                value={createFormData.username}
                onChange={(e) => setCreateFormData({ ...createFormData, username: e.target.value })}
                placeholder="usuario123"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="create-email">Email *</Label>
              <Input
                id="create-email"
                type="email"
                value={createFormData.email}
                onChange={(e) => setCreateFormData({ ...createFormData, email: e.target.value })}
                placeholder="usuario@verus.ai"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="create-first-name">Nome *</Label>
              <AIInput
                id="create-first-name"
                value={createFormData.first_name}
                onChange={(e) => setCreateFormData({ ...createFormData, first_name: e.target.value })}
                setValue={(v) => setCreateFormData({ ...createFormData, first_name: v })}
                placeholder="João"
                aiContext="Nome do usuário a ser criado no sistema jurídico"
                aiObjective="Sugerir ou corrigir o nome próprio em português"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="create-last-name">Sobrenome *</Label>
              <AIInput
                id="create-last-name"
                value={createFormData.last_name}
                onChange={(e) => setCreateFormData({ ...createFormData, last_name: e.target.value })}
                setValue={(v) => setCreateFormData({ ...createFormData, last_name: v })}
                placeholder="Silva"
                aiContext="Sobrenome do usuário a ser criado no sistema jurídico"
                aiObjective="Sugerir ou corrigir o sobrenome em português"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="create-password">Senha *</Label>
              <Input
                id="create-password"
                type="password"
                value={createFormData.password}
                onChange={(e) => setCreateFormData({ ...createFormData, password: e.target.value })}
                placeholder="••••••••"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="create-password-confirm">Confirmar Senha *</Label>
              <Input
                id="create-password-confirm"
                type="password"
                value={createFormData.password_confirm}
                onChange={(e) => setCreateFormData({ ...createFormData, password_confirm: e.target.value })}
                placeholder="••••••••"
              />
            </div>

            <div className="space-y-2 col-span-2">
              <Label htmlFor="create-role">Perfil *</Label>
              <Select
                value={createFormData.role}
                onValueChange={(value: User['role']) => setCreateFormData({ ...createFormData, role: value })}
              >
                <SelectTrigger id="create-role">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="superadmin" className="font-semibold">Super Administrador</SelectItem>
                  <SelectItem value="admin">Administrador</SelectItem>
                  <SelectItem disabled value="_sep1" className="text-xs text-muted-foreground">--- Advocacia Privada ---</SelectItem>
                  <SelectItem value="socio">Sócio / Partner</SelectItem>
                  <SelectItem value="advogado_senior">Procurador Sênior</SelectItem>
                  <SelectItem value="advogado_pleno">Procurador Pleno</SelectItem>
                  <SelectItem value="advogado_junior">Procurador Júnior</SelectItem>
                  <SelectItem value="estagiario">Estagiário de Direito</SelectItem>
                  <SelectItem disabled value="_sep2" className="text-xs text-muted-foreground">--- Gestão ---</SelectItem>
                  <SelectItem value="gestor">Gestor / Manager</SelectItem>
                  <SelectItem value="coordenador">Coordenador Jurídico</SelectItem>
                  <SelectItem value="supervisor">Supervisor</SelectItem>
                  <SelectItem disabled value="_sep3" className="text-xs text-muted-foreground">--- Operacional ---</SelectItem>
                  <SelectItem value="analista">Analista Jurídico</SelectItem>
                  <SelectItem value="assistente">Assistente de Procuradoria</SelectItem>
                  <SelectItem value="paralegal">Paralegal / Técnico Jurídico</SelectItem>
                  <SelectItem value="secretaria">Secretária Jurídica</SelectItem>
                  <SelectItem disabled value="_sep4" className="text-xs text-muted-foreground">--- Setor Público ---</SelectItem>
                  <SelectItem value="procurador">Procurador</SelectItem>
                  <SelectItem value="defensor">Defensor Público</SelectItem>
                  <SelectItem value="promotor">Promotor de Justiça</SelectItem>
                  <SelectItem value="assessor">Assessor Jurídico</SelectItem>
                  <SelectItem value="servidor">Servidor Público</SelectItem>
                  <SelectItem disabled value="_sep5" className="text-xs text-muted-foreground">--- Revisão e Controle ---</SelectItem>
                  <SelectItem value="revisor">Revisor</SelectItem>
                  <SelectItem value="auditor">Auditor Jurídico</SelectItem>
                  <SelectItem disabled value="_sep6" className="text-xs text-muted-foreground">--- Acesso Limitado ---</SelectItem>
                  <SelectItem value="cliente">Parte</SelectItem>
                  <SelectItem value="visualizador">Visualizador</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="create-phone">Telefone</Label>
              <Input
                id="create-phone"
                value={createFormData.phone}
                onChange={(e) => setCreateFormData({ ...createFormData, phone: e.target.value })}
                placeholder="(11) 98765-4321"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="create-department">Departamento</Label>
              <AIInput
                id="create-department"
                value={createFormData.department}
                onChange={(e) => setCreateFormData({ ...createFormData, department: e.target.value })}
                setValue={(v) => setCreateFormData({ ...createFormData, department: v })}
                placeholder="TI"
                aiContext="Nome do departamento do usuário em um escritório jurídico"
                aiObjective="Sugerir ou corrigir o nome do departamento em português"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="create-position">Cargo</Label>
              <AIInput
                id="create-position"
                value={createFormData.position}
                onChange={(e) => setCreateFormData({ ...createFormData, position: e.target.value })}
                setValue={(v) => setCreateFormData({ ...createFormData, position: v })}
                placeholder="Analista de Sistemas"
                aiContext="Cargo ou função do usuário em um escritório jurídico ou procuradoria"
                aiObjective="Sugerir ou corrigir o cargo em português"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
              Cancelar
            </Button>
            <Button onClick={handleCreateSubmit} disabled={isCreating}>
              {isCreating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Criando...
                </>
              ) : (
                'Criar Usuário'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit User Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Editar Usuário</DialogTitle>
            <DialogDescription>
              Atualizar dados do usuário
            </DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-first-name">Nome</Label>
              <AIInput
                id="edit-first-name"
                value={editFormData.first_name}
                onChange={(e) => setEditFormData({ ...editFormData, first_name: e.target.value })}
                setValue={(v) => setEditFormData({ ...editFormData, first_name: v })}
                aiContext="Nome do usuário no sistema jurídico"
                aiObjective="Sugerir ou corrigir o nome próprio em português"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-last-name">Sobrenome</Label>
              <AIInput
                id="edit-last-name"
                value={editFormData.last_name}
                onChange={(e) => setEditFormData({ ...editFormData, last_name: e.target.value })}
                setValue={(v) => setEditFormData({ ...editFormData, last_name: v })}
                aiContext="Sobrenome do usuário no sistema jurídico"
                aiObjective="Sugerir ou corrigir o sobrenome em português"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-email">Email</Label>
              <Input
                id="edit-email"
                type="email"
                value={editFormData.email}
                onChange={(e) => setEditFormData({ ...editFormData, email: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-phone">Telefone</Label>
              <Input
                id="edit-phone"
                value={editFormData.phone}
                onChange={(e) => setEditFormData({ ...editFormData, phone: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-department">Departamento</Label>
              <AIInput
                id="edit-department"
                value={editFormData.department}
                onChange={(e) => setEditFormData({ ...editFormData, department: e.target.value })}
                setValue={(v) => setEditFormData({ ...editFormData, department: v })}
                aiContext="Nome do departamento do usuário em um escritório jurídico"
                aiObjective="Sugerir ou corrigir o nome do departamento em português"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-position">Cargo</Label>
              <AIInput
                id="edit-position"
                value={editFormData.position}
                onChange={(e) => setEditFormData({ ...editFormData, position: e.target.value })}
                setValue={(v) => setEditFormData({ ...editFormData, position: v })}
                aiContext="Cargo ou função do usuário em um escritório jurídico ou procuradoria"
                aiObjective="Sugerir ou corrigir o cargo em português"
              />
            </div>

            <div className="space-y-2 col-span-2">
              <Label htmlFor="edit-role">Perfil</Label>
              <Select
                value={editFormData.role}
                onValueChange={(value: User['role']) => setEditFormData({ ...editFormData, role: value })}
              >
                <SelectTrigger id="edit-role">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="superadmin" className="font-semibold">Super Administrador</SelectItem>
                  <SelectItem value="admin">Administrador</SelectItem>
                  <SelectItem disabled value="_sep1" className="text-xs text-muted-foreground">--- Advocacia Privada ---</SelectItem>
                  <SelectItem value="socio">Sócio / Partner</SelectItem>
                  <SelectItem value="advogado_senior">Procurador Sênior</SelectItem>
                  <SelectItem value="advogado_pleno">Procurador Pleno</SelectItem>
                  <SelectItem value="advogado_junior">Procurador Júnior</SelectItem>
                  <SelectItem value="estagiario">Estagiário de Direito</SelectItem>
                  <SelectItem disabled value="_sep2" className="text-xs text-muted-foreground">--- Gestão ---</SelectItem>
                  <SelectItem value="gestor">Gestor / Manager</SelectItem>
                  <SelectItem value="coordenador">Coordenador Jurídico</SelectItem>
                  <SelectItem value="supervisor">Supervisor</SelectItem>
                  <SelectItem disabled value="_sep3" className="text-xs text-muted-foreground">--- Operacional ---</SelectItem>
                  <SelectItem value="analista">Analista Jurídico</SelectItem>
                  <SelectItem value="assistente">Assistente de Procuradoria</SelectItem>
                  <SelectItem value="paralegal">Paralegal / Técnico Jurídico</SelectItem>
                  <SelectItem value="secretaria">Secretária Jurídica</SelectItem>
                  <SelectItem disabled value="_sep4" className="text-xs text-muted-foreground">--- Setor Público ---</SelectItem>
                  <SelectItem value="procurador">Procurador</SelectItem>
                  <SelectItem value="defensor">Defensor Público</SelectItem>
                  <SelectItem value="promotor">Promotor de Justiça</SelectItem>
                  <SelectItem value="assessor">Assessor Jurídico</SelectItem>
                  <SelectItem value="servidor">Servidor Público</SelectItem>
                  <SelectItem disabled value="_sep5" className="text-xs text-muted-foreground">--- Revisão e Controle ---</SelectItem>
                  <SelectItem value="revisor">Revisor</SelectItem>
                  <SelectItem value="auditor">Auditor Jurídico</SelectItem>
                  <SelectItem disabled value="_sep6" className="text-xs text-muted-foreground">--- Acesso Limitado ---</SelectItem>
                  <SelectItem value="cliente">Parte</SelectItem>
                  <SelectItem value="visualizador">Visualizador</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-is-active">Status</Label>
              <Select
                value={editFormData.is_active ? 'true' : 'false'}
                onValueChange={(value) => setEditFormData({ ...editFormData, is_active: value === 'true' })}
              >
                <SelectTrigger id="edit-is-active">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="true">Ativo</SelectItem>
                  <SelectItem value="false">Inativo</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
              Cancelar
            </Button>
            <Button onClick={handleEditSubmit} disabled={isUpdating}>
              {isUpdating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Salvando...
                </>
              ) : (
                'Salvar Alterações'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirmar Exclusão</DialogTitle>
            <DialogDescription>
              Tem certeza que deseja excluir o usuário <strong>{userToDelete?.full_name}</strong>? Esta ação não pode ser desfeita.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)} disabled={isDeleting}>
              Cancelar
            </Button>
            <Button variant="destructive" onClick={handleDeleteConfirm} disabled={isDeleting}>
              {isDeleting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Excluindo...
                </>
              ) : (
                <>
                  <Trash2 className="mr-2 h-4 w-4" />
                  Excluir
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
