'use client';

import { useState, useCallback, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { Checkbox } from '@/components/ui/checkbox';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  GitBranch,
  Plus,
  Play,
  ChevronRight,
  ChevronUp,
  ChevronDown,
  CheckCircle2,
  Circle,
  Pause,
  XCircle,
  Loader2,
  Trash2,
  Pencil,
  GripVertical,
  Eye,
  Clock,
  FileText,
  User,
  Link2,
  ListChecks,
  ArrowRight,
  Ban,
  History,
  Search,
  Sparkles,
  Wand2,
  Info,
} from 'lucide-react';
import {
  useWorkflowTemplates,
  useWorkflowExecutions,
  useCreateWorkflowTemplate,
  useUpdateWorkflowTemplate,
  useDeleteWorkflowTemplate,
  useStartWorkflow,
  useAdvanceWorkflowStep,
  useUpdateWorkflowExecution,
  type WorkflowTemplate,
  type WorkflowExecution,
  type WorkflowStep,
} from '@/hooks/use-workflows';
import api from '@/lib/api';
import { toast } from 'sonner';

// ── Extended Step type for the builder ──

interface ExtendedStep {
  name: string;
  description: string;
  order: number;
  auto_advance: boolean;
  deadline_days: number | null;
  assigned_role: string;
  required_documents: string[];
  checklist: string[];
}

function toExtendedStep(step: WorkflowStep, idx: number): ExtendedStep {
  return {
    name: step.name,
    description: step.description,
    order: idx,
    auto_advance: step.auto_advance,
    deadline_days: step.deadline_days,
    assigned_role: (step as any).assigned_role || '',
    required_documents: (step as any).required_documents || [],
    checklist: (step as any).checklist || [],
  };
}

function fromExtendedStep(step: ExtendedStep): WorkflowStep & Record<string, any> {
  return {
    name: step.name,
    description: step.description,
    order: step.order,
    auto_advance: step.auto_advance,
    deadline_days: step.deadline_days,
    assigned_role: step.assigned_role,
    required_documents: step.required_documents,
    checklist: step.checklist,
  };
}

// ── Helpers ──

const specialtyLabels: Record<string, string> = {
  civel: 'Cível',
  criminal: 'Criminal',
  trabalhista: 'Trabalhista',
  tributario: 'Tributário',
  administrativo: 'Administrativo',
  previdenciario: 'Previdenciário',
  familia: 'Família e Sucessões',
  empresarial: 'Empresarial',
  ambiental: 'Ambiental',
  consumidor: 'Consumidor',
  imobiliario: 'Imobiliário',
  outros: 'Outros',
};

const roleLabels: Record<string, string> = {
  advogado: 'Advogado',
  estagiario: 'Estagiário',
  secretaria: 'Secretária',
  paralegal: 'Paralegal',
  socio: 'Sócio',
  perito: 'Perito',
  outro: 'Outro',
};

const statusConfig: Record<string, { label: string; className: string; icon: React.ComponentType<{ className?: string }> }> = {
  active: { label: 'Ativo', className: 'bg-green-100 text-green-800 border-green-200', icon: Play },
  paused: { label: 'Pausado', className: 'bg-yellow-100 text-yellow-800 border-yellow-200', icon: Pause },
  completed: { label: 'Concluído', className: 'bg-blue-100 text-blue-800 border-blue-200', icon: CheckCircle2 },
  cancelled: { label: 'Cancelado', className: 'bg-red-100 text-red-700 border-red-200', icon: XCircle },
};

function StatusBadge({ status }: { status: string }) {
  const cfg = statusConfig[status] ?? { label: status, className: '', icon: Circle };
  return <Badge variant="outline" className={cfg.className}>{cfg.label}</Badge>;
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('pt-BR');
}

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

// ── Cases hook (inline for linking) ──

function useCases() {
  return useQuery({
    queryKey: ['cases-list'],
    queryFn: async () => {
      const res = await api.get('/api/v1/processos/', { params: { page_size: 200 } });
      const data = res.data;
      return (data.results || data) as { id: string; titulo: string; numero_processo?: string }[];
    },
  });
}

// ── Step Card (Visual Builder) ──

function StepCard({
  step,
  index,
  totalSteps,
  onUpdate,
  onRemove,
  onMoveUp,
  onMoveDown,
}: {
  step: ExtendedStep;
  index: number;
  totalSteps: number;
  onUpdate: (step: ExtendedStep) => void;
  onRemove: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
}) {
  const [newDoc, setNewDoc] = useState('');
  const [newCheckItem, setNewCheckItem] = useState('');

  return (
    <Card className="shadow-sm ring-1 ring-primary/20">
      <CardHeader className="py-3 px-4">
        <div className="flex items-center gap-2">
          <div className="flex flex-col gap-0.5">
            <Button variant="ghost" size="icon" className="h-5 w-5" onClick={onMoveUp} disabled={index === 0} aria-label="Mover etapa para cima">
              <ChevronUp className="h-3 w-3" />
            </Button>
            <Button variant="ghost" size="icon" className="h-5 w-5" onClick={onMoveDown} disabled={index === totalSteps - 1} aria-label="Mover etapa para baixo">
              <ChevronDown className="h-3 w-3" />
            </Button>
          </div>
          <GripVertical className="h-4 w-4 text-muted-foreground" />
          <div className="h-7 w-7 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-bold shrink-0">
            {index + 1}
          </div>
          <Input
            value={step.name}
            onChange={(e) => onUpdate({ ...step, name: e.target.value })}
            placeholder="Nome da etapa"
            className="font-medium h-8"
          />
          <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0" onClick={onRemove} aria-label="Remover etapa">
            <Trash2 className="h-3.5 w-3.5 text-destructive" />
          </Button>
        </div>
        {/* Summary badges showing what this step requires */}
        <div className="flex items-center gap-2 mt-1.5 ml-[72px] flex-wrap">
          {step.assigned_role && (
            <Badge variant="secondary" className="text-[10px] gap-1">
              <User className="h-2.5 w-2.5" /> {roleLabels[step.assigned_role] || step.assigned_role}
            </Badge>
          )}
          {step.deadline_days && (
            <Badge variant="outline" className="text-[10px] gap-1">
              <Clock className="h-2.5 w-2.5" /> {step.deadline_days} dias
            </Badge>
          )}
          {step.required_documents.length > 0 && (
            <Badge variant="outline" className="text-[10px] gap-1 border-amber-300 text-amber-700 dark:text-amber-400">
              <FileText className="h-2.5 w-2.5" /> {step.required_documents.length} doc(s)
            </Badge>
          )}
          {step.checklist.length > 0 && (
            <Badge variant="outline" className="text-[10px] gap-1 border-blue-300 text-blue-700 dark:text-blue-400">
              <ListChecks className="h-2.5 w-2.5" /> {step.checklist.length} item(ns)
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="px-4 pb-4 pt-0 space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <Label className="text-xs">Descrição</Label>
            <Textarea
              value={step.description}
              onChange={(e) => onUpdate({ ...step, description: e.target.value })}
              placeholder="O que deve ser feito nesta etapa..."
              rows={2}
              className="text-sm"
            />
          </div>
          <div className="space-y-2">
            <div>
              <Label className="text-xs">Responsável</Label>
              <Select value={step.assigned_role} onValueChange={(v) => onUpdate({ ...step, assigned_role: v })}>
                <SelectTrigger className="h-8 text-sm">
                  <SelectValue placeholder="Selecione..." />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(roleLabels).map(([k, v]) => (
                    <SelectItem key={k} value={k}>{v}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-xs">Prazo estimado (dias)</Label>
              <Input
                type="number"
                min={1}
                value={step.deadline_days ?? ''}
                onChange={(e) => onUpdate({ ...step, deadline_days: e.target.value ? parseInt(e.target.value) : null })}
                className="h-8 text-sm"
                placeholder="Ex: 15"
              />
            </div>
          </div>
        </div>

        {/* Required Documents */}
        <div>
          <Label className="text-xs flex items-center gap-1"><FileText className="h-3 w-3" /> Documentos necessários</Label>
          <div className="flex flex-wrap gap-1 mt-1">
            {step.required_documents.map((doc, i) => (
              <Badge key={i} variant="secondary" className="text-xs gap-1">
                {doc}
                <button
                  onClick={() => onUpdate({ ...step, required_documents: step.required_documents.filter((_, j) => j !== i) })}
                  className="ml-1 hover:text-destructive"
                >
                  &times;
                </button>
              </Badge>
            ))}
          </div>
          <div className="flex gap-1 mt-1">
            <Input
              value={newDoc}
              onChange={(e) => setNewDoc(e.target.value)}
              placeholder="Nome do documento"
              className="h-7 text-xs flex-1"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && newDoc.trim()) {
                  e.preventDefault();
                  onUpdate({ ...step, required_documents: [...step.required_documents, newDoc.trim()] });
                  setNewDoc('');
                }
              }}
            />
            <Button
              variant="outline"
              size="sm"
              className="h-7 text-xs px-2"
              onClick={() => {
                if (newDoc.trim()) {
                  onUpdate({ ...step, required_documents: [...step.required_documents, newDoc.trim()] });
                  setNewDoc('');
                }
              }}
            >
              <Plus className="h-3 w-3" />
            </Button>
          </div>
        </div>

        {/* Checklist */}
        <div>
          <Label className="text-xs flex items-center gap-1"><ListChecks className="h-3 w-3" /> Checklist</Label>
          <div className="space-y-1 mt-1">
            {step.checklist.map((item, i) => (
              <div key={i} className="flex items-center gap-1.5 text-xs">
                <span className="text-muted-foreground">&#9745;</span>
                <span className="flex-1">{item}</span>
                <button
                  onClick={() => onUpdate({ ...step, checklist: step.checklist.filter((_, j) => j !== i) })}
                  className="text-muted-foreground hover:text-destructive"
                >
                  &times;
                </button>
              </div>
            ))}
          </div>
          <div className="flex gap-1 mt-1">
            <Input
              value={newCheckItem}
              onChange={(e) => setNewCheckItem(e.target.value)}
              placeholder="Item do checklist"
              className="h-7 text-xs flex-1"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && newCheckItem.trim()) {
                  e.preventDefault();
                  onUpdate({ ...step, checklist: [...step.checklist, newCheckItem.trim()] });
                  setNewCheckItem('');
                }
              }}
            />
            <Button
              variant="outline"
              size="sm"
              className="h-7 text-xs px-2"
              onClick={() => {
                if (newCheckItem.trim()) {
                  onUpdate({ ...step, checklist: [...step.checklist, newCheckItem.trim()] });
                  setNewCheckItem('');
                }
              }}
            >
              <Plus className="h-3 w-3" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ── Visual Timeline Preview ──

function TimelinePreview({ steps }: { steps: ExtendedStep[] }) {
  if (!steps.length) return <p className="text-sm text-muted-foreground text-center py-4">Nenhuma etapa adicionada</p>;

  const totalDays = steps.reduce((sum, s) => sum + (s.deadline_days || 0), 0);

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
        <span>Fluxo Visual</span>
        {totalDays > 0 && <span>Duração estimada: {totalDays} dias</span>}
      </div>
      <div className="flex items-center gap-0 overflow-x-auto pb-2">
        {steps.map((step, idx) => (
          <div key={idx} className="flex items-center">
            <div className="flex flex-col items-center min-w-[120px] max-w-[160px]">
              <div className="h-10 w-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold">
                {idx + 1}
              </div>
              <div className="mt-1 text-center">
                <p className="text-xs font-medium truncate max-w-[140px]">{step.name}</p>
                {step.assigned_role && (
                  <p className="text-[10px] text-muted-foreground">{roleLabels[step.assigned_role] || step.assigned_role}</p>
                )}
                {step.deadline_days && (
                  <p className="text-[10px] text-muted-foreground">{step.deadline_days}d</p>
                )}
              </div>
            </div>
            {idx < steps.length - 1 && (
              <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0 mx-1" />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── AI Workflow Helper ──

function parseAISteps(answer: string): ExtendedStep[] {
  // Try to parse structured steps from AI response
  // The AI may return numbered steps, JSON, or plain text
  const steps: ExtendedStep[] = [];

  // Try JSON parse first
  try {
    const jsonMatch = answer.match(/\[[\s\S]*?\]/);
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0]);
      if (Array.isArray(parsed)) {
        return parsed.map((item: any, idx: number) => ({
          name: item.name || item.nome || item.title || item.titulo || `Etapa ${idx + 1}`,
          description: item.description || item.descricao || item.desc || '',
          order: idx,
          auto_advance: item.auto_advance || false,
          deadline_days: item.deadline_days || item.prazo || item.dias || null,
          assigned_role: item.assigned_role || item.responsavel || item.role || '',
          required_documents: item.required_documents || item.documentos || [],
          checklist: item.checklist || item.items || [],
        }));
      }
    }
  } catch {}

  // Fallback: parse numbered lines like "1. Name - Description"
  const lines = answer.split('\n').filter((l) => l.trim());
  const stepRegex = /^\s*(?:\d+[\.\)\-]|[-*])\s*\*{0,2}(.+?)\*{0,2}\s*(?:[-:]\s*(.*))?$/;
  for (const line of lines) {
    const match = line.match(stepRegex);
    if (match) {
      steps.push({
        name: match[1].trim().replace(/\*+/g, ''),
        description: match[2]?.trim().replace(/\*+/g, '') || '',
        order: steps.length,
        auto_advance: false,
        deadline_days: null,
        assigned_role: '',
        required_documents: [],
        checklist: [],
      });
    }
  }

  if (steps.length === 0) {
    // Last resort: create a single step with the whole text
    steps.push({
      name: 'Etapa 1',
      description: answer.slice(0, 500),
      order: 0,
      auto_advance: false,
      deadline_days: null,
      assigned_role: '',
      required_documents: [],
      checklist: [],
    });
  }

  return steps;
}

function AIWorkflowInput({
  onStepsGenerated,
  existingSteps,
  specialty,
  templateName,
}: {
  onStepsGenerated: (steps: ExtendedStep[], name?: string, description?: string) => void;
  existingSteps?: ExtendedStep[];
  specialty: string;
  templateName?: string;
}) {
  const [prompt, setPrompt] = useState('');
  const [aiResult, setAiResult] = useState<string | null>(null);
  const isEditing = !!existingSteps && existingSteps.length > 0;

  const aiMutation = useMutation({
    mutationFn: async () => {
      const contextData = isEditing
        ? {
            existing_steps: existingSteps.map((s) => ({
              name: s.name,
              description: s.description,
              assigned_role: s.assigned_role,
              deadline_days: s.deadline_days,
              required_documents: s.required_documents,
              checklist: s.checklist,
            })),
            template_name: templateName || '',
            specialty,
          }
        : { specialty };

      const question = isEditing
        ? `Tenho um workflow jurídico chamado "${templateName}" na área de ${specialtyLabels[specialty] || specialty} com as seguintes etapas existentes. O usuário quer modificar: "${prompt}".
Retorne as etapas MODIFICADAS como um array JSON com campos: name, description, assigned_role (advogado|estagiario|secretaria|paralegal|socio|perito|outro), deadline_days (número), required_documents (array de strings), checklist (array de strings). Retorne SOMENTE o JSON array.`
        : `Crie um workflow jurídico para a área de ${specialtyLabels[specialty] || specialty} com base na seguinte descrição: "${prompt}".
Retorne as etapas como um array JSON com campos: name, description, assigned_role (advogado|estagiario|secretaria|paralegal|socio|perito|outro), deadline_days (número), required_documents (array de strings), checklist (array de strings). Retorne SOMENTE o JSON array.`;

      const res = await api.post('/api/v1/processos/copilot/analisar/', {
        context_type: 'workflow',
        context_data: contextData,
        question,
      });
      return res.data;
    },
    onSuccess: (data) => {
      setAiResult(data.answer);
      const parsedSteps = parseAISteps(data.answer);
      if (parsedSteps.length > 0) {
        onStepsGenerated(parsedSteps);
        toast.success(`${parsedSteps.length} etapas ${isEditing ? 'atualizadas' : 'geradas'} pela IA!`);
      }
    },
    onError: () => toast.error('Erro ao gerar workflow com IA'),
  });

  return (
    <div className="space-y-3 rounded-lg border border-amber-200 bg-amber-50/50 dark:bg-amber-950/20 dark:border-amber-800 p-4">
      <div className="flex items-center gap-2 text-sm font-medium">
        <Sparkles className="h-4 w-4 text-amber-500" />
        {isEditing ? 'Editar com IA' : 'Criar com IA'}
      </div>
      <Textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder={
          isEditing
            ? 'Descreva as alterações desejadas... Ex: "Adicione uma etapa de perícia antes da audiência" ou "Reduza os prazos em 5 dias"'
            : 'Descreva o workflow em linguagem natural... Ex: "Processo trabalhista de reclamação com audiência, perícia e execução" ou "Ação de despejo com notificação, citação e sentença"'
        }
        rows={3}
        className="text-sm bg-white dark:bg-background"
      />
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground">
          A IA vai gerar as etapas automaticamente. Você pode editá-las depois.
        </p>
        <Button
          size="sm"
          onClick={() => aiMutation.mutate()}
          disabled={!prompt.trim() || aiMutation.isPending}
          className="gap-1.5"
        >
          {aiMutation.isPending ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Wand2 className="h-3.5 w-3.5" />
          )}
          {isEditing ? 'Aplicar Alterações' : 'Gerar Etapas'}
        </Button>
      </div>
    </div>
  );
}

// ── Process Flow Indicator ──

function ProcessFlowIndicator({ specialty, stepsCount }: { specialty: string; stepsCount: number }) {
  const phases = [
    { label: 'Petição Inicial', phase: 'inicio' },
    { label: 'Citação / Notificação', phase: 'citacao' },
    { label: 'Instrução', phase: 'instrucao' },
    { label: 'Audiência', phase: 'audiencia' },
    { label: 'Decisão / Sentença', phase: 'decisao' },
    { label: 'Recurso', phase: 'recurso' },
    { label: 'Execução', phase: 'execução' },
  ];

  return (
    <div className="rounded-lg border bg-muted/30 p-3">
      <p className="text-xs font-medium text-muted-foreground mb-2 flex items-center gap-1">
        <Info className="h-3 w-3" /> Fases do processo ({specialtyLabels[specialty] || specialty})
      </p>
      <div className="flex items-center gap-0 overflow-x-auto pb-1">
        {phases.map((phase, idx) => (
          <div key={phase.phase} className="flex items-center">
            <div className="flex flex-col items-center min-w-[80px]">
              <div className="h-6 w-6 rounded-full bg-muted text-muted-foreground flex items-center justify-center text-[10px] font-medium">
                {idx + 1}
              </div>
              <p className="text-[9px] text-muted-foreground text-center mt-0.5 max-w-[75px] leading-tight">{phase.label}</p>
            </div>
            {idx < phases.length - 1 && (
              <ArrowRight className="h-3 w-3 text-muted-foreground/40 shrink-0" />
            )}
          </div>
        ))}
      </div>
      {stepsCount > 0 && (
        <p className="text-[10px] text-muted-foreground mt-1.5">
          Seu workflow possui {stepsCount} etapa(s) que serão executadas dentro dessas fases processuais.
        </p>
      )}
    </div>
  );
}

// ── Template Editor Dialog ──

function TemplateEditorDialog({
  template,
  open,
  onOpenChange,
  initialAIMode,
  onAIModeConsumed,
}: {
  template: WorkflowTemplate | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initialAIMode?: boolean;
  onAIModeConsumed?: () => void;
}) {
  const isNew = !template;
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [specialty, setSpecialty] = useState('civel');
  const [steps, setSteps] = useState<ExtendedStep[]>([]);
  const [editorTab, setEditorTab] = useState<'edit' | 'preview'>('edit');
  const [showAIInput, setShowAIInput] = useState(false);

  const createTemplate = useCreateWorkflowTemplate();
  const updateTemplate = useUpdateWorkflowTemplate();

  // Reset form when template changes
  useEffect(() => {
    if (template) {
      setName(template.name);
      setDescription(template.description);
      setSpecialty(template.specialty);
      setSteps(template.steps.map((s, i) => toExtendedStep(s, i)));
    } else {
      setName('');
      setDescription('');
      setSpecialty('civel');
      setSteps([]);
    }
    setEditorTab('edit');
    setShowAIInput(!!initialAIMode);
    if (initialAIMode) onAIModeConsumed?.();
  }, [template, open]);

  const addStep = () => {
    setSteps([...steps, {
      name: `Etapa ${steps.length + 1}`,
      description: '',
      order: steps.length,
      auto_advance: false,
      deadline_days: null,
      assigned_role: '',
      required_documents: [],
      checklist: [],
    }]);
  };

  const updateStep = (index: number, updated: ExtendedStep) => {
    const newSteps = [...steps];
    newSteps[index] = updated;
    setSteps(newSteps);
  };

  const removeStep = (index: number) => {
    setSteps(steps.filter((_, i) => i !== index).map((s, i) => ({ ...s, order: i })));
  };

  const moveStep = (from: number, to: number) => {
    if (to < 0 || to >= steps.length) return;
    const newSteps = [...steps];
    const [moved] = newSteps.splice(from, 1);
    newSteps.splice(to, 0, moved);
    setSteps(newSteps.map((s, i) => ({ ...s, order: i })));
  };

  const handleSave = () => {
    const payload = {
      name,
      description,
      specialty,
      steps: steps.map((s, i) => fromExtendedStep({ ...s, order: i })),
      is_active: true,
    };

    if (isNew) {
      createTemplate.mutate(payload, { onSuccess: () => onOpenChange(false) });
    } else {
      updateTemplate.mutate(
        { id: template.id, data: payload },
        { onSuccess: () => onOpenChange(false) }
      );
    }
  };

  const isSaving = createTemplate.isPending || updateTemplate.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>{isNew ? 'Novo Template de Workflow' : `Editar: ${template?.name}`}</DialogTitle>
          <DialogDescription className="sr-only">
            {isNew ? 'Formulário para criar novo template' : 'Formulário para editar template'}
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="flex-1 -mx-6 px-6" style={{ maxHeight: 'calc(90vh - 160px)' }}>
          <div className="space-y-4 pb-4">
            {/* Template metadata */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <Label>Nome</Label>
                <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Ex: Workflow Trabalhista Padrão" />
              </div>
              <div>
                <Label>Especialidade</Label>
                <Select value={specialty} onValueChange={setSpecialty}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {Object.entries(specialtyLabels).map(([k, v]) => (
                      <SelectItem key={k} value={k}>{v}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Descrição</Label>
                <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Descrição breve..." />
              </div>
            </div>

            <Separator />

            {/* Process Flow Indicator */}
            <ProcessFlowIndicator specialty={specialty} stepsCount={steps.length} />

            {/* AI Input Section */}
            {showAIInput && (
              <AIWorkflowInput
                existingSteps={isNew ? undefined : steps}
                specialty={specialty}
                templateName={name}
                onStepsGenerated={(newSteps, newName, newDesc) => {
                  setSteps(newSteps);
                  if (newName) setName(newName);
                  if (newDesc) setDescription(newDesc);
                  setShowAIInput(false);
                }}
              />
            )}

            {/* Edit / Preview toggle */}
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold">Etapas ({steps.length})</h3>
              <div className="flex gap-1">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowAIInput(!showAIInput)}
                  className="gap-1"
                >
                  <Sparkles className="h-3 w-3 text-amber-500" />
                  {steps.length > 0 ? 'Editar com IA' : 'Criar com IA'}
                </Button>
                <Button
                  variant={editorTab === 'edit' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setEditorTab('edit')}
                >
                  <Pencil className="h-3 w-3 mr-1" /> Editar
                </Button>
                <Button
                  variant={editorTab === 'preview' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setEditorTab('preview')}
                >
                  <Eye className="h-3 w-3 mr-1" /> Visualizar
                </Button>
              </div>
            </div>

            {editorTab === 'edit' ? (
              <div className="space-y-3">
                {steps.map((step, idx) => (
                  <StepCard
                    key={idx}
                    step={step}
                    index={idx}
                    totalSteps={steps.length}
                    onUpdate={(s) => updateStep(idx, s)}
                    onRemove={() => removeStep(idx)}
                    onMoveUp={() => moveStep(idx, idx - 1)}
                    onMoveDown={() => moveStep(idx, idx + 1)}
                  />
                ))}
                <Button variant="outline" onClick={addStep} className="w-full border-dashed">
                  <Plus className="h-4 w-4 mr-2" /> Adicionar Etapa
                </Button>
              </div>
            ) : (
              <Card className="p-4">
                <TimelinePreview steps={steps} />
                <Separator className="my-3" />
                {/* Step detail list in preview */}
                <Accordion type="multiple" className="w-full">
                  {steps.map((step, idx) => (
                    <AccordionItem key={idx} value={`step-${idx}`}>
                      <AccordionTrigger className="text-sm">
                        <div className="flex items-center gap-2 text-left">
                          <span className="h-6 w-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-bold shrink-0">{idx + 1}</span>
                          <span className="font-medium">{step.name}</span>
                          {step.assigned_role && <Badge variant="secondary" className="text-[10px]">{roleLabels[step.assigned_role] || step.assigned_role}</Badge>}
                          {step.deadline_days && <Badge variant="outline" className="text-[10px]">{step.deadline_days}d</Badge>}
                        </div>
                      </AccordionTrigger>
                      <AccordionContent>
                        <div className="space-y-2 pl-8">
                          {step.description && <p className="text-sm text-muted-foreground">{step.description}</p>}
                          {step.required_documents.length > 0 && (
                            <div>
                              <p className="text-xs font-medium flex items-center gap-1"><FileText className="h-3 w-3" /> Documentos:</p>
                              <ul className="list-disc list-inside text-xs text-muted-foreground ml-2">
                                {step.required_documents.map((d, i) => <li key={i}>{d}</li>)}
                              </ul>
                            </div>
                          )}
                          {step.checklist.length > 0 && (
                            <div>
                              <p className="text-xs font-medium flex items-center gap-1"><ListChecks className="h-3 w-3" /> Checklist:</p>
                              <ul className="text-xs text-muted-foreground ml-2 space-y-0.5">
                                {step.checklist.map((c, i) => <li key={i} className="flex items-center gap-1"><Checkbox disabled className="h-3 w-3" /> {c}</li>)}
                              </ul>
                            </div>
                          )}
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              </Card>
            )}
          </div>
        </ScrollArea>

        <DialogFooter className="pt-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancelar</Button>
          <Button onClick={handleSave} disabled={!name || isSaving}>
            {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isNew ? 'Criar' : 'Salvar'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── Start Workflow Dialog (with case linking) ──

function StartWorkflowDialog() {
  const [open, setOpen] = useState(false);
  const [templateId, setTemplateId] = useState('');
  const [caseId, setCaseId] = useState('');
  const [caseSearch, setCaseSearch] = useState('');
  const { data: templates } = useWorkflowTemplates({ active: 'true' });
  const { data: cases } = useCases();
  const startWorkflow = useStartWorkflow();

  const filteredCases = cases?.filter((c) => {
    if (!caseSearch) return true;
    const q = caseSearch.toLowerCase();
    return c.titulo?.toLowerCase().includes(q) || c.numero_processo?.toLowerCase().includes(q) || c.id.toLowerCase().includes(q);
  }) ?? [];

  const selectedCase = cases?.find((c) => c.id === caseId);

  const handleSubmit = () => {
    startWorkflow.mutate(
      { template: templateId, case: caseId },
      {
        onSuccess: () => {
          setOpen(false);
          setTemplateId('');
          setCaseId('');
          setCaseSearch('');
        },
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button><Play className="mr-2 h-4 w-4" /> Iniciar Workflow</Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Iniciar Workflow em Caso</DialogTitle>
          <DialogDescription className="sr-only">Selecione o template e caso para iniciar o workflow</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>Template</Label>
            <Select value={templateId} onValueChange={setTemplateId}>
              <SelectTrigger><SelectValue placeholder="Selecione um template" /></SelectTrigger>
              <SelectContent>
                {templates?.map((t) => (
                  <SelectItem key={t.id} value={t.id}>
                    {t.name} ({t.specialty_display || specialtyLabels[t.specialty] || t.specialty})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="flex items-center gap-1"><Link2 className="h-3 w-3" /> Vincular ao Caso</Label>
            <div className="relative mt-1">
              <Search className="absolute left-2 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
              <Input
                value={caseSearch}
                onChange={(e) => { setCaseSearch(e.target.value); setCaseId(''); }}
                placeholder="Buscar por título, número ou ID..."
                className="pl-7"
              />
            </div>
            {(caseSearch && !caseId) && (
              <ScrollArea className="mt-1 max-h-40 border rounded-md">
                <div className="p-1">
                  {filteredCases.length === 0 ? (
                    <p className="text-xs text-muted-foreground text-center py-2">Nenhum caso encontrado</p>
                  ) : (
                    filteredCases.slice(0, 20).map((c) => (
                      <button
                        key={c.id}
                        onClick={() => { setCaseId(c.id); setCaseSearch(c.titulo || c.id); }}
                        className="w-full text-left px-2 py-1.5 text-sm rounded hover:bg-accent"
                      >
                        <span className="font-medium">{c.titulo}</span>
                        {c.numero_processo && (
                          <span className="text-xs text-muted-foreground ml-2">{c.numero_processo}</span>
                        )}
                      </button>
                    ))
                  )}
                </div>
              </ScrollArea>
            )}
            {selectedCase && caseId && (
              <div className="mt-1 flex items-center gap-2 text-sm">
                <Badge variant="outline" className="text-xs"><Link2 className="h-3 w-3 mr-1" />{selectedCase.titulo}</Badge>
                <Button variant="ghost" size="sm" className="h-6 px-1 text-xs" onClick={() => { setCaseId(''); setCaseSearch(''); }}>Limpar</Button>
              </div>
            )}
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>Cancelar</Button>
          <Button onClick={handleSubmit} disabled={!templateId || !caseId || startWorkflow.isPending}>
            {startWorkflow.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Iniciar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── Execution Detail View ──

function ExecutionDetailView({ execution }: { execution: WorkflowExecution }) {
  const advanceStep = useAdvanceWorkflowStep();
  const updateExecution = useUpdateWorkflowExecution();
  const [notes, setNotes] = useState('');
  const [detailTab, setDetailTab] = useState<'steps' | 'history'>('steps');

  const { data: templates } = useWorkflowTemplates();
  const templateData = templates?.find((t) => t.id === execution.template);
  const steps = templateData?.steps || [];

  const progressPercent = execution.total_steps > 0
    ? Math.round(((execution.status === 'completed' ? execution.total_steps : execution.current_step) / execution.total_steps) * 100)
    : 0;

  const handleAdvance = () => {
    advanceStep.mutate(
      { id: execution.id, notes },
      { onSuccess: () => setNotes('') }
    );
  };

  const handlePause = () => {
    updateExecution.mutate({ id: execution.id, data: { status: 'paused' } as any });
  };

  const handleResume = () => {
    updateExecution.mutate({ id: execution.id, data: { status: 'active' } as any });
  };

  const handleCancel = () => {
    updateExecution.mutate({ id: execution.id, data: { status: 'cancelled' } as any });
  };

  return (
    <div className="space-y-4">
      {/* Progress bar */}
      <div className="space-y-1">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Progresso</span>
          <span className="font-medium">{progressPercent}%</span>
        </div>
        <Progress value={progressPercent} className="h-2.5" />
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>Etapa {Math.min(execution.current_step + 1, execution.total_steps)}/{execution.total_steps}</span>
          <span>Iniciado em {formatDate(execution.started_at)}</span>
        </div>
      </div>

      {/* Action buttons */}
      {execution.status !== 'completed' && execution.status !== 'cancelled' && (
        <div className="flex items-center gap-2 flex-wrap">
          {execution.status === 'active' && (
            <>
              <div className="flex items-center gap-2 flex-1">
                <Input
                  placeholder="Notas da etapa (opcional)"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="flex-1 h-8 text-sm"
                />
                <Button size="sm" onClick={handleAdvance} disabled={advanceStep.isPending}>
                  {advanceStep.isPending ? <Loader2 className="mr-1 h-3 w-3 animate-spin" /> : <ChevronRight className="mr-1 h-3 w-3" />}
                  Avançar
                </Button>
              </div>
              <Button size="sm" variant="outline" onClick={handlePause} disabled={updateExecution.isPending}>
                <Pause className="mr-1 h-3 w-3" /> Pausar
              </Button>
            </>
          )}
          {execution.status === 'paused' && (
            <Button size="sm" onClick={handleResume} disabled={updateExecution.isPending}>
              <Play className="mr-1 h-3 w-3" /> Retomar
            </Button>
          )}
          <Button size="sm" variant="destructive" onClick={handleCancel} disabled={updateExecution.isPending}>
            <Ban className="mr-1 h-3 w-3" /> Cancelar
          </Button>
        </div>
      )}

      {/* Tabs: Steps vs History */}
      <div className="flex gap-1 border-b">
        <button
          onClick={() => setDetailTab('steps')}
          className={`px-3 py-1.5 text-sm font-medium border-b-2 -mb-px ${detailTab === 'steps' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`}
        >
          Etapas
        </button>
        <button
          onClick={() => setDetailTab('history')}
          className={`px-3 py-1.5 text-sm font-medium border-b-2 -mb-px flex items-center gap-1 ${detailTab === 'history' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`}
        >
          <History className="h-3 w-3" /> Histórico
        </button>
      </div>

      {detailTab === 'steps' ? (
        /* Step-by-step view with details */
        <div className="space-y-2">
          {steps.map((step, idx) => {
            const isCompleted = idx < execution.current_step;
            const isCurrent = idx === execution.current_step;
            const isWorkflowDone = execution.status === 'completed';
            const extStep = toExtendedStep(step, idx);
            const historyEntry = execution.step_history?.find((h) => h.step === idx);

            return (
              <div key={idx} className="flex items-start gap-3">
                <div className="flex flex-col items-center">
                  <div className={`h-8 w-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                    isCompleted || (isWorkflowDone && isCurrent)
                      ? 'bg-green-500 text-white'
                      : isCurrent
                      ? 'bg-primary text-primary-foreground ring-2 ring-primary/30'
                      : 'bg-muted text-muted-foreground'
                  }`}>
                    {isCompleted || (isWorkflowDone && isCurrent) ? (
                      <CheckCircle2 className="h-4 w-4" />
                    ) : (
                      idx + 1
                    )}
                  </div>
                  {idx < steps.length - 1 && (
                    <div className={`w-0.5 h-8 ${isCompleted ? 'bg-green-500' : 'bg-muted'}`} />
                  )}
                </div>
                <div className={`flex-1 pb-2 rounded-md p-2 ${isCurrent && !isWorkflowDone ? 'bg-primary/5 border border-primary/20' : ''}`}>
                  <div className="flex items-center gap-2">
                    <p className={`text-sm font-medium ${isCurrent && !isWorkflowDone ? 'text-primary' : ''}`}>
                      {step.name}
                    </p>
                    {extStep.assigned_role && (
                      <Badge variant="secondary" className="text-[10px]">
                        <User className="h-2.5 w-2.5 mr-0.5" />{roleLabels[extStep.assigned_role] || extStep.assigned_role}
                      </Badge>
                    )}
                    {isCompleted && historyEntry?.completed_at && (
                      <span className="text-[10px] text-muted-foreground">
                        <Clock className="h-2.5 w-2.5 inline mr-0.5" />
                        {formatDateTime(historyEntry.completed_at)}
                      </span>
                    )}
                  </div>
                  {step.description && (
                    <p className="text-xs text-muted-foreground mt-0.5">{step.description}</p>
                  )}
                  {step.deadline_days && (
                    <p className="text-xs text-muted-foreground"><Clock className="h-3 w-3 inline mr-0.5" />Prazo: {step.deadline_days} dias</p>
                  )}
                  {/* Show documents and checklist for current step */}
                  {isCurrent && !isWorkflowDone && (
                    <div className="mt-2 space-y-2">
                      {extStep.required_documents.length > 0 && (
                        <div>
                          <p className="text-xs font-medium flex items-center gap-1"><FileText className="h-3 w-3" /> Documentos necessários:</p>
                          <div className="flex flex-wrap gap-1 mt-0.5">
                            {extStep.required_documents.map((d, i) => (
                              <Badge key={i} variant="outline" className="text-[10px]">{d}</Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      {extStep.checklist.length > 0 && (
                        <div>
                          <p className="text-xs font-medium flex items-center gap-1"><ListChecks className="h-3 w-3" /> Checklist:</p>
                          <div className="space-y-1 mt-0.5">
                            {extStep.checklist.map((item, i) => (
                              <label key={i} className="flex items-center gap-1.5 text-xs cursor-pointer">
                                <Checkbox className="h-3.5 w-3.5" />
                                <span>{item}</span>
                              </label>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                  {/* Show notes from history */}
                  {historyEntry?.notes && (
                    <p className="text-xs text-muted-foreground mt-1 italic">Nota: {historyEntry.notes}</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* History view */
        <div className="space-y-2">
          {(!execution.step_history || execution.step_history.length === 0) ? (
            <p className="text-sm text-muted-foreground text-center py-4">Nenhum histórico registrado</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[60px]">Etapa</TableHead>
                  <TableHead>Nome</TableHead>
                  <TableHead>Iniciado</TableHead>
                  <TableHead>Concluído</TableHead>
                  <TableHead>Notas</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {execution.step_history.map((entry, idx) => {
                  const stepName = steps[entry.step]?.name || `Etapa ${entry.step + 1}`;
                  return (
                    <TableRow key={idx}>
                      <TableCell className="text-center font-mono text-xs">{entry.step + 1}</TableCell>
                      <TableCell className="text-sm">{stepName}</TableCell>
                      <TableCell className="text-xs">{formatDateTime(entry.started_at)}</TableCell>
                      <TableCell className="text-xs">{entry.completed_at ? formatDateTime(entry.completed_at) : <Badge variant="outline" className="text-[10px]">Em andamento</Badge>}</TableCell>
                      <TableCell className="text-xs text-muted-foreground max-w-[200px] truncate">{entry.notes || '-'}</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </div>
      )}
    </div>
  );
}

// ── Linked Cases Info ──

function TemplateLinkedCases({ templateId }: { templateId: string }) {
  const { data: executions } = useWorkflowExecutions();
  const linked = executions?.filter((e) => e.template === templateId) || [];

  if (linked.length === 0) return null;

  return (
    <div className="mt-2">
      <p className="text-xs text-muted-foreground mb-1">Casos vinculados ({linked.length}):</p>
      <div className="flex flex-wrap gap-1">
        {linked.slice(0, 5).map((e) => (
          <Badge key={e.id} variant="outline" className="text-[10px] gap-1">
            <Link2 className="h-2.5 w-2.5" />
            {e.case_titulo}
            <StatusBadge status={e.status} />
          </Badge>
        ))}
        {linked.length > 5 && (
          <Badge variant="secondary" className="text-[10px]">+{linked.length - 5} mais</Badge>
        )}
      </div>
    </div>
  );
}

// ── Main Page ──

export default function WorkflowsPage() {
  const [activeTab, setActiveTab] = useState('templates');
  const [expandedExec, setExpandedExec] = useState<string | null>(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<WorkflowTemplate | null>(null);
  const [openWithAI, setOpenWithAI] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const { data: templates, isLoading: loadingTemplates } = useWorkflowTemplates();
  const { data: executions, isLoading: loadingExecs } = useWorkflowExecutions();
  const deleteTemplate = useDeleteWorkflowTemplate();

  const openNewTemplate = () => {
    setEditingTemplate(null);
    setEditorOpen(true);
  };

  const openEditTemplate = (template: WorkflowTemplate) => {
    setEditingTemplate(template);
    setEditorOpen(true);
  };

  const filteredExecutions = executions?.filter((e) => {
    if (statusFilter === 'all') return true;
    return e.status === statusFilter;
  }) ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <GitBranch className="h-6 w-6" /> Workflows
          </h1>
          <p className="text-muted-foreground">Gerencie templates e execuções de workflows automatizados</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="templates">Templates</TabsTrigger>
          <TabsTrigger value="executions">
            Execuções
            {executions && executions.filter((e) => e.status === 'active').length > 0 && (
              <Badge variant="default" className="ml-1.5 h-5 w-5 p-0 flex items-center justify-center text-[10px]">
                {executions.filter((e) => e.status === 'active').length}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        {/* Templates Tab */}
        <TabsContent value="templates" className="space-y-4">
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => {
                setEditingTemplate(null);
                setOpenWithAI(true);
                setEditorOpen(true);
              }}
              className="gap-1.5"
            >
              <Sparkles className="h-4 w-4 text-amber-500" /> Criar com IA
            </Button>
            <Button onClick={openNewTemplate}>
              <Plus className="mr-2 h-4 w-4" /> Novo Template
            </Button>
          </div>

          {loadingTemplates ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-16 w-full" />)}
            </div>
          ) : !templates?.length ? (
            <Card>
              <CardContent className="py-10 text-center text-muted-foreground">
                Nenhum template de workflow encontrado. Crie o primeiro!
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-3">
              {templates.map((t) => (
                <Card
                  key={t.id}
                  className="cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => openEditTemplate(t)}
                >
                  <CardHeader className="py-3 px-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 flex-1">
                        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                          <GitBranch className="h-5 w-5 text-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <CardTitle className="text-base">{t.name}</CardTitle>
                            <Badge variant="outline" className="text-xs">{t.specialty_display || specialtyLabels[t.specialty] || t.specialty}</Badge>
                            <Badge variant={t.is_active ? 'default' : 'secondary'} className="text-xs">
                              {t.is_active ? 'Ativo' : 'Inativo'}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-3 text-xs text-muted-foreground mt-0.5">
                            <span>{t.steps_count} etapas</span>
                            <span>Criado em {formatDate(t.created_at)}</span>
                            {t.description && <span className="truncate max-w-[300px]">{t.description}</span>}
                          </div>
                          <TemplateLinkedCases templateId={t.id} />
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          title="Editar com IA"
                          aria-label="Editar com IA"
                          onClick={(e) => {
                            e.stopPropagation();
                            setEditingTemplate(t);
                            setOpenWithAI(true);
                            setEditorOpen(true);
                          }}
                        >
                          <Sparkles className="h-4 w-4 text-amber-500" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          aria-label="Editar template"
                          onClick={(e) => {
                            e.stopPropagation();
                            openEditTemplate(t);
                          }}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          aria-label="Excluir template"
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteTemplate.mutate(t.id);
                          }}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Executions Tab */}
        <TabsContent value="executions" className="space-y-4">
          <div className="flex items-center justify-between gap-2">
            <div className="flex gap-1">
              {['all', 'active', 'paused', 'completed', 'cancelled'].map((s) => (
                <Button
                  key={s}
                  variant={statusFilter === s ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setStatusFilter(s)}
                  className="text-xs"
                >
                  {s === 'all' ? 'Todos' : statusConfig[s]?.label || s}
                  {s !== 'all' && executions && (
                    <span className="ml-1 opacity-70">({executions.filter((e) => e.status === s).length})</span>
                  )}
                </Button>
              ))}
            </div>
            <StartWorkflowDialog />
          </div>

          {loadingExecs ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-16 w-full" />)}
            </div>
          ) : !filteredExecutions.length ? (
            <Card>
              <CardContent className="py-10 text-center text-muted-foreground">
                {statusFilter === 'all'
                  ? 'Nenhuma execução de workflow. Inicie um workflow em um caso!'
                  : `Nenhuma execução com status "${statusConfig[statusFilter]?.label || statusFilter}"`}
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {filteredExecutions.map((exec) => {
                const progressPercent = exec.total_steps > 0
                  ? Math.round(((exec.status === 'completed' ? exec.total_steps : exec.current_step) / exec.total_steps) * 100)
                  : 0;

                return (
                  <Card key={exec.id} className={expandedExec === exec.id ? 'ring-1 ring-primary/30' : ''}>
                    <CardHeader
                      className="cursor-pointer py-3"
                      onClick={() => setExpandedExec(expandedExec === exec.id ? null : exec.id)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <CardTitle className="text-base">{exec.template_name}</CardTitle>
                            <StatusBadge status={exec.status} />
                          </div>
                          <div className="flex items-center gap-3 text-xs text-muted-foreground mt-1">
                            <span className="flex items-center gap-1">
                              <Link2 className="h-3 w-3" /> {exec.case_titulo}
                            </span>
                            <span>Etapa {Math.min(exec.current_step + 1, exec.total_steps)}/{exec.total_steps}</span>
                            <span>Iniciado em {formatDate(exec.started_at)}</span>
                          </div>
                          <Progress value={progressPercent} className="h-1.5 mt-2 max-w-md" />
                        </div>
                        <ChevronRight className={`h-4 w-4 transition-transform shrink-0 ml-2 ${expandedExec === exec.id ? 'rotate-90' : ''}`} />
                      </div>
                    </CardHeader>
                    {expandedExec === exec.id && (
                      <CardContent className="pt-0">
                        <Separator className="mb-4" />
                        <ExecutionDetailView execution={exec} />
                      </CardContent>
                    )}
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Template Editor Dialog */}
      <TemplateEditorDialog
        template={editingTemplate}
        open={editorOpen}
        onOpenChange={setEditorOpen}
        initialAIMode={openWithAI}
        onAIModeConsumed={() => setOpenWithAI(false)}
      />
    </div>
  );
}
