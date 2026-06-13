'use client';

import { useState, useMemo } from 'react';
import type { DocumentBlueprint, SectionAgentConfigDetail } from '@/types';
import { useBlueprintAgents } from '@/hooks/use-section-agents';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';
import {
  Bot,
  Pencil,
  Save,
  X,
  Loader2,
  ChevronsUpDown,
  ShieldCheck,
  Sparkles,
  Plus,
  Trash2,
} from 'lucide-react';
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';

// ========== Types ==========

interface AgentsConfigStepProps {
  blueprint: DocumentBlueprint;
  onUpdate?: (updated: DocumentBlueprint) => void;
}

interface SectionAgentGroup {
  sectionNumber: number;
  sectionName: string;
  sectionId: string;
  generatorAgent: SectionAgentConfigDetail | null;
  validatorAgent: SectionAgentConfigDetail | null;
  subSections: Array<{
    subNumber: string;
    subName: string;
    subId: string;
    generatorAgent: SectionAgentConfigDetail | null;
  }>;
}

// ========== ExpandableTextarea ==========

function ExpandableTextarea({
  value,
  onChange,
  placeholder,
  disabled,
  rows = 6,
  expandedRows = 20,
  enhanceContext,
  enhanceObjective,
}: {
  value: string;
  onChange: (val: string) => void;
  placeholder?: string;
  disabled?: boolean;
  rows?: number;
  expandedRows?: number;
  enhanceContext?: string;
  enhanceObjective?: string;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="relative">
      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={expanded ? expandedRows : rows}
        disabled={disabled}
        className="pr-36 font-mono text-xs transition-all"
      />
      <div className="absolute top-1.5 right-8">
        <AIEnhanceButton
          value={value}
          onEnhance={onChange}
          context={enhanceContext || 'prompt de agente jurídico'}
          objective={enhanceObjective || 'Melhore a clareza das instruções, mantendo variáveis {{}} intactas'}
          disabled={disabled}
        />
      </div>
      <button
        type="button"
        onClick={() => setExpanded((prev) => !prev)}
        className="absolute top-1.5 right-1.5 p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
        title={expanded ? 'Recolher' : 'Expandir'}
      >
        <ChevronsUpDown className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

// ========== Helpers ==========

function extractVariables(template: string): string[] {
  const matches = template.match(/\{\{?\s*(\w+)\s*\}?\}/g) || [];
  const vars = matches.map((m) => m.replace(/[{}]/g, '').trim());
  return [...new Set(vars)];
}

const PROVIDER_OPTIONS = [
  { value: 'watsonx', label: 'IBM WatsonX' },
  { value: 'openai', label: 'OpenAI (GPT)' },
];

const AGENT_TYPE_OPTIONS = [
  { value: 'generator', label: 'Gerador de Conteudo' },
  { value: 'validator', label: 'Validador de Conteudo' },
  { value: 'analyzer', label: 'Analisador de Exemplos' },
  { value: 'refiner', label: 'Refinador com Feedback' },
];

const AGENT_TYPE_LABELS: Record<string, { label: string; color: string }> = {
  generator: { label: 'Gerador', color: 'bg-blue-100 text-blue-700' },
  validator: { label: 'Validador', color: 'bg-amber-100 text-amber-700' },
  analyzer: { label: 'Analisador', color: 'bg-purple-100 text-purple-700' },
  refiner: { label: 'Refinador', color: 'bg-green-100 text-green-700' },
};

const DEFAULT_NEW_AGENT: Record<string, unknown> = {
  name: '',
  description: '',
  agent_type: 'generator',
  system_prompt: '',
  user_prompt_template: '',
  llm_provider: 'watsonx',
  model_name: 'mistralai/mistral-medium-2505',
  temperature: 0.7,
  max_tokens: 4000,
  use_rag: true,
  rag_query_template: '',
  rag_top_k: 5,
  rag_similarity_threshold: 0.7,
  is_active: true,
};

// ========== Agent Form Fields (shared between create and edit) ==========

function AgentFormFields({
  form,
  updateField,
  showAgentType = false,
}: {
  form: Record<string, unknown>;
  updateField: (field: string, value: unknown) => void;
  showAgentType?: boolean;
}) {
  const userPromptVars = extractVariables((form.user_prompt_template as string) || '');

  return (
    <div className="space-y-5">
      {/* Nome + Descrição + Tipo */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label className="text-xs font-medium">Nome *</Label>
          <Input
            value={(form.name as string) || ''}
            onChange={(e) => updateField('name', e.target.value)}
            className="text-sm"
            placeholder="Ex: Gerador Seção 1 - Descrição"
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs font-medium">Descrição</Label>
          <Input
            value={(form.description as string) || ''}
            onChange={(e) => updateField('description', e.target.value)}
            className="text-sm"
          />
        </div>
      </div>

      {showAgentType && (
        <div className="space-y-1.5 max-w-xs">
          <Label className="text-xs font-medium">Tipo do Agente</Label>
          <Select
            value={(form.agent_type as string) || 'generator'}
            onValueChange={(val) => updateField('agent_type', val)}
          >
            <SelectTrigger className="text-sm">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {AGENT_TYPE_OPTIONS.map((t) => (
                <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Prompts */}
      <Separator />
      <div className="space-y-3">
        <h4 className="text-sm font-semibold flex items-center gap-2">
          <Sparkles className="h-4 w-4" />
          Prompts
        </h4>
        <div className="space-y-1.5">
          <Label className="text-xs font-medium">System Prompt *</Label>
          <ExpandableTextarea
            value={(form.system_prompt as string) || ''}
            onChange={(val) => updateField('system_prompt', val)}
            placeholder="Instrucoes do sistema para o agente..."
            enhanceContext="system prompt de agente de blueprint jurídico"
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs font-medium">User Prompt Template *</Label>
          <ExpandableTextarea
            value={(form.user_prompt_template as string) || ''}
            onChange={(val) => updateField('user_prompt_template', val)}
            placeholder="Template do prompt do usuario. Use {{variavel}} para placeholders."
            enhanceContext="user prompt template de agente de blueprint jurídico"
          />
          {userPromptVars.length > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap mt-1">
              <span className="text-xs text-muted-foreground">Variaveis:</span>
              {userPromptVars.map((v) => (
                <Badge key={v} variant="secondary" className="text-xs font-mono">
                  {`{${v}}`}
                </Badge>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* LLM Config */}
      <Separator />
      <div className="space-y-3">
        <h4 className="text-sm font-semibold">Configuração LLM</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="space-y-1.5">
            <Label className="text-xs font-medium">Provider</Label>
            <Select
              value={(form.llm_provider as string) || 'watsonx'}
              onValueChange={(val) => updateField('llm_provider', val)}
            >
              <SelectTrigger className="text-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PROVIDER_OPTIONS.map((p) => (
                  <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs font-medium">Modelo</Label>
            <Input
              value={(form.model_name as string) || ''}
              onChange={(e) => updateField('model_name', e.target.value)}
              className="text-sm font-mono"
              placeholder="mistralai/mistral-medium-2505"
            />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs font-medium">Temperature ({String(form.temperature ?? 0.7)})</Label>
            <Input
              type="number"
              min={0}
              max={2}
              step={0.05}
              value={form.temperature as number ?? 0.7}
              onChange={(e) => updateField('temperature', parseFloat(e.target.value) || 0)}
              className="text-sm"
            />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs font-medium">Max Tokens</Label>
            <Input
              type="number"
              min={1}
              max={32000}
              step={100}
              value={form.max_tokens as number ?? 4000}
              onChange={(e) => updateField('max_tokens', parseInt(e.target.value) || 4000)}
              className="text-sm"
            />
          </div>
        </div>
      </div>

      {/* RAG Config */}
      <Separator />
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold">Configuração RAG</h4>
          <div className="flex items-center gap-2">
            <Label className="text-xs text-muted-foreground">Usar RAG</Label>
            <Switch
              checked={(form.use_rag as boolean) ?? false}
              onCheckedChange={(val) => updateField('use_rag', val)}
            />
          </div>
        </div>
        {(form.use_rag as boolean) && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-1.5 md:col-span-3">
              <Label className="text-xs font-medium">Query Template</Label>
              <div className="relative">
                <Textarea
                  value={(form.rag_query_template as string) || ''}
                  onChange={(e) => updateField('rag_query_template', e.target.value)}
                  rows={2}
                  className="text-sm font-mono pr-32"
                  placeholder="Template para busca na KB..."
                />
                <div className="absolute top-1 right-1">
                  <AIEnhanceButton
                    value={(form.rag_query_template as string) || ''}
                    onEnhance={(text) => updateField('rag_query_template', text)}
                    context="template de query RAG para base de conhecimento jurídica"
                    objective="Melhore a clareza da query, mantendo variáveis {{}} intactas"
                  />
                </div>
              </div>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs font-medium">Top K</Label>
              <Input
                type="number"
                min={1}
                max={20}
                value={form.rag_top_k as number ?? 5}
                onChange={(e) => updateField('rag_top_k', parseInt(e.target.value) || 5)}
                className="text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs font-medium">Threshold Similaridade</Label>
              <Input
                type="number"
                min={0}
                max={1}
                step={0.05}
                value={form.rag_similarity_threshold as number ?? 0.7}
                onChange={(e) => updateField('rag_similarity_threshold', parseFloat(e.target.value) || 0.7)}
                className="text-sm"
              />
            </div>
          </div>
        )}
      </div>

      {/* Ativo */}
      <Separator />
      <div className="flex items-center gap-2">
        <Switch
          checked={(form.is_active as boolean) ?? true}
          onCheckedChange={(val) => updateField('is_active', val)}
        />
        <Label className="text-sm">Agente ativo</Label>
      </div>
    </div>
  );
}

// ========== AgentCard ==========

function AgentCard({
  agent,
  isEditing,
  onStartEdit,
  onCancelEdit,
  onSave,
  onDelete,
  isSaving,
}: {
  agent: SectionAgentConfigDetail;
  isEditing: boolean;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  onSave: (data: Record<string, unknown>) => void;
  onDelete: () => void;
  isSaving: boolean;
}) {
  const [form, setForm] = useState<Record<string, unknown>>({});

  const startEditing = () => {
    setForm({
      name: agent.name,
      description: agent.description,
      system_prompt: agent.system_prompt,
      user_prompt_template: agent.user_prompt_template,
      llm_provider: agent.llm_provider,
      model_name: agent.model_name,
      temperature: agent.temperature,
      max_tokens: agent.max_tokens,
      use_rag: agent.use_rag,
      rag_query_template: agent.rag_query_template,
      rag_top_k: agent.rag_top_k,
      rag_similarity_threshold: agent.rag_similarity_threshold,
      is_active: agent.is_active,
    });
    onStartEdit();
  };

  const updateField = (field: string, value: unknown) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    const changed: Record<string, unknown> = {};
    for (const [key, val] of Object.entries(form)) {
      if (val !== (agent as unknown as Record<string, unknown>)[key]) {
        changed[key] = val;
      }
    }
    if (Object.keys(changed).length === 0) {
      onCancelEdit();
      return;
    }
    onSave(changed);
  };

  const typeInfo = AGENT_TYPE_LABELS[agent.agent_type] || { label: agent.agent_type, color: 'bg-gray-100 text-gray-700' };

  // --- View Mode ---
  if (!isEditing) {
    return (
      <Card className="hover:ring-1 hover:ring-primary/30 transition-all">
        <CardContent className="py-3 px-4">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0 flex-1">
              <Bot className="h-4 w-4 shrink-0 text-muted-foreground" />
              <span className="font-medium text-sm truncate">{agent.name}</span>
              <Badge variant="outline" className={`text-xs shrink-0 ${typeInfo.color}`}>
                {typeInfo.label}
              </Badge>
              <Badge variant="secondary" className="text-xs shrink-0">
                {agent.model_name.split('/').pop()}
              </Badge>
              {!agent.is_active && (
                <Badge variant="destructive" className="text-xs shrink-0">Inativo</Badge>
              )}
            </div>
            <div className="flex items-center gap-1 shrink-0">
              <Button variant="ghost" size="sm" onClick={startEditing}>
                <Pencil className="h-3.5 w-3.5 mr-1" />
                Editar
              </Button>
              <Button variant="ghost" size="sm" onClick={onDelete} className="text-destructive hover:text-destructive">
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // --- Edit Mode ---
  return (
    <Card className="ring-1 ring-primary/60">
      <CardContent className="py-4 px-5">
        <AgentFormFields form={form} updateField={updateField} />

        {/* Actions */}
        <div className="flex justify-end gap-2 pt-4">
          <Button variant="outline" size="sm" onClick={onCancelEdit} disabled={isSaving}>
            <X className="h-3.5 w-3.5 mr-1" />
            Cancelar
          </Button>
          <Button size="sm" onClick={handleSave} disabled={isSaving}>
            {isSaving ? (
              <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" />
            ) : (
              <Save className="h-3.5 w-3.5 mr-1" />
            )}
            Salvar
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ========== Create Agent Dialog ==========

function CreateAgentDialog({
  open,
  onOpenChange,
  onCreate,
  isCreating,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreate: (data: Record<string, unknown>) => void;
  isCreating: boolean;
}) {
  const [form, setForm] = useState<Record<string, unknown>>({ ...DEFAULT_NEW_AGENT });

  const updateField = (field: string, value: unknown) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleCreate = () => {
    onCreate(form);
  };

  const handleOpenChange = (val: boolean) => {
    if (val) {
      setForm({ ...DEFAULT_NEW_AGENT });
    }
    onOpenChange(val);
  };

  const isValid = !!(form.name as string)?.trim() && !!(form.system_prompt as string)?.trim() && !!(form.user_prompt_template as string)?.trim();

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Plus className="h-5 w-5" />
            Novo Agente
          </DialogTitle>
          <DialogDescription className="sr-only">Criar novo agente para o blueprint</DialogDescription>
        </DialogHeader>

        <AgentFormFields form={form} updateField={updateField} showAgentType />

        <DialogFooter className="pt-4">
          <Button variant="outline" onClick={() => handleOpenChange(false)} disabled={isCreating}>
            Cancelar
          </Button>
          <Button onClick={handleCreate} disabled={isCreating || !isValid}>
            {isCreating ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Plus className="h-4 w-4 mr-2" />
            )}
            Criar Agente
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ========== Main Component ==========

export function AgentsConfigStep({ blueprint }: AgentsConfigStepProps) {
  const { toast } = useToast();
  const {
    agents, total, isLoading,
    updateAgent, isUpdating,
    createAgent, isCreating,
    deleteAgent, isDeleting,
  } = useBlueprintAgents(blueprint.id);
  const [editingAgentId, setEditingAgentId] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<SectionAgentConfigDetail | null>(null);

  // Agrupar agentes por seção
  const sectionGroups = useMemo<SectionAgentGroup[]>(() => {
    if (!blueprint.sections || agents.length === 0) return [];

    const groups: SectionAgentGroup[] = [];

    for (const section of blueprint.sections) {
      const group: SectionAgentGroup = {
        sectionNumber: section.section_number,
        sectionName: section.section_name,
        sectionId: section.id,
        generatorAgent: null,
        validatorAgent: null,
        subSections: [],
      };

      for (const agent of agents) {
        for (const link of agent.linked_sections) {
          if (link.section_id === section.id) {
            if (link.role === 'generator') group.generatorAgent = agent;
            if (link.role === 'validator') group.validatorAgent = agent;
          }
        }
      }

      if (section.sub_sections) {
        for (const sub of section.sub_sections) {
          let subAgent: SectionAgentConfigDetail | null = null;
          for (const agent of agents) {
            for (const link of agent.linked_sub_sections) {
              if (link.sub_section_id === sub.id) {
                subAgent = agent;
              }
            }
          }
          if (subAgent) {
            group.subSections.push({
              subNumber: sub.sub_number,
              subName: sub.sub_name,
              subId: sub.id,
              generatorAgent: subAgent,
            });
          }
        }
      }

      if (group.generatorAgent || group.validatorAgent || group.subSections.length > 0) {
        groups.push(group);
      }
    }

    return groups.sort((a, b) => a.sectionNumber - b.sectionNumber);
  }, [blueprint.sections, agents]);

  // Agentes avulsos (não vinculados a nenhuma seção - criados pelo usuário e ainda não linkados)
  const unlinkedAgents = useMemo(() => {
    return agents.filter(
      (a) => a.linked_sections.length === 0 && a.linked_sub_sections.length === 0
    );
  }, [agents]);

  const handleSave = async (agentId: string, data: Record<string, unknown>) => {
    try {
      await updateAgent({ agentId, data });
      setEditingAgentId(null);
      toast({ title: 'Agente atualizado', description: 'As alterações foram salvas.' });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Erro ao salvar agente';
      toast({ title: 'Erro', description: message, variant: 'destructive' });
    }
  };

  const handleCreate = async (data: Record<string, unknown>) => {
    try {
      await createAgent(data);
      setCreateDialogOpen(false);
      toast({ title: 'Agente criado', description: 'O novo agente foi criado. Vincule-o a uma seção na etapa "Seções".' });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Erro ao criar agente';
      toast({ title: 'Erro', description: message, variant: 'destructive' });
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteAgent(deleteTarget.id);
      setDeleteTarget(null);
      if (editingAgentId === deleteTarget.id) setEditingAgentId(null);
      toast({ title: 'Agente excluido', description: `"${deleteTarget.name}" foi removido.` });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Erro ao excluir agente';
      toast({ title: 'Erro', description: message, variant: 'destructive' });
    }
  };

  // Loading
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Carregando agentes...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-bold flex items-center gap-2">
            <Bot className="h-5 w-5" />
            Configuração dos Agentes
            {total > 0 && <Badge variant="secondary" className="ml-1">{total}</Badge>}
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Crie, edite ou remova agentes de IA. Vincule-os as secoes na etapa &quot;Secoes&quot;.
          </p>
        </div>
        <Button onClick={() => setCreateDialogOpen(true)} size="sm">
          <Plus className="h-4 w-4 mr-1" />
          Novo Agente
        </Button>
      </div>

      {/* Empty state */}
      {total === 0 && (
        <div className="text-center py-16 border-2 border-dashed rounded-lg">
          <Bot className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-medium mb-1">Nenhum agente vinculado</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Crie um agente ou vincule agentes existentes as secoes na etapa &quot;Secoes&quot;.
          </p>
          <Button variant="outline" onClick={() => setCreateDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-1" />
            Criar primeiro agente
          </Button>
        </div>
      )}

      {/* Accordion por seção */}
      {sectionGroups.length > 0 && (
        <Accordion type="multiple" defaultValue={sectionGroups.map((g) => g.sectionId)} className="space-y-2">
          {sectionGroups.map((group) => (
            <AccordionItem key={group.sectionId} value={group.sectionId} className="border rounded-lg">
              <AccordionTrigger className="px-4 py-3 hover:no-underline">
                <div className="flex items-center gap-3 text-left">
                  <span className="font-semibold text-sm">
                    Seção {group.sectionNumber} - {group.sectionName}
                  </span>
                  <div className="flex gap-1.5">
                    {group.generatorAgent && (
                      <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-200">
                        <Sparkles className="h-3 w-3 mr-1" />
                        Gerador
                      </Badge>
                    )}
                    {group.validatorAgent && (
                      <Badge variant="outline" className="text-xs bg-amber-50 text-amber-700 border-amber-200">
                        <ShieldCheck className="h-3 w-3 mr-1" />
                        Validador
                      </Badge>
                    )}
                    {group.subSections.length > 0 && (
                      <Badge variant="outline" className="text-xs">
                        {group.subSections.length} sub
                      </Badge>
                    )}
                  </div>
                </div>
              </AccordionTrigger>
              <AccordionContent className="px-4 pb-4 space-y-3">
                {group.generatorAgent && (
                  <AgentCard
                    agent={group.generatorAgent}
                    isEditing={editingAgentId === group.generatorAgent.id}
                    onStartEdit={() => setEditingAgentId(group.generatorAgent!.id)}
                    onCancelEdit={() => setEditingAgentId(null)}
                    onSave={(data) => handleSave(group.generatorAgent!.id, data)}
                    onDelete={() => setDeleteTarget(group.generatorAgent)}
                    isSaving={isUpdating}
                  />
                )}
                {group.validatorAgent && (
                  <AgentCard
                    agent={group.validatorAgent}
                    isEditing={editingAgentId === group.validatorAgent.id}
                    onStartEdit={() => setEditingAgentId(group.validatorAgent!.id)}
                    onCancelEdit={() => setEditingAgentId(null)}
                    onSave={(data) => handleSave(group.validatorAgent!.id, data)}
                    onDelete={() => setDeleteTarget(group.validatorAgent)}
                    isSaving={isUpdating}
                  />
                )}
                {group.subSections.length > 0 && (
                  <>
                    <Separator className="my-2" />
                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Sub-secoes
                    </p>
                    {group.subSections.map((sub) => (
                      sub.generatorAgent && (
                        <div key={sub.subId}>
                          <p className="text-xs text-muted-foreground mb-1.5 ml-1">
                            {sub.subNumber} - {sub.subName}
                          </p>
                          <AgentCard
                            agent={sub.generatorAgent}
                            isEditing={editingAgentId === sub.generatorAgent.id}
                            onStartEdit={() => setEditingAgentId(sub.generatorAgent!.id)}
                            onCancelEdit={() => setEditingAgentId(null)}
                            onSave={(data) => handleSave(sub.generatorAgent!.id, data)}
                            onDelete={() => setDeleteTarget(sub.generatorAgent)}
                            isSaving={isUpdating}
                          />
                        </div>
                      )
                    ))}
                  </>
                )}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      )}

      {/* Agentes avulsos (criados mas não vinculados a seções) */}
      {unlinkedAgents.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-muted-foreground flex items-center gap-2">
            Agentes sem vinculo
            <Badge variant="outline" className="text-xs">{unlinkedAgents.length}</Badge>
          </h3>
          <p className="text-xs text-muted-foreground">
            Estes agentes foram criados mas ainda nao estao vinculados a nenhuma secao. Vincule-os na etapa &quot;Secoes&quot;.
          </p>
          {unlinkedAgents.map((agent) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              isEditing={editingAgentId === agent.id}
              onStartEdit={() => setEditingAgentId(agent.id)}
              onCancelEdit={() => setEditingAgentId(null)}
              onSave={(data) => handleSave(agent.id, data)}
              onDelete={() => setDeleteTarget(agent)}
              isSaving={isUpdating}
            />
          ))}
        </div>
      )}

      {/* Create Dialog */}
      <CreateAgentDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onCreate={handleCreate}
        isCreating={isCreating}
      />

      {/* Delete Confirmation */}
      <AlertDialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir agente</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja excluir <strong>&quot;{deleteTarget?.name}&quot;</strong>?
              {deleteTarget && (deleteTarget.linked_sections.length > 0 || deleteTarget.linked_sub_sections.length > 0) && (
                <span className="block mt-2 text-destructive">
                  Este agente esta vinculado a {deleteTarget.linked_sections.length} secao(oes)
                  {deleteTarget.linked_sub_sections.length > 0 && ` e ${deleteTarget.linked_sub_sections.length} sub-secao(oes)`}.
                  Os vinculos serao removidos.
                </span>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Trash2 className="h-4 w-4 mr-2" />}
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
