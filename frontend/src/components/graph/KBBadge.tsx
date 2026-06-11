'use client';

import { Database } from 'lucide-react';

interface KBBadgeProps {
  kb: string;
  purpose: string;
  results: number;
}

const PURPOSE_COLORS: Record<string, string> = {
  examples: 'bg-purple-100 text-purple-700 border-purple-200',
  evaluation: 'bg-amber-100 text-amber-700 border-amber-200',
  normative: 'bg-blue-100 text-blue-700 border-blue-200',
  context: 'bg-green-100 text-green-700 border-green-200',
  reference: 'bg-gray-100 text-gray-700 border-gray-200',
};

export function KBBadge({ kb, purpose, results }: KBBadgeProps) {
  const colorClass = PURPOSE_COLORS[purpose] || PURPOSE_COLORS.reference;

  return (
    <div className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium border ${colorClass}`}>
      <Database className="w-2.5 h-2.5" />
      <span className="truncate max-w-[120px]">{kb}</span>
      <span className="opacity-60">{results}</span>
    </div>
  );
}
