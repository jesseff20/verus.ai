'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Activity, Play, CheckCircle2, XCircle, Clock,
  ExternalLink, Loader2, AlertCircle, ChevronRight, Workflow,
  FileUp, Sparkles,
} from 'lucide-react';
import { useFlowTemplates } from '@/hooks/useFlowTemplates';
import { useFlowInstance, useStartFlowForCase } from '@/hooks/useFlowExecution';
import { useAuth } from '@/hooks/use-auth';
import api from '@/lib/api';

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

type ExtractedCaseData = {
  titulo?: string;
  numero_processo?: string;
  especialidade?: string;
  descricao?: string;
  observacoes?: string;
  cliente_nome?: string;
  cliente_documento?: string;
  parte_contraria?: string;
  parte_contraria_documento?: string;
  tribunal?: string;
  comarca?: string;
  vara_juizo?: string;
  estado?: string;
  valor_causa?: string | number;
  data_distribuicao?: string;
  prazos_identificados?: unknown[];
};

function applyCNJMask(value: string): string {
  const digits = value.replace(/\D/g, '').slice(0, 20);
  let result = '';
  for (let i = 0; i < digits.length; i++) {
    if (i === 7) result += '-';
    if (i === 9) result += '.';
    if (i === 13) result += '.';
    if (i === 14) result += '.';
    if (i === 16) result += '.';
    result += digits[i];
  }
  return result;
}

function applyCpfCnpjMask(value: string): string {
  const digits = value.replace(/\D/g, '');
  if (digits.length <= 11) {
    let result = '';
    for (let i = 0; i < Math.min(digits.length, 11); i++) {
      if (i === 3 || i === 6) result += '.';
      if (i === 9) result += '-';
      result += digits[i];
    }
    return result;
  }

  const cnpj = digits.slice(0, 14);
  let result = '';
  for (let i = 0; i < cnpj.length; i++) {
    if (i === 2) result += '.';
    if (i === 5) result += '.';
    if (i === 8) result += '/';
    if (i === 12) result += '-';
    result += cnpj[i];
  }
  return result;
}

function toCasePatch(data: ExtractedCaseData): Record<string, string | number> {
  const patch: Record<string, string | number> = {};
  const assign = (target: string, value: unknown, transform?: (v: string) => string) => {
    if (value === undefined || value === null || value === '') return;
    const normalized = typeof value === 'number' ? value : String(value).trim();
    if (normalized === '') return;
    patch[target] = transform && typeof normalized === 'string' ? transform(normalized) : normalized;
  };

  assign('titulo', data.titulo);
  assign('numero_processo', data.numero_processo, applyCNJMask);
  assign('especialidade', data.especialidade);
  assign('descricao', data.descricao);
  assign('observacoes', data.observacoes);
  assign('cliente_nome', data.cliente_nome);
  assign('cliente_cpf_cnpj', data.cliente_documento, applyCpfCnpjMask);
  assign('parte_contraria', data.parte_contraria);
  assign('parte_contraria_cpf_cnpj', data.parte_contraria_documento, applyCpfCnpjMask);
  assign('tribunal', data.tribunal);
  assign('comarca', data.comarca);
  assign('vara_juizo', data.vara_juizo);
  assign('valor_causa', data.valor_causa);
  assign('data_distribuicao', data.data_distribuicao);
  return patch;
}

function SelectTemplateModal({
  caseId,
  onClose,
}: {
  caseId: string;
  onClose: () => void;
}) {
  const router = useRouter();
  const { user } = useAuth();
  const { data: templates } = useFlowTemplates();
  const startFlow = useStartFlowForCase();
  const [selectedId, setSelectedId] = useState('');
  const [documentName, setDocumentName] = useState('');
  const [extractedData, setExtractedData] = useState<ExtractedCaseData | null>(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isApplying, setIsApplying] = useState(false);
  const [extractError, setExtractError] = useState('');

  const published = templates?.filter((t) => t.status === 'published') ?? [];
  const filledFields = extractedData ? Object.keys(toCasePatch(extractedData)).length : 0;
  const userIdentity = `${user?.username ?? ''} ${user?.email ?? ''}`.toLowerCase();
  const isDemoUser = (
    userIdentity.includes('demo')
    || userIdentity.includes('demonstracao')
    || userIdentity.includes('demonstração')
  );

  const handleDocumentUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setDocumentName(file.name);
    setExtractedData(null);
    setExtractError('');
    setIsExtracting(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const { data } = await api.post<ExtractedCaseData>(
        '/api/v1/processos/extract-from-document/',
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } },
      );
      setExtractedData(data);

      const suggestionPayload = {
        especialidade: data.especialidade || '',
        descricao: data.descricao || data.titulo || '',
        tribunal: data.tribunal || '',
      };
      const suggestion = await api.post('/api/v1/workflow-execution/suggest-flow/', suggestionPayload);
      const firstSuggestion = suggestion.data?.suggestions?.[0];
      if (firstSuggestion?.id) {
        setSelectedId(String(firstSuggestion.id));
      }
    } catch (error: any) {
      setExtractError(
        error?.response?.data?.error
        || error?.response?.data?.detail
        || 'Nao foi possivel extrair dados do documento.',
      );
    } finally {
      setIsExtracting(false);
      event.target.value = '';
    }
  };

  const handleStart = async () => {
    if (!selectedId) return;
    setIsApplying(true);
    try {
      if (isDemoUser && extractedData) {
        const patch = toCasePatch(extractedData);
        if (Object.keys(patch).length > 0) {
          await api.patch(`/api/v1/processos/${caseId}/`, patch);
        }
      }
      const instance = await startFlow.mutateAsync({ caseId, template_id: selectedId });
      onClose();
      router.push(`/dashboard/execucoes/${instance.id}`);
    } catch {
      /* handled */
    } finally {
      setIsApplying(false);
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
          {isDemoUser
            ? 'Anexe o documento do processo para preencher os dados e sugerir o fluxo.'
            : 'Selecione o template de fluxo para este processo.'}
        </p>

        {isDemoUser && (
          <>
            <label
              className="mb-4 flex cursor-pointer items-center gap-3 rounded-lg border px-3 py-3 transition-all hover:bg-white/5"
              style={{ borderColor: '#2A2A2A', background: '#0A0A0A' }}
            >
              <input
                type="file"
                className="hidden"
                accept=".pdf,.docx,.doc,.odt,.txt"
                onChange={handleDocumentUpload}
                disabled={isExtracting || isApplying}
              />
              <FileUp size={16} className="text-[#C084FC] shrink-0" />
              <div className="min-w-0 flex-1">
                <p className="text-sm text-white/80 truncate">
                  {documentName || 'Anexar documento processual'}
                </p>
                <p className="text-[10px] text-white/35">
                  PDF, DOCX, ODT ou TXT. A IA extrai numero, partes, tribunal, prazos e assunto.
                </p>
              </div>
              {isExtracting && <Loader2 size={14} className="animate-spin text-[#C084FC]" />}
            </label>

            {extractError && (
              <div
                className="mb-4 rounded-lg border px-3 py-2 text-xs"
                style={{ borderColor: '#EF444440', background: '#EF444410', color: '#FCA5A5' }}
              >
                {extractError}
              </div>
            )}

            {extractedData && (
              <div
                className="mb-4 rounded-lg border px-3 py-2 text-xs"
                style={{ borderColor: '#22C55E40', background: '#22C55E10', color: '#86EFAC' }}
              >
                <div className="flex items-center gap-2 font-medium">
                  <Sparkles size={12} />
                  {filledFields} campo{filledFields !== 1 ? 's' : ''} do processo pronto{filledFields !== 1 ? 's' : ''} para atualizar
                </div>
                {(extractedData.titulo || extractedData.numero_processo) && (
                  <p className="mt-1 truncate text-white/55">
                    {extractedData.numero_processo ? applyCNJMask(extractedData.numero_processo) : extractedData.titulo}
                  </p>
                )}
              </div>
            )}
          </>
        )}

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
            disabled={!selectedId || startFlow.isPending || isExtracting || isApplying}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all disabled:opacity-50"
            style={{ background: '#7030A0', color: '#fff' }}
          >
            {startFlow.isPending || isApplying ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            {extractedData ? 'Atualizar e iniciar' : 'Iniciar fluxo'}
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

  const hasFlow = Boolean(
    activeFlowId
    && activeFlowStatus
    && !['completed', 'cancelled'].includes(activeFlowStatus),
  );
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
              {/* Botão para iniciar NOVO fluxo independente */}
              <button
                onClick={() => setShowModal(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all hover:bg-white/8 text-white/50 hover:text-white"
              >
                <Play size={12} />
                Novo fluxo
              </button>
            </div>

            {activeFlowStatus === 'running' && (
              <p className="text-[10px] text-white/25 leading-relaxed">
                Você pode iniciar múltiplos fluxos independentes para o mesmo processo.
                Cada fluxo é executado separadamente.
              </p>
            )}
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
