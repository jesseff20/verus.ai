'use client';

import { useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { AgentNode } from './AgentNode';
import type { PipelineNode, PipelineEdge } from '@/hooks/use-intelligent-assistant';

interface PipelineGraphProps {
  nodes: PipelineNode[];
  edges: PipelineEdge[];
  activeNode: string | null;
}

const nodeTypes = {
  agentNode: AgentNode,
};

const STATUS_MINIMAP_COLORS: Record<string, string> = {
  pending: '#d1d5db',
  running: '#3b82f6',
  success: '#22c55e',
  error: '#ef4444',
  rejected: '#f59e0b',
};

export function PipelineGraph({ nodes, edges, activeNode }: PipelineGraphProps) {
  // Converter PipelineNode → React Flow Node
  const flowNodes: Node[] = useMemo(() =>
    nodes.map(n => ({
      id: n.id,
      type: 'agentNode',
      position: n.position,
      data: { ...n },
    })),
    [nodes]
  );

  // Converter PipelineEdge → React Flow Edge
  const flowEdges: Edge[] = useMemo(() =>
    edges.map(e => ({
      id: e.id,
      source: e.source,
      target: e.target,
      animated: e.animated,
      type: 'smoothstep',
      style: {
        stroke: e.animated ? '#3b82f6' : '#94a3b8',
        strokeWidth: e.animated ? 2 : 1,
      },
    })),
    [edges]
  );

  if (nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
        Aguardando estrutura do pipeline...
      </div>
    );
  }

  return (
    <ReactFlow
      nodes={flowNodes}
      edges={flowEdges}
      nodeTypes={nodeTypes}
      fitView
      fitViewOptions={{ padding: 0.3 }}
      minZoom={0.3}
      maxZoom={1.5}
      proOptions={{ hideAttribution: true }}
      nodesDraggable={false}
      nodesConnectable={false}
      elementsSelectable={false}
    >
      <Background gap={16} size={1} color="#f1f5f9" />
      <Controls showInteractive={false} position="bottom-left" />
      <MiniMap
        nodeColor={(node) => {
          const data = node.data as unknown as PipelineNode;
          return STATUS_MINIMAP_COLORS[data?.status] || '#d1d5db';
        }}
        maskColor="rgba(0,0,0,0.08)"
        position="bottom-right"
      />
    </ReactFlow>
  );
}
