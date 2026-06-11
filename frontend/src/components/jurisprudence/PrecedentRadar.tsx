'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Scale,
  FileText,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  Search,
  Calendar,
  BarChart3,
  Lightbulb,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';
import {
  usePrecedentRadar,
  type RadarAnalysisParams,
  formatSuccessRate,
  getOutcomeColor,
  getWeightBadge,
  getTrendIcon,
  getTrendColor,
} from '@/hooks/use-precedent-radar';

interface PrecedentRadarProps {
  /** Callback quando análise é completada */
  onAnalysisComplete?: () => void;
}

/**
 * Radar de Precedentes — Componente principal
 *
 * Mostra análise jurisprudencial com:
 * - Taxa de sucesso por tribunal
 * - Timeline de julgamentos
 * - Precedentes chave
 * - Recomendações estratégicas
 */
export function PrecedentRadar({ onAnalysisComplete }: PrecedentRadarProps) {
  const {
    report,
    isLoading,
    analyze,
    tribunais,
    teses,
  } = usePrecedentRadar();

  const [query, setQuery] = React.useState('');
  const [specialty, setSpecialty] = React.useState('');

  const handleAnalyze = () => {
    if (!query.trim()) return;

    analyze({
      query,
      specialty: specialty || undefined,
      include_timeline: true,
      limit_precedents: 10,
    });
  };

  const handleAnalysisComplete = () => {
    onAnalysisComplete?.();
  };

  React.useEffect(() => {
    if (report) {
      handleAnalysisComplete();
    }
  }, [report]);

  return (
    <div className="space-y-6">
      {/* Formulário de Análise */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Radar de Precedentes
          </CardTitle>
          <CardDescription>
            Analise a jurisprudência e identifique taxas de sucesso por tribunal
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Tese Jurídica *</label>
            <div className="relative">
              <Textarea
                placeholder="Ex: responsabilidade civil por dano moral em acidentes de trânsito"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="min-h-[80px] pr-32"
              />
              <div className="absolute top-1 right-1">
                <AIEnhanceButton
                  value={query}
                  onEnhance={setQuery}
                  context="tese jurídica para análise de precedentes"
                  objective="Melhore a precisão e clareza da tese jurídica"
                />
              </div>
            </div>
          </div>

          <div className="flex items-end gap-3">
            <div className="space-y-2 flex-1">
              <label className="text-sm font-medium">Especialidade (opcional)</label>
              <select
                value={specialty}
                onChange={(e) => setSpecialty(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Todas</option>
                <option value="CIV">Cível</option>
                <option value="PEN">Criminal</option>
                <option value="TRB">Trabalhista</option>
                <option value="FAM">Família</option>
                <option value="PRE">Previdenciário</option>
                <option value="ADM">Administrativo</option>
              </select>
            </div>

            <Button
              onClick={handleAnalyze}
              disabled={!query.trim() || isLoading}
              className="gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Analisando...
                </>
              ) : (
                <>
                  <Search className="h-4 w-4" />
                  Analisar
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Loading State */}
      {isLoading && (
        <Card>
          <CardContent className="py-8">
            <div className="flex flex-col items-center justify-center gap-3">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <p className="text-muted-foreground">
                Analisando jurisprudência...
              </p>
              <p className="text-xs text-muted-foreground">
                Isso pode levar alguns segundos
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Resultados */}
      {report && !isLoading && (
        <>
          {/* Resumo Geral */}
          <Card>
            <CardHeader>
              <CardTitle>Resumo da Análise</CardTitle>
              <CardDescription>
                {report.total_analyzed} precedentes analisados para &quot;{report.query}&quot;
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-3">
                {/* Taxa de Sucesso */}
                <div className="rounded-lg border p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-muted-foreground">
                      Taxa de Sucesso
                    </span>
                    <Scale className="h-4 w-4 text-primary" />
                  </div>
                  <div className="text-2xl font-bold">
                    {formatSuccessRate(report.overall_success_rate)}
                  </div>
                  <Progress
                    value={report.overall_success_rate * 100}
                    className="h-2 mt-2"
                  />
                </div>

                {/* Total de Casos */}
                <div className="rounded-lg border p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-muted-foreground">
                      Total de Casos
                    </span>
                    <FileText className="h-4 w-4 text-primary" />
                  </div>
                  <div className="text-2xl font-bold">
                    {report.total_analyzed}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Precedentes encontrados
                  </p>
                </div>

                {/* Tribunais */}
                <div className="rounded-lg border p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-muted-foreground">
                      Tribunais
                    </span>
                    <Scale className="h-4 w-4 text-primary" />
                  </div>
                  <div className="text-2xl font-bold">
                    {report.tribunal_stats.length}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Com jurisprudência encontrada
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Estatísticas por Tribunal */}
          <Card>
            <CardHeader>
              <CardTitle>Estatísticas por Tribunal</CardTitle>
              <CardDescription>
                Taxa de sucesso em cada tribunal
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {report.tribunal_stats.map((stat) => (
                  <TribunalCard key={stat.tribunal} stat={stat} />
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Precedentes Chave */}
          <Card>
            <CardHeader>
              <CardTitle>Precedentes Chave</CardTitle>
              <CardDescription>
                Julgamentos mais relevantes para esta tese
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                <div className="space-y-3">
                  {report.key_precedents.map((precedent) => (
                    <PrecedentCard key={precedent.id} precedent={precedent} />
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Recomendações */}
          {report.recommendations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lightbulb className="h-5 w-5 text-yellow-600" />
                  Recomendações Estratégicas
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {report.recommendations.map((rec, idx) => (
                    <li
                      key={idx}
                      className="flex items-start gap-2 text-sm"
                    >
                      <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 shrink-0" />
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Sem resultados */}
      {report && !isLoading && report.total_analyzed === 0 && (
        <Card>
          <CardContent className="py-8">
            <div className="flex flex-col items-center justify-center gap-3 text-center">
              <Search className="h-10 w-10 text-muted-foreground opacity-30" />
              <div>
                <p className="font-medium">Nenhum precedente encontrado</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Tente ajustar os termos da busca ou ampliar o período
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

interface TribunalCardProps {
  stat: {
    tribunal: string;
    total_cases: number;
    favorable_count: number;
    unfavorable_count: number;
    success_rate: number;
    recent_trend: 'improving' | 'worsening' | 'stable';
  };
}

function TribunalCard({ stat }: TribunalCardProps) {
  return (
    <div className="rounded-lg border p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Scale className="h-4 w-4 text-primary" />
          <span className="font-medium">{stat.tribunal}</span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={cn(
              'text-xs font-medium',
              getTrendColor(stat.recent_trend)
            )}
          >
            {getTrendIcon(stat.recent_trend)} {stat.recent_trend === 'improving' ? 'Melhorando' : stat.recent_trend === 'worsening' ? 'Piorando' : 'Estável'}
          </span>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-2 sm:grid-cols-3">
        <div>
          <p className="text-xs text-muted-foreground">Sucesso</p>
          <p className="text-lg font-semibold text-green-600">
            {stat.favorable_count}
          </p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Insucesso</p>
          <p className="text-lg font-semibold text-red-600">
            {stat.unfavorable_count}
          </p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Taxa</p>
          <p className="text-lg font-semibold">
            {formatSuccessRate(stat.success_rate)}
          </p>
        </div>
      </div>

      {/* Progress bar */}
      <div className="relative h-2 rounded-full bg-muted overflow-hidden">
        <div
          className="absolute left-0 top-0 h-full bg-green-600 transition-all"
          style={{ width: `${stat.success_rate * 100}%` }}
        />
        <div
          className="absolute right-0 top-0 h-full bg-red-600 transition-all"
          style={{ width: `${(1 - stat.success_rate) * 100}%` }}
        />
      </div>

      {/* Total */}
      <p className="text-xs text-muted-foreground">
        Total: {stat.total_cases} casos
      </p>
    </div>
  );
}

interface PrecedentCardProps {
  precedent: {
    id: string;
    tribunal: string;
    case_number: string;
    outcome: 'favorable' | 'unfavorable' | 'neutral' | 'mixed';
    weight: 'binding' | 'persuasive' | 'informative';
    relevance_score: number;
    summary: string;
    judgment_date: string | null;
    relator: string | null;
    organ: string | null;
    keywords: string[];
    citation: string;
  };
}

function PrecedentCard({ precedent }: PrecedentCardProps) {
  return (
    <div className="rounded-lg border p-4 space-y-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <Badge variant="outline">{precedent.tribunal}</Badge>
            {precedent.case_number && (
              <span className="text-xs font-mono text-muted-foreground">
                {precedent.case_number}
              </span>
            )}
            <Badge className={getWeightBadge(precedent.weight)}>
              {precedent.weight === 'binding' ? 'Vinculante' : precedent.weight === 'persuasive' ? 'Persuasivo' : 'Informativo'}
            </Badge>
          </div>
        </div>
        <Badge className={getOutcomeColor(precedent.outcome)}>
          {precedent.outcome === 'favorable' && <CheckCircle2 className="h-3 w-3 mr-1" />}
          {precedent.outcome === 'unfavorable' && <XCircle className="h-3 w-3 mr-1" />}
          {precedent.outcome === 'mixed' && <AlertCircle className="h-3 w-3 mr-1" />}
          {precedent.outcome === 'favorable' ? 'Favorável' : precedent.outcome === 'unfavorable' ? 'Desfavorável' : precedent.outcome === 'mixed' ? 'Misto' : 'Neutro'}
        </Badge>
      </div>

      {/* Resumo */}
      <p className="text-sm text-muted-foreground line-clamp-3">
        {precedent.summary}
      </p>

      {/* Meta */}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <div className="flex items-center gap-3">
          {precedent.judgment_date && (
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {new Date(precedent.judgment_date).toLocaleDateString('pt-BR')}
            </span>
          )}
          {precedent.relator && (
            <span>Rel.: {precedent.relator}</span>
          )}
        </div>
        <span className="flex items-center gap-1">
          Relevância: {(precedent.relevance_score * 100).toFixed(0)}%
        </span>
      </div>

      {/* Keywords */}
      {precedent.keywords.length > 0 && (
        <div className="flex gap-1 flex-wrap">
          {precedent.keywords.map((keyword, idx) => (
            <span
              key={idx}
              className="text-[10px] bg-muted px-1.5 py-0.5 rounded"
            >
              #{keyword}
            </span>
          ))}
        </div>
      )}

      {/* Citação */}
      <div className="pt-2 border-t">
        <p className="text-xs text-muted-foreground">
          <span className="font-medium">Citar como:</span>{' '}
          <span className="font-mono">{precedent.citation}</span>
        </p>
      </div>
    </div>
  );
}
