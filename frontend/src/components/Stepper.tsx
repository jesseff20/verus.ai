'use client';

import { cn } from '@/lib/utils';
import type { Phase } from '@/types';
import { Check, Upload, FileCode, ThumbsUp, BarChart3, FileCheck, History } from 'lucide-react';

const PHASES: { key: Phase; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { key: 'upload', label: 'Upload', icon: Upload },
  { key: 'generation', label: 'Geração', icon: FileCode },
  { key: 'evaluation', label: 'Avaliação', icon: ThumbsUp },
  { key: 'analysis', label: 'Análise', icon: BarChart3 },
  { key: 'result', label: 'Resultado', icon: FileCheck },
  { key: 'history', label: 'Histórico', icon: History },
];

interface StepperProps {
  currentPhase: Phase;
  onPhaseChange: (phase: Phase) => void;
  disabled?: boolean;
  className?: string;
}

export function Stepper({ currentPhase, onPhaseChange, disabled, className }: StepperProps) {
  const currentIndex = PHASES.findIndex((p) => p.key === currentPhase);

  return (
    <nav className={cn('w-full bg-background border-b', className)}>
      <div className="max-w-[1600px] mx-auto px-6">
        <ol className="flex items-center justify-between py-3">
          {PHASES.map((phase, index) => {
            const isActive = phase.key === currentPhase;
            const isCompleted = index < currentIndex;
            const isClickable = !disabled && (isCompleted || index <= currentIndex + 1);
            const Icon = phase.icon;

            return (
              <li key={phase.key} className="flex items-center flex-1">
                <button
                  type="button"
                  disabled={!isClickable}
                  onClick={() => isClickable && onPhaseChange(phase.key)}
                  className={cn(
                    'flex items-center gap-2 text-sm transition-colors',
                    isActive && 'text-primary font-medium',
                    isCompleted && 'text-green-600 dark:text-green-400',
                    !isActive && !isCompleted && 'text-muted-foreground',
                    isClickable && 'cursor-pointer hover:text-primary',
                    !isClickable && 'cursor-not-allowed opacity-50'
                  )}
                >
                  <span
                    className={cn(
                      'flex items-center justify-center w-8 h-8 rounded-full border-2 text-xs font-semibold transition-colors',
                      isActive && 'border-primary bg-primary text-primary-foreground',
                      isCompleted && 'border-green-500 bg-green-50 dark:bg-green-950 text-green-600 dark:text-green-400',
                      !isActive && !isCompleted && 'border-muted-foreground/30 bg-muted/50'
                    )}
                  >
                    {isCompleted ? (
                      <Check className="h-4 w-4" />
                    ) : (
                      <Icon className="h-4 w-4" />
                    )}
                  </span>
                  <span className="hidden sm:inline">{phase.label}</span>
                </button>

                {index < PHASES.length - 1 && (
                  <div
                    className={cn(
                      'flex-1 h-px mx-3',
                      index < currentIndex
                        ? 'bg-green-500'
                        : 'bg-border'
                    )}
                  />
                )}
              </li>
            );
          })}
        </ol>
      </div>
    </nav>
  );
}
