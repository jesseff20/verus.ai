'use client';

import { Badge } from '@/components/ui/badge';
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

export type SimTabStatus = 'idle' | 'running' | 'completed' | 'error';

export interface SimTab {
  index: number;
  label: string;
  status: SimTabStatus;
}

interface SimulationTabBarProps {
  tabs: SimTab[];
  activeIndex: number;
  onTabChange: (index: number) => void;
}

export default function SimulationTabBar({
  tabs,
  activeIndex,
  onTabChange,
}: SimulationTabBarProps) {
  if (tabs.length <= 1) return null;

  return (
    <div className="flex items-center gap-1 px-2 sm:px-6 py-2 bg-muted/30 border-b overflow-x-auto">
      <span className="text-xs text-muted-foreground mr-2 shrink-0">Simulacoes:</span>
      {tabs.map((tab) => {
        const isActive = tab.index === activeIndex;
        return (
          <button
            key={tab.index}
            onClick={() => onTabChange(tab.index)}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors shrink-0',
              isActive
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
            )}
          >
            {tab.status === 'running' && (
              <Loader2 className="h-3 w-3 animate-spin" />
            )}
            {tab.status === 'completed' && (
              <CheckCircle2 className="h-3 w-3 text-green-500" />
            )}
            {tab.status === 'error' && (
              <AlertCircle className="h-3 w-3 text-red-500" />
            )}
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
