'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';

export type GatewayData = {
  label: string;
  role: string;
  node_type: 'exclusive_gateway' | 'parallel_gateway' | 'inclusive_gateway';
};

const SIZE = 52;

function GatewayNode({ data, selected }: NodeProps) {
  const d = data as GatewayData;
  const isParallel = d.node_type === 'parallel_gateway';
  const isInclusive = d.node_type === 'inclusive_gateway';

  const borderColor = selected ? '#8B5CF6' : '#6D28D950';
  const bgColor = selected ? '#5B2EE022' : '#5B2EE010';

  return (
    <div
      style={{
        width: SIZE,
        height: SIZE,
        transform: 'rotate(45deg)',
        border: `2px solid ${borderColor}`,
        background: bgColor,
        boxShadow: selected ? `0 0 0 2px #8B5CF640` : 'none',
        position: 'relative',
        transition: 'all 0.15s',
      }}
    >
      {/* Inner symbol */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transform: 'rotate(-45deg)',
        }}
      >
        {isParallel ? (
          <span style={{ color: '#8B5CF6', fontSize: 18, fontWeight: 700, lineHeight: 1 }}>+</span>
        ) : isInclusive ? (
          <span style={{ color: '#8B5CF6', fontSize: 18, fontWeight: 700, lineHeight: 1 }}>○</span>
        ) : (
          <span style={{ color: '#8B5CF6', fontSize: 16, fontWeight: 700, lineHeight: 1 }}>×</span>
        )}
      </div>

      {/* Handles — rotated back to align with the diamond edges */}
      <Handle
        type="target"
        position={Position.Left}
        style={{
          background: '#8B5CF6',
          width: 8, height: 8, border: 'none',
          left: -4, top: '50%',
          transform: 'translateY(-50%) rotate(-45deg)',
        }}
      />
      <Handle
        type="source"
        id="yes"
        position={Position.Right}
        style={{
          background: '#8B5CF6',
          width: 8, height: 8, border: 'none',
          right: -4, top: '50%',
          transform: 'translateY(-50%) rotate(-45deg)',
        }}
      />
      <Handle
        type="source"
        id="no"
        position={Position.Bottom}
        style={{
          background: '#8B5CF6',
          width: 8, height: 8, border: 'none',
          bottom: -4, left: '50%',
          transform: 'translateX(-50%) rotate(-45deg)',
        }}
      />

      {/* Label below diamond */}
      <div
        style={{
          position: 'absolute',
          top: SIZE + 4,
          left: '50%',
          transform: 'translateX(-50%) rotate(-45deg)',
          whiteSpace: 'nowrap',
          fontSize: 10,
          color: '#9CA3AF',
          fontWeight: 500,
          pointerEvents: 'none',
          textAlign: 'center',
          maxWidth: 120,
          whiteSpace: 'normal',
        }}
      >
        {d.label}
      </div>
    </div>
  );
}

export default memo(GatewayNode);
