'use client';

import { useState, useEffect } from 'react';
import { useAgents } from '@/hooks/use-agents';
import { useToast } from '@/hooks/use-toast';
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
import { useLLMProviders } from '@/hooks/use-llm-providers';

interface CreateAgentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
  defaultCategory?: string; // Pre-seleciona categoria (ex: 'document_generator', 'form_assistant')
}

export default function CreateAgentDialog({
  open,
  onOpenChange,
  onSuccess,
  defaultCategory,
}: CreateAgentDialogProps) {
  const { createAgent, isCreating } = useAgents();
  const { toast } = useToast();
  const { providers, getModelsForProvider, isLoading: isLoadingProviders } = useLLMProviders();

  // Form State
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [agentType, setAgentType] = useState(defaultCategory || 'chat_assistant');
  const [icon, setIcon] = useState('Bot');
  const [color, setColor] = useState('#3b82f6');
  const [displayOrder, setDisplayOrder] = useState(0);
  const [systemPrompt, setSystemPrompt] = useState('');
  const [userPromptTemplate, setUserPromptTemplate] = useState('');
  const [llmProvider, setLlmProvider] = useState<string>('watsonx');
  const [modelName, setModelName] = useState('');
  const [temperature, setTemperature] = useState([0.7]);
  const [maxTokens, setMaxTokens] = useState(1000);
  const [useRag, setUseRag] = useState(false);
  const [ragQueryTemplate, setRagQueryTemplate] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [isDefault, setIsDefault] = useState(false);

  // Reset agentType quando dialog abre ou defaultCategory muda
  useEffect(() => {
    if (open) {
      setAgentType(defaultCategory || 'chat_assistant');
    }
  }, [open, defaultCategory]);

  // Extract variables from template
  const extractVariables = (template: string): string[] => {
    const regex = /\{\{(\w+)\}\}/g;
    const matches = template.matchAll(regex);
    const variables = new Set<string>();
    for (const match of matches) {
      variables.add(match[1]);
    }
    return Array.from(variables);
  };

  const variables = extractVariables(userPromptTemplate);

  const resetForm = () => {
    setName('');
    setDescription('');
    setAgentType('chat_assistant');
    setIcon('Bot');
    setColor('#3b82f6');
    setDisplayOrder(0);
    setSystemPrompt('');
    setUserPromptTemplate('');
    setLlmProvider('watsonx');
    setModelName('');
    setTemperature([0.7]);
    setMaxTokens(1000);
    setUseRag(false);
    setRagQueryTemplate('');
    setIsActive(true);
    setIsDefault(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validação
    if (!name.trim()) {
      toast({
        title: 'Nome obrigatório',
        description: 'Por favor, informe o nome do agente.',
        variant: 'destructive',
      });
      return;
    }

    if (!agentType) {
      toast({
        title: 'Tipo obrigatório',
        description: 'Por favor, selecione o tipo do agente.',
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
      // Criar payload inicial
      const rawPayload = {
        name: name.trim(),
        description: description.trim() || undefined,
        agent_type: agentType.trim(),
        icon: icon.trim() || 'Bot',
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
      };

      // Remover campos undefined (Django não gosta de undefined, apenas null ou campo ausente)
      const payload = Object.fromEntries(
        Object.entries(rawPayload).filter(([_, value]) => value !== undefined)
      );

      console.log('=== DEBUG: Criando agente ===');
      console.log('Payload enviado:', JSON.stringify(payload, null, 2));

      await createAgent(payload);

      toast({
        title: 'Agente criado',
        description: `O agente "${name}" foi criado com sucesso.`,
      });

      resetForm();
      onOpenChange(false);
      onSuccess?.();
    } catch (error: any) {
      console.error('=== DEBUG: Erro ao criar agente ===');
      console.error('Error completo:', error);
      console.error('Error response:', error.response);
      console.error('Error response data:', error.response?.data);
      console.error('Error response status:', error.response?.status);

      // Tentar obter mensagem de erro mais detalhada
      let errorMessage = 'Não foi possível criar o agente.';

      if (error.response?.data) {
        if (typeof error.response.data === 'string') {
          errorMessage = error.response.data;
        } else if (error.response.data.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.response.data.message) {
          errorMessage = error.response.data.message;
        } else {
          // Tentar mostrar o primeiro erro de campo
          const firstError = Object.values(error.response.data)[0];
          if (Array.isArray(firstError) && firstError.length > 0) {
            errorMessage = `${Object.keys(error.response.data)[0]}: ${firstError[0]}`;
          } else {
            errorMessage = JSON.stringify(error.response.data);
          }
        }
      }

      toast({
        title: 'Erro ao criar agente',
        description: errorMessage,
        variant: 'destructive',
      });
    }
  };

  const availableModels = getModelsForProvider(llmProvider).map(m => ({
    value: m.model_id,
    label: m.display_name,
  }));

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Criar Novo Agente de IA</DialogTitle>
          <DialogDescription>
            Configure um novo agente com prompts personalizados e parâmetros de IA
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
                placeholder="Ex: Corretor Avançado de Documents"
                required
                aiContext="nome do agente de IA jurídico"
                aiObjective="Sugira um nome claro e descritivo para o agente"
              />
            </div>

            <div>
              <Label htmlFor="description">Descrição</Label>
              <AITextarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                setValue={setDescription}
                placeholder="Descrição opcional do agente"
                rows={2}
                aiContext="descrição de agente de IA jurídico"
                aiObjective="Descreva de forma clara as capacidades e propósito do agente"
              />
            </div>
          </div>

          {/* Tipo de Agente */}
          <div className="space-y-4">
            <div>
              <Label htmlFor="agent-type">
                Tipo/Subtipo do Agente *
                {defaultCategory && (
                  <span className="text-xs text-muted-foreground ml-2">
                    (pré-definido: {defaultCategory})
                  </span>
                )}
              </Label>
              <AIInput
                id="agent-type"
                value={agentType}
                onChange={(e) => setAgentType(e.target.value)}
                setValue={setAgentType}
                placeholder="Ex: chat_assistant, document_generator, form_assistant"
                required
                disabled={!!defaultCategory}
                className={defaultCategory ? 'bg-muted cursor-not-allowed' : ''}
                aiContext="tipo/subtipo do agente de IA"
                aiObjective="Defina o identificador único do tipo de agente"
              />
              <p className="text-xs text-muted-foreground mt-1">
                {defaultCategory
                  ? 'Tipo fixo para este contexto (não editável)'
                  : 'Identificador único do tipo de agente (ex: chat_assistant, document_generator)'}
              </p>
            </div>
          </div>

          {/* Customização Visual */}
          <div className="space-y-4">
            <h4 className="font-medium text-sm">Customização Visual</h4>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="icon">Ícone (Lucide)</Label>
                <AIInput
                  id="icon"
                  value={icon}
                  onChange={(e) => setIcon(e.target.value)}
                  setValue={setIcon}
                  placeholder="Bot, FileText, Mail..."
                  aiContext="nome do ícone Lucide para o agente"
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
                placeholder="Você é um assistente especializado em..."
                rows={4}
                required
                aiContext="system prompt de agente de IA jurídico"
                aiObjective="Melhore a clareza das instruções, mantendo variáveis {{}} intactas"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Instruções gerais para o comportamento do agente
              </p>
            </div>

            <div>
              <Label htmlFor="user-prompt">User Prompt Template *</Label>
              <AITextarea
                id="user-prompt"
                value={userPromptTemplate}
                onChange={(e) => setUserPromptTemplate(e.target.value)}
                setValue={setUserPromptTemplate}
                placeholder="Analise o seguinte texto: {{texto}}"
                rows={4}
                required
                aiContext="user prompt template de agente de IA jurídico"
                aiObjective="Melhore a clareza do template, mantendo variáveis {{}} intactas"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Use <code className="bg-muted px-1 py-0.5 rounded">{'{{variavel}}'}</code> para
                variáveis dinâmicas. Exemplos: <code className="bg-muted px-1 py-0.5 rounded">{'{{texto}}'}</code>,{' '}
                <code className="bg-muted px-1 py-0.5 rounded">{'{{contexto}}'}</code>,{' '}
                <code className="bg-muted px-1 py-0.5 rounded">{'{{instrucao}}'}</code>
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
              {isLoadingProviders ? (
                <div className="flex items-center gap-2 mt-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Carregando providers...
                </div>
              ) : (
                <RadioGroup
                  value={llmProvider}
                  onValueChange={(value) => {
                    setLlmProvider(value as string);
                    setModelName('');
                  }}
                  className="flex flex-wrap gap-4 mt-2"
                >
                  {providers.map((p) => (
                    <div key={p.code} className="flex items-center space-x-2">
                      <RadioGroupItem value={p.code} id={`create-${p.code}`} />
                      <Label htmlFor={`create-${p.code}`} className="cursor-pointer">
                        {p.name}
                        {!p.has_api_key && (
                          <span className="text-xs text-destructive ml-1">(sem chave)</span>
                        )}
                      </Label>
                    </div>
                  ))}
                </RadioGroup>
              )}
            </div>

            <div>
              <Label htmlFor="model">Modelo *</Label>
              <Select value={modelName} onValueChange={setModelName}>
                <SelectTrigger id="model">
                  <SelectValue placeholder={availableModels.length === 0 ? 'Nenhum modelo disponível' : 'Selecione o modelo'} />
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
                onChange={(e) => setMaxTokens(parseInt(e.target.value) || 1000)}
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
                  aiContext="template de query RAG para base de conhecimento jurídica"
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
              <Label htmlFor="is-active">Agente Ativo</Label>
              <Switch id="is-active" checked={isActive} onCheckedChange={setIsActive} />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="is-default">Agente Padrão</Label>
                <p className="text-xs text-muted-foreground">
                  Será usado como padrão para este tipo
                </p>
              </div>
              <Switch id="is-default" checked={isDefault} onCheckedChange={setIsDefault} />
            </div>
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
                'Criar Agente'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
