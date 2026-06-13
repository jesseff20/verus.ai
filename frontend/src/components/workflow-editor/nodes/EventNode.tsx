'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { Play, Square, Circle } from 'lucide-react';
import { useTheme } from 'next-themes';

export type EventData = {
  label: string;
  role: string;
  node_type: 'start_event' | 'end_event' | 'intermediate_event';
};

const SIZE = 40;

function EventNode({ data, selected }: NodeProps) {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === 'dark';
  const d = data as EventData;
  const isStart = d.node_type === 'start_event';
  const isEnd = d.node_type === 'end_event';

  const borderColor = isStart ? '#22C55E' : isEnd ? '#EF4444' : '#F59E0B';
  const bgColor = isStart ? '#22C55E12' : isEnd ? '#EF444412' : '#F59E0B12';
  const activeColor = selected ? borderColor : `${borderColor}60`;

  return (
    <div
      style={{
        width: SIZE,
        height: SIZE,
        borderRadius: '50%',
        border: `${isEnd ? 3 : 2}px solid ${activeColor}`,
        background: bgColor,
        boxShadow: selected ? `0 0 0 2px ${borderColor}40` : 'none',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        transition: 'all 0.15s',
      }}
    >
      {isStart ? (
        <Play size={14} fill={borderColor} color={borderColor} />
      ) : isEnd ? (
        <Square size={12} fill={borderColor} color={borderColor} />
      ) : (
        <Circle size={12} color={borderColor} />
      )}

      {/* Label below */}
      <div
        style={{
          position: 'absolute',
          top: SIZE + 4,
          left: '50%',
          transform: 'translateX(-50%)',
          whiteSpace: 'nowrap',
          fontSize: 10,
          color: isDark ? '#9CA3AF' : '#374151',
          fontWeight: 500,
          pointerEvents: 'none',
          textAlign: 'center',
          maxWidth: 100,
        }}
      >
        {d.label}
      </div>

      {!isStart && (
        <Handle
          type="target"
          position={Position.Left}
          style={{
            background: borderColor,
            width: 8, height: 8, border: 'none',
          }}
        />
      )}
      {!isEnd && (
        <Handle
          type="source"
          position={Position.Right}
          style={{
            background: borderColor,
            width: 8, height: 8, border: 'none',
          }}
        />
      )}
    </div>
  );
}

export default memo(EventNode);
