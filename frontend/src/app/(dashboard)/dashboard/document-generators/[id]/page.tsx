'use client';

import { useParams, useRouter } from 'next/navigation';
import { useDocumentGenerators } from '@/hooks/use-document-generators';
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
  FileText,
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
import EditDocumentGeneratorDialog from '@/components/documents/EditDocumentGeneratorDialog';

const documentTypeLabels: Record<string, { label: string; icon: string; color: string }> = {
  peticao_inicial: {
    label: 'Petição Inicial',
    icon: '📄',
    color: 'bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300',
  },
  contestacao: {
    label: 'Contestação',
    icon: '📋',
    color: 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300',
  },
  recurso: {
    label: 'Recurso',
    icon: '📑',
    color: 'bg-orange-100 text-orange-700 dark:bg-orange-950 dark:text-orange-300',
  },
  memoriais: {
    label: 'Memoriais',
    icon: '📝',
    color: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300',
  },
  tutela_urgencia: {
    label: 'Tutela de Urgência',
    icon: '⚡',
    color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-950 dark:text-yellow-300',
  },
  impugnacao: {
    label: 'Impugnação',
    icon: '🚫',
    color: 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300',
  },
  embargos_declaracao: {
    label: 'Embargos de Declaração',
    icon: '📜',
    color: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
  },
  contrato: {
    label: 'Contrato',
    icon: '🤝',
    color: 'bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300',
  },
  procuracao: {
    label: 'Procuração',
    icon: '✍️',
    color: 'bg-teal-100 text-teal-700 dark:bg-teal-950 dark:text-teal-300',
  },
  notificacao_extrajudicial: {
    label: 'Notificação Extrajudicial',
    icon: '📬',
    color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
  },
  parecer: {
    label: 'Parecer Jurídico',
    icon: '📊',
    color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-950 dark:text-yellow-200',
  },
  nota_juridica: {
    label: 'Nota Jurídica',
    icon: '🗒️',
    color: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300',
  },
  habeas_corpus: {
    label: 'Habeas Corpus',
    icon: '⚖️',
    color: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200',
  },
  mandado_seguranca: {
    label: 'Mandado de Segurança',
    icon: '🛡️',
    color: 'bg-violet-100 text-violet-700 dark:bg-violet-950 dark:text-violet-300',
  },
  acao_popular: {
    label: 'Ação Popular',
    icon: '🏛️',
    color: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-200',
  },
  acao_civil_publica: {
    label: 'Ação Civil Pública',
    icon: '🌿',
    color: 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-200',
  },
};

const providerLabels: Record<string, string> = {
  openai: 'OpenAI',
  watsonx: 'IBM WatsonX',
};

export default function DocumentGeneratorDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const generatorId = params?.id as string;

  const { useDocumentGenerator, deleteGenerator, isDeleting } = useDocumentGenerators();
  const { data: generator, isLoading, error } = useDocumentGenerator(generatorId);

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
      await deleteGenerator(generatorId);
      toast({
        title: 'Gerador deletado',
        description: 'O gerador foi removido com sucesso.',
      });
      router.push('/dashboard/document-generators');
    } catch (error: any) {
      toast({
        title: 'Erro ao deletar',
        description: error.response?.data?.detail || 'Não foi possível deletar o gerador.',
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

  if (error || !generator) {
    return (
      <div className="space-y-6">
        <Link href="/dashboard/document-generators">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Voltar
          </Button>
        </Link>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Não foi possível carregar os detalhes do gerador. Ele pode ter sido deletado ou você não
            tem permissão para visualizá-lo.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const typeInfo = documentTypeLabels[generator.document_type] || {
    label: generator.document_type,
    icon: '📄',
    color: 'bg-gray-100 text-gray-700',
  };

  const variables = extractVariables(generator.user_prompt_template);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Link href="/dashboard/document-generators">
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
          <FileText className="h-8 w-8 text-primary" />
          <h1 className="text-3xl font-bold">{generator.name}</h1>
        </div>
        {generator.description && (
          <p className="text-muted-foreground text-lg">{generator.description}</p>
        )}

        <div className="flex gap-2 mt-4">
          {generator.is_active ? (
            <Badge variant="default">Ativo</Badge>
          ) : (
            <Badge variant="secondary">Inativo</Badge>
          )}
          {generator.is_default && (
            <Badge variant="outline" className="border-purple-500 text-purple-700">
              Padrão
            </Badge>
          )}
          {generator.use_rag && (
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
              {providerLabels[generator.llm_provider] || generator.llm_provider}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Modelo</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold truncate" title={generator.model_name}>
              {generator.model_name}
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
            <div className="text-2xl font-bold">{generator.temperature}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Max Tokens
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{generator.max_tokens}</div>
          </CardContent>
        </Card>
      </div>

      {/* System Prompt */}
      <Card>
        <CardHeader>
          <CardTitle>System Prompt</CardTitle>
          <CardDescription>Instruções gerais para o comportamento do gerador</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="bg-muted p-4 rounded-lg">
            <pre className="whitespace-pre-wrap font-mono text-sm">{generator.system_prompt}</pre>
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
              {generator.user_prompt_template}
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
      {generator.use_rag && (
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
                {generator.rag_query_template || 'Nenhum template configurado'}
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
            <span className="text-muted-foreground">Tipo de Documento:</span>
            <span className="font-medium">{typeInfo.label}</span>
          </div>
          {generator.document_template_name && (
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Template de Documento:</span>
              <span className="font-medium">{generator.document_template_name}</span>
            </div>
          )}
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Criado por:</span>
            <span className="font-medium">{generator.created_by_name || 'N/A'}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Criado em:</span>
            <span className="font-medium">
              {new Date(generator.created_at).toLocaleDateString('pt-BR')}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Última atualização:</span>
            <span className="font-medium">
              {new Date(generator.updated_at).toLocaleDateString('pt-BR')}
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Edit Generator Dialog */}
      <EditDocumentGeneratorDialog
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
        generator={generator}
        onSuccess={() => {
          toast({
            title: 'Gerador atualizado',
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
              Tem certeza que deseja deletar o gerador &quot;{generator.name}&quot;? Esta ação não pode
              ser desfeita.
              {generator.is_default && (
                <span className="block mt-2 text-amber-600 font-medium">
                  ⚠️ Este é um gerador padrão. Deletá-lo pode afetar o funcionamento do sistema.
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
