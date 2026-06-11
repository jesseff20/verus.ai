'use client';

import { Play, Square, Circle, User, Cog, FileText, Diamond, AlignLeft } from 'lucide-react';

type PaletteItem = {
  type: string;
  nodeType: string;
  label: string;
  icon: React.ElementType;
  color: string;
};

const PALETTE_ITEMS: PaletteItem[] = [
  { type: 'event', nodeType: 'start_event', label: 'Início', icon: Play, color: '#22C55E' },
  { type: 'event', nodeType: 'end_event', label: 'Fim', icon: Square, color: '#EF4444' },
  { type: 'event', nodeType: 'intermediate_event', label: 'Evento Interm.', icon: Circle, color: '#F59E0B' },
  { type: 'task', nodeType: 'user_task', label: 'Tarefa Usuário', icon: User, color: '#7030A0' },
  { type: 'task', nodeType: 'service_task', label: 'Tarefa Serviço', icon: Cog, color: '#5B2EE0' },
  { type: 'task', nodeType: 'task', label: 'Tarefa Genérica', icon: FileText, color: '#6D28D9' },
  { type: 'gateway', nodeType: 'exclusive_gateway', label: 'Gateway XOR', icon: Diamond, color: '#8B5CF6' },
  { type: 'gateway', nodeType: 'parallel_gateway', label: 'Gateway AND', icon: Diamond, color: '#7C3AED' },
  { type: 'swimlane', nodeType: 'swimlane', label: 'Swim Lane', icon: AlignLeft, color: '#4B5563' },
];

export default function NodePalette() {
  const onDragStart = (event: React.DragEvent, item: PaletteItem) => {
    event.dataTransfer.setData(
      'application/verus-node',
      JSON.stringify({ nodeType: item.nodeType, label: item.label })
    );
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div
      className="absolute left-0 top-0 bottom-0 z-10 flex flex-col border-r overflow-y-auto"
      style={{ width: 180, background: '#0F0F0F', borderColor: '#1F1F1F' }}
    >
      <div className="px-3 pt-3 pb-2">
        <p className="text-[10px] text-white/30 font-mono uppercase tracking-widest">Elementos</p>
      </div>

      {/* Groups */}
      {[
        { group: 'Eventos', types: ['event'] },
        { group: 'Tarefas', types: ['task'] },
        { group: 'Gateways', types: ['gateway'] },
        { group: 'Estrutura', types: ['swimlane'] },
      ].map(({ group, types }) => (
        <div key={group} className="mb-1">
          <p className="px-3 py-1.5 text-[10px] text-white/20 font-medium uppercase tracking-widest">
            {group}
          </p>
          {PALETTE_ITEMS.filter((i) => types.includes(i.type)).map((item) => (
            <div
              key={item.nodeType}
              draggable
              onDragStart={(e) => onDragStart(e, item)}
              className="mx-2 mb-1 px-2.5 py-2 rounded-lg border flex items-center gap-2 cursor-grab active:cursor-grabbing select-none hover:bg-white/5 transition-all"
              style={{ borderColor: `${item.color}30`, background: `${item.color}08` }}
            >
              <item.icon size={13} style={{ color: item.color, flexShrink: 0 }} />
              <span className="text-[11px] text-white/65 font-medium">{item.label}</span>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
