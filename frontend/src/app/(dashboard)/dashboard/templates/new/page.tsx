'use client';

import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useTheme } from 'next-themes';
import { Editor } from '@tinymce/tinymce-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, ArrowLeft, CheckCircle, Info } from 'lucide-react';
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';
import { useTemplates } from '@/hooks/use-templates';
import { useBlueprints } from '@/hooks/use-blueprints';
import { useToast } from '@/hooks/use-toast';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Switch } from '@/components/ui/switch';

export default function NewTemplatePage() {
  const router = useRouter();
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === 'dark';
  const { createTemplate, isCreating } = useTemplates();
  const { blueprints } = useBlueprints();
  const { toast } = useToast();
  const editorRef = useRef<any>(null);

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    blueprint: '',
    template_type: 'html',
    is_active: true,
  });

  const [editorContent, setEditorContent] = useState('');
  const [detectedPlaceholders, setDetectedPlaceholders] = useState<string[]>([]);

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
  };

  const handleSubmit = async () => {
    if (!formData.name.trim()) {
      toast({
        title: 'Nome obrigatório',
        description: 'Por favor, informe o nome do template.',
        variant: 'destructive',
      });
      return;
    }

    if (!editorContent.trim()) {
      toast({
        title: 'Conteúdo obrigatório',
        description: 'Por favor, crie o conteúdo do template no editor.',
        variant: 'destructive',
      });
      return;
    }

    if (detectedPlaceholders.length === 0) {
      toast({
        title: 'Nenhum placeholder detectado',
        description: 'Adicione pelo menos um placeholder no formato {{nome_campo}}',
        variant: 'destructive',
      });
      return;
    }

    try {
      const payload = {
        ...formData,
        content: editorContent,
        blueprint: formData.blueprint || undefined,
      };

      await createTemplate(payload);

      toast({
        title: 'Template criado',
        description: `${formData.name} foi criado com sucesso!`,
      });

      router.push('/dashboard/templates');
    } catch (error: any) {
      toast({
        title: 'Erro ao criar template',
        description: error.response?.data?.message || 'Ocorreu um erro ao criar o template.',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="outline" size="icon" onClick={() => router.push('/dashboard/templates')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Criar Novo Template</h1>
          <p className="text-muted-foreground">
            Crie um template de documento com editor visual
          </p>
        </div>
      </div>

      {/* Form */}
      <Card>
        <CardHeader>
          <CardTitle>Informações do Template</CardTitle>
          <CardDescription>Configure os dados e conteúdo do template</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Informações Básicas */}
          <div className="space-y-4">
            <h3 className="font-semibold text-lg">Informações Básicas</h3>
            <div className="space-y-4">
              <div>
                <Label htmlFor="name">Nome *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Ex: Petição Inicial Cível"
                />
              </div>

              <div>
                <Label htmlFor="description">Descrição</Label>
                <div className="relative">
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Descreva o propósito deste template..."
                    rows={3}
                    className="pr-32"
                  />
                  <div className="absolute top-1 right-1">
                    <AIEnhanceButton
                      value={formData.description}
                      onEnhance={(text) => setFormData({ ...formData, description: text })}
                      context="descrição de template de documento jurídico"
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
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

                <div className="flex items-center justify-between pt-6">
                  <Label htmlFor="is_active">Template ativo</Label>
                  <Switch
                    id="is_active"
                    checked={formData.is_active}
                    onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Conteúdo */}
          <div className="space-y-4">
            <h3 className="font-semibold text-lg">Conteúdo do Template</h3>
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                Use o editor abaixo para criar o conteúdo do template. Você pode colar do Word, inserir imagens e adicionar placeholders no formato <code className="bg-slate-200 dark:bg-slate-800 px-1 rounded">{'{{nome_campo}}'}</code>
              </AlertDescription>
            </Alert>

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
                    height: 600,
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
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button variant="outline" onClick={() => router.push('/dashboard/templates')}>
              Cancelar
            </Button>
            <Button onClick={handleSubmit} disabled={isCreating}>
              {isCreating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Criando...
                </>
              ) : (
                'Criar Template'
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
