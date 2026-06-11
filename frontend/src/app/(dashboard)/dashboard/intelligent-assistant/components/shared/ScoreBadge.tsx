import React, { memo } from 'react';
import { cn } from '@/lib/utils';

interface ScoreBadgeProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

function ScoreBadgeComponent({ score, size = 'sm', showLabel = false, className }: ScoreBadgeProps) {
  const colorClass =
    score >= 80
      ? 'bg-emerald-500 text-white'
      : score >= 60
        ? 'bg-amber-500 text-white'
        : 'bg-red-500 text-white';

  const sizeClass = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-6 py-4 text-4xl',
  }[size];

  return (
    <span className={cn('font-black rounded-xl inline-flex items-center gap-1', colorClass, sizeClass, className)}>
      {showLabel && <span className="text-[10px] font-bold uppercase tracking-widest opacity-80">Score IA</span>}
      {score}
      {size !== 'lg' && '%'}
    </span>
  );
}

export const ScoreBadge = memo(ScoreBadgeComponent);
