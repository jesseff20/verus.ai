'use client';

import { useState } from 'react';
import {
  CheckCircle2, XCircle, Clock, AlertCircle,
  Loader2, ClipboardList, User, MessageSquare, ShieldOff,
} from 'lucide-react';
import { AITextarea } from '@/components/ui/ai-textarea';
import {
  useTaskRequests,
  useApproveRequest,
  useRejectRequest,
  type TaskRequestDto,
  type RequestType,
} from '@/hooks/useFlowExecution';
import { useAuth } from '@/hooks/use-auth';

const REQUEST_TYPE_LABELS: Record<RequestType, string> = {
  redistribuicao: 'Redistribuição',
  avocacao:       'Avocação',
  assessoria:     'Pedido de Assessoria',
};

const STATUS_CONFIG = {
  pending:  { label: 'Pendente',   color: '#F59E0B', icon: Clock },
  approved: { label: 'Aprovado',   color: '#22C55E', icon: CheckCircle2 },
  rejected: { label: 'Rejeitado',  color: '#EF4444', icon: XCircle },
};

function ResolveModal({
  action,
  request,
  onClose,
  onConfirm,
  isPending,
}: {
  action: 'approve' | 'reject';
  request: TaskRequestDto;
  onClose: () => void;
  onConfirm: (note: string) => void;
  isPending: boolean;
}) {
  const [note, setNote] = useState('');
  const isApprove = action === 'approve';

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
        <h2 className="text-base font-semibold mb-1">
          {isApprove ? 'Aprovar solicitação' : 'Rejeitar solicitação'}
        </h2>
        <p className="text-xs text-white/40 mb-4">
          {REQUEST_TYPE_LABELS[request.request_type]} — {request.requester_name}
        </p>

        <label className="block text-xs text-white/50 mb-1">
          Observação {isApprove ? '(opcional)' : '(obrigatória)'}
        </label>
        <AITextarea
          variant="dark"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          setValue={setNote}
          placeholder="Descreva o motivo da decisão..."
          rows={3}
          aiContext="nota de resolução de solicitação de tarefa"
          aiObjective="Ajude a redigir uma observação formal e clara para a decisão de aprovação ou rejeição"
          className="w-full px-3 py-2 rounded-lg text-sm text-white bg-white/5 border border-white/10 focus:border-[#7030A0] focus:outline-none resize-none mb-4 placeholder:text-white/20"
        />

        <div className="flex gap-2">
          <button
            onClick={() => onConfirm(note)}
            disabled={isPending || (!isApprove && note.trim().length < 3)}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all disabled:opacity-50"
            style={{
              background: isApprove ? '#22C55E' : '#EF4444',
              color: '#fff',
            }}
          >
            {isPending
              ? <Loader2 size={14} className="animate-spin" />
              : isApprove ? <CheckCircle2 size={14} /> : <XCircle size={14} />
            }
            {isApprove ? 'Confirmar aprovação' : 'Confirmar rejeição'}
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

function RequestCard({ req }: { req: TaskRequestDto }) {
  const [modal, setModal] = useState<'approve' | 'reject' | null>(null);
  const approve = useApproveRequest();
  const reject = useRejectRequest();

  const statusConf = STATUS_CONFIG[req.status];
  const StatusIcon = statusConf.icon;
  const isPending = req.status === 'pending';

  return (
    <>
      <div
        className="rounded-xl border p-4 flex flex-col gap-3"
        style={{ borderColor: '#1A1A1A', background: '#0D0D0D' }}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex flex-col gap-0.5">
            <span className="text-sm font-semibold text-white/80">
              {REQUEST_TYPE_LABELS[req.request_type]}
            </span>
            <div className="flex items-center gap-1.5 text-[11px] text-white/35">
              <User size={10} />
              <span>Solicitante: {req.requester_name ?? 'Desconhecido'}</span>
            </div>
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            <StatusIcon size={12} style={{ color: statusConf.color }} />
            <span className="text-[11px] font-medium" style={{ color: statusConf.color }}>
              {statusConf.label}
            </span>
          </div>
        </div>

        {/* Target user */}
        {req.target_user_name && (
          <div className="flex items-center gap-1.5 text-[11px] text-white/40">
            <User size={10} />
            <span>Destino: <span className="text-white/60">{req.target_user_name}</span></span>
          </div>
        )}

        {/* Justification */}
        {req.justification && (
          <div className="flex items-start gap-1.5 text-xs text-white/40">
            <MessageSquare size={11} className="mt-0.5 shrink-0" />
            <p className="leading-relaxed line-clamp-2">{req.justification}</p>
          </div>
        )}

        {/* Resolution note */}
        {req.resolution_note && (
          <div
            className="flex items-start gap-1.5 text-xs px-2 py-1.5 rounded-md"
            style={{ background: '#ffffff08' }}
          >
            <MessageSquare size={11} className="mt-0.5 shrink-0 text-white/30" />
            <p className="text-white/40 leading-relaxed">{req.resolution_note}</p>
          </div>
        )}

        {/* Date */}
        <p className="text-[10px] text-white/20">
          {new Date(req.created_at).toLocaleString('pt-BR')}
          {req.resolved_at && ` · Resolvido em ${new Date(req.resolved_at).toLocaleString('pt-BR')}`}
        </p>

        {/* Actions */}
        {isPending && (
          <div className="flex items-center gap-2 pt-2 border-t border-white/5">
            <button
              onClick={() => setModal('approve')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
              style={{ background: '#22C55E20', color: '#22C55E', border: '1px solid #22C55E30' }}
            >
              <CheckCircle2 size={12} />
              Aprovar
            </button>
            <button
              onClick={() => setModal('reject')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
              style={{ background: '#EF444415', color: '#EF4444', border: '1px solid #EF444430' }}
            >
              <XCircle size={12} />
              Rejeitar
            </button>
          </div>
        )}
      </div>

      {modal && (
        <ResolveModal
          action={modal}
          request={req}
          onClose={() => setModal(null)}
          isPending={modal === 'approve' ? approve.isPending : reject.isPending}
          onConfirm={(note) => {
            if (modal === 'approve') {
              approve.mutate(
                { requestId: req.id, resolution_note: note },
                { onSuccess: () => setModal(null) },
              );
            } else {
              reject.mutate(
                { requestId: req.id, resolution_note: note },
                { onSuccess: () => setModal(null) },
              );
            }
          }}
        />
      )}
    </>
  );
}

export default function SolicitacoesPage() {
  const { hasPermission } = useAuth();
  const canApprove = hasPermission('gerente');

  const [statusFilter, setStatusFilter] = useState('pending');
  const { data: requests, isLoading, error } = useTaskRequests(statusFilter);

  if (!canApprove) {
    return (
      <div className="p-6 max-w-4xl mx-auto flex flex-col items-center justify-center min-h-[300px] gap-4 text-center">
        <ShieldOff className="h-12 w-12 text-muted-foreground/40" />
        <h2 className="text-lg font-semibold">Acesso restrito</h2>
        <p className="text-sm text-muted-foreground">
          Apenas gerentes e procuradores de nível superior podem visualizar e resolver solicitações de tarefas.
        </p>
      </div>
    );
  }

  const filters = [
    { value: 'pending',  label: 'Pendentes' },
    { value: 'approved', label: 'Aprovadas' },
    { value: 'rejected', label: 'Rejeitadas' },
    { value: 'all',      label: 'Todas' },
  ];

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <ClipboardList size={22} className="text-[#8B5CF6]" />
          Solicitações de Tarefas
        </h1>
        <p className="text-sm text-white/45 mt-1">
          Pedidos de redistribuição, avocação e assessoria do seu órgão
        </p>
      </div>

      {/* Filter tabs */}
      <div className="flex items-center gap-1 mb-6">
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
        {requests && (
          <span className="ml-2 text-xs text-white/25">{requests.length} solicitação(ões)</span>
        )}
      </div>

      {/* Content */}
      {isLoading && (
        <div className="flex items-center justify-center py-24">
          <Loader2 size={24} className="animate-spin text-white/20" />
        </div>
      )}

      {error && (
        <div className="flex items-center gap-3 p-4 rounded-xl border border-red-500/20 bg-red-500/5 text-red-400 text-sm">
          <AlertCircle size={16} />
          Erro ao carregar solicitações.
        </div>
      )}

      {requests?.length === 0 && !isLoading && (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <ClipboardList size={40} className="text-white/10 mb-4" />
          <p className="text-white/40 text-sm">Nenhuma solicitação encontrada.</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {requests?.map((req) => (
          <RequestCard key={req.id} req={req} />
        ))}
      </div>
    </div>
  );
}
