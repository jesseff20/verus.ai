'use client';

import { useState, useEffect } from 'react';
import { useDocumentGenerators } from '@/hooks/use-document-generators';
import { useTemplates } from '@/hooks/use-templates';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/hooks/use-auth';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { AIInput } from '@/components/ui/ai-input';
import { AITextarea } from '@/components/ui/ai-textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Loader2, Sparkles, Info } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface CreateDocumentGeneratorDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

const openaiModels = [
  { value: 'gpt-4o', label: 'GPT-4o' },
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
  { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
];

const watsonxModels = [
  { value: 'mistralai/mistral-medium-2505', label: 'Mistral Medium 2505' },
  { value: 'meta-llama/llama-3-3-70b-instruct', label: 'Llama 3.3 70B' },
  { value: 'ibm/granite-3-3-8b-instruct', label: 'Granite 3.3 8B' },
  { value: 'ibm/granite-3-2-2b-instruct', label: 'Granite 3.3 2B' },
];

export default function CreateDocumentGeneratorDialog({
  open,
  onOpenChange,
  onSuccess,
}: CreateDocumentGeneratorDialogProps) {
  const { createGenerator, isCreating } = useDocumentGenerators();
  const { templates } = useTemplates();
  const { toast } = useToast();
  const { user } = useAuth();

  const isAnalyst = user?.role === 'analyst';

  // Form State (valores default para criação)
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [documentType, setDocumentType] = useState('');
  const [specialty, setSpecialty] = useState('geral');
  const [documentTemplate, setDocumentTemplate] = useState('');
  const [icon, setIcon] = useState('FileText');
  const [color, setColor] = useState('#3b82f6');
  const [displayOrder, setDisplayOrder] = useState(0);
  const [systemPrompt, setSystemPrompt] = useState('');
  const [userPromptTemplate, setUserPromptTemplate] = useState('');
  const [llmProvider, setLlmProvider] = useState<'openai' | 'anthropic' | 'watsonx'>('openai');
  const [modelName, setModelName] = useState('');
  const [temperature, setTemperature] = useState([0.7]);
  const [maxTokens, setMaxTokens] = useState(4000);
  const [useRag, setUseRag] = useState(true);
  const [ragQueryTemplate, setRagQueryTemplate] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [isDefault, setIsDefault] = useState(false);

  // Reset form quando dialog abre
  useEffect(() => {
    if (open) {
      setName('');
      setDescription('');
      setDocumentType('');
      setSpecialty('geral');
      setDocumentTemplate('');
      setIcon('FileText');
      setColor('#3b82f6');
      setDisplayOrder(0);
      setSystemPrompt('');
      setUserPromptTemplate('');
      setLlmProvider('openai');
      setModelName('');
      setTemperature([0.7]);
      setMaxTokens(4000);
      setUseRag(true);
      setRagQueryTemplate('');
      setIsActive(true);
      setIsDefault(false);
    }
  }, [open]);

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

  const variables = extractVariables(userPromptTemplate || '');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validação
    if (!name.trim()) {
      toast({
        title: 'Nome obrigatório',
        description: 'Por favor, informe o nome do gerador.',
        variant: 'destructive',
      });
      return;
    }

    if (!documentType.trim()) {
      toast({
        title: 'Tipo de documento obrigatório',
        description: 'Por favor, informe o tipo de documento.',
        variant: 'destructive',
      });
      return;
    }

    if (!documentTemplate) {
      toast({
        title: 'Template obrigatório',
        description: 'Por favor, selecione um template de documento.',
        variant: 'destructive',
      });
      return;
    }

    if (!systemPrompt.trim()) {
      toast({
        title: 'System Prompt obrigatório',
        description: 'Por favor, informe o prompt de sistema.',
        variant: 'destructive',
      });
      return;
    }

    if (!userPromptTemplate.trim()) {
      toast({
        title: 'User Prompt obrigatório',
        description: 'Por favor, informe o template de prompt do usuário.',
        variant: 'destructive',
      });
      return;
    }

    if (!modelName) {
      toast({
        title: 'Modelo obrigatório',
        description: 'Por favor, selecione o modelo de IA.',
        variant: 'destructive',
      });
      return;
    }

    if (useRag && !ragQueryTemplate.trim()) {
      toast({
        title: 'Query RAG obrigatória',
        description: 'Quando RAG está ativado, o template de query é obrigatório.',
        variant: 'destructive',
      });
      return;
    }

    try {
      await createGenerator({
        name: name.trim(),
        description: description.trim() || undefined,
        document_type: documentType.trim(),
        specialty: specialty || 'geral',
        document_template: documentTemplate,
        icon: icon.trim() || 'FileText',
        color: color || '#3b82f6',
        display_order: displayOrder,
        system_prompt: systemPrompt.trim(),
        user_prompt_template: userPromptTemplate.trim(),
        llm_provider: llmProvider,
        model_name: modelName,
        temperature: temperature[0],
        max_tokens: maxTokens,
        use_rag: useRag,
        rag_query_template: useRag ? ragQueryTemplate.trim() : undefined,
        is_active: isActive,
        is_default: isDefault,
      });

      toast({
        title: 'Gerador criado',
        description: `O gerador "${name}" foi criado com sucesso.`,
      });

      onOpenChange(false);
      onSuccess?.();
    } catch (error: any) {
      console.error('Erro ao criar gerador:', error);
      toast({
        title: 'Erro ao criar gerador',
        description: error.response?.data?.detail || 'Não foi possível criar o gerador.',
        variant: 'destructive',
      });
    }
  };

  const availableModels = llmProvider === 'openai' ? openaiModels : watsonxModels;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Criar Novo Gerador de Documento</DialogTitle>
          <DialogDescription>
            Configure um novo gerador de IA para gerar documentos automaticamente
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Nome e Descrição */}
          <div className="space-y-4">
            <div>
              <Label htmlFor="name">Nome *</Label>
              <AIInput
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                setValue={setName}
                placeholder="Ex: Gerador de Parecer Jurídico"
                required
                aiContext="nome de gerador de documentos jurídicos de procuradoria"
                aiObjective="Sugira um nome claro e descritivo para o gerador de documentos"
              />
            </div>

            <div>
              <Label htmlFor="description">Descrição</Label>
              <AITextarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                setValue={setDescription}
                placeholder="Descrição opcional do gerador"
                rows={2}
                aiContext="descrição de gerador de documentos jurídicos de procuradoria"
                aiObjective="Descreva de forma clara as capacidades e propósito do gerador"
              />
            </div>
          </div>

          {/* Tipo de Documento */}
          <div className="space-y-4">
            <div>
              <Label htmlFor="document-type">Tipo de Documento *</Label>
              <Input
                id="document-type"
                value={documentType}
                onChange={(e) => setDocumentType(e.target.value)}
                placeholder="Ex: peticao_inicial, contestacao, recurso"
                required
              />
              <p className="text-xs text-muted-foreground mt-1">
                Identificador único do tipo de documento (ex: peticao_inicial, contestacao, recurso)
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="specialty">Especialidade Jurídica</Label>
              <Select value={specialty} onValueChange={setSpecialty}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecione a especialidade" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="geral">Geral (Todas as Especialidades)</SelectItem>
                  <SelectItem value="civel">Direito Civil</SelectItem>
                  <SelectItem value="penal">Direito Penal</SelectItem>
                  <SelectItem value="trabalhista">Direito Trabalhista</SelectItem>
                  <SelectItem value="tributario">Direito Tributário</SelectItem>
                  <SelectItem value="previdenciario">Direito Previdenciário</SelectItem>
                  <SelectItem value="administrativo">Direito Administrativo</SelectItem>
                  <SelectItem value="constitucional">Direito Constitucional</SelectItem>
                  <SelectItem value="empresarial">Direito Empresarial</SelectItem>
                  <SelectItem value="consumidor">Direito do Consumidor</SelectItem>
                  <SelectItem value="familia">Direito de Família e Sucessões</SelectItem>
                  <SelectItem value="imobiliario">Direito Imobiliário</SelectItem>
                  <SelectItem value="ambiental">Direito Ambiental</SelectItem>
                  <SelectItem value="digital">Direito Digital e LGPD</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="document-template">Template Associado *</Label>
              <Select value={documentTemplate} onValueChange={setDocumentTemplate}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecione um template..." />
                </SelectTrigger>
                <SelectContent>
                  {templates.map((template) => (
                    <SelectItem key={template.id} value={template.id}>
                      {template.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground mt-1">
                Template que define a estrutura e placeholders do documento
              </p>
            </div>
          </div>

          {/* Customização Visual */}
          <div className="space-y-4">
            <h4 className="font-medium text-sm">Customização Visual</h4>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="icon">Ícone (Lucide)</Label>
                <Input
                  id="icon"
                  value={icon}
                  onChange={(e) => setIcon(e.target.value)}
                  placeholder="FileText, File, Document..."
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Nome do ícone Lucide
                </p>
              </div>

              <div>
                <Label htmlFor="color">Cor (Hex)</Label>
                <div className="flex gap-2">
                  <Input
                    id="color"
                    type="color"
                    value={color}
                    onChange={(e) => setColor(e.target.value)}
                    className="h-10 w-14 p-1"
                  />
                  <Input
                    value={color}
                    onChange={(e) => setColor(e.target.value)}
                    placeholder="#3b82f6"
                    className="flex-1"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="display-order">Ordem de Exibição</Label>
                <Input
                  id="display-order"
                  type="number"
                  value={displayOrder}
                  onChange={(e) => setDisplayOrder(Number(e.target.value))}
                  placeholder="0"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Menor = primeiro
                </p>
              </div>
            </div>
          </div>

          {/* Prompts */}
          <div className="space-y-4">
            <div>
              <Label htmlFor="system-prompt">System Prompt *</Label>
              <AITextarea
                id="system-prompt"
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                setValue={setSystemPrompt}
                placeholder="Você é um gerador especializado em..."
                rows={4}
                required
                aiContext="system prompt de gerador de documentos jurídicos de procuradoria"
                aiObjective="Melhore a clareza das instruções, mantendo variáveis {{}} intactas"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Instruções gerais para o comportamento do gerador
              </p>
            </div>

            <div>
              <Label htmlFor="user-prompt">User Prompt Template *</Label>
              <AITextarea
                id="user-prompt"
                value={userPromptTemplate}
                onChange={(e) => setUserPromptTemplate(e.target.value)}
                setValue={setUserPromptTemplate}
                placeholder="Gere um documento com os seguintes dados: {{dados}}"
                rows={4}
                required
                aiContext="user prompt template de gerador de documentos jurídicos de procuradoria"
                aiObjective="Melhore a clareza do template, mantendo variáveis {{}} intactas"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Use <code className="bg-muted px-1 py-0.5 rounded">{'{{variavel}}'}</code> para
                variáveis dinâmicas. Exemplos: <code className="bg-muted px-1 py-0.5 rounded">{'{{dados}}'}</code>,{' '}
                <code className="bg-muted px-1 py-0.5 rounded">{'{{contexto}}'}</code>
              </p>

              {/* Preview de Variáveis */}
              {variables.length > 0 && (
                <Alert className="mt-2">
                  <Info className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Variáveis detectadas:</strong>{' '}
                    {variables.map((v) => (
                      <code
                        key={v}
                        className="bg-primary/10 text-primary px-1.5 py-0.5 rounded ml-1"
                      >
                        {v}
                      </code>
                    ))}
                  </AlertDescription>
                </Alert>
              )}
            </div>
          </div>

          {/* LLM Provider e Modelo */}
          <div className="space-y-4">
            <div>
              <Label>Provider *</Label>
              <RadioGroup
                value={llmProvider}
                onValueChange={(value) => {
                  setLlmProvider(value as 'openai' | 'watsonx');
                  // Keep model if still valid for new provider
                  const newModels = value === 'openai' ? openaiModels : watsonxModels;
                  if (!newModels.find((m) => m.value === modelName)) {
                    setModelName('');
                  }
                }}
                className="flex gap-4 mt-2"
              >
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="openai" id="openai" />
                  <Label htmlFor="openai" className="cursor-pointer">
                    OpenAI
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="watsonx" id="watsonx" />
                  <Label htmlFor="watsonx" className="cursor-pointer">
                    IBM WatsonX
                  </Label>
                </div>
              </RadioGroup>
            </div>

            <div>
              <Label htmlFor="model">Modelo *</Label>
              <Select value={modelName} onValueChange={setModelName}>
                <SelectTrigger id="model">
                  <SelectValue placeholder="Selecione o modelo" />
                </SelectTrigger>
                <SelectContent>
                  {availableModels.map((model) => (
                    <SelectItem key={model.value} value={model.value}>
                      {model.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Temperature e Max Tokens */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="temperature">
                Temperature: <strong>{temperature[0].toFixed(1)}</strong>
              </Label>
              <Slider
                id="temperature"
                min={0}
                max={2}
                step={0.1}
                value={temperature}
                onValueChange={setTemperature}
                className="mt-2"
              />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>Preciso (0.0)</span>
                <span>Criativo (2.0)</span>
              </div>
            </div>

            <div>
              <Label htmlFor="max-tokens">Max Tokens</Label>
              <Input
                id="max-tokens"
                type="number"
                min={100}
                max={4000}
                step={100}
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value) || 4000)}
              />
              <p className="text-xs text-muted-foreground mt-1">100 - 4000 tokens</p>
            </div>
          </div>

          {/* RAG */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-indigo-600" />
                <Label htmlFor="use-rag">Usar RAG (Busca em Base de Conhecimento)</Label>
              </div>
              <Switch id="use-rag" checked={useRag} onCheckedChange={setUseRag} />
            </div>

            {useRag && (
              <div>
                <Label htmlFor="rag-query">Template de Query RAG *</Label>
                <AITextarea
                  id="rag-query"
                  value={ragQueryTemplate}
                  onChange={(e) => setRagQueryTemplate(e.target.value)}
                  setValue={setRagQueryTemplate}
                  placeholder="Buscar informações sobre {{topic}} relacionado a {{context}}"
                  rows={3}
                  aiContext="template de query RAG para base de conhecimento jurídica de procuradoria"
                  aiObjective="Melhore a clareza da query, mantendo variáveis {{}} intactas"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Template para buscar contexto na base de conhecimento
                </p>
              </div>
            )}
          </div>

          {/* Status */}
          <div className="space-y-3 pt-2 border-t">
            <div className="flex items-center justify-between">
              <Label htmlFor="is-active">Gerador Ativo</Label>
              <Switch id="is-active" checked={isActive} onCheckedChange={setIsActive} />
            </div>

            {!isAnalyst && (
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="is-default">Gerador Público</Label>
                  <p className="text-xs text-muted-foreground">
                    Ficará visível para todos os usuários
                  </p>
                </div>
                <Switch id="is-default" checked={isDefault} onCheckedChange={setIsDefault} />
              </div>
            )}
          </div>

          {/* Actions */}
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isCreating}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={isCreating}>
              {isCreating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Criando...
                </>
              ) : (
                'Criar Gerador'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
