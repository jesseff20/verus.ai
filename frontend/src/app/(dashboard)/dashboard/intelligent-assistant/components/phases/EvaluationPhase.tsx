import React, { memo } from 'react';
import { motion } from 'motion/react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { SafeContent } from '@/components/ui/safe-content';
import { StarRating } from '../shared/StarRating';
import {
  Check,
  X,
  Loader2,
  PenLine,
  Save,
  CheckCircle2,
  ChevronRight,
  Brain,
  Cpu,
} from 'lucide-react';
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';
import type { SectionProgress } from '@/hooks/use-intelligent-assistant';
import type { ApprovalStatus } from '../../types';

interface EvaluationPhaseProps {
  generatedContent: Record<string, string>;
  sectionNames: Record<number, string>;
  sections: Record<number, SectionProgress>;
  sectionAgentInfo: Record<number, { generatorName?: string; validatorName?: string }>;
  sectionRatings: Record<number, number>;
  onRate: (sectionNum: number, rating: number) => void;
  editingSection: number | null;
  editedContent: Record<number, string>;
  onStartEdit: (sectionNum: number) => void;
  onCancelEdit: () => void;
  onSaveEdit: (sectionNum: number) => void;
  onEditChange: (sectionNum: number, content: string) => void;
  savingFeedback: Record<number, boolean>;
  evaluatedSections: Record<number, 'approved' | 'improved'>;
  onSaveFeedback: (sectionNum: number) => void;
  approvalStatus: Record<number, ApprovalStatus>;
  onSetApproval: (sectionNum: number, status: ApprovalStatus) => void;
  onAdvance: () => void;
  updatingDocument: boolean;
}

function EvaluationPhaseComponent({
  generatedContent,
  sectionNames,
  sections,
  sectionAgentInfo,
  sectionRatings,
  onRate,
  editingSection,
  editedContent,
  onStartEdit,
  onCancelEdit,
  onSaveEdit,
  onEditChange,
  savingFeedback,
  evaluatedSections,
  onSaveFeedback,
  approvalStatus,
  onSetApproval,
  onAdvance,
  updatingDocument,
}: EvaluationPhaseProps) {
  const sectionEntries = Object.entries(generatedContent);

  return (
    <motion.div
      key="evaluation"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="space-y-6"
    >
      {/* Top bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-3 sm:p-4 shadow-sm flex flex-col sm:flex-row sm:flex-wrap sm:items-center justify-between gap-3 sm:gap-4 sticky top-12 sm:top-16 z-30">
        <div className="flex items-center gap-3 sm:gap-4">
          <h2 className="text-base sm:text-lg font-bold text-slate-900">Avaliação</h2>
          <span className="text-xs bg-slate-100 px-2 sm:px-3 py-1 rounded-full text-slate-500 font-medium">
            {Object.values(approvalStatus).filter((s) => s !== 'pending').length}/{sectionEntries.length}
          </span>
        </div>
        {/* Desktop: inline buttons; Mobile: fixed bottom bar */}
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
            className="flex items-center gap-1.5 text-sm font-medium text-emerald-600 hover:bg-emerald-50 px-3 py-1.5 rounded-lg transition-all"
          >
            <Check size={14} />
            Aprovar todas
          </button>
          <Button onClick={onAdvance} disabled={updatingDocument} className="rounded-xl gap-2">
            {updatingDocument ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Salvando...
              </>
            ) : (
              <>
                Ir para Análise
                <ChevronRight size={16} />
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Section cards - layout Studio */}
      {sectionEntries.map(([key, content]) => {
        const num = parseInt(key.replace('section_', ''));
        const name = sectionNames[num] || `Seção ${num}`;
        const sectionData = sections[num];
        const agentInfo = sectionAgentInfo[num];
        const rating = sectionRatings[num] || 0;
        const isEditing = editingSection === num;
        const currentContent = editedContent[num] || content;
        const hasBeenEdited = editedContent[num] && editedContent[num] !== content;
        const status = approvalStatus[num] || 'pending';
        const score = sectionData?.score;
        const feedback = sectionData?.feedback;
        const sectionStatus = sectionData?.status;

        return (
          <div
            key={key}
            id={`eval-section-${num}`}
            className="bg-white rounded-2xl sm:rounded-3xl border border-slate-200 shadow-sm overflow-hidden scroll-mt-20"
          >
            {/* ── Header: número, nome, status, agente ── */}
            <div className="px-4 sm:px-6 py-4 sm:py-5 border-b border-slate-100">
              <div className="flex flex-col sm:flex-row sm:flex-wrap sm:items-start justify-between gap-3 sm:gap-4">
                <div className="flex items-start gap-3 sm:gap-4">
                  <div
                    className={cn(
                      'w-10 h-10 sm:w-12 sm:h-12 rounded-xl sm:rounded-2xl flex items-center justify-center font-black text-base sm:text-lg shrink-0',
                      status === 'approved'
                        ? 'bg-emerald-500/10 text-emerald-600'
                        : status === 'rejected'
                          ? 'bg-red-500/10 text-red-600'
                          : 'bg-slate-100 text-slate-500'
                    )}
                  >
                    {String(num).padStart(2, '0')}
                  </div>
                  <div className="min-w-0">
                    <h3 className="text-base sm:text-lg font-bold text-slate-900 break-words">{name}</h3>
                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                      {sectionStatus && (
                        <Badge
                          variant="outline"
                          className={cn(
                            'text-[10px]',
                            sectionStatus === 'approved'
                              ? 'text-emerald-600 border-emerald-300 bg-emerald-50'
                              : sectionStatus === 'rejected'
                                ? 'text-red-600 border-red-300 bg-red-50'
                                : 'text-slate-500'
                          )}
                        >
                          {sectionStatus === 'approved' ? 'Concluída' : sectionStatus === 'rejected' ? 'Reprovada' : 'Pendente'}
                        </Badge>
                      )}
                      {agentInfo?.generatorName && (
                        <span className="flex items-center gap-1 text-[11px] text-slate-400 hidden sm:flex">
                          <Cpu className="h-3 w-3" />
                          {agentInfo.generatorName}
                        </span>
                      )}
                      {hasBeenEdited && (
                        <Badge variant="outline" className="text-blue-600 text-[10px]">
                          <PenLine className="h-3 w-3 mr-1" />
                          Editado
                        </Badge>
                      )}
                      {evaluatedSections[num] && (
                        <Badge variant="outline" className="text-emerald-600 border-emerald-300 text-[10px]">
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                          {evaluatedSections[num] === 'approved' ? 'Aprovado' : 'Melhoria Enviada'}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>

                {/* Star rating + Approve / Reject - full-width on mobile */}
                <div className="flex items-center gap-2 sm:gap-3 w-full sm:w-auto">
                  <StarRating value={rating} onChange={(r) => onRate(num, r)} />
                  <div className="w-px h-6 bg-slate-200 hidden sm:block" />
                  <div className="flex-1 sm:flex-initial" />
                  <button
                    type="button"
                    onClick={() => onSetApproval(num, 'rejected')}
                    className={cn(
                      'flex items-center gap-1 sm:gap-1.5 px-2.5 sm:px-3 py-2 sm:py-1.5 rounded-xl text-xs font-bold transition-all active:scale-95 touch-manipulation',
                      status === 'rejected'
                        ? 'bg-red-500 text-white'
                        : 'text-red-500 hover:bg-red-50'
                    )}
                  >
                    <X size={14} />
                    <span className="hidden xs:inline">Rejeitar</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => onSetApproval(num, 'approved')}
                    className={cn(
                      'flex items-center gap-1 sm:gap-1.5 px-2.5 sm:px-3 py-2 sm:py-1.5 rounded-xl text-xs font-bold transition-all active:scale-95 touch-manipulation',
                      status === 'approved'
                        ? 'bg-emerald-500 text-white'
                        : 'text-emerald-500 hover:bg-emerald-50'
                    )}
                  >
                    <Check size={14} />
                    <span className="hidden xs:inline">Aprovar</span>
                  </button>
                </div>
              </div>
            </div>

            {/* ── Content: conteúdo gerado (completo, sem truncar) ── */}
            <div className="px-4 sm:px-6 py-4 sm:py-6">
              {isEditing ? (
                <div className="space-y-3">
                  <div className="relative">
                    <Textarea
                      value={editedContent[num] || ''}
                      onChange={(e) => onEditChange(num, e.target.value)}
                      className="min-h-[200px] max-h-[600px] resize-y font-mono text-sm sm:text-sm rounded-xl pr-12 sm:pr-32 text-[16px]"
                      style={{ fontSize: '16px' }}
                    />
                    <div className="absolute top-1 right-1">
                      <AIEnhanceButton
                        value={editedContent[num] || ''}
                        onEnhance={(text) => onEditChange(num, text)}
                        context="conteúdo de seção de documento jurídico"
                        objective="Melhore a qualidade jurídica, clareza e precisão do texto"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button variant="outline" size="sm" onClick={onCancelEdit} className="rounded-xl">
                      Cancelar
                    </Button>
                    <Button size="sm" onClick={() => onSaveEdit(num)} className="rounded-xl gap-1">
                      <Check className="h-4 w-4" />
                      Salvar Edição
                    </Button>
                  </div>
                </div>
              ) : (
                <SafeContent content={currentContent} />
              )}
            </div>

            {/* ── Score + Sugestões do Validador (SEMPRE visível) ── */}
            <div className="border-t border-slate-100 px-4 sm:px-6 py-4 sm:py-5">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 sm:gap-6">
                {/* Score IA - destaque visual grande */}
                <div className="md:col-span-1">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-3">
                    Score IA
                  </p>
                  {score !== undefined ? (
                    <div>
                      <div className="flex items-baseline gap-1">
                        <span
                          className={cn(
                            'text-4xl font-black',
                            score >= 80 ? 'text-emerald-500' : score >= 60 ? 'text-amber-500' : 'text-red-500'
                          )}
                        >
                          {Math.round(score)}
                        </span>
                        <span className="text-slate-400 font-bold text-sm">/ 100</span>
                      </div>
                      <div className="mt-2 h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className={cn(
                            'h-full rounded-full transition-all',
                            score >= 80 ? 'bg-emerald-500' : score >= 60 ? 'bg-amber-500' : 'bg-red-500'
                          )}
                          style={{ width: `${score}%` }}
                        />
                      </div>
                    </div>
                  ) : (
                    <p className="text-2xl font-black text-slate-300">--</p>
                  )}
                </div>

                {/* Sugestões do Validador */}
                <div className="md:col-span-3">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-3 flex items-center gap-2">
                    <Brain className="h-3.5 w-3.5" />
                    Sugestões do Validador
                    {agentInfo?.validatorName && (
                      <span className="normal-case tracking-normal font-medium text-slate-300">
                        ({agentInfo.validatorName})
                      </span>
                    )}
                  </p>
                  {feedback && feedback.length > 0 ? (
                    <ul className="space-y-2">
                      {feedback.map((fb, idx) => (
                        <li
                          key={idx}
                          className={cn(
                            'flex items-start gap-3 text-sm leading-relaxed p-3 rounded-xl',
                            score !== undefined && score < 60
                              ? 'bg-red-50/70 text-red-800'
                              : score !== undefined && score < 80
                                ? 'bg-amber-50/70 text-amber-800'
                                : 'bg-slate-50 text-slate-700'
                          )}
                        >
                          <span className="shrink-0 mt-0.5 text-slate-400">{idx + 1}.</span>
                          <span>{fb}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-slate-400 italic p-3 bg-slate-50 rounded-xl">
                      {sectionStatus === 'rejected'
                        ? 'Feedback do validador não disponível para esta seção.'
                        : 'Nenhuma sugestão - seção aprovada sem ressalvas.'}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* ── Actions: edit + enviar avaliação ── */}
            {!isEditing && (
              <div className="px-4 sm:px-6 py-3 sm:py-4 border-t border-slate-50 bg-slate-50/30 flex flex-wrap items-center justify-end gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onStartEdit(num)}
                  className="rounded-xl gap-1 active:scale-95 touch-manipulation"
                >
                  <PenLine className="h-4 w-4" />
                  <span className="hidden sm:inline">Editar</span>
                </Button>
                <Button
                  size="sm"
                  variant={evaluatedSections[num] ? 'outline' : 'default'}
                  onClick={() => onSaveFeedback(num)}
                  disabled={savingFeedback[num] || !rating}
                  className="rounded-xl gap-1 active:scale-95 touch-manipulation"
                >
                  {savingFeedback[num] ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : evaluatedSections[num] ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : (
                    <Save className="h-4 w-4" />
                  )}
                  <span className="hidden sm:inline">
                    {evaluatedSections[num] ? 'Avaliação Enviada' : 'Enviar Avaliação'}
                  </span>
                  <span className="sm:hidden">
                    {evaluatedSections[num] ? 'Enviada' : 'Enviar'}
                  </span>
                </Button>
              </div>
            )}
          </div>
        );
      })}

      {/* Spacer for mobile fixed bottom bar */}
      <div className="h-20 sm:hidden" />

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
            className="flex items-center gap-1.5 text-sm font-medium text-emerald-600 px-3 py-3 rounded-xl active:bg-emerald-50 touch-manipulation"
          >
            <Check size={16} />
            Todas
          </button>
          <Button
            onClick={onAdvance}
            disabled={updatingDocument}
            className="flex-1 rounded-xl gap-2 text-[16px] py-3"
          >
            {updatingDocument ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Salvando...
              </>
            ) : (
              <>
                Ir para Análise
                <ChevronRight size={16} />
              </>
            )}
          </Button>
        </div>
      </div>
    </motion.div>
  );
}

export const EvaluationPhase = memo(EvaluationPhaseComponent);
