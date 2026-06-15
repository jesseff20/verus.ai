'use client';

import { use, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  ArrowLeft, Loader2, AlertCircle, CheckCircle2,
  Clock, Activity, XCircle, User, FileText,
} from 'lucide-react';
import { useFlowInstance, useCancelFlow, useCompleteTask, type TaskInstanceDto } from '@/hooks/useFlowExecution';

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  pending:   { label: 'Aguardando',   color: '#F59E0B' },
  running:   { label: 'Em andamento', color: '#3B82F6' },
  completed: { label: 'Concluído',    color: '#22C55E' },
  cancelled: { label: 'Cancelado',    color: '#6B7280' },
};

const TASK_STATUS_CONFIG: Record<string, { label: string; color: string; icon: React.ElementType }> = {
  pending:     { label: 'Pendente',     color: '#F59E0B', icon: Clock },
  in_progress: { label: 'Em andamento', color: '#3B82F6', icon: Activity },
  completed:   { label: 'Concluído',    color: '#22C55E', icon: CheckCircle2 },
  skipped:     { label: 'Pulado',       color: '#6B7280', icon: XCircle },
};

const EVENT_LABELS: Record<string, string> = {
  flow_started:       'Fluxo iniciado',
  flow_completed:     'Fluxo concluído',
  flow_cancelled:     'Fluxo cancelado',
  task_created:       'Tarefa criada',
  task_started:       'Tarefa iniciada',
  task_completed:     'Tarefa concluída',
  task_skipped:       'Tarefa pulada',
  task_reassigned:    'Tarefa reatribuída',
  gateway_evaluated:  'Gateway avaliado',
  request_created:    'Solicitação criada',
  request_approved:   'Solicitação aprovada',
  request_rejected:   'Solicitação rejeitada',
};

function TaskRow({ task, instanceId }: { task: TaskInstanceDto; instanceId: string }) {
  const conf = TASK_STATUS_CONFIG[task.status];
  const StatusIcon = conf.icon;
  const complete = useCompleteTask(instanceId);

  return (
    <div className="flex items-start gap-3 p-3 rounded-lg border border-border bg-card">
      <StatusIcon size={14} style={{ color: conf.color, marginTop: 2, flexShrink: 0 }} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span className="text-sm text-foreground/80 truncate">{task.label}</span>
          <span className="text-[10px] font-medium shrink-0" style={{ color: conf.color }}>
            {conf.label}
          </span>
        </div>
        {task.assigned_to_name && (
          <p className="text-[11px] text-foreground/40 mt-0.5 flex items-center gap-1">
            <User size={10} />
            {task.assigned_to_name}
          </p>
        )}
        {task.notes && (
          <p className="text-[11px] text-foreground/45 mt-1 flex items-start gap-1">
            <FileText size={10} className="mt-0.5 shrink-0" />
            {task.notes}
          </p>
        )}
        {task.completed_at && (
          <p className="text-[10px] text-foreground/25 mt-1">
            Concluído em {new Date(task.completed_at).toLocaleString('pt-BR')}
          </p>
        )}
      </div>
      {task.status === 'pending' && (
        <button
          onClick={() => complete.mutate({ taskId: task.id })}
          disabled={complete.isPending}
          className="px-2.5 py-1 rounded-lg text-[11px] font-medium shrink-0 transition-all disabled:opacity-50"
          style={{ background: '#22C55E20', color: '#22C55E', border: '1px solid #22C55E30' }}
        >
          {complete.isPending ? <Loader2 size={11} className="animate-spin" /> : 'Concluir'}
        </button>
      )}
    </div>
  );
}

export default function ExecucaoDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [confirmCancel, setConfirmCancel] = useState(false);
  const { data: instance, isLoading, error } = useFlowInstance(id);
  const cancelFlow = useCancelFlow();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 size={24} className="animate-spin text-foreground/20" />
      </div>
    );
  }

  if (error || !instance) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <AlertCircle size={32} className="text-red-400/50" />
        <p className="text-sm text-foreground/40">Execução não encontrada.</p>
        <button
          onClick={() => router.push('/dashboard/execucoes')}
          className="text-sm text-[#8B5CF6] hover:underline"
        >
          Voltar para execuções
        </button>
      </div>
    );
  }

  const statusConf = STATUS_CONFIG[instance.status];
  const canCancel = instance.status === 'running' || instance.status === 'pending';

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Breadcrumb */}
      <button
        onClick={() => router.push('/dashboard/execucoes')}
        className="flex items-center gap-1.5 text-xs text-foreground/40 hover:text-foreground transition-colors mb-6"
      >
        <ArrowLeft size={12} />
        Execuções
      </button>

      {/* Header */}
      <div className="flex items-start justify-between mb-6 gap-4" data-tour="ed-header">
        <div>
          <h1 className="text-xl font-bold tracking-tight">{instance.template_name_snapshot}</h1>
          <p className="text-sm text-foreground/50 mt-1">
            {instance.case_title || instance.case_ref || 'Sem referência de processo'}
          </p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <div
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium"
            style={{
              color: statusConf.color,
              borderColor: `${statusConf.color}40`,
              background: `${statusConf.color}10`,
            }}
          >
            {statusConf.label}
          </div>
          {canCancel && !confirmCancel && (
            <button
              onClick={() => setConfirmCancel(true)}
              className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
              style={{ background: '#EF444415', color: '#EF4444', border: '1px solid #EF444430' }}
            >
              Cancelar fluxo
            </button>
          )}
          {canCancel && confirmCancel && (
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-foreground/40">Confirmar cancelamento?</span>
              <button
                onClick={() => {
                  cancelFlow.mutate(id, { onSuccess: () => router.push('/dashboard/execucoes') });
                  setConfirmCancel(false);
                }}
                disabled={cancelFlow.isPending}
                className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all disabled:opacity-50"
                style={{ background: '#EF4444', color: '#fff' }}
              >
                {cancelFlow.isPending ? <Loader2 size={12} className="animate-spin" /> : 'Confirmar'}
              </button>
              <button
                onClick={() => setConfirmCancel(false)}
                className="px-3 py-1.5 rounded-lg text-xs font-medium text-foreground/40 hover:text-foreground hover:bg-foreground/8 transition-all"
              >
                Não
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Tasks — 3 cols */}
        <div className="lg:col-span-3 flex flex-col gap-3" data-tour="ed-tasks">
          <h2 className="text-xs font-mono uppercase tracking-widest text-foreground/30 mb-1">
            Tarefas ({instance.tasks.length})
          </h2>
          {instance.tasks.length === 0 && (
            <p className="text-sm text-foreground/30">Nenhuma tarefa gerada ainda.</p>
          )}
          {instance.tasks.map((task) => (
            <TaskRow key={task.id} task={task} instanceId={id} />
          ))}
        </div>

        {/* Timeline — 2 cols */}
        <div className="lg:col-span-2" data-tour="ed-timeline">
          <h2 className="text-xs font-mono uppercase tracking-widest text-foreground/30 mb-3">
            Histórico
          </h2>
          <div className="flex flex-col">
            {instance.events.map((event, i) => (
              <div key={event.id} className="flex gap-3">
                {/* Timeline line */}
                <div className="flex flex-col items-center">
                  <div
                    className="w-2 h-2 rounded-full shrink-0 mt-1"
                    style={{ background: '#7030A0' }}
                  />
                  {i < instance.events.length - 1 && (
                    <div className="w-px flex-1 my-1 bg-border" />
                  )}
                </div>
                {/* Event content */}
                <div className="pb-4 flex-1 min-w-0">
                  <p className="text-xs text-foreground/60">
                    {EVENT_LABELS[event.event_type] ?? event.event_type}
                    {event.node_label && (
                      <span className="text-foreground/30"> — {event.node_label}</span>
                    )}
                  </p>
                  <p className="text-[10px] text-foreground/30 mt-0.5">
                    {event.actor_name && `${event.actor_name} · `}
                    {new Date(event.created_at).toLocaleString('pt-BR')}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
