'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useFormAssistants } from '@/hooks/use-form-assistants';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
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
  Plus, Eye, Edit, Trash2, Loader2, Sparkles,
  Copy, FileEdit, Search, Filter, ArrowLeft
} from 'lucide-react';
import * as LucideIcons from 'lucide-react';
import type { FormAssistant } from '@/hooks/use-form-assistants';
import CreateAgentDialog from '@/components/agents/CreateAgentDialog';
import EditFormAssistantDialog from '@/components/forms/EditFormAssistantDialog';

const providerLabels: Record<string, string> = {
  openai: 'OpenAI',
  anthropic: 'Anthropic',
};

const assistantTypeLabels: Record<string, { label: string; color: string }> = {
  corretor: { label: 'Corretor', color: 'bg-red-100 text-red-700' },
  tradutor: { label: 'Tradutor', color: 'bg-blue-100 text-blue-700' },
  expansao: { label: 'Expansor', color: 'bg-green-100 text-green-700' },
  sugestao: { label: 'Sugestor', color: 'bg-purple-100 text-purple-700' },
  resumo: { label: 'Resumidor', color: 'bg-orange-100 text-orange-700' },
  simplificacao: { label: 'Simplificador', color: 'bg-yellow-100 text-yellow-700' },
  analise: { label: 'Analisador', color: 'bg-indigo-100 text-indigo-700' },
  exemplo: { label: 'Gerador de Exemplos', color: 'bg-pink-100 text-pink-700' },
};

export default function FormAssistantsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [providerFilter, setProviderFilter] = useState<string>('all');

  const {
    assistants,
    count,
    isLoading,
    refetch,
    deleteAssistant,
    isDeleting,
    duplicateAssistant,
    isDuplicating,
    useStats
  } = useFormAssistants(1, 100);

  const { data: stats } = useStats();
  const { toast } = useToast();

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [assistantToDelete, setAssistantToDelete] = useState<FormAssistant | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [assistantToEdit, setAssistantToEdit] = useState<FormAssistant | null>(null);

  const handleDeleteClick = (assistant: FormAssistant) => {
    setAssistantToDelete(assistant);
    setDeleteDialogOpen(true);
  };

  const handleEditClick = (assistant: FormAssistant) => {
    setAssistantToEdit(assistant);
    setEditDialogOpen(true);
  };

  const handleDuplicateClick = async (assistant: FormAssistant) => {
    try {
      await duplicateAssistant(assistant.id);
      toast({
        title: 'Assistente duplicado',
        description: `Uma cópia de "${assistant.name}" foi criada com sucesso.`,
      });
      refetch();
    } catch (error: any) {
      toast({
        title: 'Erro ao duplicar',
        description: error.response?.data?.detail || 'Não foi possível duplicar o assistente.',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteConfirm = async () => {
    if (!assistantToDelete) return;

    try {
      await deleteAssistant(assistantToDelete.id);
      toast({
        title: 'Assistente deletado',
        description: `O assistente "${assistantToDelete.name}" foi removido com sucesso.`,
      });
      setDeleteDialogOpen(false);
      setAssistantToDelete(null);
      refetch();
    } catch (error: any) {
      toast({
        title: 'Erro ao deletar',
        description: error.response?.data?.detail || 'Não foi possível deletar o assistente.',
        variant: 'destructive',
      });
    }
  };

  // Função para obter ícone dinamicamente
  const getIcon = (iconName: string) => {
    const Icon = (LucideIcons as any)[iconName] || LucideIcons.Bot;
    return Icon;
  };

  // Filtrar assistentes
  const filteredAssistants = assistants.filter(assistant => {
    const matchesSearch = assistant.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         assistant.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = typeFilter === 'all' || assistant.assistant_type === typeFilter;
    const matchesProvider = providerFilter === 'all' || assistant.llm_provider === providerFilter;

    return matchesSearch && matchesType && matchesProvider;
  });

  // Obter tipos únicos dos assistentes
  const uniqueTypes = Array.from(new Set(assistants.map(a => a.assistant_type)));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/dashboard/agents">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Voltar
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold">Assistentes de Formulário</h1>
            <p className="text-muted-foreground">
              Agentes de IA para assistir no preenchimento de campos
            </p>
          </div>
        </div>
        <Button onClick={() => setCreateDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Novo Assistente
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total de Assistentes</CardTitle>
              <FileEdit className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total}</div>
              <p className="text-xs text-muted-foreground">
                {stats.active} ativos
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">OpenAI</CardTitle>
              <Sparkles className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.by_provider.openai.count}</div>
              <p className="text-xs text-muted-foreground">
                assistentes
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Anthropic</CardTitle>
              <Sparkles className="h-4 w-4 text-purple-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.by_provider.anthropic.count}</div>
              <p className="text-xs text-muted-foreground">
                assistentes
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Filter className="h-4 w-4" />
            Filtros
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <label className="text-sm font-medium">Buscar</label>
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Nome ou descrição..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Tipo de Assistente</label>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Todos os tipos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos os tipos</SelectItem>
                  {uniqueTypes.map(type => (
                    <SelectItem key={type} value={type}>
                      {assistantTypeLabels[type]?.label || type}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Provider</label>
              <Select value={providerFilter} onValueChange={setProviderFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Todos os providers" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos os providers</SelectItem>
                  <SelectItem value="openai">OpenAI</SelectItem>
                  <SelectItem value="anthropic">Anthropic</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {(searchTerm || typeFilter !== 'all' || providerFilter !== 'all') && (
            <div className="flex items-center justify-between pt-2 border-t">
              <p className="text-sm text-muted-foreground">
                {filteredAssistants.length} de {assistants.length} assistentes
              </p>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setSearchTerm('');
                  setTypeFilter('all');
                  setProviderFilter('all');
                }}
              >
                Limpar filtros
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Assistants Grid */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : filteredAssistants.length === 0 ? (
        <Card className="p-12">
          <div className="flex flex-col items-center text-center gap-4">
            <FileEdit className="h-16 w-16 text-muted-foreground opacity-50" />
            <div>
              <h3 className="text-lg font-semibold mb-2">
                {searchTerm || typeFilter !== 'all' || providerFilter !== 'all'
                  ? 'Nenhum assistente encontrado'
                  : 'Nenhum assistente configurado'
                }
              </h3>
              <p className="text-sm text-muted-foreground mb-4">
                {searchTerm || typeFilter !== 'all' || providerFilter !== 'all'
                  ? 'Tente ajustar os filtros de busca'
                  : 'Crie seu primeiro assistente de formulário'
                }
              </p>
            </div>
            {!(searchTerm || typeFilter !== 'all' || providerFilter !== 'all') && (
              <Button onClick={() => setCreateDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Criar Assistente
              </Button>
            )}
          </div>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredAssistants.map((assistant) => {
            const Icon = getIcon(assistant.icon || 'Bot');
            const typeInfo = assistantTypeLabels[assistant.assistant_type];

            return (
              <Card key={assistant.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <Icon
                        className="h-8 w-8"
                        style={{ color: assistant.color }}
                      />
                    </div>
                    <div className="flex gap-2 flex-wrap">
                      {assistant.is_active ? (
                        <Badge variant="default">Ativo</Badge>
                      ) : (
                        <Badge variant="secondary">Inativo</Badge>
                      )}
                      {assistant.is_default && (
                        <Badge variant="outline" className="border-purple-500 text-purple-700">
                          Padrão
                        </Badge>
                      )}
                      {assistant.use_rag && (
                        <Badge variant="secondary" className="bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
                          <Sparkles className="h-3 w-3 mr-1" />
                          RAG
                        </Badge>
                      )}
                    </div>
                  </div>
                  <CardTitle className="mt-4 line-clamp-1">{assistant.name}</CardTitle>
                  <CardDescription className="line-clamp-2">
                    {assistant.description || 'Sem descrição'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {/* Badge de Tipo */}
                    <div className="flex items-center gap-2">
                      {typeInfo && (
                        <Badge className={typeInfo.color}>
                          {typeInfo.label}
                        </Badge>
                      )}
                    </div>

                    {/* Informações Técnicas */}
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <p className="text-muted-foreground text-xs">Provider</p>
                        <p className="font-medium">{assistant.provider_display || providerLabels[assistant.llm_provider]}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground text-xs">Modelo</p>
                        <p className="font-medium text-xs truncate" title={assistant.model_name}>
                          {assistant.model_name}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground text-xs">Temperature</p>
                        <p className="font-medium">{assistant.temperature}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground text-xs">Max Tokens</p>
                        <p className="font-medium">{assistant.max_tokens}</p>
                      </div>
                    </div>

                    {/* Metadados */}
                    {(assistant.variable_count > 0 || assistant.created_by_name) && (
                      <div className="pt-2 border-t space-y-1">
                        {assistant.variable_count > 0 && (
                          <p className="text-xs text-muted-foreground">
                            Variáveis: <span className="font-medium">{assistant.variable_count}</span>
                          </p>
                        )}
                        {assistant.created_by_name && (
                          <p className="text-xs text-muted-foreground">
                            Criado por: <span className="font-medium">{assistant.created_by_name}</span>
                          </p>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Ações */}
                  <div className="flex gap-2 mt-4">
                    <Link href={`/dashboard/form-assistants/${assistant.id}`} className="flex-1">
                      <Button variant="outline" className="w-full" size="sm">
                        <Eye className="mr-2 h-4 w-4" />
                        Detalhes
                      </Button>
                    </Link>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDuplicateClick(assistant)}
                      title="Duplicar assistente"
                      disabled={isDuplicating}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEditClick(assistant)}
                      title="Editar assistente"
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteClick(assistant)}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      title="Deletar assistente"
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

      {/* Create Assistant Dialog */}
      <CreateAgentDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onSuccess={refetch}
        defaultCategory="form_assistant"
      />

      {/* Edit Assistant Dialog */}
      {assistantToEdit && (
        <EditFormAssistantDialog
          open={editDialogOpen}
          onOpenChange={setEditDialogOpen}
          assistant={assistantToEdit}
          onSuccess={refetch}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirmar exclusão</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja deletar o assistente &quot;{assistantToDelete?.name}&quot;?
              Esta ação não pode ser desfeita.
              {assistantToDelete?.is_default && (
                <span className="block mt-2 text-amber-600 font-medium">
                  ⚠️ Este é um assistente padrão. Deletá-lo pode afetar o funcionamento dos formulários.
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
