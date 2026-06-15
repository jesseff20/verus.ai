'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Plus, Workflow, Clock, CheckCircle2, Archive,
  Copy, Trash2, ExternalLink, Loader2, AlertCircle, Play,
  FilePlus2, Inbox, ListChecks, MessageSquareText,
} from 'lucide-react';
import { AIInput } from '@/components/ui/ai-input';
import { AITextarea } from '@/components/ui/ai-textarea';
import api from '@/lib/api';
import {
  useFlowTemplates,
  useCreateFlowTemplate,
  useDuplicateFlow,
  useDeleteFlowTemplate,
  type FlowTemplateListItem,
} from '@/hooks/useFlowTemplates';
import { useStartFlow, useStartFlowForCase } from '@/hooks/useFlowExecution';
import { useAuth } from '@/hooks/use-auth';

const CATEGORY_LABELS: Record<string, string> = {
  judicial_1: 'Judicial — 1º Grau',
  judicial_2: 'Judicial — 2º Grau',
  administrative: 'Administrativo',
  other: 'Outro',
};

const STATUS_CONFIG = {
  draft: { label: 'Rascunho', color: '#F59E0B', icon: Clock },
  published: { label: 'Publicado', color: '#22C55E', icon: CheckCircle2 },
  archived: { label: 'Arquivado', color: '#6B7280', icon: Archive },
};

type DemoCaseOption = {
  id: string;
  numero_processo: string;
  titulo: string;
  cliente_nome?: string;
  active_flow_id?: string | null;
  active_flow_status?: string | null;
};

type CasesResponse = {
  results?: DemoCaseOption[];
};

function isDemoUser(user: { username?: string; email?: string } | null | undefined) {
  const identity = `${user?.username ?? ''} ${user?.email ?? ''}`.toLowerCase();
  return identity.includes('usuario_demo') || identity.includes('demo');
}

function DemoEntryModal({
  onClose,
  onNewTask,
  onNewProcess,
  onExistingExecution,
  onMyTask,
}: {
  onClose: () => void;
  onNewTask: () => void;
  onNewProcess: () => void;
  onExistingExecution: () => void;
  onMyTask: () => void;
}) {
  const options = [
    {
      icon: MessageSquareText,
      title: 'Iniciar nova tarefa',
      description: 'Escolha o fluxo, selecione um processo existente e descreva o objetivo para a IA.',
      action: onNewTask,
    },
    {
      icon: FilePlus2,
      title: 'Iniciar novo processo',
      description: 'Crie um processo/caso antes de vincula-lo a uma jornada de trabalho.',
      action: onNewProcess,
    },
    {
      icon: Workflow,
      title: 'Abrir tarefa existente',
      description: 'Veja execucoes ja abertas e acompanhe o andamento dos processos.',
      action: onExistingExecution,
    },
    {
      icon: Inbox,
      title: 'Tratar tarefa comigo',
      description: 'Abra a fila de tarefas atribuidas ao usuario de demonstracao.',
      action: onMyTask,
    },
  ];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.75)' }}
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl rounded-xl border border-border bg-card p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-5">
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-foreground/35">Perfil demo</p>
          <h2 className="mt-1 text-lg font-semibold">Como deseja iniciar a jornada?</h2>
          <p className="mt-1 text-sm text-foreground/45">
            Escolha a entrada do fluxo de trabalho para demonstrar os cenarios principais.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {options.map((option) => {
            const Icon = option.icon;
            return (
              <button
                key={option.title}
                type="button"
                onClick={option.action}
                className="min-h-[132px] rounded-lg border border-border bg-muted/30 p-4 text-left transition-all hover:border-[#7030A0]/50 hover:bg-[#7030A0]/10"
              >
                <span className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg border border-[#7030A0]/25 bg-[#7030A0]/15 text-[#C084FC]">
                  <Icon size={17} />
                </span>
                <span className="block text-sm font-semibold text-foreground">{option.title}</span>
                <span className="mt-1 block text-xs leading-relaxed text-foreground/45">{option.description}</span>
              </button>
            );
          })}
        </div>

        <div className="mt-5 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm text-foreground/50 hover:text-foreground hover:bg-foreground/8 transition-all"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
}

function DemoStartTaskModal({
  templates,
  onClose,
}: {
  templates: FlowTemplateListItem[];
  onClose: () => void;
}) {
  const router = useRouter();
  const startFlowForCase = useStartFlowForCase();
  const publishedTemplates = templates.filter((template) => template.status === 'published');
  const firstPublishedTemplateId = publishedTemplates[0]?.id ?? '';
  const [templateId, setTemplateId] = useState(firstPublishedTemplateId);
  const [cases, setCases] = useState<DemoCaseOption[]>([]);
  const [caseId, setCaseId] = useState('');
  const [prompt, setPrompt] = useState('');
  const [loadingCases, setLoadingCases] = useState(true);
  const [caseError, setCaseError] = useState('');

  useEffect(() => {
    let cancelled = false;

    async function loadCases() {
      setLoadingCases(true);
      setCaseError('');
      try {
        const { data } = await api.get<CasesResponse | DemoCaseOption[]>('/api/v1/processos/', {
          params: { page_size: 50 },
        });
        const list = Array.isArray(data) ? data : data.results ?? [];
        if (!cancelled) {
          setCases(list);
          setCaseId((current) => current || list.find((item) => item.active_flow_status !== 'running')?.id || list[0]?.id || '');
        }
      } catch {
        if (!cancelled) {
          setCaseError('Nao foi possivel carregar os processos disponiveis.');
        }
      } finally {
        if (!cancelled) {
          setLoadingCases(false);
        }
      }
    }

    loadCases();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!templateId && firstPublishedTemplateId) {
      setTemplateId(firstPublishedTemplateId);
    }
  }, [firstPublishedTemplateId, templateId]);

  const selectedCase = cases.find((item) => item.id === caseId);
  const caseHasRunningFlow = selectedCase?.active_flow_status === 'running';
  const canSubmit = Boolean(templateId && caseId && prompt.trim() && !caseHasRunningFlow);

  const handleStart = async () => {
    if (!canSubmit) return;
    try {
      const instance = await startFlowForCase.mutateAsync({ caseId, template_id: templateId });
      router.push(`/dashboard/execucoes/${instance.id}`);
    } catch {
      /* handled by react-query */
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.75)' }}
      onClick={onClose}
    >
      <div
        className="w-full max-w-xl rounded-xl border border-border bg-card p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-5 flex items-start gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-[#7030A0]/25 bg-[#7030A0]/15 text-[#C084FC]">
            <ListChecks size={18} />
          </span>
          <div>
            <h2 className="text-lg font-semibold">Iniciar nova tarefa</h2>
            <p className="mt-1 text-sm text-foreground/45">
              Selecione o fluxo publicado, escolha um processo existente e descreva a demanda para a IA.
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <label className="block">
            <span className="mb-1 block text-xs text-foreground/50">Tipo de tarefa</span>
            <select
              value={templateId}
              onChange={(event) => setTemplateId(event.target.value)}
              className="w-full rounded-lg border border-border bg-muted/50 px-3 py-2 text-sm text-foreground focus:border-[#7030A0] focus:outline-none"
            >
              {publishedTemplates.map((template) => (
                <option key={template.id} value={template.id}>
                  {template.name}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="mb-1 block text-xs text-foreground/50">Processo ou caso criado</span>
            <select
              value={caseId}
              onChange={(event) => setCaseId(event.target.value)}
              disabled={loadingCases}
              className="w-full rounded-lg border border-border bg-muted/50 px-3 py-2 text-sm text-foreground focus:border-[#7030A0] focus:outline-none disabled:opacity-60"
            >
              {loadingCases && <option>Carregando processos...</option>}
              {!loadingCases && cases.length === 0 && <option value="">Nenhum processo disponivel</option>}
              {!loadingCases && cases.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.numero_processo || item.titulo} - {item.titulo}
                </option>
              ))}
            </select>
          </label>

          {caseError && (
            <p className="rounded-lg border border-red-500/20 bg-red-500/5 px-3 py-2 text-xs text-red-400">{caseError}</p>
          )}

          {caseHasRunningFlow && (
            <p className="rounded-lg border border-amber-500/20 bg-amber-500/5 px-3 py-2 text-xs text-amber-300">
              Este processo ja possui fluxo em andamento. Escolha outro processo para iniciar uma nova tarefa.
            </p>
          )}

          <label className="block">
            <span className="mb-1 block text-xs text-foreground/50">Pedido inicial para a IA</span>
            <AITextarea
              variant="dark"
              rows={4}
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              setValue={setPrompt}
              placeholder="Ex: Analise a distribuicao do processo e prepare a triagem inicial."
              aiContext="inicio de tarefa em fluxo de trabalho juridico"
              aiObjective="Melhore o pedido inicial para orientar a execucao da tarefa no processo selecionado"
              className="min-h-[112px]"
            />
          </label>
        </div>

        <div className="mt-5 flex gap-2">
          <button
            type="button"
            onClick={handleStart}
            disabled={!canSubmit || startFlowForCase.isPending}
            className="flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all disabled:opacity-50"
            style={{ background: '#7030A0', color: '#fff' }}
          >
            {startFlowForCase.isPending ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            Iniciar tarefa
          </button>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm text-foreground/50 hover:text-foreground hover:bg-foreground/8 transition-all"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
}

function StartFlowModal({
  template,
  onClose,
}: {
  template: FlowTemplateListItem;
  onClose: () => void;
}) {
  const router = useRouter();
  const startFlow = useStartFlow();
  const [caseRef, setCaseRef] = useState('');
  const [caseTitle, setCaseTitle] = useState('');

  const handleStart = async () => {
    try {
      const instance = await startFlow.mutateAsync({
        template_id: template.id,
        case_ref: caseRef.trim(),
        case_title: caseTitle.trim(),
      });
      router.push(`/dashboard/execucoes/${instance.id}`);
    } catch {
      /* handled by react-query */
    }
  };

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
        <h2 className="text-base font-semibold mb-1">Iniciar fluxo</h2>
        <p className="text-xs text-foreground/40 mb-4">{template.name}</p>

        <label className="block text-xs text-foreground/50 mb-1">
          Número/referência do processo <span className="text-foreground/30">(opcional)</span>
        </label>
        <AIInput
          type="text"
          variant="dark"
          autoFocus
          value={caseRef}
          onChange={(e) => setCaseRef(e.target.value)}
          setValue={setCaseRef}
          placeholder="ex: 0001234-12.2024.8.00.0000"
          aiContext="número do processo judicial"
          aiObjective="Formate ou sugira o número do processo no padrão CNJ"
          className="w-full px-3 py-2 rounded-lg text-sm text-foreground bg-muted/50 border border-border focus:border-[#7030A0] focus:outline-none mb-3 placeholder:text-muted-foreground/50"
        />

        <label className="block text-xs text-foreground/50 mb-1">
          Título/ementa <span className="text-foreground/30">(opcional)</span>
        </label>
        <AIInput
          type="text"
          variant="dark"
          value={caseTitle}
          onChange={(e) => setCaseTitle(e.target.value)}
          setValue={setCaseTitle}
          onKeyDown={(e) => e.key === 'Enter' && handleStart()}
          placeholder="Breve descrição do processo..."
          aiContext="ementa ou título do processo"
          aiObjective="Sugira uma ementa clara e concisa para o processo judicial"
          className="w-full px-3 py-2 rounded-lg text-sm text-foreground bg-muted/50 border border-border focus:border-[#7030A0] focus:outline-none mb-4 placeholder:text-muted-foreground/50"
        />

        <div className="flex gap-2">
          <button
            onClick={handleStart}
            disabled={startFlow.isPending}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all disabled:opacity-50"
            style={{ background: '#7030A0', color: '#fff' }}
          >
            {startFlow.isPending ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            Iniciar fluxo
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm text-foreground/50 hover:text-foreground hover:bg-foreground/8 transition-all"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
}

function TemplateCard({
  template,
  onOpen,
  onDuplicate,
  onDelete,
  onStart,
  canStart,
}: {
  template: FlowTemplateListItem;
  onOpen: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
  onStart: () => void;
  canStart: boolean;
}) {
  const [confirmDelete, setConfirmDelete] = useState(false);
  const status = STATUS_CONFIG[template.status];
  const StatusIcon = status.icon;

  return (
    <div
      className="group rounded-xl border border-border bg-card p-5 flex flex-col gap-3 hover:border-foreground/15 transition-all cursor-pointer"
      onClick={onOpen}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <div
            className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
            style={{ background: '#7030A015', border: '1px solid #7030A030' }}
          >
            <Workflow size={17} className="text-[#8B5CF6]" />
          </div>
          <div>
            <h3 className="text-sm font-semibold leading-tight">{template.name}</h3>
            <p className="text-[11px] text-foreground/40 mt-0.5">
              {CATEGORY_LABELS[template.category] ?? template.category}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1 shrink-0">
          <StatusIcon size={12} style={{ color: status.color }} />
          <span
            className="text-[10px] font-medium"
            style={{ color: status.color }}
          >
            {status.label}
          </span>
        </div>
      </div>

      {/* Description */}
      {template.description && (
        <p className="text-xs text-foreground/40 leading-relaxed line-clamp-2">{template.description}</p>
      )}

      {/* Stats */}
      <div className="flex items-center gap-3 text-[11px] text-foreground/35">
        <span>{template.node_count} nós</span>
        <span>·</span>
        <span>{template.swimlane_count} swim lanes</span>
        <span>·</span>
        <span>v{template.version}</span>
        {template.is_system_template && (
          <>
            <span>·</span>
            <span
              className="px-1.5 py-0.5 rounded text-[10px] font-mono"
              style={{ background: '#7030A015', color: '#8B5CF6', border: '1px solid #7030A030' }}
            >
              sistema
            </span>
          </>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 pt-1 border-t border-foreground/8">
        <button
          onClick={(e) => { e.stopPropagation(); onOpen(); }}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all hover:bg-foreground/8 text-foreground/60 hover:text-foreground"
        >
          <ExternalLink size={12} />
          Abrir editor
        </button>
        {template.status === 'published' && canStart && (
          <button
            onClick={(e) => { e.stopPropagation(); onStart(); }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
            style={{ background: '#7030A015', color: '#C084FC', border: '1px solid #7030A030' }}
          >
            <Play size={12} />
            Iniciar
          </button>
        )}
        <div className="flex-1" />
        <button
          onClick={(e) => { e.stopPropagation(); onDuplicate(); }}
          className="w-7 h-7 rounded flex items-center justify-center text-foreground/30 hover:text-foreground hover:bg-foreground/8 transition-all"
          title="Duplicar"
        >
          <Copy size={13} />
        </button>
        {!template.is_system_template && (
          confirmDelete ? (
            <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
              <button
                onClick={() => { onDelete(); setConfirmDelete(false); }}
                className="px-2 py-0.5 rounded text-[10px] font-medium transition-all"
                style={{ background: '#EF444420', color: '#EF4444', border: '1px solid #EF444430' }}
              >
                Confirmar
              </button>
              <button
                onClick={() => setConfirmDelete(false)}
                className="px-2 py-0.5 rounded text-[10px] font-medium text-foreground/40 hover:text-foreground transition-all"
              >
                Não
              </button>
            </div>
          ) : (
            <button
              onClick={(e) => { e.stopPropagation(); setConfirmDelete(true); }}
              className="w-7 h-7 rounded flex items-center justify-center text-foreground/30 hover:text-red-400 hover:bg-red-400/10 transition-all"
              title="Deletar"
            >
              <Trash2 size={13} />
            </button>
          )
        )}
      </div>
    </div>
  );
}

export default function FluxosPage() {
  const router = useRouter();
  const { user, hasPermission } = useAuth();
  const { data: templates, isLoading, error } = useFlowTemplates();
  const createTemplate = useCreateFlowTemplate();
  const duplicateFlow = useDuplicateFlow();
  const deleteFlow = useDeleteFlowTemplate();

  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [filter, setFilter] = useState<'all' | 'draft' | 'published'>('all');
  const [startingTemplate, setStartingTemplate] = useState<FlowTemplateListItem | null>(null);
  const [showDemoEntry, setShowDemoEntry] = useState(false);
  const [showDemoStartTask, setShowDemoStartTask] = useState(false);

  // distribuidor=30 é o mínimo para iniciar fluxo (alinhado com CanStartFlow no backend)
  const canStart = hasPermission('distribuidor');
  const demoProfile = isDemoUser(user);

  const filtered = templates?.filter((t) => filter === 'all' || t.status === filter);

  useEffect(() => {
    if (demoProfile) {
      setShowDemoEntry(true);
    }
  }, [demoProfile]);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    try {
      const result = await createTemplate.mutateAsync({ name: newName.trim() });
      router.push(`/dashboard/fluxos/editor/${result.id}`);
    } catch {
      /* handled by react-query */
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Fluxos de Trabalho</h1>
          <p className="text-sm text-foreground/50 mt-1">
            Templates BPMN de processos judiciais e administrativos
          </p>
        </div>
        <button
          onClick={() => setCreating(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all"
          style={{ background: '#7030A0', color: '#fff' }}
        >
          <Plus size={15} />
          Novo fluxo
        </button>
      </div>

      {/* Start flow modal */}
      {startingTemplate && (
        <StartFlowModal
          template={startingTemplate}
          onClose={() => setStartingTemplate(null)}
        />
      )}

      {showDemoEntry && (
        <DemoEntryModal
          onClose={() => setShowDemoEntry(false)}
          onNewTask={() => {
            setShowDemoEntry(false);
            setShowDemoStartTask(true);
          }}
          onNewProcess={() => router.push('/dashboard/processos/novo')}
          onExistingExecution={() => router.push('/dashboard/execucoes')}
          onMyTask={() => router.push('/dashboard/minhas-tarefas')}
        />
      )}

      {showDemoStartTask && templates && (
        <DemoStartTaskModal
          templates={templates}
          onClose={() => setShowDemoStartTask(false)}
        />
      )}

      {/* New template modal */}
      {creating && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center"
          style={{ background: 'rgba(0,0,0,0.7)' }}
          onClick={() => setCreating(false)}
        >
          <div
            className="rounded-xl border border-border bg-card p-6 w-full max-w-sm"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-base font-semibold mb-4">Novo fluxo</h2>
            <AIInput
              autoFocus
              type="text"
              variant="dark"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              setValue={setNewName}
              onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
              placeholder="Nome do fluxo..."
              aiContext="nome do fluxo de trabalho judicial"
              aiObjective="Sugira um nome claro e descritivo para o fluxo de trabalho"
              className="w-full px-3 py-2 rounded-lg text-sm text-foreground bg-muted/50 border border-border focus:border-[#7030A0] focus:outline-none mb-4 placeholder:text-muted-foreground/50"
            />
            <div className="flex gap-2">
              <button
                onClick={handleCreate}
                disabled={!newName.trim() || createTemplate.isPending}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all disabled:opacity-50"
                style={{ background: '#7030A0', color: '#fff' }}
              >
                {createTemplate.isPending ? <Loader2 size={14} className="animate-spin" /> : null}
                Criar e abrir editor
              </button>
              <button
                onClick={() => setCreating(false)}
                className="px-4 py-2 rounded-lg text-sm text-foreground/50 hover:text-foreground hover:bg-foreground/8 transition-all"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Filter tabs */}
      <div className="flex items-center gap-1 mb-6">
        {(['all', 'published', 'draft'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
            style={{
              background: filter === f ? '#7030A020' : 'transparent',
              color: filter === f ? '#C084FC' : '#6B7280',
              border: filter === f ? '1px solid #7030A040' : '1px solid transparent',
            }}
          >
            {f === 'all' ? 'Todos' : f === 'published' ? 'Publicados' : 'Rascunhos'}
          </button>
        ))}
        {templates && (
          <span className="ml-2 text-xs text-foreground/30">{filtered?.length ?? 0} templates</span>
        )}
      </div>

      {/* Content */}
      {isLoading && (
        <div className="flex items-center justify-center py-24">
          <Loader2 size={24} className="animate-spin text-foreground/20" />
        </div>
      )}

      {error && (
        <div className="flex items-center gap-3 p-4 rounded-xl border border-red-500/20 bg-red-500/5 text-red-400 text-sm">
          <AlertCircle size={16} />
          Erro ao carregar templates. Verifique a conexão com o servidor.
        </div>
      )}

      {filtered && filtered.length === 0 && !isLoading && (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <Workflow size={40} className="text-foreground/15 mb-4" />
          <p className="text-foreground/40 text-sm">Nenhum template encontrado.</p>
          <button
            onClick={() => setCreating(true)}
            className="mt-4 text-sm text-[#8B5CF6] hover:underline"
          >
            Criar o primeiro fluxo
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered?.map((template) => (
          <TemplateCard
            key={template.id}
            template={template}
            onOpen={() => router.push(`/dashboard/fluxos/editor/${template.id}`)}
            onDuplicate={() => duplicateFlow.mutate(template.id)}
            onStart={() => setStartingTemplate(template)}
            onDelete={() => deleteFlow.mutate(template.id)}
            canStart={canStart}
          />
        ))}
      </div>
    </div>
  );
}
