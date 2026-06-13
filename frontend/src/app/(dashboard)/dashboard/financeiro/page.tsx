'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import api from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  Clock,
  BarChart3,
  Sparkles,
  Brain,
  Send,
  Users,
  MessageSquare,
} from 'lucide-react';

type Period = 'month' | 'quarter' | 'year';

interface KPIs {
  total_receivable: string;
  total_overdue: string;
  paid_this_month: string;
  expenses_this_month: string;
  profit_this_month: string;
}

interface ChartEntry {
  month: string;
  total: string;
}

interface ClientEntry {
  client_name: string;
  total: string;
}

interface LawyerEntry {
  lawyer_name: string;
  lawyer_email: string;
  total: string;
}

interface DashboardData {
  kpis: KPIs;
  revenue_chart: ChartEntry[];
  expense_chart: ChartEntry[];
  by_client: ClientEntry[];
  by_lawyer: LawyerEntry[];
  period: { start: string; end: string; label: string };
}

interface CashFlowPrediction {
  predicted_revenue: number;
  predicted_expenses: number;
  net_cash_flow: number;
  daily_forecast: Array<{ day: number; revenue: number; expenses: number; balance: number }>;
  confidence: number;
  warnings: string[];
  recommendations: string[];
}

interface ClientRisk {
  client: { id: string; name: string };
  data: {
    risk_level: 'low' | 'medium' | 'high' | 'critical';
    risk_score: number;
    factors: string[];
    recommendations: string[];
    suggested_payment_terms: string;
  };
}

const formatCurrency = (value: string | number) => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
};

const getRiskBadgeColor = (level: string) => {
  switch (level) {
    case 'low': return 'bg-green-500';
    case 'medium': return 'bg-yellow-500';
    case 'high': return 'bg-orange-500';
    case 'critical': return 'bg-red-500';
    default: return 'bg-gray-500';
  }
};

const getRiskLabel = (level: string) => {
  switch (level) {
    case 'low': return 'Baixo';
    case 'medium': return 'Médio';
    case 'high': return 'Alto';
    case 'critical': return 'Crítico';
    default: return level;
  }
};

export default function FinanceiroPage() {
  const [period, setPeriod] = useState<Period>('month');
  const [cashFlowDialogOpen, setCashFlowDialogOpen] = useState(false);
  const [collectionDialogOpen, setCollectionDialogOpen] = useState(false);
  const [selectedClientForRisk, setSelectedClientForRisk] = useState<{ id: string; name: string } | null>(null);
  const [selectedClientForCollection, setSelectedClientForCollection] = useState<{ id: string; name: string; debt_value: number; days_overdue: number } | null>(null);

  const { data, isLoading, error } = useQuery<DashboardData>({
    queryKey: ['financial-dashboard', period],
    queryFn: async () => {
      const res = await api.get('/api/v1/processos/financeiro/dashboard/', {
        params: { period },
      });
      return res.data;
    },
  });

  // Previsão de Fluxo de Caixa
  const cashFlowMutation = useMutation({
    mutationFn: async (periodDays: number) => {
      const res = await api.get('/api/v1/processos/financeiro/copilot/prever-fluxo/', {
        params: { period: periodDays },
      });
      return res.data.data as CashFlowPrediction;
    },
    onSuccess: () => {
      setCashFlowDialogOpen(true);
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || 'Erro ao gerar previsão de fluxo de caixa');
    },
  });

  // Análise de Risco por Cliente
  const clientRiskMutation = useMutation({
    mutationFn: async (clientId: string) => {
      const res = await api.post('/api/v1/processos/financeiro/copilot/analisar-risco/', {
        client_id: clientId,
      });
      return res.data as ClientRisk;
    },
    onSuccess: (data) => {
      toast.success(`Risco de inadimplência: ${getRiskLabel(data.data.risk_level)}`);
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || 'Erro ao analisar risco');
    },
  });

  // Gerar Mensagem de Cobrança
  const collectionMutation = useMutation({
    mutationFn: async (payload: { client_id?: string; client_name: string; debt_value: number; days_overdue: number; invoice_number?: string }) => {
      const res = await api.post('/api/v1/processos/financeiro/copilot/gerar-cobranca/', payload);
      return res.data.data as { message: string };
    },
    onSuccess: (data) => {
      // Copiar mensagem para clipboard
      navigator.clipboard.writeText(data.message);
      toast.success('Mensagem de cobrança gerada e copiada!');
      setCollectionDialogOpen(false);
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || 'Erro ao gerar mensagem de cobrança');
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Dashboard Financeiro</h1>
          <p className="text-muted-foreground">Carregando dados financeiros...</p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-32" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Dashboard Financeiro</h1>
          <p className="text-muted-foreground text-red-600">
            Erro ao carregar dados financeiros. Verifique se existem movimentacoes cadastradas.
          </p>
        </div>
      </div>
    );
  }

  const kpis = data.kpis;
  const profitValue = parseFloat(kpis.profit_this_month);

  const allMonths = new Set<string>();
  data.revenue_chart.forEach((e) => allMonths.add(e.month));
  data.expense_chart.forEach((e) => allMonths.add(e.month));
  const sortedMonths = Array.from(allMonths).sort();

  const revenueMap = Object.fromEntries(data.revenue_chart.map((e) => [e.month, parseFloat(e.total)]));
  const expenseMap = Object.fromEntries(data.expense_chart.map((e) => [e.month, parseFloat(e.total)]));

  const maxChartValue = Math.max(
    ...sortedMonths.map((m) => Math.max(revenueMap[m] || 0, expenseMap[m] || 0)),
    1
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard Financeiro</h1>
          <p className="text-muted-foreground">
            Periodo: {data.period.start} a {data.period.end}
          </p>
        </div>
        <div className="flex gap-2">
          {(['month', 'quarter', 'year'] as Period[]).map((p) => (
            <Button
              key={p}
              variant={period === p ? 'default' : 'outline'}
              size="sm"
              onClick={() => setPeriod(p)}
            >
              {p === 'month' ? 'Mes' : p === 'quarter' ? 'Trimestre' : 'Ano'}
            </Button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Receitas (Mes)</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-700">
              {formatCurrency(kpis.paid_this_month)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Despesas (Mes)</CardTitle>
            <TrendingDown className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-700">
              {formatCurrency(kpis.expenses_this_month)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Lucro (Mes)</CardTitle>
            <DollarSign className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${profitValue >= 0 ? 'text-green-700' : 'text-red-700'}`}>
              {formatCurrency(kpis.profit_this_month)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">A Receber</CardTitle>
            <Clock className="h-4 w-4 text-amber-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-700">
              {formatCurrency(kpis.total_receivable)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Em Atraso</CardTitle>
            <AlertCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-700">
              {formatCurrency(kpis.total_overdue)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Card de Previsão de Fluxo de Caixa com IA */}
      <Card className="border-primary/20 bg-gradient-to-r from-primary/5 to-primary/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-primary" />
            Copilot Financeiro - Previsão de Fluxo de Caixa
          </CardTitle>
          <CardDescription>
            IA analisa seu histórico e prevê receitas, despesas e fluxo de caixa
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <Button
              onClick={() => cashFlowMutation.mutate(30)}
              disabled={cashFlowMutation.isPending}
              className="gap-2"
            >
              <Sparkles className="h-4 w-4" />
              Prever 30 dias
            </Button>
            <Button
              variant="outline"
              onClick={() => cashFlowMutation.mutate(60)}
              disabled={cashFlowMutation.isPending}
              className="gap-2"
            >
              <Sparkles className="h-4 w-4" />
              Prever 60 dias
            </Button>
            <Button
              variant="outline"
              onClick={() => cashFlowMutation.mutate(90)}
              disabled={cashFlowMutation.isPending}
              className="gap-2"
            >
              <Sparkles className="h-4 w-4" />
              Prever 90 dias
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Revenue vs Expenses Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Receitas vs Despesas
          </CardTitle>
          <CardDescription>Comparativo mensal no periodo selecionado</CardDescription>
        </CardHeader>
        <CardContent>
          {sortedMonths.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">
              Nenhuma movimentacao financeira no periodo selecionado.
            </p>
          ) : (
            <div className="space-y-3">
              <div className="flex gap-4 text-sm mb-4">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-green-500" />
                  <span>Receitas</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-red-400" />
                  <span>Despesas</span>
                </div>
              </div>

              {sortedMonths.map((month) => {
                const rev = revenueMap[month] || 0;
                const exp = expenseMap[month] || 0;
                const revPercent = (rev / maxChartValue) * 100;
                const expPercent = (exp / maxChartValue) * 100;

                return (
                  <div key={month} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="font-medium">{month}</span>
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-5 bg-muted rounded overflow-hidden">
                          <div
                            className="h-full bg-green-500 rounded transition-all duration-500"
                            style={{ width: `${revPercent}%` }}
                          />
                        </div>
                        <span className="text-xs text-muted-foreground w-28 text-right">
                          {formatCurrency(rev)}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-5 bg-muted rounded overflow-hidden">
                          <div
                            className="h-full bg-red-400 rounded transition-all duration-500"
                            style={{ width: `${expPercent}%` }}
                          />
                        </div>
                        <span className="text-xs text-muted-foreground w-28 text-right">
                          {formatCurrency(exp)}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Tables */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* By Client com Análise de Risco */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Receitas por Cliente</span>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardTitle>
            <CardDescription>Recursos utilizados no período</CardDescription>
          </CardHeader>
          <CardContent>
            {data.by_client.length === 0 ? (
              <p className="text-muted-foreground text-sm">Nenhum dado no periodo.</p>
            ) : (
              <div className="space-y-2">
                <div className="grid grid-cols-3 text-sm font-medium text-muted-foreground border-b pb-2">
                  <span className="col-span-2">Cliente</span>
                  <span className="text-right">Ações</span>
                </div>
                {data.by_client.map((entry, idx) => (
                  <div key={idx} className="grid grid-cols-3 text-sm py-1.5 border-b border-muted last:border-0 items-center">
                    <span className="truncate col-span-2">{entry.client_name || 'N/A'}</span>
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedClientForRisk({ id: entry.client_name, name: entry.client_name })}
                        title="Analisar risco"
                      >
                        <AlertCircle className="h-3 w-3" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedClientForCollection({
                          id: entry.client_name,
                          name: entry.client_name,
                          debt_value: parseFloat(entry.total) || 0,
                          days_overdue: 0
                        })}
                        title="Gerar cobrança"
                      >
                        <MessageSquare className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* By Lawyer */}
        <Card>
          <CardHeader>
            <CardTitle>Atuação por Procurador</CardTitle>
            <CardDescription>Processos por procurador responsável</CardDescription>
          </CardHeader>
          <CardContent>
            {data.by_lawyer.length === 0 ? (
              <p className="text-muted-foreground text-sm">Nenhum dado no periodo.</p>
            ) : (
              <div className="space-y-2">
                <div className="grid grid-cols-2 text-sm font-medium text-muted-foreground border-b pb-2">
                  <span>Procurador</span>
                  <span className="text-right">Total</span>
                </div>
                {data.by_lawyer.map((entry, idx) => (
                  <div key={idx} className="grid grid-cols-2 text-sm py-1.5 border-b border-muted last:border-0">
                    <span className="truncate">{entry.lawyer_name || entry.lawyer_email || 'N/A'}</span>
                    <span className="text-right font-medium">{formatCurrency(entry.total)}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Dialog de Previsão de Fluxo */}
      <Dialog open={cashFlowDialogOpen} onOpenChange={setCashFlowDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-primary" />
              Previsão de Fluxo de Caixa
            </DialogTitle>
            <DialogDescription>
              Análise preditiva baseada em IA do seu histórico orçamentário
            </DialogDescription>
          </DialogHeader>
          {cashFlowMutation.data && (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-xs text-muted-foreground">Receitas Previstas</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-xl font-bold text-green-600">
                      {formatCurrency(cashFlowMutation.data.predicted_revenue)}
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-xs text-muted-foreground">Despesas Previstas</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-xl font-bold text-red-600">
                      {formatCurrency(cashFlowMutation.data.predicted_expenses)}
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-xs text-muted-foreground">Fluxo Líquido</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className={`text-xl font-bold ${cashFlowMutation.data.net_cash_flow >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency(cashFlowMutation.data.net_cash_flow)}
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="flex items-center gap-2">
                <Badge variant={cashFlowMutation.data.confidence > 70 ? 'default' : 'secondary'}>
                  Confiança: {cashFlowMutation.data.confidence}%
                </Badge>
              </div>

              {cashFlowMutation.data.warnings.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-medium text-sm text-amber-600 flex items-center gap-2">
                    <AlertCircle className="h-4 w-4" />
                    Alertas
                  </h4>
                  <ul className="text-sm text-muted-foreground list-disc list-inside space-y-1">
                    {cashFlowMutation.data.warnings.map((warning, i) => (
                      <li key={i}>{warning}</li>
                    ))}
                  </ul>
                </div>
              )}

              {cashFlowMutation.data.recommendations.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-medium text-sm flex items-center gap-2">
                    <Sparkles className="h-4 w-4" />
                    Recomendações da IA
                  </h4>
                  <ul className="text-sm text-muted-foreground list-disc list-inside space-y-1">
                    {cashFlowMutation.data.recommendations.map((rec, i) => (
                      <li key={i}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Dialog de Análise de Risco */}
      <Dialog open={!!selectedClientForRisk} onOpenChange={() => setSelectedClientForRisk(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5" />
              Análise de Risco - {selectedClientForRisk?.name}
            </DialogTitle>
            <DialogDescription>
              IA analisa histórico de pagamentos e calcula risco de inadimplência
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Button
              onClick={() => selectedClientForRisk && clientRiskMutation.mutate(selectedClientForRisk.id)}
              disabled={clientRiskMutation.isPending}
              className="w-full gap-2"
            >
              <Brain className="h-4 w-4" />
              {clientRiskMutation.isPending ? 'Analisando...' : 'Gerar Análise com IA'}
            </Button>
            {clientRiskMutation.data && (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">Nível de Risco:</span>
                  <Badge className={getRiskBadgeColor(clientRiskMutation.data.data.risk_level)}>
                    {getRiskLabel(clientRiskMutation.data.data.risk_level)}
                  </Badge>
                  <span className="text-sm font-medium">({clientRiskMutation.data.data.risk_score}/100)</span>
                </div>
                {clientRiskMutation.data.data.factors.length > 0 && (
                  <div>
                    <h5 className="text-sm font-medium mb-1">Fatores:</h5>
                    <ul className="text-sm text-muted-foreground list-disc list-inside">
                      {clientRiskMutation.data.data.factors.map((f, i) => <li key={i}>{f}</li>)}
                    </ul>
                  </div>
                )}
                {clientRiskMutation.data.data.recommendations.length > 0 && (
                  <div>
                    <h5 className="text-sm font-medium mb-1">Recomendações:</h5>
                    <ul className="text-sm text-muted-foreground list-disc list-inside">
                      {clientRiskMutation.data.data.recommendations.map((r, i) => <li key={i}>{r}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Dialog de Comunicado */}
      <Dialog open={collectionDialogOpen} onOpenChange={setCollectionDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              Gerar Comunicado
            </DialogTitle>
            <DialogDescription>
              IA gera comunicado personalizado baseado no perfil da parte
            </DialogDescription>
          </DialogHeader>
          {selectedClientForCollection && (
            <div className="space-y-4">
              <div className="text-sm space-y-1">
                <p><strong>Cliente:</strong> {selectedClientForCollection.name}</p>
                <p><strong>Valor:</strong> {formatCurrency(selectedClientForCollection.debt_value)}</p>
                <p><strong>Dias em atraso:</strong> {selectedClientForCollection.days_overdue}</p>
              </div>
              <Button
                onClick={() => collectionMutation.mutate({
                  client_id: selectedClientForCollection?.id,
                  client_name: selectedClientForCollection?.name || '',
                  debt_value: selectedClientForCollection?.debt_value || 0,
                  days_overdue: selectedClientForCollection?.days_overdue || 0,
                })}
                disabled={collectionMutation.isPending}
                className="w-full gap-2"
              >
                <Send className="h-4 w-4" />
                {collectionMutation.isPending ? 'Gerando...' : 'Gerar Mensagem'}
              </Button>
              {collectionMutation.data && (
                <div>
                  <h5 className="text-sm font-medium mb-2">Mensagem Gerada:</h5>
                  <div className="p-3 bg-muted rounded text-sm whitespace-pre-wrap">
                    {collectionMutation.data.message}
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    Mensagem copiada para a área de transferência!
                  </p>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
