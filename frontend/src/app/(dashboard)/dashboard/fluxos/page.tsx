'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Plus, Workflow, Clock, CheckCircle2, Archive,
  Copy, Trash2, ExternalLink, Loader2, AlertCircle, Play,
} from 'lucide-react';
import { AIInput } from '@/components/ui/ai-input';
import {
  useFlowTemplates,
  useCreateFlowTemplate,
  useDuplicateFlow,
  useDeleteFlowTemplate,
  type FlowTemplateListItem,
} from '@/hooks/useFlowTemplates';
import { useStartFlow } from '@/hooks/useFlowExecution';
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
          className="w-full px-3 py-2 rounded-lg text-sm text-foreground bg-foreground/5 border border-foreground/10 focus:border-[#7030A0] focus:outline-none mb-3 placeholder:text-foreground/25"
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
          className="w-full px-3 py-2 rounded-lg text-sm text-foreground bg-foreground/5 border border-foreground/10 focus:border-[#7030A0] focus:outline-none mb-4 placeholder:text-foreground/25"
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

  // distribuidor=30 é o mínimo para iniciar fluxo (alinhado com CanStartFlow no backend)
  const canStart = hasPermission('distribuidor');

  const filtered = templates?.filter((t) => filter === 'all' || t.status === filter);

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
              className="w-full px-3 py-2 rounded-lg text-sm text-foreground bg-foreground/5 border border-foreground/10 focus:border-[#7030A0] focus:outline-none mb-4 placeholder:text-foreground/25"
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
