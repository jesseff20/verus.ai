'use client';

import Link from 'next/link';
import { useForms } from '@/hooks/use-forms';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { FileEdit, Plus, Eye, Loader2, Sparkles, Edit, Trash2, FileJson, FileText, AlertTriangle } from 'lucide-react';
import { CreateFormDialog } from '@/components/forms/CreateFormDialog';
import { FullEditFormDialog } from '@/components/forms/FullEditFormDialog';
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

export default function FormsPage() {
  const { forms, count, isLoading, refetch, deleteForm, isDeleting } = useForms();
  const { toast } = useToast();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [formToDelete, setFormToDelete] = useState<any>(null);

  const handleDeleteClick = (form: any) => {
    setFormToDelete(form);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!formToDelete) return;

    try {
      await deleteForm(formToDelete.id);
      toast({
        title: 'Formulário deletado',
        description: `O formulário "${formToDelete.name}" foi removido com sucesso.`,
      });
      setDeleteDialogOpen(false);
      setFormToDelete(null);
      refetch();
    } catch (error: any) {
      toast({
        title: 'Erro ao deletar',
        description: error.response?.data?.detail || 'Não foi possível deletar o formulário.',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Formulários</h1>
          <p className="text-muted-foreground">
            Templates de formulários dinâmicos • {count} formulário{count !== 1 ? 's' : ''}
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/dashboard/forms/import">
            <Button variant="outline">
              <FileJson className="mr-2 h-4 w-4" />
              Importar JSON
            </Button>
          </Link>
          <CreateFormDialog
            trigger={
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Novo Formulário
              </Button>
            }
            onSuccess={() => refetch()}
          />
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      ) : forms.length === 0 ? (
        <Card className="p-12">
          <div className="flex flex-col items-center text-center gap-4">
            <FileEdit className="h-16 w-16 text-muted-foreground opacity-50" />
            <div>
              <h3 className="text-lg font-semibold mb-2">Nenhum formulário criado</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Crie seu primeiro formulário dinâmico com assistência de IA
              </p>
            </div>
            <CreateFormDialog
              trigger={
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Criar Primeiro Formulário
                </Button>
              }
              onSuccess={() => refetch()}
            />
          </div>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {forms.map((form) => (
            <Card key={form.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <FileEdit className="h-8 w-8 text-primary" />
                  <div className="flex gap-2 flex-wrap">
                    {form.is_active && <Badge>Ativo</Badge>}
                    {form.fields?.some((f: any) => f.ai_assist) && (
                      <Badge variant="secondary" className="bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300">
                        <Sparkles className="h-3 w-3 mr-1" />
                        IA
                      </Badge>
                    )}
                    {form.blueprint_name && (
                      <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                        <FileText className="h-3 w-3 mr-1" />
                        Blueprint
                      </Badge>
                    )}
                    {form.has_generator_warning && (
                      <Badge variant="destructive" className="bg-amber-100 text-amber-800 border-amber-300">
                        <AlertTriangle className="h-3 w-3 mr-1" />
                        Aviso
                      </Badge>
                    )}
                  </div>
                </div>
                <CardTitle className="mt-4">{form.name}</CardTitle>
                <CardDescription>{form.description || 'Sem descrição'}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <p>
                    <span className="text-muted-foreground">Campos:</span> {form.fields?.length || 0}
                  </p>
                  <p>
                    <span className="text-muted-foreground">Versão:</span> {form.version}
                  </p>
                  {form.blueprint_name && (
                    <p className="text-blue-600 dark:text-blue-400">
                      <FileText className="h-3 w-3 inline mr-1" />
                      Blueprint: {form.blueprint_name}
                    </p>
                  )}
                  {form.fields?.some((f: any) => f.ai_assist) && (
                    <p className="text-purple-600 dark:text-purple-400">
                      <Sparkles className="h-3 w-3 inline mr-1" />
                      {form.fields.filter((f: any) => f.ai_assist).length} campo{form.fields.filter((f: any) => f.ai_assist).length !== 1 ? 's' : ''} com IA
                    </p>
                  )}
                </div>

                {/* Aviso de gerador deletado */}
                {form.has_generator_warning && (
                  <Alert variant="destructive" className="mt-3 bg-amber-50 border-amber-300 text-amber-800">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription className="text-xs">
                      {form.generator_warning_message || 'Gerador de documento foi removido. Selecione um novo gerador.'}
                    </AlertDescription>
                  </Alert>
                )}
                <div className="flex gap-2 mt-4">
                  <Link href={`/dashboard/forms/${form.id}`} className="flex-1">
                    <Button variant="outline" className="w-full">
                      <Eye className="mr-2 h-4 w-4" />
                      Detalhes
                    </Button>
                  </Link>
                  <FullEditFormDialog form={form} onSuccess={refetch}>
                    <Button variant="ghost" size="icon">
                      <Edit className="h-4 w-4" />
                    </Button>
                  </FullEditFormDialog>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDeleteClick(form)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirmar exclusão</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja deletar o formulário &quot;{formToDelete?.name}&quot;? Esta ação não pode ser desfeita.
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
