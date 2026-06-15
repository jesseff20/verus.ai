'use client';

import { useState } from 'react';
import {
  CheckCircle2, Clock, AlertCircle, Loader2,
  User, Briefcase, ChevronRight, Send, Shield,
  AlertTriangle, Timer,
} from 'lucide-react';
import {
  useMyTasks,
  useCompleteTask,
  useCreateTaskRequest,
  type TaskInstanceDto,
  type RequestType,
} from '@/hooks/useFlowExecution';
import { useUsers } from '@/hooks/use-users';
import { SignatureModal } from '@/components/signature/SignatureModal';
import { AIInput } from '@/components/ui/ai-input';
import { AITextarea } from '@/components/ui/ai-textarea';

const STATUS_CONFIG = {
  pending:     { label: 'Pendente',      color: '#F59E0B' },
  in_progress: { label: 'Em andamento',  color: '#3B82F6' },
  completed:   { label: 'Concluído',     color: '#22C55E' },
  skipped:     { label: 'Pulado',        color: '#6B7280' },
};

const NODE_TYPE_LABELS: Record<string, string> = {
  task:              'Tarefa',
  user_task:         'Tarefa de Usuário',
  service_task:      'Tarefa de Serviço',
  exclusive_gateway: 'Decisão (Gateway)',
  inclusive_gateway: 'Gateway Inclusivo',
};

const ROLE_LABELS: Record<string, string> = {
  distribuidor:       'Distribuidor(a)',
  procurador:         'Procurador(a)',
  gerente:            'Gerente',
  assessor_gerencial: 'Assessor(a) Gerencial',
  assessor_gabinete:  'Assessor(a) de Gabinete',
  procurador_geral:   'Procurador(a)-Geral',
  subprocurador_geral:'Subprocurador(a)-Geral',
  any:                'Qualquer papel',
};

/* ── Due date helper ─────────────────────────────────────────── */
type DueDateUrgency = 'ok' | 'warning' | 'critical' | 'overdue';

function getDueDateInfo(
  dueDateStr: string | null,
): { text: string; urgency: DueDateUrgency } | null {
  if (!dueDateStr) return null;
  const due = new Date(dueDateStr);
  const now = new Date();
  const diffDays = Math.ceil((due.getTime() - now.getTime()) / 86_400_000);

  if (diffDays < 0)
    return { text: `${Math.abs(diffDays)}d atrasado`, urgency: 'overdue' };
  if (diffDays === 0) return { text: 'Vence hoje', urgency: 'critical' };
  if (diffDays <= 3)
    return {
      text: `${diffDays}d restante${diffDays !== 1 ? 's' : ''}`,
      urgency: 'critical',
    };
  if (diffDays <= 7)
    return { text: `${diffDays}d restantes`, urgency: 'warning' };
  return { text: `${diffDays}d restantes`, urgency: 'ok' };
}

const DUE_URGENCY_STYLE: Record<
  DueDateUrgency,
  { color: string; bg: string; border: string; icon: typeof Timer }
> = {
  ok:       { color: '#22C55E', bg: '#22C55E10', border: '#22C55E20', icon: Timer },
  warning:  { color: '#F59E0B', bg: '#F59E0B10', border: '#F59E0B25', icon: Clock },
  critical: { color: '#EF4444', bg: '#EF444412', border: '#EF444428', icon: AlertTriangle },
  overdue:  { color: '#EF4444', bg: '#EF444418', border: '#EF444440', icon: AlertCircle },
};

/* ── Complete Modal ──────────────────────────────────────────── */
function CompleteModal({
  task,
  onClose,
  onConfirm,
  isPending,
}: {
  task: TaskInstanceDto;
  onClose: () => void;
  onConfirm: (notes: string, gateway_choice: string) => void;
  isPending: boolean;
}) {
  const [notes, setNotes] = useState('');
  const [gatewayChoice, setGatewayChoice] = useState('');
  const [showSignature, setShowSignature] = useState(false);
  const [signed, setSigned] = useState(false);

  const isGateway = task.node_type.includes('gateway');
  const hasChoices = task.gateway_choices && task.gateway_choices.length > 0;

  const handleSign = () => setShowSignature(true);
  const handleSignedOk = (_id: string) => {
    setSigned(true);
    setShowSignature(false);
  };

  return (
    <>
      <div
        className="fixed inset-0 z-50 flex items-center justify-center"
        style={{ background: 'rgba(0,0,0,0.75)' }}
        onClick={onClose}
      >
        <div
          className="rounded-xl border border-border bg-card p-6 w-full max-w-md"
          onClick={(e) => e.stopPropagation()}
        >
          <h2 className="text-base font-semibold mb-1">Concluir tarefa</h2>
          <p className="text-xs text-foreground/40 mb-4">{task.label}</p>

          {/* Gateway choice */}
          {isGateway && (
            <div className="mb-4">
              <label className="block text-xs text-foreground/50 mb-1">
                Branch de saída <span className="text-red-400">*</span>
              </label>
              {hasChoices ? (
                <div className="space-y-1.5">
                  {task.gateway_choices.map((choice) => (
                    <button
                      key={choice.value}
                      onClick={() => setGatewayChoice(choice.value)}
                      className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all border ${
                        gatewayChoice === choice.value
                          ? 'border-[#7030A0] bg-[#7030A015] text-foreground'
                          : 'border-foreground/10 text-foreground/60 hover:border-foreground/20 hover:bg-foreground/5'
                      }`}
                    >
                      <span className="font-medium">{choice.label}</span>
                      {choice.condition && (
                        <span className="ml-2 text-[10px] text-foreground/30 font-mono">
                          {choice.condition}
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              ) : (
                <AIInput
                  type="text"
                  variant="dark"
                  value={gatewayChoice}
                  onChange={(e) => setGatewayChoice(e.target.value)}
                  setValue={setGatewayChoice}
                  placeholder="ex: yes / no / edge_id"
                  aiContext="branch de saída do gateway de decisão"
                  aiObjective="Sugira o identificador correto do branch de saída para este gateway"
                  className="w-full px-3 py-2 rounded-lg text-sm text-foreground bg-muted/50 border border-border focus:border-[#7030A0] focus:outline-none placeholder:text-muted-foreground/50"
                />
              )}
            </div>
          )}

          <label className="block text-xs text-foreground/50 mb-1">
            Observações (opcional)
          </label>
          <AITextarea
            variant="dark"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            setValue={setNotes}
            placeholder="Descreva o resultado ou próximos passos..."
            rows={3}
            aiContext="observações de conclusão de tarefa"
            aiObjective="Ajude a redigir uma observação clara sobre o resultado da tarefa"
            className="w-full px-3 py-2 rounded-lg text-sm text-foreground bg-muted/50 border border-border focus:border-[#7030A0] focus:outline-none resize-none mb-4 placeholder:text-muted-foreground/50"
          />

          {/* Optional signature */}
          <button
            type="button"
            onClick={handleSign}
            className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs transition-all mb-4 ${
              signed
                ? 'bg-green-500/10 text-green-400 border border-green-500/25'
                : 'bg-muted/50 text-muted-foreground hover:bg-accent hover:text-foreground border border-border'
            }`}
          >
            <Shield size={12} />
            {signed ? 'Documento assinado digitalmente ✓' : 'Assinar documento (opcional)'}
          </button>

          <div className="flex gap-2">
            <button
              onClick={() => onConfirm(notes, gatewayChoice)}
              disabled={isPending || (isGateway && !gatewayChoice)}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all disabled:opacity-50"
              style={{ background: '#22C55E', color: '#fff' }}
            >
              {isPending ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <CheckCircle2 size={14} />
              )}
              Confirmar conclusão
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-sm text-foreground/50 hover:text-foreground hover:bg-accent transition-all"
            >
              Cancelar
            </button>
          </div>
        </div>
      </div>

      {showSignature && (
        <SignatureModal
          documentRef={task.id}
          documentType="task_completion"
          documentTitle={`Conclusão: ${task.label}`}
          content={`Tarefa: ${task.label}\nNota: ${notes || '(sem observações)'}\nData: ${new Date().toISOString()}`}
          onClose={() => setShowSignature(false)}
          onSigned={handleSignedOk}
        />
      )}
    </>
  );
}

/* ── Request Modal ───────────────────────────────────────────── */
function RequestModal({
  task,
  onClose,
  onConfirm,
  isPending,
}: {
  task: TaskInstanceDto;
  onClose: () => void;
  onConfirm: (type: RequestType, justification: string, target?: string) => void;
  isPending: boolean;
}) {
  const [type, setType] = useState<RequestType>('redistribuicao');
  const [justification, setJustification] = useState('');
  const [target, setTarget] = useState('');
  const [search, setSearch] = useState('');
  const { users } = useUsers();

  const filteredUsers = users.filter(
    (u) =>
      u.is_active &&
      u.id !== task.assigned_to &&
      (search === '' ||
        u.full_name.toLowerCase().includes(search.toLowerCase()) ||
        u.email.toLowerCase().includes(search.toLowerCase())),
  );

  const ROLE_LABELS_LOCAL: Record<string, string> = {
    superadmin: 'Super Admin',
    admin: 'Administrador',
    procurador_geral: 'Procurador(a)-Geral',
    subprocurador_geral: 'Subprocurador(a)-Geral',
    gerente: 'Gerente',
    procurador: 'Procurador(a)',
    assessor_gerencial: 'Assessor(a) Gerencial',
    assessor_gabinete: 'Assessor(a) de Gabinete',
    distribuidor: 'Distribuidor(a)',
    servidor: 'Servidor(a)',
    visualizador: 'Visualizador',
  };

  const selectedUser = users.find((u) => u.id === target);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: 'rgba(0,0,0,0.75)' }}
      onClick={onClose}
    >
      <div
        className="rounded-xl border border-border bg-card p-6 w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-base font-semibold mb-1">Criar solicitação</h2>
        <p className="text-xs text-foreground/40 mb-4">{task.label}</p>

        <label className="block text-xs text-foreground/50 mb-1">Tipo</label>
        <select
          value={type}
          onChange={(e) => { setType(e.target.value as RequestType); setTarget(''); setSearch(''); }}
          className="w-full px-3 py-2 rounded-lg text-sm text-foreground bg-muted/50 border border-border focus:border-[#7030A0] focus:outline-none mb-4"
        >
          <option value="redistribuicao">Redistribuição</option>
          <option value="avocacao">Avocação</option>
          <option value="assessoria">Pedido de Assessoria</option>
        </select>

        {(type === 'redistribuicao' || type === 'avocacao') && (
          <>
            <label className="block text-xs text-foreground/50 mb-1">
              Usuário destino <span className="text-red-400">*</span>
            </label>

            {/* Search filter */}
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Buscar por nome ou email..."
              className="w-full px-3 py-2 rounded-lg text-sm text-foreground bg-muted/50 border border-border focus:border-[#7030A0] focus:outline-none mb-2 placeholder:text-foreground/25"
            />

            {/* User list */}
            <div className="max-h-48 overflow-y-auto mb-4 rounded-lg border border-border bg-muted/30">
              {filteredUsers.length === 0 ? (
                <p className="text-xs text-foreground/30 text-center py-6">
                  Nenhum usuário encontrado.
                </p>
              ) : (
                filteredUsers.map((u) => (
                  <button
                    key={u.id}
                    type="button"
                    onClick={() => setTarget(u.id)}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 text-left text-sm transition-all border-b border-border/50 last:border-b-0 hover:bg-muted/50 ${
                      target === u.id ? 'bg-[#7030A0]/10 border-l-2 border-l-[#7030A0]' : ''
                    }`}
                  >
                    <div className="w-7 h-7 rounded-full bg-[#7030A0]/20 flex items-center justify-center text-[11px] font-semibold text-[#C084FC] shrink-0">
                      {u.full_name
                        ? u.full_name.split(' ').map((n) => n[0]).slice(0, 2).join('').toUpperCase()
                        : '??'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-foreground truncate font-medium">
                        {u.full_name || u.username}
                      </p>
                      <p className="text-[10px] text-foreground/35 truncate">
                        {ROLE_LABELS_LOCAL[u.role] || u.role}
                        {u.email && ` · ${u.email}`}
                      </p>
                    </div>
                    {target === u.id && (
                      <svg className="w-4 h-4 text-[#7030A0] shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </button>
                ))
              )}
            </div>

            {selectedUser && (
              <div className="flex items-center gap-2 mb-3 px-3 py-2 rounded-lg bg-[#7030A0]/10 border border-[#7030A0]/20">
                <span className="text-xs text-foreground/60">
                  Destino: <strong className="text-foreground">{selectedUser.full_name}</strong>
                  <span className="text-foreground/40"> ({ROLE_LABELS_LOCAL[selectedUser.role] || selectedUser.role})</span>
                </span>
              </div>
            )}
          </>
        )}

        <label className="block text-xs text-foreground/50 mb-1">Justificativa</label>
        <AITextarea
          variant="dark"
          value={justification}
          onChange={(e) => setJustification(e.target.value)}
          setValue={setJustification}
          placeholder="Descreva o motivo da solicitação..."
          rows={3}
          aiContext="justificativa de redistribuição ou solicitação de tarefa"
          aiObjective="Ajude a redigir uma justificativa clara e formal para a solicitação"
          className="w-full px-3 py-2 rounded-lg text-sm text-foreground bg-muted/50 border border-border focus:border-[#7030A0] focus:outline-none resize-none mb-4 placeholder:text-muted-foreground/50"
        />

        <div className="flex gap-2">
          <button
            onClick={() => onConfirm(type, justification, target || undefined)}
            disabled={
              isPending ||
              justification.trim().length < 10 ||
              ((type === 'redistribuicao' || type === 'avocacao') && !target)
            }
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all disabled:opacity-50"
            style={{ background: '#7030A0', color: '#fff' }}
          >
            {isPending ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Send size={14} />
            )}
            Enviar solicitação
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm text-foreground/50 hover:text-foreground hover:bg-accent transition-all"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── Task Card ───────────────────────────────────────────────── */
function TaskCard({ task }: { task: TaskInstanceDto }) {
  const [showComplete, setShowComplete] = useState(false);
  const [showRequest, setShowRequest] = useState(false);

  const instanceId = task.instance;
  const complete = useCompleteTask(instanceId);
  const request = useCreateTaskRequest(instanceId);

  const statusConf = STATUS_CONFIG[task.status];
  const canAct = task.status !== 'completed' && task.status !== 'skipped';
  const dueInfo = getDueDateInfo(task.due_date);

  return (
    <>
      <div className="rounded-xl border border-border bg-card p-4 flex flex-col gap-3" data-tour="mt-task-card">
        {/* Header */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex flex-col gap-0.5 flex-1 min-w-0">
            <span className="text-sm font-semibold truncate">
              {task.label}
            </span>
            <span className="text-[11px] text-foreground/40">
              {NODE_TYPE_LABELS[task.node_type] ?? task.node_type}
            </span>
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            <div
              className="w-1.5 h-1.5 rounded-full"
              style={{ background: statusConf.color }}
            />
            <span className="text-[11px]" style={{ color: statusConf.color }}>
              {statusConf.label}
            </span>
          </div>
        </div>

        {/* Meta */}
        <div className="flex flex-wrap items-center gap-2">
          {task.role_required !== 'any' && (
            <span className="flex items-center gap-1 text-[11px] text-foreground/35">
              <User size={10} />
              {ROLE_LABELS[task.role_required] ?? task.role_required}
            </span>
          )}
          {task.assigned_to_name && (
            <span className="flex items-center gap-1 text-[11px] text-foreground/25">
              <User size={10} />
              {task.assigned_to_name}
            </span>
          )}
          {dueInfo && (
            <span
              className="flex items-center gap-1 text-[11px] px-1.5 py-0.5 rounded font-medium"
              style={{
                color: DUE_URGENCY_STYLE[dueInfo.urgency].color,
                background: DUE_URGENCY_STYLE[dueInfo.urgency].bg,
                border: `1px solid ${DUE_URGENCY_STYLE[dueInfo.urgency].border}`,
              }}
            >
              {(() => {
                const Icon = DUE_URGENCY_STYLE[dueInfo.urgency].icon;
                return <Icon size={9} />;
              })()}
              {dueInfo.text}
            </span>
          )}
        </div>

        {/* Instructions */}
        {task.instructions && (
          <p className="text-xs text-foreground/40 leading-relaxed line-clamp-2">
            {task.instructions}
          </p>
        )}

        {/* Pending requests badge */}
        {task.requests.some((r) => r.status === 'pending') && (
          <div className="flex items-center gap-1.5 text-[11px] text-amber-400/70 px-2 py-1 rounded-md bg-amber-500/5 border border-amber-500/15">
            <AlertCircle size={11} />
            Solicitação aguardando aprovação
          </div>
        )}
        {/* Approved/rejected request badge */}
        {task.requests.some((r) => r.status === 'approved') && (
          <div className="flex items-center gap-1.5 text-[11px] text-green-400/70 px-2 py-1 rounded-md bg-green-500/5 border border-green-500/15">
            <CheckCircle2 size={11} />
            Solicitação aprovada
          </div>
        )}
        {task.requests.some((r) => r.status === 'rejected') && (
          <div className="flex items-center gap-1.5 text-[11px] text-red-400/70 px-2 py-1 rounded-md bg-red-500/5 border border-red-500/15">
            <AlertCircle size={11} />
            Solicitação rejeitada
          </div>
        )}

        {/* Actions */}
        {canAct && (
          <div className="flex items-center gap-2 pt-2 border-t border-foreground/8">
            <button
              data-tour="mt-complete-btn"
              onClick={() => setShowComplete(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
              style={{
                background: '#22C55E20',
                color: '#22C55E',
                border: '1px solid #22C55E30',
              }}
            >
              <CheckCircle2 size={12} />
              Concluir
            </button>
            <button
              data-tour="mt-request-btn"
              onClick={() => setShowRequest(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all hover:bg-accent text-foreground/50 hover:text-foreground"
            >
              <ChevronRight size={12} />
              Solicitar
            </button>
          </div>
        )}
      </div>

      {showComplete && (
        <CompleteModal
          task={task}
          onClose={() => setShowComplete(false)}
          isPending={complete.isPending}
          onConfirm={(notes, gateway_choice) => {
            complete.mutate(
              { taskId: task.id, notes, gateway_choice },
              { onSuccess: () => setShowComplete(false) },
            );
          }}
        />
      )}

      {showRequest && (
        <RequestModal
          task={task}
          onClose={() => setShowRequest(false)}
          isPending={request.isPending}
          onConfirm={(type, justification, target) => {
            request.mutate(
              { taskId: task.id, request_type: type, justification, target_user: target },
              { onSuccess: () => setShowRequest(false) },
            );
          }}
        />
      )}
    </>
  );
}

/* ── Page ────────────────────────────────────────────────────── */
export default function MinhasTarefasPage() {
  const [statusFilter, setStatusFilter] = useState<string>('pending');
  const { data: tasks, isLoading, error, isRefetching } = useMyTasks(statusFilter);

  const filters = [
    { value: 'pending',     label: 'Pendentes' },
    { value: 'in_progress', label: 'Em andamento' },
    { value: 'completed',   label: 'Concluídas' },
    { value: 'all',         label: 'Todas' },
  ];

  // Count overdue tasks for badge
  const overdueCount = tasks?.filter((t) => {
    if (!t.due_date || t.status === 'completed' || t.status === 'skipped') return false;
    return new Date(t.due_date) < new Date();
  }).length ?? 0;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between" data-tour="mt-header">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Briefcase size={22} className="text-[#8B5CF6]" />
            Minhas Tarefas
          </h1>
          <p className="text-sm text-foreground/50 mt-1">
            Tarefas atribuídas a você nos fluxos de trabalho ativos
          </p>
        </div>
        {isRefetching && (
          <div className="flex items-center gap-1.5 text-[11px] text-foreground/30 mt-1">
            <Loader2 size={10} className="animate-spin" />
            Atualizando...
          </div>
        )}
      </div>

      {/* Overdue alert */}
      {overdueCount > 0 && (
        <div
          className="flex items-center gap-3 px-4 py-3 rounded-xl mb-5 text-sm"
          style={{
            background: '#EF444410',
            border: '1px solid #EF444425',
            color: '#EF4444',
          }}
        >
          <AlertCircle size={15} />
          <span>
            <strong>{overdueCount}</strong> tarefa{overdueCount !== 1 ? 's' : ''} com prazo vencido.
          </span>
        </div>
      )}

      {/* Filter tabs */}
      <div className="flex items-center gap-1 mb-6" data-tour="mt-filters">
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
        {tasks && (
          <span className="ml-2 text-xs text-foreground/30">{tasks.length} tarefa(s)</span>
        )}
      </div>

      {/* Content */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="rounded-xl border border-border bg-card p-4 animate-pulse">
              <div className="flex items-start justify-between gap-2 mb-3">
                <div className="flex-1">
                  <div className="h-4 bg-foreground/8 rounded w-3/4 mb-2" />
                  <div className="h-3 bg-foreground/5 rounded w-1/3" />
                </div>
                <div className="h-3 bg-foreground/8 rounded w-16" />
              </div>
              <div className="h-3 bg-foreground/5 rounded w-1/2 mb-3" />
              <div className="h-3 bg-foreground/5 rounded w-full mb-1" />
              <div className="h-3 bg-foreground/5 rounded w-2/3 mb-4" />
              <div className="flex gap-2 pt-2 border-t border-foreground/8">
                <div className="h-7 bg-foreground/8 rounded-lg w-20" />
                <div className="h-7 bg-foreground/5 rounded-lg w-16" />
              </div>
            </div>
          ))}
        </div>
      )}

      {error && (
        <div className="flex items-center gap-3 p-4 rounded-xl border border-red-500/20 bg-red-500/5 text-red-400 text-sm">
          <AlertCircle size={16} />
          Erro ao carregar tarefas.
        </div>
      )}

      {tasks?.length === 0 && !isLoading && (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <CheckCircle2 size={40} className="text-foreground/15 mb-4" />
          <p className="text-foreground/40 text-sm font-medium">Nenhuma tarefa encontrada.</p>
          <p className="text-foreground/25 text-xs mt-1 max-w-sm">
            {statusFilter === 'pending'
              ? 'Você não possui tarefas pendentes no momento. Tarefas são criadas quando um fluxo de trabalho é iniciado e atribuído a você.'
              : statusFilter === 'in_progress'
                ? 'Nenhuma tarefa em andamento. Inicie uma tarefa pendente para vê-la aqui.'
                : statusFilter === 'completed'
                  ? 'Nenhuma tarefa concluída ainda. Complete suas tarefas pendentes para acompanhá-las aqui.'
                  : 'Nenhuma tarefa encontrada neste filtro.'}
          </p>
          {statusFilter !== 'pending' && (
            <button
              onClick={() => setStatusFilter('pending')}
              className="mt-4 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
              style={{ background: '#7030A015', color: '#C084FC', border: '1px solid #7030A040' }}
            >
              Ver tarefas pendentes
            </button>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {tasks?.map((task) => (
          <TaskCard key={task.id} task={task} />
        ))}
      </div>
    </div>
  );
}
