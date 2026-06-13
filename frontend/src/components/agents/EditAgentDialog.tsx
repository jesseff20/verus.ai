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
import { Badge } from '@/components/ui/badge';
import { useLLMProviders } from '@/hooks/use-llm-providers';
import type { AgentPrompt } from '@/types';

interface EditAgentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agent: AgentPrompt;
  onSuccess?: () => void;
}

export default function EditAgentDialog({
  open,
  onOpenChange,
  agent,
  onSuccess,
}: EditAgentDialogProps) {
  const { updateAgent, isUpdating } = useAgents();
  const { toast } = useToast();
  const { providers, getModelsForProvider, isLoading: isLoadingProviders } = useLLMProviders();

  // Form State - initialize with agent data
  const [name, setName] = useState(agent.name);
  const [description, setDescription] = useState(agent.description || '');
  const [agentType, setAgentType] = useState(agent.agent_type);
  const [icon, setIcon] = useState(agent.icon || 'Bot');
  const [color, setColor] = useState(agent.color || '#3b82f6');
  const [displayOrder, setDisplayOrder] = useState(agent.display_order || 0);
  const [systemPrompt, setSystemPrompt] = useState(agent.system_prompt);
  const [userPromptTemplate, setUserPromptTemplate] = useState(agent.user_prompt_template);
  const [llmProvider, setLlmProvider] = useState<'openai' | 'anthropic' | 'watsonx'>(agent.llm_provider);
  const [modelName, setModelName] = useState(agent.model_name);
  const [temperature, setTemperature] = useState([agent.temperature ?? 0.7]);
  const [maxTokens, setMaxTokens] = useState(agent.max_tokens ?? 1000);
  const [useRag, setUseRag] = useState(agent.use_rag ?? false);
  const [ragQueryTemplate, setRagQueryTemplate] = useState(agent.rag_query_template || '');
  const [isActive, setIsActive] = useState(agent.is_active ?? true);
  const [isDefault, setIsDefault] = useState(agent.is_default ?? false);

  // Reset form when agent changes
  useEffect(() => {
    if (agent) {
      setName(agent.name);
      setDescription(agent.description || '');
      setAgentType(agent.agent_type);
      setIcon(agent.icon || 'Bot');
      setColor(agent.color || '#3b82f6');
      setDisplayOrder(agent.display_order || 0);
      setSystemPrompt(agent.system_prompt);
      setUserPromptTemplate(agent.user_prompt_template);
      setLlmProvider(agent.llm_provider);
      setModelName(agent.model_name);
      setTemperature([agent.temperature ?? 0.7]);
      setMaxTokens(agent.max_tokens ?? 1000);
      setUseRag(agent.use_rag ?? false);
      setRagQueryTemplate(agent.rag_query_template || '');
      setIsActive(agent.is_active ?? true);
      setIsDefault(agent.is_default ?? false);
    }
  }, [agent]);

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
        description: 'Por favor, informe o nome do agente.',
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
      await updateAgent({
        id: agent.id,
        data: {
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
        },
      });

      toast({
        title: 'Agente atualizado',
        description: `O agente "${name}" foi atualizado com sucesso.`,
      });

      onOpenChange(false);
      onSuccess?.();
    } catch (error: any) {
      toast({
        title: 'Erro ao atualizar agente',
        description: error.response?.data?.detail || 'Não foi possível atualizar o agente.',
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
          <DialogTitle>Editar Agente de IA</DialogTitle>
          <DialogDescription>
            Atualize as configurações do agente &quot;{agent.name}&quot;
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
              <Label htmlFor="agent-type">Tipo/Subtipo do Agente Chat *</Label>
              <AIInput
                id="agent-type"
                value={agentType}
                onChange={(e) => setAgentType(e.target.value)}
                setValue={setAgentType}
                placeholder="Ex: especialista_direito_civil, consultor_juridico, analista_processual"
                required
                aiContext="tipo/subtipo do agente de IA"
                aiObjective="Defina o identificador único do tipo de agente"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Identificador único do subtipo de agente (ex: especialista_direito_civil, consultor_juridico)
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
                    setLlmProvider(value as 'openai' | 'anthropic' | 'watsonx');
                    setModelName('');
                  }}
                  className="flex flex-col gap-3 mt-2"
                >
                  {providers.map((p) => {
                    const hasApiKey = p.has_api_key;
                    const isWatsonX = p.code === 'watsonx';

                    return (
                      <div key={p.code} className="flex items-start gap-2 p-2 rounded border">
                        <RadioGroupItem value={p.code} id={`edit-${p.code}`} className="mt-1" />
                        <Label htmlFor={`edit-${p.code}`} className="cursor-pointer flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{p.name}</span>
                            {!hasApiKey && (
                              <Badge variant="outline" className="text-xs border-destructive text-destructive">
                                Sem API Key
                              </Badge>
                            )}
                          </div>
                          <p className="text-xs text-muted-foreground mt-1">
                            {isWatsonX && !hasApiKey
                              ? 'Configure a WATSONX_API_KEY e WATSONX_PROJECT_ID no .env para usar este provider.'
                              : p.description || ''}
                          </p>
                        </Label>
                      </div>
                    );
                  })}
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
