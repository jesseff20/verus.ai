import React, { memo, useState } from 'react';
import { motion } from 'motion/react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { SectionFieldsForm } from '@/components/blueprint/SectionFieldsForm';
import { SubSectionPanel } from '@/components/blueprint/SubSectionPanel';
import type { SubSectionDecision } from '@/types';
import { SafeContent } from '@/components/ui/safe-content';
import { ScoreBadge } from '../shared/ScoreBadge';
import { EtpImportSelector } from '../EtpImportSelector';
import {
  Play,
  X,
  Loader2,
  AlertCircle,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  XCircle,
  CheckCircle2,
  Clock,
  Brain,
  Sparkles,
  Zap,
  ClipboardList,
  RefreshCw,
  MessageSquarePlus,
  Send,
} from 'lucide-react';
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';
import type { GenerationProgress } from '@/hooks/use-intelligent-assistant';

interface GenerationPhaseProps {
  sessionDetail: any;
  blueprintName: string;
  sectionNames: Record<number, string>;
  sectionFieldsMap: Record<number, any[]>;
  sectionFieldsValues: Record<number, Record<string, any>>;
  onSectionFieldsChange: (sectionNum: number, values: Record<string, any>) => void;
  selectedSections: Set<number>;
  totalSections: number;
  allSelected: boolean;
  onToggleSection: (num: number) => void;
  onToggleAll: (selectAll: boolean) => void;
  generationProgress: GenerationProgress;
  expandedSections: Set<number>;
  onToggleExpand: (num: number) => void;
  onGenerate: () => void;
  onCancel: () => void;
  onReset: () => void;
  onAdvance: () => void;
  isLoadingSections: boolean;
  onRegenerateSection?: (sectionNumber: number, feedback: string) => void;
  regeneratingSection?: number | null;
  subSectionsMap?: Record<number, any[]>;
  subSectionDecisions?: Record<string, SubSectionDecision>;
  onSubSectionDecisionChange?: (subKey: string, decision: SubSectionDecision | null) => void;
  onEtpImport?: (etpSessionId: string) => void;
  /** True while auto-extraction from uploaded docs is in progress */
  isExtractingFields?: boolean;
  /** Set of section numbers that were auto-filled from uploaded docs */
  autoFilledSections?: Set<number>;
}

const STATUS_CONFIG = {
  pending: {
    bg: 'bg-slate-50',
    border: 'border-slate-200',
    icon: Clock,
    iconClass: 'text-slate-400',
    label: 'Aguardando',
    labelClass: 'text-slate-400',
  },
  generating: {
    bg: 'bg-primary/5',
    border: 'border-primary/30',
    icon: Loader2,
    iconClass: 'text-primary animate-spin',
    label: 'Gerando...',
    labelClass: 'text-primary',
  },
  validating: {
    bg: 'bg-amber-500/5',
    border: 'border-amber-500/30',
    icon: Brain,
    iconClass: 'text-amber-500',
    label: 'Validando',
    labelClass: 'text-amber-600',
  },
  approved: {
    bg: 'bg-emerald-500/5',
    border: 'border-emerald-500/30',
    icon: CheckCircle2,
    iconClass: 'text-emerald-500',
    label: 'Aprovada',
    labelClass: 'text-emerald-600',
  },
  rejected: {
    bg: 'bg-red-500/5',
    border: 'border-red-500/30',
    icon: XCircle,
    iconClass: 'text-red-500',
    label: 'Reprovada',
    labelClass: 'text-red-600',
  },
} as const;

function GenerationPhaseComponent({
  sessionDetail,
  blueprintName,
  sectionNames,
  sectionFieldsMap,
  sectionFieldsValues,
  onSectionFieldsChange,
  selectedSections,
  totalSections,
  allSelected,
  onToggleSection,
  onToggleAll,
  generationProgress,
  expandedSections,
  onToggleExpand,
  onGenerate,
  onCancel,
  onReset,
  onAdvance,
  isLoadingSections,
  onRegenerateSection,
  regeneratingSection,
  subSectionsMap,
  subSectionDecisions,
  onSubSectionDecisionChange,
  onEtpImport,
  isExtractingFields,
  autoFilledSections,
}: GenerationPhaseProps) {
  const { isGenerating, result, error } = generationProgress;
  const showSelector = !isGenerating && !result && !error;
  const showProgress = isGenerating;
  const showResults = !isGenerating && !!result;
  const showError = error && !isGenerating && !result;

  // Estado local para controle de feedback por seção
  const [feedbackSections, setFeedbackSections] = useState<Record<number, string>>({});
  const [openFeedbackSections, setOpenFeedbackSections] = useState<Set<number>>(new Set());
  // Seções colapsadas pelo usuário (conteúdo visível por padrão)
  const [collapsedSections, setCollapsedSections] = useState<Set<number>>(new Set());
  // ETP Import para TR
  const [etpImportDone, setEtpImportDone] = useState(false);
  const [importedEtpSections, setImportedEtpSections] = useState<any[] | null>(null);
  const isTR = sessionDetail?.blueprint?.document_type_code === 'termo_referencia' ||
               sessionDetail?.document_type_code === 'termo_referencia';

  const toggleFeedback = (sectionNum: number) => {
    setOpenFeedbackSections((prev) => {
      const next = new Set(prev);
      if (next.has(sectionNum)) {
        next.delete(sectionNum);
      } else {
        next.add(sectionNum);
      }
      return next;
    });
  };

  const handleRegenerate = (sectionNum: number) => {
    const feedback = feedbackSections[sectionNum] || '';
    if (!feedback.trim()) return;
    onRegenerateSection?.(sectionNum, feedback);
    setOpenFeedbackSections((prev) => {
      const next = new Set(prev);
      next.delete(sectionNum);
      return next;
    });
    setFeedbackSections((prev) => ({ ...prev, [sectionNum]: '' }));
  };

  // Renderiza um card de seção (compartilhado entre showProgress e showResults)
  const renderSectionCard = (key: string, section: GenerationProgress['sections'][number], isResultMode: boolean) => {
    const sectionNum = parseInt(key);
    const sectionName = sectionNames[sectionNum] || `Seção ${sectionNum}`;
    const config = STATUS_CONFIG[section.status] || STATUS_CONFIG.pending;
    const StatusIcon = config.icon;
    const isRegenerating = regeneratingSection === sectionNum;
    const isFeedbackOpen = openFeedbackSections.has(sectionNum);

    return (
      <div
        key={key}
        className={cn(
          'rounded-2xl border overflow-hidden transition-all',
          isRegenerating ? 'border-primary/30 bg-primary/5' : config.border,
          isRegenerating ? '' : config.bg
        )}
      >
        <div
          className="p-4 flex items-center justify-between cursor-pointer hover:bg-white/50 transition-colors"
          onClick={() => section.content && setCollapsedSections((prev) => {
            const next = new Set(prev);
            if (next.has(sectionNum)) {
              next.delete(sectionNum);
            } else {
              next.add(sectionNum);
            }
            return next;
          })}
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center border">
              {isRegenerating ? (
                <Loader2 className="h-4 w-4 text-primary animate-spin" />
              ) : (
                <StatusIcon className={cn('h-4 w-4', config.iconClass)} />
              )}
            </div>
            <div>
              <p className="font-medium text-sm">
                {sectionNum}. {sectionName}
              </p>
              <p className={cn('text-xs', isRegenerating ? 'text-primary' : config.labelClass)}>
                {isRegenerating ? 'Regenerando...' : config.label}
                {section.score !== undefined && section.status !== 'pending' && !isRegenerating && (
                  <span className="ml-2 font-semibold">({section.score}%)</span>
                )}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {section.score !== undefined && section.status !== 'pending' && !isRegenerating && (
              <ScoreBadge score={section.score} />
            )}
            {section.content && (
              <button type="button" className="p-1 text-slate-400">
                {collapsedSections.has(sectionNum) ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
              </button>
            )}
          </div>
        </div>

        {/* Validation feedback */}
        {section.feedback && section.feedback.length > 0 && !isRegenerating && (
          <div className="px-4 py-2 bg-amber-500/5 border-t border-amber-500/20">
            <p className="text-xs font-medium text-amber-700 mb-1">
              <AlertCircle className="h-3 w-3 inline mr-1" />
              Observações da validação:
            </p>
            <ul className="text-xs text-slate-500 space-y-0.5">
              {section.feedback.map((fb, idx) => (
                <li key={idx} className="flex items-start gap-1">
                  <span className="text-amber-600">&bull;</span>
                  <span>{fb}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Content preview - always visible when content exists (collapsible via chevron) */}
        {section.content && (isResultMode || !collapsedSections.has(sectionNum)) && (
          <div className="px-4 pb-4 border-t border-slate-100">
            <div className="mt-3 p-3 bg-white rounded-xl">
              {section.status === 'generating' ? (
                /* During streaming: plain text — no markdown parsing overhead */
                <div className="prose prose-sm dark:prose-invert max-w-none break-words">
                  <p className="whitespace-pre-wrap">{section.content}</p>
                </div>
              ) : (
                /* After streaming: full markdown render */
                <SafeContent content={section.content} />
              )}
            </div>
          </div>
        )}

        {/* Regenerate button (only in result mode, not for structured sections) */}
        {isResultMode && section.content && !isRegenerating && !sectionFieldsMap[sectionNum]?.length && (
          <div className="px-4 py-3 border-t border-slate-100 bg-slate-50/50">
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                className="text-xs gap-1.5 text-slate-600 hover:text-primary"
                onClick={(e) => {
                  e.stopPropagation();
                  toggleFeedback(sectionNum);
                }}
              >
                <MessageSquarePlus size={14} />
                {isFeedbackOpen ? 'Fechar' : 'Regenerar com Orientações'}
              </Button>
            </div>

            {/* Feedback textarea */}
            {isFeedbackOpen && (
              <div className="mt-3 space-y-2" onClick={(e) => e.stopPropagation()}>
                <div className="relative">
                  <Textarea
                    placeholder="Descreva o que deseja melhorar nesta seção... Ex: 'Detalhar mais os requisitos técnicos' ou 'Adicionar referência à Lei 14.133/2021'"
                    value={feedbackSections[sectionNum] || ''}
                    onChange={(e) =>
                      setFeedbackSections((prev) => ({ ...prev, [sectionNum]: e.target.value }))
                    }
                    className="min-h-[80px] text-sm resize-none pr-32"
                  />
                  <div className="absolute top-1 right-1">
                    <AIEnhanceButton
                      value={feedbackSections[sectionNum] || ''}
                      onEnhance={(text) =>
                        setFeedbackSections((prev) => ({ ...prev, [sectionNum]: text }))
                      }
                      context="feedback para regeneração de seção de documento jurídico"
                    />
                  </div>
                </div>
                <div className="flex justify-end">
                  <Button
                    size="sm"
                    className="gap-1.5 rounded-lg"
                    disabled={!feedbackSections[sectionNum]?.trim()}
                    onClick={() => handleRegenerate(sectionNum)}
                  >
                    <RefreshCw size={14} />
                    Regenerar Seção
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <motion.div
      key="generation"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="space-y-8"
    >
      {/* Control panel */}
      <div className="bg-white rounded-2xl sm:rounded-3xl border border-slate-200 p-4 sm:p-6 shadow-sm sticky top-12 sm:top-16 z-40">
        <div className="flex flex-col sm:flex-row sm:flex-wrap sm:items-center justify-between gap-3 sm:gap-4">
          <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
            <div>
              <h2 className="text-base sm:text-lg font-bold text-slate-900">Painel de Geração</h2>
              <p className="text-xs sm:text-sm text-slate-500">
                Blueprint: <span className="font-semibold text-primary">{blueprintName}</span>
              </p>
            </div>
            <div className="h-8 w-px bg-slate-200 hidden sm:block" />
            {showSelector && (
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <Checkbox
                    checked={allSelected}
                    onCheckedChange={(checked) => onToggleAll(checked as boolean)}
                  />
                  <span className="text-sm font-medium text-slate-600">Todas</span>
                </div>
                <span className="text-xs font-bold text-slate-400 bg-slate-100 px-2 py-1 rounded-md">
                  {selectedSections.size}/{totalSections}
                </span>
              </div>
            )}
            {showResults && (
              <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200 self-start">
                <CheckCircle2 className="h-3 w-3 mr-1" />
                Concluída
              </Badge>
            )}
          </div>

          {/* Desktop buttons inline; Mobile: shown in fixed bottom bar */}
          <div className="hidden sm:flex items-center gap-3">
            {isGenerating ? (
              <Button
                onClick={onCancel}
                variant="destructive"
                className="rounded-xl gap-2"
              >
                <X size={18} />
                Parar Geração
              </Button>
            ) : !result ? (
              <Button
                onClick={onGenerate}
                disabled={!sessionDetail || selectedSections.size === 0}
                className="rounded-xl gap-2 shadow-lg shadow-primary/20"
              >
                <Zap size={18} />
                Gerar {allSelected ? 'Completo' : `${selectedSections.size} Seções`}
              </Button>
            ) : (
              <Button
                onClick={onReset}
                variant="ghost"
                className="rounded-xl gap-2 text-slate-500"
              >
                <RefreshCw size={16} />
                Nova Geração
              </Button>
            )}
            {(showResults || showProgress) && (
              <Button
                onClick={onAdvance}
                className="rounded-xl gap-2"
                disabled={isGenerating}
              >
                Avaliar Resultados
                <ChevronRight size={18} />
              </Button>
            )}
            {showSelector && (
              <Button
                onClick={onAdvance}
                variant="outline"
                className="rounded-xl gap-2"
              >
                Avaliar Resultados
                <ChevronRight size={18} />
              </Button>
            )}
          </div>
        </div>

        {/* Progress bar - always visible during generation */}
        {isGenerating && (
          <div className="mt-3 sm:mt-4 space-y-1.5 sm:space-y-2">
            <div className="flex justify-between text-xs font-bold text-slate-400 uppercase tracking-widest">
              <span className="truncate mr-2">{generationProgress.message}</span>
              <span className="shrink-0">{Math.round(generationProgress.percentage)}%</span>
            </div>
            <div className="h-2.5 sm:h-2 bg-slate-100 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-primary rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${generationProgress.percentage}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </div>
        )}

        {/* Results summary bar */}
        {showResults && result && (
          <div className="mt-3 sm:mt-4 flex flex-wrap items-center gap-2 sm:gap-4 text-xs sm:text-sm">
            <span className="text-slate-500">
              <span className="font-semibold text-slate-900">{result.validSections}</span>/{generationProgress.totalSections} válidas
            </span>
            <span className="text-slate-300 hidden sm:inline">|</span>
            <span className="text-slate-500">
              Score: <span className="font-semibold text-slate-900">{result.averageScore}%</span>
            </span>
            {result.generationTime && (
              <>
                <span className="text-slate-300 hidden sm:inline">|</span>
                <span className="text-slate-500">
                  <span className="font-semibold text-slate-900">{result.generationTime}s</span>
                </span>
              </>
            )}
          </div>
        )}
      </div>

      {/* Mobile: Fixed bottom action bar */}
      <div className="fixed bottom-0 left-0 right-0 sm:hidden z-40 bg-white/95 backdrop-blur-sm border-t border-slate-200 px-4 py-3 safe-area-bottom">
        <div className="flex items-center gap-2">
          {isGenerating ? (
            <Button
              onClick={onCancel}
              variant="destructive"
              className="flex-1 rounded-xl gap-2 text-[16px] py-3"
            >
              <X size={18} />
              Parar
            </Button>
          ) : !result ? (
            <Button
              onClick={onGenerate}
              disabled={!sessionDetail || selectedSections.size === 0}
              className="flex-1 rounded-xl gap-2 shadow-lg shadow-primary/20 text-[16px] py-3"
            >
              <Zap size={18} />
              Gerar {allSelected ? 'Completo' : `${selectedSections.size} Seções`}
            </Button>
          ) : (
            <Button
              onClick={onReset}
              variant="outline"
              className="rounded-xl gap-2 text-slate-500 py-3"
            >
              <RefreshCw size={16} />
            </Button>
          )}
          {(showResults || showProgress || showSelector) && (
            <Button
              onClick={onAdvance}
              className="flex-1 rounded-xl gap-2 text-[16px] py-3"
              disabled={isGenerating}
              variant={showSelector && !showResults && !showProgress ? 'outline' : 'default'}
            >
              Avaliar
              <ChevronRight size={18} />
            </Button>
          )}
        </div>
      </div>

      {/* Auto-fill extraction banner */}
      {isExtractingFields && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-2xl flex items-center gap-3">
          <Loader2 className="h-5 w-5 animate-spin text-blue-600 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-blue-800">
              Analisando documentos para pre-preenchimento...
            </p>
            <p className="text-xs text-blue-600 mt-0.5">
              Extraindo informações dos documentos enviados para preencher os campos automaticamente.
            </p>
          </div>
        </div>
      )}

      {/* Auto-fill success banner */}
      {!isExtractingFields && autoFilledSections && autoFilledSections.size > 0 && showSelector && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center gap-3">
          <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-emerald-800">
              Campos preenchidos automaticamente
            </p>
            <p className="text-xs text-emerald-600 mt-0.5">
              {autoFilledSections.size} secao(oes) com campos pre-preenchidos a partir dos documentos enviados. Revise e ajuste os valores antes de gerar.
            </p>
          </div>
        </div>
      )}

      {/* ETP Import for TR */}
      {showSelector && isTR && !etpImportDone && (
        <div className="mb-4">
          <EtpImportSelector
            trBlueprintId={sessionDetail?.blueprint_id || sessionDetail?.blueprint?.id || ''}
            onImportComplete={(sections, etpSessionId) => {
              setImportedEtpSections(sections);
              setEtpImportDone(true);
              onEtpImport?.(etpSessionId);
            }}
            onSkip={() => setEtpImportDone(true)}
          />
        </div>
      )}

      {/* Imported sections badge */}
      {showSelector && isTR && importedEtpSections && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-xl text-sm text-blue-700">
          <strong>{importedEtpSections.filter(s => s.has_content).length}</strong> seções pré-populadas do documento base.
          As seções importadas aparecerão com o conteúdo do documento base no documento final.
        </div>
      )}

      {/* Section selector (before generation) */}
      {showSelector && (!isTR || etpImportDone) && (
        <div className="bg-white rounded-2xl sm:rounded-3xl border border-slate-200 p-3 sm:p-6 shadow-sm pb-24 sm:pb-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-3">
            {isLoadingSections ? (
              <div className="col-span-full flex items-center justify-center py-8">
                <Loader2 className="h-5 w-5 animate-spin text-primary mr-2" />
                <span className="text-sm text-slate-400">Carregando seções...</span>
              </div>
            ) : Object.keys(sectionNames).length === 0 ? (
              <div className="col-span-full text-center py-8">
                <AlertCircle className="h-8 w-8 text-amber-500 mx-auto mb-2" />
                <p className="text-sm font-medium">Nenhuma seção encontrada</p>
              </div>
            ) : (
              Object.entries(sectionNames).map(([num, name]) => {
                const sectionNum = parseInt(num);
                const isSelected = selectedSections.has(sectionNum);
                const hasFields = sectionFieldsMap[sectionNum]?.length > 0;
                const hasSubSections = (subSectionsMap?.[sectionNum]?.length ?? 0) > 0;

                return (
                  <div
                    key={sectionNum}
                    className={(hasFields || hasSubSections) && isSelected ? 'col-span-full' : ''}
                  >
                    <div
                      className={cn(
                        'flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-all',
                        isSelected
                          ? 'bg-primary/5 border-primary/30'
                          : 'hover:bg-slate-50 border-transparent'
                      )}
                      onClick={() => onToggleSection(sectionNum)}
                    >
                      <Checkbox
                        checked={isSelected}
                        onCheckedChange={() => onToggleSection(sectionNum)}
                        className="mt-0.5"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium leading-tight">
                            {sectionNum}. {name}
                          </p>
                          {hasFields && (
                            <Badge
                              variant="outline"
                              className="text-[10px] px-1.5 py-0 h-5 bg-blue-50 text-blue-700 border-blue-200"
                            >
                              <ClipboardList className="h-3 w-3 mr-0.5" />
                              Formulário
                            </Badge>
                          )}
                          {hasFields && autoFilledSections?.has(sectionNum) && (
                            <Badge
                              variant="outline"
                              className="text-[10px] px-1.5 py-0 h-5 bg-emerald-50 text-emerald-700 border-emerald-200"
                            >
                              <CheckCircle2 className="h-3 w-3 mr-0.5" />
                              Pre-preenchido
                            </Badge>
                          )}
                          {hasSubSections && (
                            <Badge
                              variant="outline"
                              className="text-[10px] px-1.5 py-0 h-5 bg-purple-50 text-purple-700 border-purple-200"
                            >
                              <Sparkles className="h-3 w-3 mr-0.5" />
                              {subSectionsMap![sectionNum].length} sub-itens
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Structured fields */}
                    {hasFields && isSelected && !hasSubSections && (
                      <div className="ml-0 sm:ml-8 mt-2 p-3 sm:p-4 bg-blue-50/50 border border-blue-100 rounded-xl">
                        <p className="text-xs font-medium text-blue-700 mb-2">
                          Preencha os dados desta seção:
                        </p>
                        <SectionFieldsForm
                          fields={sectionFieldsMap[sectionNum]}
                          values={sectionFieldsValues[sectionNum] || {}}
                          onChange={(values) => onSectionFieldsChange(sectionNum, values)}
                          compact
                          showFillFromDocument
                          blueprintName={blueprintName}
                        />
                      </div>
                    )}

                    {/* Sub-sections panel */}
                    {hasSubSections && isSelected && onSubSectionDecisionChange && (
                      <div className="ml-0 sm:ml-8 mt-2 p-3 sm:p-4 bg-purple-50/30 border border-purple-100 rounded-xl">
                        <p className="text-xs font-medium text-purple-700 mb-2">
                          Configure cada sub-item (Gerando com IA, inserindo manulamente ou escolhendo a opção padrão):
                        </p>
                        <SubSectionPanel
                          subSections={subSectionsMap![sectionNum]}
                          decisions={subSectionDecisions || {}}
                          onDecisionChange={onSubSectionDecisionChange}
                        />
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>

          <div className="flex items-center gap-2 pt-4 mt-4 border-t border-slate-100">
            <Button variant="ghost" size="sm" onClick={() => onToggleAll(true)} className="text-xs">
              Selecionar todas
            </Button>
            <Button variant="ghost" size="sm" onClick={() => onToggleAll(false)} className="text-xs">
              Limpar seleção
            </Button>
            <div className="flex-1" />
            <span className="text-xs text-slate-400">
              ~{Math.ceil(selectedSections.size * 0.5)} min estimado
            </span>
          </div>
        </div>
      )}

      {/* Generation progress (during generation) */}
      {showProgress && (
        <div className="space-y-3 pb-20 sm:pb-0">
          {Object.entries(generationProgress.sections).map(([key, section]) =>
            renderSectionCard(key, section, false)
          )}
        </div>
      )}

      {/* Results (after generation completed) */}
      {showResults && (
        <div className="space-y-3 pb-20 sm:pb-0">
          {Object.entries(generationProgress.sections).map(([key, section]) =>
            renderSectionCard(key, section, true)
          )}
        </div>
      )}

      {/* Error state */}
      {showError && (
        <div className="p-6 bg-red-500/5 border border-red-500/20 rounded-3xl">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center">
              <XCircle className="h-5 w-5 text-red-500" />
            </div>
            <div>
              <p className="font-semibold text-red-600">Erro na geração</p>
              <p className="text-sm text-slate-500">{generationProgress.error}</p>
            </div>
          </div>
          <Button onClick={onReset} className="rounded-xl gap-2">
            <Sparkles className="h-4 w-4" />
            Tentar Novamente
          </Button>
        </div>
      )}
    </motion.div>
  );
}

export const GenerationPhase = memo(GenerationPhaseComponent);
