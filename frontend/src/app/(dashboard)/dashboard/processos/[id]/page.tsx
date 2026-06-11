'use client';

import { useParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import Link from 'next/link';
import { useState } from 'react';
import {
  ArrowLeft,
  Scale,
  Calendar,
  Loader2,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Plus,
  Pencil,
  FileText,
  Users,
  Bot,
  History,
  Gavel,
  Paperclip,
  ExternalLink,
  Circle,
  Check,
  MessageSquare,
  ListChecks,
  ListOrdered,
  Eye,
  MapPin,
  ClipboardList,
  Timer,
  RotateCcw,
  Mail,
  Send,
  Bell,
  ArrowDownLeft,
  ArrowUpRight,
  Activity,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
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
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';
import { AIInput } from '@/components/ui/ai-input';
import { AITextarea } from '@/components/ui/ai-textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import api from '@/lib/api';
import FlowPanel from '@/components/workflow-editor/FlowPanel';

interface CaseDocument {
  id: string;
  titulo: string;
  tipo: string;
  tipo_display: string;
  descricao: string;
  data_documento: string | null;
  generated_document_id: string | null;
  generated_document: string | null;
  simulation: string | null;
  created_at: string;
}

interface TimelineEvent {
  type: string;
  icon: string;
  title: string;
  description: string;
  date: string;
  metadata: Record<string, any>;
}

interface CasePhaseData {
  id: string;
  caso: string;
  order: number;
  name: string;
  description: string;
  status: string;
  status_display: string;
  estimated_date: string | null;
  actual_date: string | null;
  reopened_at: string | null;
  reopened_reason: string;
  overdue_since: string | null;
  is_overdue: boolean;
  days_overdue: number;
  copilot_prompt: string;
  suggested_documents: string[];
  notes: string;
  created_at: string;
}

interface LegalCase {
  id: string;
  titulo: string;
  numero_processo: string;
  especialidade_display: string;
  status: string;
  status_display: string;
  fase_display: string;
  client_id: string | null;
  client_name: string | null;
  cliente_nome: string;
  cliente_cpf_cnpj: string;
  parte_contraria: string;
  tribunal: string;
  vara_juizo: string;
  comarca: string;
  valor_causa: string | null;
  honorarios_combinados: string | null;
  advogado_nome: string | null;
  data_distribuicao: string | null;
  descricao: string;
  observacoes: string;
  prazos: LegalDeadline[];
  tarefas: CaseTask[];
  documentos_caso: CaseDocument[];
  phases: CasePhaseData[];
  notificacoes: LegalNotificationData[];
  created_at: string;
  // Fase 4 — Fluxo de trabalho
  active_flow_id: string | null;
  active_flow_status: string | null;
  active_flow_node: string | null;
  active_flow_pending_tasks: number;
  active_flow_template_name: string | null;
}

interface LegalDeadline {
  id: string;
  titulo: string;
  tipo_display: string;
  prioridade_display: string;
  status: string;
  status_display: string;
  data_prazo: string;
  dias_restantes: number | null;
  responsavel_nome: string | null;
  descricao: string;
  appeal_type: string;
  base_legal: string;
  auto_generated: boolean;
}

interface CaseTask {
  id: string;
  titulo: string;
  status: string;
  status_display: string;
  prioridade_display: string;
  data_limite: string | null;
  responsavel_nome: string | null;
  descricao: string;
}

interface LegalNotificationData {
  id: string;
  caso: string;
  tipo: string;
  tipo_display: string;
  direcao: string;
  direcao_display: string;
  status: string;
  status_display: string;
  meio: string;
  meio_display: string;
  destinatario_nome: string;
  remetente: string;
  data_expedicao: string | null;
  data_ciencia: string | null;
  data_publicacao_dje: string | null;
  prazo_dias: number | null;
  prazo_tipo: string;
  prazo_tipo_display: string;
  prazo_vencimento: string | null;
  prazo_default: { dias: number; tipo: string; descricao: string } | null;
  base_legal: string;
  conteudo_resumo: string;
  observacoes: string;
  deadline_created: string | null;
  created_at: string;
}

const statusConfig: Record<string, { color: string }> = {
  ativo: { color: 'bg-green-100 text-green-800' },
  aguardando: { color: 'bg-blue-100 text-blue-800' },
  suspenso: { color: 'bg-orange-100 text-orange-800' },
  encerrado: { color: 'bg-gray-100 text-gray-800' },
  ganho: { color: 'bg-emerald-100 text-emerald-800' },
  perdido: { color: 'bg-red-100 text-red-800' },
  acordo: { color: 'bg-purple-100 text-purple-800' },
};

function formatDate(d: string | null) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('pt-BR');
}

function formatCurrency(v: string | null) {
  if (!v) return '—';
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(parseFloat(v));
}

export default function CaseDetailPage() {
  const params = useParams();
  const caseId = params.id as string;
  const queryClient = useQueryClient();

  const [addDeadlineOpen, setAddDeadlineOpen] = useState(false);
  const [addTaskOpen, setAddTaskOpen] = useState(false);
  const [deadlineForm, setDeadlineForm] = useState({ titulo: '', data_prazo: '', tipo: 'processual', prioridade: 'media', descricao: '' });
  const [taskForm, setTaskForm] = useState({ titulo: '', data_limite: '', prioridade: 'media', descricao: '' });
  const [addNotificationOpen, setAddNotificationOpen] = useState(false);

  // Prazo Recursal (#6)
  const [appealDialogOpen, setAppealDialogOpen] = useState(false);
  const [appealForm, setAppealForm] = useState({ appeal_type: '', intimation_date: '' });
  const [appealResult, setAppealResult] = useState<{
    deadline_date: string; dias: number; base_legal: string; descricao: string;
  } | null>(null);

  // Checklist (#14)
  const [checklistDialogOpen, setChecklistDialogOpen] = useState(false);
  const [checklistPreview, setChecklistPreview] = useState<{ titulo: string; descricao: string; prioridade: string }[]>([]);
  const [notifForm, setNotifForm] = useState({
    tipo: 'intimacao_dje',
    direcao: 'recebida',
    meio: '',
    destinatario_nome: '',
    remetente: '',
    data_expedicao: '',
    data_ciencia: '',
    data_publicacao_dje: '',
    prazo_dias: '',
    prazo_tipo: 'uteis',
    base_legal: '',
    conteudo_resumo: '',
    observacoes: '',
  });

  const { data: caso, isLoading, error } = useQuery({
    queryKey: ['caso', caseId],
    queryFn: async () => {
      const response = await api.get<LegalCase>(`/api/v1/processos/${caseId}/`);
      return response.data;
    },
  });

  const addDeadlineMutation = useMutation({
    mutationFn: async (data: typeof deadlineForm) => {
      await api.post(`/api/v1/processos/${caseId}/prazos/`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['caso', caseId] });
      setAddDeadlineOpen(false);
      setDeadlineForm({ titulo: '', data_prazo: '', tipo: 'processual', prioridade: 'media', descricao: '' });
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || err?.response?.data?.detail || 'Erro ao processar solicitação');
    },
  });

  const addTaskMutation = useMutation({
    mutationFn: async (data: typeof taskForm) => {
      await api.post(`/api/v1/processos/${caseId}/tarefas/`, {
        ...data,
        data_limite: data.data_limite || null,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['caso', caseId] });
      setAddTaskOpen(false);
      setTaskForm({ titulo: '', data_limite: '', prioridade: 'media', descricao: '' });
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || err?.response?.data?.detail || 'Erro ao processar solicitação');
    },
  });

  const addNotificationMutation = useMutation({
    mutationFn: async (data: typeof notifForm) => {
      await api.post(`/api/v1/processos/${caseId}/notificacoes/`, {
        ...data,
        data_expedicao: data.data_expedicao || null,
        data_ciencia: data.data_ciencia || null,
        data_publicacao_dje: data.data_publicacao_dje || null,
        prazo_dias: data.prazo_dias ? parseInt(data.prazo_dias) : null,
        meio: data.meio || '',
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['caso', caseId] });
      setAddNotificationOpen(false);
      setNotifForm({
        tipo: 'intimacao_dje', direcao: 'recebida', meio: '', destinatario_nome: '',
        remetente: '', data_expedicao: '', data_ciencia: '', data_publicacao_dje: '',
        prazo_dias: '', prazo_tipo: 'uteis', base_legal: '', conteudo_resumo: '', observacoes: '',
      });
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || err?.response?.data?.detail || 'Erro ao processar solicitação');
    },
  });

  // Prazo Recursal (#6) — queries and mutations
  const { data: tiposRecurso } = useQuery({
    queryKey: ['tipos-recurso'],
    queryFn: async () => {
      const res = await api.get('/api/v1/processos/prazos/tipos-recurso/');
      return res.data as Record<string, { dias: number; base_legal: string; descricao: string }>;
    },
  });

  const calcularRecursalMutation = useMutation({
    mutationFn: async (data: { appeal_type: string; intimation_date: string }) => {
      const res = await api.post('/api/v1/processos/prazos/calcular-recursal/', data);
      return res.data;
    },
    onSuccess: (data) => {
      setAppealResult({
        deadline_date: data.deadline_date,
        dias: data.dias,
        base_legal: data.base_legal,
        descricao: data.descricao,
      });
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || err?.response?.data?.detail || 'Erro ao processar solicitação');
    },
  });

  const salvarRecursalMutation = useMutation({
    mutationFn: async (data: { appeal_type: string; intimation_date: string; caso_id: string }) => {
      const res = await api.post('/api/v1/processos/prazos/calcular-recursal/', data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['caso', caseId] });
      setAppealDialogOpen(false);
      setAppealForm({ appeal_type: '', intimation_date: '' });
      setAppealResult(null);
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || err?.response?.data?.detail || 'Erro ao processar solicitação');
    },
  });

  // Checklist (#14) — mutations
  const checklistPreviewQuery = useMutation({
    mutationFn: async () => {
      const res = await api.get(`/api/v1/processos/${caseId}/checklist/`);
      return res.data;
    },
    onSuccess: (data) => {
      setChecklistPreview(data.checklist || []);
      setChecklistDialogOpen(true);
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || err?.response?.data?.detail || 'Erro ao processar solicitação');
    },
  });

  const applyChecklistMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post(`/api/v1/processos/${caseId}/checklist/`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['caso', caseId] });
      setChecklistDialogOpen(false);
      setChecklistPreview([]);
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || err?.response?.data?.detail || 'Erro ao processar solicitação');
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !caso) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-4">
        <AlertTriangle className="h-10 w-10 text-destructive" />
        <p className="text-muted-foreground">Caso não encontrado</p>
        <Button asChild variant="outline">
          <Link href="/dashboard/processos"><ArrowLeft className="h-4 w-4 mr-2" />Voltar</Link>
        </Button>
      </div>
    );
  }

  const statusCfg = statusConfig[caso.status] || { color: 'bg-gray-100 text-gray-800' };

  return (
    <div className="space-y-6 pb-20 sm:pb-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start gap-4">
        <Button variant="outline" size="icon" asChild className="shrink-0">
          <Link href="/dashboard/processos"><ArrowLeft className="h-4 w-4" /></Link>
        </Button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight">{caso.titulo}</h1>
            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${statusCfg.color}`}>
              {caso.status_display}
            </span>
          </div>
          <div className="flex items-center gap-2 mt-1 text-sm text-muted-foreground flex-wrap">
            {caso.numero_processo && (
              <span className="font-mono text-xs sm:text-sm">{caso.numero_processo}</span>
            )}
            {caso.numero_processo && <span>•</span>}
            <span>{caso.especialidade_display}</span>
            <span>•</span>
            <span>{caso.fase_display}</span>
          </div>
        </div>
        <Button variant="outline" size="sm" asChild className="hidden sm:inline-flex">
          <Link href={`/dashboard/processos/${caseId}/editar`}>
            <Pencil className="h-4 w-4 mr-2" />
            Editar
          </Link>
        </Button>
      </div>

      {/* Cards de Info */}
      <div className="grid gap-3 sm:gap-4 grid-cols-2 lg:grid-cols-4">
        {caso.client_id ? (
          <Link href={`/dashboard/clients`} className="block group">
            <Card className="h-full transition-all duration-150 group-hover:border-primary/40 group-hover:shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
                  <Users className="h-3.5 w-3.5" />
                  Cliente
                  <ExternalLink className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity ml-auto" />
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="font-medium group-hover:text-primary transition-colors">{caso.client_name || caso.cliente_nome}</p>
                {caso.cliente_cpf_cnpj && <p className="text-xs text-muted-foreground">{caso.cliente_cpf_cnpj}</p>}
              </CardContent>
            </Card>
          </Link>
        ) : (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
                <Users className="h-3.5 w-3.5" />
                Cliente
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="font-medium">{caso.cliente_nome}</p>
              {caso.cliente_cpf_cnpj && <p className="text-xs text-muted-foreground">{caso.cliente_cpf_cnpj}</p>}
            </CardContent>
          </Card>
        )}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Parte Contrária</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-medium">{caso.parte_contraria || '—'}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Valor da Causa</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-medium">{formatCurrency(caso.valor_causa)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Distribuído em</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-medium">{formatDate(caso.data_distribuicao)}</p>
          </CardContent>
        </Card>
      </div>

      {/* Abas — 4 tabs: Visão Geral, Cronograma, Atividades, Documentos */}
      <Tabs defaultValue="visao-geral">
        <TabsList className="w-full sm:w-auto overflow-x-auto flex scrollbar-hide">
          <TabsTrigger value="visao-geral" className="flex-shrink-0 min-h-[44px] gap-1.5 text-xs sm:text-sm">
            <Eye className="h-4 w-4" />
            <span className="hidden sm:inline">Visão Geral</span>
            <span className="sm:hidden">Geral</span>
          </TabsTrigger>
          <TabsTrigger value="cronograma" className="flex-shrink-0 min-h-[44px] gap-1.5 text-xs sm:text-sm">
            <ListOrdered className="h-4 w-4" />
            <span className="hidden sm:inline">Cronograma</span>
            <span className="sm:hidden">Crono</span>
          </TabsTrigger>
          <TabsTrigger value="atividades" className="flex-shrink-0 min-h-[44px] gap-1.5 text-xs sm:text-sm">
            <Clock className="h-4 w-4" />
            <span className="hidden sm:inline">Atividades</span>
            <span className="sm:hidden">Ativ.</span>
          </TabsTrigger>
          <TabsTrigger value="documentos" className="flex-shrink-0 min-h-[44px] gap-1.5 text-xs sm:text-sm">
            <FileText className="h-4 w-4" />
            <span className="hidden sm:inline">Documentos</span>
            <span className="sm:hidden">Docs</span>
            {caso.documentos_caso && caso.documentos_caso.length > 0 && (
              <Badge className="ml-1 h-5 w-5 p-0 flex items-center justify-center text-xs bg-green-500">
                {caso.documentos_caso.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="notificacoes" className="flex-shrink-0 min-h-[44px] gap-1.5 text-xs sm:text-sm">
            <Bell className="h-4 w-4" />
            <span className="hidden sm:inline">Notificações</span>
            <span className="sm:hidden">Notif.</span>
            {caso.notificacoes && caso.notificacoes.length > 0 && (
              <Badge className="ml-1 h-5 w-5 p-0 flex items-center justify-center text-xs bg-blue-500">
                {caso.notificacoes.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="fluxo" className="flex-shrink-0 min-h-[44px] gap-1.5 text-xs sm:text-sm">
            <Activity className="h-4 w-4" />
            <span className="hidden sm:inline">Fluxo</span>
            <span className="sm:hidden">Fluxo</span>
            {caso.active_flow_pending_tasks > 0 && (
              <Badge className="ml-1 h-5 w-5 p-0 flex items-center justify-center text-xs bg-blue-500">
                {caso.active_flow_pending_tasks}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        {/* VISAO GERAL */}
        <TabsContent value="visao-geral" className="mt-4 space-y-4">
          {/* Quick summary cards */}
          <div className="grid gap-3 grid-cols-2 sm:grid-cols-3">
            <Card>
              <CardContent className="flex items-center gap-3 py-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 text-blue-700">
                  <ListOrdered className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Fase Atual</p>
                  <p className="font-semibold text-sm">{caso.fase_display}</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="flex items-center gap-3 py-4">
                <div className={`flex h-10 w-10 items-center justify-center rounded-full ${
                  caso.prazos.filter(p => p.status === 'pendente').length > 0
                    ? 'bg-yellow-100 text-yellow-700'
                    : 'bg-gray-100 text-gray-400'
                }`}>
                  <Timer className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Prazos Pendentes</p>
                  <p className="font-semibold text-sm">
                    {caso.prazos.filter(p => p.status === 'pendente').length > 0
                      ? `${caso.prazos.filter(p => p.status === 'pendente').length} prazo(s)`
                      : 'Nenhum'}
                  </p>
                  {(() => {
                    const nextDeadline = caso.prazos
                      .filter(p => p.status === 'pendente' && p.dias_restantes !== null)
                      .sort((a, b) => (a.dias_restantes ?? 999) - (b.dias_restantes ?? 999))[0];
                    if (!nextDeadline) return null;
                    return (
                      <p className={`text-[10px] ${
                        (nextDeadline.dias_restantes ?? 0) < 0 ? 'text-red-600' :
                        (nextDeadline.dias_restantes ?? 0) <= 3 ? 'text-orange-500' :
                        'text-muted-foreground'
                      }`}>
                        Próximo: {nextDeadline.titulo} ({nextDeadline.dias_restantes}d)
                      </p>
                    );
                  })()}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="flex items-center gap-3 py-4">
                <div className={`flex h-10 w-10 items-center justify-center rounded-full ${
                  caso.tarefas.filter(t => t.status !== 'concluida').length > 0
                    ? 'bg-orange-100 text-orange-700'
                    : 'bg-green-100 text-green-700'
                }`}>
                  <ClipboardList className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Tarefas</p>
                  <p className="font-semibold text-sm">
                    {caso.tarefas.filter(t => t.status !== 'concluida').length > 0
                      ? `${caso.tarefas.filter(t => t.status !== 'concluida').length} pendente(s)`
                      : 'Todas concluídas'}
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Copilot Analysis Button */}
          <Card className="border-primary/20 bg-primary/5">
            <CardContent className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 py-4">
              <div className="flex items-center gap-3">
                <Bot className="h-5 w-5 text-primary shrink-0" />
                <div>
                  <p className="font-medium text-sm">Analisar com Copilot</p>
                  <p className="text-xs text-muted-foreground">Obtenha análise inteligente, riscos e recomendações</p>
                </div>
              </div>
              <Button size="sm" asChild className="w-full sm:w-auto">
                <Link href={`/dashboard/copilot?prompt=${encodeURIComponent(
                  `Analise o caso "${caso.titulo}" (${caso.especialidade_display}). ` +
                  `Cliente: ${caso.cliente_nome}. Parte contrária: ${caso.parte_contraria || 'não informada'}. ` +
                  `Status: ${caso.status_display}. Fase: ${caso.fase_display}. ` +
                  (caso.tribunal ? `Tribunal: ${caso.tribunal}. ` : '') +
                  (caso.descricao ? `Descrição: ${caso.descricao.slice(0, 300)}. ` : '') +
                  `Forneça um resumo do status atual, próximas ações recomendadas e riscos identificados.`
                )}`}>
                  <Bot className="h-4 w-4 mr-2" />
                  Analisar
                </Link>
              </Button>
            </CardContent>
          </Card>

          {/* Case details */}
          <div className="grid gap-4 grid-cols-1 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Localização Processual</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-xs text-muted-foreground">Tribunal</p>
                  <p className="font-medium">{caso.tribunal || '—'}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Vara / Juizo</p>
                  <p className="font-medium">{caso.vara_juizo || '—'}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Comarca</p>
                  <p className="font-medium">{caso.comarca || '—'}</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Financeiro</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-xs text-muted-foreground">Valor da Causa</p>
                  <p className="font-medium">{formatCurrency(caso.valor_causa)}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Honorários Combinados</p>
                  <p className="font-medium">{formatCurrency(caso.honorarios_combinados)}</p>
                </div>
              </CardContent>
            </Card>

            {caso.descricao && (
              <Card className="md:col-span-2">
                <CardHeader>
                  <CardTitle className="text-base">Descrição do Caso</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm whitespace-pre-wrap">{caso.descricao}</p>
                </CardContent>
              </Card>
            )}

            {caso.observacoes && (
              <Card className="md:col-span-2">
                <CardHeader>
                  <CardTitle className="text-base">Observações Internas</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm whitespace-pre-wrap text-muted-foreground">{caso.observacoes}</p>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Inline: Prazos + Tarefas summaries */}
          <div className="grid gap-4 grid-cols-1 md:grid-cols-2">
            {/* Prazos summary */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <div>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Timer className="h-4 w-4" />
                    Prazos
                  </CardTitle>
                  <CardDescription>{caso.prazos.length} prazo(s)</CardDescription>
                </div>
                <div className="flex gap-1.5">
                  <Button size="sm" variant="outline" onClick={() => {
                    setAppealForm({ appeal_type: '', intimation_date: '' });
                    setAppealResult(null);
                    setAppealDialogOpen(true);
                  }}>
                    <Scale className="h-3.5 w-3.5 mr-1" />
                    Recursal
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => setAddDeadlineOpen(true)}>
                    <Plus className="h-3.5 w-3.5 mr-1" />
                    Adicionar
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {caso.prazos.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-4">Nenhum prazo cadastrado</p>
                ) : (
                  <div className="space-y-2">
                    {caso.prazos.slice(0, 5).map(prazo => (
                      <div key={prazo.id} className="flex items-center justify-between p-2 rounded-lg border text-sm">
                        <div>
                          <p className="font-medium text-sm">{prazo.titulo}</p>
                          <div className="flex items-center gap-1.5 mt-0.5">
                            <Badge variant="outline" className="text-[10px]">{prazo.tipo_display}</Badge>
                            <Badge variant="outline" className="text-[10px]">{prazo.prioridade_display}</Badge>
                          </div>
                        </div>
                        <div className="text-right shrink-0 ml-3">
                          <p className="text-xs font-medium">{formatDate(prazo.data_prazo)}</p>
                          {prazo.dias_restantes !== null && (
                            <p className={`text-[10px] ${prazo.dias_restantes < 0 ? 'text-red-600' : prazo.dias_restantes <= 3 ? 'text-orange-500' : 'text-muted-foreground'}`}>
                              {prazo.dias_restantes < 0 ? `${Math.abs(prazo.dias_restantes)}d atrasado` :
                               prazo.dias_restantes === 0 ? 'Hoje' :
                               `${prazo.dias_restantes}d restantes`}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                    {caso.prazos.length > 5 && (
                      <p className="text-xs text-muted-foreground text-center pt-1">
                        +{caso.prazos.length - 5} prazo(s) adicionais
                      </p>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Tarefas summary */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <div>
                  <CardTitle className="text-base flex items-center gap-2">
                    <ClipboardList className="h-4 w-4" />
                    Tarefas
                  </CardTitle>
                  <CardDescription>{caso.tarefas.length} tarefa(s)</CardDescription>
                </div>
                <div className="flex gap-1.5">
                  <Button size="sm" variant="outline" onClick={() => checklistPreviewQuery.mutate()}>
                    <ListChecks className="h-3.5 w-3.5 mr-1" />
                    Checklist
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => setAddTaskOpen(true)}>
                    <Plus className="h-3.5 w-3.5 mr-1" />
                    Adicionar
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {caso.tarefas.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-4">Nenhuma tarefa cadastrada</p>
                ) : (
                  <div className="space-y-2">
                    {caso.tarefas.slice(0, 5).map(tarefa => (
                      <div key={tarefa.id} className="flex items-center justify-between p-2 rounded-lg border">
                        <div className="flex items-center gap-2">
                          {tarefa.status === 'concluida' ? (
                            <CheckCircle2 className="h-3.5 w-3.5 text-green-500 shrink-0" />
                          ) : (
                            <Clock className="h-3.5 w-3.5 text-yellow-500 shrink-0" />
                          )}
                          <div>
                            <p className={`font-medium text-sm ${tarefa.status === 'concluida' ? 'line-through text-muted-foreground' : ''}`}>
                              {tarefa.titulo}
                            </p>
                            <div className="flex items-center gap-1.5 mt-0.5">
                              <Badge variant="outline" className="text-[10px]">{tarefa.prioridade_display}</Badge>
                              <span className="text-[10px] text-muted-foreground">{tarefa.status_display}</span>
                            </div>
                          </div>
                        </div>
                        {tarefa.data_limite && (
                          <p className="text-[10px] text-muted-foreground shrink-0 ml-3">
                            {formatDate(tarefa.data_limite)}
                          </p>
                        )}
                      </div>
                    ))}
                    {caso.tarefas.length > 5 && (
                      <p className="text-xs text-muted-foreground text-center pt-1">
                        +{caso.tarefas.length - 5} tarefa(s) adicionais
                      </p>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* CRONOGRAMA */}
        <TabsContent value="cronograma" className="mt-4">
          <CasePhases caseId={caseId} caso={caso} />
        </TabsContent>

        {/* ATIVIDADES (merged Timeline) */}
        <TabsContent value="atividades" className="mt-4">
          <CaseTimeline caseId={caseId} />
        </TabsContent>

        {/* DOCUMENTOS */}
        <TabsContent value="documentos" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Documentos do Caso
                </CardTitle>
                <CardDescription>
                  Peças, simulações e arquivos vinculados ao processo
                </CardDescription>
              </div>
              <Button size="sm" asChild className="w-full sm:w-auto mt-2 sm:mt-0">
                <Link href={`/dashboard/intelligent-assistant?case_id=${caseId}`}>
                  <Plus className="h-4 w-4 mr-2" />
                  Gerar Peca
                </Link>
              </Button>
            </CardHeader>
            <CardContent>
              {!caso.documentos_caso || caso.documentos_caso.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <FileText className="h-10 w-10 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">Nenhum documento vinculado</p>
                  <p className="text-xs mt-1 text-muted-foreground">
                    Gere peças pelo Assistente Inteligente e vincule a este caso
                  </p>
                  <Button asChild size="sm" variant="outline" className="mt-3">
                    <Link href="/dashboard/intelligent-assistant">
                      Ir ao Gerador de Peças
                    </Link>
                  </Button>
                </div>
              ) : (
                <div className="space-y-2">
                  {caso.documentos_caso.map(doc => {
                    const docContent = (
                      <div className={`flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 rounded-lg border ${doc.generated_document_id ? 'group hover:border-primary/40 hover:shadow-sm cursor-pointer' : ''} transition-all duration-150`}>
                        <div className="flex items-center gap-3">
                          <FileText className="h-4 w-4 text-primary shrink-0" />
                          <div>
                            <p className={`font-medium text-sm ${doc.generated_document_id ? 'group-hover:text-primary transition-colors' : ''}`}>{doc.titulo}</p>
                            <div className="flex items-center gap-2 mt-0.5">
                              <Badge variant="outline" className="text-xs">{doc.tipo_display}</Badge>
                              {doc.descricao && (
                                <span className="text-xs text-muted-foreground truncate max-w-[150px] sm:max-w-[300px]">
                                  {doc.descricao}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 shrink-0 ml-4">
                          <p className="text-xs text-muted-foreground">
                            {formatDate(doc.data_documento || doc.created_at)}
                          </p>
                          {doc.generated_document_id && (
                            <ExternalLink className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                          )}
                        </div>
                      </div>
                    );
                    return doc.generated_document_id ? (
                      <Link key={doc.id} href={`/dashboard/document-generators?doc_id=${doc.generated_document_id}`}>
                        {docContent}
                      </Link>
                    ) : (
                      <div key={doc.id}>{docContent}</div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* NOTIFICACOES */}
        <TabsContent value="notificacoes" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Bell className="h-5 w-5" />
                  Notificações Jurídicas
                </CardTitle>
                <CardDescription>
                  Citações, intimações e notificações vinculadas ao processo
                </CardDescription>
              </div>
              <Button size="sm" onClick={() => setAddNotificationOpen(true)} className="w-full sm:w-auto mt-2 sm:mt-0">
                <Plus className="h-4 w-4 mr-2" />
                Registrar
              </Button>
            </CardHeader>
            <CardContent>
              {!caso.notificacoes || caso.notificacoes.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Bell className="h-10 w-10 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">Nenhuma notificação registrada</p>
                  <p className="text-xs mt-1 text-muted-foreground">
                    Registre citações, intimações e notificações recebidas ou enviadas
                  </p>
                  <Button size="sm" variant="outline" className="mt-3" onClick={() => setAddNotificationOpen(true)}>
                    Registrar Notificação
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  {caso.notificacoes.map(notif => {
                    const direcaoColor = notif.direcao === 'recebida' ? 'text-blue-600' : 'text-green-600';
                    const DirecaoIcon = notif.direcao === 'recebida' ? ArrowDownLeft : ArrowUpRight;
                    const statusColor =
                      notif.status === 'pendente' ? 'bg-yellow-100 text-yellow-800' :
                      notif.status === 'efetivada' ? 'bg-green-100 text-green-800' :
                      notif.status === 'frustrada' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800';

                    return (
                      <div key={notif.id} className="p-3 rounded-lg border hover:border-primary/30 transition-colors">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                          <div className="flex items-start gap-3">
                            <div className={`mt-0.5 ${direcaoColor}`}>
                              <DirecaoIcon className="h-4 w-4" />
                            </div>
                            <div>
                              <div className="flex items-center gap-2 flex-wrap">
                                <p className="font-medium text-sm">{notif.tipo_display}</p>
                                <Badge variant="outline" className="text-[10px]">{notif.direcao_display}</Badge>
                                <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium ${statusColor}`}>
                                  {notif.status_display}
                                </span>
                              </div>
                              {notif.destinatario_nome && (
                                <p className="text-xs text-muted-foreground mt-0.5">
                                  Dest.: {notif.destinatario_nome}
                                </p>
                              )}
                              {notif.meio_display && (
                                <p className="text-xs text-muted-foreground">
                                  Via: {notif.meio_display}
                                </p>
                              )}
                              {notif.conteudo_resumo && (
                                <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                                  {notif.conteudo_resumo}
                                </p>
                              )}
                              {notif.base_legal && (
                                <p className="text-[10px] text-muted-foreground mt-0.5">
                                  Base legal: {notif.base_legal}
                                </p>
                              )}
                            </div>
                          </div>
                          <div className="text-right shrink-0 space-y-0.5">
                            {notif.data_ciencia && (
                              <p className="text-xs">
                                <span className="text-muted-foreground">Ciência: </span>
                                <span className="font-medium">{formatDate(notif.data_ciencia)}</span>
                              </p>
                            )}
                            {notif.data_publicacao_dje && (
                              <p className="text-xs">
                                <span className="text-muted-foreground">DJe: </span>
                                <span className="font-medium">{formatDate(notif.data_publicacao_dje)}</span>
                              </p>
                            )}
                            {notif.prazo_vencimento && (
                              <p className="text-xs">
                                <span className="text-muted-foreground">Prazo: </span>
                                <span className="font-semibold text-red-600">{formatDate(notif.prazo_vencimento)}</span>
                                {notif.prazo_dias && (
                                  <span className="text-muted-foreground ml-1">
                                    ({notif.prazo_dias}d {notif.prazo_tipo_display?.toLowerCase()})
                                  </span>
                                )}
                              </p>
                            )}
                            {notif.deadline_created && (
                              <p className="text-[10px] text-green-600 flex items-center gap-1 justify-end">
                                <CheckCircle2 className="h-3 w-3" />
                                Prazo criado
                              </p>
                            )}
                            <p className="text-[10px] text-muted-foreground">
                              {formatDate(notif.created_at)}
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* FLUXO DE TRABALHO */}
        <TabsContent value="fluxo" className="mt-4">
          <FlowPanel
            caseId={caso.id}
            activeFlowId={caso.active_flow_id ?? null}
            activeFlowStatus={caso.active_flow_status ?? null}
            activeFlowNode={caso.active_flow_node ?? null}
            activeFlowPendingTasks={caso.active_flow_pending_tasks ?? 0}
            activeFlowTemplateName={caso.active_flow_template_name ?? null}
          />
        </TabsContent>
      </Tabs>

      {/* Mobile bottom actions bar */}
      <div className="sm:hidden fixed bottom-0 left-0 right-0 z-40 bg-background/95 backdrop-blur-sm border-t px-4 py-3 flex items-center gap-2">
        <Button variant="outline" size="sm" asChild className="flex-1 min-h-[44px]">
          <Link href={`/dashboard/processos/${caseId}/editar`}>
            <Pencil className="h-4 w-4 mr-1.5" />
            Editar
          </Link>
        </Button>
        <Button size="sm" asChild className="flex-1 min-h-[44px]">
          <Link href={`/dashboard/copilot?prompt=${encodeURIComponent(
            `Analise o caso "${caso.titulo}" (${caso.especialidade_display}). Status: ${caso.status_display}. Fase: ${caso.fase_display}.`
          )}`}>
            <Bot className="h-4 w-4 mr-1.5" />
            Copilot
          </Link>
        </Button>
      </div>

      {/* Dialog: Adicionar Prazo */}
      <Dialog open={addDeadlineOpen} onOpenChange={setAddDeadlineOpen}>
        <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Adicionar Prazo</DialogTitle>
            <DialogDescription>Cadastre um novo prazo processual para este caso.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Título do Prazo *</Label>
              <AIInput
                placeholder="Ex: Prazo para contestação"
                value={deadlineForm.titulo}
                onChange={e => setDeadlineForm(p => ({ ...p, titulo: e.target.value }))}
                setValue={v => setDeadlineForm(p => ({ ...p, titulo: v }))}
                aiContext="título de prazo processual judicial"
                aiObjective="Sugira um título claro e objetivo para o prazo processual, indicando sua natureza jurídica"
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Data do Prazo *</Label>
                <Input
                  type="date"
                  value={deadlineForm.data_prazo}
                  onChange={e => setDeadlineForm(p => ({ ...p, data_prazo: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>Tipo</Label>
                <Select value={deadlineForm.tipo} onValueChange={v => setDeadlineForm(p => ({ ...p, tipo: v }))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="processual">Processual</SelectItem>
                    <SelectItem value="recursal">Recursal</SelectItem>
                    <SelectItem value="extrajudicial">Extrajudicial</SelectItem>
                    <SelectItem value="contratual">Contratual</SelectItem>
                    <SelectItem value="prescricional">Prescricional</SelectItem>
                    <SelectItem value="decadencial">Decadencial</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Prioridade</Label>
              <Select value={deadlineForm.prioridade} onValueChange={v => setDeadlineForm(p => ({ ...p, prioridade: v }))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="baixa">Baixa</SelectItem>
                  <SelectItem value="media">Média</SelectItem>
                  <SelectItem value="alta">Alta</SelectItem>
                  <SelectItem value="urgente">Urgente</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Descrição</Label>
              <AITextarea
                placeholder="Detalhes sobre o prazo..."
                className="min-h-[80px]"
                value={deadlineForm.descricao}
                onChange={e => setDeadlineForm(p => ({ ...p, descricao: e.target.value }))}
                setValue={v => setDeadlineForm(p => ({ ...p, descricao: v }))}
                aiContext="descrição de prazo processual judicial"
                aiObjective="Elabore uma descrição técnica e objetiva do prazo processual, incluindo fundamentação legal e consequências de seu descumprimento"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddDeadlineOpen(false)}>Cancelar</Button>
            <Button
              onClick={() => addDeadlineMutation.mutate(deadlineForm)}
              disabled={!deadlineForm.titulo || !deadlineForm.data_prazo || addDeadlineMutation.isPending}
            >
              {addDeadlineMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Salvar Prazo
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog: Adicionar Tarefa */}
      <Dialog open={addTaskOpen} onOpenChange={setAddTaskOpen}>
        <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Adicionar Tarefa</DialogTitle>
            <DialogDescription>Cadastre uma nova tarefa para este caso.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Título da Tarefa *</Label>
              <Input
                placeholder="Ex: Elaborar petição inicial"
                value={taskForm.titulo}
                onChange={e => setTaskForm(p => ({ ...p, titulo: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Data Limite</Label>
                <Input
                  type="date"
                  value={taskForm.data_limite}
                  onChange={e => setTaskForm(p => ({ ...p, data_limite: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>Prioridade</Label>
                <Select value={taskForm.prioridade} onValueChange={v => setTaskForm(p => ({ ...p, prioridade: v }))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="baixa">Baixa</SelectItem>
                    <SelectItem value="media">Média</SelectItem>
                    <SelectItem value="alta">Alta</SelectItem>
                    <SelectItem value="urgente">Urgente</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Descrição</Label>
              <div className="relative">
                <Textarea
                  placeholder="Detalhes da tarefa..."
                  className="min-h-[80px] pr-32"
                  value={taskForm.descricao}
                  onChange={e => setTaskForm(p => ({ ...p, descricao: e.target.value }))}
                />
                <div className="absolute top-1 right-1">
                  <AIEnhanceButton
                    value={taskForm.descricao}
                    onEnhance={(text) => setTaskForm(p => ({ ...p, descricao: text }))}
                    context="descrição de tarefa processual"
                  />
                </div>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddTaskOpen(false)}>Cancelar</Button>
            <Button
              onClick={() => addTaskMutation.mutate(taskForm)}
              disabled={!taskForm.titulo || addTaskMutation.isPending}
            >
              {addTaskMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Salvar Tarefa
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog: Calcular Prazo Recursal (#6) */}
      <Dialog open={appealDialogOpen} onOpenChange={setAppealDialogOpen}>
        <DialogContent className="sm:max-w-[520px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Calcular Prazo Recursal</DialogTitle>
            <DialogDescription>Selecione o tipo de recurso e a data de intimacao para calcular o prazo final em dias uteis.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Tipo de Recurso *</Label>
              <Select value={appealForm.appeal_type} onValueChange={v => {
                setAppealForm(p => ({ ...p, appeal_type: v }));
                setAppealResult(null);
              }}>
                <SelectTrigger><SelectValue placeholder="Selecione o recurso" /></SelectTrigger>
                <SelectContent>
                  {tiposRecurso && Object.entries(tiposRecurso).map(([key, info]) => (
                    <SelectItem key={key} value={key}>
                      {info.descricao} ({info.dias} dias)
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Data de Intimacao *</Label>
              <Input
                type="date"
                value={appealForm.intimation_date}
                onChange={e => {
                  setAppealForm(p => ({ ...p, intimation_date: e.target.value }));
                  setAppealResult(null);
                }}
              />
            </div>
            {appealForm.appeal_type && tiposRecurso?.[appealForm.appeal_type] && (
              <div className="rounded-lg border p-3 bg-muted/50">
                <p className="text-xs font-medium text-muted-foreground">Base Legal</p>
                <p className="text-sm font-medium">{tiposRecurso[appealForm.appeal_type].base_legal}</p>
                <p className="text-xs text-muted-foreground mt-1">{tiposRecurso[appealForm.appeal_type].dias} dias uteis</p>
              </div>
            )}
            <Button
              variant="secondary"
              className="w-full"
              disabled={!appealForm.appeal_type || !appealForm.intimation_date || calcularRecursalMutation.isPending}
              onClick={() => calcularRecursalMutation.mutate(appealForm)}
            >
              {calcularRecursalMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Scale className="h-4 w-4 mr-2" />}
              Calcular Prazo
            </Button>
            {appealResult && (
              <div className="rounded-lg border p-4 bg-green-50 dark:bg-green-950/20 space-y-1">
                <p className="text-sm font-semibold text-green-800 dark:text-green-200">Prazo Calculado</p>
                <p className="text-lg font-bold">{new Date(appealResult.deadline_date + 'T00:00:00').toLocaleDateString('pt-BR')}</p>
                <p className="text-xs text-muted-foreground">{appealResult.descricao} - {appealResult.dias} dias uteis</p>
                <p className="text-xs text-muted-foreground">Base legal: {appealResult.base_legal}</p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAppealDialogOpen(false)}>Cancelar</Button>
            <Button
              disabled={!appealResult || salvarRecursalMutation.isPending}
              onClick={() => salvarRecursalMutation.mutate({ ...appealForm, caso_id: caseId })}
            >
              {salvarRecursalMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Salvar como Prazo
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog: Aplicar Checklist (#14) */}
      <Dialog open={checklistDialogOpen} onOpenChange={setChecklistDialogOpen}>
        <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Aplicar Checklist</DialogTitle>
            <DialogDescription>
              Checklist para casos de especialidade {caso?.especialidade_display || ''}. As tarefas abaixo serao criadas automaticamente.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 max-h-[400px] overflow-y-auto">
            {checklistPreview.map((item, idx) => (
              <div key={idx} className="flex items-start gap-3 p-3 rounded-lg border">
                <div className="mt-0.5 shrink-0">
                  <Circle className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">{item.titulo}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{item.descricao}</p>
                  <Badge variant="outline" className="text-[10px] mt-1">
                    {item.prioridade === 'urgente' ? 'Urgente' : item.prioridade === 'alta' ? 'Alta' : item.prioridade === 'media' ? 'Media' : 'Baixa'}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setChecklistDialogOpen(false)}>Cancelar</Button>
            <Button
              disabled={applyChecklistMutation.isPending || checklistPreview.length === 0}
              onClick={() => applyChecklistMutation.mutate()}
            >
              {applyChecklistMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <ListChecks className="h-4 w-4 mr-2" />}
              Criar {checklistPreview.length} Tarefa(s)
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog: Registrar Notificação */}
      <Dialog open={addNotificationOpen} onOpenChange={setAddNotificationOpen}>
        <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Registrar Notificação</DialogTitle>
            <DialogDescription>Registre uma citação, intimação ou notificação jurídica.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Tipo *</Label>
                <Select value={notifForm.tipo} onValueChange={v => setNotifForm(p => ({ ...p, tipo: v }))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="citacao_pessoal">Citação Pessoal</SelectItem>
                    <SelectItem value="citacao_hora_certa">Citação por Hora Certa</SelectItem>
                    <SelectItem value="citacao_edital">Citação por Edital</SelectItem>
                    <SelectItem value="citacao_eletronica">Citação Eletrônica</SelectItem>
                    <SelectItem value="intimacao_pessoal">Intimação Pessoal</SelectItem>
                    <SelectItem value="intimacao_dje">Intimação via DJe</SelectItem>
                    <SelectItem value="intimacao_eletronica">Intimação Eletrônica</SelectItem>
                    <SelectItem value="intimacao_publicacao">Intimação por Publicação</SelectItem>
                    <SelectItem value="notificacao_extrajudicial">Notificação Extrajudicial</SelectItem>
                    <SelectItem value="notificacao_judicial">Notificação Judicial</SelectItem>
                    <SelectItem value="carta_precatoria">Carta Precatória</SelectItem>
                    <SelectItem value="carta_rogatoria">Carta Rogatória</SelectItem>
                    <SelectItem value="mandado_citacao">Mandado de Citação</SelectItem>
                    <SelectItem value="mandado_intimacao">Mandado de Intimação</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Direção</Label>
                <Select value={notifForm.direcao} onValueChange={v => setNotifForm(p => ({ ...p, direcao: v }))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="recebida">Recebida</SelectItem>
                    <SelectItem value="enviada">Enviada</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Meio de Comunicação</Label>
                <Select value={notifForm.meio} onValueChange={v => setNotifForm(p => ({ ...p, meio: v }))}>
                  <SelectTrigger><SelectValue placeholder="Selecione..." /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="oficial_justica">Oficial de Justiça</SelectItem>
                    <SelectItem value="correio_ar">Correio (AR)</SelectItem>
                    <SelectItem value="dje">Diário de Justiça Eletrônico</SelectItem>
                    <SelectItem value="pje">PJe</SelectItem>
                    <SelectItem value="esaj">e-SAJ</SelectItem>
                    <SelectItem value="whatsapp">WhatsApp</SelectItem>
                    <SelectItem value="email">E-mail</SelectItem>
                    <SelectItem value="cartorio">Cartório de Títulos</SelectItem>
                    <SelectItem value="edital">Edital</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Destinatário</Label>
                <Input
                  placeholder="Nome do destinatário"
                  value={notifForm.destinatario_nome}
                  onChange={e => setNotifForm(p => ({ ...p, destinatario_nome: e.target.value }))}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Remetente</Label>
              <Input
                placeholder="Nome do remetente"
                value={notifForm.remetente}
                onChange={e => setNotifForm(p => ({ ...p, remetente: e.target.value }))}
              />
            </div>
            <Separator />
            <p className="text-sm font-medium">Datas e Prazos</p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="space-y-2">
                <Label>Data Expedição</Label>
                <Input
                  type="date"
                  value={notifForm.data_expedicao}
                  onChange={e => setNotifForm(p => ({ ...p, data_expedicao: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>Data Ciência</Label>
                <Input
                  type="date"
                  value={notifForm.data_ciencia}
                  onChange={e => setNotifForm(p => ({ ...p, data_ciencia: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>Publicação DJe</Label>
                <Input
                  type="date"
                  value={notifForm.data_publicacao_dje}
                  onChange={e => setNotifForm(p => ({ ...p, data_publicacao_dje: e.target.value }))}
                />
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Prazo (dias)</Label>
                <Input
                  type="number"
                  placeholder="Ex: 15"
                  value={notifForm.prazo_dias}
                  onChange={e => setNotifForm(p => ({ ...p, prazo_dias: e.target.value }))}
                />
                <p className="text-[10px] text-muted-foreground">
                  Deixe vazio para usar o prazo padrão do tipo selecionado
                </p>
              </div>
              <div className="space-y-2">
                <Label>Tipo de Prazo</Label>
                <Select value={notifForm.prazo_tipo} onValueChange={v => setNotifForm(p => ({ ...p, prazo_tipo: v }))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="uteis">Dias Úteis</SelectItem>
                    <SelectItem value="corridos">Dias Corridos</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            {(notifForm.data_ciencia || notifForm.data_publicacao_dje) && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-xs font-medium text-blue-800 flex items-center gap-1.5">
                  <Timer className="h-3.5 w-3.5" />
                  Prazo será calculado automaticamente ao salvar
                </p>
                <p className="text-[10px] text-blue-600 mt-0.5">
                  Um prazo processual (LegalDeadline) será criado automaticamente para este caso
                </p>
              </div>
            )}
            <Separator />
            <div className="space-y-2">
              <Label>Base Legal</Label>
              <AIInput
                placeholder="Ex: CPC art. 335"
                value={notifForm.base_legal}
                onChange={e => setNotifForm(p => ({ ...p, base_legal: e.target.value }))}
                setValue={v => setNotifForm(p => ({ ...p, base_legal: v }))}
                aiContext="base legal de notificação processual"
                aiObjective="Indique o dispositivo legal aplicável (lei, artigo, inciso) que fundamenta esta notificação"
              />
            </div>
            <div className="space-y-2">
              <Label>Resumo do Conteúdo</Label>
              <AITextarea
                placeholder="Resumo do conteúdo da notificação..."
                className="min-h-[60px]"
                value={notifForm.conteudo_resumo}
                onChange={e => setNotifForm(p => ({ ...p, conteudo_resumo: e.target.value }))}
                setValue={v => setNotifForm(p => ({ ...p, conteudo_resumo: v }))}
                aiContext="resumo de conteúdo de notificação processual"
                aiObjective="Elabore um resumo claro e técnico do conteúdo da notificação, identificando objeto, obrigações e prazos"
              />
            </div>
            <div className="space-y-2">
              <Label>Observações</Label>
              <AITextarea
                placeholder="Observações adicionais..."
                className="min-h-[60px]"
                value={notifForm.observacoes}
                onChange={e => setNotifForm(p => ({ ...p, observacoes: e.target.value }))}
                setValue={v => setNotifForm(p => ({ ...p, observacoes: v }))}
                aiContext="observações sobre notificação processual"
                aiObjective="Acrescente observações técnicas relevantes sobre a notificação, como pendências, irregularidades ou providências necessárias"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddNotificationOpen(false)}>Cancelar</Button>
            <Button
              onClick={() => addNotificationMutation.mutate(notifForm)}
              disabled={!notifForm.tipo || addNotificationMutation.isPending}
            >
              {addNotificationMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Registrar Notificação
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ─── Timeline Component ─────────────────────────────────────────────────────

const TIMELINE_ICON_MAP: Record<string, React.ElementType> = {
  'file-text': FileText,
  'scale': Scale,
  'paperclip': Paperclip,
  'clock': Clock,
  'check-circle': CheckCircle2,
  'gavel': Gavel,
  'mail': Mail,
  'send': Send,
};

const TIMELINE_COLOR_MAP: Record<string, string> = {
  documento_gerado: 'bg-blue-100 text-blue-700',
  simulacao: 'bg-purple-100 text-purple-700',
  documento_caso: 'bg-green-100 text-green-700',
  prazo: 'bg-yellow-100 text-yellow-700',
  tarefa: 'bg-orange-100 text-orange-700',
  audiencia: 'bg-red-100 text-red-700',
  notificacao: 'bg-indigo-100 text-indigo-700',
};

const TIMELINE_TYPE_LABELS: Record<string, string> = {
  documento_gerado: 'Documento Gerado',
  simulacao: 'Simulação',
  documento_caso: 'Documento',
  prazo: 'Prazo',
  tarefa: 'Tarefa',
  audiencia: 'Audiência',
  notificacao: 'Notificação',
};

function CaseTimeline({ caseId }: { caseId: string }) {
  const { data: events, isLoading } = useQuery({
    queryKey: ['case-timeline', caseId],
    queryFn: async () => {
      const res = await api.get(`/api/v1/processos/${caseId}/timeline/`);
      const data = res.data;
      // Handle paginated response ({count, next, results}) or flat array
      const items: TimelineEvent[] = data?.results || (Array.isArray(data) ? data : []);
      return items;
    },
  });

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  // Sort newest first
  const sortedEvents = events ? [...events].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()) : [];

  if (!events || events.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Atividades
          </CardTitle>
          <CardDescription>Histórico completo de ações, documentos e eventos</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <History className="h-10 w-10 mx-auto mb-2 opacity-30" />
            <p className="text-sm">Nenhuma atividade registrada</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5" />
          Atividades
        </CardTitle>
        <CardDescription>
          Histórico completo de ações, documentos e eventos — {sortedEvents.length} evento(s)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="relative">
          {/* Vertical line */}
          <div className="absolute left-4 top-0 bottom-0 w-px bg-border" />

          <div className="space-y-4">
            {sortedEvents.map((event, idx) => {
              const IconComponent = TIMELINE_ICON_MAP[event.icon] || FileText;
              const colorClass = TIMELINE_COLOR_MAP[event.type] || 'bg-gray-100 text-gray-700';
              const typeLabel = TIMELINE_TYPE_LABELS[event.type] || event.type;

              // Determine contextual actions for each event type
              const hasTarefa = event.metadata?.has_task === true;
              const copilotPrompt = encodeURIComponent(
                `Analise a atividade "${event.title}" do tipo "${typeLabel}" ocorrida em ${new Date(event.date).toLocaleDateString('pt-BR')}. ${event.description || ''} O que devo fazer a seguir?`
              );

              return (
                <div key={`${event.type}-${idx}`} className="group relative flex gap-3 sm:gap-4 pl-1">
                  {/* Icon dot */}
                  <div className={`relative z-10 flex h-7 w-7 sm:h-8 sm:w-8 shrink-0 items-center justify-center rounded-full ${colorClass}`}>
                    <IconComponent className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0 pb-3 sm:pb-4">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="font-medium text-sm">{event.title}</p>
                      <Badge variant="outline" className="text-[10px]">{typeLabel}</Badge>
                    </div>
                    {event.description && (
                      <p className="text-xs text-muted-foreground mt-0.5">{event.description}</p>
                    )}
                    <p className="text-[10px] text-muted-foreground mt-1">
                      {new Date(event.date).toLocaleDateString('pt-BR', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>

                    {/* Contextual actions - touch-friendly */}
                    <div className="flex flex-wrap gap-2 mt-2 opacity-100 sm:opacity-70 sm:group-hover:opacity-100 transition-opacity">
                      {/* Copilot — always available */}
                      <Link href={`/dashboard/copilot?prompt=${copilotPrompt}`}>
                        <Button variant="ghost" size="sm" className="min-h-[44px] sm:min-h-0 sm:h-6 px-3 sm:px-2 text-xs sm:text-[10px] gap-1.5 sm:gap-1 text-primary hover:text-primary touch-manipulation">
                          <Bot className="h-4 w-4 sm:h-3 sm:w-3" /> <span className="hidden sm:inline">Perguntar ao Copilot</span><span className="sm:hidden">Copilot</span>
                        </Button>
                      </Link>

                      {/* Document actions */}
                      {event.type === 'documento_gerado' && event.metadata?.session_id && (
                        <Link href={`/dashboard/intelligent-assistant/gerador?session=${event.metadata.session_id}&phase=result`}>
                          <Button variant="ghost" size="sm" className="min-h-[44px] sm:min-h-0 sm:h-6 px-3 sm:px-2 text-xs sm:text-[10px] gap-1.5 sm:gap-1 touch-manipulation">
                            <Eye className="h-4 w-4 sm:h-3 sm:w-3" /> Ver doc
                          </Button>
                        </Link>
                      )}

                      {/* Simulation actions */}
                      {event.type === 'simulação' && (
                        <Link href={`/dashboard/simulations/${event.metadata?.simulation_type === 'jury' ? 'jury' : 'judge'}`}>
                          <Button variant="ghost" size="sm" className="min-h-[44px] sm:min-h-0 sm:h-6 px-3 sm:px-2 text-xs sm:text-[10px] gap-1.5 sm:gap-1 touch-manipulation">
                            <Scale className="h-4 w-4 sm:h-3 sm:w-3" /> Ver sim.
                          </Button>
                        </Link>
                      )}

                      {/* Deadline actions */}
                      {event.type === 'prazo' && (
                        <>
                          {event.metadata?.status === 'pendente' && (
                            <Button variant="ghost" size="sm" className="min-h-[44px] sm:min-h-0 sm:h-6 px-3 sm:px-2 text-xs sm:text-[10px] gap-1.5 sm:gap-1 text-green-600 touch-manipulation">
                              <CheckCircle2 className="h-4 w-4 sm:h-3 sm:w-3" /> Concluir
                            </Button>
                          )}
                          <Link href={`/dashboard/copilot?prompt=${encodeURIComponent(`O prazo "${event.title}" vence em ${event.metadata?.data_prazo ? new Date(event.metadata.data_prazo).toLocaleDateString('pt-BR') : 'breve'}. Quais providências tomar e quais documentos preparar?`)}`}>
                            <Button variant="ghost" size="sm" className="min-h-[44px] sm:min-h-0 sm:h-6 px-3 sm:px-2 text-xs sm:text-[10px] gap-1.5 sm:gap-1 text-amber-600 touch-manipulation">
                              <AlertTriangle className="h-4 w-4 sm:h-3 sm:w-3" /> O que fazer?
                            </Button>
                          </Link>
                        </>
                      )}

                      {/* Task actions */}
                      {event.type === 'tarefa' && event.metadata?.status !== 'concluida' && (
                        <Button variant="ghost" size="sm" className="min-h-[44px] sm:min-h-0 sm:h-6 px-3 sm:px-2 text-xs sm:text-[10px] gap-1.5 sm:gap-1 text-green-600 touch-manipulation">
                          <CheckCircle2 className="h-4 w-4 sm:h-3 sm:w-3" /> Concluir
                        </Button>
                      )}
                      {event.type === 'tarefa' && event.metadata?.status === 'concluida' && (
                        <span className="text-xs sm:text-[10px] text-muted-foreground flex items-center gap-1 min-h-[44px] sm:min-h-0">
                          <Check className="h-4 w-4 sm:h-3 sm:w-3" /> Concluída
                        </span>
                      )}

                      {/* Create task — for events that don't have one yet */}
                      {!hasTarefa && event.type !== 'tarefa' && (
                        <Link href={`/dashboard/copilot?prompt=${encodeURIComponent(`Preciso criar uma tarefa para a atividade "${event.title}" (${typeLabel}). Sugira o título, descrição, prazo e prioridade adequados.`)}`}>
                          <Button variant="ghost" size="sm" className="min-h-[44px] sm:min-h-0 sm:h-6 px-3 sm:px-2 text-xs sm:text-[10px] gap-1.5 sm:gap-1 touch-manipulation">
                            <Plus className="h-4 w-4 sm:h-3 sm:w-3" /> Tarefa
                          </Button>
                        </Link>
                      )}
                      {hasTarefa && event.type !== 'tarefa' && (
                        <span className="text-xs sm:text-[10px] text-muted-foreground flex items-center gap-1 px-2 min-h-[44px] sm:min-h-0">
                          <ListChecks className="h-4 w-4 sm:h-3 sm:w-3" /> Ja criada
                        </span>
                      )}

                      {/* Generate document — for deadlines and phases */}
                      {(event.type === 'prazo' || event.type === 'audiencia') && (
                        <Link href="/dashboard/intelligent-assistant">
                          <Button variant="ghost" size="sm" className="min-h-[44px] sm:min-h-0 sm:h-6 px-3 sm:px-2 text-xs sm:text-[10px] gap-1.5 sm:gap-1 touch-manipulation">
                            <FileText className="h-4 w-4 sm:h-3 sm:w-3" /> Gerar peca
                          </Button>
                        </Link>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}


// ─── Case Phases (Cronograma) Component ─────────────────────────────────────

function CasePhases({ caseId, caso }: { caseId: string; caso: LegalCase }) {
  const queryClient = useQueryClient();
  const [reopenDialogOpen, setReopenDialogOpen] = useState(false);
  const [reopenPhase, setReopenPhase] = useState<CasePhaseData | null>(null);
  const [reopenReason, setReopenReason] = useState('');

  const { data: phases, isLoading } = useQuery({
    queryKey: ['case-phases', caseId],
    queryFn: async () => {
      const res = await api.get<CasePhaseData[]>(`/api/v1/processos/${caseId}/phases/`);
      return res.data;
    },
  });

  const updatePhaseMutation = useMutation({
    mutationFn: async ({ phaseId, data }: { phaseId: string; data: Record<string, any> }) => {
      await api.patch(`/api/v1/processos/${caseId}/phases/${phaseId}/`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['case-phases', caseId] });
      queryClient.invalidateQueries({ queryKey: ['caso', caseId] });
      setReopenDialogOpen(false);
      setReopenPhase(null);
      setReopenReason('');
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || err?.response?.data?.detail || 'Erro ao processar solicitação');
    },
  });

  const handleReopenClick = (phase: CasePhaseData) => {
    setReopenPhase(phase);
    setReopenReason('');
    setReopenDialogOpen(true);
  };

  const handleReopenConfirm = () => {
    if (!reopenPhase || !reopenReason.trim()) return;
    updatePhaseMutation.mutate({
      phaseId: reopenPhase.id,
      data: { status: 'in_progress', reopened_reason: reopenReason.trim() },
    });
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (!phases || phases.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ListOrdered className="h-5 w-5" />
            Cronograma Processual
          </CardTitle>
          <CardDescription>Etapas do processo jurídico em ordem sequencial</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <ListChecks className="h-10 w-10 mx-auto mb-2 opacity-30" />
            <p className="text-sm">Nenhuma fase registrada</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const completedCount = phases.filter(p => p.status === 'completed').length;
  const totalCount = phases.length;
  const progressPercent = Math.round((completedCount / totalCount) * 100);
  const overdueCount = phases.filter(p => p.status === 'overdue' || p.is_overdue).length;

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <CardTitle className="flex items-center gap-2 text-base sm:text-lg">
                <ListOrdered className="h-5 w-5" />
                Cronograma Processual
              </CardTitle>
              <CardDescription className="text-xs sm:text-sm">
                Etapas do processo jurídico em ordem sequencial — {completedCount} de {totalCount} concluídas ({progressPercent}%)
                {overdueCount > 0 && (
                  <span className="text-red-600 font-medium"> — {overdueCount} atrasada(s)</span>
                )}
              </CardDescription>
            </div>
            <div className="text-left sm:text-right">
              <Badge variant="outline" className="text-xs">
                {caso.especialidade_display}
              </Badge>
            </div>
          </div>
          {/* Progress bar */}
          <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
            <div
              className="bg-green-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </CardHeader>
        <CardContent>
          <div className="relative">
            {/* Vertical line */}
            <div className="absolute left-[15px] top-0 bottom-0 w-0.5 bg-gray-200" />

            <div className="space-y-1">
              {phases.map((phase, idx) => {
                const isCompleted = phase.status === 'completed';
                const isInProgress = phase.status === 'in_progress';
                const isPending = phase.status === 'pending';
                const isSkipped = phase.status === 'skipped';
                const isOverdue = phase.status === 'overdue' || phase.is_overdue;
                const isReopened = !!phase.reopened_at;
                const daysOverdue = phase.days_overdue || 0;

                return (
                  <div key={phase.id} className={`relative flex gap-3 sm:gap-4 pl-0 group ${isOverdue ? 'rounded-lg border border-red-200 bg-red-50/50 p-2 -ml-2' : ''}`}>
                    {/* Status icon */}
                    <div className="relative z-10 flex shrink-0">
                      {isCompleted ? (
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-green-100 text-green-700 ring-2 ring-green-200">
                          <Check className="h-4 w-4" />
                        </div>
                      ) : isOverdue ? (
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-red-100 text-red-700 ring-2 ring-red-300 animate-pulse">
                          <AlertTriangle className="h-4 w-4" />
                        </div>
                      ) : isInProgress ? (
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-blue-700 ring-2 ring-blue-300 animate-pulse">
                          <Clock className="h-4 w-4" />
                        </div>
                      ) : isSkipped ? (
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-100 text-gray-400 ring-2 ring-gray-200">
                          <Circle className="h-4 w-4" />
                        </div>
                      ) : (
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-50 text-gray-300 ring-2 ring-gray-200">
                          <Circle className="h-4 w-4" />
                        </div>
                      )}
                    </div>

                    {/* Content */}
                    <div className={`flex-1 min-w-0 pb-3 sm:pb-4 ${isPending ? 'opacity-50' : ''}`}>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={`text-xs font-mono ${
                          isCompleted ? 'text-green-600' :
                          isOverdue ? 'text-red-600' :
                          isInProgress ? 'text-blue-600' :
                          'text-gray-400'
                        }`}>
                          {phase.order}.
                        </span>
                        <p className={`font-medium text-sm ${
                          isCompleted ? 'text-green-800' :
                          isOverdue ? 'text-red-800 font-semibold' :
                          isInProgress ? 'text-blue-800 font-semibold' :
                          isSkipped ? 'text-gray-400 line-through' :
                          'text-gray-400'
                        }`}>
                          {phase.name}
                        </p>
                        {isCompleted && (
                          <Badge className="text-[10px] bg-green-100 text-green-700 hover:bg-green-100">
                            Concluída
                          </Badge>
                        )}
                        {isOverdue && (
                          <Badge className="text-[10px] bg-red-100 text-red-700 hover:bg-red-100">
                            ATRASADA ({daysOverdue} dias)
                          </Badge>
                        )}
                        {isInProgress && !isOverdue && (
                          <Badge className="text-[10px] bg-blue-100 text-blue-700 hover:bg-blue-100">
                            Em Andamento
                          </Badge>
                        )}
                        {isReopened && !isCompleted && (
                          <Badge className="text-[10px] bg-yellow-100 text-yellow-700 hover:bg-yellow-100">
                            <RotateCcw className="h-2.5 w-2.5 mr-0.5" />
                            Reaberta
                          </Badge>
                        )}
                        {isInProgress && !isOverdue && (
                          <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-blue-600 bg-blue-50 border border-blue-200 rounded-full px-2 py-0.5">
                            <MapPin className="h-3 w-3" />
                            Voce esta aqui
                          </span>
                        )}
                      </div>

                      {/* Reopened info */}
                      {isReopened && !isCompleted && (
                        <div className="flex items-start gap-1 mt-1 text-[11px] text-yellow-700 bg-yellow-50 rounded px-2 py-1 border border-yellow-200">
                          <RotateCcw className="h-3 w-3 shrink-0 mt-0.5" />
                          <span>
                            Reaberta em {formatDate(phase.reopened_at)}: &ldquo;{phase.reopened_reason}&rdquo;
                          </span>
                        </div>
                      )}

                      {/* Overdue alert */}
                      {isOverdue && (
                        <div className="flex items-start gap-1 mt-1 text-[11px] text-red-700 bg-red-50 rounded px-2 py-1 border border-red-200">
                          <AlertTriangle className="h-3 w-3 shrink-0 mt-0.5" />
                          <span>
                            {isReopened ? 'Atrasada' : 'Prazo estimado'}: {formatDate(phase.estimated_date)} — Atrasada ha {daysOverdue} dias!
                          </span>
                        </div>
                      )}

                      {/* Description */}
                      {phase.description && (
                        <p className={`text-xs mt-0.5 ${
                          isCompleted ? 'text-green-600/70' :
                          isOverdue ? 'text-red-600/70' :
                          isInProgress ? 'text-blue-600/70' :
                          'text-gray-400'
                        }`}>
                          {phase.description}
                        </p>
                      )}

                      {/* Date info */}
                      <div className="flex items-center gap-3 mt-1">
                        {phase.actual_date && (
                          <span className="text-[11px] text-green-600 flex items-center gap-1">
                            <Check className="h-3 w-3" />
                            {formatDate(phase.actual_date)}
                          </span>
                        )}
                        {!phase.actual_date && phase.estimated_date && !isOverdue && (
                          <span className={`text-[11px] flex items-center gap-1 ${
                            isInProgress ? 'text-blue-500' : 'text-gray-400'
                          }`}>
                            <Calendar className="h-3 w-3" />
                            {isInProgress ? 'Prazo: ' : 'Estimativa: '}
                            {formatDate(phase.estimated_date)}
                          </span>
                        )}
                      </div>

                      {/* Action buttons for overdue phase */}
                      {isOverdue && (
                        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 mt-2">
                          <Button
                            size="sm"
                            variant="outline"
                            className="min-h-[44px] sm:min-h-0 sm:h-7 text-xs w-full sm:w-auto border-green-300 text-green-700 hover:bg-green-50 touch-manipulation"
                            onClick={() => updatePhaseMutation.mutate({
                              phaseId: phase.id,
                              data: { status: 'completed' },
                            })}
                            disabled={updatePhaseMutation.isPending}
                          >
                            <Check className="h-3 w-3 mr-1" />
                            Marcar concluida
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="min-h-[44px] sm:min-h-0 sm:h-7 text-xs w-full sm:w-auto border-red-300 text-red-700 hover:bg-red-50 touch-manipulation"
                            asChild
                          >
                            <Link href={`/dashboard/copilot?prompt=${encodeURIComponent(
                              `A etapa '${phase.name}' do processo '${caso.titulo}' (${caso.especialidade_display}) está atrasada há ${daysOverdue} dias. ` +
                              `O prazo estimado era ${formatDate(phase.estimated_date)}. ` +
                              `Analise:\n` +
                              `1. Quais são as consequências processuais deste atraso?\n` +
                              `2. Existe risco de perda de prazo fatal?\n` +
                              `3. Quais providências imediatas devo tomar?\n` +
                              `4. Como posso regularizar a situação?`
                            )}`}>
                              <MessageSquare className="h-3 w-3 mr-1" />
                              Analisar com Copilot
                            </Link>
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="min-h-[44px] sm:min-h-0 sm:h-7 text-xs w-full sm:w-auto touch-manipulation"
                            asChild
                          >
                            <Link href={`/dashboard/intelligent-assistant?case_id=${caseId}`}>
                              <FileText className="h-3 w-3 mr-1" />
                              Gerar Documento
                            </Link>
                          </Button>
                        </div>
                      )}

                      {/* Action buttons for in_progress phase (not overdue) */}
                      {isInProgress && !isOverdue && (
                        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 mt-2">
                          <Button
                            size="sm"
                            variant="outline"
                            className="min-h-[44px] sm:min-h-0 sm:h-7 text-xs w-full sm:w-auto touch-manipulation"
                            onClick={() => updatePhaseMutation.mutate({
                              phaseId: phase.id,
                              data: { status: 'completed' },
                            })}
                            disabled={updatePhaseMutation.isPending}
                          >
                            <Check className="h-3 w-3 mr-1" />
                            Marcar concluida
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="min-h-[44px] sm:min-h-0 sm:h-7 text-xs w-full sm:w-auto touch-manipulation"
                            asChild
                          >
                            <Link href={`/dashboard/copilot?prompt=${encodeURIComponent(
                              `Estou na fase "${phase.name}" do processo "${caso.titulo}" (${caso.especialidade_display}). ` +
                              `${phase.description}. ` +
                              `Cliente: ${caso.cliente_nome}. ` +
                              (caso.parte_contraria ? `Parte contrária: ${caso.parte_contraria}. ` : '') +
                              `O que devo fazer nesta fase? Quais são os próximos passos e cuidados?`
                            )}`}>
                              <MessageSquare className="h-3 w-3 mr-1" />
                              Analisar com Copilot
                            </Link>
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="min-h-[44px] sm:min-h-0 sm:h-7 text-xs w-full sm:w-auto touch-manipulation"
                            asChild
                          >
                            <Link href={`/dashboard/intelligent-assistant?case_id=${caseId}`}>
                              <FileText className="h-3 w-3 mr-1" />
                              Gerar Documento
                            </Link>
                          </Button>
                        </div>
                      )}

                      {/* Action button for completed phases — reopen with modal */}
                      {isCompleted && (
                        <div className="hidden group-hover:flex items-center gap-2 mt-1">
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-6 text-[10px] text-gray-400 hover:text-yellow-600"
                            onClick={() => handleReopenClick(phase)}
                            disabled={updatePhaseMutation.isPending}
                          >
                            <RotateCcw className="h-3 w-3 mr-1" />
                            Reabrir
                          </Button>
                        </div>
                      )}

                      {/* Advance pending phase to in_progress */}
                      {isPending && idx > 0 && phases[idx - 1]?.status !== 'pending' && (
                        <div className="hidden group-hover:flex items-center gap-2 mt-1">
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-6 text-[10px] text-gray-400"
                            onClick={() => updatePhaseMutation.mutate({
                              phaseId: phase.id,
                              data: { status: 'in_progress' },
                            })}
                            disabled={updatePhaseMutation.isPending}
                          >
                            Iniciar esta fase
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Reopen Phase Dialog */}
      <Dialog open={reopenDialogOpen} onOpenChange={setReopenDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reabrir etapa: {reopenPhase?.name}</DialogTitle>
            <DialogDescription>
              Esta etapa foi marcada como concluida. Deseja reabri-la?
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Motivo da reabertura *</Label>
              <AITextarea
                placeholder="Informe o motivo pelo qual esta etapa precisa ser reaberta..."
                className="min-h-[100px]"
                value={reopenReason}
                onChange={e => setReopenReason(e.target.value)}
                setValue={setReopenReason}
                aiContext="motivo de reabertura de etapa processual"
                aiObjective="Elabore uma justificativa técnica e objetiva para a reabertura desta etapa, indicando os fatos e fundamentos que tornam necessária a ação"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setReopenDialogOpen(false)}>
              Cancelar
            </Button>
            <Button
              variant="default"
              className="bg-yellow-600 hover:bg-yellow-700"
              onClick={handleReopenConfirm}
              disabled={!reopenReason.trim() || updatePhaseMutation.isPending}
            >
              {updatePhaseMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <RotateCcw className="h-4 w-4 mr-2" />}
              Reabrir Etapa
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
