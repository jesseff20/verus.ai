'use client';

import { useState, useMemo, useCallback, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Checkbox } from '@/components/ui/checkbox';
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  ChevronLeft,
  ChevronRight,
  Calendar as CalendarIcon,
  AlertTriangle,
  Clock,
  ExternalLink,
  Plus,
  Sparkles,
  RefreshCw,
  CheckCircle2,
  XCircle,
  ListChecks,
  MessageSquare,
  Filter,
} from 'lucide-react';
import {
  useCalendarEvents,
  useUpcomingDeadlines,
  useOverdueItems,
  type CalendarEvent,
} from '@/hooks/use-calendar';

// ── Helpers ──

const WEEKDAYS = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab'];

const EVENT_COLORS: Record<string, string> = {
  deadline: '#ef4444',
  reminder: '#3b82f6',
  hearing: '#8b5cf6',
  notification: '#f59e0b',
  phase: '#10b981',
  task: '#6366f1',
};

const EVENT_LABELS: Record<string, string> = {
  deadline: 'Prazo',
  reminder: 'Lembrete',
  hearing: 'Audiência',
  notification: 'Intimacao',
  phase: 'Fase',
  task: 'Tarefa',
};

const PRIORITY_LABELS: Record<number, string> = {
  1: 'Baixa',
  2: 'Media',
  3: 'Alta',
  4: 'Urgente',
};

const PRIORITY_COLORS: Record<number, string> = {
  1: 'text-green-600',
  2: 'text-yellow-600',
  3: 'text-orange-600',
  4: 'text-red-600',
};

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pendente',
  in_progress: 'Em andamento',
  completed: 'Concluído',
  cancelled: 'Cancelado',
};

type ViewMode = 'month' | 'week' | 'agenda';

// Filter types that can be toggled
type FilterKey = 'deadline' | 'hearing' | 'task' | 'reminder' | 'notification' | 'phase';

interface TaskFormData {
  title: string;
  description: string;
  type: string;
  date: string;
  time: string;
}

function pad(n: number) {
  return n.toString().padStart(2, '0');
}

function formatDate(d: Date) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function formatMonthYear(d: Date) {
  const months = [
    'Janeiro', 'Fevereiro', 'Marco', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
  ];
  return `${months[d.getMonth()]} ${d.getFullYear()}`;
}

function formatWeekRange(sel: Date) {
  const dayOfWeek = sel.getDay();
  const startOfWeek = new Date(sel.getFullYear(), sel.getMonth(), sel.getDate() - dayOfWeek);
  const endOfWeek = new Date(sel.getFullYear(), sel.getMonth(), sel.getDate() + (6 - dayOfWeek));
  return `${pad(startOfWeek.getDate())}/${pad(startOfWeek.getMonth() + 1)} - ${pad(endOfWeek.getDate())}/${pad(endOfWeek.getMonth() + 1)}/${endOfWeek.getFullYear()}`;
}

function isSameDay(a: Date, b: Date) {
  return a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate();
}

function getDaysInMonth(year: number, month: number) {
  return new Date(year, month + 1, 0).getDate();
}

function getFirstDayOfWeek(year: number, month: number) {
  return new Date(year, month, 1).getDay();
}

function formatTime(iso: string) {
  const d = new Date(iso);
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function formatFullDate(d: Date) {
  const weekdays = ['Domingo', 'Segunda-feira', 'Terca-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sabado'];
  return `${weekdays[d.getDay()]}, ${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}`;
}

function getDaysUntil(dateStr: string) {
  const target = new Date(dateStr);
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  target.setHours(0, 0, 0, 0);
  return Math.ceil((target.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
}

// ── Sync Status Component ──

interface SyncProvider {
  provider: string;
  label: string;
  connected: boolean;
  setup_required: boolean;
  env_vars?: string[];
}

function SyncStatusBar() {
  const { data: providers } = useQuery<SyncProvider[]>({
    queryKey: ['calendar', 'sync-providers'],
    queryFn: async () => {
      const res = await api.get('/api/v1/processos/calendario/sync/providers/');
      const data = res.data;
      return (data.providers || data.results || data) as SyncProvider[];
    },
  });

  const handleConnect = (provider: string) => {
    // Redirect to OAuth flow for the provider
    window.location.href = `/api/v1/processos/calendario/sync/${provider}/connect/`;
  };

  const statusIcon = (provider: SyncProvider) => {
    if (provider.connected) return <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />;
    if (provider.setup_required) return <XCircle className="h-3.5 w-3.5 text-muted-foreground" />;
    return <XCircle className="h-3.5 w-3.5 text-muted-foreground" />;
  };

  const statusText = (provider: SyncProvider) => {
    if (provider.connected) return 'Sincronizado';
    if (provider.setup_required) return 'Nao configurado';
    return 'Nao conectado';
  };

  // Fallback display when providers haven't loaded yet
  const displayProviders: SyncProvider[] = providers || [
    { provider: 'google', label: 'Google Calendar', connected: false, setup_required: true },
    { provider: 'outlook', label: 'Outlook', connected: false, setup_required: true },
  ];

  return (
    <div className="flex items-center gap-4 text-xs text-muted-foreground">
      {displayProviders.map((prov) => (
        <div key={prov.provider} className="flex items-center gap-1.5">
          {statusIcon(prov)}
          <span>{prov.label}: {statusText(prov)}</span>
          {!prov.connected && (
            prov.setup_required ? (
              <span className="text-xs text-muted-foreground">
                <Badge variant="outline" className="text-[10px] ml-1">Nao configurado</Badge>
                {prov.env_vars && prov.env_vars.length > 0 && (
                  <span className="text-xs text-muted-foreground block ml-1">
                    Configure: {prov.env_vars.join(', ')}
                  </span>
                )}
              </span>
            ) : (
              <Button
                variant="link"
                size="sm"
                className="h-auto p-0 text-xs text-primary"
                onClick={() => handleConnect(prov.provider)}
              >
                Conectar
              </Button>
            )
          )}
        </div>
      ))}
    </div>
  );
}

// ── Copilot Suggestions Panel ──

function CopilotPanel({
  events,
  upcoming,
  overdue,
}: {
  events: CalendarEvent[];
  upcoming: CalendarEvent[];
  overdue: CalendarEvent[];
}) {
  const suggestions = useMemo(() => {
    const items: Array<{ icon: React.ReactNode; text: string; severity: 'warning' | 'info' | 'urgent' }> = [];

    // Overdue items
    if (overdue.length > 0) {
      items.push({
        icon: <AlertTriangle className="h-4 w-4 text-red-500 shrink-0" />,
        text: `Voce tem ${overdue.length} ${overdue.length === 1 ? 'prazo vencido' : 'prazos vencidos'} que precisam de atencao imediata`,
        severity: 'urgent',
      });
    }

    // Upcoming deadlines this week
    const weekDeadlines = upcoming.filter(ev => ev.type === 'deadline');
    if (weekDeadlines.length > 0) {
      items.push({
        icon: <Clock className="h-4 w-4 text-amber-500 shrink-0" />,
        text: `Voce tem ${weekDeadlines.length} ${weekDeadlines.length === 1 ? 'prazo vencendo' : 'prazos vencendo'} esta semana`,
        severity: 'warning',
      });
    }

    // Tomorrow hearings
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const tomorrowKey = formatDate(tomorrow);
    const tomorrowHearings = upcoming.filter(
      ev => ev.type === 'hearing' && ev.start.startsWith(tomorrowKey)
    );
    if (tomorrowHearings.length > 0) {
      tomorrowHearings.forEach(h => {
        items.push({
          icon: <CalendarIcon className="h-4 w-4 text-purple-500 shrink-0" />,
          text: `Audiência amanha as ${formatTime(h.start)} -- preparar documentos: "${h.title}"`,
          severity: 'warning',
        });
      });
    }

    // High priority items
    const highPriority = upcoming.filter(ev => ev.priority >= 3);
    if (highPriority.length > 0 && items.length < 4) {
      items.push({
        icon: <AlertTriangle className="h-4 w-4 text-orange-500 shrink-0" />,
        text: `${highPriority.length} ${highPriority.length === 1 ? 'item de alta prioridade' : 'itens de alta prioridade'} nos proximos dias`,
        severity: 'info',
      });
    }

    // If no suggestions
    if (items.length === 0) {
      items.push({
        icon: <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />,
        text: 'Tudo em dia! Nenhuma pendencia urgente encontrada.',
        severity: 'info',
      });
    }

    return items;
  }, [events, upcoming, overdue]);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-purple-500" />
          Copilot - Sugestoes
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {suggestions.map((s, i) => (
          <div
            key={i}
            className={`flex items-start gap-2.5 rounded-md border p-2.5 text-sm ${
              s.severity === 'urgent'
                ? 'border-red-200 bg-red-50/50 dark:border-red-800 dark:bg-red-950/20'
                : s.severity === 'warning'
                ? 'border-amber-200 bg-amber-50/50 dark:border-amber-800 dark:bg-amber-950/20'
                : 'border-border'
            }`}
          >
            {s.icon}
            <span className="text-sm leading-snug">{s.text}</span>
          </div>
        ))}
        <Button
          variant="outline"
          size="sm"
          className="w-full gap-2 mt-2"
          onClick={() => window.location.href = '/dashboard'}
        >
          <MessageSquare className="h-4 w-4" />
          Pedir conselho ao Copilot
        </Button>
      </CardContent>
    </Card>
  );
}

// ── Event Detail Popover ──

function EventDetailCard({ ev }: { ev: CalendarEvent }) {
  const daysUntil = getDaysUntil(ev.start);
  const daysLabel =
    daysUntil === 0 ? 'Hoje' :
    daysUntil === 1 ? 'Amanha' :
    daysUntil < 0 ? `${Math.abs(daysUntil)} dias atras` :
    `Em ${daysUntil} dias`;

  return (
    <div
      className="rounded-md border p-3 transition-shadow hover:shadow-md"
      style={{ borderLeftWidth: 4, borderLeftColor: EVENT_COLORS[ev.type] || ev.color }}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium leading-tight">{ev.title}</p>
        <Badge variant="secondary" className="text-[10px] shrink-0">
          {EVENT_LABELS[ev.type] || ev.type}
        </Badge>
      </div>

      <div className="flex items-center gap-3 mt-1.5">
        <p className="text-xs text-muted-foreground">
          {formatTime(ev.start)}
          {ev.end ? ` - ${formatTime(ev.end)}` : ''}
        </p>
        <span className={`text-xs font-medium ${
          daysUntil < 0 ? 'text-red-600' :
          daysUntil <= 1 ? 'text-amber-600' :
          'text-muted-foreground'
        }`}>
          {daysLabel}
        </span>
      </div>

      {ev.case_title && (
        <a
          href={`/dashboard/processos/${ev.case_id}`}
          className="inline-flex items-center gap-1 text-xs text-primary hover:underline mt-1.5"
        >
          {ev.case_title}
          <ExternalLink className="h-3 w-3" />
        </a>
      )}

      {ev.description && (
        <p className="text-xs text-muted-foreground mt-1.5 line-clamp-2">
          {ev.description}
        </p>
      )}

      <div className="flex items-center gap-3 mt-2 pt-2 border-t">
        {ev.status && (
          <span className="text-[10px] text-muted-foreground">
            Status: {STATUS_LABELS[ev.status] || ev.status}
          </span>
        )}
        {ev.priority > 0 && (
          <span className={`text-[10px] font-medium ${PRIORITY_COLORS[ev.priority] || ''}`}>
            Prioridade: {PRIORITY_LABELS[ev.priority] || ev.priority}
          </span>
        )}
      </div>
    </div>
  );
}

// ── Create Task Dialog ──

function CreateTaskDialog({
  open,
  onOpenChange,
  initialDate,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initialDate: Date | null;
}) {
  const [formData, setFormData] = useState<TaskFormData>({
    title: '',
    description: '',
    type: 'task',
    date: initialDate ? formatDate(initialDate) : formatDate(new Date()),
    time: '09:00',
  });
  const [saving, setSaving] = useState(false);

  // Sync form date when initialDate changes or dialog opens
  useEffect(() => {
    if (open && initialDate) {
      setFormData(prev => ({
        ...prev,
        title: '',
        description: '',
        type: 'task',
        date: formatDate(initialDate),
        time: '09:00',
      }));
    }
  }, [open, initialDate]);

  const handleSave = async () => {
    if (!formData.title.trim()) return;
    setSaving(true);
    // In a real implementation, this would call the API
    // await api.post('/api/v1/processos/calendario/events/', { ... });
    setTimeout(() => {
      setSaving(false);
      onOpenChange(false);
      setFormData({ title: '', description: '', type: 'task', date: formatDate(new Date()), time: '09:00' });
    }, 500);
  };

  const dateValue = formData.date;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Nova Tarefa</DialogTitle>
          <DialogDescription>
            Crie uma tarefa, prazo ou lembrete para o dia selecionado.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="task-title">Titulo</Label>
            <Input
              id="task-title"
              placeholder="Ex: Preparar petição inicial"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="task-type">Tipo</Label>
            <Select
              value={formData.type}
              onValueChange={(v) => setFormData({ ...formData, type: v })}
            >
              <SelectTrigger id="task-type">
                <SelectValue placeholder="Selecione o tipo" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="task">Tarefa</SelectItem>
                <SelectItem value="deadline">Prazo</SelectItem>
                <SelectItem value="hearing">Audiência</SelectItem>
                <SelectItem value="reminder">Lembrete</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="grid gap-2">
              <Label htmlFor="task-date">Data</Label>
              <Input
                id="task-date"
                type="date"
                value={dateValue}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="task-time">Horario</Label>
              <Input
                id="task-time"
                type="time"
                value={formData.time}
                onChange={(e) => setFormData({ ...formData, time: e.target.value })}
              />
            </div>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="task-desc">Descrição (opcional)</Label>
            <Textarea
              id="task-desc"
              placeholder="Detalhes adicionais..."
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button onClick={handleSave} disabled={saving || !formData.title.trim()}>
            {saving ? 'Salvando...' : 'Criar Tarefa'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── Quick Filters ──

function QuickFilters({
  filters,
  onToggle,
}: {
  filters: Record<FilterKey, boolean>;
  onToggle: (key: FilterKey) => void;
}) {
  const filterItems: Array<{ key: FilterKey; label: string; color: string }> = [
    { key: 'deadline', label: 'Prazos', color: EVENT_COLORS.deadline },
    { key: 'hearing', label: 'Audiências', color: EVENT_COLORS.hearing },
    { key: 'task', label: 'Tarefas', color: EVENT_COLORS.task },
    { key: 'reminder', label: 'Lembretes', color: EVENT_COLORS.reminder },
    { key: 'notification', label: 'Intimacoes', color: EVENT_COLORS.notification },
    { key: 'phase', label: 'Fases', color: EVENT_COLORS.phase },
  ];

  return (
    <div className="flex flex-wrap items-center gap-3">
      <Filter className="h-4 w-4 text-muted-foreground" />
      {filterItems.map(({ key, label, color }) => (
        <label
          key={key}
          className="flex items-center gap-1.5 cursor-pointer select-none"
        >
          <Checkbox
            checked={filters[key]}
            onCheckedChange={() => onToggle(key)}
            className="h-3.5 w-3.5"
          />
          <div
            className="w-2.5 h-2.5 rounded-full shrink-0"
            style={{ backgroundColor: color }}
          />
          <span className="text-xs">{label}</span>
        </label>
      ))}
    </div>
  );
}

// ── Component ──

export default function CalendarioPage() {
  const today = new Date();
  const [currentDate, setCurrentDate] = useState(new Date(today.getFullYear(), today.getMonth(), 1));
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [view, setView] = useState<ViewMode>('month');
  const [createTaskOpen, setCreateTaskOpen] = useState(false);
  const [createTaskDate, setCreateTaskDate] = useState<Date | null>(null);

  // Quick filters
  const [filters, setFilters] = useState<Record<FilterKey, boolean>>({
    deadline: true,
    hearing: true,
    task: true,
    reminder: true,
    notification: true,
    phase: true,
  });

  const toggleFilter = useCallback((key: FilterKey) => {
    setFilters(prev => ({ ...prev, [key]: !prev[key] }));
  }, []);

  // Calculate date range for API
  const { start, end } = useMemo(() => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    if (view === 'month' || view === 'agenda') {
      const firstDay = getFirstDayOfWeek(year, month);
      const s = new Date(year, month, 1 - firstDay);
      const daysInMonth = getDaysInMonth(year, month);
      const lastDayOfWeek = new Date(year, month, daysInMonth).getDay();
      const e = new Date(year, month, daysInMonth + (6 - lastDayOfWeek));
      return { start: formatDate(s), end: formatDate(e) };
    } else {
      const sel = selectedDate || today;
      const dayOfWeek = sel.getDay();
      const s = new Date(sel.getFullYear(), sel.getMonth(), sel.getDate() - dayOfWeek);
      const e = new Date(sel.getFullYear(), sel.getMonth(), sel.getDate() + (6 - dayOfWeek));
      return { start: formatDate(s), end: formatDate(e) };
    }
  }, [currentDate, view, selectedDate]);

  const { data: rawEvents = [], isLoading: loadingEvents } = useCalendarEvents(start, end);
  const { data: upcoming = [] } = useUpcomingDeadlines(7);
  const { data: overdue = [] } = useOverdueItems();

  // Apply filters
  const events = useMemo(() => {
    return rawEvents.filter(ev => {
      const type = ev.type as FilterKey;
      if (type in filters) return filters[type];
      return true;
    });
  }, [rawEvents, filters]);

  // Build event map by date key
  const eventsByDate = useMemo(() => {
    const map: Record<string, CalendarEvent[]> = {};
    events.forEach((ev) => {
      const key = ev.start.slice(0, 10);
      if (!map[key]) map[key] = [];
      map[key].push(ev);
    });
    return map;
  }, [events]);

  // Navigation
  const goToday = () => {
    setCurrentDate(new Date(today.getFullYear(), today.getMonth(), 1));
    setSelectedDate(today);
  };

  const goPrev = () => {
    if (view === 'month' || view === 'agenda') {
      setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
    } else {
      const sel = selectedDate || today;
      const newDate = new Date(sel.getFullYear(), sel.getMonth(), sel.getDate() - 7);
      setSelectedDate(newDate);
      setCurrentDate(new Date(newDate.getFullYear(), newDate.getMonth(), 1));
    }
  };

  const goNext = () => {
    if (view === 'month' || view === 'agenda') {
      setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
    } else {
      const sel = selectedDate || today;
      const newDate = new Date(sel.getFullYear(), sel.getMonth(), sel.getDate() + 7);
      setSelectedDate(newDate);
      setCurrentDate(new Date(newDate.getFullYear(), newDate.getMonth(), 1));
    }
  };

  // Handle creating task from date click
  const handleDateDoubleClick = (date: Date) => {
    setCreateTaskDate(date);
    setCreateTaskOpen(true);
  };

  const handleCreateTaskFromButton = () => {
    setCreateTaskDate(selectedDate || today);
    setCreateTaskOpen(true);
  };

  // Build month grid
  const monthGrid = useMemo(() => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const daysInMonth = getDaysInMonth(year, month);
    const firstDay = getFirstDayOfWeek(year, month);
    const cells: Array<{ date: Date; isCurrentMonth: boolean }> = [];

    const prevMonthDays = getDaysInMonth(year, month - 1);
    for (let i = firstDay - 1; i >= 0; i--) {
      cells.push({
        date: new Date(year, month - 1, prevMonthDays - i),
        isCurrentMonth: false,
      });
    }

    for (let d = 1; d <= daysInMonth; d++) {
      cells.push({ date: new Date(year, month, d), isCurrentMonth: true });
    }

    const remaining = 7 - (cells.length % 7);
    if (remaining < 7) {
      for (let d = 1; d <= remaining; d++) {
        cells.push({ date: new Date(year, month + 1, d), isCurrentMonth: false });
      }
    }

    return cells;
  }, [currentDate]);

  // Week grid
  const weekGrid = useMemo(() => {
    if (view !== 'week') return [];
    const sel = selectedDate || today;
    const dayOfWeek = sel.getDay();
    const cells: Array<{ date: Date; isCurrentMonth: boolean }> = [];
    for (let i = 0; i < 7; i++) {
      const d = new Date(sel.getFullYear(), sel.getMonth(), sel.getDate() - dayOfWeek + i);
      cells.push({ date: d, isCurrentMonth: d.getMonth() === currentDate.getMonth() });
    }
    return cells;
  }, [view, selectedDate, currentDate]);

  // Agenda list (all events in month sorted by date)
  const agendaEvents = useMemo(() => {
    if (view !== 'agenda') return [];
    const sorted = [...events].sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());
    return sorted;
  }, [view, events]);

  const grid = view === 'month' ? monthGrid : weekGrid;

  // Selected day events
  const selectedEvents = useMemo(() => {
    if (!selectedDate) return [];
    const key = formatDate(selectedDate);
    return eventsByDate[key] || [];
  }, [selectedDate, eventsByDate]);

  // Navigation label
  const navLabel = useMemo(() => {
    if (view === 'week') {
      const sel = selectedDate || today;
      return formatWeekRange(sel);
    }
    return formatMonthYear(currentDate);
  }, [view, currentDate, selectedDate]);

  return (
    <TooltipProvider delayDuration={200}>
      <div className="space-y-4">
        {/* Header + Sync Status */}
        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold">Calendario de Prazos</h1>
            <p className="text-muted-foreground">
              Acompanhe prazos, audiencias e compromissos processuais
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <SyncStatusBar />
            <Button size="sm" className="gap-2" onClick={handleCreateTaskFromButton}>
              <Plus className="h-4 w-4" />
              Nova Tarefa
            </Button>
          </div>
        </div>

        {/* Overdue Alert */}
        {overdue.length > 0 && (
          <div className="flex items-center gap-3 rounded-lg bg-red-50 border border-red-200 px-4 py-3 dark:bg-red-950/30 dark:border-red-800">
            <AlertTriangle className="h-5 w-5 text-red-600 shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-medium text-red-800 dark:text-red-300">
                {overdue.length} {overdue.length === 1 ? 'item atrasado' : 'itens atrasados'}
              </p>
              <p className="text-xs text-red-600 dark:text-red-400">
                Verifique os prazos vencidos e tome as providencias necessarias
              </p>
            </div>
          </div>
        )}

        {/* Quick Filters */}
        <Card>
          <CardContent className="py-3">
            <QuickFilters filters={filters} onToggle={toggleFilter} />
          </CardContent>
        </Card>

        <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
          {/* Calendar */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                {/* View toggle */}
                <div className="flex gap-1">
                  <Button
                    variant={view === 'month' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setView('month')}
                  >
                    Mes
                  </Button>
                  <Button
                    variant={view === 'week' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setView('week')}
                  >
                    Semana
                  </Button>
                  <Button
                    variant={view === 'agenda' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setView('agenda')}
                  >
                    <ListChecks className="h-4 w-4 mr-1" />
                    Agenda
                  </Button>
                </div>

                {/* Navigation */}
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="icon" onClick={goPrev} aria-label="Período anterior">
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <span className="text-sm font-medium min-w-[160px] text-center">
                    {navLabel}
                  </span>
                  <Button variant="outline" size="icon" onClick={goNext} aria-label="Próximo período">
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="sm" onClick={goToday}>
                    Hoje
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loadingEvents ? (
                <div className="space-y-2">
                  {Array.from({ length: 6 }).map((_, i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : view === 'agenda' ? (
                /* ── Agenda View ── */
                <div className="space-y-2">
                  {agendaEvents.length === 0 ? (
                    <p className="text-sm text-muted-foreground text-center py-8">
                      Nenhum evento neste periodo
                    </p>
                  ) : (
                    (() => {
                      let lastDateKey = '';
                      return agendaEvents.map((ev) => {
                        const dateKey = ev.start.slice(0, 10);
                        const evDate = new Date(ev.start);
                        const showDateHeader = dateKey !== lastDateKey;
                        lastDateKey = dateKey;
                        return (
                          <div key={ev.id}>
                            {showDateHeader && (
                              <div className="flex items-center gap-2 pt-3 pb-1">
                                <span className={`text-xs font-semibold ${
                                  isSameDay(evDate, today)
                                    ? 'text-primary'
                                    : 'text-muted-foreground'
                                }`}>
                                  {formatFullDate(evDate)}
                                </span>
                                {isSameDay(evDate, today) && (
                                  <Badge variant="default" className="text-[10px]">Hoje</Badge>
                                )}
                              </div>
                            )}
                            <EventDetailCard ev={ev} />
                          </div>
                        );
                      });
                    })()
                  )}
                </div>
              ) : (
                /* ── Month/Week Grid View ── */
                <>
                  {/* Weekday headers */}
                  <div className="grid grid-cols-7 mb-1">
                    {WEEKDAYS.map((day) => (
                      <div
                        key={day}
                        className="text-center text-xs font-medium text-muted-foreground py-2"
                      >
                        {day}
                      </div>
                    ))}
                  </div>

                  {/* Day cells */}
                  <div className="grid grid-cols-7 border-t border-l">
                    {grid.map(({ date, isCurrentMonth }, idx) => {
                      const key = formatDate(date);
                      const dayEvents = eventsByDate[key] || [];
                      const isToday = isSameDay(date, today);
                      const isSelected = selectedDate ? isSameDay(date, selectedDate) : false;

                      return (
                        <button
                          key={idx}
                          onClick={() => setSelectedDate(date)}
                          onDoubleClick={() => handleDateDoubleClick(date)}
                          className={`
                            relative border-r border-b p-1 text-left transition-colors group
                            ${view === 'week' ? 'min-h-[120px]' : 'min-h-[72px] sm:min-h-[80px]'}
                            hover:bg-accent/50 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-inset
                            ${!isCurrentMonth ? 'bg-muted/30' : ''}
                            ${isSelected ? 'bg-accent' : ''}
                          `}
                        >
                          {/* Date number + add button */}
                          <div className="flex items-center justify-between">
                            <span
                              className={`
                                inline-flex items-center justify-center text-xs font-medium w-6 h-6 rounded-full
                                ${isToday ? 'bg-primary text-primary-foreground' : ''}
                                ${!isCurrentMonth ? 'text-muted-foreground' : ''}
                              `}
                            >
                              {date.getDate()}
                            </span>
                            <span
                              className="hidden group-hover:inline-flex items-center justify-center w-5 h-5 rounded-full hover:bg-primary/10 text-muted-foreground hover:text-primary cursor-pointer"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDateDoubleClick(date);
                              }}
                            >
                              <Plus className="h-3 w-3" />
                            </span>
                          </div>

                          {/* Event indicators */}
                          <div className="flex flex-col gap-0.5 mt-0.5">
                            {view === 'week' ? (
                              // Week view: show mini event cards
                              dayEvents.slice(0, 4).map((ev) => (
                                <Tooltip key={ev.id}>
                                  <TooltipTrigger asChild>
                                    <div
                                      className="text-[10px] leading-tight px-1 py-0.5 rounded truncate cursor-default"
                                      style={{
                                        backgroundColor: `${EVENT_COLORS[ev.type] || ev.color}18`,
                                        borderLeft: `2px solid ${EVENT_COLORS[ev.type] || ev.color}`,
                                      }}
                                    >
                                      <span className="font-medium">{formatTime(ev.start)}</span>{' '}
                                      {ev.title}
                                    </div>
                                  </TooltipTrigger>
                                  <TooltipContent side="right" className="max-w-[280px] p-0">
                                    <div className="p-3 space-y-1">
                                      <p className="font-medium text-sm">{ev.title}</p>
                                      <p className="text-xs opacity-80">
                                        {EVENT_LABELS[ev.type] || ev.type} - {formatTime(ev.start)}
                                        {ev.end ? ` a ${formatTime(ev.end)}` : ''}
                                      </p>
                                      {ev.case_title && (
                                        <p className="text-xs opacity-80">Processo: {ev.case_title}</p>
                                      )}
                                      {ev.description && (
                                        <p className="text-xs opacity-70 line-clamp-2">{ev.description}</p>
                                      )}
                                      {ev.status && (
                                        <p className="text-xs opacity-80">Status: {STATUS_LABELS[ev.status] || ev.status}</p>
                                      )}
                                    </div>
                                  </TooltipContent>
                                </Tooltip>
                              ))
                            ) : (
                              // Month view: show dots
                              <div className="flex flex-wrap gap-0.5">
                                {dayEvents.slice(0, 3).map((ev) => (
                                  <Tooltip key={ev.id}>
                                    <TooltipTrigger asChild>
                                      <div
                                        className="w-2 h-2 rounded-full shrink-0 cursor-default"
                                        style={{ backgroundColor: EVENT_COLORS[ev.type] || ev.color }}
                                      />
                                    </TooltipTrigger>
                                    <TooltipContent side="top" className="max-w-[250px]">
                                      <p className="font-medium">{ev.title}</p>
                                      <p className="text-xs opacity-80">
                                        {EVENT_LABELS[ev.type] || ev.type} - {formatTime(ev.start)}
                                      </p>
                                      {ev.case_title && (
                                        <p className="text-xs opacity-70">Processo: {ev.case_title}</p>
                                      )}
                                    </TooltipContent>
                                  </Tooltip>
                                ))}
                                {dayEvents.length > 3 && (
                                  <span className="text-[10px] text-muted-foreground leading-none">
                                    +{dayEvents.length - 3}
                                  </span>
                                )}
                              </div>
                            )}
                            {view === 'week' && dayEvents.length > 4 && (
                              <span className="text-[10px] text-muted-foreground text-center">
                                +{dayEvents.length - 4} mais
                              </span>
                            )}
                          </div>
                        </button>
                      );
                    })}
                  </div>

                  {/* Click hint */}
                  <p className="text-[10px] text-muted-foreground mt-2 text-center">
                    Clique para selecionar um dia. Clique duplo ou no + para criar uma tarefa.
                  </p>
                </>
              )}
            </CardContent>
          </Card>

          {/* Side Panel */}
          <div className="space-y-4">
            {/* Copilot Suggestions */}
            <CopilotPanel events={events} upcoming={upcoming} overdue={overdue} />

            {/* Selected day events */}
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    <CalendarIcon className="h-4 w-4" />
                    {selectedDate
                      ? `${pad(selectedDate.getDate())}/${pad(selectedDate.getMonth() + 1)}/${selectedDate.getFullYear()}`
                      : 'Selecione um dia'}
                  </CardTitle>
                  {selectedDate && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      onClick={() => handleDateDoubleClick(selectedDate)}
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {!selectedDate ? (
                  <p className="text-sm text-muted-foreground">
                    Clique em um dia do calendario para ver os eventos
                  </p>
                ) : selectedEvents.length === 0 ? (
                  <div className="text-center py-4">
                    <p className="text-sm text-muted-foreground mb-3">
                      Nenhum evento neste dia
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-2"
                      onClick={() => handleDateDoubleClick(selectedDate)}
                    >
                      <Plus className="h-4 w-4" />
                      Criar tarefa
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {selectedEvents.map((ev) => (
                      <EventDetailCard key={ev.id} ev={ev} />
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Upcoming 7 days */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Próximos 7 dias
                </CardTitle>
              </CardHeader>
              <CardContent>
                {upcoming.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    Nenhum prazo nos proximos 7 dias
                  </p>
                ) : (
                  <div className="space-y-2">
                    {upcoming.slice(0, 8).map((ev) => {
                      const evDate = new Date(ev.start);
                      const daysUntil = getDaysUntil(ev.start);
                      return (
                        <div
                          key={ev.id}
                          className="flex items-center gap-2 text-sm"
                        >
                          <div
                            className="w-2 h-2 rounded-full shrink-0"
                            style={{ backgroundColor: EVENT_COLORS[ev.type] || ev.color }}
                          />
                          <span className="text-xs text-muted-foreground w-10 shrink-0">
                            {pad(evDate.getDate())}/{pad(evDate.getMonth() + 1)}
                          </span>
                          <span className="truncate flex-1">{ev.title}</span>
                          {daysUntil <= 2 && (
                            <Badge variant={daysUntil <= 1 ? 'destructive' : 'secondary'} className="text-[10px] shrink-0">
                              {daysUntil === 0 ? 'Hoje' : daysUntil === 1 ? 'Amanha' : `${daysUntil}d`}
                            </Badge>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Color Legend */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground">Legenda</CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(EVENT_LABELS).map(([type, label]) => (
                    <div key={type} className="flex items-center gap-2 text-xs">
                      <div
                        className="w-3 h-3 rounded-full shrink-0"
                        style={{ backgroundColor: EVENT_COLORS[type] }}
                      />
                      <span>{label}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Create Task Dialog */}
        <CreateTaskDialog
          open={createTaskOpen}
          onOpenChange={setCreateTaskOpen}
          initialDate={createTaskDate}
        />
      </div>
    </TooltipProvider>
  );
}
