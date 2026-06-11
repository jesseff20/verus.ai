'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { AIInput } from '@/components/ui/ai-input';
import { AITextarea } from '@/components/ui/ai-textarea';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import {
  Clock,
  Plus,
  Pause,
  Play,
  Trash2,
  Edit,
  Calendar,
  Bell,
  Bot,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  AtSign,
  Briefcase,
  FileText,
  Link2,
} from 'lucide-react';
import { toast } from 'sonner';

// Types
interface Reminder {
  id: number;
  title: string;
  description: string;
  frequency: string;
  frequency_display: string;
  scheduled_date: string;
  end_date: string | null;
  custom_interval_days: number | null;
  related_case: string | null;
  related_case_title: string | null;
  copilot_prompt: string;
  link: string;
  status: string;
  status_display: string;
  last_triggered: string | null;
  trigger_count: number;
  notify_before_minutes: number;
  priority: string;
  priority_display: string;
  created_at: string;
  updated_at: string;
}

interface ReminderFormData {
  title: string;
  description: string;
  frequency: string;
  scheduled_date: string;
  end_date: string;
  custom_interval_days: number | null;
  copilot_prompt: string;
  link: string;
  priority: string;
  notify_before_minutes: number;
  related_case: string;
}

interface CaseOption {
  id: string;
  title: string;
  case_number: string;
}

interface MentionItem {
  type: 'case' | 'document' | 'route';
  label: string;
  value: string;
  icon: 'case' | 'doc' | 'link';
}

const SYSTEM_ROUTES: MentionItem[] = [
  { type: 'route', label: 'Dashboard', value: '/dashboard', icon: 'link' },
  { type: 'route', label: 'Processos', value: '/dashboard/processos', icon: 'link' },
  { type: 'route', label: 'Documentos', value: '/dashboard/documentos', icon: 'link' },
  { type: 'route', label: 'Calendario', value: '/dashboard/calendario', icon: 'link' },
  { type: 'route', label: 'Auditoria', value: '/dashboard/auditoria', icon: 'link' },
  { type: 'route', label: 'Lembretes', value: '/dashboard/reminders', icon: 'link' },
];

const FREQUENCY_OPTIONS = [
  { value: 'once', label: 'Uma vez' },
  { value: 'daily', label: 'Diário' },
  { value: 'weekly', label: 'Semanal' },
  { value: 'biweekly', label: 'Quinzenal' },
  { value: 'monthly', label: 'Mensal' },
  { value: 'quarterly', label: 'Trimestral' },
  { value: 'yearly', label: 'Anual' },
  { value: 'custom', label: 'Personalizado' },
];

const PRIORITY_OPTIONS = [
  { value: 'low', label: 'Baixa' },
  { value: 'medium', label: 'Média' },
  { value: 'high', label: 'Alta' },
  { value: 'urgent', label: 'Urgente' },
];

const STATUS_FILTERS = [
  { value: 'all', label: 'Todos' },
  { value: 'active', label: 'Ativos' },
  { value: 'paused', label: 'Pausados' },
  { value: 'completed', label: 'Concluídos' },
  { value: 'cancelled', label: 'Cancelados' },
];

const priorityColors: Record<string, string> = {
  low: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
  medium: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
  high: 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300',
  urgent: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
};

const statusColors: Record<string, string> = {
  active: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
  paused: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
  completed: 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400',
  cancelled: 'bg-red-100 text-red-500 dark:bg-red-900 dark:text-red-400',
};

const QUICK_TEMPLATES = [
  {
    label: 'Verificar prazo processual',
    data: {
      title: 'Verificar prazo processual',
      frequency: 'weekly',
      priority: 'high',
      description: 'Verificar prazos judiciais pendentes e providências necessárias.',
      copilot_prompt: 'Quais são os prazos judiciais que vencem esta semana e quais providências devo tomar?',
    },
  },
  {
    label: 'Revisar andamento do caso',
    data: {
      title: 'Revisar andamento dos casos ativos',
      frequency: 'daily',
      priority: 'medium',
      description: 'Revisar o andamento de todos os casos ativos.',
      copilot_prompt: 'Faça uma revisão geral dos meus casos ativos e indique quais precisam de atenção imediata.',
    },
  },
  {
    label: 'Relatório mensal',
    data: {
      title: 'Preparar relatório mensal',
      frequency: 'monthly',
      priority: 'medium',
      description: 'Preparar relatório mensal consolidado para clientes.',
      copilot_prompt: 'Ajude-me a preparar o relatório mensal de atividades jurídicas para os clientes.',
    },
  },
  {
    label: 'Lembrete de audiência',
    data: {
      title: 'Audiência agendada',
      frequency: 'once',
      priority: 'urgent',
      description: 'Preparar documentação e argumentos para a audiência.',
      copilot_prompt: 'Preciso me preparar para uma audiência. Ajude-me a revisar os pontos principais do caso e a documentação necessária.',
    },
  },
];

const emptyForm: ReminderFormData = {
  title: '',
  description: '',
  frequency: 'once',
  scheduled_date: '',
  end_date: '',
  custom_interval_days: null,
  copilot_prompt: '',
  link: '',
  priority: 'medium',
  notify_before_minutes: 30,
  related_case: '',
};

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function toLocalDatetimeValue(dateString?: string): string {
  if (!dateString) return '';
  const d = new Date(dateString);
  // Format to "YYYY-MM-DDTHH:mm" for datetime-local input
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export default function RemindersPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState('all');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingReminder, setEditingReminder] = useState<Reminder | null>(null);
  const [form, setForm] = useState<ReminderFormData>({ ...emptyForm });

  // Mention state
  const [showMentionPopup, setShowMentionPopup] = useState(false);
  const [mentionQuery, setMentionQuery] = useState('');
  const [mentionCursorPos, setMentionCursorPos] = useState(0);
  const [mentionStartPos, setMentionStartPos] = useState(0);
  const descriptionRef = useRef<HTMLTextAreaElement>(null);

  // Fetch cases for selector and mentions
  const { data: cases = [] } = useQuery<CaseOption[]>({
    queryKey: ['cases-for-reminders'],
    queryFn: async () => {
      const res = await api.get('/api/v1/processos/', { params: { page_size: 100 } });
      const results = res.data.results ?? res.data;
      return results.map((c: Record<string, unknown>) => ({
        id: c.id as string,
        title: (c.title || c.titulo || c.case_number || '') as string,
        case_number: (c.case_number || c.numero || '') as string,
      }));
    },
  });

  // Build mention items
  const mentionItems = useCallback((): MentionItem[] => {
    const items: MentionItem[] = [];
    const q = mentionQuery.toLowerCase();

    // Cases
    cases.forEach((c) => {
      const label = c.case_number ? `${c.case_number} - ${c.title}` : c.title;
      if (!q || label.toLowerCase().includes(q)) {
        items.push({ type: 'case', label, value: `[Caso: ${label}]`, icon: 'case' });
      }
    });

    // Routes
    SYSTEM_ROUTES.forEach((r) => {
      if (!q || r.label.toLowerCase().includes(q)) {
        items.push({ ...r, value: `[Rota: ${r.label}](${r.value})` });
      }
    });

    return items.slice(0, 10);
  }, [mentionQuery, cases]);

  const handleDescriptionChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    const cursorPos = e.target.selectionStart || 0;
    setForm({ ...form, description: value });

    // Check for @ trigger
    const textBeforeCursor = value.slice(0, cursorPos);
    const lastAtIdx = textBeforeCursor.lastIndexOf('@');

    if (lastAtIdx >= 0) {
      const textAfterAt = textBeforeCursor.slice(lastAtIdx + 1);
      // Only show popup if @ is at start or preceded by a space, and no space in the query
      const charBeforeAt = lastAtIdx > 0 ? value[lastAtIdx - 1] : ' ';
      if ((charBeforeAt === ' ' || charBeforeAt === '\n' || lastAtIdx === 0) && !textAfterAt.includes(' ')) {
        setShowMentionPopup(true);
        setMentionQuery(textAfterAt);
        setMentionStartPos(lastAtIdx);
        setMentionCursorPos(cursorPos);
        return;
      }
    }
    setShowMentionPopup(false);
  };

  const insertMention = (item: MentionItem) => {
    const before = form.description.slice(0, mentionStartPos);
    const after = form.description.slice(mentionCursorPos);
    const newValue = `${before}${item.value} ${after}`;
    setForm({ ...form, description: newValue });
    setShowMentionPopup(false);
    // Focus back on textarea
    setTimeout(() => {
      if (descriptionRef.current) {
        descriptionRef.current.focus();
        const pos = mentionStartPos + item.value.length + 1;
        descriptionRef.current.setSelectionRange(pos, pos);
      }
    }, 0);
  };

  const handleDescriptionKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (showMentionPopup && e.key === 'Escape') {
      setShowMentionPopup(false);
      e.preventDefault();
    }
  };

  // Fetch reminders
  const { data: reminders, isLoading } = useQuery<Reminder[]>({
    queryKey: ['reminders', statusFilter],
    queryFn: async () => {
      const params = statusFilter !== 'all' ? { status: statusFilter } : {};
      const res = await api.get('/api/v1/auth/reminders/', { params });
      return res.data.results ?? res.data;
    },
  });

  // Create
  const createMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v1/auth/reminders/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reminders'] });
      toast.success('Lembrete criado com sucesso!');
      closeDialog();
    },
    onError: () => toast.error('Erro ao criar lembrete.'),
  });

  // Update
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Record<string, unknown> }) =>
      api.put(`/api/v1/auth/reminders/${id}/`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reminders'] });
      toast.success('Lembrete atualizado!');
      closeDialog();
    },
    onError: () => toast.error('Erro ao atualizar lembrete.'),
  });

  // Delete
  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/api/v1/auth/reminders/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reminders'] });
      toast.success('Lembrete excluído.');
    },
    onError: () => toast.error('Erro ao excluir lembrete.'),
  });

  // Pause
  const pauseMutation = useMutation({
    mutationFn: (id: number) => api.post(`/api/v1/auth/reminders/${id}/pause/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reminders'] });
      toast.success('Lembrete pausado.');
    },
    onError: () => toast.error('Erro ao pausar lembrete.'),
  });

  // Resume
  const resumeMutation = useMutation({
    mutationFn: (id: number) => api.post(`/api/v1/auth/reminders/${id}/resume/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reminders'] });
      toast.success('Lembrete retomado.');
    },
    onError: () => toast.error('Erro ao retomar lembrete.'),
  });

  function closeDialog() {
    setIsDialogOpen(false);
    setEditingReminder(null);
    setForm({ ...emptyForm });
  }

  function openCreate(templateData?: Partial<ReminderFormData>) {
    const now = new Date();
    now.setHours(now.getHours() + 1, 0, 0, 0);
    setEditingReminder(null);
    setForm({
      ...emptyForm,
      scheduled_date: toLocalDatetimeValue(now.toISOString()),
      ...templateData,
    });
    setIsDialogOpen(true);
  }

  function openEdit(reminder: Reminder) {
    setEditingReminder(reminder);
    setForm({
      title: reminder.title,
      description: reminder.description,
      frequency: reminder.frequency,
      scheduled_date: toLocalDatetimeValue(reminder.scheduled_date),
      end_date: reminder.end_date ? toLocalDatetimeValue(reminder.end_date) : '',
      custom_interval_days: reminder.custom_interval_days,
      copilot_prompt: reminder.copilot_prompt,
      link: reminder.link,
      priority: reminder.priority,
      notify_before_minutes: reminder.notify_before_minutes,
      related_case: reminder.related_case || '',
    });
    setIsDialogOpen(true);
  }

  function handleSubmit() {
    if (!form.title.trim() || !form.scheduled_date) {
      toast.error('Título e data/hora são obrigatórios.');
      return;
    }

    const payload: Record<string, unknown> = {
      title: form.title,
      description: form.description,
      frequency: form.frequency,
      scheduled_date: new Date(form.scheduled_date).toISOString(),
      priority: form.priority,
      notify_before_minutes: form.notify_before_minutes,
      copilot_prompt: form.copilot_prompt,
      link: form.link,
    };

    if (form.end_date) {
      payload.end_date = new Date(form.end_date).toISOString();
    } else {
      payload.end_date = null;
    }

    if (form.frequency === 'custom' && form.custom_interval_days) {
      payload.custom_interval_days = form.custom_interval_days;
    } else {
      payload.custom_interval_days = null;
    }

    if (form.related_case) {
      payload.related_case = form.related_case;
    } else {
      payload.related_case = null;
    }

    if (editingReminder) {
      updateMutation.mutate({ id: editingReminder.id, data: payload });
    } else {
      createMutation.mutate(payload);
    }
  }

  const isSaving = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight flex items-center gap-2">
            <Bell className="h-7 w-7 sm:h-8 sm:w-8" />
            Lembretes
          </h1>
          <p className="text-muted-foreground text-sm sm:text-base">
            Gerencie seus lembretes e tarefas recorrentes
          </p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={(open) => { if (!open) closeDialog(); else setIsDialogOpen(true); }}>
          <DialogTrigger asChild>
            <Button onClick={() => openCreate()}>
              <Plus className="mr-2 h-4 w-4" />
              Novo Lembrete
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[600px] max-h-[90dvh] overflow-y-auto w-[calc(100%-2rem)] sm:w-full rounded-t-xl sm:rounded-lg">
            <DialogHeader>
              <DialogTitle>
                {editingReminder ? 'Editar Lembrete' : 'Novo Lembrete'}
              </DialogTitle>
              <DialogDescription>
                {editingReminder
                  ? 'Altere os dados do lembrete.'
                  : 'Crie um novo lembrete ou tarefa recorrente.'}
              </DialogDescription>
            </DialogHeader>

            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="title">Título *</Label>
                <AIInput
                  id="title"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  setValue={(v) => setForm({ ...form, title: v })}
                  placeholder="Ex: Verificar prazo Processo 123/2026"
                  aiContext="Título de um lembrete jurídico ou tarefa recorrente"
                  aiObjective="Sugerir um título claro e objetivo para o lembrete em português"
                />
              </div>

              {/* Case Selector */}
              <div className="grid gap-2">
                <Label htmlFor="related_case">Caso Vinculado (opcional)</Label>
                <Select
                  value={form.related_case || '_none'}
                  onValueChange={(v) => setForm({ ...form, related_case: v === '_none' ? '' : v })}
                >
                  <SelectTrigger id="related_case" className="min-h-[44px]">
                    <SelectValue placeholder="Selecione um caso" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="_none">Nenhum caso</SelectItem>
                    {cases.map((c) => (
                      <SelectItem key={c.id} value={c.id} className="py-2">
                        <span className="flex items-center gap-2">
                          <Briefcase className="h-3 w-3 text-muted-foreground inline" />
                          {c.case_number ? `${c.case_number} - ${c.title}` : c.title}
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {form.related_case && (
                  <p className="text-xs text-muted-foreground flex items-center gap-1">
                    <Briefcase className="h-3 w-3" />
                    Caso vinculado ao lembrete
                  </p>
                )}
              </div>

              {/* Description with @mention support */}
              <div className="grid gap-2 relative">
                <Label htmlFor="description">
                  Descrição
                  <span className="text-xs text-muted-foreground ml-2 font-normal">
                    (digite @ para referenciar)
                  </span>
                </Label>
                <AITextarea
                  ref={descriptionRef}
                  id="description"
                  value={form.description}
                  onChange={handleDescriptionChange}
                  onKeyDown={handleDescriptionKeyDown}
                  setValue={(v) => setForm({ ...form, description: v })}
                  placeholder="Detalhes do lembrete. Use @ para referenciar casos, documentos ou rotas."
                  rows={3}
                  aiContext="Descrição detalhada de um lembrete ou tarefa jurídica recorrente"
                  aiObjective="Melhorar ou completar a descrição do lembrete com linguagem jurídica clara"
                />
                {/* @Mention Popup */}
                {showMentionPopup && (
                  <div className="absolute top-full left-0 right-0 z-50 mt-1 max-h-[200px] overflow-y-auto rounded-md border bg-popover p-1 shadow-md">
                    {mentionItems().length === 0 ? (
                      <p className="text-xs text-muted-foreground p-2">Nenhum resultado</p>
                    ) : (
                      mentionItems().map((item, idx) => (
                        <button
                          key={`${item.type}-${idx}`}
                          type="button"
                          className="flex items-center gap-2 w-full rounded-sm px-2 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground cursor-pointer text-left"
                          onMouseDown={(e) => {
                            e.preventDefault();
                            insertMention(item);
                          }}
                        >
                          {item.icon === 'case' && <Briefcase className="h-3.5 w-3.5 text-blue-500 shrink-0" />}
                          {item.icon === 'doc' && <FileText className="h-3.5 w-3.5 text-green-500 shrink-0" />}
                          {item.icon === 'link' && <Link2 className="h-3.5 w-3.5 text-purple-500 shrink-0" />}
                          <span className="truncate">{item.label}</span>
                          <Badge variant="secondary" className="text-[10px] ml-auto shrink-0">
                            {item.type === 'case' ? 'Caso' : item.type === 'document' ? 'Doc' : 'Rota'}
                          </Badge>
                        </button>
                      ))
                    )}
                  </div>
                )}
                <p className="text-xs text-muted-foreground flex items-center gap-1">
                  <AtSign className="h-3 w-3" />
                  Use @ para inserir referências a casos ou rotas do sistema
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="scheduled_date">Data/Hora *</Label>
                  <Input
                    id="scheduled_date"
                    type="datetime-local"
                    value={form.scheduled_date}
                    onChange={(e) => setForm({ ...form, scheduled_date: e.target.value })}
                    className="min-h-[44px]"
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="frequency">Frequência</Label>
                  <Select
                    value={form.frequency}
                    onValueChange={(v) => setForm({ ...form, frequency: v })}
                  >
                    <SelectTrigger id="frequency" className="min-h-[44px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {FREQUENCY_OPTIONS.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value} className="py-3">
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {form.frequency === 'custom' && (
                <div className="grid gap-2">
                  <Label htmlFor="custom_interval">Intervalo personalizado (dias)</Label>
                  <Input
                    id="custom_interval"
                    type="number"
                    min={1}
                    value={form.custom_interval_days ?? ''}
                    onChange={(e) =>
                      setForm({ ...form, custom_interval_days: e.target.value ? parseInt(e.target.value) : null })
                    }
                    placeholder="Ex: 10"
                  />
                </div>
              )}

              {form.frequency !== 'once' && (
                <div className="grid gap-2">
                  <Label htmlFor="end_date">Data de término (opcional)</Label>
                  <Input
                    id="end_date"
                    type="datetime-local"
                    value={form.end_date}
                    onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                  />
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="priority">Prioridade</Label>
                  <Select
                    value={form.priority}
                    onValueChange={(v) => setForm({ ...form, priority: v })}
                  >
                    <SelectTrigger id="priority">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {PRIORITY_OPTIONS.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="notify_before">Notificar antes (min)</Label>
                  <Input
                    id="notify_before"
                    type="number"
                    min={0}
                    value={form.notify_before_minutes}
                    onChange={(e) =>
                      setForm({ ...form, notify_before_minutes: parseInt(e.target.value) || 0 })
                    }
                  />
                </div>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="copilot_prompt">Prompt do Copilot (opcional)</Label>
                <AITextarea
                  id="copilot_prompt"
                  value={form.copilot_prompt}
                  onChange={(e) => setForm({ ...form, copilot_prompt: e.target.value })}
                  setValue={(v) => setForm({ ...form, copilot_prompt: v })}
                  placeholder="O que o Copilot deve analisar quando este lembrete disparar?"
                  rows={2}
                  aiContext="Prompt de instrução para o Copilot de IA executar quando o lembrete disparar"
                  aiObjective="Sugerir ou melhorar o prompt de análise jurídica para o Copilot"
                />
                {form.copilot_prompt && (
                  <p className="text-xs text-muted-foreground flex items-center gap-1">
                    <Bot className="h-3 w-3" />
                    O Copilot será aberto automaticamente com este prompt
                  </p>
                )}
              </div>

              <div className="grid gap-2">
                <Label htmlFor="link">Link direto (opcional)</Label>
                <Input
                  id="link"
                  value={form.link}
                  onChange={(e) => setForm({ ...form, link: e.target.value })}
                  placeholder="Ex: /dashboard/processos/123"
                />
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={closeDialog}>
                Cancelar
              </Button>
              <Button onClick={handleSubmit} disabled={isSaving}>
                {isSaving ? (
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                ) : null}
                {editingReminder ? 'Salvar' : 'Criar Lembrete'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Quick Templates - horizontal scroll chips on mobile */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">Templates Rápidos</CardTitle>
          <CardDescription>Crie lembretes comuns com um clique</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="chips-scroll sm:flex-wrap sm:overflow-visible">
            {QUICK_TEMPLATES.map((tpl) => (
              <Button
                key={tpl.label}
                variant="outline"
                size="sm"
                onClick={() => openCreate(tpl.data)}
                className="whitespace-nowrap shrink-0"
              >
                <Plus className="mr-1 h-3 w-3" />
                {tpl.label}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Filters - horizontal scroll on mobile */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        <span className="text-sm font-medium text-muted-foreground shrink-0">Filtrar:</span>
        {STATUS_FILTERS.map((f) => (
          <Button
            key={f.value}
            variant={statusFilter === f.value ? 'default' : 'outline'}
            size="sm"
            onClick={() => setStatusFilter(f.value)}
            className="shrink-0"
          >
            {f.label}
          </Button>
        ))}
      </div>

      {/* Reminders List */}
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-2 flex-1">
                    <Skeleton className="h-5 w-64" />
                    <Skeleton className="h-4 w-48" />
                  </div>
                  <Skeleton className="h-8 w-24" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : !reminders || reminders.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Bell className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
            <h3 className="text-lg font-medium mb-1">Nenhum lembrete encontrado</h3>
            <p className="text-muted-foreground mb-4">
              Crie seu primeiro lembrete para organizar suas tarefas jurídicas.
            </p>
            <Button onClick={() => openCreate()}>
              <Plus className="mr-2 h-4 w-4" />
              Criar Lembrete
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {reminders.map((reminder) => (
            <Card key={reminder.id} className={reminder.status === 'completed' || reminder.status === 'cancelled' ? 'opacity-60' : ''}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0 space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-medium truncate">{reminder.title}</h3>
                      <Badge className={statusColors[reminder.status] || ''} variant="outline">
                        {reminder.status === 'active' && <CheckCircle className="h-3 w-3 mr-1" />}
                        {reminder.status === 'paused' && <Pause className="h-3 w-3 mr-1" />}
                        {reminder.status_display}
                      </Badge>
                      <Badge className={priorityColors[reminder.priority] || ''} variant="outline">
                        {reminder.priority === 'urgent' && <AlertCircle className="h-3 w-3 mr-1" />}
                        {reminder.priority_display}
                      </Badge>
                      <Badge variant="secondary">
                        {reminder.frequency_display}
                      </Badge>
                    </div>

                    {reminder.description && (
                      <p className="text-sm text-muted-foreground line-clamp-1">
                        {reminder.description}
                      </p>
                    )}

                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        Próximo: {formatDate(reminder.scheduled_date)}
                      </span>
                      {reminder.trigger_count > 0 && (
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          Disparado {reminder.trigger_count}x
                        </span>
                      )}
                      {reminder.copilot_prompt && (
                        <span className="flex items-center gap-1">
                          <Bot className="h-3 w-3" />
                          Copilot
                        </span>
                      )}
                      {reminder.related_case_title && (
                        <span className="truncate max-w-[200px]">
                          Caso: {reminder.related_case_title}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-1 shrink-0">
                    {reminder.status === 'active' && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => pauseMutation.mutate(reminder.id)}
                        title="Pausar"
                      >
                        <Pause className="h-4 w-4" />
                      </Button>
                    )}
                    {reminder.status === 'paused' && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => resumeMutation.mutate(reminder.id)}
                        title="Retomar"
                      >
                        <Play className="h-4 w-4" />
                      </Button>
                    )}
                    {(reminder.status === 'active' || reminder.status === 'paused') && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openEdit(reminder)}
                        title="Editar"
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                    )}
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button variant="ghost" size="sm" title="Excluir">
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Excluir lembrete?</AlertDialogTitle>
                          <AlertDialogDescription>
                            Esta ação não pode ser desfeita. O lembrete &quot;{reminder.title}&quot; será removido permanentemente.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Cancelar</AlertDialogCancel>
                          <AlertDialogAction onClick={() => deleteMutation.mutate(reminder.id)}>
                            Excluir
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
