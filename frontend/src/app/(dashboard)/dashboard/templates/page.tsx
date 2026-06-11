'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useTemplates } from '@/hooks/use-templates';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { LayoutTemplate, Plus, Loader2, FileCode, Code, Calendar, Copy, Trash2, Edit, Eye } from 'lucide-react';
import { ViewTemplateDialog } from '@/components/templates/ViewTemplateDialog';
import { useToast } from '@/hooks/use-toast';

export default function TemplatesPage() {
  const { templates, count, isLoading, refetch, duplicateTemplate, deleteTemplate } = useTemplates();
  const { toast } = useToast();
  const [duplicating, setDuplicating] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const handleDuplicate = async (id: string, name: string) => {
    setDuplicating(id);
    try {
      await duplicateTemplate({ id, name: `${name} (Cópia)` });
      toast({
        title: 'Template duplicado!',
        description: 'O template foi duplicado com sucesso.',
      });
      refetch();
    } catch (error: any) {
      toast({
        title: 'Erro ao duplicar template',
        description: error.response?.data?.detail || 'Ocorreu um erro.',
        variant: 'destructive',
      });
    } finally {
      setDuplicating(null);
    }
  };

  const handleDelete = async (id: string) => {
    setDeleting(id);
    setConfirmDeleteId(null);
    try {
      await deleteTemplate(id);
      toast({
        title: 'Template excluído!',
        description: 'O template foi removido com sucesso.',
      });
      refetch();
    } catch (error: any) {
      toast({
        title: 'Erro ao excluir template',
        description: error.response?.data?.detail || 'Ocorreu um erro.',
        variant: 'destructive',
      });
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Templates de Documentos</h1>
          <p className="text-muted-foreground">
            Gerencie templates para geração de Documents e outros documentos
          </p>
        </div>
        <Link href="/dashboard/templates/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Novo Template
          </Button>
        </Link>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : templates.length === 0 ? (
        <div className="text-center py-12">
          <LayoutTemplate className="mx-auto h-12 w-12 text-muted-foreground opacity-50" />
          <h3 className="mt-4 text-lg font-semibold">Nenhum template encontrado</h3>
          <p className="text-muted-foreground mt-2">
            Comece criando seu primeiro template de documento
          </p>
          <Link href="/dashboard/templates/new">
            <Button className="mt-4">
              <Plus className="mr-2 h-4 w-4" />
              Criar Primeiro Template
            </Button>
          </Link>
        </div>
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {templates.map((template) => (
              <Card key={template.id} className="hover:shadow-lg transition-shadow">
                <ViewTemplateDialog template={template}>
                  <CardHeader className="cursor-pointer hover:bg-accent/50 transition-colors">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <LayoutTemplate className="h-5 w-5 text-primary shrink-0" />
                        <CardTitle className="text-lg truncate">{template.name}</CardTitle>
                      </div>
                      <div className="flex gap-1 shrink-0 flex-wrap">
                        <Badge variant={template.is_active ? 'default' : 'secondary'} className="text-xs">
                          {template.is_active ? 'Ativo' : 'Inativo'}
                        </Badge>
                        {template.is_default && (
                          <Badge variant="outline" className="text-xs">
                            Padrão
                          </Badge>
                        )}
                      </div>
                    </div>
                    {template.description && (
                      <CardDescription className="line-clamp-2">{template.description}</CardDescription>
                    )}
                  </CardHeader>
                </ViewTemplateDialog>
                <CardContent className="space-y-4">
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <FileCode className="h-4 w-4" />
                      <span>
                        {template.template_type.toUpperCase()} • {template.blueprint_name || 'Sem blueprint'}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Code className="h-4 w-4" />
                      <span>
                        Versão {template.version}
                        {template.placeholder_count !== undefined && ` • ${template.placeholder_count} placeholders`}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Calendar className="h-4 w-4" />
                      <span>{new Date(template.created_at).toLocaleDateString('pt-BR')}</span>
                    </div>
                    {template.custom_css && (
                      <div className="flex items-center gap-2 text-xs text-purple-600 dark:text-purple-400">
                        <FileCode className="h-3 w-3" />
                        CSS Customizado
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2 pt-2 border-t">
                    <ViewTemplateDialog template={template}>
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                      >
                        <Eye className="mr-1 h-3 w-3" />
                        Ver
                      </Button>
                    </ViewTemplateDialog>
                    <Link href={`/dashboard/templates/${template.id}/edit`}>
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                      >
                        <Edit className="mr-1 h-3 w-3" />
                        Editar
                      </Button>
                    </Link>
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => handleDuplicate(template.id, template.name)}
                      disabled={duplicating === template.id}
                    >
                      {duplicating === template.id ? (
                        <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                      ) : (
                        <Copy className="mr-1 h-3 w-3" />
                      )}
                      Duplicar
                    </Button>
                    {confirmDeleteId === template.id ? (
                      <div className="flex items-center gap-1">
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleDelete(template.id)}
                          disabled={deleting === template.id}
                        >
                          {deleting === template.id ? <Loader2 className="h-3 w-3 animate-spin" /> : 'Sim'}
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setConfirmDeleteId(null)}
                        >
                          Não
                        </Button>
                      </div>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setConfirmDeleteId(template.id)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950"
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {templates.length > 0 && (
            <div className="text-center pt-4 text-sm text-muted-foreground">
              Total: {count} template{count !== 1 ? 's' : ''}
            </div>
          )}
        </>
      )}
    </div>
  );
}
