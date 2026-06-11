'use client';

import { useState, useRef, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { Editor } from '@tinymce/tinymce-react';
import { useDocuments } from '@/hooks/use-documents';
import { useForms } from '@/hooks/use-forms';
import { useTemplates } from '@/hooks/use-templates';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
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
import { ArrowLeft, Loader2, Save, FileText, Trash2, Copy, Download, Wand2, FileType, Sparkles, CheckCircle, AlertCircle } from 'lucide-react';
import { DynamicForm } from '@/components/documents/DynamicForm';
import { PermissionGuard } from '@/components/auth/permission-guard';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useMutation } from '@tanstack/react-query';
import api from '@/lib/api';

const statusLabels: Record<string, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
  rascunho: { label: 'Rascunho', variant: 'outline' },
  em_analise: { label: 'Em Análise', variant: 'secondary' },
  aprovado: { label: 'Aprovado', variant: 'default' },
  rejeitado: { label: 'Rejeitado', variant: 'destructive' },
  finalizado: { label: 'Finalizado', variant: 'default' },
};

export default function DocumentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const documentId = params.id as string;
  const { toast } = useToast();

  const { useDocument, updateDocument, generateDocument, createVersion, deleteDocument, isUpdating, isGenerating, isDeleting } = useDocuments();
  const { data: documentData, isLoading: documentLoading, error: documentError } = useDocument(documentId);
  const { useForm } = useForms();
  const { data: formTemplate, isLoading: formLoading } = useForm(documentData?.form_template || '', !!documentData?.form_template);
  const { useTemplatesByBlueprint } = useTemplates();
  const { data: documentTemplates, isLoading: templatesLoading } = useTemplatesByBlueprint(
    formTemplate?.blueprint || '',
    !!formTemplate?.blueprint
  );

  const editorRef = useRef<any>(null);

  // Função para extrair apenas o conteúdo do <body> de um HTML completo
  const extractBodyContent = (html: string): string => {
    if (!html) return '';

    // Tenta extrair conteúdo entre <body> e </body>
    const bodyMatch = html.match(/<body[^>]*>([\s\S]*)<\/body>/i);
    if (bodyMatch && bodyMatch[1]) {
      return bodyMatch[1].trim();
    }

    // Se não encontrar body, retorna o HTML original (pode ser apenas conteúdo)
    return html;
  };

  const [activeTab, setActiveTab] = useState('dados');
  const [formData, setFormData] = useState<Record<string, any>>(documentData?.data || {});
  const [basicInfo, setBasicInfo] = useState({
    title: documentData?.title || '',
    numero_processo: documentData?.numero_processo || '',
    document_template: documentData?.document_template || '',
  });
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [editorContent, setEditorContent] = useState('');
  const [hasUnsavedEdits, setHasUnsavedEdits] = useState(false);

  // Copilot review states
  const [showReviewDialog, setShowReviewDialog] = useState(false);
  const [reviewResult, setReviewResult] = useState<any>(null);
  const [isReviewing, setIsReviewing] = useState(false);

  const handleSaveData = async () => {
    try {
      await updateDocument({
        id: documentId,
        data: {
          data: formData,
          title: basicInfo.title,
          numero_processo: basicInfo.numero_processo,
          document_template: basicInfo.document_template || undefined,
        },
      });

      toast({
        title: "Dados salvos",
        description: "As alterações foram salvas com sucesso.",
      });
    } catch (error: any) {
      toast({
        title: "Erro ao salvar",
        description: error.response?.data?.detail || "Ocorreu um erro ao salvar os dados.",
        variant: "destructive",
      });
    }
  };

  const handleGenerate = async () => {
    // Mostrar mensagem de que está processando
    toast({
      title: "Gerando documento...",
      description: "A IA está processando. Isso pode levar até 2 minutos. Aguarde...",
    });

    try {
      await generateDocument(documentId);

      toast({
        title: "Documento gerado!",
        description: "O documento foi gerado com sucesso pela IA.",
      });
    } catch (error: any) {
      console.error('Erro ao gerar documento:', error);

      // Verificar se foi timeout
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        toast({
          title: "Tempo esgotado",
          description: "A geração demorou muito. Tente novamente ou reduza o tamanho do documento.",
          variant: "destructive",
        });
        return;
      }

      const errorMessage = error.response?.data?.error || error.response?.data?.detail || "Ocorreu um erro ao gerar o documento.";
      toast({
        title: "Erro ao gerar documento",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };

  const handleCreateVersion = async () => {
    try {
      const newDocument = await createVersion(documentId);

      toast({
        title: "Nova versão criada",
        description: `Versão ${newDocument.version} criada com sucesso.`,
      });

      router.push(`/dashboard/documents/${newDocument.id}`);
    } catch (error: any) {
      toast({
        title: "Erro ao criar versão",
        description: error.response?.data?.detail || "Ocorreu um erro ao criar nova versão.",
        variant: "destructive",
      });
    }
  };

  const handleDelete = async () => {
    try {
      await deleteDocument(documentId);

      toast({
        title: "Documento excluído",
        description: "O documento foi excluído com sucesso.",
      });

      router.push('/dashboard/documents');
    } catch (error: any) {
      toast({
        title: "Erro ao excluir",
        description: error.response?.data?.detail || "Ocorreu um erro ao excluir o documento.",
        variant: "destructive",
      });
    }
  };

  const handleDownloadDocx = async () => {
    try {
      toast({
        title: 'Gerando DOCX...',
        description: 'Aguarde enquanto o arquivo é gerado.',
      });

      const baseUrl = (/^https?:\/\//.test(process.env.NEXT_PUBLIC_API_URL || '')) ? process.env.NEXT_PUBLIC_API_URL! : '';
      const response = await fetch(`${baseUrl}/api/v1/documents/items/${documentId}/export_docx/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Erro ao gerar DOCX: ${response.status} ${response.statusText}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = window.document.createElement('a');
      a.href = url;
      a.download = `${documentData?.title || 'documento'}.docx`;
      window.document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      window.document.body.removeChild(a);

      toast({
        title: 'DOCX gerado',
        description: 'O download do arquivo Word foi iniciado.',
      });
    } catch (error: any) {
      toast({
        title: 'Erro ao gerar DOCX',
        description: error.message || 'Ocorreu um erro ao gerar o arquivo Word.',
        variant: 'destructive',
      });
    }
  };

  const handleSaveEdits = async () => {
    try {
      const htmlContent = editorRef.current?.getContent() || editorContent;

      await updateDocument({
        id: documentId,
        data: {
          generated_html: htmlContent,
        },
      });

      setHasUnsavedEdits(false);

      toast({
        title: "Edições salvas",
        description: "As alterações no documento foram salvas com sucesso.",
      });
    } catch (error: any) {
      toast({
        title: "Erro ao salvar edições",
        description: error.response?.data?.detail || "Ocorreu um erro ao salvar as edições.",
        variant: "destructive",
      });
    }
  };

  const handleDownloadPDF = async () => {
    try {
      toast({
        title: "Gerando PDF...",
        description: "Aguarde enquanto o PDF é gerado.",
      });

      const baseUrl = (/^https?:\/\//.test(process.env.NEXT_PUBLIC_API_URL || '')) ? process.env.NEXT_PUBLIC_API_URL! : '';
      const response = await fetch(`${baseUrl}/api/v1/documents/items/${documentId}/export_pdf/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Erro ao gerar PDF: ${response.status} ${response.statusText} — ${errorText}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = window.document.createElement('a');
      a.href = url;
      a.download = `${documentData?.title || 'documento'}.pdf`;
      window.document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      window.document.body.removeChild(a);

      toast({
        title: "PDF gerado",
        description: "O download do PDF foi iniciado.",
      });
    } catch (error: any) {
      toast({
        title: "Erro ao gerar PDF",
        description: error.message || "Ocorreu um erro ao gerar o PDF.",
        variant: "destructive",
      });
    }
  };

  // Copilot: Revisar documento com IA
  const reviewDocumentMutation = useMutation({
    mutationFn: async (data: { content: string; doc_type: string }) => {
      const res = await api.post('/api/v1/processos/copilot/revisar-documento/', data);
      return res.data;
    },
    onSuccess: (data) => {
      setReviewResult(data);
      setShowReviewDialog(true);
      if (data.score >= 80) {
        toast({
          title: 'Revisão concluída',
          description: `Documento com qualidade ${data.score}% - Excelente!`,
        });
      } else if (data.score >= 60) {
        toast({
          title: 'Revisão concluída',
          description: `Documento com qualidade ${data.score}% - Algumas melhorias sugeridas.`,
        });
      } else {
        toast({
          title: 'Revisão concluída',
          description: `Documento com qualidade ${data.score}% - Melhorias recomendadas.`,
          variant: 'destructive',
        });
      }
    },
    onError: () => {
      toast({
        title: 'Erro na revisão',
        description: 'Não foi possível revisar o documento com IA.',
        variant: 'destructive',
      });
    },
  });

  const handleReviewDocument = () => {
    const content = editorRef.current?.getContent() || editorContent;
    if (!content) {
      toast({
        title: 'Documento vazio',
        description: 'Gere o documento antes de revisar.',
        variant: 'destructive',
      });
      return;
    }

    setIsReviewing(true);
    reviewDocumentMutation.mutate(
      {
        content: content,
        doc_type: 'peticao_inicial',
      },
      {
        onSettled: () => setIsReviewing(false),
      }
    );
  };

  // Update form data when document loads
  useEffect(() => {
    if (documentData?.data && Object.keys(formData).length === 0) {
      setFormData(documentData.data);
    }
  }, [documentData?.data]);

  // Update basicInfo when document loads
  useEffect(() => {
    if (documentData) {
      setBasicInfo({
        title: documentData.title || '',
        numero_processo: documentData.numero_processo || '',
        document_template: documentData.document_template || '',
      });
    }
  }, [documentData?.id]);

  // Update editor content when document loads or changes
  useEffect(() => {
    if (documentData?.generated_html) {
      const bodyContent = extractBodyContent(documentData.generated_html);
      if (editorContent !== bodyContent) {
        setEditorContent(bodyContent);
        setHasUnsavedEdits(false);
      }
    }
  }, [documentData?.generated_html]);

  if (documentLoading || formLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (documentError || !documentData) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href="/dashboard/documents">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Voltar
            </Button>
          </Link>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center text-muted-foreground py-8">
              Documento não encontrado.
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <PermissionGuard anyPermission={['documents.edit_own', 'documents.edit_all']} redirectOnDeny redirectTo="/dashboard/documents">
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/dashboard/documents">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Voltar
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{documentData.title}</h1>
            <p className="text-muted-foreground">
              {documentData.numero_processo && `Processo: ${documentData.numero_processo} • `}
              Versão {documentData.version}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={statusLabels[documentData.status]?.variant || 'outline'}>
            {statusLabels[documentData.status]?.label || documentData.status}
          </Badge>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="dados">Dados</TabsTrigger>
          <TabsTrigger value="documento">Documento</TabsTrigger>
          <TabsTrigger value="info">Info</TabsTrigger>
        </TabsList>

        {/* TAB: Dados */}
        <TabsContent value="dados" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Informações Básicas</CardTitle>
              <CardDescription>
                Edite as informações básicas do documento
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="title">Título</Label>
                <Input
                  id="title"
                  value={basicInfo.title}
                  onChange={(e) => setBasicInfo({ ...basicInfo, title: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="numero_processo">Número do Processo</Label>
                <Input
                  id="numero_processo"
                  placeholder="Ex: 2024/001"
                  value={basicInfo.numero_processo}
                  onChange={(e) => setBasicInfo({ ...basicInfo, numero_processo: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="document_template">
                  Template de Documento {documentTemplates && documentTemplates.length > 0 && <span className="text-red-500">*</span>}
                </Label>
                {templatesLoading ? (
                  <div className="flex items-center gap-2 py-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm text-muted-foreground">Carregando templates...</span>
                  </div>
                ) : documentTemplates && documentTemplates.length > 0 ? (
                  <>
                    <Select
                      value={basicInfo.document_template}
                      onValueChange={(value) => setBasicInfo({ ...basicInfo, document_template: value })}
                    >
                      <SelectTrigger id="document_template">
                        <SelectValue placeholder="Selecione um template de documento" />
                      </SelectTrigger>
                      <SelectContent>
                        {documentTemplates.map((template) => (
                          <SelectItem key={template.id} value={template.id}>
                            {template.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground">
                      Template usado para gerar o documento final
                    </p>
                  </>
                ) : (
                  <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                    <p className="text-sm text-yellow-800">
                      ⚠️ Nenhum template de documento associado a este formulário.
                      Configure um template no admin para poder gerar documentos.
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Campos do Formulário</CardTitle>
              <CardDescription>
                {formTemplate?.name || 'Carregando template...'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {formTemplate ? (
                <>
                  <DynamicForm
                    fields={formTemplate.fields}
                    sections={formTemplate.sections}
                    data={formData}
                    onChange={setFormData}
                    documentTitle={documentData.title}
                    blueprintAgents={formTemplate.blueprint_agents}
                  />

                  <div className="flex gap-2 pt-4 border-t">
                    <Button onClick={handleSaveData} disabled={isUpdating}>
                      {isUpdating ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Salvando...
                        </>
                      ) : (
                        <>
                          <Save className="mr-2 h-4 w-4" />
                          Salvar Alterações
                        </>
                      )}
                    </Button>
                  </div>
                </>
              ) : (
                <div className="text-center text-muted-foreground py-8">
                  <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" />
                  Carregando formulário...
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* TAB: Documento */}
        <TabsContent value="documento" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Documento Gerado</CardTitle>
              <CardDescription>
                Gere e visualize o documento final
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {!documentData.generated_html ? (
                <div className="text-center py-12">
                  <FileText className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-2">Documento não gerado</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Clique no botão abaixo para gerar o documento a partir dos dados preenchidos.
                  </p>
                  <Button onClick={handleGenerate} disabled={isGenerating}>
                    {isGenerating ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Gerando...
                      </>
                    ) : (
                      <>
                        <Wand2 className="mr-2 h-4 w-4" />
                        Gerar Documento
                      </>
                    )}
                  </Button>
                </div>
              ) : (
                <>
                  <div className="flex gap-2 mb-4">
                    <Button onClick={handleGenerate} disabled={isGenerating} size="sm">
                      {isGenerating ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Regenerando...
                        </>
                      ) : (
                        <>
                          <Wand2 className="mr-2 h-4 w-4" />
                          Regenerar
                        </>
                      )}
                    </Button>

                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={handleReviewDocument}
                      disabled={isReviewing || reviewDocumentMutation.isPending}
                    >
                      {isReviewing || reviewDocumentMutation.isPending ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Revisindo...
                        </>
                      ) : (
                        <>
                          <Sparkles className="mr-2 h-4 w-4" />
                          Revisir com IA
                        </>
                      )}
                    </Button>

                    {hasUnsavedEdits && (
                      <Button onClick={handleSaveEdits} disabled={isUpdating} size="sm" variant="default">
                        {isUpdating ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Salvando...
                          </>
                        ) : (
                          <>
                            <Save className="mr-2 h-4 w-4" />
                            Salvar Edições
                          </>
                        )}
                      </Button>
                    )}

                    <Button variant="outline" size="sm" onClick={handleDownloadPDF}>
                      <Download className="mr-2 h-4 w-4" />
                      Baixar PDF
                    </Button>
                    <Button variant="outline" size="sm" onClick={handleDownloadDocx}>
                      <FileType className="mr-2 h-4 w-4" />
                      Baixar DOCX
                    </Button>
                  </div>

                  <div className="border rounded-lg bg-white">
                    <Editor
                      apiKey={process.env.NEXT_PUBLIC_TINYMCE_API_KEY}
                      onInit={(_evt: any, editor: any) => (editorRef.current = editor)}
                      value={editorContent}
                      onEditorChange={(content) => {
                        setEditorContent(content);
                        setHasUnsavedEdits(true);
                      }}
                      init={{
                  license_key: 'gpl',
                        height: 600,
                        menubar: true,
                        plugins: 'advlist autolink lists link image charmap preview anchor searchreplace visualblocks code fullscreen insertdatetime media table wordcount',
                        toolbar: 'undo redo | blocks fontfamily fontsize | bold italic underline strikethrough | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | forecolor backcolor | table image link | removeformat code fullscreen',
                        content_style: 'body { font-family: Calibri, Arial, sans-serif; font-size: 11pt; padding: 40px; }',
                        language: 'pt_BR',
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
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* TAB: Info */}
        <TabsContent value="info" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Metadados</CardTitle>
              <CardDescription>
                Informações sobre o documento
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-muted-foreground">Status</Label>
                  <div className="mt-1">
                    <Badge variant={statusLabels[documentData.status]?.variant || 'outline'}>
                      {statusLabels[documentData.status]?.label || documentData.status}
                    </Badge>
                  </div>
                </div>

                <div>
                  <Label className="text-muted-foreground">Versão</Label>
                  <p className="mt-1">v{documentData.version}</p>
                </div>

                <div>
                  <Label className="text-muted-foreground">Progresso</Label>
                  <p className="mt-1">{documentData.progress}%</p>
                </div>

                <div>
                  <Label className="text-muted-foreground">Criado em</Label>
                  <p className="mt-1">
                    {new Date(documentData.created_at).toLocaleDateString('pt-BR', {
                      day: '2-digit',
                      month: '2-digit',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>

                <div>
                  <Label className="text-muted-foreground">Atualizado em</Label>
                  <p className="mt-1">
                    {new Date(documentData.updated_at).toLocaleDateString('pt-BR', {
                      day: '2-digit',
                      month: '2-digit',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>

                {documentData.completed_at && (
                  <div>
                    <Label className="text-muted-foreground">Completado em</Label>
                    <p className="mt-1">
                      {new Date(documentData.completed_at).toLocaleDateString('pt-BR', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Ações</CardTitle>
              <CardDescription>
                Ações disponíveis para este documento
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" className="w-full justify-start" onClick={handleCreateVersion}>
                <Copy className="mr-2 h-4 w-4" />
                Criar Nova Versão
              </Button>

              <Button
                variant="destructive"
                className="w-full justify-start"
                onClick={() => setShowDeleteDialog(true)}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Excluir Documento
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Tem certeza?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta ação não pode ser desfeita. O documento será permanentemente excluído.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} disabled={isDeleting}>
              {isDeleting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Excluindo...
                </>
              ) : (
                'Excluir'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Dialog: Revisão com IA */}
      <Dialog open={showReviewDialog} onOpenChange={setShowReviewDialog}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-purple-500" />
                Revisão de Documento com IA
              </div>
            </DialogTitle>
            <DialogDescription>
              Análise de qualidade e sugestões de melhoria
            </DialogDescription>
          </DialogHeader>

          {reviewResult && (
            <div className="space-y-4 max-h-[60vh] overflow-auto">
              {/* Score */}
              <div className="flex items-center gap-4 p-4 rounded-lg bg-muted">
                <div className="text-center">
                  <div className={`text-3xl font-bold ${
                    reviewResult.score >= 80 ? 'text-green-600' :
                    reviewResult.score >= 60 ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {reviewResult.score}%
                  </div>
                  <div className="text-xs text-muted-foreground">Qualidade</div>
                </div>
                {reviewResult.total_issues > 0 ? (
                  <div className="flex items-center gap-2 text-yellow-600">
                    <AlertCircle className="h-5 w-5" />
                    <span>{reviewResult.total_issues} problema(s) encontrado(s)</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-green-600">
                    <CheckCircle className="h-5 w-5" />
                    <span>Nenhum problema encontrado</span>
                  </div>
                )}
              </div>

              {/* Issues */}
              {reviewResult.issues && reviewResult.issues.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-semibold">Problemas Encontrados:</h4>
                  {reviewResult.issues.map((issue: any, idx: number) => (
                    <Card key={idx} className={
                      issue.severity === 'alta' ? 'border-red-300 bg-red-50' :
                      issue.severity === 'media' ? 'border-yellow-300 bg-yellow-50' :
                      'border-blue-300 bg-blue-50'
                    }>
                      <CardContent className="pt-4">
                        <div className="flex items-start gap-2">
                          <Badge
                            variant={
                              issue.severity === 'alta' ? 'destructive' :
                              issue.severity === 'media' ? 'secondary' : 'outline'
                            }
                            className="text-xs"
                          >
                            {issue.type}
                          </Badge>
                          <div className="flex-1">
                            <p className="text-sm font-medium">{issue.description}</p>
                            {issue.location && (
                              <p className="text-xs text-muted-foreground">
                                Localização: {issue.location}
                              </p>
                            )}
                            {issue.suggestion && (
                              <p className="text-xs text-green-700 mt-1">
                                Sugestão: {issue.suggestion}
                              </p>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}

              {/* Suggestions */}
              {reviewResult.suggestions && reviewResult.suggestions.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-semibold">Sugestões de Melhoria:</h4>
                  <ul className="list-disc list-inside text-sm space-y-1 text-muted-foreground">
                    {reviewResult.suggestions.map((suggestion: string, idx: number) => (
                      <li key={idx}>{suggestion}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Revised content */}
              {reviewResult.revised_content && (
                <div className="space-y-2">
                  <h4 className="font-semibold">Versão Revisada:</h4>
                  <div className="border rounded-md p-4 max-h-48 overflow-auto bg-muted text-sm whitespace-pre-wrap">
                    {reviewResult.revised_content}
                  </div>
                </div>
              )}
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowReviewDialog(false)}>
              Fechar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
    </PermissionGuard>
  );
}
