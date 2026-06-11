'use client';

import { Node } from '@xyflow/react';
import { X } from 'lucide-react';

const ROLE_OPTIONS = [
  { value: 'any', label: 'Qualquer papel' },
  { value: 'distribuidor', label: 'Distribuidor(a)' },
  { value: 'procurador', label: 'Procurador(a)' },
  { value: 'gerente', label: 'Gerente' },
  { value: 'assessor_gerencial', label: 'Assessor(a) Gerencial' },
  { value: 'assessor_gabinete', label: 'Assessor(a) de Gabinete' },
  { value: 'procurador_geral', label: 'Procurador(a)-Geral' },
  { value: 'subprocurador_geral', label: 'Subprocurador(a)-Geral' },
];

const NODE_TYPE_LABELS: Record<string, string> = {
  swimlane: 'Swim Lane',
  start_event: 'Evento de Início',
  end_event: 'Evento de Fim',
  intermediate_event: 'Evento Intermediário',
  task: 'Tarefa',
  user_task: 'Tarefa de Usuário',
  service_task: 'Tarefa de Serviço',
  exclusive_gateway: 'Gateway Exclusivo (XOR)',
  parallel_gateway: 'Gateway Paralelo (AND)',
  inclusive_gateway: 'Gateway Inclusivo (OR)',
};

type Props = {
  node: Node | null;
  onUpdate: (nodeId: string, changes: Partial<{ label: string; role: string; description: string }>) => void;
  onClose: () => void;
};

export default function PropertiesPanel({ node, onUpdate, onClose }: Props) {
  if (!node) return null;

  const data = node.data as Record<string, unknown>;
  const label = (data.label as string) ?? '';
  const role = (data.role as string) ?? 'any';
  const description = (data.description as string) ?? '';
  const nodeType = (data.node_type as string) ?? node.type ?? '';

  return (
    <div
      className="absolute right-0 top-0 bottom-0 z-10 flex flex-col border-l"
      style={{
        width: 280,
        background: '#0F0F0F',
        borderColor: '#1F1F1F',
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: '#1F1F1F' }}>
        <div>
          <p className="text-[11px] text-white/40 font-mono uppercase tracking-widest mb-0.5">Propriedades</p>
          <p className="text-xs font-medium text-white/80">{NODE_TYPE_LABELS[nodeType] ?? nodeType}</p>
        </div>
        <button
          onClick={onClose}
          className="w-6 h-6 rounded flex items-center justify-center text-white/40 hover:text-white hover:bg-white/10 transition-all"
        >
          <X size={13} />
        </button>
      </div>

      {/* Fields */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Rótulo */}
        <div>
          <label className="block text-[11px] text-white/50 mb-1.5 font-medium uppercase tracking-wide">
            Rótulo
          </label>
          <textarea
            value={label}
            onChange={(e) => onUpdate(node.id, { label: e.target.value })}
            rows={2}
            className="w-full px-3 py-2 rounded-lg text-sm text-white bg-white/5 border border-white/10 focus:border-[#7030A0] focus:outline-none resize-none transition-colors placeholder:text-white/20"
            placeholder="Nome do nó"
          />
        </div>

        {/* Papel */}
        {nodeType !== 'swimlane' && (
          <div>
            <label className="block text-[11px] text-white/50 mb-1.5 font-medium uppercase tracking-wide">
              Papel responsável
            </label>
            <select
              value={role}
              onChange={(e) => onUpdate(node.id, { role: e.target.value })}
              className="w-full px-3 py-2 rounded-lg text-sm text-white bg-white/5 border border-white/10 focus:border-[#7030A0] focus:outline-none transition-colors"
              style={{ background: '#181818' }}
            >
              {ROLE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
        )}

        {/* Descrição / Instruções */}
        {!['start_event', 'end_event', 'exclusive_gateway', 'parallel_gateway', 'inclusive_gateway', 'swimlane'].includes(nodeType) && (
          <div>
            <label className="block text-[11px] text-white/50 mb-1.5 font-medium uppercase tracking-wide">
              Instruções
            </label>
            <textarea
              value={description}
              onChange={(e) => onUpdate(node.id, { description: e.target.value })}
              rows={4}
              className="w-full px-3 py-2 rounded-lg text-sm text-white bg-white/5 border border-white/10 focus:border-[#7030A0] focus:outline-none resize-none transition-colors placeholder:text-white/20"
              placeholder="Descreva o que deve ser feito nesta tarefa..."
            />
          </div>
        )}

        {/* ID info (readonly) */}
        <div>
          <label className="block text-[11px] text-white/30 mb-1 font-mono uppercase tracking-wide">
            ID interno
          </label>
          <p className="text-[11px] text-white/20 font-mono break-all">{node.id}</p>
        </div>
      </div>
    </div>
  );
}
