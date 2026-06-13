'use client';

import { useState, useRef, useEffect } from 'react';
import { useTheme } from 'next-themes';
import { Editor } from '@tinymce/tinymce-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { AIInput } from '@/components/ui/ai-input';
import { AITextarea } from '@/components/ui/ai-textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Loader2, FileText, Link as LinkIcon,
  AlertCircle, CheckCircle, Eye, Info
} from 'lucide-react';
import { useTemplates } from '@/hooks/use-templates';
import { useForms } from '@/hooks/use-forms';
import { useBlueprints } from '@/hooks/use-blueprints';
import { useToast } from '@/hooks/use-toast';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Switch } from '@/components/ui/switch';
import { TemplatePreviewDialog } from './TemplatePreviewDialog';
import type { DocumentTemplate } from '@/types';

interface EditTemplateDialogProps {
  children: React.ReactNode;
  template: DocumentTemplate;
  onSuccess?: () => void;
}

export function EditTemplateDialog({ children, template, onSuccess }: EditTemplateDialogProps) {
  const [open, setOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('info');
  const [showPreview, setShowPreview] = useState(false);
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === 'dark';

  const { updateTemplate, isUpdating, useTemplate } = useTemplates();
  const { forms } = useForms(1);
  const { blueprints } = useBlueprints();
  const { toast } = useToast();
  const editorRef = useRef<any>(null);

  // Carrega detalhes completos do template
  const { data: fullTemplate, isLoading } = useTemplate(template.id, open);

  const [formData, setFormData] = useState({
    name: template.name,
    description: template.description || '',
    blueprint: template.blueprint || '',
    template_type: 'html',
    form_template: '',
    is_active: template.is_active,
  });

  const [editorContent, setEditorContent] = useState('');
  const [detectedPlaceholders, setDetectedPlaceholders] = useState<string[]>([]);
  const [compatibilityCheck, setCompatibilityCheck] = useState<any>(null);

  // Reset form quando template carrega
  useEffect(() => {
    if (open && fullTemplate) {
      setFormData({
        name: fullTemplate.name,
        description: fullTemplate.description || '',
        blueprint: fullTemplate.blueprint || '',
        template_type: 'html',
        form_template: fullTemplate.form_template || '',
        is_active: fullTemplate.is_active,
      });

      // Carrega conteúdo no editor
      const content = fullTemplate.rendered_content || fullTemplate.content || '';
      setEditorContent(content);

      // Detecta placeholders
      const placeholders = extractPlaceholders(content);
      setDetectedPlaceholders(placeholders);

      setActiveTab('info');
    }
  }, [open, fullTemplate]);

  const extractPlaceholders = (content: string): string[] => {
    const regex = /\{\{(\w+)\}\}/g;
    const matches = content.matchAll(regex);
    const placeholders = new Set<string>();
    for (const match of matches) {
      placeholders.add(match[1]);
    }
    return Array.from(placeholders);
  };

  const handleEditorChange = (content: string) => {
    setEditorContent(content);
    const placeholders = extractPlaceholders(content);
    setDetectedPlaceholders(placeholders);

    // Se houver formulário selecionado, revalidar compatibilidade
    if (formData.form_template) {
      checkCompatibility(placeholders);
    }
  };

  const checkCompatibility = (placeholders: string[]) => {
    const selectedForm = forms.find((f) => f.id === formData.form_template);
    if (!selectedForm) return;

    const formFieldIds = selectedForm.fields.map((f) => f.name);
    const placeholderSet = new Set(placeholders);
    const formFieldSet = new Set(formFieldIds);

    const missing = Array.from(placeholderSet).filter((p) => !formFieldSet.has(p));
    const extra = Array.from(formFieldSet).filter((f) => !placeholderSet.has(f));

    setCompatibilityCheck({
      compatible: missing.length === 0,
      missing_fields: missing,
      extra_fields: extra,
      match_count: placeholders.filter((p) => formFieldSet.has(p)).length,
    });
  };

  const handleFormTemplateChange = (value: string) => {
    setFormData({ ...formData, form_template: value });
    if (detectedPlaceholders.length > 0) {
      checkCompatibility(detectedPlaceholders);
    }
  };

  const handleSubmit = async () => {
    // Validações
    if (!formData.name.trim()) {
      toast({
        title: 'Nome obrigatório',
        description: 'Por favor, informe o nome do template.',
        variant: 'destructive',
      });
      setActiveTab('info');
      return;
    }

    if (!editorContent.trim()) {
      toast({
        title: 'Conteúdo obrigatório',
        description: 'Por favor, edite o conteúdo do template no editor.',
        variant: 'destructive',
      });
      setActiveTab('content');
      return;
    }

    if (detectedPlaceholders.length === 0) {
      toast({
        title: 'Nenhum placeholder detectado',
        description: 'Adicione pelo menos um placeholder no formato {{nome_campo}}',
        variant: 'destructive',
      });
      setActiveTab('content');
      return;
    }

    try {
      const payload = {
        ...formData,
        content: editorContent,
        blueprint: formData.blueprint || undefined,
        form_template: formData.form_template || undefined,
      };

      await updateTemplate(template.id, payload);

      toast({
        title: 'Template atualizado',
        description: `${formData.name} foi atualizado com sucesso!`,
      });

      setOpen(false);
      setActiveTab('info');
      onSuccess?.();
    } catch (error: any) {
      toast({
        title: 'Erro ao atualizar template',
        description: error.response?.data?.message || 'Ocorreu um erro ao atualizar o template.',
        variant: 'destructive',
      });
    }
  };

  const renderInfoTab = () => (
    <TabsContent value="info" className="space-y-4">
      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          Edite as informações básicas do template. O conteúdo pode ser editado na aba "Conteúdo".
        </AlertDescription>
      </Alert>

      <div className="space-y-4">
        <div>
          <Label htmlFor="name">Nome *</Label>
          <AIInput
            id="name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            setValue={(val) => setFormData({ ...formData, name: val })}
            placeholder="Ex: Petição Inicial Cível"
            aiContext="nome de template de documento jurídico de procuradoria"
            aiObjective="Sugira um nome claro e descritivo para o template"
          />
        </div>

        <div>
          <Label htmlFor="description">Descrição</Label>
          <AITextarea
            id="description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            setValue={(val) => setFormData({ ...formData, description: val })}
            placeholder="Descreva o propósito deste template..."
            rows={3}
            aiContext="descrição de template de documento jurídico de procuradoria"
            aiObjective="Descreva de forma clara o propósito e uso deste template"
          />
        </div>

        <div>
          <Label htmlFor="blueprint">Blueprint</Label>
          <Select value={formData.blueprint} onValueChange={(value) => setFormData({ ...formData, blueprint: value })}>
            <SelectTrigger>
              <SelectValue placeholder="Selecione o blueprint..." />
            </SelectTrigger>
            <SelectContent>
              {blueprints.map((bp) => (
                <SelectItem key={bp.id} value={bp.id}>
                  {bp.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center justify-between">
          <Label htmlFor="is_active">Template ativo</Label>
          <Switch
            id="is_active"
            checked={formData.is_active}
            onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
          />
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button variant="outline" onClick={() => setOpen(false)}>
          Cancelar
        </Button>
        <Button onClick={() => setActiveTab('content')}>
          Próximo: Conteúdo
        </Button>
      </div>
    </TabsContent>
  );

  const renderContentTab = () => (
    <TabsContent value="content" className="space-y-4">
      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          Edite o conteúdo do template. Você pode colar do Word, inserir imagens e adicionar placeholders no formato <code className="bg-slate-200 dark:bg-slate-800 px-1 rounded">{'{{nome_campo}}'}</code>
        </AlertDescription>
      </Alert>

      {isLoading ? (
        <div className="flex justify-center items-center py-12">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      ) : (
        <>
          <div>
            <Label>Conteúdo do Template *</Label>
            <div className="mt-2 border rounded-lg overflow-hidden">
              <Editor
                key={resolvedTheme}
                apiKey={process.env.NEXT_PUBLIC_TINYMCE_API_KEY}
                onInit={(_evt, editor) => (editorRef.current = editor)}
                value={editorContent}
                onEditorChange={handleEditorChange}
                init={{
                  license_key: 'gpl',
                  height: 500,
                  menubar: true,
                  skin_url: isDark ? '/tinymce/skins/ui/oxide-dark' : '/tinymce/skins/ui/oxide',
                  content_css: isDark ? '/tinymce/skins/content/dark/content.css' : '/tinymce/skins/content/default/content.css',
                  plugins: 'advlist autolink lists link image charmap preview anchor searchreplace visualblocks code fullscreen insertdatetime media table wordcount',
                  toolbar: 'undo redo | blocks fontfamily fontsize | bold italic underline strikethrough | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | forecolor backcolor | table image link | removeformat code fullscreen',
                  content_style: `body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 14px; background-color: ${isDark ? '#1a1a1a' : '#ffffff'}; color: ${isDark ? '#e0e0e0' : '#000000'}; }`,
                  images_upload_handler: (blobInfo: any) => {
                    return new Promise((resolve) => {
                      const base64 = 'data:' + blobInfo.blob().type + ';base64,' + blobInfo.base64();
                      resolve(base64);
                    });
                  },
                  file_picker_types: 'image',
                  automatic_uploads: true,
                }}
              />
            </div>
          </div>

          {/* Placeholders detectados */}
          {detectedPlaceholders.length > 0 && (
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertDescription>
                <p className="font-semibold mb-2">Placeholders detectados ({detectedPlaceholders.length}):</p>
                <div className="flex flex-wrap gap-2">
                  {detectedPlaceholders.map((placeholder) => (
                    <code key={placeholder} className="bg-slate-200 dark:bg-slate-800 px-2 py-1 rounded text-xs">
                      {`{{${placeholder}}}`}
                    </code>
                  ))}
                </div>
              </AlertDescription>
            </Alert>
          )}
        </>
      )}

      <div className="flex justify-between gap-2 pt-4">
        <Button variant="outline" onClick={() => setActiveTab('info')}>
          Voltar
        </Button>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancelar
          </Button>
          <Button onClick={() => setActiveTab('link')}>
            Próximo: Vincular Formulário
          </Button>
        </div>
      </div>
    </TabsContent>
  );

  const renderLinkTab = () => (
    <TabsContent value="link" className="space-y-4">
      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          Vincule este template a um formulário para validar compatibilidade de campos (opcional).
        </AlertDescription>
      </Alert>

      <div>
        <Label htmlFor="form_template">Formulário (Opcional)</Label>
        <Select value={formData.form_template || 'none'} onValueChange={v => handleFormTemplateChange(v === 'none' ? '' : v)}>
          <SelectTrigger>
            <SelectValue placeholder="Selecione um formulário..." />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="none">Nenhum</SelectItem>
            {forms.map((form) => (
              <SelectItem key={form.id} value={form.id}>
                {form.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Resultado da verificação de compatibilidade */}
      {compatibilityCheck && (
        <Alert variant={compatibilityCheck.compatible ? 'default' : 'destructive'}>
          {compatibilityCheck.compatible ? (
            <CheckCircle className="h-4 w-4" />
          ) : (
            <AlertCircle className="h-4 w-4" />
          )}
          <AlertDescription>
            {compatibilityCheck.compatible ? (
              <div>
                <p className="font-semibold text-green-700 dark:text-green-400">
                  ✓ Template compatível com o formulário
                </p>
                <p className="text-sm mt-1">
                  {compatibilityCheck.match_count} campo(s) encontrado(s) no formulário.
                </p>
              </div>
            ) : (
              <div>
                <p className="font-semibold">⚠ Template possui campos não encontrados no formulário</p>
                <div className="mt-2">
                  <p className="text-sm font-medium">Placeholders sem campo correspondente:</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {compatibilityCheck.missing_fields.map((field: string) => (
                      <code key={field} className="bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 px-2 py-0.5 rounded text-xs">
                        {field}
                      </code>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </AlertDescription>
        </Alert>
      )}

      <div className="flex justify-between gap-2 pt-4">
        <Button variant="outline" onClick={() => setActiveTab('content')}>
          Voltar
        </Button>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowPreview(true)}>
            <Eye className="mr-2 h-4 w-4" />
            Preview
          </Button>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancelar
          </Button>
          <Button onClick={handleSubmit} disabled={isUpdating}>
            {isUpdating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Salvando...
              </>
            ) : (
              'Salvar Alterações'
            )}
          </Button>
        </div>
      </div>
    </TabsContent>
  );

  return (
    <>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>{children}</DialogTrigger>
        <DialogContent
          className="max-w-5xl max-h-[90vh] overflow-y-auto"
          onInteractOutside={(e) => {
            // Previne fechar dialog quando interagir com TinyMCE
            const target = e.target as HTMLElement;
            if (target.closest('.tox-tinymce, .tox-tinymce-aux, .moxman-window, .tam-assetmanager-root')) {
              e.preventDefault();
            }
          }}
        >
          <DialogHeader>
            <DialogTitle>Editar Template</DialogTitle>
            <DialogDescription className="sr-only">Editar informações, conteúdo e vinculação do template</DialogDescription>
          </DialogHeader>

          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="info">
                <FileText className="mr-2 h-4 w-4" />
                Informações
              </TabsTrigger>
              <TabsTrigger value="content">
                <FileText className="mr-2 h-4 w-4" />
                Conteúdo
              </TabsTrigger>
              <TabsTrigger value="link">
                <LinkIcon className="mr-2 h-4 w-4" />
                Vincular Formulário
              </TabsTrigger>
            </TabsList>

            {renderInfoTab()}
            {renderContentTab()}
            {renderLinkTab()}
          </Tabs>
        </DialogContent>
      </Dialog>

      {/* Preview Dialog */}
      {fullTemplate && (
        <TemplatePreviewDialog
          template={fullTemplate}
          open={showPreview}
          onClose={() => setShowPreview(false)}
        />
      )}
    </>
  );
}
