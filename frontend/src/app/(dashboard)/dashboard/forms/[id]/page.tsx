'use client';

import { useParams, useRouter } from 'next/navigation';
import { useForms } from '@/hooks/use-forms';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, ArrowLeft, Trash2, Sparkles, Copy } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useState } from 'react';
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
import { FullEditFormDialog } from '@/components/forms/FullEditFormDialog';

export default function FormDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const { useForm, deleteForm, duplicateForm, isDeleting, isDuplicating } = useForms();
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const formId = params.id as string;
  const { data: form, isLoading } = useForm(formId);

  const handleDuplicate = async () => {
    try {
      const newForm = await duplicateForm(formId);
      toast({
        title: 'Formulário duplicado',
        description: `"${newForm.name}" foi criado com sucesso.`,
      });
      router.push(`/dashboard/forms/${newForm.id}`);
    } catch (error: any) {
      toast({
        title: 'Erro ao duplicar',
        description: error.response?.data?.detail || 'Não foi possível duplicar o formulário.',
        variant: 'destructive',
      });
    }
  };

  const handleDelete = async () => {
    try {
      await deleteForm(formId);
      toast({
        title: 'Formulário deletado',
        description: 'O formulário foi removido com sucesso.',
      });
      router.push('/dashboard/forms');
    } catch (error: any) {
      toast({
        title: 'Erro ao deletar',
        description: error.response?.data?.detail || 'Não foi possível deletar o formulário.',
        variant: 'destructive',
      });
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!form) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Voltar
        </Button>
        <Card className="p-12">
          <div className="text-center">
            <h3 className="text-lg font-semibold mb-2">Formulário não encontrado</h3>
            <p className="text-sm text-muted-foreground">
              O formulário que você está procurando não existe ou foi removido.
            </p>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Voltar
          </Button>
          <div>
            <h1 className="text-3xl font-bold">{form.name}</h1>
            <p className="text-muted-foreground">{form.description || 'Sem descrição'}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleDuplicate}
            disabled={isDuplicating}
          >
            {isDuplicating ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Copy className="mr-2 h-4 w-4" />
            )}
            Duplicar
          </Button>
          <FullEditFormDialog form={form} onSuccess={() => window.location.reload()} />
          <Button
            variant="destructive"
            onClick={() => setShowDeleteDialog(true)}
            disabled={isDeleting}
          >
            {isDeleting ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Trash2 className="mr-2 h-4 w-4" />
            )}
            Deletar
          </Button>
        </div>
      </div>

      {/* Info Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant={form.is_active ? 'default' : 'secondary'}>
              {form.is_active ? 'Ativo' : 'Inativo'}
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Categoria
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{form.category}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Campos
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{form.fields?.length || 0}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Versão
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{form.version}</p>
          </CardContent>
        </Card>
      </div>

      {/* Fields List */}
      <Card>
        <CardHeader>
          <CardTitle>Campos do Formulário</CardTitle>
          <CardDescription>
            Lista de campos configurados neste formulário
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!form.fields || form.fields.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              Nenhum campo configurado
            </p>
          ) : (
            <div className="space-y-3">
              {form.fields.map((field: any, index: number) => (
                <Card key={field.id} className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-muted-foreground">
                          #{index + 1}
                        </span>
                        <h4 className="font-semibold">{field.label}</h4>
                        {field.required && (
                          <span className="text-red-500 text-xs">* Obrigatório</span>
                        )}
                        {field.ai_assist && (
                          <Badge variant="secondary" className="bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300">
                            <Sparkles className="h-3 w-3 mr-1" />
                            IA
                          </Badge>
                        )}
                      </div>
                      <div className="text-sm text-muted-foreground space-y-1">
                        <p>
                          <span className="font-medium">ID:</span>{' '}
                          <span className="font-mono">{field.id}</span>
                        </p>
                        <p>
                          <span className="font-medium">Tipo:</span> {field.type}
                        </p>
                        {field.help_text && (
                          <p>
                            <span className="font-medium">Ajuda:</span> {field.help_text}
                          </p>
                        )}
                        {field.placeholder && (
                          <p>
                            <span className="font-medium">Placeholder:</span> {field.placeholder}
                          </p>
                        )}
                        {field.ai_assist && field.ai_prompt_types && (
                          <div className="mt-2 p-2 bg-purple-50 dark:bg-purple-950/20 rounded">
                            <p className="font-medium text-purple-700 dark:text-purple-300 text-xs mb-1">
                              Assistências de IA:
                            </p>
                            <ul className="list-disc list-inside text-xs text-purple-600 dark:text-purple-400 space-y-0.5">
                              {field.ai_prompt_types.map((type: string, idx: number) => (
                                <li key={idx}>{type}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {field.options && field.options.length > 0 && (
                          <div className="mt-2">
                            <p className="font-medium text-xs mb-1">Opções:</p>
                            <ul className="list-disc list-inside text-xs ml-2 space-y-0.5">
                              {field.options.map((opt: any, idx: number) => (
                                <li key={idx}>
                                  {opt.label} <span className="text-muted-foreground">({opt.value})</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Metadata */}
      <Card>
        <CardHeader>
          <CardTitle>Informações</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>
            <span className="text-muted-foreground">Criado por:</span> {form.created_by_name || 'N/A'}
          </p>
          <p>
            <span className="text-muted-foreground">Criado em:</span>{' '}
            {new Date(form.created_at).toLocaleString('pt-BR')}
          </p>
          <p>
            <span className="text-muted-foreground">Atualizado em:</span>{' '}
            {new Date(form.updated_at).toLocaleString('pt-BR')}
          </p>
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirmar exclusão</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja deletar o formulário &quot;{form.name}&quot;? Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Deletar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
