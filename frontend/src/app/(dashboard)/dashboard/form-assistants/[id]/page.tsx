'use client';

import { useParams, useRouter } from 'next/navigation';
import { useFormAssistants } from '@/hooks/use-form-assistants';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
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
  FileEdit,
  ArrowLeft,
  Edit,
  Trash2,
  Copy,
  Sparkles,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { useState } from 'react';
import Link from 'next/link';
import { Alert, AlertDescription } from '@/components/ui/alert';
import EditFormAssistantDialog from '@/components/forms/EditFormAssistantDialog';

const assistantTypeLabels: Record<string, { label: string; icon: string; color: string }> = {
  corretor: {
    label: 'Corretor de Texto',
    icon: '✍️',
    color: 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300',
  },
  tradutor: {
    label: 'Tradutor',
    icon: '🌐',
    color: 'bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300',
  },
  expansao: {
    label: 'Expansor de Conteúdo',
    icon: '📝',
    color: 'bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300',
  },
  sugestao: {
    label: 'Sugestor',
    icon: '💡',
    color: 'bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300',
  },
  resumo: {
    label: 'Resumidor',
    icon: '📋',
    color: 'bg-orange-100 text-orange-700 dark:bg-orange-950 dark:text-orange-300',
  },
  simplificacao: {
    label: 'Simplificador',
    icon: '✂️',
    color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-950 dark:text-yellow-300',
  },
};

const providerLabels: Record<string, string> = {
  openai: 'OpenAI',
  anthropic: 'Anthropic',
};

export default function FormAssistantDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const assistantId = params?.id as string;

  const { useFormAssistant, deleteAssistant, isDeleting } = useFormAssistants();
  const { data: assistant, isLoading, error } = useFormAssistant(assistantId);

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  // Extract variables from template
  const extractVariables = (template: string): string[] => {
    if (!template || typeof template !== 'string') return [];
    const regex = /\{\{(\w+)\}\}/g;
    const matches = template.matchAll(regex);
    const variables = new Set<string>();
    for (const match of matches) {
      variables.add(match[1]);
    }
    return Array.from(variables);
  };

  const handleDelete = async () => {
    try {
      await deleteAssistant(assistantId);
      toast({
        title: 'Assistente deletado',
        description: 'O assistente foi removido com sucesso.',
      });
      router.push('/dashboard/form-assistants');
    } catch (error: any) {
      toast({
        title: 'Erro ao deletar',
        description: error.response?.data?.detail || 'Não foi possível deletar o assistente.',
        variant: 'destructive',
      });
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !assistant) {
    return (
      <div className="space-y-6">
        <Link href="/dashboard/form-assistants">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Voltar
          </Button>
        </Link>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Não foi possível carregar os detalhes do assistente. Ele pode ter sido deletado ou você não
            tem permissão para visualizá-lo.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const typeInfo = assistantTypeLabels[assistant.assistant_type] || {
    label: assistant.assistant_type,
    icon: '🤖',
    color: 'bg-gray-100 text-gray-700',
  };

  const variables = extractVariables(assistant.user_prompt_template);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Link href="/dashboard/form-assistants">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Voltar
          </Button>
        </Link>

        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => setEditDialogOpen(true)}>
            <Edit className="mr-2 h-4 w-4" />
            Editar
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setDeleteDialogOpen(true)}
            disabled={isDeleting}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Deletar
          </Button>
        </div>
      </div>

      {/* Title and Description */}
      <div>
        <div className="flex items-center gap-3 mb-2">
          <FileEdit className="h-8 w-8 text-primary" />
          <h1 className="text-3xl font-bold">{assistant.name}</h1>
        </div>
        {assistant.description && (
          <p className="text-muted-foreground text-lg">{assistant.description}</p>
        )}

        <div className="flex gap-2 mt-4">
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
            <Badge
              variant="secondary"
              className="bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300"
            >
              <Sparkles className="h-3 w-3 mr-1" />
              RAG
            </Badge>
          )}
          <Badge className={typeInfo.color}>
            <span className="mr-1">{typeInfo.icon}</span>
            {typeInfo.label}
          </Badge>
        </div>
      </div>

      <Separator />

      {/* Configuration Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Provider</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {providerLabels[assistant.llm_provider] || assistant.llm_provider}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Modelo</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold truncate" title={assistant.model_name}>
              {assistant.model_name}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Temperature
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{assistant.temperature}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Max Tokens
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{assistant.max_tokens}</div>
          </CardContent>
        </Card>
      </div>

      {/* System Prompt */}
      <Card>
        <CardHeader>
          <CardTitle>System Prompt</CardTitle>
          <CardDescription>Instruções gerais para o comportamento do assistente</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="bg-muted p-4 rounded-lg">
            <pre className="whitespace-pre-wrap font-mono text-sm">{assistant.system_prompt}</pre>
          </div>
        </CardContent>
      </Card>

      {/* User Prompt Template */}
      <Card>
        <CardHeader>
          <CardTitle>User Prompt Template</CardTitle>
          <CardDescription>Template de prompt com variáveis dinâmicas</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-muted p-4 rounded-lg">
            <pre className="whitespace-pre-wrap font-mono text-sm">
              {assistant.user_prompt_template}
            </pre>
          </div>

          {variables.length > 0 && (
            <div>
              <div className="text-sm font-medium mb-2">Variáveis detectadas:</div>
              <div className="flex flex-wrap gap-2">
                {variables.map((variable) => (
                  <Badge
                    key={variable}
                    variant="secondary"
                    className="bg-primary/10 text-primary font-mono"
                  >
                    {variable}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* RAG Configuration */}
      {assistant.use_rag && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-indigo-600" />
              <CardTitle>Configuração RAG</CardTitle>
            </div>
            <CardDescription>Template de query para busca na base de conhecimento</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="bg-muted p-4 rounded-lg">
              <pre className="whitespace-pre-wrap font-mono text-sm">
                {assistant.rag_query_template || 'Nenhum template configurado'}
              </pre>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Metadata */}
      <Card>
        <CardHeader>
          <CardTitle>Informações</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Criado por:</span>
            <span className="font-medium">{assistant.created_by_name || 'N/A'}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Criado em:</span>
            <span className="font-medium">
              {new Date(assistant.created_at).toLocaleDateString('pt-BR')}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Última atualização:</span>
            <span className="font-medium">
              {new Date(assistant.updated_at).toLocaleDateString('pt-BR')}
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Edit Assistant Dialog */}
      <EditFormAssistantDialog
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
        assistant={assistant}
        onSuccess={() => {
          toast({
            title: 'Assistente atualizado',
            description: 'As alterações foram salvas com sucesso.',
          });
        }}
      />

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirmar exclusão</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja deletar o assistente &quot;{assistant.name}&quot;? Esta ação não pode
              ser desfeita.
              {assistant.is_default && (
                <span className="block mt-2 text-amber-600 font-medium">
                  ⚠️ Este é um assistente padrão. Deletá-lo pode afetar o funcionamento dos formulários.
                </span>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
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
