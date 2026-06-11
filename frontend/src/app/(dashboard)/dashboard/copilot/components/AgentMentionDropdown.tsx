'use client';

import { useEffect, useRef } from 'react';
import { Bot } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface AgentMentionOption {
  id: string;
  name: string;
  agent_type: string;
  description?: string;
  color?: string;
  icon?: string;
}

interface AgentMentionDropdownProps {
  agents: AgentMentionOption[];
  query: string;
  selectedIndex: number;
  onSelect: (agent: AgentMentionOption) => void;
  onClose: () => void;
  anchorRef: React.RefObject<HTMLElement | null>;
}

export function AgentMentionDropdown({
  agents,
  query,
  selectedIndex,
  onSelect,
  onClose,
  anchorRef,
}: AgentMentionDropdownProps) {
  const dropdownRef = useRef<HTMLDivElement>(null);

  const filtered = agents.filter((a) =>
    a.name.toLowerCase().includes(query.toLowerCase()) ||
    a.agent_type.toLowerCase().includes(query.toLowerCase())
  );

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node) &&
        anchorRef.current &&
        !anchorRef.current.contains(e.target as Node)
      ) {
        onClose();
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose, anchorRef]);

  if (filtered.length === 0) return null;

  return (
    <div
      ref={dropdownRef}
      className="absolute bottom-full mb-1 left-0 z-50 w-72 rounded-lg border bg-popover shadow-lg overflow-hidden"
    >
      <div className="px-2 py-1.5 text-xs font-medium text-muted-foreground border-b">
        Agentes especializados
      </div>
      <ul className="max-h-52 overflow-y-auto py-1">
        {filtered.map((agent, idx) => (
          <li key={agent.id}>
            <button
              type="button"
              className={cn(
                'flex w-full items-center gap-2.5 px-3 py-2 text-left text-sm transition-colors',
                idx === selectedIndex
                  ? 'bg-accent text-accent-foreground'
                  : 'hover:bg-accent hover:text-accent-foreground'
              )}
              onMouseDown={(e) => {
                e.preventDefault(); // prevent textarea blur
                onSelect(agent);
              }}
            >
              <span
                className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-white text-xs"
                style={{ backgroundColor: agent.color || '#003366' }}
              >
                <Bot className="h-3 w-3" />
              </span>
              <span className="flex flex-col min-w-0">
                <span className="font-medium truncate">{agent.name}</span>
                {agent.description && (
                  <span className="text-xs text-muted-foreground truncate">
                    {agent.description}
                  </span>
                )}
              </span>
            </button>
          </li>
        ))}
      </ul>
      <div className="px-3 py-1 text-[10px] text-muted-foreground border-t">
        ↑↓ navegar · Enter selecionar · Esc fechar
      </div>
    </div>
  );
}
