'use client';

import { PipelineGraph } from './PipelineGraph';
import { GraphLog } from './GraphLog';
import type { GraphVisualization } from '@/hooks/use-intelligent-assistant';

interface PipelinePanelProps {
  graphVisualization: GraphVisualization;
}

export function PipelinePanel({ graphVisualization }: PipelinePanelProps) {
  const { nodes, edges, log, activeNode } = graphVisualization;

  return (
    <div className="flex flex-col h-full border rounded-lg overflow-hidden bg-background">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b bg-muted/30">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${activeNode ? 'bg-blue-500 animate-pulse' : 'bg-gray-300'}`} />
          <span className="text-sm font-medium">Pipeline de Geração</span>
        </div>
        <span className="text-xs text-muted-foreground">
          {nodes.filter(n => n.status === 'success').length}/{nodes.length} nós
        </span>
      </div>

      {/* Graph */}
      <div className="flex-1 min-h-[250px]">
        <PipelineGraph nodes={nodes} edges={edges} activeNode={activeNode} />
      </div>

      {/* Log */}
      <div className="border-t">
        <div className="px-3 py-1.5 border-b bg-muted/20">
          <span className="text-xs font-medium text-muted-foreground">Log</span>
        </div>
        <GraphLog log={log} />
      </div>
    </div>
  );
}
