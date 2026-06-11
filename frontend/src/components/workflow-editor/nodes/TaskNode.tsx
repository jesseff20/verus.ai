'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { User, Cog, FileText } from 'lucide-react';

const ROLE_COLOR: Record<string, string> = {
  distribuidor: '#7030A0',
  procurador: '#5B2EE0',
  gerente: '#8B5CF6',
  assessor_gerencial: '#6D28D9',
  assessor_gabinete: '#7C3AED',
  procurador_geral: '#4C1D95',
  subprocurador_geral: '#4C1D95',
  any: '#374151',
};

export type TaskData = {
  label: string;
  role: string;
  node_type: 'task' | 'user_task' | 'service_task';
  description?: string;
};

function TaskNode({ data, selected }: NodeProps) {
  const d = data as TaskData;
  const color = ROLE_COLOR[d.role] ?? ROLE_COLOR.any;
  const Icon = d.node_type === 'service_task' ? Cog : d.node_type === 'user_task' ? User : FileText;

  return (
    <div
      className="rounded-lg border transition-all"
      style={{
        width: 160,
        minHeight: 60,
        borderColor: selected ? color : `${color}50`,
        background: selected ? `${color}18` : `${color}0C`,
        boxShadow: selected ? `0 0 0 2px ${color}60` : 'none',
      }}
    >
      <Handle
        type="target"
        position={Position.Left}
        style={{ background: color, width: 8, height: 8, border: 'none' }}
      />

      <div className="p-2.5 flex items-start gap-2">
        <div
          className="shrink-0 w-5 h-5 rounded flex items-center justify-center mt-0.5"
          style={{ background: `${color}25` }}
        >
          <Icon size={11} style={{ color }} />
        </div>
        <span
          className="text-[11px] font-medium leading-tight"
          style={{ color: '#E5E7EB' }}
        >
          {d.label}
        </span>
      </div>

      <Handle
        type="source"
        position={Position.Right}
        style={{ background: color, width: 8, height: 8, border: 'none' }}
      />
    </div>
  );
}

export default memo(TaskNode);
