'use client';

import { useState, useEffect } from 'react';
import { useFormAssistants } from '@/hooks/use-form-assistants';
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
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
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
import { Badge } from '@/components/ui/badge';
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';
import type { FormAssistant } from '@/hooks/use-form-assistants';

interface EditFormAssistantDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  assistant: FormAssistant;
  onSuccess?: () => void;
}

const openaiModels = [
  { value: 'gpt-4o', label: 'GPT-4o' },
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
  { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
];

const anthropicModels = [
  { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet' },
  { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus' },
  { value: 'claude-3-sonnet-20240229', label: 'Claude 3 Sonnet' },
  { value: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku' },
];

export default function EditFormAssistantDialog({
  open,
  onOpenChange,
  assistant,
  onSuccess,
}: EditFormAssistantDialogProps) {
  const { updateAssistant, isUpdating } = useFormAssistants();
  const { toast } = useToast();

  // Form State - initialize with agent data
  const [name, setName] = useState(assistant.name);
  const [description, setDescription] = useState(assistant.description || '');
  const [assistantType, setAssistantType] = useState(assistant.assistant_type);
  const [icon, setIcon] = useState(assistant.icon || 'Bot');
  const [color, setColor] = useState(assistant.color || '#3b82f6');
  const [displayOrder, setDisplayOrder] = useState(assistant.display_order || 0);
  const [systemPrompt, setSystemPrompt] = useState(assistant.system_prompt);
  const [userPromptTemplate, setUserPromptTemplate] = useState(assistant.user_prompt_template);
  const [llmProvider, setLlmProvider] = useState<'openai' | 'anthropic'>(assistant.llm_provider);
  const [modelName, setModelName] = useState(assistant.model_name);
  const [temperature, setTemperature] = useState([assistant.temperature ?? 0.7]);
  const [maxTokens, setMaxTokens] = useState(assistant.max_tokens ?? 1000);
  const [useRag, setUseRag] = useState(assistant.use_rag ?? false);
  const [ragQueryTemplate, setRagQueryTemplate] = useState(assistant.rag_query_template || '');
  const [isActive, setIsActive] = useState(assistant.is_active ?? true);
  const [isDefault, setIsDefault] = useState(assistant.is_default ?? false);

  // Reset form when agent changes
  useEffect(() => {
    if (assistant) {
      setName(assistant.name);
      setDescription(assistant.description || '');
      setAssistantType(assistant.assistant_type);
      setIcon(assistant.icon || 'Bot');
      setColor(assistant.color || '#3b82f6');
      setDisplayOrder(assistant.display_order || 0);
      setSystemPrompt(assistant.system_prompt);
      setUserPromptTemplate(assistant.user_prompt_template);
      setLlmProvider(assistant.llm_provider);
      setModelName(assistant.model_name);
      setTemperature([assistant.temperature ?? 0.7]);
      setMaxTokens(assistant.max_tokens ?? 1000);
      setUseRag(assistant.use_rag ?? false);
      setRagQueryTemplate(assistant.rag_query_template || '');
      setIsActive(assistant.is_active ?? true);
      setIsDefault(assistant.is_default ?? false);
    }
  }, [assistant]);

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
        description: 'Por favor, informe o nome do assistente.',
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
      await updateAssistant({
        id: assistant.id,
        data: {
          name: name.trim(),
          description: description.trim() || undefined,
          assistant_type: assistantType.trim(),
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
        },
      });

      toast({
        title: 'Assistente atualizado',
        description: `O assistente "${name}" foi atualizado com sucesso.`,
      });

      onOpenChange(false);
      onSuccess?.();
    } catch (error: any) {
      toast({
        title: 'Erro ao atualizar assistente',
        description: error.response?.data?.detail || 'Não foi possível atualizar o assistente.',
        variant: 'destructive',
      });
    }
  };

  const availableModels = llmProvider === 'openai' ? openaiModels : anthropicModels;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Editar Assistente de Formulário</DialogTitle>
          <DialogDescription>
            Atualize as configurações do assistente &quot;{assistant.name}&quot;
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Nome e Descrição */}
          <div className="space-y-4">
            <div>
              <Label htmlFor="name">Nome *</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Ex: Corretor Avançado de Textos"
                required
              />
            </div>

            <div>
              <Label htmlFor="description">Descrição</Label>
              <div className="relative">
                <Textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Descrição opcional do assistente"
                  rows={2}
                  className="pr-32"
                />
                <div className="absolute top-1 right-1">
                  <AIEnhanceButton
                    value={description}
                    onEnhance={setDescription}
                    context="descrição de assistente de formulário jurídico"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Tipo de Agente */}
          <div className="space-y-4">
            <div>
              <Label htmlFor="agent-type">Tipo do Assistente de Campo *</Label>
              <Input
                id="agent-type"
                value={assistantType}
                onChange={(e) => setAssistantType(e.target.value)}
                placeholder="Ex: corretor, tradutor, expansao, sugestao"
                required
              />
              <p className="text-xs text-muted-foreground mt-1">
                Identificador único do tipo de assistente (ex: corretor, tradutor, expansao, sugestao)
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
                  placeholder="Bot, FileText, Mail..."
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
              <div className="relative">
                <Textarea
                  id="system-prompt"
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  placeholder="Você é um assistente especializado em..."
                  rows={4}
                  required
                  className="pr-32"
                />
                <div className="absolute top-1 right-1">
                  <AIEnhanceButton
                    value={systemPrompt}
                    onEnhance={setSystemPrompt}
                    context="system prompt de assistente de formulário jurídico"
                    objective="Melhore a clareza das instruções, mantendo variáveis {{}} intactas"
                  />
                </div>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Instruções gerais para o comportamento do assistente
              </p>
            </div>

            <div>
              <Label htmlFor="user-prompt">User Prompt Template *</Label>
              <div className="relative">
                <Textarea
                  id="user-prompt"
                  value={userPromptTemplate}
                  onChange={(e) => setUserPromptTemplate(e.target.value)}
                  placeholder="Analise o seguinte texto: {{texto}}"
                  rows={4}
                  required
                  className="pr-32"
                />
                <div className="absolute top-1 right-1">
                  <AIEnhanceButton
                    value={userPromptTemplate}
                    onEnhance={setUserPromptTemplate}
                    context="user prompt template de assistente de formulário"
                    objective="Melhore a clareza do template, mantendo variáveis {{}} intactas"
                  />
                </div>
              </div>
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
              <RadioGroup
                value={llmProvider}
                onValueChange={(value) => {
                  setLlmProvider(value as 'openai' | 'anthropic');
                  // Keep model if still valid for new provider
                  const newModels = value === 'openai' ? openaiModels : anthropicModels;
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
                  <RadioGroupItem value="anthropic" id="anthropic" />
                  <Label htmlFor="anthropic" className="cursor-pointer">
                    Anthropic
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
                <div className="relative">
                  <Textarea
                    id="rag-query"
                    value={ragQueryTemplate}
                    onChange={(e) => setRagQueryTemplate(e.target.value)}
                    placeholder="Buscar informações sobre {{topic}} relacionado a {{context}}"
                    rows={3}
                    className="pr-32"
                  />
                  <div className="absolute top-1 right-1">
                    <AIEnhanceButton
                      value={ragQueryTemplate}
                      onEnhance={setRagQueryTemplate}
                      context="template de query RAG para base de conhecimento jurídica"
                      objective="Melhore a clareza da query, mantendo variáveis {{}} intactas"
                    />
                  </div>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Template para buscar contexto na base de conhecimento
                </p>
              </div>
            )}
          </div>

          {/* Status */}
          <div className="space-y-3 pt-2 border-t">
            <div className="flex items-center justify-between">
              <Label htmlFor="is-active">Assistente Ativo</Label>
              <Switch id="is-active" checked={isActive} onCheckedChange={setIsActive} />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="is-default">Assistente Padrão</Label>
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
              disabled={isUpdating}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={isUpdating}>
              {isUpdating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Atualizando...
                </>
              ) : (
                'Salvar Alterações'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
