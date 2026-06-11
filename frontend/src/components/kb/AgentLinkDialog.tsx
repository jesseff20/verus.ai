'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Loader2, FileText, AlertCircle } from 'lucide-react';
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';
import { useSectionAgents } from '@/hooks/use-section-agents';
import type { AgentKnowledgeBaseLink, KBSource, SectionAgent } from '@/types';

const PURPOSE_OPTIONS = [
  { value: 'reference', label: 'Referência Geral' },
  { value: 'examples', label: 'Exemplos Reais da Seção' },
  { value: 'evaluation', label: 'Padrões Avaliados (4+ estrelas)' },
  { value: 'normative', label: 'Normas e Legislação' },
  { value: 'context', label: 'Contexto do Usuário (sessão)' },
];

interface AgentLinkDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  kbName: string;
  editingLink: AgentKnowledgeBaseLink | null;
  sources: KBSource[];
  onSubmit: (data: {
    agent?: string;
    priority?: number;
    purpose?: string;
    instruction?: string;
    top_k?: number;
    min_similarity?: number;
    include_summary?: boolean;
    selected_sources?: string[];
  }) => void;
  isSubmitting: boolean;
}

export function AgentLinkDialog({
  open,
  onOpenChange,
  kbName,
  editingLink,
  sources,
  onSubmit,
  isSubmitting,
}: AgentLinkDialogProps) {
  const { data: agentsData } = useSectionAgents();
  const agents = agentsData?.agents || [];

  const [form, setForm] = useState({
    agent: '',
    priority: 0,
    purpose: 'reference',
    instruction: '',
    top_k: 5,
    min_similarity: 0.6,
    include_summary: false,
    selected_sources: [] as string[],
  });

  useEffect(() => {
    if (editingLink) {
      setForm({
        agent: editingLink.agent,
        priority: editingLink.priority,
        purpose: editingLink.purpose,
        instruction: editingLink.instruction,
        top_k: editingLink.top_k,
        min_similarity: editingLink.min_similarity,
        include_summary: editingLink.include_summary,
        selected_sources: editingLink.selected_sources || [],
      });
    } else {
      setForm({
        agent: '',
        priority: 0,
        purpose: 'reference',
        instruction: '',
        top_k: 5,
        min_similarity: 0.6,
        include_summary: false,
        selected_sources: [],
      });
    }
  }, [editingLink, open]);

  const handleSubmit = () => {
    if (editingLink) {
      const { agent: _agent, ...rest } = form;
      onSubmit(rest);
    } else {
      onSubmit(form);
    }
  };

  const toggleSource = (sourceName: string) => {
    setForm((prev) => {
      const current = prev.selected_sources;
      if (current.includes(sourceName)) {
        return { ...prev, selected_sources: current.filter((s) => s !== sourceName) };
      }
      return { ...prev, selected_sources: [...current, sourceName] };
    });
  };

  const selectAllSources = () => {
    setForm((prev) => ({
      ...prev,
      selected_sources: sources.map((s) => s.source_name),
    }));
  };

  const clearSources = () => {
    setForm((prev) => ({ ...prev, selected_sources: [] }));
  };

  const isEdit = !!editingLink;
  const allSelected = sources.length > 0 && form.selected_sources.length === sources.length;
  const noneSelected = form.selected_sources.length === 0;

  // Agrupar agentes por escopo (seção, sub-seção, sem vínculo)
  const SCOPE_LABELS: Record<string, string> = {
    section: 'Agentes de Seção',
    sub_section: 'Agentes de Sub-seção',
    unlinked: 'Sem vínculo',
  };
  const SCOPE_ORDER = ['section', 'sub_section', 'unlinked'];

  const grouped = agents.reduce<Record<string, SectionAgent[]>>((acc, agent) => {
    const scope = agent.agent_scope || 'unlinked';
    const key = SCOPE_LABELS[scope] || 'Sem vínculo';
    if (!acc[key]) acc[key] = [];
    acc[key].push(agent);
    return acc;
  }, {});

  // Ordenar grupos na ordem definida
  const sortedGroups = SCOPE_ORDER
    .map((s) => SCOPE_LABELS[s])
    .filter((label) => grouped[label])
    .map((label) => [label, grouped[label]] as [string, SectionAgent[]]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? 'Editar Vínculo' : 'Vincular Agente'}
          </DialogTitle>
          <DialogDescription>{kbName}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {!isEdit && (
            <div className="space-y-2">
              <Label>Agente *</Label>
              <Select
                value={form.agent}
                onValueChange={(v) => setForm({ ...form, agent: v })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione um agente" />
                </SelectTrigger>
                <SelectContent>
                  {sortedGroups.map(([groupLabel, groupAgents]) => (
                    <div key={groupLabel}>
                      <div className="px-2 py-1.5 text-xs font-bold text-muted-foreground border-b mb-1">
                        {groupLabel}
                      </div>
                      {groupAgents.map((agent) => (
                        <SelectItem key={agent.id} value={agent.id}>
                          <div className="flex flex-col">
                            <span>
                              {agent.name}
                              <span className="ml-1 text-xs text-muted-foreground">
                                ({agent.agent_type})
                              </span>
                            </span>
                            {agent.context_label && (
                              <span className="text-[11px] text-muted-foreground">
                                {agent.context_label}
                              </span>
                            )}
                          </div>
                        </SelectItem>
                      ))}
                    </div>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Prioridade</Label>
              <Input
                type="number"
                min={0}
                value={form.priority}
                onChange={(e) => setForm({ ...form, priority: parseInt(e.target.value) || 0 })}
              />
              <p className="text-xs text-muted-foreground">0 = maior prioridade</p>
            </div>

            <div className="space-y-2">
              <Label>Propósito</Label>
              <Select
                value={form.purpose}
                onValueChange={(v) => setForm({ ...form, purpose: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PURPOSE_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Instrução de Uso</Label>
            <div className="relative">
              <Textarea
                value={form.instruction}
                onChange={(e) => setForm({ ...form, instruction: e.target.value })}
                placeholder="Ex: Extraia o padrão de escrita destes exemplos reais..."
                rows={3}
                className="pr-32"
              />
              <div className="absolute top-1 right-1">
                <AIEnhanceButton
                  value={form.instruction}
                  onEnhance={(text) => setForm({ ...form, instruction: text })}
                  context="instrução de uso de base de conhecimento jurídica"
                />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Top K</Label>
              <Input
                type="number"
                min={1}
                max={20}
                value={form.top_k}
                onChange={(e) => setForm({ ...form, top_k: parseInt(e.target.value) || 5 })}
              />
            </div>

            <div className="space-y-2">
              <Label>Similaridade Min.</Label>
              <Input
                type="number"
                min={0}
                max={1}
                step={0.05}
                value={form.min_similarity}
                onChange={(e) => setForm({ ...form, min_similarity: parseFloat(e.target.value) || 0.6 })}
              />
            </div>

            <div className="space-y-2">
              <Label>Incluir Resumo</Label>
              <Select
                value={form.include_summary ? 'true' : 'false'}
                onValueChange={(v) => setForm({ ...form, include_summary: v === 'true' })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="false">Não</SelectItem>
                  <SelectItem value="true">Sim</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* ── Seleção de Fontes de Dados ── */}
          {sources.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Fontes de Dados</Label>
                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-6 text-xs"
                    onClick={selectAllSources}
                    disabled={allSelected}
                  >
                    Selecionar Todas
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-6 text-xs"
                    onClick={clearSources}
                    disabled={noneSelected}
                  >
                    Limpar
                  </Button>
                </div>
              </div>

              {noneSelected && (
                <div className="flex items-center gap-1.5 text-xs text-amber-600 bg-amber-50 rounded px-2 py-1.5">
                  <AlertCircle className="h-3 w-3 shrink-0" />
                  <span>Nenhuma fonte selecionada - o agente acessará todas as fontes desta KB.</span>
                </div>
              )}

              <div className="border rounded-md max-h-40 overflow-y-auto">
                {sources.map((source) => (
                  <label
                    key={source.source_name}
                    className="flex items-center gap-2 px-3 py-2 hover:bg-muted/50 cursor-pointer border-b last:border-b-0"
                  >
                    <Checkbox
                      checked={form.selected_sources.includes(source.source_name)}
                      onCheckedChange={() => toggleSource(source.source_name)}
                    />
                    <FileText className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                    <span className="text-sm truncate flex-1">{source.source_name}</span>
                    <Badge variant="outline" className="text-[10px] shrink-0">
                      {source.chunks_count} chunks
                    </Badge>
                  </label>
                ))}
              </div>

              <p className="text-xs text-muted-foreground">
                {form.selected_sources.length} de {sources.length} fonte{sources.length !== 1 ? 's' : ''} selecionada{form.selected_sources.length !== 1 ? 's' : ''}
              </p>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting || (!isEdit && !form.agent)}
          >
            {isSubmitting ? (
              <><Loader2 className="mr-2 h-4 w-4 animate-spin" />{isEdit ? 'Salvando...' : 'Vinculando...'}</>
            ) : (
              isEdit ? 'Salvar' : 'Vincular'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
