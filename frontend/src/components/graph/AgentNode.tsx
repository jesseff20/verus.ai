'use client';

import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { Search, Sparkles, ShieldCheck, RefreshCw, Flag, Loader2 } from 'lucide-react';
import { KBBadge } from './KBBadge';
import type { PipelineNode } from '@/hooks/use-intelligent-assistant';

const TYPE_CONFIG: Record<string, { icon: React.ReactNode; label: string }> = {
  analyze: { icon: <Search className="w-3.5 h-3.5" />, label: 'Analisar' },
  generate: { icon: <Sparkles className="w-3.5 h-3.5" />, label: 'Gerar' },
  validate: { icon: <ShieldCheck className="w-3.5 h-3.5" />, label: 'Validar' },
  refine: { icon: <RefreshCw className="w-3.5 h-3.5" />, label: 'Refinar' },
  finalize: { icon: <Flag className="w-3.5 h-3.5" />, label: 'Finalizar' },
};

const STATUS_STYLES: Record<string, string> = {
  pending: 'border-gray-300 bg-gray-50 text-gray-600',
  running: 'border-blue-400 bg-blue-50 text-blue-700 shadow-md shadow-blue-100',
  success: 'border-green-400 bg-green-50 text-green-700',
  error: 'border-red-400 bg-red-50 text-red-700',
  rejected: 'border-amber-400 bg-amber-50 text-amber-700',
};

function AgentNodeComponent({ data }: NodeProps) {
  const nodeData = data as unknown as PipelineNode;
  const { type, label, status, kbs, llm, duration_ms, score, section, section_name } = nodeData;
  const config = TYPE_CONFIG[type] || TYPE_CONFIG.generate;
  const statusStyle = STATUS_STYLES[status] || STATUS_STYLES.pending;
  const isRunning = status === 'running';

  return (
    <div className={`rounded-lg border-2 px-3 py-2 min-w-[200px] max-w-[260px] transition-all duration-300 ${statusStyle}`}>
      <Handle type="target" position={Position.Left} className="!bg-gray-400 !w-2 !h-2" />

      {/* Header */}
      <div className="flex items-center gap-1.5 mb-1">
        <span className="shrink-0">{isRunning ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : config.icon}</span>
        <span className="text-xs font-semibold truncate">{label}</span>
      </div>

      {/* Section info */}
      {section > 0 && (
        <div className="text-[10px] opacity-60 mb-1 truncate">
          Seção {section}: {section_name}
        </div>
      )}

      {/* KB Badges */}
      {kbs && kbs.length > 0 && (
        <div className="flex flex-wrap gap-0.5 mb-1">
          {kbs.map((kb, i) => (
            <KBBadge key={i} kb={kb.kb} purpose={kb.purpose} results={kb.results} />
          ))}
        </div>
      )}

      {/* LLM info */}
      {llm && (
        <div className="text-[10px] text-muted-foreground">
          {isRunning && <Loader2 className="w-2.5 h-2.5 inline animate-spin mr-0.5" />}
          {llm.model}
        </div>
      )}

      {/* Result info */}
      {(duration_ms !== undefined || score !== undefined) && (
        <div className="flex items-center gap-2 text-[10px] mt-1 opacity-70">
          {duration_ms !== undefined && <span>{(duration_ms / 1000).toFixed(1)}s</span>}
          {score !== undefined && <span>score: {score}</span>}
        </div>
      )}

      {/* Running pulse indicator */}
      {isRunning && (
        <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-blue-500 animate-ping" />
      )}

      <Handle type="source" position={Position.Right} className="!bg-gray-400 !w-2 !h-2" />
    </div>
  );
}

export const AgentNode = memo(AgentNodeComponent);
