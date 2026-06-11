'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Activity, CheckCircle2, Clock, XCircle, AlertCircle,
  Loader2, ExternalLink, Play,
} from 'lucide-react';
import { useFlowInstances, useCancelFlow, type FlowInstanceListItem } from '@/hooks/useFlowExecution';

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: React.ElementType }> = {
  pending:   { label: 'Aguardando',   color: '#F59E0B', icon: Clock },
  running:   { label: 'Em andamento', color: '#3B82F6', icon: Activity },
  completed: { label: 'Concluído',    color: '#22C55E', icon: CheckCircle2 },
  cancelled: { label: 'Cancelado',    color: '#6B7280', icon: XCircle },
};

function InstanceRow({
  instance,
  onCancel,
  onView,
}: {
  instance: FlowInstanceListItem;
  onCancel: () => void;
  onView: () => void;
}) {
  const [confirmCancel, setConfirmCancel] = useState(false);
  const conf = STATUS_CONFIG[instance.status];
  const StatusIcon = conf.icon;
  const canCancel = instance.status === 'running' || instance.status === 'pending';

  return (
    <div
      className="flex items-center gap-3 px-4 py-3 border-b hover:bg-white/3 transition-all cursor-pointer"
      style={{ borderColor: '#141414' }}
      onClick={onView}
    >
      {/* Status */}
      <div className="flex items-center gap-1.5 w-32 shrink-0">
        <StatusIcon size={13} style={{ color: conf.color }} />
        <span className="text-xs font-medium" style={{ color: conf.color }}>
          {conf.label}
        </span>
      </div>

      {/* Template + case */}
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white/80 truncate">{instance.template_name_snapshot}</p>
        <p className="text-[11px] text-white/35 truncate">
          {instance.case_title || instance.case_ref || 'Sem referência'}
        </p>
      </div>

      {/* Pending tasks */}
      {instance.pending_task_count > 0 && (
        <div
          className="px-2 py-0.5 rounded-full text-[10px] font-medium shrink-0"
          style={{ background: '#3B82F620', color: '#3B82F6', border: '1px solid #3B82F640' }}
        >
          {instance.pending_task_count} pendente{instance.pending_task_count !== 1 ? 's' : ''}
        </div>
      )}

      {/* Date */}
      <span className="text-[11px] text-white/25 shrink-0">
        {new Date(instance.created_at).toLocaleDateString('pt-BR')}
      </span>

      {/* Actions */}
      <div className="flex items-center gap-1 shrink-0" onClick={(e) => e.stopPropagation()}>
        <button
          onClick={onView}
          className="w-7 h-7 rounded flex items-center justify-center text-white/30 hover:text-white hover:bg-white/8 transition-all"
          title="Ver detalhes"
        >
          <ExternalLink size={13} />
        </button>
        {canCancel && !confirmCancel && (
          <button
            onClick={() => setConfirmCancel(true)}
            className="w-7 h-7 rounded flex items-center justify-center text-white/30 hover:text-red-400 hover:bg-red-400/10 transition-all"
            title="Cancelar fluxo"
          >
            <XCircle size={13} />
          </button>
        )}
        {canCancel && confirmCancel && (
          <div className="flex items-center gap-1">
            <button
              onClick={() => { onCancel(); setConfirmCancel(false); }}
              className="px-2 py-0.5 rounded text-[10px] font-medium transition-all"
              style={{ background: '#EF444420', color: '#EF4444', border: '1px solid #EF444430' }}
            >
              Confirmar
            </button>
            <button
              onClick={() => setConfirmCancel(false)}
              className="px-2 py-0.5 rounded text-[10px] font-medium text-white/40 hover:text-white transition-all"
            >
              Não
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default function ExecucoesPage() {
  const router = useRouter();
  const [statusFilter, setStatusFilter] = useState<string>('running');
  const { data: instances, isLoading, error } = useFlowInstances({ status: statusFilter === 'all' ? undefined : statusFilter });
  const cancelFlow = useCancelFlow();

  const filters = [
    { value: 'running',   label: 'Em andamento' },
    { value: 'pending',   label: 'Aguardando' },
    { value: 'completed', label: 'Concluídos' },
    { value: 'cancelled', label: 'Cancelados' },
    { value: 'all',       label: 'Todos' },
  ];

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Play size={22} className="text-[#8B5CF6]" />
            Execuções de Fluxos
          </h1>
          <p className="text-sm text-white/45 mt-1">
            Instâncias de fluxos de trabalho em andamento e histórico
          </p>
        </div>
        <button
          onClick={() => router.push('/dashboard/fluxos')}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all"
          style={{ background: '#7030A015', color: '#C084FC', border: '1px solid #7030A040' }}
        >
          <Activity size={14} />
          Iniciar novo fluxo
        </button>
      </div>

      {/* Filter tabs */}
      <div className="flex items-center gap-1 mb-4">
        {filters.map((f) => (
          <button
            key={f.value}
            onClick={() => setStatusFilter(f.value)}
            className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
            style={{
              background: statusFilter === f.value ? '#7030A020' : 'transparent',
              color: statusFilter === f.value ? '#C084FC' : '#6B7280',
              border: statusFilter === f.value ? '1px solid #7030A040' : '1px solid transparent',
            }}
          >
            {f.label}
          </button>
        ))}
        {instances && (
          <span className="ml-2 text-xs text-white/25">{instances.length} instância(s)</span>
        )}
      </div>

      {/* Table */}
      <div
        className="rounded-xl border overflow-hidden"
        style={{ borderColor: '#1A1A1A', background: '#0D0D0D' }}
      >
        {/* Header row */}
        <div
          className="flex items-center gap-3 px-4 py-2 border-b"
          style={{ borderColor: '#1A1A1A', background: '#0A0A0A' }}
        >
          <span className="text-[10px] text-white/20 font-mono uppercase tracking-widest w-32 shrink-0">Status</span>
          <span className="text-[10px] text-white/20 font-mono uppercase tracking-widest flex-1">Fluxo / Processo</span>
          <span className="text-[10px] text-white/20 font-mono uppercase tracking-widest shrink-0">Data</span>
          <span className="w-16 shrink-0" />
        </div>

        {isLoading && (
          <div className="flex items-center justify-center py-16">
            <Loader2 size={24} className="animate-spin text-white/20" />
          </div>
        )}

        {error && (
          <div className="flex items-center gap-3 p-4 text-red-400 text-sm">
            <AlertCircle size={16} />
            Erro ao carregar execuções.
          </div>
        )}

        {instances?.length === 0 && !isLoading && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <Activity size={32} className="text-white/10 mb-3" />
            <p className="text-white/40 text-sm">Nenhuma execução encontrada.</p>
          </div>
        )}

        {instances?.map((instance) => (
          <InstanceRow
            key={instance.id}
            instance={instance}
            onView={() => router.push(`/dashboard/execucoes/${instance.id}`)}
            onCancel={() => cancelFlow.mutate(instance.id)}
          />
        ))}
      </div>
    </div>
  );
}
