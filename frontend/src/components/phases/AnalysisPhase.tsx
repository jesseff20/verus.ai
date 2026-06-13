'use client';

import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Progress } from '@/components/ui/progress';
import {
  BarChart3,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ThumbsUp,
  ThumbsDown,
  FileText,
  TrendingUp,
  Clock,
  Zap,
  ChevronRight,
} from 'lucide-react';
import type { ApprovalStatus } from '@/types';
import { useMemo } from 'react';

interface SectionData {
  section_number: number;
  section_name: string;
  content?: string;
  score?: number;
  status: string;
  feedback?: string[];
  tokens_used?: number;
}

interface AnalysisPhaseProps {
  generatedContent: Record<string, string>;
  sectionNames: Record<number, string>;
  sections: Record<string, SectionData>;
  generationMetadata: {
    total_tokens_used?: number;
    valid_sections?: number;
    average_score?: number;
    generation_time?: number | null;
    document_id?: string;
    generation_session_id?: string;
  } | null;
  totalSections: number;
  approvalStatus: Record<number, ApprovalStatus>;
  onSetApproval: (num: number, status: ApprovalStatus) => void;
  onAdvance: () => void;
  className?: string;
}

export function AnalysisPhase({
  generatedContent,
  sectionNames,
  sections,
  generationMetadata,
  totalSections,
  approvalStatus,
  onSetApproval,
  onAdvance,
  className,
}: AnalysisPhaseProps) {
  // Section entries
  const sectionEntries = useMemo(() => {
    return Object.entries(generatedContent)
      .filter(([key]) => key.startsWith('section_'))
      .map(([key, content]) => {
        const num = parseInt(key.replace('section_', ''), 10);
        return { num, key, name: sectionNames[num] || `Seção ${num}`, content };
      })
      .sort((a, b) => a.num - b.num);
  }, [generatedContent, sectionNames]);

  // Stats
  const stats = useMemo(() => {
    const scores = Object.values(sections).map((s) => s.score).filter(Boolean) as number[];
    const avgScore = scores.length > 0
      ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
      : generationMetadata?.average_score || 0;

    const approved = Object.values(approvalStatus).filter((s) => s === 'approved').length;
    const improved = Object.values(approvalStatus).filter((s) => s === 'improved').length;
    const pending = Object.values(approvalStatus).filter((s) => s === 'pending').length;

    return {
      avgScore,
      approved,
      improved,
      pending,
      totalTokens: generationMetadata?.total_tokens_used || 0,
      genTime: generationMetadata?.generation_time,
      validSections: generationMetadata?.valid_sections || sectionEntries.length,
    };
  }, [sections, generationMetadata, approvalStatus, sectionEntries]);

  const getScoreBarColor = (score: number) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const formatTime = (seconds: number | null | undefined) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const min = Math.floor(seconds / 60);
    const sec = Math.round(seconds % 60);
    return `${min}m ${sec}s`;
  };

  return (
    <div className={cn('space-y-6', className)}>
      <h2 className="text-lg font-semibold flex items-center gap-2">
        <BarChart3 className="h-5 w-5 text-primary" />
        Análise do Documento
      </h2>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <TrendingUp className="h-6 w-6 mx-auto mb-2 text-primary" />
            <div className="text-2xl font-bold">{stats.avgScore}%</div>
            <div className="text-xs text-muted-foreground">Score Médio</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <CheckCircle2 className="h-6 w-6 mx-auto mb-2 text-green-600" />
            <div className="text-2xl font-bold">
              {stats.validSections}/{totalSections}
            </div>
            <div className="text-xs text-muted-foreground">Seções Válidas</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <Zap className="h-6 w-6 mx-auto mb-2 text-yellow-500" />
            <div className="text-2xl font-bold">{stats.totalTokens.toLocaleString()}</div>
            <div className="text-xs text-muted-foreground">Tokens Utilizados</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <Clock className="h-6 w-6 mx-auto mb-2 text-blue-500" />
            <div className="text-2xl font-bold">{formatTime(stats.genTime)}</div>
            <div className="text-xs text-muted-foreground">Tempo de Geração</div>
          </CardContent>
        </Card>
      </div>

      {/* Approval Summary */}
      <Card>
        <CardContent className="p-4">
          <h3 className="text-sm font-medium mb-3">Resumo de Aprovações</h3>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <ThumbsUp className="h-4 w-4 text-green-600" />
              <span className="text-sm">{stats.approved} aprovadas</span>
            </div>
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
              <span className="text-sm">{stats.improved} melhoradas</span>
            </div>
            <div className="flex items-center gap-2">
              <XCircle className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm">{stats.pending} pendentes</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Section Analysis */}
      <ScrollArea className="h-[400px]">
        <div className="space-y-2">
          {sectionEntries.map(({ num, name, content }) => {
            const sectionKey = `section_${String(num).padStart(2, '0')}`;
            const sectionData = sections[num];
            const score = sectionData?.score ?? 0;
            const status = approvalStatus[num] || 'pending';

            return (
              <Card key={num} className="overflow-hidden">
                <div className={cn('h-1', getScoreBarColor(score))} />
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <FileText className="h-4 w-4 text-primary shrink-0" />
                      <h4 className="text-sm font-medium truncate">{num}. {name}</h4>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className={cn(
                        'text-xs font-mono font-bold',
                        score >= 80 ? 'text-green-600' : score >= 60 ? 'text-yellow-600' : 'text-red-600'
                      )}>
                        {score}%
                      </span>
                      <div className="flex gap-1">
                        <button
                          onClick={() => onSetApproval(num, 'approved')}
                          className={cn(
                            'p-1.5 rounded text-xs border transition-colors',
                            status === 'approved'
                              ? 'bg-green-50 border-green-200 text-green-700 dark:bg-green-950 dark:border-green-800'
                              : 'border-border text-muted-foreground hover:bg-muted'
                          )}
                        >
                          <ThumbsUp className="h-3 w-3" />
                        </button>
                        <button
                          onClick={() => onSetApproval(num, 'improved')}
                          className={cn(
                            'p-1.5 rounded text-xs border transition-colors',
                            status === 'improved'
                              ? 'bg-yellow-50 border-yellow-200 text-yellow-700 dark:bg-yellow-950 dark:border-yellow-800'
                              : 'border-border text-muted-foreground hover:bg-muted'
                          )}
                        >
                          <AlertTriangle className="h-3 w-3" />
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Score bar */}
                  <div className="flex items-center gap-2">
                    <Progress value={score} className="h-1.5 flex-1" />
                    <div className="flex items-center gap-1">
                      <Badge variant="outline" className="text-[10px]">
                        {sectionData?.tokens_used || 0} tokens
                      </Badge>
                    </div>
                  </div>

                  {/* Content preview */}
                  {content && (
                    <p className="text-xs text-muted-foreground mt-2 line-clamp-2">
                      {content.slice(0, 200)}
                    </p>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      </ScrollArea>

      {/* Action */}
      <div className="flex justify-end">
        <Button onClick={onAdvance} className="gap-2">
          Ver Resultado
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
