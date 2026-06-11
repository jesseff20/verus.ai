'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import api from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Scale,
  Calculator,
  Search,
  DollarSign,
  Brain,
  Sparkles,
  Info,
} from 'lucide-react';

interface FeeEntry {
  id: string;
  state: string;
  service_category: string;
  service_type: string;
  minimum_value: string | null;
  suggested_value: string | null;
  percentage: string | null;
  year: number;
}

interface FeeTableResponse {
  count: number;
  results: FeeEntry[];
  available_states: string[];
  available_categories: string[];
}

interface CalculationResult {
  service_type: string;
  state: string;
  category: string;
  minimum_value: string;
  suggested_value: string;
  percentage: string;
  valor_causa: string;
  calculated_by_percentage: string;
  recommended_value: string;
}

interface AISuggestion {
  min_value: number;
  max_value: number;
  suggested_value: number;
  percentage: number;
  fee_type: 'fixed' | 'percentage' | 'mixed' | 'success';
  factors: string[];
  justification: string;
  oab_reference: number;
}

const CATEGORY_LABELS: Record<string, string> = {
  civel: 'Civel',
  criminal: 'Criminal',
  trabalhista: 'Trabalhista',
  tributario: 'Tributario',
  familia: 'Familia e Sucessoes',
  previdenciario: 'Previdenciario',
  administrativo: 'Administrativo',
  empresarial: 'Empresarial',
  consumidor: 'Consumidor',
  imobiliario: 'Imobiliario',
  ambiental: 'Ambiental',
  outros: 'Outros',
};

const formatCurrency = (value: string | number | null) => {
  if (value === null || value === undefined) return '-';
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num) || num === 0) return '-';
  return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
};

export default function HonoráriosPage() {
  const [selectedState, setSelectedState] = useState<string>('SP');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedFee, setSelectedFee] = useState<FeeEntry | null>(null);
  const [valorCausa, setValorCausa] = useState<string>('');
  const [calcResult, setCalcResult] = useState<CalculationResult | null>(null);
  const [aiDialogOpen, setAiDialogOpen] = useState(false);
  const [aiFormData, setAiFormData] = useState({
    specialty: 'civel',
    service_type: '',
    valor_causa: '',
    complexity: 'media',
    client_id: '',
  });

  const { data, isLoading } = useQuery<FeeTableResponse>({
    queryKey: ['oab-fees', selectedState, selectedCategory],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (selectedState) params.state = selectedState;
      if (selectedCategory) params.category = selectedCategory;
      const res = await api.get('/api/v1/processos/honorarios/tabela/', { params });
      return res.data;
    },
  });

  const calculateMutation = useMutation({
    mutationFn: async ({ feeId, valorCausa }: { feeId: string; valorCausa: string }) => {
      const res = await api.post('/api/v1/processos/honorarios/calcular/', {
        fee_id: feeId,
        valor_causa: valorCausa,
      });
      return res.data as CalculationResult;
    },
    onSuccess: (result) => {
      setCalcResult(result);
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || err?.response?.data?.detail || 'Erro ao processar solicitação');
    },
  });

  // Sugestão de Honorários com IA
  const aiSuggestMutation = useMutation({
    mutationFn: async (payload: {
      specialty: string;
      service_type: string;
      valor_causa: string;
      complexity: string;
      client_id?: string;
    }) => {
      const res = await api.post('/api/v1/processos/financeiro/copilot/sugerir-honorarios/', payload);
      return res.data.data as AISuggestion;
    },
    onSuccess: () => {
      setAiDialogOpen(true);
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || 'Erro ao gerar sugestão com IA');
    },
  });

  const handleCalculate = () => {
    if (!selectedFee) return;
    calculateMutation.mutate({
      feeId: selectedFee.id,
      valorCausa: valorCausa || '0',
    });
  };

  const handleAISuggest = () => {
    aiSuggestMutation.mutate({
      specialty: aiFormData.specialty,
      service_type: aiFormData.service_type || 'acao_simples',
      valor_causa: aiFormData.valor_causa || '0',
      complexity: aiFormData.complexity,
      client_id: aiFormData.client_id || undefined,
    });
  };

  const availableStates = data?.available_states || [];
  const availableCategories = data?.available_categories || [];
  const fees = data?.results || [];

  const getFeeTypeLabel = (type: string) => {
    switch (type) {
      case 'fixed': return 'Valor Fixo';
      case 'percentage': return 'Percentual';
      case 'mixed': return 'Misto';
      case 'success': return 'Êxito';
      default: return type;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Scale className="h-8 w-8" />
          Tabela OAB de Honorários
        </h1>
        <p className="text-muted-foreground">
          Consulte os valores de referencia da OAB por estado e categoria
        </p>
      </div>

      {/* Card de Sugestão com IA */}
      <Card className="border-primary/20 bg-gradient-to-r from-primary/5 to-primary/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-primary" />
            Copilot - Sugestão Inteligente de Honorários
          </CardTitle>
          <CardDescription>
            IA analisa caso, cliente e histórico para sugerir honorários justos e competitivos
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-5">
            <div className="md:col-span-2 space-y-1.5">
              <Label htmlFor="ai-specialty">Especialidade</Label>
              <select
                id="ai-specialty"
                value={aiFormData.specialty}
                onChange={(e) => setAiFormData({ ...aiFormData, specialty: e.target.value })}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="civel">Civel</option>
                <option value="criminal">Criminal</option>
                <option value="trabalhista">Trabalhista</option>
                <option value="tributario">Tributario</option>
                <option value="familia">Familia</option>
                <option value="empresarial">Empresarial</option>
                <option value="previdenciario">Previdenciario</option>
                <option value="administrativo">Administrativo</option>
              </select>
            </div>

            <div className="md:col-span-2 space-y-1.5">
              <Label htmlFor="ai-service-type">Tipo de Serviço</Label>
              <select
                id="ai-service-type"
                value={aiFormData.service_type}
                onChange={(e) => setAiFormData({ ...aiFormData, service_type: e.target.value })}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Selecione...</option>
                <option value="consulta">Consulta</option>
                <option value="peticao_inicial">Petição Inicial</option>
                <option value="contestacao">Contestação</option>
                <option value="acao_simples">Ação Simples</option>
                <option value="acao_complexa">Ação Complexa</option>
                <option value="recursos">Recursos</option>
              </select>
            </div>

            <div className="md:col-span-1 space-y-1.5">
              <Label htmlFor="ai-complexity">Complexidade</Label>
              <select
                id="ai-complexity"
                value={aiFormData.complexity}
                onChange={(e) => setAiFormData({ ...aiFormData, complexity: e.target.value })}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="baixa">Baixa</option>
                <option value="media">Média</option>
                <option value="alta">Alta</option>
              </select>
            </div>

            <div className="md:col-span-2 space-y-1.5">
              <Label htmlFor="ai-valor-causa">Valor da Causa (R$)</Label>
              <Input
                id="ai-valor-causa"
                type="number"
                placeholder="Ex: 50000"
                value={aiFormData.valor_causa}
                onChange={(e) => setAiFormData({ ...aiFormData, valor_causa: e.target.value })}
              />
            </div>

            <div className="md:col-span-2 space-y-1.5">
              <Label htmlFor="ai-client">Cliente (opcional)</Label>
              <Input
                id="ai-client"
                placeholder="ID do cliente"
                value={aiFormData.client_id}
                onChange={(e) => setAiFormData({ ...aiFormData, client_id: e.target.value })}
              />
            </div>

            <div className="md:col-span-1 flex items-end">
              <Button
                onClick={handleAISuggest}
                disabled={aiSuggestMutation.isPending}
                className="w-full gap-2"
              >
                <Sparkles className="h-4 w-4" />
                {aiSuggestMutation.isPending ? 'Analisando...' : 'Sugerir com IA'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Filtros
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            {/* State Selector */}
            <div className="space-y-1.5">
              <Label htmlFor="state-select">Estado (UF)</Label>
              <select
                id="state-select"
                value={selectedState}
                onChange={(e) => setSelectedState(e.target.value)}
                className="flex h-10 w-40 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="">Todos</option>
                {availableStates.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>

            {/* Category Selector */}
            <div className="space-y-1.5">
              <Label htmlFor="category-select">Categoria</Label>
              <select
                id="category-select"
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="flex h-10 w-56 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="">Todas</option>
                {availableCategories.map((c) => (
                  <option key={c} value={c}>
                    {CATEGORY_LABELS[c] || c}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Fee Table */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Tabela de Honorários</CardTitle>
              <CardDescription>
                {fees.length} {fees.length === 1 ? 'servico encontrado' : 'servicos encontrados'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-2">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} className="h-12 w-full" />
                  ))}
                </div>
              ) : fees.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">
                  Nenhum servico encontrado com os filtros selecionados.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-muted-foreground">
                        <th className="text-left py-2 pr-2">UF</th>
                        <th className="text-left py-2 pr-2">Categoria</th>
                        <th className="text-left py-2 pr-2">Servico</th>
                        <th className="text-right py-2 pr-2">Minimo</th>
                        <th className="text-right py-2 pr-2">Sugerido</th>
                        <th className="text-right py-2 pr-2">%</th>
                        <th className="text-center py-2">Calcular</th>
                      </tr>
                    </thead>
                    <tbody>
                      {fees.map((fee) => (
                        <tr
                          key={fee.id}
                          className={`border-b border-muted last:border-0 hover:bg-muted/50 transition-colors ${
                            selectedFee?.id === fee.id ? 'bg-primary/5' : ''
                          }`}
                        >
                          <td className="py-2 pr-2 font-medium">{fee.state}</td>
                          <td className="py-2 pr-2 text-muted-foreground">
                            {CATEGORY_LABELS[fee.service_category] || fee.service_category}
                          </td>
                          <td className="py-2 pr-2">{fee.service_type}</td>
                          <td className="py-2 pr-2 text-right">{formatCurrency(fee.minimum_value)}</td>
                          <td className="py-2 pr-2 text-right">{formatCurrency(fee.suggested_value)}</td>
                          <td className="py-2 pr-2 text-right">
                            {fee.percentage ? `${fee.percentage}%` : '-'}
                          </td>
                          <td className="py-2 text-center">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setSelectedFee(fee);
                                setCalcResult(null);
                              }}
                            >
                              <Calculator className="h-4 w-4" />
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Calculator */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calculator className="h-5 w-5" />
                Calculadora
              </CardTitle>
              <CardDescription>
                Selecione um servico na tabela e informe o valor da causa
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {selectedFee ? (
                <>
                  <div className="p-3 bg-muted rounded-lg text-sm space-y-1">
                    <p className="font-medium">{selectedFee.service_type}</p>
                    <p className="text-muted-foreground">
                      {selectedFee.state} - {CATEGORY_LABELS[selectedFee.service_category] || selectedFee.service_category}
                    </p>
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="valor-causa">Valor da Causa (R$)</Label>
                    <Input
                      id="valor-causa"
                      type="number"
                      placeholder="Ex: 50000"
                      value={valorCausa}
                      onChange={(e) => setValorCausa(e.target.value)}
                    />
                  </div>

                  <Button
                    className="w-full"
                    onClick={handleCalculate}
                    disabled={calculateMutation.isPending}
                  >
                    {calculateMutation.isPending ? 'Calculando...' : 'Calcular Honorários'}
                  </Button>

                  {/* Calculation Result */}
                  {calcResult && (
                    <div className="space-y-3 pt-2">
                      <div className="p-4 bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 rounded-lg space-y-2">
                        <div className="flex items-center gap-2 text-green-700 dark:text-green-400 font-medium">
                          <DollarSign className="h-4 w-4" />
                          Resultado
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <span className="text-muted-foreground">Valor Minimo:</span>
                          <span className="text-right font-medium">
                            {formatCurrency(calcResult.minimum_value)}
                          </span>

                          <span className="text-muted-foreground">Valor Sugerido:</span>
                          <span className="text-right font-medium">
                            {formatCurrency(calcResult.suggested_value)}
                          </span>

                          {parseFloat(calcResult.percentage) > 0 && (
                            <>
                              <span className="text-muted-foreground">
                                Por Percentual ({calcResult.percentage}%):
                              </span>
                              <span className="text-right font-medium">
                                {formatCurrency(calcResult.calculated_by_percentage)}
                              </span>
                            </>
                          )}

                          <div className="col-span-2 border-t pt-2 mt-1">
                            <div className="flex justify-between items-center">
                              <span className="font-medium text-green-700 dark:text-green-400">
                                Valor Recomendado:
                              </span>
                              <span className="text-lg font-bold text-green-700 dark:text-green-400">
                                {formatCurrency(calcResult.recommended_value)}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-muted-foreground text-sm text-center py-6">
                  Clique no icone de calculadora em um servico da tabela para iniciar o calculo.
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Dialog de Sugestão com IA */}
      <Dialog open={aiDialogOpen} onOpenChange={setAiDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-primary" />
              Sugestão de Honorários - IA
            </DialogTitle>
            <DialogDescription>
              Análise inteligente baseada em caso, cliente e histórico
            </DialogDescription>
          </DialogHeader>
          {aiSuggestMutation.data && (
            <div className="space-y-4">
              {/* Faixa Sugerida */}
              <div className="grid grid-cols-3 gap-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-xs text-muted-foreground flex items-center gap-1">
                      <Info className="h-3 w-3" />
                      Mínimo Sugerido
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-lg font-bold text-green-600">
                      {formatCurrency(aiSuggestMutation.data.min_value)}
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-xs text-muted-foreground">Valor Recomendado</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-xl font-bold text-primary">
                      {formatCurrency(aiSuggestMutation.data.suggested_value)}
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-xs text-muted-foreground">Máximo Sugerido</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-lg font-bold text-orange-600">
                      {formatCurrency(aiSuggestMutation.data.max_value)}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Tipo e Percentual */}
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline">
                  Tipo: {getFeeTypeLabel(aiSuggestMutation.data.fee_type)}
                </Badge>
                {aiSuggestMutation.data.percentage > 0 && (
                  <Badge variant="secondary">
                    Percentual sugerido: {aiSuggestMutation.data.percentage}%
                  </Badge>
                )}
                <Badge variant="outline">
                  Referência OAB: {formatCurrency(aiSuggestMutation.data.oab_reference)}
                </Badge>
              </div>

              {/* Fatores */}
              {aiSuggestMutation.data.factors.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-sm font-medium flex items-center gap-2">
                    <Sparkles className="h-4 w-4" />
                    Fatores Considerados
                  </h4>
                  <ul className="text-sm text-muted-foreground list-disc list-inside space-y-1">
                    {aiSuggestMutation.data.factors.map((f, i) => (
                      <li key={i}>{f}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Justificativa */}
              {aiSuggestMutation.data.justification && (
                <div className="space-y-2">
                  <h4 className="text-sm font-medium">Justificativa da IA</h4>
                  <p className="text-sm text-muted-foreground bg-muted p-3 rounded">
                    {aiSuggestMutation.data.justification}
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
