'use client';

import * as React from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import {
  AlertTriangle,
  CheckCircle2,
  XCircle,
  FileWarning,
  Shield,
  Scale,
  Gavel,
  BookOpen,
  FileText,
  UserCheck,
  MessageSquare,
  ListChecks,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Interfaces
// ---------------------------------------------------------------------------

export interface ScorecardItem {
  label: string;
  key: string;
  value: number;
  max: number;
  icon?: React.ReactNode;
}

export interface LegalValidationPanelProps {
  /** Pontuação geral (0-100) */
  overallScore: number;
  /** Breakdown do scorecard */
  scorecard: ScorecardItem[];
  /** Placeholders não resolvidos */
  unresolvedPlaceholders: { section: string; placeholders: string[] }[];
  /** Total de placeholders não resolvidos */
  totalUnresolved: number;
  /** Status da revisão */
  isReviewed?: boolean;
  /** OAB do revisor */
  reviewerOab?: string;
  /** Callback quando o checkbox de revisão é alterado */
  onReviewChange?: (reviewed: boolean) => void;
  /** Callback quando o campo OAB é alterado */
  onOabChange?: (oab: string) => void;
  /** Callback para exportar */
  onExport?: () => void;
  /** Se está pronto para exportação */
  canExport?: boolean;
}

// ---------------------------------------------------------------------------
// Score color helpers
// ---------------------------------------------------------------------------

function getScoreColor(score: number): string {
  if (score >= 90) return 'text-green-600';
  if (score >= 70) return 'text-yellow-600';
  if (score >= 50) return 'text-orange-600';
  return 'text-red-600';
}

function getScoreBg(score: number): string {
  if (score >= 90) return 'bg-green-50 border-green-200';
  if (score >= 70) return 'bg-yellow-50 border-yellow-200';
  if (score >= 50) return 'bg-orange-50 border-orange-200';
  return 'bg-red-50 border-red-200';
}

function getScoreLabel(score: number): string {
  if (score >= 90) return 'Excelente';
  if (score >= 70) return 'Bom';
  if (score >= 50) return 'Regular';
  return 'Requer revisão';
}

function getProgressColor(score: number): string {
  if (score >= 90) return 'bg-green-500';
  if (score >= 70) return 'bg-yellow-500';
  if (score >= 50) return 'bg-orange-500';
  return 'bg-red-500';
}

const DEFAULT_ICONS: Record<string, React.ReactNode> = {
  qualificacao_partes: <UserCheck className="h-4 w-4" />,
  fatos_coerentes: <FileText className="h-4 w-4" />,
  fundamentos_verificados: <Scale className="h-4 w-4" />,
  pedidos_especificos: <ListChecks className="h-4 w-4" />,
  sem_alucinacao: <Shield className="h-4 w-4" />,
  linguagem_tecnica: <BookOpen className="h-4 w-4" />,
  requerimentos_completos: <FileWarning className="h-4 w-4" />,
};

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function LegalValidationPanel({
  overallScore,
  scorecard,
  unresolvedPlaceholders,
  totalUnresolved,
  isReviewed = false,
  reviewerOab = '',
  onReviewChange,
  onOabChange,
  onExport,
  canExport = false,
}: LegalValidationPanelProps) {
  const scoreColor = getScoreColor(overallScore);
  const scoreBg = getScoreBg(overallScore);
  const scoreLabel = getScoreLabel(overallScore);
  const progressColor = getProgressColor(overallScore);

  return (
    <div className="space-y-6">
      {/* Score Geral */}
      <Card className={cn('border-2', scoreBg)}>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2">
            <Gavel className="h-5 w-5" />
            Scorecard Jurídico
          </CardTitle>
          <CardDescription>
            Avaliação da qualidade jurídica do documento gerado
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <div className={cn('text-4xl font-bold', scoreColor)}>
              {Math.round(overallScore)}
            </div>
            <div className="flex-1 space-y-1">
              <Progress
                value={overallScore}
                className="h-3"
                indicatorClassName={progressColor}
              />
              <p className={cn('text-sm font-medium', scoreColor)}>
                {scoreLabel}
              </p>
            </div>
          </div>

          {/* Breakdown */}
          <div className="space-y-2 pt-2">
            <p className="text-sm font-medium text-muted-foreground">
              Detalhamento por critério
            </p>
            {scorecard.map((item) => (
              <div key={item.key} className="flex items-center gap-3">
                <div className="text-muted-foreground">
                  {item.icon || DEFAULT_ICONS[item.key] || <Scale className="h-4 w-4" />}
                </div>
                <div className="flex-1">
                  <div className="flex justify-between text-sm">
                    <span>{item.label}</span>
                    <span
                      className={cn(
                        'font-medium',
                        getScoreColor((item.value / item.max) * 100)
                      )}
                    >
                      {item.value}/{item.max}
                    </span>
                  </div>
                  <Progress
                    value={(item.value / item.max) * 100}
                    className="h-1.5 mt-1"
                    indicatorClassName={getProgressColor(
                      (item.value / item.max) * 100
                    )}
                  />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Placeholders não resolvidos */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle
              className={cn(
                'h-5 w-5',
                totalUnresolved > 0 ? 'text-orange-500' : 'text-green-500'
              )}
            />
            Placeholders
          </CardTitle>
          <CardDescription>
            Campos com dados pendentes de preenchimento
          </CardDescription>
        </CardHeader>
        <CardContent>
          {totalUnresolved === 0 ? (
            <div className="flex items-center gap-2 text-green-600">
              <CheckCircle2 className="h-4 w-4" />
              <span className="text-sm">
                Nenhum placeholder não resolvido encontrado.
              </span>
            </div>
          ) : (
            <div className="space-y-3">
              <Badge variant="outline" className="text-orange-600 border-orange-300">
                {totalUnresolved} placeholder{totalUnresolved !== 1 ? 's' : ''} pendente
                {totalUnresolved !== 1 ? 's' : ''}
              </Badge>
              {unresolvedPlaceholders.map((item, idx) => (
                <div key={idx} className="text-sm">
                  <p className="font-medium text-muted-foreground">
                    {item.section}
                  </p>
                  <ul className="list-disc list-inside ml-2 space-y-0.5">
                    {item.placeholders.map((ph, i) => (
                      <li key={i} className="text-orange-700">
                        {ph}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Revisão Humana */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2">
            <UserCheck className="h-5 w-5" />
            Revisão Humana Obrigatória
          </CardTitle>
          <CardDescription>
            Um procurador competente deve revisar o documento antes da exportação
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-3">
            <Checkbox
              id="review-check"
              checked={isReviewed}
              onCheckedChange={(checked) =>
                onReviewChange?.(checked === true)
              }
            />
            <Label htmlFor="review-check" className="text-sm font-normal">
              Declaro que revisei o documento e confirmo que está adequado
              para exportação.
            </Label>
          </div>

          <div className="space-y-2">
            <Label htmlFor="oab-field">Número da OAB do Revisor</Label>
            <Input
              id="oab-field"
              placeholder="00000/UF"
              value={reviewerOab}
              onChange={(e) => onOabChange?.(e.target.value)}
              className="max-w-xs"
            />
          </div>
        </CardContent>
        <CardFooter className="border-t pt-4">
          <Button
            onClick={onExport}
            disabled={!canExport || !isReviewed || !reviewerOab.trim()}
            className="w-full"
          >
            <FileText className="h-4 w-4 mr-2" />
            Exportar Documento
          </Button>
          {(!isReviewed || !reviewerOab.trim()) && (
            <p className="text-xs text-muted-foreground mt-2 text-center w-full">
              {!isReviewed
                ? 'Marque a declaração de revisão para habilitar a exportação.'
                : 'Preencha o número da OAB para habilitar a exportação.'}
            </p>
          )}
        </CardFooter>
      </Card>
    </div>
  );
}

/**
 * Hook de validação de exportação.
 * Verifica se todas as condições para exportação foram atendidas.
 */
export function useExportValidation() {
  const [isReviewed, setIsReviewed] = React.useState(false);
  const [reviewerOab, setReviewerOab] = React.useState('');

  const canExport = React.useMemo(() => {
    return isReviewed && reviewerOab.trim().length >= 5;
  }, [isReviewed, reviewerOab]);

  return {
    isReviewed,
    setIsReviewed,
    reviewerOab,
    setReviewerOab,
    canExport,
  };
}
