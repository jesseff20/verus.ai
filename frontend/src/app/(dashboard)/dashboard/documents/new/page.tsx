'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useDocuments } from '@/hooks/use-documents';
import { useForms } from '@/hooks/use-forms';
import { useTemplates } from '@/hooks/use-templates';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Loader2, Save, FileText, Wand2, Sparkles, X } from 'lucide-react';
import { DynamicForm } from '@/components/documents/DynamicForm';
import api from '@/lib/api';
import { useMutation } from '@tanstack/react-query';

export default function NewDocumentPage() {
  const router = useRouter();
  const { createDocument, isCreating } = useDocuments();
  const { forms, isLoading: formsLoading } = useForms();
  const { useTemplatesByBlueprint } = useTemplates();
  const { toast } = useToast();

  const [step, setStep] = useState<'basic' | 'form'>('basic');
  const [basicData, setBasicData] = useState({
    title: '',
    numero_processo: '',
    form_template: '',
    document_template: '',
  });
  const [formFieldsData, setFormFieldsData] = useState<Record<string, any>>({});

  // Copilot states
  const [showCopilotDialog, setShowCopilotDialog] = useState(false);
  const [copilotPrompt, setCopilotPrompt] = useState('');
  const [generatedContent, setGeneratedContent] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  // Template suggestion state
  const [showTemplateSuggestion, setShowTemplateSuggestion] = useState(false);
  const [suggestedTemplates, setSuggestedTemplates] = useState<any[]>([]);

  const selectedForm = forms.find(f => f.id === basicData.form_template);

  // Buscar templates de documento associados ao blueprint do formulário selecionado
  const { data: documentTemplates, isLoading: templatesLoading } = useTemplatesByBlueprint(
    selectedForm?.blueprint || '',
    !!selectedForm?.blueprint
  );

  // Auto-selecionar template se houver apenas um
  useEffect(() => {
    if (documentTemplates?.length === 1 && !basicData.document_template) {
      setBasicData(prev => ({ ...prev, document_template: documentTemplates[0].id }));
    }
  }, [documentTemplates]);

  // Handler para mudança de form_template (limpa document_template)
  const handleFormTemplateChange = (value: string) => {
    setBasicData({ ...basicData, form_template: value, document_template: '' });
  };

  // Copilot mutations
  const suggestTemplateMutation = useMutation({
    mutationFn: async (caseData: { specialty?: string; phase?: string; case_type?: string }) => {
      const res = await api.post('/api/v1/processos/copilot/sugerir-template/', { case_data: caseData });
      return res.data;
    },
    onSuccess: (data) => {
      setSuggestedTemplates(data.suggested_templates || []);
      setShowTemplateSuggestion(true);
      toast({
        title: 'Templates sugeridos',
        description: 'IA sugeriu templates baseados no tipo de caso.',
      });
    },
    onError: () => {
      toast({
        title: 'Erro ao sugerir templates',
        description: 'Não foi possível obter sugestões da IA.',
        variant: 'destructive',
      });
    },
  });

  const generateDocumentMutation = useMutation({
    mutationFn: async (data: { prompt: string; template_type: string; context: Record<string, any> }) => {
      const res = await api.post('/api/v1/processos/copilot/gerar-documento/', data);
      return res.data;
    },
    onSuccess: (data) => {
      setGeneratedContent(data.content || '');
      toast({
        title: 'Documento gerado',
        description: 'IA gerou o documento com sucesso.',
      });
    },
    onError: () => {
      toast({
        title: 'Erro ao gerar documento',
        description: 'Não foi possível gerar o documento com IA.',
        variant: 'destructive',
      });
    },
  });

  const autoFillMutation = useMutation({
    mutationFn: async (data: { template: string; case_data: Record<string, any> }) => {
      const res = await api.post('/api/v1/processos/copilot/auto-preencher/', data);
      return res.data;
    },
    onSuccess: (data) => {
      if (data.filled_content) {
        setGeneratedContent(data.filled_content);
        toast({
          title: 'Template preenchido',
          description: `Preencheu ${data.placeholders_filled?.length || 0} de ${data.placeholders_found?.length || 0} campos.`,
        });
      }
    },
    onError: () => {
      toast({
        title: 'Erro ao preencher template',
        description: 'Não foi possível preencher automaticamente.',
        variant: 'destructive',
      });
    },
  });

  const handleCopilotGenerate = () => {
    if (!copilotPrompt.trim()) {
      toast({
        title: 'Prompt necessário',
        description: 'Descreva o documento que deseja gerar.',
        variant: 'destructive',
      });
      return;
    }

    setIsGenerating(true);
    generateDocumentMutation.mutate({
      prompt: copilotPrompt,
      template_type: 'peticao_inicial',
      context: {
        form_template: basicData.form_template,
        title: basicData.title,
        numero_processo: basicData.numero_processo,
      },
    }, {
      onSettled: () => setIsGenerating(false),
    });
  };

  const handleRequestTemplateSuggestion = () => {
    const selectedForm = forms.find(f => f.id === basicData.form_template);
    suggestTemplateMutation.mutate({
      specialty: 'civel',
      phase: 'inicial',
      case_type: 'acao',
    });
  };

  const handleBasicSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!basicData.title || !basicData.form_template) {
      toast({
        title: "Campos obrigatórios",
        description: "Por favor, preencha todos os campos obrigatórios.",
        variant: "destructive",
      });
      return;
    }

    // Verificar se tem templates disponíveis e se um foi selecionado
    if (documentTemplates && documentTemplates.length > 0 && !basicData.document_template) {
      toast({
        title: "Template de documento obrigatório",
        description: "Por favor, selecione um template de documento.",
        variant: "destructive",
      });
      return;
    }

    // Verificar se o form template tem blueprint
    if (!selectedForm?.blueprint) {
      toast({
        title: "Template incompleto",
        description: "O template selecionado não possui um blueprint vinculado. Por favor, configure isso no admin.",
        variant: "destructive",
      });
      return;
    }

    setStep('form');
  };

  const handleFormSubmit = async () => {
    if (!selectedForm?.blueprint) {
      toast({
        title: "Erro",
        description: "Blueprint não encontrado.",
        variant: "destructive",
      });
      return;
    }

    try {
      const document = await createDocument({
        title: basicData.title,
        numero_processo: basicData.numero_processo || undefined,
        form_template: basicData.form_template,
        document_template: basicData.document_template || undefined,
        data: formFieldsData,
      });

      toast({
        title: "Documento criado",
        description: "O documento foi criado com sucesso.",
      });

      // Redireciona para a página de detalhes do documento criado
      router.push(`/dashboard/documents/${document.id}`);
    } catch (error: any) {
      toast({
        title: "Erro ao criar documento",
        description: error.response?.data?.detail || "Ocorreu um erro ao criar o documento.",
        variant: "destructive",
      });
    }
  };

  if (step === 'basic') {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href="/dashboard/documents">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Voltar
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Novo Documento</h1>
            <p className="text-muted-foreground">
              Passo 1: Informações básicas
            </p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Informações Básicas</CardTitle>
            <CardDescription>
              Preencha as informações iniciais do documento
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleBasicSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="title">
                  Título <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="title"
                  placeholder="Ex: Petição Inicial - João Silva vs Empresa X"
                  value={basicData.title}
                  onChange={(e) =>
                    setBasicData({ ...basicData, title: e.target.value })
                  }
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="numero_processo">Número do Processo</Label>
                <Input
                  id="numero_processo"
                  placeholder="Ex: 2024/001"
                  value={basicData.numero_processo}
                  onChange={(e) =>
                    setBasicData({ ...basicData, numero_processo: e.target.value })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="form_template">
                  Template de Formulário <span className="text-red-500">*</span>
                </Label>
                {formsLoading ? (
                  <div className="flex items-center justify-center py-4">
                    <Loader2 className="h-5 w-5 animate-spin text-primary" />
                  </div>
                ) : (
                  <>
                    <Select
                      value={basicData.form_template}
                      onValueChange={handleFormTemplateChange}
                      required
                    >
                      <SelectTrigger id="form_template">
                        <SelectValue placeholder="Selecione um template de formulário" />
                      </SelectTrigger>
                      <SelectContent>
                        {forms.map((form) => (
                          <SelectItem key={form.id} value={form.id}>
                            {form.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {selectedForm && (
                      <div className="mt-2 space-y-1">
                        <p className="text-sm text-muted-foreground">
                          {selectedForm.description}
                        </p>
                        {selectedForm.blueprint_name && (
                          <p className="text-xs text-muted-foreground">
                            <strong>Blueprint:</strong> {selectedForm.blueprint_name}
                          </p>
                        )}
                        {selectedForm.has_generator_warning && (
                          <p className="text-xs text-yellow-600">
                            ⚠️ Este template tinha um gerador que foi removido
                          </p>
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>

              {/* Seletor de Template de Documento - aparece quando há templates disponíveis */}
              {basicData.form_template && (
                <div className="space-y-2">
                  <Label htmlFor="document_template">
                    Template de Documento {documentTemplates && documentTemplates.length > 0 && <span className="text-red-500">*</span>}
                  </Label>
                  {templatesLoading ? (
                    <div className="flex items-center justify-center py-4">
                      <Loader2 className="h-5 w-5 animate-spin text-primary" />
                    </div>
                  ) : documentTemplates && documentTemplates.length > 0 ? (
                    <>
                      <Select
                        value={basicData.document_template}
                        onValueChange={(value) =>
                          setBasicData({ ...basicData, document_template: value })
                        }
                      >
                        <SelectTrigger id="document_template">
                          <SelectValue placeholder="Selecione um template de documento" />
                        </SelectTrigger>
                        <SelectContent>
                          {documentTemplates.map((template) => (
                            <SelectItem key={template.id} value={template.id}>
                              <div className="flex items-center gap-2">
                                <FileText className="h-4 w-4" />
                                {template.name}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <p className="text-xs text-muted-foreground">
                        {documentTemplates.length} template(s) disponível(is) para este formulário
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
              )}

              <div className="flex gap-2">
                <Button type="submit" disabled={formsLoading || templatesLoading}>
                  Próximo: Preencher Formulário
                  <ArrowLeft className="ml-2 h-4 w-4 rotate-180" />
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleRequestTemplateSuggestion}
                  disabled={suggestTemplateMutation.isPending}
                >
                  <Sparkles className="mr-2 h-4 w-4" />
                  Sugerir Template
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => setShowCopilotDialog(true)}
                >
                  <Wand2 className="mr-2 h-4 w-4" />
                  Gerar com IA
                </Button>
                <Link href="/dashboard/documents">
                  <Button type="button" variant="outline">
                    Cancelar
                  </Button>
                </Link>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Step 2: Form fields
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => setStep('basic')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Voltar
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Novo Documento</h1>
          <p className="text-muted-foreground">
            Passo 2: Preencher campos do formulário
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>
            {selectedForm?.name}
          </CardTitle>
          <CardDescription>
            Preencha os campos abaixo para criar o documento
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <DynamicForm
            fields={selectedForm?.fields}
            sections={selectedForm?.sections}
            data={formFieldsData}
            onChange={setFormFieldsData}
            documentTitle={basicData.title}
            blueprintAgents={selectedForm?.blueprint_agents}
          />

          <div className="flex gap-2 pt-4 border-t">
            <Button onClick={handleFormSubmit} disabled={isCreating}>
              {isCreating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Criando...
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  Criar Documento
                </>
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => setStep('basic')}
            >
              Voltar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Dialog: Gerar com IA */}
      <Dialog open={showCopilotDialog} onOpenChange={setShowCopilotDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-purple-500" />
                Gerar Documento com IA
              </div>
            </DialogTitle>
            <DialogDescription>
              Descreva o documento que deseja gerar. A IA criará um documento jurídico completo.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="copilot-prompt">Descrição do Documento</Label>
              <Textarea
                id="copilot-prompt"
                placeholder="Ex: Gere uma petição inicial de ação de danos morais contra empresa de telefonia por cobrança indevida..."
                value={copilotPrompt}
                onChange={(e) => setCopilotPrompt(e.target.value)}
                rows={6}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Tipo de Documento</Label>
                <Select defaultValue="peticao_inicial">
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="peticao_inicial">Petição Inicial</SelectItem>
                    <SelectItem value="contestacao">Contestação</SelectItem>
                    <SelectItem value="recurso_apelacao">Recurso de Apelação</SelectItem>
                    <SelectItem value="mandado_seguranca">Mandado de Segurança</SelectItem>
                    <SelectItem value="procuracao">Procuração</SelectItem>
                    <SelectItem value="contrato_honorarios">Termo de Referência</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {generatedContent && (
              <div className="space-y-2">
                <Label>Documento Gerado</Label>
                <div className="border rounded-md p-4 max-h-64 overflow-auto bg-muted text-sm whitespace-pre-wrap">
                  {generatedContent}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      navigator.clipboard.writeText(generatedContent);
                      toast({ title: 'Copiado!', description: 'Conteúdo copiado para área de transferência.' });
                    }}
                  >
                    Copiar
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setGeneratedContent('')}
                  >
                    <X className="h-4 w-4 mr-2" />
                    Limpar
                  </Button>
                </div>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCopilotDialog(false)}>
              Fechar
            </Button>
            <Button onClick={handleCopilotGenerate} disabled={isGenerating || generateDocumentMutation.isPending}>
              {isGenerating || generateDocumentMutation.isPending ? (
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
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog: Sugestão de Templates */}
      <Dialog open={showTemplateSuggestion} onOpenChange={setShowTemplateSuggestion}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Templates Sugeridos</DialogTitle>
            <DialogDescription>
              A IA analisou o caso e sugeriu os seguintes templates:
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3">
            {suggestedTemplates.map((tmpl, idx) => (
              <Card key={idx} className={tmpl.priority === 1 ? 'border-purple-300 bg-purple-50' : ''}>
                <CardContent className="pt-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-medium">{tmpl.name}</h4>
                      <p className="text-sm text-muted-foreground">{tmpl.reason}</p>
                    </div>
                    {tmpl.priority === 1 && (
                      <Badge variant="default">Recomendado</Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <DialogFooter>
            <Button onClick={() => setShowTemplateSuggestion(false)}>
              Fechar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
