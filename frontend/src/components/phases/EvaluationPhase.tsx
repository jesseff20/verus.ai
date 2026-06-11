'use client';

import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Star,
  Edit3,
  Check,
  X,
  Save,
  ThumbsUp,
  ThumbsDown,
  Loader2,
  AlertTriangle,
  FileText,
} from 'lucide-react';
import type { ApprovalStatus } from '@/types';
import { useState, useMemo, useCallback } from 'react';

interface SectionData {
  section_number: number;
  section_name: string;
  content?: string;
  score?: number;
  status: string;
  feedback?: string[];
}

interface EvaluationPhaseProps {
  generatedContent: Record<string, string>;
  sectionNames: Record<number, string>;
  sections: Record<string, SectionData>;
  sectionAgentInfo: Record<number, { generatorName?: string; validatorName?: string }>;
  sectionRatings: Record<number, number>;
  onRate: (num: number, rating: number) => void;
  editingSection: number | null;
  editedContent: Record<number, string>;
  onStartEdit: (num: number) => void;
  onCancelEdit: () => void;
  onSaveEdit: (num: number) => void;
  onEditChange: (num: number, content: string) => void;
  savingFeedback: Record<number, boolean>;
  evaluatedSections: Record<number, 'approved' | 'improved'>;
  onSaveFeedback: (num: number) => Promise<void>;
  approvalStatus: Record<number, ApprovalStatus>;
  onSetApproval: (num: number, status: ApprovalStatus) => void;
  onAdvance: () => Promise<void>;
  updatingDocument: boolean;
  className?: string;
}

export function EvaluationPhase({
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
  className,
}: EvaluationPhaseProps) {
  // Parse content into section entries
  const sectionEntries = useMemo(() => {
    return Object.entries(generatedContent)
      .filter(([key]) => key.startsWith('section_'))
      .map(([key, content]) => {
        const num = parseInt(key.replace('section_', ''), 10);
        return { num, key, name: sectionNames[num] || `Seção ${num}`, content };
      })
      .sort((a, b) => a.num - b.num);
  }, [generatedContent, sectionNames]);

  const allEvaluated = useMemo(
    () => sectionEntries.length > 0 && sectionEntries.every((e) => evaluatedSections[e.num]),
    [sectionEntries, evaluatedSections]
  );

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <ThumbsUp className="h-5 w-5 text-primary" />
          Avaliação de Seções
        </h2>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">
            {Object.keys(evaluatedSections).length}/{sectionEntries.length} avaliadas
          </span>
          <Button
            onClick={onAdvance}
            disabled={!allEvaluated || updatingDocument}
            className="gap-2"
            size="sm"
          >
            {updatingDocument ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Check className="h-4 w-4" />
            )}
            Avançar
          </Button>
        </div>
      </div>

      <ScrollArea className="h-[calc(100vh-280px)]">
        <div className="space-y-4">
          {sectionEntries.map(({ num, key, name, content }) => {
            const sectionData = sections[num];
            const sectionKey = `section_${String(num).padStart(2, '0')}`;
            const isEditing = editingSection === num;
            const isSaving = savingFeedback[num];
            const isEvaluated = !!evaluatedSections[num];
            const rating = sectionRatings[num] || 0;
            const agentInfo = sectionAgentInfo[num];

            return (
              <Card key={num} className={cn(isEvaluated && 'border-green-200 dark:border-green-800')}>
                <CardContent className="p-4 space-y-3">
                  {/* Header */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 min-w-0">
                      <FileText className="h-4 w-4 text-primary shrink-0" />
                      <h3 className="text-sm font-medium truncate">
                        {num}. {name}
                      </h3>
                      <Badge variant="outline" className="text-[10px]">
                        Score: {sectionData?.score ?? 'N/A'}
                      </Badge>
                      {isEvaluated && (
                        <Badge variant="success" className="text-[10px]">
                          {evaluatedSections[num] === 'approved' ? 'Aprovada' : 'Melhorada'}
                        </Badge>
                      )}
                    </div>

                    <div className="flex items-center gap-1 shrink-0">
                      {/* Star Rating */}
                      {[1, 2, 3, 4, 5].map((star) => (
                        <button
                          key={star}
                          onClick={() => onRate(num, star === rating ? 0 : star)}
                          className={cn(
                            'p-0.5 transition-colors',
                            star <= rating ? 'text-yellow-500' : 'text-muted-foreground/30 hover:text-yellow-500/50'
                          )}
                        >
                          <Star className="h-4 w-4 fill-current" />
                        </button>
                      ))}

                      {/* Edit / Save */}
                      {!isEditing ? (
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7"
                          onClick={() => onStartEdit(num)}
                        >
                          <Edit3 className="h-3.5 w-3.5" />
                        </Button>
                      ) : (
                        <>
                          <Button
                            size="icon"
                            variant="ghost"
                            className="h-7 w-7 text-green-600"
                            onClick={() => onSaveEdit(num)}
                          >
                            <Check className="h-3.5 w-3.5" />
                          </Button>
                          <Button
                            size="icon"
                            variant="ghost"
                            className="h-7 w-7"
                            onClick={onCancelEdit}
                          >
                            <X className="h-3.5 w-3.5" />
                          </Button>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Agent Info */}
                  {agentInfo && (
                    <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
                      {agentInfo.generatorName && (
                        <span>Gerador: {agentInfo.generatorName}</span>
                      )}
                      {agentInfo.validatorName && (
                        <span>Validador: {agentInfo.validatorName}</span>
                      )}
                    </div>
                  )}

                  {/* Content Area */}
                  <div className="relative">
                    {isEditing ? (
                      <textarea
                        value={editedContent[num] || content}
                        onChange={(e) => onEditChange(num, e.target.value)}
                        className="w-full min-h-[150px] rounded-md border border-input bg-background p-3 text-sm font-mono resize-y focus:outline-none focus:ring-2 focus:ring-ring"
                      />
                    ) : (
                      <div className="prose prose-sm max-w-none dark:prose-invert text-sm text-muted-foreground whitespace-pre-wrap line-clamp-6">
                        {content || 'Sem conteúdo gerado.'}
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center justify-between pt-1">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => onSetApproval(num, 'approved')}
                        className={cn(
                          'flex items-center gap-1 px-2.5 py-1.5 rounded text-xs font-medium border transition-colors',
                          approvalStatus[num] === 'approved'
                            ? 'bg-green-50 border-green-200 text-green-700 dark:bg-green-950 dark:border-green-800 dark:text-green-400'
                            : 'border-border text-muted-foreground hover:bg-muted'
                        )}
                      >
                        <ThumbsUp className="h-3 w-3" />
                        Aprovar
                      </button>
                      <button
                        onClick={() => onSetApproval(num, 'improved')}
                        className={cn(
                          'flex items-center gap-1 px-2.5 py-1.5 rounded text-xs font-medium border transition-colors',
                          approvalStatus[num] === 'improved'
                            ? 'bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-950 dark:border-blue-800 dark:text-blue-400'
                            : 'border-border text-muted-foreground hover:bg-muted'
                        )}
                      >
                        <Edit3 className="h-3 w-3" />
                        Precisa Melhorar
                      </button>
                    </div>

                    <Button
                      size="sm"
                      className="h-8 text-xs gap-1"
                      onClick={() => onSaveFeedback(num)}
                      disabled={isSaving || rating === 0}
                    >
                      {isSaving ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      ) : (
                        <Save className="h-3 w-3" />
                      )}
                      Salvar Avaliação
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}

          {sectionEntries.length === 0 && (
            <div className="text-center py-12">
              <AlertTriangle className="h-10 w-10 mx-auto mb-3 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                Nenhuma seção gerada para avaliar.
              </p>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
