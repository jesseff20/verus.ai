'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Eye, Loader2 } from 'lucide-react';
import { useTemplates } from '@/hooks/use-templates';
import type { DocumentTemplate } from '@/types';
import DOMPurify from 'isomorphic-dompurify';

interface ViewTemplateDialogProps {
  children: React.ReactNode;
  template: DocumentTemplate;
}

export function ViewTemplateDialog({ children, template }: ViewTemplateDialogProps) {
  const [open, setOpen] = useState(false);
  const { useTemplate } = useTemplates();
  // Só carrega os detalhes do template quando o dialog está aberto
  const { data: fullTemplate, isLoading } = useTemplate(template.id, open);

  const renderPreview = () => {
    if (!fullTemplate || !fullTemplate.rendered_content) {
      return (
        <div className="border border-dashed rounded-lg p-12 text-center text-muted-foreground">
          <Eye className="h-12 w-12 mx-auto mb-3 opacity-20" />
          <p>Sem conteúdo para visualizar</p>
        </div>
      );
    }

    return (
      <div className="border rounded-lg p-4 bg-white dark:bg-slate-900 overflow-auto max-h-[500px]">
        <style>{fullTemplate.custom_css}</style>
        <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(fullTemplate.rendered_content) }} />
      </div>
    );
  };

  const displayTemplate = fullTemplate || template;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogDescription className="sr-only">Visualizar conteúdo e detalhes do template</DialogDescription>
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <DialogTitle className="text-2xl mb-2">{displayTemplate.name}</DialogTitle>
              {displayTemplate.description && (
                <p className="text-sm text-muted-foreground">{displayTemplate.description}</p>
              )}
            </div>
            <div className="flex gap-2 flex-wrap">
              <Badge variant={displayTemplate.is_active ? 'default' : 'secondary'}>
                {displayTemplate.is_active ? 'Ativo' : 'Inativo'}
              </Badge>
              {displayTemplate.is_default && (
                <Badge variant="outline">Padrão</Badge>
              )}
            </div>
          </div>
        </DialogHeader>

        {isLoading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="space-y-4 py-4">
            {/* Info Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-slate-50 dark:bg-slate-900 rounded-lg">
              <div>
                <p className="text-xs text-muted-foreground">Blueprint</p>
                <p className="font-medium text-sm">{displayTemplate.blueprint_name || 'Não definido'}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Tipo</p>
                <p className="font-medium text-sm">{displayTemplate.template_type.toUpperCase()}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Versão</p>
                <p className="font-medium text-sm">v{displayTemplate.version}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Placeholders</p>
                <p className="font-medium text-sm">{displayTemplate.placeholder_count || 0}</p>
              </div>
            </div>

            {/* Preview */}
            <div className="space-y-3">
              <div>
                <h3 className="font-semibold mb-3">Preview do Template</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Visualização de como o template será renderizado.
                </p>
                {renderPreview()}
              </div>
            </div>

            {/* Metadata */}
            <div className="pt-4 border-t text-sm text-muted-foreground">
              <div className="grid grid-cols-2 gap-2">
                <p>
                  <span className="font-medium">Criado em:</span>{' '}
                  {new Date(displayTemplate.created_at).toLocaleDateString('pt-BR', {
                    day: '2-digit',
                    month: 'long',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
                <p>
                  <span className="font-medium">Atualizado em:</span>{' '}
                  {new Date(displayTemplate.updated_at).toLocaleDateString('pt-BR', {
                    day: '2-digit',
                    month: 'long',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
                {displayTemplate.created_by_name && (
                  <p>
                    <span className="font-medium">Criado por:</span> {displayTemplate.created_by_name}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
