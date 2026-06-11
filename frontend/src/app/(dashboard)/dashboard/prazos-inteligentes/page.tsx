'use client';

import { useState, useMemo } from 'react';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  Brain,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ChevronDown,
  Sparkles,
  Shield,
  TrendingUp,
  Calculator,
  Group,
  Flag,
  Lightbulb,
  Calendar,
} from 'lucide-react';
import {
  useSmartDeadlineAnalysis,
  useSmartDeadlineSuggest,
  useSmartDeadlineRisk,
  type PrazoPriorizado,
  type DeadlineAnalysis,
  type DeadlineSuggestResult,
  type CaseRiskPrediction,
} from '@/hooks/use-smart-deadlines';
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '@/lib/api';

// ── Copilot Types ──

interface DeadlineCalculation {
  deadline_date: string;
  days_count: number;
  type: 'uteis' | 'corridos';
  base_legal: string;
  start_date: string;
  intermediate_dates: { marker: string; date: string }[];
  warnings: string[];
  deadline_type: string;
  error?: string;
}

interface StrategySuggestion {
  deadline_type: string;
  days_remaining: number;
  case_urgency: string;
  strategy: string;
}

interface DeadlineGroup {
  case_id: string;
  case_name: string;
  deadlines: any[];
  total: number;
  pending: number;
  overdue: number;
  priority: 'critico' | 'alta' | 'normal';
  priority_label: string;
}

interface CriticalDeadline {
  id: string;
  titulo: string;
  tipo: string;
  data_prazo: string;
  status: string;
  prioridade: string;
  criticality_score: number;
  critical_level: 'extremo' | 'alto' | 'medio' | 'baixo';
  critical_level_label: string;
  critical_reasons: string[];
}

interface GroupedDeadlinesResult {
  total_groups: number;
  groups: DeadlineGroup[];
}

interface CriticalDeadlinesResult {
  total_critical: number;
  critical_deadlines: CriticalDeadline[];
}

/**
 * Tenta extrair JSON estruturado de uma string que pode conter
 * markdown code fences ou ser JSON puro. Retorna null se falhar.
 */
function tryParseAnalysisJson(text: string): {
  analise_geral?: string;
  prazos_priorizados?: PrazoPriorizado[];
  recomendacoes?: string[];
} | null {
  if (!text || typeof text !== 'string') return null;
  let clean = text.trim();
  // Remover markdown code fences
  if (clean.includes('```json')) {
    clean = clean.split('```json')[1]?.split('```')[0] || clean;
  } else if (clean.includes('```')) {
    clean = clean.split('```')[1]?.split('```')[0] || clean;
  }
  try {
    const parsed = JSON.parse(clean.trim());
    if (typeof parsed === 'object' && parsed !== null) return parsed;
  } catch {
    // Não é JSON válido
  }
  return null;
}

/**
 * Normaliza os dados da análise: se o backend retornou o JSON cru
 * no campo `analise` (porque _extract_json falhou), tenta parsear
 * no frontend e extrair os campos estruturados.
 */
function normalizeAnalysis(raw: DeadlineAnalysis): DeadlineAnalysis {
  // Se já tem prazos_priorizados populados, está OK
  if (raw.prazos_priorizados && raw.prazos_priorizados.length > 0) {
    return raw;
  }

  // Tentar parsear o campo analise como JSON
  const parsed = tryParseAnalysisJson(raw.analise);
  if (!parsed) return raw;

  return {
    ...raw,
    analise: parsed.analise_geral || raw.analise,
    prazos_priorizados: parsed.prazos_priorizados || raw.prazos_priorizados || [],
    recomendacoes: parsed.recomendacoes || raw.recomendacoes || [],
  };
}

const riskColor: Record<string, string> = {
  alto: 'bg-red-100 text-red-800 dark:bg-red-950/30 dark:text-red-400',
  medio: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-950/30 dark:text-yellow-400',
  baixo: 'bg-green-100 text-green-800 dark:bg-green-950/30 dark:text-green-400',
};

const riskBadgeVariant: Record<string, 'destructive' | 'default' | 'secondary'> = {
  alto: 'destructive',
  medio: 'default',
  baixo: 'secondary',
};

const urgencyColor: Record<string, string> = {
  alta: 'text-red-600',
  media: 'text-yellow-600',
  baixa: 'text-green-600',
};

function RiskIcon({ nivel }: { nivel: string }) {
  if (nivel === 'alto') return <AlertTriangle className="h-5 w-5 text-red-500" />;
  if (nivel === 'medio') return <Clock className="h-5 w-5 text-yellow-500" />;
  return <CheckCircle2 className="h-5 w-5 text-green-500" />;
}

export default function PrazosInteligentesPage() {
  const [analysis, setAnalysis] = useState<DeadlineAnalysis | null>(null);
  const [suggestions, setSuggestions] = useState<Record<string, DeadlineSuggestResult>>({});
  const [selectedCaseId, setSelectedCaseId] = useState('');
  const [riskResult, setRiskResult] = useState<CaseRiskPrediction | null>(null);

  // Copilot states
  const [calcResult, setCalcResult] = useState<DeadlineCalculation | null>(null);
  const [strategyResult, setStrategyResult] = useState<StrategySuggestion | null>(null);
  const [groupedDeadlines, setGroupedDeadlines] = useState<GroupedDeadlinesResult | null>(null);
  const [criticalDeadlines, setCriticalDeadlines] = useState<CriticalDeadlinesResult | null>(null);

  // Copilot form states
  const [calcDeadlineType, setCalcDeadlineType] = useState('contestacao');
  const [calcStartDate, setCalcStartDate] = useState('');
  const [strategyDeadlineType, setStrategyDeadlineType] = useState('contestacao');
  const [strategyDaysRemaining, setStrategyDaysRemaining] = useState('');
  const [strategyUrgency, setStrategyUrgency] = useState('media');

  const analysisMutation = useSmartDeadlineAnalysis();
  const suggestMutation = useSmartDeadlineSuggest();
  const riskMutation = useSmartDeadlineRisk();

  // Copilot mutations
  const calcMutation = useMutation({
    mutationFn: async (data: { deadline_type: string; start_date: string; case_data?: any }) => {
      const res = await api.post<DeadlineCalculation>('/api/v1/processos/prazos/copilot/calcular/', data);
      return res.data;
    },
  });

  const strategyMutation = useMutation({
    mutationFn: async (data: { deadline_type: string; days_remaining: number; case_urgency: string }) => {
      const res = await api.post<StrategySuggestion>('/api/v1/processos/prazos/copilot/estrategia/', data);
      return res.data;
    },
  });

  const groupMutation = useMutation({
    mutationFn: async (deadlines: any[]) => {
      const res = await api.post<GroupedDeadlinesResult>('/api/v1/processos/prazos/copilot/agrupar/', { deadlines });
      return res.data;
    },
  });

  const criticalQuery = useQuery({
    queryKey: ['critical-deadlines'],
    queryFn: async () => {
      const res = await api.get<CriticalDeadlinesResult>('/api/v1/processos/prazos/copilot/criticos/');
      return res.data;
    },
    enabled: false,
  });

  // Normalizar análise: se o backend retornou JSON cru, parsear no frontend
  const normalizedAnalysis = useMemo(
    () => (analysis ? normalizeAnalysis(analysis) : null),
    [analysis],
  );

  // Buscar casos para dropdown
  const { data: casesData } = useQuery({
    queryKey: ['cases-list-simple'],
    queryFn: async () => {
      const res = await api.get('/api/v1/processos/', { params: { page_size: 100 } });
      return res.data?.results || [];
    },
  });

  const handleAnalysis = async () => {
    try {
      const data = await analysisMutation.mutateAsync();
      setAnalysis(data);
      if (data.prazos_analisados === 0) {
        toast.info('Nenhum prazo pendente encontrado para análise.');
      } else {
        toast.success('Análise concluída com sucesso.');
      }
    } catch {
      toast.error('Erro ao processar análise com IA.');
    }
  };

  const handleSuggest = async (deadlineId: string) => {
    try {
      const data = await suggestMutation.mutateAsync(deadlineId);
      setSuggestions((prev) => ({ ...prev, [deadlineId]: data }));
    } catch {
      toast.error('Erro ao obter sugestões da IA.');
    }
  };

  const handleRiskPrediction = async () => {
    if (!selectedCaseId) {
      toast.error('Selecione um caso para análise de risco.');
      return;
    }
    try {
      const data = await riskMutation.mutateAsync(selectedCaseId);
      setRiskResult(data);
      toast.success('Predição de risco concluída.');
    } catch {
      toast.error('Erro ao processar predição de risco.');
    }
  };

  // Copilot handlers
  const handleCalculateDeadline = async () => {
    if (!calcDeadlineType || !calcStartDate) {
      toast.error('Preencha o tipo de prazo e a data inicial.');
      return;
    }
    try {
      const data = await calcMutation.mutateAsync({
        deadline_type: calcDeadlineType,
        start_date: calcStartDate,
        case_data: { estado: 'BR' },
      });
      setCalcResult(data);
      toast.success('Prazo calculado com sucesso.');
    } catch {
      toast.error('Erro ao calcular prazo com IA.');
    }
  };

  const handleSuggestStrategy = async () => {
    if (!strategyDeadlineType || !strategyDaysRemaining) {
      toast.error('Preencha o tipo de prazo e dias restantes.');
      return;
    }
    try {
      const data = await strategyMutation.mutateAsync({
        deadline_type: strategyDeadlineType,
        days_remaining: parseInt(strategyDaysRemaining),
        case_urgency: strategyUrgency,
      });
      setStrategyResult(data);
      toast.success('Estratégia sugerida com sucesso.');
    } catch {
      toast.error('Erro ao obter sugestão de estratégia.');
    }
  };

  const handleGroupDeadlines = async () => {
    try {
      // Buscar prazos pendentes para agrupar
      const res = await api.get('/api/v1/processos/prazos/', { params: { page_size: 100 } });
      const deadlines = res.data?.results || [];
      const data = await groupMutation.mutateAsync(deadlines);
      setGroupedDeadlines(data);
      toast.success('Prazos agrupados com sucesso.');
    } catch {
      toast.error('Erro ao agrupar prazos.');
    }
  };

  const handleLoadCritical = async () => {
    try {
      await criticalQuery.refetch();
      if (criticalQuery.data) {
        setCriticalDeadlines(criticalQuery.data);
      }
      toast.success('Prazos críticos carregados.');
    } catch {
      toast.error('Erro ao carregar prazos críticos.');
    }
  };

  return (
    <div className="flex flex-col gap-6 p-4 md:p-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Brain className="h-8 w-8 text-primary" />
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold tracking-tight">Prazos Inteligentes</h1>
          <Badge className="bg-primary/10 text-primary">
            <Sparkles className="h-3 w-3 mr-1" />
            IA
          </Badge>
        </div>
      </div>
      <p className="text-sm text-muted-foreground -mt-4 ml-11">
        Análise, priorização e predição de riscos com inteligência artificial
      </p>

      {/* AI Analysis Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Análise de Prazos com IA
              </CardTitle>
              <CardDescription>
                A IA analisa todos os seus prazos pendentes e sugere priorização
              </CardDescription>
            </div>
            <Button onClick={handleAnalysis} disabled={analysisMutation.isPending}>
              {analysisMutation.isPending ? (
                <Brain className="h-4 w-4 animate-pulse mr-2" />
              ) : (
                <Sparkles className="h-4 w-4 mr-2" />
              )}
              Analisar com IA
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {analysisMutation.isPending && (
            <div className="space-y-3">
              <Skeleton className="h-6 w-1/2" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-2/3" />
              <Skeleton className="h-20 w-full" />
            </div>
          )}

          {normalizedAnalysis && !analysisMutation.isPending && (
            <div className="space-y-6">
              {/* General Analysis */}
              <div className="p-4 bg-muted/50 rounded-lg">
                <p className="text-sm font-medium mb-1">Analise Geral</p>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {normalizedAnalysis.analise}
                </p>
                <p className="text-xs text-muted-foreground mt-2">
                  {normalizedAnalysis.prazos_analisados} prazo(s) analisado(s)
                </p>
              </div>

              {/* Prioritized Deadlines */}
              {normalizedAnalysis.prazos_priorizados && normalizedAnalysis.prazos_priorizados.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold">Prazos Priorizados</h3>
                  {normalizedAnalysis.prazos_priorizados.map((prazo: PrazoPriorizado, idx: number) => (
                    <Collapsible key={prazo.id || `prazo-${idx}`}>
                      <div className={`p-4 rounded-lg border ${riskColor[prazo.risco] || ''}`}>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <RiskIcon nivel={prazo.risco} />
                            <div>
                              <p className="font-medium text-sm">{prazo.titulo}</p>
                              <p className="text-xs text-muted-foreground">{prazo.motivo}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant={riskBadgeVariant[prazo.risco] || 'default'}>
                              Risco {prazo.risco}
                            </Badge>
                            {prazo.id && (
                              <CollapsibleTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => {
                                    if (!suggestions[prazo.id]) handleSuggest(prazo.id);
                                  }}
                                >
                                  <ChevronDown className="h-4 w-4 mr-1" />
                                  Sugestoes IA
                                </Button>
                              </CollapsibleTrigger>
                            )}
                          </div>
                        </div>
                        {prazo.acao_sugerida && (
                          <div className="mt-2 p-2 bg-primary/5 rounded text-xs">
                            <strong>Acao sugerida:</strong> {prazo.acao_sugerida}
                          </div>
                        )}

                        <CollapsibleContent>
                          {suggestMutation.isPending && !suggestions[prazo.id] && (
                            <div className="mt-3 space-y-2">
                              <Skeleton className="h-4 w-3/4" />
                              <Skeleton className="h-4 w-1/2" />
                            </div>
                          )}

                          {suggestions[prazo.id] && (
                            <div className="mt-3 space-y-2 border-t pt-3">
                              <p className="text-xs font-semibold">Sugestoes da IA:</p>
                              {suggestions[prazo.id].sugestoes.map((s, i) => (
                                <div key={i} className="flex items-start gap-2 text-xs">
                                  <CheckCircle2 className={`h-3.5 w-3.5 mt-0.5 ${urgencyColor[s.urgencia] || ''}`} />
                                  <div>
                                    <p>{s.acao}</p>
                                    <p className="text-muted-foreground">
                                      Urgencia: {s.urgencia} | Prazo: {s.prazo_sugerido}
                                    </p>
                                  </div>
                                </div>
                              ))}
                              {suggestions[prazo.id].observacoes && (
                                <p className="text-xs text-muted-foreground mt-2">
                                  {suggestions[prazo.id].observacoes}
                                </p>
                              )}
                            </div>
                          )}
                        </CollapsibleContent>
                      </div>
                    </Collapsible>
                  ))}
                </div>
              )}

              {/* Fallback: se não conseguiu parsear prazos, mostrar texto bruto formatado */}
              {(!normalizedAnalysis.prazos_priorizados || normalizedAnalysis.prazos_priorizados.length === 0) &&
                normalizedAnalysis.analise &&
                normalizedAnalysis.analise !== 'Nenhum prazo pendente encontrado.' && (
                <div className="p-4 bg-muted/30 rounded-lg border">
                  <p className="text-xs font-medium mb-2 text-muted-foreground">
                    Resposta da IA (texto bruto):
                  </p>
                  <pre className="text-sm whitespace-pre-wrap break-words font-mono">
                    {normalizedAnalysis.analise}
                  </pre>
                </div>
              )}

              {/* Recommendations */}
              {normalizedAnalysis.recomendacoes && normalizedAnalysis.recomendacoes.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold mb-2">Recomendacoes</h3>
                  <ul className="space-y-1">
                    {normalizedAnalysis.recomendacoes.map((rec, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <Sparkles className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Risk Prediction Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Predição de Risco por Caso
          </CardTitle>
          <CardDescription>
            Selecione um caso para avaliar o nível de risco com base nos prazos
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3 items-end">
            <div className="flex-1">
              <Select value={selectedCaseId} onValueChange={setSelectedCaseId}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecione um caso..." />
                </SelectTrigger>
                <SelectContent>
                  {(casesData || []).map((c: { id: string; titulo: string; numero_processo?: string }) => (
                    <SelectItem key={c.id} value={c.id}>
                      {c.titulo} {c.numero_processo ? `(${c.numero_processo})` : ''}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleRiskPrediction} disabled={riskMutation.isPending || !selectedCaseId}>
              {riskMutation.isPending ? (
                <Brain className="h-4 w-4 animate-pulse mr-2" />
              ) : (
                <Shield className="h-4 w-4 mr-2" />
              )}
              Avaliar Risco
            </Button>
          </div>

          {riskMutation.isPending && (
            <div className="mt-4 space-y-3">
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-4 w-3/4" />
            </div>
          )}

          {riskResult && !riskMutation.isPending && (
            <div className="mt-6 space-y-4">
              {/* Risk Level */}
              <div className={`p-4 rounded-lg ${riskColor[riskResult.nivel_risco] || ''}`}>
                <div className="flex items-center gap-3">
                  <RiskIcon nivel={riskResult.nivel_risco} />
                  <div>
                    <p className="font-semibold">
                      Nível de Risco: {riskResult.nivel_risco.toUpperCase()}
                    </p>
                    <p className="text-sm">Score: {riskResult.score}/100</p>
                  </div>
                </div>
              </div>

              {/* Explanation */}
              <div>
                <p className="text-sm font-medium mb-1">Explicação</p>
                <p className="text-sm text-muted-foreground">{riskResult.explicacao}</p>
              </div>

              {/* Stats */}
              {riskResult.estatisticas && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="p-3 bg-muted/50 rounded-lg text-center">
                    <p className="text-2xl font-bold">{riskResult.estatisticas.total_prazos}</p>
                    <p className="text-xs text-muted-foreground">Total de Prazos</p>
                  </div>
                  <div className="p-3 bg-muted/50 rounded-lg text-center">
                    <p className="text-2xl font-bold">{riskResult.estatisticas.pendentes}</p>
                    <p className="text-xs text-muted-foreground">Pendentes</p>
                  </div>
                  <div className="p-3 bg-red-50 dark:bg-red-950/20 rounded-lg text-center">
                    <p className="text-2xl font-bold text-red-600">{riskResult.estatisticas.atrasados}</p>
                    <p className="text-xs text-muted-foreground">Atrasados</p>
                  </div>
                  <div className="p-3 bg-green-50 dark:bg-green-950/20 rounded-lg text-center">
                    <p className="text-2xl font-bold text-green-600">{riskResult.estatisticas.concluidos}</p>
                    <p className="text-xs text-muted-foreground">Concluídos</p>
                  </div>
                </div>
              )}

              {/* Risk Factors */}
              {riskResult.fatores_risco && riskResult.fatores_risco.length > 0 && (
                <div>
                  <p className="text-sm font-medium mb-2">Fatores de Risco</p>
                  <ul className="space-y-1">
                    {riskResult.fatores_risco.map((fator, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <AlertTriangle className="h-4 w-4 text-yellow-500 mt-0.5 shrink-0" />
                        <span>{fator}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Recommendations */}
              {riskResult.recomendacoes && riskResult.recomendacoes.length > 0 && (
                <div>
                  <p className="text-sm font-medium mb-2">Recomendações</p>
                  <ul className="space-y-1">
                    {riskResult.recomendacoes.map((rec, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <Sparkles className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* ========== COPILOT: CALCULADORA DE PRAZOS ========== */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Calculator className="h-5 w-5" />
                Calculadora de Prazos com IA
              </CardTitle>
              <CardDescription>
                Calcule prazos processuais considerando dias úteis e feriados
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <label className="text-sm font-medium mb-2 block">Tipo de Prazo</label>
              <Select value={calcDeadlineType} onValueChange={setCalcDeadlineType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="contestacao">Contestação (15 dias)</SelectItem>
                  <SelectItem value="replica">Réplica (15 dias)</SelectItem>
                  <SelectItem value="apelacao">Apelação (15 dias)</SelectItem>
                  <SelectItem value="agravo_instrumento">Agravo de Instrumento (15 dias)</SelectItem>
                  <SelectItem value="embargos_declaracao">Embargos de Declaração (5 dias)</SelectItem>
                  <SelectItem value="resposta_acusacao">Resposta à Acusação (10 dias)</SelectItem>
                  <SelectItem value="alegacoes_finais">Alegações Finais (15 dias)</SelectItem>
                  <SelectItem value="impugnacao">Impugnação (15 dias)</SelectItem>
                  <SelectItem value="provas">Especificação de Provas (10 dias)</SelectItem>
                  <SelectItem value="pericia">Perícia (30 dias)</SelectItem>
                  <SelectItem value="manifestacao">Manifestação (5 dias)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Data Inicial</label>
              <input
                type="date"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={calcStartDate}
                onChange={(e) => setCalcStartDate(e.target.value)}
              />
            </div>
            <div className="flex items-end">
              <Button onClick={handleCalculateDeadline} disabled={calcMutation.isPending} className="w-full">
                {calcMutation.isPending ? (
                  <Brain className="h-4 w-4 animate-pulse mr-2" />
                ) : (
                  <Calculator className="h-4 w-4 mr-2" />
                )}
                Calcular com IA
              </Button>
            </div>
          </div>

          {calcResult && !calcMutation.isPending && (
            <div className="mt-6 space-y-4">
              <div className="p-4 bg-primary/5 rounded-lg border border-primary/20">
                <div className="flex items-center gap-2 mb-2">
                  <Calendar className="h-5 w-5 text-primary" />
                  <p className="font-semibold text-primary">Prazo Calculado</p>
                </div>
                <p className="text-2xl font-bold">{calcResult.deadline_date}</p>
                <p className="text-sm text-muted-foreground mt-1">
                  {calcResult.days_count} dias {calcResult.type === 'uteis' ? 'úteis' : 'corridos'} • {calcResult.base_legal}
                </p>
              </div>

              {calcResult.intermediate_dates && calcResult.intermediate_dates.length > 0 && (
                <div>
                  <p className="text-sm font-medium mb-2">Datas Intermediárias</p>
                  <div className="flex gap-4">
                    {calcResult.intermediate_dates.map((d, i) => (
                      <div key={i} className="px-3 py-2 bg-muted/50 rounded text-sm">
                        <span className="text-muted-foreground">{d.marker}:</span>{' '}
                        <span className="font-medium">{d.date}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {calcResult.warnings && calcResult.warnings.length > 0 && (
                <div className="p-3 bg-yellow-50 dark:bg-yellow-950/20 rounded border border-yellow-200 dark:border-yellow-800">
                  <div className="flex items-center gap-2 mb-1">
                    <AlertTriangle className="h-4 w-4 text-yellow-600" />
                    <p className="font-medium text-yellow-800 dark:text-yellow-200">Atenção</p>
                  </div>
                  <ul className="text-sm text-yellow-700 dark:text-yellow-300 space-y-1">
                    {calcResult.warnings.map((w, i) => (
                      <li key={i}>• {w}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* ========== COPILOT: SUGESTÃO DE ESTRATÉGIA ========== */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Lightbulb className="h-5 w-5" />
                Sugestão de Estratégia
              </CardTitle>
              <CardDescription>
                Receba sugestões de atuação baseadas no tipo de prazo e urgência
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Tipo de Prazo</label>
              <Select value={strategyDeadlineType} onValueChange={setStrategyDeadlineType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="contestacao">Contestação</SelectItem>
                  <SelectItem value="replica">Réplica</SelectItem>
                  <SelectItem value="apelacao">Apelação</SelectItem>
                  <SelectItem value="agravo_instrumento">Agravo de Instrumento</SelectItem>
                  <SelectItem value="embargos_declaracao">Embargos de Declaração</SelectItem>
                  <SelectItem value="impugnacao">Impugnação</SelectItem>
                  <SelectItem value="provas">Provas</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Dias Restantes</label>
              <input
                type="number"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={strategyDaysRemaining}
                onChange={(e) => setStrategyDaysRemaining(e.target.value)}
                placeholder="Ex: 5"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Urgência do Caso</label>
              <Select value={strategyUrgency} onValueChange={setStrategyUrgency}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="alta">Alta</SelectItem>
                  <SelectItem value="media">Média</SelectItem>
                  <SelectItem value="baixa">Baixa</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button onClick={handleSuggestStrategy} disabled={strategyMutation.isPending} className="w-full">
                {strategyMutation.isPending ? (
                  <Brain className="h-4 w-4 animate-pulse mr-2" />
                ) : (
                  <Lightbulb className="h-4 w-4 mr-2" />
                )}
                Sugerir Estratégia
              </Button>
            </div>
          </div>

          {strategyResult && !strategyMutation.isPending && (
            <div className="mt-6 p-4 bg-gradient-to-r from-primary/5 to-primary/10 rounded-lg border border-primary/20">
              <div className="flex items-center gap-2 mb-3">
                <Lightbulb className="h-5 w-5 text-primary" />
                <p className="font-semibold">Estratégia Sugerida</p>
              </div>
              <p className="text-sm whitespace-pre-wrap">{strategyResult.strategy}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ========== COPILOT: PRAZOS AGRUPADOS ========== */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Group className="h-5 w-5" />
                Prazos Agrupados por Caso
              </CardTitle>
              <CardDescription>
                Visualize prazos relacionados agrupados por caso
              </CardDescription>
            </div>
            <Button onClick={handleGroupDeadlines} disabled={groupMutation.isPending}>
              {groupMutation.isPending ? (
                <Brain className="h-4 w-4 animate-pulse mr-2" />
              ) : (
                <Group className="h-4 w-4 mr-2" />
              )}
              Agrupar Prazos
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {groupMutation.isPending && (
            <div className="space-y-3">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          )}

          {groupedDeadlines && !groupMutation.isPending && (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                {groupedDeadlines.total_groups} grupos de prazos encontrados
              </p>
              {groupedDeadlines.groups.map((group, idx) => (
                <div
                  key={group.case_id || idx}
                  className={`p-4 rounded-lg border ${
                    group.priority === 'critico'
                      ? 'border-red-300 bg-red-50 dark:bg-red-950/20'
                      : group.priority === 'alta'
                      ? 'border-yellow-300 bg-yellow-50 dark:bg-yellow-950/20'
                      : 'border-border bg-card'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <p className="font-medium">{group.case_name}</p>
                      <p className="text-sm text-muted-foreground">
                        {group.total} prazos • {group.pending} pendentes • {group.overdue} atrasados
                      </p>
                    </div>
                    <Badge
                      variant={
                        group.priority === 'critico' ? 'destructive' : group.priority === 'alta' ? 'default' : 'secondary'
                      }
                    >
                      {group.priority_label}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}

          {!groupedDeadlines && !groupMutation.isPending && (
            <p className="text-sm text-muted-foreground text-center py-8">
              Clique em "Agrupar Prazos" para visualizar
            </p>
          )}
        </CardContent>
      </Card>

      {/* ========== COPILOT: PRAZOS CRÍTICOS ========== */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Flag className="h-5 w-5 text-red-500" />
                Prazos Críticos
              </CardTitle>
              <CardDescription>
                Identificação automática de prazos que exigem atenção imediata
              </CardDescription>
            </div>
            <Button onClick={handleLoadCritical} disabled={criticalQuery.isFetching} variant="destructive">
              {criticalQuery.isFetching ? (
                <Brain className="h-4 w-4 animate-pulse mr-2" />
              ) : (
                <Flag className="h-4 w-4 mr-2" />
              )}
              Carregar Críticos
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {criticalQuery.isLoading && (
            <div className="space-y-3">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          )}

          {criticalDeadlines && !criticalQuery.isLoading && (
            <div className="space-y-3">
              {criticalDeadlines.total_critical === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">
                  <CheckCircle2 className="h-8 w-8 mx-auto mb-2 text-green-500" />
                  Nenhum prazo crítico encontrado!
                </p>
              ) : (
                <>
                  <p className="text-sm text-muted-foreground">
                    {criticalDeadlines.total_critical} prazo(s) crítico(s) identificado(s)
                  </p>
                  {criticalDeadlines.critical_deadlines.map((deadline, idx) => (
                    <div
                      key={deadline.id || idx}
                      className={`p-4 rounded-lg border ${
                        deadline.critical_level === 'extremo'
                          ? 'border-red-500 bg-red-50 dark:bg-red-950/30'
                          : deadline.critical_level === 'alto'
                          ? 'border-orange-400 bg-orange-50 dark:bg-orange-950/20'
                          : deadline.critical_level === 'medio'
                          ? 'border-yellow-400 bg-yellow-50 dark:bg-yellow-950/20'
                          : 'border-border'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium">{deadline.titulo}</span>
                            <Badge
                              variant={
                                deadline.critical_level === 'extremo'
                                  ? 'destructive'
                                  : deadline.critical_level === 'alto'
                                  ? 'default'
                                  : 'secondary'
                              }
                              className="text-xs"
                            >
                              {deadline.critical_level_label}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {deadline.tipo} • Vence em: {deadline.data_prazo}
                          </p>
                          {deadline.critical_reasons && deadline.critical_reasons.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-2">
                              {deadline.critical_reasons.map((reason, i) => (
                                <span
                                  key={i}
                                  className="text-xs px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded"
                                >
                                  {reason}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </>
              )}
            </div>
          )}

          {!criticalDeadlines && !criticalMutation.isFetching && (
            <p className="text-sm text-muted-foreground text-center py-8">
              Clique em "Carregar Críticos" para identificar prazos urgentes
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
