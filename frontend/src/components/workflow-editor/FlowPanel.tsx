'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Activity, Play, CheckCircle2, XCircle, Clock,
  ExternalLink, Loader2, AlertCircle, ChevronRight, Workflow,
} from 'lucide-react';
import { useFlowTemplates } from '@/hooks/useFlowTemplates';
import { useFlowInstance, useStartFlowForCase } from '@/hooks/useFlowExecution';

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: React.ElementType }> = {
  pending:   { label: 'Aguardando',   color: '#F59E0B', icon: Clock },
  running:   { label: 'Em andamento', color: '#3B82F6', icon: Activity },
  completed: { label: 'Concluído',    color: '#22C55E', icon: CheckCircle2 },
  cancelled: { label: 'Cancelado',    color: '#6B7280', icon: XCircle },
};

type FlowPanelProps = {
  caseId: string;
  activeFlowId: string | null;
  activeFlowStatus: string | null;
  activeFlowNode: string | null;
  activeFlowPendingTasks: number;
  activeFlowTemplateName: string | null;
};

function SelectTemplateModal({
  caseId,
  onClose,
}: {
  caseId: string;
  onClose: () => void;
}) {
  const router = useRouter();
  const { data: templates } = useFlowTemplates();
  const startFlow = useStartFlowForCase();
  const [selectedId, setSelectedId] = useState('');

  const published = templates?.filter((t) => t.status === 'published') ?? [];

  const handleStart = async () => {
    if (!selectedId) return;
    try {
      const instance = await startFlow.mutateAsync({ caseId, template_id: selectedId });
      onClose();
      router.push(`/dashboard/execucoes/${instance.id}`);
    } catch {
      /* handled */
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: 'rgba(0,0,0,0.75)' }}
      onClick={onClose}
    >
      <div
        className="rounded-xl border p-6 w-full max-w-md"
        style={{ background: '#0F0F0F', borderColor: '#2A2A2A' }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-base font-semibold mb-1">Iniciar fluxo de trabalho</h2>
        <p className="text-xs text-white/40 mb-4">
          Selecione o template de fluxo para este processo
        </p>

        {published.length === 0 && (
          <p className="text-sm text-white/30 text-center py-4">
            Nenhum template publicado disponível.
          </p>
        )}

        <div className="flex flex-col gap-2 mb-4 max-h-64 overflow-y-auto">
          {published.map((t) => (
            <button
              key={t.id}
              onClick={() => setSelectedId(t.id)}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg border text-left transition-all"
              style={{
                borderColor: selectedId === t.id ? '#7030A0' : '#1A1A1A',
                background: selectedId === t.id ? '#7030A015' : '#0A0A0A',
              }}
            >
              <Workflow size={14} className="text-[#8B5CF6] shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-white/80 truncate">{t.name}</p>
                <p className="text-[10px] text-white/30 mt-0.5">
                  v{t.version} · {t.node_count} nós · {t.swimlane_count} swim lanes
                </p>
              </div>
              {selectedId === t.id && (
                <CheckCircle2 size={14} className="text-[#7030A0] shrink-0" />
              )}
            </button>
          ))}
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleStart}
            disabled={!selectedId || startFlow.isPending}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all disabled:opacity-50"
            style={{ background: '#7030A0', color: '#fff' }}
          >
            {startFlow.isPending ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            Iniciar fluxo
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm text-white/50 hover:text-white hover:bg-white/8 transition-all"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
}

export default function FlowPanel({
  caseId,
  activeFlowId,
  activeFlowStatus,
  activeFlowNode,
  activeFlowPendingTasks,
  activeFlowTemplateName,
}: FlowPanelProps) {
  const router = useRouter();
  const [showModal, setShowModal] = useState(false);

  const hasFlow = Boolean(activeFlowId && activeFlowStatus && activeFlowStatus !== 'cancelled');
  const conf = activeFlowStatus ? STATUS_CONFIG[activeFlowStatus] : null;
  const StatusIcon = conf?.icon ?? Activity;

  return (
    <>
      <div
        className="rounded-xl border p-4 flex flex-col gap-3"
        style={{ borderColor: '#1A1A1A', background: '#0D0D0D' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Workflow size={15} className="text-[#8B5CF6]" />
            <span className="text-xs font-mono uppercase tracking-widest text-white/30">
              Fluxo de Trabalho
            </span>
          </div>
          {hasFlow && conf && (
            <div className="flex items-center gap-1.5">
              <StatusIcon size={12} style={{ color: conf.color }} />
              <span className="text-[11px] font-medium" style={{ color: conf.color }}>
                {conf.label}
              </span>
            </div>
          )}
        </div>

        {/* Content */}
        {!hasFlow ? (
          <div className="flex flex-col items-center gap-3 py-4">
            <p className="text-xs text-white/30 text-center">
              Nenhum fluxo ativo para este processo.
            </p>
            <button
              onClick={() => setShowModal(true)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all"
              style={{ background: '#7030A015', color: '#C084FC', border: '1px solid #7030A040' }}
            >
              <Play size={13} />
              Iniciar fluxo
            </button>
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {/* Template name */}
            {activeFlowTemplateName && (
              <p className="text-sm text-white/70 font-medium">{activeFlowTemplateName}</p>
            )}

            {/* Current node */}
            {activeFlowNode && activeFlowStatus === 'running' && (
              <div className="flex items-center gap-2 text-[11px] text-white/40">
                <ChevronRight size={11} />
                <span>Nó atual: <span className="text-white/60">{activeFlowNode}</span></span>
              </div>
            )}

            {/* Pending tasks */}
            {activeFlowPendingTasks > 0 && (
              <div
                className="flex items-center gap-1.5 text-[11px] px-2 py-1 rounded-md self-start"
                style={{ background: '#3B82F620', color: '#3B82F6' }}
              >
                <AlertCircle size={11} />
                {activeFlowPendingTasks} tarefa{activeFlowPendingTasks !== 1 ? 's' : ''} pendente{activeFlowPendingTasks !== 1 ? 's' : ''}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-2 pt-1">
              <button
                onClick={() => router.push(`/dashboard/execucoes/${activeFlowId}`)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all hover:bg-white/8 text-white/50 hover:text-white"
              >
                <ExternalLink size={12} />
                Ver detalhes
              </button>
              {activeFlowStatus === 'running' && (
                <button
                  onClick={() => router.push('/dashboard/minhas-tarefas')}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
                  style={{ background: '#3B82F620', color: '#3B82F6', border: '1px solid #3B82F640' }}
                >
                  <Activity size={12} />
                  Minhas tarefas
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {showModal && (
        <SelectTemplateModal
          caseId={caseId}
          onClose={() => setShowModal(false)}
        />
      )}
    </>
  );
}
