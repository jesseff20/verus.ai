import React, { memo, useMemo, useState } from 'react';
import { motion } from 'motion/react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { ScoreBadge } from '../shared/ScoreBadge';
import {
  Check,
  X,
  Edit3,
  RefreshCw,
  ChevronRight,
} from 'lucide-react';
import type { SectionProgress } from '@/hooks/use-intelligent-assistant';
import type { ApprovalStatus } from '../../types';

type FilterTab = 'all' | 'approved' | 'pending' | 'rejected';

interface AnalysisPhaseProps {
  generatedContent: Record<string, string>;
  sectionNames: Record<number, string>;
  sections: Record<number, SectionProgress>;
  generationMetadata: any;
  totalSections: number;
  approvalStatus: Record<number, ApprovalStatus>;
  onSetApproval: (sectionNum: number, status: ApprovalStatus) => void;
  onAdvance: () => void;
}

function AnalysisPhaseComponent({
  generatedContent,
  sectionNames,
  sections,
  generationMetadata,
  totalSections,
  approvalStatus,
  onSetApproval,
  onAdvance,
}: AnalysisPhaseProps) {
  const [filter, setFilter] = useState<FilterTab>('all');

  const sectionEntries = Object.entries(generatedContent);

  const stats = useMemo(() => {
    const approved = sectionEntries.filter(
      ([key]) => approvalStatus[parseInt(key.replace('section_', ''))] === 'approved'
    ).length;
    const rejected = sectionEntries.filter(
      ([key]) => approvalStatus[parseInt(key.replace('section_', ''))] === 'rejected'
    ).length;
    const pending = sectionEntries.length - approved - rejected;

    return { approved, rejected, pending };
  }, [sectionEntries, approvalStatus]);

  const filteredEntries = useMemo(() => {
    if (filter === 'all') return sectionEntries;
    return sectionEntries.filter(([key]) => {
      const num = parseInt(key.replace('section_', ''));
      const status = approvalStatus[num] || 'pending';
      return status === filter;
    });
  }, [sectionEntries, filter, approvalStatus]);

  const avgScore = generationMetadata?.average_score || 0;

  return (
    <motion.div
      key="analysis"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="space-y-4 sm:space-y-8 pb-20 sm:pb-0"
    >
      {/* Dashboard cards */}
      <div className="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6">
        <div className="bg-white p-4 sm:p-6 rounded-2xl sm:rounded-[2rem] border border-slate-200 shadow-sm">
          <p className="text-[10px] sm:text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Score</p>
          <div className="flex items-end gap-1 sm:gap-2">
            <span className="text-2xl sm:text-4xl font-black text-primary">{avgScore}</span>
            <span className="text-slate-400 font-bold mb-0.5 sm:mb-1 text-xs sm:text-base">/ 100</span>
          </div>
          <div className="mt-2 sm:mt-4 h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div className="h-full bg-primary rounded-full" style={{ width: `${avgScore}%` }} />
          </div>
        </div>

        <div className="bg-white p-4 sm:p-6 rounded-2xl sm:rounded-[2rem] border border-slate-200 shadow-sm">
          <p className="text-[10px] sm:text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Status</p>
          <div className="flex items-center gap-2 sm:gap-4">
            <div className="text-center">
              <p className="text-xl sm:text-2xl font-black text-emerald-500">{stats.approved}</p>
              <p className="text-[9px] sm:text-[10px] font-bold text-slate-400">OK</p>
            </div>
            <div className="w-px h-6 sm:h-8 bg-slate-100" />
            <div className="text-center">
              <p className="text-xl sm:text-2xl font-black text-amber-500">{stats.pending}</p>
              <p className="text-[9px] sm:text-[10px] font-bold text-slate-400">PEND</p>
            </div>
            <div className="w-px h-6 sm:h-8 bg-slate-100" />
            <div className="text-center">
              <p className="text-xl sm:text-2xl font-black text-red-500">{stats.rejected}</p>
              <p className="text-[9px] sm:text-[10px] font-bold text-slate-400">REJ</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-4 sm:p-6 rounded-2xl sm:rounded-[2rem] border border-slate-200 shadow-sm">
          <p className="text-[10px] sm:text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Tokens</p>
          <div className="flex items-end gap-1">
            <span className="text-xl sm:text-2xl font-black text-slate-800">
              {generationMetadata?.total_tokens_used
                ? `${(generationMetadata.total_tokens_used / 1000).toFixed(1)}k`
                : '--'}
            </span>
          </div>
        </div>

        <div className="bg-white p-4 sm:p-6 rounded-2xl sm:rounded-[2rem] border border-slate-200 shadow-sm">
          <p className="text-[10px] sm:text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Tempo</p>
          <div className="flex items-end gap-1">
            <span className="text-xl sm:text-2xl font-black text-slate-800">
              {generationMetadata?.generation_time
                ? `${Math.floor(generationMetadata.generation_time / 60)}:${String(
                    Math.round(generationMetadata.generation_time % 60)
                  ).padStart(2, '0')}`
                : '--'}
            </span>
            <span className="text-slate-400 text-[10px] sm:text-xs font-bold mb-0.5 sm:mb-1">MIN</span>
          </div>
        </div>
      </div>

      {/* Filters & Actions */}
      <div className="flex flex-col sm:flex-row sm:flex-wrap sm:items-center justify-between gap-3 sm:gap-4">
        <div className="flex items-center gap-0.5 sm:gap-1 bg-white border border-slate-200 rounded-xl p-1 overflow-x-auto scrollbar-hide">
          {[
            { id: 'all' as FilterTab, label: 'Todas' },
            { id: 'approved' as FilterTab, label: 'Aprovadas' },
            { id: 'pending' as FilterTab, label: 'Pendentes' },
            { id: 'rejected' as FilterTab, label: 'Rejeitadas' },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setFilter(tab.id)}
              className={cn(
                'px-3 sm:px-4 py-2 text-xs font-bold rounded-lg transition-all shrink-0 active:scale-95 touch-manipulation',
                filter === tab.id ? 'bg-primary text-white' : 'text-slate-500 hover:bg-slate-50'
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>
        {/* Desktop: inline actions; Mobile: fixed bottom bar */}
        <div className="hidden sm:flex items-center gap-3">
          <button
            type="button"
            onClick={() => {
              sectionEntries.forEach(([key]) => {
                const num = parseInt(key.replace('section_', ''));
                if ((approvalStatus[num] || 'pending') === 'pending') {
                  onSetApproval(num, 'approved');
                }
              });
            }}
            className="flex items-center gap-2 text-sm font-bold text-emerald-500 hover:bg-emerald-500/5 px-4 py-2 rounded-xl transition-all"
          >
            <Check size={16} />
            Aprovar todas pendentes
          </button>
          <Button onClick={onAdvance} className="rounded-xl gap-2">
            Ver Resultado
            <ChevronRight size={16} />
          </Button>
        </div>
      </div>

      {/* Compact card grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-6">
        {filteredEntries.map(([key]) => {
          const num = parseInt(key.replace('section_', ''));
          const name = sectionNames[num] || `Seção ${num}`;
          const sectionData = sections[num];
          const status = approvalStatus[num] || 'pending';

          return (
            <div
              key={key}
              className="bg-white rounded-2xl sm:rounded-3xl border border-slate-200 p-4 sm:p-5 shadow-sm hover:shadow-md transition-all active:shadow-md"
            >
              <div className="flex items-start justify-between mb-3 sm:mb-4">
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <div
                    className={cn(
                      'w-9 h-9 sm:w-10 sm:h-10 rounded-xl flex items-center justify-center font-black text-base sm:text-lg shrink-0',
                      status === 'approved'
                        ? 'bg-emerald-500/10 text-emerald-500'
                        : status === 'rejected'
                          ? 'bg-red-500/10 text-red-500'
                          : 'bg-slate-100 text-slate-400'
                    )}
                  >
                    {num}
                  </div>
                  <div className="min-w-0">
                    <h4 className="font-bold text-slate-800 text-sm truncate">{name}</h4>
                  </div>
                </div>
                <div
                  className={cn(
                    'text-lg font-black shrink-0',
                    (sectionData?.score || 0) >= 80
                      ? 'text-emerald-500'
                      : (sectionData?.score || 0) >= 60
                        ? 'text-amber-500'
                        : 'text-red-500'
                  )}
                >
                  {sectionData?.score || '--'}
                </div>
              </div>

              <p className="text-xs text-slate-500 line-clamp-2 mb-3 sm:mb-5 italic">
                {sectionData?.feedback?.[0] || 'Nenhuma sugestão pendente.'}
              </p>

              <div className="flex items-center justify-between pt-3 sm:pt-4 border-t border-slate-50">
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => onSetApproval(num, 'approved')}
                    className={cn(
                      'p-2.5 sm:p-2 rounded-lg transition-all active:scale-95 touch-manipulation',
                      status === 'approved'
                        ? 'text-emerald-500 bg-emerald-500/10'
                        : 'text-slate-400 hover:text-emerald-500 hover:bg-emerald-500/5'
                    )}
                  >
                    <Check size={16} className="sm:w-3.5 sm:h-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => onSetApproval(num, 'rejected')}
                    className={cn(
                      'p-2.5 sm:p-2 rounded-lg transition-all active:scale-95 touch-manipulation',
                      status === 'rejected'
                        ? 'text-red-500 bg-red-500/10'
                        : 'text-slate-400 hover:text-red-500 hover:bg-red-500/5'
                    )}
                  >
                    <X size={16} className="sm:w-3.5 sm:h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Mobile: Fixed bottom action bar */}
      <div className="fixed bottom-0 left-0 right-0 sm:hidden z-40 bg-white/95 backdrop-blur-sm border-t border-slate-200 px-4 py-3 safe-area-bottom">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => {
              sectionEntries.forEach(([key]) => {
                const num = parseInt(key.replace('section_', ''));
                if ((approvalStatus[num] || 'pending') === 'pending') {
                  onSetApproval(num, 'approved');
                }
              });
            }}
            className="flex items-center gap-1.5 text-sm font-bold text-emerald-500 px-3 py-3 rounded-xl active:bg-emerald-50 touch-manipulation"
          >
            <Check size={16} />
            Todas
          </button>
          <Button onClick={onAdvance} className="flex-1 rounded-xl gap-2 text-[16px] py-3">
            Ver Resultado
            <ChevronRight size={16} />
          </Button>
        </div>
      </div>
    </motion.div>
  );
}

export const AnalysisPhase = memo(AnalysisPhaseComponent);
