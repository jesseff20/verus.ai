'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/use-auth';
import { useDashboardStats, type RecentDocument } from '@/hooks/use-dashboard-stats';
import { useMyTasks, type TaskInstanceDto } from '@/hooks/useFlowExecution';
import { useFlowTemplates } from '@/hooks/useFlowTemplates';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  FileText,
  FileEdit,
  Brain,
  BookOpen,
  Clock,
  CheckCircle,
  AlertCircle,
  Bot,
  RefreshCw,
  Scale,
  Search,
  Gavel,
  BookMarked,
  Bell,
  Calendar,
  Settings,
  MessageSquare,
  PenTool,
  Users,
  Play,
  Inbox,
  Workflow,
} from 'lucide-react';
import Link from 'next/link';
import Image from 'next/image';

// Mapeamento de status para badges
const statusColors: Record<string, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; label: string }> = {
  draft: { variant: 'outline', label: 'Rascunho' },
  in_review: { variant: 'secondary', label: 'Em Revisão' },
  completed: { variant: 'default', label: 'Completo' },
  archived: { variant: 'destructive', label: 'Arquivado' },
};

// Mapeamento de origem para badges
const sourceConfig: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  manual: { label: 'Manual', icon: <FileEdit className="h-3 w-3" />, color: 'bg-slate-100 text-slate-700' },
  generator: { label: 'Gerador', icon: <FileText className="h-3 w-3" />, color: 'bg-blue-100 text-blue-700' },
  assistant: { label: 'Assistente IA', icon: <Bot className="h-3 w-3" />, color: 'bg-purple-100 text-purple-700' },
};

// Formatar data
const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
};

// Formatar tempo relativo (ex: "há 2 horas", "há 3 dias")
const formatRelativeTime = (dateString: string) => {
  const now = new Date();
  const date = new Date(dateString);
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMin < 1) return 'agora';
  if (diffMin < 60) return `há ${diffMin} min`;
  if (diffHours < 24) return `há ${diffHours}h`;
  if (diffDays === 1) return 'ontem';
  if (diffDays < 7) return `há ${diffDays} dias`;
  return formatDate(dateString);
};

// ── Modal obrigatório de tarefas (aparece em toda carga do dashboard) ──

function TaskActionModal({ onClose }: { onClose: () => void }) {
  const router = useRouter();
  const { data: pendingTasks } = useMyTasks('pending');
  const { data: inProgressTasks } = useMyTasks('in_progress');
  const { data: templates } = useFlowTemplates();

  const pendingCount = pendingTasks?.length ?? 0;
  const inProgressCount = inProgressTasks?.length ?? 0;
  const totalActiveTasks = pendingCount + inProgressCount;
  const publishedTemplates = templates?.filter((t) => t.status === 'published') ?? [];

  // Tarefa mais urgente (primeiro pending ou in_progress)
  const urgentTask: TaskInstanceDto | undefined = pendingTasks?.[0] ?? inProgressTasks?.[0];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.75)' }}
    >
      <div
        className="w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="mb-5 flex items-start gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/15 text-primary">
            <Workflow size={20} />
          </span>
          <div>
            <h2 className="text-lg font-semibold">Central de Tarefas</h2>
            <p className="mt-0.5 text-sm text-muted-foreground">
              O que deseja fazer agora?
            </p>
          </div>
        </div>

        {/* Cards de ação */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {/* Iniciar nova tarefa */}
          <button
            type="button"
            onClick={() => {
              onClose();
              router.push('/dashboard/fluxos');
            }}
            className="group relative rounded-lg border border-primary/20 bg-primary/5 p-4 text-left transition-all hover:border-primary/40 hover:bg-primary/10"
          >
            <span className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-primary/20 text-primary">
              <Play size={17} />
            </span>
            <span className="block text-sm font-semibold">Iniciar nova tarefa</span>
            <span className="mt-1 block text-xs leading-relaxed text-muted-foreground">
              Selecione um fluxo publicado e inicie uma nova jornada de trabalho.
            </span>
            {publishedTemplates.length > 0 && (
              <span className="mt-2 inline-block rounded-full bg-primary/15 px-2 py-0.5 text-[10px] font-medium text-primary">
                {publishedTemplates.length} fluxo{publishedTemplates.length !== 1 ? 's' : ''} disponíve{publishedTemplates.length !== 1 ? 'is' : 'l'}
              </span>
            )}
          </button>

          {/* Finalizar tarefa */}
          <button
            type="button"
            onClick={() => {
              onClose();
              router.push('/dashboard/minhas-tarefas');
            }}
            className={`group relative rounded-lg border p-4 text-left transition-all ${
              totalActiveTasks > 0
                ? 'border-amber-500/30 bg-amber-500/5 hover:border-amber-500/50 hover:bg-amber-500/10'
                : 'border-foreground/10 bg-foreground/[0.03] hover:border-foreground/20 hover:bg-foreground/[0.06]'
            }`}
          >
            <span className={`mb-3 flex h-9 w-9 items-center justify-center rounded-lg ${
              totalActiveTasks > 0
                ? 'bg-amber-500/20 text-amber-500'
                : 'bg-muted text-muted-foreground'
            }`}>
              <Inbox size={17} />
            </span>
            <span className="block text-sm font-semibold">Finalizar tarefa</span>
            <span className="mt-1 block text-xs leading-relaxed text-muted-foreground">
              {totalActiveTasks > 0
                ? `Você tem ${totalActiveTasks} tarefa${totalActiveTasks !== 1 ? 's' : ''} aguardando sua ação.`
                : 'Nenhuma tarefa pendente no momento.'}
            </span>
            {totalActiveTasks > 0 && (
              <span className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-amber-500/15 px-2 py-0.5 text-[10px] font-medium text-amber-600 dark:text-amber-400">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-pulse" />
                {pendingCount > 0 && `${pendingCount} pendente${pendingCount !== 1 ? 's' : ''}`}
                {pendingCount > 0 && inProgressCount > 0 && ' · '}
                {inProgressCount > 0 && `${inProgressCount} em andamento`}
              </span>
            )}
            {urgentTask && (
              <span className="mt-2 block truncate text-[10px] text-muted-foreground">
                Mais recente: {urgentTask.label}
              </span>
            )}
          </button>
        </div>

        {/* Quick links */}
        <div className="mt-4 flex items-center justify-between border-t border-border pt-4">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => { onClose(); router.push('/dashboard/execucoes'); }}
              className="text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              Ver execuções
            </button>
            <span className="text-muted-foreground/30">·</span>
            <button
              type="button"
              onClick={() => { onClose(); router.push('/dashboard/solicitacoes'); }}
              className="text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              Solicitações
            </button>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-accent transition-all"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const { user } = useAuth();
  const { stats, recentDocuments, isLoading, isFetching, refetch } = useDashboardStats();
  const [showTaskModal, setShowTaskModal] = useState(false);

  // Mostrar modal de tarefas em toda carga do dashboard
  useEffect(() => {
    setShowTaskModal(true);
  }, []);

  // Upcoming reminders (next 7 days, show top 3)
  const { data: upcomingReminders } = useQuery<Array<{
    id: number; title: string; scheduled_date: string;
    priority: string; priority_display: string;
    frequency_display: string; copilot_prompt: string;
  }>>({
    queryKey: ['reminders-upcoming'],
    queryFn: async () => {
      const res = await api.get('/api/v1/auth/reminders/upcoming/');
      const data = res.data.results ?? res.data;
      return (data as Array<{ id: number; title: string; scheduled_date: string; priority: string; priority_display: string; frequency_display: string; copilot_prompt: string }>).slice(0, 3);
    },
  });

  // Portal activity (last client activities)
  const { data: portalActivity } = useQuery<{
    activities: Array<{
      type: string; icon: string; title: string; description: string;
      case: string | null; case_id: string | null; date: string; is_read: boolean;
    }>;
    total: number;
  }>({
    queryKey: ['portal-activity'],
    queryFn: async () => {
      const res = await api.get('/api/v1/processos/atividade-portal/');
      return res.data;
    },
  });

  // Cards de estatisticas - usam dados reais quando disponíveis
  const statsCards = [
    {
      title: 'Peças Processuais',
      value: stats?.documents.total ?? '-',
      description: `${stats?.documents.traditional ?? 0} manuais + ${stats?.documents.assistant ?? 0} via IA`,
      icon: Scale,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100 dark:bg-blue-950',
    },
    {
      title: 'Em Revisão',
      value: stats?.documents.by_status.in_review ?? '-',
      description: 'Aguardando revisão',
      icon: Clock,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100 dark:bg-yellow-950',
    },
    {
      title: 'Finalizadas',
      value: stats?.documents.by_status.completed ?? '-',
      description: 'Peças concluídas',
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-100 dark:bg-green-950',
    },
    {
      title: 'Base Jurídica',
      value: stats?.knowledge_base.total ?? '-',
      description: 'Documentos indexados',
      icon: BookMarked,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100 dark:bg-purple-950',
    },
  ];

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Modal obrigatório de tarefas */}
      {showTaskModal && <TaskActionModal onClose={() => setShowTaskModal(false)} />}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Image src="/logo.png" alt="Verus.AI" width={40} height={40} className="h-9 w-9 object-contain shrink-0 hidden sm:block" unoptimized />
          <div>
          <h1 className="text-lg sm:text-2xl md:text-3xl font-bold tracking-tight">
            Bem-vindo, {user?.first_name || user?.username}!
          </h1>
          <p className="text-muted-foreground text-sm sm:text-base">
            Aqui está um resumo das suas atividades no Verus.AI
          </p>
          </div>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
          <Link href="/dashboard/dashboard-config">
            <Button variant="outline" size="sm" title="Configurar Dashboard">
              <Settings className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </div>

      {/* Cards de Estatisticas */}
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        {statsCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-1 sm:pb-2 p-3 sm:p-6">
                <CardTitle className="text-xs sm:text-sm font-medium leading-tight">{stat.title}</CardTitle>
                <div className={`p-1.5 sm:p-2 rounded-lg ${stat.bgColor}`}>
                  <Icon className={`h-3.5 w-3.5 sm:h-4 sm:w-4 ${stat.color}`} />
                </div>
              </CardHeader>
              <CardContent className="px-3 pb-3 sm:px-6 sm:pb-6 pt-0">
                {isLoading ? (
                  <>
                    <Skeleton className="h-7 sm:h-8 w-12 sm:w-16 mb-1" />
                    <Skeleton className="h-3 sm:h-4 w-20 sm:w-24" />
                  </>
                ) : (
                  <>
                    <div className="text-xl sm:text-2xl font-bold">{stat.value}</div>
                    <p className="text-[10px] sm:text-xs text-muted-foreground flex items-center gap-1 leading-tight">
                      {stat.description}
                    </p>
                  </>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Grid de Documentos Recentes e Ações Rapidas */}
      <div className="grid gap-4 sm:gap-6 grid-cols-1 lg:grid-cols-2">
        {/* Documentos Recentes */}
        <Card>
          <CardHeader>
            <CardTitle>Peças Recentes</CardTitle>
            <CardDescription>Últimas peças processuais criadas</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex items-center justify-between p-3 rounded-lg border">
                    <div className="space-y-2">
                      <Skeleton className="h-4 w-48" />
                      <Skeleton className="h-3 w-32" />
                    </div>
                    <Skeleton className="h-6 w-20" />
                  </div>
                ))}
              </div>
            ) : recentDocuments.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Scale className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>Nenhuma peça processual encontrada</p>
              </div>
            ) : (
              <div className="space-y-2 sm:space-y-4">
                {recentDocuments.map((doc: RecentDocument) => {
                  const source = sourceConfig[doc.source] || sourceConfig.manual;
                  const status = statusColors[doc.status] || { variant: 'outline' as const, label: doc.status_display };

                  return (
                    <div
                      key={`${doc.system}-${doc.id}`}
                      className="flex items-start sm:items-center justify-between p-2.5 sm:p-3 rounded-lg border hover:bg-accent transition-colors gap-2 min-h-[44px]"
                    >
                      <div className="space-y-1 flex-1 min-w-0">
                        <p className="font-medium leading-tight text-sm sm:text-base truncate" title={doc.title}>
                          {doc.title}
                        </p>
                        <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 text-xs sm:text-sm text-muted-foreground">
                          <Badge variant="outline" className={`${source.color} gap-1 text-[10px] sm:text-xs`}>
                            {source.icon}
                            {source.label}
                          </Badge>
                          <span className="text-[10px] sm:text-xs">{formatDate(doc.created_at)}</span>
                        </div>
                      </div>
                      <Badge variant={status.variant} className="text-[10px] sm:text-xs shrink-0">{status.label}</Badge>
                    </div>
                  );
                })}
              </div>
            )}
            <Link href="/dashboard/documents">
              <Button variant="outline" className="w-full mt-4">
                Ver todas as Peças
              </Button>
            </Link>
          </CardContent>
        </Card>

        {/* Ações Rapidas */}
        <Card>
          <CardHeader>
            <CardTitle>Ações Rápidas</CardTitle>
            <CardDescription>Acesso rápido às funcionalidades jurídicas</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <Link href="/dashboard/intelligent-assistant">
              <Button className="w-full justify-start h-11 sm:h-10 text-sm" variant="outline">
                <Gavel className="mr-2 h-4 w-4 shrink-0" />
                Gerar Peça Processual
              </Button>
            </Link>
            <Link href="/dashboard/processos/novo">
              <Button className="w-full justify-start h-11 sm:h-10 text-sm" variant="outline">
                <FileText className="mr-2 h-4 w-4 shrink-0" />
                Novo Caso Jurídico
              </Button>
            </Link>
            <Link href="/dashboard/jurisprudencia">
              <Button className="w-full justify-start h-11 sm:h-10 text-sm" variant="outline">
                <Search className="mr-2 h-4 w-4 shrink-0" />
                Pesquisar Jurisprudência
              </Button>
            </Link>
            <Link href="/dashboard/processos">
              <Button className="w-full justify-start h-11 sm:h-10 text-sm" variant="outline">
                <Scale className="mr-2 h-4 w-4 shrink-0" />
                Meus Casos Jurídicos
              </Button>
            </Link>
            <Link href="/dashboard/knowledge-base">
              <Button className="w-full justify-start h-11 sm:h-10 text-sm" variant="outline">
                <BookMarked className="mr-2 h-4 w-4 shrink-0" />
                Base Jurídica
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Próximos Lembretes */}
      {upcomingReminders && upcomingReminders.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Próximos Lembretes
            </CardTitle>
            <CardDescription>Lembretes dos próximos 7 dias</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {upcomingReminders.map((r) => {
                const priorityBg: Record<string, string> = {
                  low: 'bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800',
                  medium: 'bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-900',
                  high: 'bg-orange-50 dark:bg-orange-950 border-orange-200 dark:border-orange-900',
                  urgent: 'bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-900',
                };
                return (
                  <div
                    key={r.id}
                    className={`flex items-start gap-2.5 sm:gap-3 p-2.5 sm:p-3 rounded-lg border ${priorityBg[r.priority] || priorityBg.medium}`}
                  >
                    <Calendar className="h-4 w-4 sm:h-5 sm:w-5 mt-0.5 text-muted-foreground shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-xs sm:text-sm truncate">{r.title}</p>
                      <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 text-[10px] sm:text-xs text-muted-foreground mt-0.5">
                        <span>{formatDate(r.scheduled_date)}</span>
                        <Badge variant="outline" className="text-[10px] sm:text-xs py-0 h-4 sm:h-5">
                          {r.frequency_display}
                        </Badge>
                        <Badge variant="outline" className="text-[10px] sm:text-xs py-0 h-4 sm:h-5">
                          {r.priority_display}
                        </Badge>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
            <Link href="/dashboard/reminders">
              <Button variant="outline" className="w-full mt-4">
                Ver todos os Lembretes
              </Button>
            </Link>
          </CardContent>
        </Card>
      )}

      {/* Atividade do Portal do Cliente */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Atividade do Portal do Cliente
          </CardTitle>
          <CardDescription>Ações recentes dos clientes no portal</CardDescription>
        </CardHeader>
        <CardContent>
          {!portalActivity || portalActivity.activities.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Users className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Nenhuma atividade recente do portal</p>
            </div>
          ) : (
            <div className="space-y-3">
              {portalActivity.activities.slice(0, 5).map((activity, idx) => {
                const IconComponent = activity.icon === 'PenTool' ? PenTool : MessageSquare;
                const iconColor = activity.type === 'message'
                  ? (activity.is_read ? 'text-blue-400' : 'text-blue-600')
                  : 'text-green-600';
                const bgColor = activity.type === 'message'
                  ? (activity.is_read ? 'bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-900' : 'bg-blue-100 dark:bg-blue-950 border-blue-300 dark:border-blue-800')
                  : 'bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-900';
                const timeAgo = formatRelativeTime(activity.date);

                return (
                  <div
                    key={`${activity.type}-${idx}`}
                    className={`flex items-start gap-2.5 sm:gap-3 p-2.5 sm:p-3 rounded-lg border ${bgColor}`}
                  >
                    <IconComponent className={`h-4 w-4 sm:h-5 sm:w-5 mt-0.5 shrink-0 ${iconColor}`} />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm truncate">{activity.title}</p>
                      <p className="text-xs text-muted-foreground truncate mt-0.5">
                        {activity.description}
                      </p>
                      <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 text-[10px] sm:text-xs text-muted-foreground mt-1">
                        <span>{timeAgo}</span>
                        {activity.case && (
                          <Badge variant="outline" className="text-[10px] sm:text-xs py-0 h-4 sm:h-5">
                            {activity.case}
                          </Badge>
                        )}
                        {!activity.is_read && (
                          <Badge className="bg-blue-600 text-white text-[10px] py-0 h-4">Nova</Badge>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
          <Link href="/dashboard/mensagens-clientes">
            <Button variant="outline" className="w-full mt-4">
              Ver Todas as Atividades
            </Button>
          </Link>
        </CardContent>
      </Card>

      {/* Notificacoes */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            Notificações
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          ) : (
            <div className="space-y-3">
              {(stats?.notifications.pending_review ?? 0) > 0 && (
                <div className="flex items-start gap-2.5 sm:gap-3 p-2.5 sm:p-3 rounded-lg bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-900">
                  <FileText className="h-4 w-4 sm:h-5 sm:w-5 text-blue-600 mt-0.5 shrink-0" />
                  <div>
                    <p className="font-medium text-sm">
                      {stats?.notifications.pending_review} peça{(stats?.notifications.pending_review ?? 0) !== 1 ? 's' : ''} aguardando revisão
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Peças com status &quot;Em Revisão&quot;
                    </p>
                  </div>
                </div>
              )}

              {(stats?.knowledge_base.total ?? 0) > 0 && (
                <div className="flex items-start gap-2.5 sm:gap-3 p-2.5 sm:p-3 rounded-lg bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-900">
                  <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-green-600 mt-0.5 shrink-0" />
                  <div>
                    <p className="font-medium text-sm">
                      {stats?.knowledge_base.total} documentos na Base Jurídica
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Documentos processados e disponíveis para consulta jurídica
                    </p>
                  </div>
                </div>
              )}

              {(stats?.documents.by_status.draft ?? 0) > 0 && (
                <div className="flex items-start gap-2.5 sm:gap-3 p-2.5 sm:p-3 rounded-lg bg-yellow-50 dark:bg-yellow-950 border border-yellow-200 dark:border-yellow-900">
                  <Clock className="h-4 w-4 sm:h-5 sm:w-5 text-yellow-600 mt-0.5 shrink-0" />
                  <div>
                    <p className="font-medium text-sm">
                      {stats?.documents.by_status.draft} peça{(stats?.documents.by_status.draft ?? 0) !== 1 ? 's' : ''} em rascunho
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Peças que ainda não foram finalizadas
                    </p>
                  </div>
                </div>
              )}

              {(stats?.notifications.pending_review ?? 0) === 0 &&
                (stats?.documents.by_status.draft ?? 0) === 0 && (
                  <div className="flex items-start gap-2.5 sm:gap-3 p-2.5 sm:p-3 rounded-lg bg-gray-50 dark:bg-gray-950 border border-gray-200 dark:border-gray-800">
                    <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-gray-500 mt-0.5 shrink-0" />
                    <div>
                      <p className="font-medium text-sm">Tudo em dia!</p>
                      <p className="text-sm text-muted-foreground">
                        Nenhuma notificação pendente no momento
                      </p>
                    </div>
                  </div>
                )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
