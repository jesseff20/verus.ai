'use client';

import { memo } from 'react';
import { NodeProps, NodeResizer } from '@xyflow/react';

const ROLE_COLORS: Record<string, string> = {
  distribuidor: '#7030A0',
  procurador: '#5B2EE0',
  gerente: '#8B5CF6',
  assessor_gerencial: '#6D28D9',
  assessor_gabinete: '#7C3AED',
  procurador_geral: '#4C1D95',
  subprocurador_geral: '#4C1D95',
  any: '#374151',
};

const ROLE_LABELS: Record<string, string> = {
  distribuidor: 'Distribuidor(a)',
  procurador: 'Procurador(a)',
  gerente: 'Gerente',
  assessor_gerencial: 'Assessor(a) Gerencial',
  assessor_gabinete: 'Assessor(a) de Gabinete',
  procurador_geral: 'Procurador(a)-Geral',
  subprocurador_geral: 'Subprocurador(a)-Geral',
  any: 'Qualquer papel',
};

export type SwimLaneData = {
  label: string;
  role: string;
  laneIndex?: number;
};

function SwimLaneNode({ data, selected }: NodeProps) {
  const d = data as SwimLaneData;
  const color = ROLE_COLORS[d.role] ?? ROLE_COLORS.any;

  return (
    <>
      <NodeResizer
        minWidth={400}
        minHeight={120}
        isVisible={selected}
        lineStyle={{ borderColor: color, borderWidth: 1 }}
        handleStyle={{ width: 8, height: 8, background: color }}
      />
      <div
        className="w-full h-full rounded-lg border flex items-stretch overflow-hidden"
        style={{
          borderColor: `${color}40`,
          background: `${color}08`,
          minWidth: 400,
          minHeight: 120,
        }}
      >
        {/* Vertical label strip */}
        <div
          className="flex items-center justify-center shrink-0"
          style={{
            width: 32,
            background: `${color}22`,
            borderRight: `1px solid ${color}30`,
          }}
        >
          <span
            className="text-[10px] font-semibold tracking-widest uppercase select-none"
            style={{
              writingMode: 'vertical-rl',
              transform: 'rotate(180deg)',
              color,
              opacity: 0.85,
            }}
          >
            {d.label}
          </span>
        </div>
        {/* Lane content area (children nodes float inside via parentId) */}
        <div className="flex-1" />
      </div>
    </>
  );
}

export default memo(SwimLaneNode);
