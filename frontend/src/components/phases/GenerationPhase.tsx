'use client';

import { useState, useCallback, useMemo } from 'react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Zap,
  Loader2,
  Check,
  X,
  AlertTriangle,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  FileText,
} from 'lucide-react';

interface GenerationSectionData {
  section_number: number;
  section_name: string;
  content?: string;
  score?: number;
  status: 'pending' | 'generating' | 'completed' | 'rejected';
  feedback?: string[];
  tokens_used?: number;
}

interface GenerationProgress {
  status: 'idle' | 'generating' | 'completed' | 'error' | 'cancelled';
  sections: Record<string, GenerationSectionData>;
  cancelled: boolean;
  result: any;
  error?: string;
}

interface BlueprintField {
  id: string;
  field_name: string;
  field_label: string;
  field_type: 'text' | 'textarea' | 'select' | 'multi_select' | 'date' | 'currency' | 'cpf' | 'cnpj' | 'oab' | 'processo';
  field_options?: string[];
  required: boolean;
  placeholder?: string;
  order: number;
}

interface SubSection {
  id: string;
  name: string;
  description?: string;
  optional: boolean;
  order: number;
}

interface GenerationPhaseProps {
  sessionDetail: any;
  blueprintName: string;
  sectionNames: Record<number, string>;
  sectionFieldsMap: Record<number, BlueprintField[]>;
  sectionFieldsValues: Record<number, Record<string, any>>;
  onSectionFieldsChange: (sectionNumber: number, values: Record<string, any>) => void;
  subSectionsMap: Record<number, SubSection[]>;
  subSectionDecisions: Record<number, Record<string, boolean>>;
  onSubSectionDecisionChange: (sectionNumber: number, subSectionId: string, value: boolean) => void;
  selectedSections: Set<number>;
  totalSections: number;
  allSelected: boolean;
  onToggleSection: (num: number) => void;
  onToggleAll: (selectAll: boolean) => void;
  generationProgress: GenerationProgress;
  expandedSections: Set<number>;
  onToggleExpand: (num: number) => void;
  onGenerate: () => Promise<void>;
  onCancel: () => void;
  onReset: () => void;
  onAdvance: () => void;
  isLoadingSections: boolean;
  onRegenerateSection: (sectionNumber: number, feedback?: string) => void;
  regeneratingSection: number | null;
  onEtpImport?: ((blueprintId: string) => Promise<void>) | undefined;
  className?: string;
}

export function GenerationPhase({
  sessionDetail,
  blueprintName,
  sectionNames,
  sectionFieldsMap,
  sectionFieldsValues,
  onSectionFieldsChange,
  subSectionsMap,
  subSectionDecisions,
  onSubSectionDecisionChange,
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
  onEtpImport,
  className,
}: GenerationPhaseProps) {
  const isGenerating = generationProgress.status === 'generating';
  const isCompleted = generationProgress.status === 'completed';
  const isIdle = generationProgress.status === 'idle';
  const hasResult = Object.keys(generationProgress.sections).length > 0;

  const sectionArray = useMemo(() => {
    const arr: { num: number; name: string }[] = [];
    for (let i = 1; i <= totalSections; i++) {
      if (sectionNames[i]) {
        arr.push({ num: i, name: sectionNames[i] });
      }
    }
    return arr;
  }, [totalSections, sectionNames]);

  // Calculate generation progress percentage
  const generationPercent = useMemo(() => {
    if (isIdle) return 0;
    const completed = Object.values(generationProgress.sections).filter(
      (s) => s.status === 'completed'
    ).length;
    const total = Object.keys(generationProgress.sections).length || 1;
    return Math.round((completed / total) * 100);
  }, [generationProgress, isIdle]);

  const getScoreColor = (score?: number) => {
    if (!score) return 'text-muted-foreground';
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className={cn('space-y-6', className)}>
      {/* Section Selection */}
      {isIdle && !hasResult && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium">Seções para Gerar</h3>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">
                  {selectedSections.size}/{totalSections}
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs"
                  onClick={() => onToggleAll(!allSelected)}
                >
                  {allSelected ? 'Desmarcar Todas' : 'Selecionar Todas'}
                </Button>
              </div>
            </div>

            {isLoadingSections ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <div className="space-y-1">
                {sectionArray.map(({ num, name }) => {
                  const isSelected = selectedSections.has(num);
                  const fields = sectionFieldsMap[num] || [];
                  const subs = subSectionsMap[num] || [];

                  return (
                    <div key={num}>
                      <button
                        onClick={() => onToggleSection(num)}
                        className={cn(
                          'w-full flex items-center gap-3 p-2.5 rounded-md border text-left transition-colors',
                          isSelected
                            ? 'border-primary/50 bg-primary/5'
                            : 'border-transparent hover:bg-muted'
                        )}
                      >
                        <div
                          className={cn(
                            'w-5 h-5 rounded border-2 flex items-center justify-center shrink-0 transition-colors',
                            isSelected
                              ? 'border-primary bg-primary text-primary-foreground'
                              : 'border-muted-foreground/30'
                          )}
                        >
                          {isSelected && <Check className="h-3 w-3" />}
                        </div>
                        <span className="text-sm font-medium truncate flex-1">
                          {num}. {name}
                        </span>
                        {fields.length > 0 && (
                          <Badge variant="outline" className="text-[10px]">
                            {fields.length} campos
                          </Badge>
                        )}
                        {subs.length > 0 && (
                          <Badge variant="outline" className="text-[10px]">
                            {subs.filter((s) => !s.optional).length}/{subs.length} sub
                          </Badge>
                        )}
                      </button>

                      {/* Expanded section fields */}
                      {isSelected && expandedSections.has(num) && (
                        <div className="ml-8 mt-2 space-y-3 p-3 bg-muted/30 rounded-lg">
                          {fields.map((field) => (
                            <FieldInput
                              key={field.id}
                              field={field}
                              value={sectionFieldsValues[num]?.[field.field_name] || ''}
                              onChange={(val) =>
                                onSectionFieldsChange(num, {
                                  ...(sectionFieldsValues[num] || {}),
                                  [field.field_name]: val,
                                })
                              }
                            />
                          ))}

                          {subs.map((sub) => (
                            <div key={sub.id} className="flex items-center justify-between p-2 bg-background rounded border">
                              <div>
                                <p className="text-sm font-medium">{sub.name}</p>
                                {sub.description && (
                                  <p className="text-xs text-muted-foreground">{sub.description}</p>
                                )}
                              </div>
                              <button
                                onClick={() =>
                                  onSubSectionDecisionChange(
                                    num,
                                    sub.id,
                                    !subSectionDecisions[num]?.[sub.id]
                                  )
                                }
                                className={cn(
                                  'px-3 py-1 rounded text-xs font-medium border transition-colors',
                                  subSectionDecisions[num]?.[sub.id] !== false
                                    ? 'bg-green-50 border-green-200 text-green-700 dark:bg-green-950 dark:border-green-800 dark:text-green-400'
                                    : 'bg-muted/50 border-border text-muted-foreground'
                                )}
                              >
                                {subSectionDecisions[num]?.[sub.id] !== false ? 'Incluir' : 'Excluir'}
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {/* Generate button */}
            {selectedSections.size > 0 && (
              <div className="mt-4">
                <Button onClick={onGenerate} className="w-full gap-2" size="lg">
                  <Zap className="h-5 w-5" />
                  Gerar Documento ({selectedSections.size} seções)
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Generation Progress */}
      {isGenerating && (
        <Card>
          <CardContent className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium">Gerando Documento...</h3>
              <Button
                variant="outline"
                size="sm"
                className="h-8 text-xs"
                onClick={onCancel}
              >
                <X className="h-3 w-3 mr-1" />
                Cancelar
              </Button>
            </div>
            <Progress value={generationPercent} className="h-2" />
            <p className="text-xs text-muted-foreground">
              {generationPercent}% concluído — {
                Object.values(generationProgress.sections).filter(s => s.status === 'completed').length
              }/{Object.keys(generationProgress.sections).length} seções
            </p>

            <ScrollArea className="h-[200px]">
              <div className="space-y-2">
                {Object.entries(generationProgress.sections).map(([key, section]) => (
                  <div
                    key={key}
                    className={cn(
                      'flex items-center justify-between p-2 rounded border text-xs',
                      section.status === 'completed' && 'border-green-200 bg-green-50 dark:bg-green-950 dark:border-green-800',
                      section.status === 'generating' && 'border-blue-200 bg-blue-50 dark:bg-blue-950 dark:border-blue-800',
                      section.status === 'rejected' && 'border-red-200 bg-red-50 dark:bg-red-950 dark:border-red-800'
                    )}
                  >
                    <span className="font-medium truncate">
                      {section.section_number}. {section.section_name}
                    </span>
                    <div className="flex items-center gap-2 shrink-0">
                      {section.status === 'generating' && (
                        <Loader2 className="h-3 w-3 animate-spin text-blue-600" />
                      )}
                      {section.status === 'completed' && (
                        <span className={cn('text-xs font-medium', getScoreColor(section.score))}>
                          {section.score}%
                        </span>
                      )}
                      {section.status === 'rejected' && (
                        <AlertTriangle className="h-3 w-3 text-red-600" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}

      {/* Error State */}
      {generationProgress.status === 'error' && (
        <Card>
          <CardContent className="p-6 text-center">
            <AlertTriangle className="h-10 w-10 mx-auto mb-3 text-destructive" />
            <h3 className="text-lg font-medium mb-1">Erro na Geração</h3>
            <p className="text-sm text-muted-foreground mb-4">
              {generationProgress.error || 'Ocorreu um erro ao gerar o documento.'}
            </p>
            <Button onClick={onReset} variant="outline" className="gap-2">
              <RefreshCw className="h-4 w-4" />
              Tentar Novamente
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Completed */}
      {isCompleted && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Check className="h-5 w-5 text-green-600" />
                <h3 className="text-sm font-medium">Geração Concluída</h3>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="h-8 text-xs"
                  onClick={onReset}
                >
                  <RefreshCw className="h-3 w-3 mr-1" />
                  Regenerar
                </Button>
                <Button size="sm" className="h-8 text-xs" onClick={onAdvance}>
                  Avaliar Seções
                </Button>
              </div>
            </div>

            {/* Summary */}
            {generationProgress.result && (
              <div className="grid grid-cols-3 gap-3 mb-3">
                <div className="p-2 rounded bg-muted/50 text-center">
                  <div className="text-lg font-bold">
                    {generationProgress.result.validSections}/{totalSections}
                  </div>
                  <div className="text-xs text-muted-foreground">Seções Válidas</div>
                </div>
                <div className="p-2 rounded bg-muted/50 text-center">
                  <div className="text-lg font-bold">{generationProgress.result.averageScore}%</div>
                  <div className="text-xs text-muted-foreground">Score Médio</div>
                </div>
                <div className="p-2 rounded bg-muted/50 text-center">
                  <div className="text-lg font-bold">
                    {generationProgress.result.totalTokensUsed.toLocaleString()}
                  </div>
                  <div className="text-xs text-muted-foreground">Tokens</div>
                </div>
              </div>
            )}

            {/* Section Results */}
            <ScrollArea className="h-[250px]">
              <div className="space-y-1">
                {Object.entries(generationProgress.sections).map(([key, section]) => (
                  <div
                    key={key}
                    className="flex items-center justify-between p-2 rounded border text-xs"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                      <span className="truncate">
                        {section.section_number}. {section.section_name}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className={cn('font-medium', getScoreColor(section.score))}>
                        {section.score !== undefined ? `${section.score}%` : 'N/A'}
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={() => onToggleExpand(section.section_number)}
                      >
                        {expandedSections.has(section.section_number) ? (
                          <ChevronDown className="h-3 w-3" />
                        ) : (
                          <ChevronRight className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}

      {/* Error on generation progress */}
      {generationProgress.status === 'error' && (
        <div className="text-center py-8">
          <AlertTriangle className="h-12 w-12 mx-auto mb-3 text-destructive" />
          <h3 className="text-lg font-semibold mb-2">Erro na Geração</h3>
          <p className="text-sm text-muted-foreground mb-4">
            {generationProgress.error || 'Ocorreu um erro inesperado durante a geração.'}
          </p>
          <Button variant="outline" onClick={onReset}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Tentar Novamente
          </Button>
        </div>
      )}
    </div>
  );
}

// Internal FieldInput component
function FieldInput({
  field,
  value,
  onChange,
}: {
  field: BlueprintField;
  value: any;
  onChange: (val: any) => void;
}) {
  const label = field.field_label || field.field_name;

  switch (field.field_type) {
    case 'textarea':
      return (
        <div className="space-y-1">
          <Label className="text-xs">
            {label}
            {field.required && <span className="text-destructive ml-1">*</span>}
          </Label>
          <textarea
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={field.placeholder}
            className="w-full min-h-[60px] rounded-md border border-input bg-background px-3 py-2 text-xs resize-none focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
      );

    case 'select':
      return (
        <div className="space-y-1">
          <Label className="text-xs">
            {label}
            {field.required && <span className="text-destructive ml-1">*</span>}
          </Label>
          <Select value={value || ''} onValueChange={onChange}>
            <SelectTrigger className="h-8 text-xs">
              <SelectValue placeholder={field.placeholder || `Selecione ${label.toLowerCase()}`} />
            </SelectTrigger>
            <SelectContent>
              {field.field_options?.map((opt) => (
                <SelectItem key={opt} value={opt} className="text-xs">
                  {opt}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      );

    case 'date':
      return (
        <div className="space-y-1">
          <Label className="text-xs">
            {label}
            {field.required && <span className="text-destructive ml-1">*</span>}
          </Label>
          <Input
            type="date"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            className="h-8 text-xs"
          />
        </div>
      );

    default:
      return (
        <div className="space-y-1">
          <Label className="text-xs">
            {label}
            {field.required && <span className="text-destructive ml-1">*</span>}
          </Label>
          <Input
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={field.placeholder || `Informe ${label.toLowerCase()}`}
            className="h-8 text-xs"
          />
        </div>
      );
  }
}
