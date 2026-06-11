'use client';

import { useEffect, useRef } from 'react';
import { Database, Cpu, Play, CheckCircle, XCircle, ArrowRight } from 'lucide-react';
import type { PipelineLogEntry } from '@/hooks/use-intelligent-assistant';

interface GraphLogProps {
  log: PipelineLogEntry[];
}

const LOG_ICONS: Record<string, React.ReactNode> = {
  node_enter: <Play className="w-3 h-3 text-blue-500" />,
  kb_query: <Database className="w-3 h-3 text-purple-500" />,
  llm_call: <Cpu className="w-3 h-3 text-amber-500" />,
  node_exit: <CheckCircle className="w-3 h-3 text-green-500" />,
  edge_traverse: <ArrowRight className="w-3 h-3 text-gray-400" />,
};

export function GraphLog({ log }: GraphLogProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [log.length]);

  if (log.length === 0) {
    return (
      <div className="text-xs text-muted-foreground text-center py-3">
        Aguardando eventos do pipeline...
      </div>
    );
  }

  return (
    <div ref={scrollRef} className="overflow-y-auto max-h-[180px] space-y-0.5 font-mono text-[11px]">
      {log.map((entry, i) => {
        const icon = entry.type === 'node_exit' && entry.message.startsWith('Erro')
          ? <XCircle className="w-3 h-3 text-red-500" />
          : LOG_ICONS[entry.type] || null;

        return (
          <div key={i} className="flex items-start gap-1.5 px-2 py-0.5 hover:bg-muted/50 rounded">
            <span className="text-muted-foreground shrink-0">{entry.timestamp}</span>
            <span className="shrink-0 mt-0.5">{icon}</span>
            <span className="text-foreground">{entry.message}</span>
          </div>
        );
      })}
    </div>
  );
}
