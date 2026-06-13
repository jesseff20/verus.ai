'use client';

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Loader2, Eye, FileText, AlertCircle } from 'lucide-react';
import DOMPurify from 'isomorphic-dompurify';
import { useTemplates } from '@/hooks/use-templates';
import { useToast } from '@/hooks/use-toast';
import { Alert, AlertDescription } from '@/components/ui/alert';
import type { DocumentTemplate } from '@/types';

interface TemplatePreviewDialogProps {
  template: DocumentTemplate;
  open: boolean;
  onClose: () => void;
}

export function TemplatePreviewDialog({ template, open, onClose }: TemplatePreviewDialogProps) {
  const { previewTemplate, extractPlaceholders } = useTemplates();
  const { toast } = useToast();

  const [placeholders, setPlaceholders] = useState<string[]>([]);
  const [previewData, setPreviewData] = useState<Record<string, string>>({});
  const [renderedContent, setRenderedContent] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [loadingPlaceholders, setLoadingPlaceholders] = useState(true);

  // Carregar placeholders do template ao abrir
  useEffect(() => {
    if (open && template.id) {
      loadPlaceholders();
    }
  }, [open, template.id]);

  const loadPlaceholders = async () => {
    try {
      setLoadingPlaceholders(true);
      const result = await extractPlaceholders(template.id);
      setPlaceholders(result.placeholders || []);

      // Inicializar previewData com valores vazios
      const initialData: Record<string, string> = {};
      result.placeholders.forEach((ph: string) => {
        initialData[ph] = '';
      });
      setPreviewData(initialData);
    } catch (error) {
      console.error('Erro ao carregar placeholders:', error);
      toast({
        title: 'Erro ao carregar placeholders',
        description: 'Não foi possível extrair os placeholders do template.',
        variant: 'destructive',
      });
    } finally {
      setLoadingPlaceholders(false);
    }
  };

  const handleGeneratePreview = async () => {
    try {
      setIsGenerating(true);
      const result = await previewTemplate({
        id: template.id,
        data: previewData,
      });

      setRenderedContent(result.rendered_content);

      toast({
        title: 'Preview gerado!',
        description: 'O preview foi gerado com sucesso.',
      });
    } catch (error: any) {
      toast({
        title: 'Erro ao gerar preview',
        description: error.response?.data?.detail || 'Não foi possível gerar o preview.',
        variant: 'destructive',
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleClose = () => {
    setRenderedContent('');
    setPreviewData({});
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Preview do Template: {template.name}</DialogTitle>
          <DialogDescription className="sr-only">Preencher dados e visualizar preview do template</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {loadingPlaceholders ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              <span className="ml-3">Carregando placeholders...</span>
            </div>
          ) : (
            <>
              {/* Form Fields */}
              <div>
                <h3 className="font-semibold mb-3">Preencher Dados de Teste</h3>
                {placeholders.length === 0 ? (
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      Nenhum placeholder encontrado neste template.
                      Certifique-se de que o template contém placeholders no formato {`{{campo}}`}.
                    </AlertDescription>
                  </Alert>
                ) : (
                  <>
                    <p className="text-sm text-muted-foreground mb-4">
                      Preencha os campos abaixo para ver como o documento ficará com dados reais.
                      Campos vazios serão automaticamente removidos do documento.
                    </p>

                    <div className="grid grid-cols-2 gap-4 max-h-[300px] overflow-y-auto p-2 border rounded-lg">
                      {placeholders.map((placeholder) => {
                        // Determinar se é campo longo (textarea) baseado no nome
                        const longFieldKeywords = ['descricao', 'justificativa', 'observacao', 'texto', 'conteudo'];
                        const isLongField = longFieldKeywords.some(keyword =>
                          placeholder.toLowerCase().includes(keyword)
                        );

                        return (
                          <div key={placeholder} className={isLongField ? 'col-span-2' : ''}>
                            <Label className="text-xs font-medium">
                              {placeholder.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            </Label>
                            {isLongField ? (
                              <Textarea
                                value={previewData[placeholder] || ''}
                                onChange={(e) =>
                                  setPreviewData({ ...previewData, [placeholder]: e.target.value })
                                }
                                placeholder={`Digite ${placeholder.replace(/_/g, ' ')}`}
                                rows={3}
                                className="text-sm"
                              />
                            ) : (
                              <Input
                                value={previewData[placeholder] || ''}
                                onChange={(e) =>
                                  setPreviewData({ ...previewData, [placeholder]: e.target.value })
                                }
                                placeholder={`Digite ${placeholder.replace(/_/g, ' ')}`}
                                className="text-sm"
                              />
                            )}
                          </div>
                        );
                      })}
                    </div>

                    <div className="flex justify-end mt-4">
                      <Button onClick={handleGeneratePreview} disabled={isGenerating}>
                        {isGenerating ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Gerando Preview...
                          </>
                        ) : (
                          <>
                            <Eye className="mr-2 h-4 w-4" />
                            Gerar Preview
                          </>
                        )}
                      </Button>
                    </div>
                  </>
                )}
              </div>

              {/* Preview Result */}
              {renderedContent && (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold">Resultado do Preview</h3>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <FileText className="h-3 w-3" />
                      <span>{template.template_type.toUpperCase()}</span>
                    </div>
                  </div>

                  <Alert className="mb-3">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      <strong>Note:</strong> Linhas com campos vazios foram automaticamente removidas do documento.
                      Este é o comportamento da renderização inteligente!
                    </AlertDescription>
                  </Alert>

                  <div className="border rounded-lg p-6 bg-white dark:bg-slate-900 max-h-[500px] overflow-y-auto">
                    {template.template_type === 'html' || template.template_type === 'tinymce' ? (
                      <div
                        dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(renderedContent) }}
                        className="prose prose-sm dark:prose-invert max-w-none"
                      />
                    ) : (
                      <pre className="whitespace-pre-wrap text-sm font-mono">
                        {renderedContent}
                      </pre>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end pt-4 border-t">
          <Button variant="outline" onClick={handleClose}>
            Fechar
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
