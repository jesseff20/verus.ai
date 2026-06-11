import React, { memo, useRef, useEffect } from 'react';
import {
  Upload,
  Play,
  CheckCircle2,
  LayoutDashboard,
  FileText,
  History,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Phase, PhaseConfig } from '../types';

const PHASES: PhaseConfig[] = [
  { id: 'upload', label: 'Upload', icon: Upload },
  { id: 'generation', label: 'Geração', icon: Play },
  { id: 'evaluation', label: 'Avaliação', icon: CheckCircle2 },
  { id: 'analysis', label: 'Análise', icon: LayoutDashboard },
  { id: 'result', label: 'Resultado', icon: FileText },
  { id: 'history', label: 'Histórico', icon: History },
];

interface StepperProps {
  currentPhase: Phase;
  onPhaseChange: (phase: Phase) => void;
  disabled?: boolean;
}

function StepperComponent({ currentPhase, onPhaseChange, disabled }: StepperProps) {
  const currentIdx = PHASES.findIndex((p) => p.id === currentPhase);
  const scrollRef = useRef<HTMLDivElement>(null);
  const activeRef = useRef<HTMLButtonElement>(null);

  // Auto-scroll to center the active step on mobile
  useEffect(() => {
    if (activeRef.current && scrollRef.current) {
      const container = scrollRef.current;
      const el = activeRef.current;
      const scrollLeft = el.offsetLeft - container.offsetWidth / 2 + el.offsetWidth / 2;
      container.scrollTo({ left: scrollLeft, behavior: 'smooth' });
    }
  }, [currentPhase]);

  return (
    <div className="w-full bg-white border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-[1600px] mx-auto px-3 sm:px-6">
        <div
          ref={scrollRef}
          className="flex items-center h-12 sm:h-14 overflow-x-auto scrollbar-hide snap-x snap-mandatory scroll-smooth -mx-3 px-3 sm:mx-0 sm:px-0"
        >
          <nav className="flex-1 flex items-center gap-0.5 sm:gap-1 min-w-max">
            {PHASES.map((phase, idx) => {
              const Icon = phase.icon;
              const isActive = currentPhase === phase.id;
              const isPast = currentIdx > idx;

              return (
                <React.Fragment key={phase.id}>
                  <button
                    ref={isActive ? activeRef : undefined}
                    type="button"
                    onClick={() => !disabled && onPhaseChange(phase.id)}
                    disabled={disabled}
                    className={cn(
                      'flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-2 rounded-full transition-all text-sm font-medium snap-center shrink-0',
                      'active:scale-95 touch-manipulation',
                      isActive
                        ? 'bg-primary text-primary-foreground shadow-md'
                        : isPast
                          ? 'text-primary hover:bg-slate-100'
                          : 'text-slate-400 hover:bg-slate-50',
                      disabled && 'cursor-not-allowed opacity-50'
                    )}
                  >
                    <Icon size={16} />
                    <span className="hidden xs:inline sm:inline text-xs sm:text-sm">{phase.label}</span>
                  </button>
                  {idx < PHASES.length - 1 && (
                    <ChevronRight size={14} className="text-slate-300 mx-0.5 sm:mx-1 hidden sm:block" />
                  )}
                </React.Fragment>
              );
            })}
          </nav>
        </div>
      </div>
    </div>
  );
}

export const Stepper = memo(StepperComponent);
