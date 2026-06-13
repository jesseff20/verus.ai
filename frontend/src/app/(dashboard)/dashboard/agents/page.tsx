'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useAgents } from '@/hooks/use-agents';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Brain, Plus, Eye, Edit, Trash2, Loader2, Sparkles,
  Copy, FileText, MessageSquare, FileEdit
} from 'lucide-react';
import * as LucideIcons from 'lucide-react';
import type { AgentPrompt } from '@/types';
import CreateAgentDialog from '@/components/agents/CreateAgentDialog';
import EditAgentDialog from '@/components/agents/EditAgentDialog';

const providerLabels: Record<string, string> = {
  openai: 'OpenAI',
  watsonx: 'IBM WatsonX',
};

export default function AgentsPage() {
  const {
    agents,
    count,
    isLoading,
    refetch,
    deleteAgent,
    isDeleting,
    duplicateAgent,
    isDuplicating,
    useStats
  } = useAgents(1, 100);

  const { data: stats } = useStats();
  const { toast } = useToast();

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [agentToDelete, setAgentToDelete] = useState<AgentPrompt | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [agentToEdit, setAgentToEdit] = useState<AgentPrompt | null>(null);

  const handleDeleteClick = (agent: AgentPrompt) => {
    setAgentToDelete(agent);
    setDeleteDialogOpen(true);
  };

  const handleEditClick = (agent: AgentPrompt) => {
    setAgentToEdit(agent);
    setEditDialogOpen(true);
  };

  const handleDuplicateClick = async (agent: AgentPrompt) => {
    try {
      await duplicateAgent(agent.id);
      toast({
        title: 'Agente duplicado',
        description: `Uma cópia de "${agent.name}" foi criada com sucesso.`,
      });
      refetch();
    } catch (error: any) {
      toast({
        title: 'Erro ao duplicar',
        description: error.response?.data?.detail || 'Não foi possível duplicar o agente.',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteConfirm = async () => {
    if (!agentToDelete) return;

    try {
      await deleteAgent(agentToDelete.id);
      toast({
        title: 'Agente deletado',
        description: `O agente "${agentToDelete.name}" foi removido com sucesso.`,
      });
      setDeleteDialogOpen(false);
      setAgentToDelete(null);
      refetch();
    } catch (error: any) {
      toast({
        title: 'Erro ao deletar',
        description: error.response?.data?.detail || 'Não foi possível deletar o agente.',
        variant: 'destructive',
      });
    }
  };

  // Função para obter ícone dinamicamente
  const getIcon = (iconName: string) => {
    const Icon = (LucideIcons as any)[iconName] || LucideIcons.Bot;
    return Icon;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Agentes de IA</h1>
          <p className="text-muted-foreground">
            Prompts configuráveis para assistência com IA
          </p>
        </div>
        <Button onClick={() => setCreateDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Novo Agente
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Agentes de Chat</CardTitle>
              <MessageSquare className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.by_category.chat_assistant.count}</div>
              <p className="text-xs text-muted-foreground">
                {stats.by_category.chat_assistant.active} ativos
              </p>
            </CardContent>
          </Card>

          <Link href="/dashboard/form-assistants">
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Assistentes de Formulário</CardTitle>
                <FileEdit className="h-4 w-4 text-blue-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">Ver todos</div>
                <p className="text-xs text-muted-foreground">
                  Gerenciar assistentes de campo
                </p>
              </CardContent>
            </Card>
          </Link>

          <Link href="/dashboard/document-generators">
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Geradores de Documento</CardTitle>
                <FileText className="h-4 w-4 text-purple-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">Ver todos</div>
                <p className="text-xs text-muted-foreground">
                  Gerenciar geradores de documento
                </p>
              </CardContent>
            </Card>
          </Link>
        </div>
      )}

      {/* Lista de Agentes */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : agents.length === 0 ? (
        <Card className="p-12">
          <div className="flex flex-col items-center text-center gap-4">
            <Brain className="h-16 w-16 text-muted-foreground opacity-50" />
            <div>
              <h3 className="text-lg font-semibold mb-2">
                Nenhum agente configurado
              </h3>
              <p className="text-sm text-muted-foreground mb-4">
                Crie seu primeiro agente de IA para começar a usar assistência inteligente
              </p>
            </div>
            <Button onClick={() => setCreateDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Criar Agente
            </Button>
          </div>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {agents.map((agent) => {
            const Icon = getIcon(agent.icon);

            return (
              <Card key={agent.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <Icon
                        className="h-8 w-8"
                        style={{ color: agent.color }}
                      />
                    </div>
                    <div className="flex gap-2 flex-wrap">
                      {agent.is_active ? (
                        <Badge variant="default">Ativo</Badge>
                      ) : (
                        <Badge variant="secondary">Inativo</Badge>
                      )}
                      {agent.is_default && (
                        <Badge variant="outline" className="border-purple-500 text-purple-700">
                          Padrão
                        </Badge>
                      )}
                      {agent.use_rag && (
                        <Badge variant="secondary" className="bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
                          <Sparkles className="h-3 w-3 mr-1" />
                          RAG
                        </Badge>
                      )}
                    </div>
                  </div>
                  <CardTitle className="mt-4 line-clamp-1">{agent.name}</CardTitle>
                  <CardDescription className="line-clamp-2">
                    {agent.description || 'Sem descrição'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {/* Badge de Tipo */}
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="flex items-center gap-1">
                        <MessageSquare className="h-3 w-3" />
                        Agente de Chat
                      </Badge>
                      <Badge variant="secondary" className="text-xs">
                        {agent.agent_type}
                      </Badge>
                    </div>

                    {/* Informações Técnicas */}
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <p className="text-muted-foreground text-xs">Provider</p>
                        <p className="font-medium">{agent.provider_display || providerLabels[agent.llm_provider]}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground text-xs">Modelo</p>
                        <p className="font-medium text-xs truncate" title={agent.model_name}>
                          {agent.model_name}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground text-xs">Temperature</p>
                        <p className="font-medium">{agent.temperature}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground text-xs">Max Tokens</p>
                        <p className="font-medium">{agent.max_tokens}</p>
                      </div>
                    </div>

                    {/* Metadados */}
                    {(agent.variable_count > 0 || agent.created_by_name) && (
                      <div className="pt-2 border-t space-y-1">
                        {agent.variable_count > 0 && (
                          <p className="text-xs text-muted-foreground">
                            Variáveis: <span className="font-medium">{agent.variable_count}</span>
                          </p>
                        )}
                        {agent.created_by_name && (
                          <p className="text-xs text-muted-foreground">
                            Criado por: <span className="font-medium">{agent.created_by_name}</span>
                          </p>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Ações */}
                  <div className="flex gap-2 mt-4">
                    <Link href={`/dashboard/agents/${agent.id}`} className="flex-1">
                      <Button variant="outline" className="w-full" size="sm">
                        <Eye className="mr-2 h-4 w-4" />
                        Detalhes
                      </Button>
                    </Link>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDuplicateClick(agent)}
                      title="Duplicar agente"
                      disabled={isDuplicating}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEditClick(agent)}
                      title="Editar agente"
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteClick(agent)}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      title="Deletar agente"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Create Agent Dialog */}
      <CreateAgentDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onSuccess={refetch}
      />

      {/* Edit Agent Dialog */}
      {agentToEdit && (
        <EditAgentDialog
          open={editDialogOpen}
          onOpenChange={setEditDialogOpen}
          agent={agentToEdit}
          onSuccess={refetch}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirmar exclusão</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja deletar o agente &quot;{agentToDelete?.name}&quot;?
              Esta ação não pode ser desfeita.
              {agentToDelete?.is_default && (
                <span className="block mt-2 text-amber-600 font-medium">
                  ⚠️ Este é um agente padrão. Deletá-lo pode afetar o funcionamento do sistema.
                </span>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={isDeleting}
            >
              {isDeleting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Deletando...
                </>
              ) : (
                'Deletar'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
