'use client';

import { useState } from 'react';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DollarSign,
  Calculator,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Save,
  Eye,
  Receipt,
  TrendingUp,
  Copy,
  Barcode,
} from 'lucide-react';
import {
  useCourtFees,
  useCourtFeeSummary,
  useCalculateCourtFee,
  useCreateCourtFee,
  useMarkFeePaid,
  type CourtFeeGuide,
} from '@/hooks/use-court-fees';

const formatCurrency = (value: number) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);

const TRIBUNAIS = [
  { value: 'TJSP', label: 'TJSP - Tribunal de Justiça de São Paulo' },
  { value: 'TJRJ', label: 'TJRJ - Tribunal de Justiça do Rio de Janeiro' },
  { value: 'TJMG', label: 'TJMG - Tribunal de Justiça de Minas Gerais' },
  { value: 'TJRS', label: 'TJRS - Tribunal de Justiça do Rio Grande do Sul' },
  { value: 'TJPR', label: 'TJPR - Tribunal de Justiça do Paraná' },
  { value: 'TJSC', label: 'TJSC - Tribunal de Justiça de Santa Catarina' },
  { value: 'TJBA', label: 'TJBA - Tribunal de Justiça da Bahia' },
  { value: 'TJPE', label: 'TJPE - Tribunal de Justiça de Pernambuco' },
  { value: 'TJCE', label: 'TJCE - Tribunal de Justiça do Ceará' },
  { value: 'TJGO', label: 'TJGO - Tribunal de Justiça de Goiás' },
  { value: 'TJDF', label: 'TJDF - Tribunal de Justiça do Distrito Federal' },
  { value: 'TRF1', label: 'TRF1 - Tribunal Regional Federal da 1a Região' },
  { value: 'TRF2', label: 'TRF2 - Tribunal Regional Federal da 2a Região' },
  { value: 'TRF3', label: 'TRF3 - Tribunal Regional Federal da 3a Região' },
  { value: 'TRF4', label: 'TRF4 - Tribunal Regional Federal da 4a Região' },
  { value: 'TRF5', label: 'TRF5 - Tribunal Regional Federal da 5a Região' },
  { value: 'TST', label: 'TST - Tribunal Superior do Trabalho' },
  { value: 'STJ', label: 'STJ - Superior Tribunal de Justiça' },
  { value: 'STF', label: 'STF - Supremo Tribunal Federal' },
];

const ESTADOS = [
  'AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA',
  'PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO',
];

const TIPOS_CUSTAS = [
  { value: 'custas_iniciais', label: 'Custas Iniciais' },
  { value: 'custas_recursais', label: 'Custas Recursais' },
  { value: 'preparo', label: 'Preparo' },
  { value: 'porte_remessa', label: 'Porte de Remessa e Retorno' },
  { value: 'diligencia', label: 'Diligência' },
  { value: 'pericia', label: 'Perícia' },
  { value: 'outras', label: 'Outras' },
];

const STATUS_MAP: Record<string, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline'; className: string; icon: React.ReactNode }> = {
  pending: { label: 'Pendente', variant: 'outline', className: 'border-yellow-500 text-yellow-700 bg-yellow-50', icon: <Clock className="h-3 w-3" /> },
  paid: { label: 'Pago', variant: 'outline', className: 'border-green-500 text-green-700 bg-green-50', icon: <CheckCircle2 className="h-3 w-3" /> },
  overdue: { label: 'Vencida', variant: 'destructive', className: '', icon: <AlertTriangle className="h-3 w-3" /> },
  exempt: { label: 'Isenta', variant: 'secondary', className: '', icon: null },
  waived: { label: 'Dispensada', variant: 'outline', className: 'border-blue-500 text-blue-700 bg-blue-50', icon: null },
};

function StatusBadge({ status }: { status: string }) {
  const config = STATUS_MAP[status];
  if (!config) return <Badge variant="outline">{status}</Badge>;
  return (
    <Badge variant={config.variant} className={`${config.className} gap-1`}>
      {config.icon}
      {config.label}
    </Badge>
  );
}

function BarcodeDisplay({ barcode }: { barcode: string }) {
  const handleCopy = () => {
    navigator.clipboard.writeText(barcode);
    toast.success('Código de barras copiado!');
  };

  return (
    <div className="rounded-lg border bg-muted/30 p-3">
      <div className="flex items-center gap-2 mb-2">
        <Barcode className="h-4 w-4 text-muted-foreground" />
        <span className="text-xs font-medium text-muted-foreground">Código de Barras</span>
      </div>
      <div className="flex items-center gap-2">
        <code className="flex-1 text-xs font-mono bg-background border rounded px-2 py-1.5 break-all select-all">
          {barcode}
        </code>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="sm" onClick={handleCopy} className="flex-shrink-0" aria-label="Copiar código de barras">
              <Copy className="h-3.5 w-3.5" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Copiar código de barras</TooltipContent>
        </Tooltip>
      </div>
    </div>
  );
}

export default function CustasPage() {
  const { data: fees, isLoading: isLoadingFees } = useCourtFees();
  const { data: summary, isLoading: isLoadingSummary } = useCourtFeeSummary();
  const calculateMutation = useCalculateCourtFee();
  const createMutation = useCreateCourtFee();
  const markPaidMutation = useMarkFeePaid();

  // Calculator state
  const [court, setCourt] = useState('');
  const [state, setState] = useState('');
  const [feeType, setFeeType] = useState('');
  const [caseValue, setCaseValue] = useState('');
  const [calcResult, setCalcResult] = useState<{ amount: number; formula: string } | null>(null);

  // Pay dialog state
  const [payDialogOpen, setPayDialogOpen] = useState(false);
  const [payingFee, setPayingFee] = useState<CourtFeeGuide | null>(null);
  const [paymentDate, setPaymentDate] = useState('');

  // Detail dialog state
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [detailFee, setDetailFee] = useState<CourtFeeGuide | null>(null);

  const handleCalculate = () => {
    if (!court || !state || !feeType || !caseValue) {
      toast.error('Preencha todos os campos para calcular.');
      return;
    }
    calculateMutation.mutate(
      { court, state, fee_type: feeType, case_value: parseFloat(caseValue) },
      {
        onSuccess: (data) => {
          setCalcResult({ amount: data.calculated_amount, formula: data.calculation_formula });
          toast.success('Cálculo realizado com sucesso!');
        },
      }
    );
  };

  const handleSaveGuide = () => {
    if (!calcResult) return;
    createMutation.mutate(
      {
        court,
        state,
        fee_type: feeType,
        case_value: parseFloat(caseValue),
        calculated_amount: calcResult.amount,
        calculation_formula: calcResult.formula,
      },
      {
        onSuccess: () => {
          toast.success('Guia salva com sucesso!');
          setCalcResult(null);
          setCourt('');
          setState('');
          setFeeType('');
          setCaseValue('');
        },
      }
    );
  };

  const handleMarkPaid = () => {
    if (!payingFee || !paymentDate) return;
    markPaidMutation.mutate(
      { id: payingFee.id, payment_date: paymentDate },
      {
        onSuccess: () => {
          toast.success('Guia marcada como paga!');
          setPayDialogOpen(false);
          setPayingFee(null);
          setPaymentDate('');
        },
      }
    );
  };

  // Group fees by case for display
  const feesByCase = fees?.reduce((acc, fee) => {
    const caseKey = fee.case_titulo || fee.case || 'Sem caso';
    if (!acc[caseKey]) acc[caseKey] = [];
    acc[caseKey].push(fee);
    return acc;
  }, {} as Record<string, CourtFeeGuide[]>);

  // Compute totals
  const totalFees = summary?.total_pending != null && summary?.total_paid != null
    ? (summary.total_pending + summary.total_paid)
    : 0;
  const paidPercent = totalFees > 0 ? Math.round(((summary?.total_paid ?? 0) / totalFees) * 100) : 0;

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold">Guias de Custas</h1>
          <p className="text-muted-foreground">Gerencie custas processuais e calcule valores por tribunal</p>
        </div>

        {/* Stats Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {isLoadingSummary ? (
            Array.from({ length: 4 }).map((_, i) => (
              <Card key={i}>
                <CardHeader className="pb-2"><Skeleton className="h-4 w-24" /></CardHeader>
                <CardContent><Skeleton className="h-8 w-32" /></CardContent>
              </Card>
            ))
          ) : (
            <>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">Total em Custas</CardTitle>
                  <DollarSign className="h-4 w-4 text-blue-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {formatCurrency(totalFees)}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">Valor total registrado</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">Total Pago</CardTitle>
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-700">
                    {formatCurrency(summary?.total_paid ?? 0)}
                  </div>
                  <div className="mt-2">
                    <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                      <span>Progresso</span>
                      <span>{paidPercent}%</span>
                    </div>
                    <Progress value={paidPercent} className="h-1.5" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">Total Pendente</CardTitle>
                  <Clock className="h-4 w-4 text-yellow-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-yellow-700">
                    {formatCurrency(summary?.total_pending ?? 0)}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">Aguardando pagamento</p>
                </CardContent>
              </Card>
              <Card className={`${(summary?.overdue_count ?? 0) > 0 ? 'border-red-200 bg-red-50/30' : ''}`}>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">Vencidas</CardTitle>
                  <AlertTriangle className={`h-4 w-4 ${(summary?.overdue_count ?? 0) > 0 ? 'text-red-600' : 'text-muted-foreground'}`} />
                </CardHeader>
                <CardContent>
                  <div className={`text-2xl font-bold ${(summary?.overdue_count ?? 0) > 0 ? 'text-red-700' : 'text-muted-foreground'}`}>
                    {summary?.overdue_count ?? 0}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {(summary?.overdue_count ?? 0) > 0 ? 'Atenção: custas vencidas!' : 'Nenhuma custa vencida'}
                  </p>
                </CardContent>
              </Card>
            </>
          )}
        </div>

        {/* Calculator */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calculator className="h-5 w-5" />
              Calculadora de Custas
            </CardTitle>
            <CardDescription>Calcule o valor das custas por tribunal, estado e tipo</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <div className="space-y-2">
                <Label>Tribunal</Label>
                <Select value={court} onValueChange={setCourt}>
                  <SelectTrigger><SelectValue placeholder="Selecione o tribunal" /></SelectTrigger>
                  <SelectContent>
                    {TRIBUNAIS.map((t) => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Estado</Label>
                <Select value={state} onValueChange={setState}>
                  <SelectTrigger><SelectValue placeholder="UF" /></SelectTrigger>
                  <SelectContent>
                    {ESTADOS.map((uf) => (
                      <SelectItem key={uf} value={uf}>{uf}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Tipo de Custas</Label>
                <Select value={feeType} onValueChange={setFeeType}>
                  <SelectTrigger><SelectValue placeholder="Selecione o tipo" /></SelectTrigger>
                  <SelectContent>
                    {TIPOS_CUSTAS.map((t) => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Valor da Causa (R$)</Label>
                <Input
                  type="number"
                  placeholder="0,00"
                  value={caseValue}
                  onChange={(e) => setCaseValue(e.target.value)}
                />
              </div>
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-3">
              <Button onClick={handleCalculate} disabled={calculateMutation.isPending}>
                <Calculator className="mr-2 h-4 w-4" />
                {calculateMutation.isPending ? 'Calculando...' : 'Calcular'}
              </Button>
              {calcResult && (
                <Button variant="outline" onClick={handleSaveGuide} disabled={createMutation.isPending}>
                  <Save className="mr-2 h-4 w-4" />
                  {createMutation.isPending ? 'Salvando...' : 'Salvar Guia'}
                </Button>
              )}
            </div>

            {calcResult && (
              <div className="mt-4 rounded-lg border-2 border-green-200 bg-green-50/50 p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="rounded-full bg-green-100 p-1.5">
                    <DollarSign className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <span className="font-bold text-xl text-green-800">{formatCurrency(calcResult.amount)}</span>
                    <p className="text-xs text-muted-foreground">Valor calculado das custas</p>
                  </div>
                </div>
                <Separator className="my-2" />
                <p className="text-sm text-muted-foreground">
                  <span className="font-medium">Fórmula:</span> {calcResult.formula}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Fees by Case */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Receipt className="h-5 w-5" />
                  Guias Cadastradas
                </CardTitle>
                <CardDescription>
                  {fees?.length ?? 0} guia(s) registrada(s)
                  {feesByCase ? ` em ${Object.keys(feesByCase).length} caso(s)` : ''}
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {isLoadingFees ? (
              <div className="space-y-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : !fees || fees.length === 0 ? (
              <div className="text-center py-12">
                <Receipt className="h-10 w-10 text-muted-foreground/40 mx-auto mb-3" />
                <p className="text-muted-foreground mb-1">Nenhuma guia de custas cadastrada.</p>
                <p className="text-xs text-muted-foreground">Use a calculadora acima para criar sua primeira guia.</p>
              </div>
            ) : feesByCase ? (
              <div className="space-y-6">
                {Object.entries(feesByCase).map(([caseName, caseFees]) => {
                  const caseTotal = caseFees.reduce((sum, f) => sum + f.calculated_amount, 0);
                  const casePaid = caseFees.filter(f => f.payment_status === 'paid').reduce((sum, f) => sum + f.calculated_amount, 0);
                  const hasPending = caseFees.some(f => f.payment_status === 'pending' || f.payment_status === 'overdue');

                  return (
                    <div key={caseName} className="rounded-lg border">
                      {/* Case header */}
                      <div className="flex items-center justify-between px-4 py-3 bg-muted/30 border-b">
                        <div className="flex items-center gap-3">
                          <div className="font-medium text-sm">{caseName}</div>
                          <Badge variant="outline" className="text-xs">
                            {caseFees.length} guia(s)
                          </Badge>
                        </div>
                        <div className="flex items-center gap-3 text-sm">
                          <span className="text-muted-foreground">Total:</span>
                          <span className="font-bold">{formatCurrency(caseTotal)}</span>
                          {casePaid > 0 && (
                            <Badge variant="outline" className="border-green-500 text-green-700 bg-green-50 text-xs gap-1">
                              <CheckCircle2 className="h-3 w-3" />
                              {formatCurrency(casePaid)} pago
                            </Badge>
                          )}
                        </div>
                      </div>
                      {/* Fees table */}
                      <div className="overflow-x-auto">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Tipo Custas</TableHead>
                              <TableHead>Tribunal/UF</TableHead>
                              <TableHead className="text-right">Valor</TableHead>
                              <TableHead>Vencimento</TableHead>
                              <TableHead>Status</TableHead>
                              <TableHead>Cod. Barras</TableHead>
                              <TableHead className="text-right">Ações</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {caseFees.map((fee) => (
                              <TableRow key={fee.id}>
                                <TableCell>
                                  <span className="font-medium text-sm">
                                    {fee.fee_type_display || fee.fee_type}
                                  </span>
                                </TableCell>
                                <TableCell>
                                  <Badge variant="secondary" className="font-mono text-xs">
                                    {fee.court}/{fee.state}
                                  </Badge>
                                </TableCell>
                                <TableCell className="text-right font-bold tabular-nums">
                                  {formatCurrency(fee.calculated_amount)}
                                </TableCell>
                                <TableCell>
                                  {fee.due_date ? (
                                    <span className={`text-sm ${
                                      fee.payment_status === 'overdue' ? 'text-red-700 font-medium' : 'text-muted-foreground'
                                    }`}>
                                      {new Date(fee.due_date).toLocaleDateString('pt-BR')}
                                    </span>
                                  ) : (
                                    <span className="text-muted-foreground text-sm">---</span>
                                  )}
                                </TableCell>
                                <TableCell>
                                  <StatusBadge status={fee.payment_status} />
                                </TableCell>
                                <TableCell>
                                  {fee.barcode ? (
                                    <Tooltip>
                                      <TooltipTrigger asChild>
                                        <Button
                                          variant="ghost"
                                          size="sm"
                                          className="font-mono text-xs h-7 px-2 max-w-[100px] truncate"
                                          onClick={() => {
                                            navigator.clipboard.writeText(fee.barcode);
                                            toast.success('Código copiado!');
                                          }}
                                        >
                                          <Copy className="h-3 w-3 mr-1 flex-shrink-0" />
                                          {fee.barcode.slice(0, 10)}...
                                        </Button>
                                      </TooltipTrigger>
                                      <TooltipContent>Clique para copiar: {fee.barcode}</TooltipContent>
                                    </Tooltip>
                                  ) : (
                                    <span className="text-muted-foreground text-xs">---</span>
                                  )}
                                </TableCell>
                                <TableCell className="text-right">
                                  <div className="flex justify-end gap-1">
                                    {(fee.payment_status === 'pending' || fee.payment_status === 'overdue') && (
                                      <Tooltip>
                                        <TooltipTrigger asChild>
                                          <Button
                                            variant={fee.payment_status === 'overdue' ? 'default' : 'outline'}
                                            size="sm"
                                            className={`gap-1 ${fee.payment_status === 'overdue' ? 'bg-green-600 hover:bg-green-700' : ''}`}
                                            onClick={() => {
                                              setPayingFee(fee);
                                              setPaymentDate(new Date().toISOString().split('T')[0]);
                                              setPayDialogOpen(true);
                                            }}
                                          >
                                            <CheckCircle2 className="h-3 w-3" />
                                            <span className="hidden md:inline">Marcar Pago</span>
                                          </Button>
                                        </TooltipTrigger>
                                        <TooltipContent>Marcar como pago</TooltipContent>
                                      </Tooltip>
                                    )}
                                    <Tooltip>
                                      <TooltipTrigger asChild>
                                        <Button
                                          variant="ghost"
                                          size="sm"
                                          onClick={() => {
                                            setDetailFee(fee);
                                            setDetailDialogOpen(true);
                                          }}
                                        >
                                          <Eye className="h-3.5 w-3.5" />
                                        </Button>
                                      </TooltipTrigger>
                                      <TooltipContent>Ver detalhes</TooltipContent>
                                    </Tooltip>
                                  </div>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : null}
          </CardContent>
        </Card>

        {/* Pay Dialog */}
        <Dialog open={payDialogOpen} onOpenChange={setPayDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Marcar como Pago</DialogTitle>
              <DialogDescription>
                Confirme o pagamento da guia de custas informando a data.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              {payingFee && (
                <div className="rounded-lg border bg-muted/30 p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Caso</span>
                    <span className="text-sm font-medium">{payingFee.case_titulo || payingFee.case}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Tipo</span>
                    <span className="text-sm">{payingFee.fee_type_display || payingFee.fee_type}</span>
                  </div>
                  <Separator />
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Valor</span>
                    <span className="text-lg font-bold text-green-700">{formatCurrency(payingFee.calculated_amount)}</span>
                  </div>
                  {payingFee.barcode && (
                    <>
                      <Separator />
                      <BarcodeDisplay barcode={payingFee.barcode} />
                    </>
                  )}
                </div>
              )}
              <div className="space-y-2">
                <Label>Data de Pagamento</Label>
                <Input
                  type="date"
                  value={paymentDate}
                  onChange={(e) => setPaymentDate(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setPayDialogOpen(false)}>
                Cancelar
              </Button>
              <Button onClick={handleMarkPaid} disabled={markPaidMutation.isPending} className="bg-green-600 hover:bg-green-700">
                <CheckCircle2 className="mr-2 h-4 w-4" />
                {markPaidMutation.isPending ? 'Salvando...' : 'Confirmar Pagamento'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Detail Dialog */}
        <Dialog open={detailDialogOpen} onOpenChange={setDetailDialogOpen}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Detalhes da Guia</DialogTitle>
              <DialogDescription>Informações completas da guia de custas processuais.</DialogDescription>
            </DialogHeader>
            {detailFee && (
              <div className="space-y-4">
                {/* Amount highlight */}
                <div className="rounded-lg border-2 border-blue-200 bg-blue-50/50 p-4 text-center">
                  <p className="text-xs text-muted-foreground mb-1">Valor das Custas</p>
                  <p className="text-2xl font-bold">{formatCurrency(detailFee.calculated_amount)}</p>
                  <div className="mt-2">
                    <StatusBadge status={detailFee.payment_status} />
                  </div>
                </div>

                <div className="space-y-3 text-sm">
                  <div className="grid grid-cols-2 gap-2">
                    <span className="text-muted-foreground">Caso:</span>
                    <span className="font-medium">{detailFee.case_titulo || detailFee.case}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <span className="text-muted-foreground">Tipo:</span>
                    <span>{detailFee.fee_type_display || detailFee.fee_type}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <span className="text-muted-foreground">Tribunal:</span>
                    <Badge variant="secondary" className="w-fit font-mono text-xs">{detailFee.court}</Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <span className="text-muted-foreground">Estado:</span>
                    <span>{detailFee.state}</span>
                  </div>

                  <Separator />

                  <div className="grid grid-cols-2 gap-2">
                    <span className="text-muted-foreground">Valor da Causa:</span>
                    <span>{detailFee.case_value != null ? formatCurrency(detailFee.case_value) : '---'}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <span className="text-muted-foreground">Fórmula:</span>
                    <span className="text-xs">{detailFee.calculation_formula || '---'}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <span className="text-muted-foreground">Vencimento:</span>
                    <span className={detailFee.payment_status === 'overdue' ? 'text-red-700 font-medium' : ''}>
                      {detailFee.due_date ? new Date(detailFee.due_date).toLocaleDateString('pt-BR') : '---'}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <span className="text-muted-foreground">Data Pagamento:</span>
                    <span>
                      {detailFee.payment_date
                        ? new Date(detailFee.payment_date).toLocaleDateString('pt-BR')
                        : '---'}
                    </span>
                  </div>

                  {detailFee.barcode && (
                    <>
                      <Separator />
                      <BarcodeDisplay barcode={detailFee.barcode} />
                    </>
                  )}

                  {detailFee.notes && (
                    <>
                      <Separator />
                      <div>
                        <span className="text-muted-foreground text-xs font-medium">Observações</span>
                        <p className="mt-1 text-sm bg-muted/30 rounded p-2">{detailFee.notes}</p>
                      </div>
                    </>
                  )}
                </div>

                {/* Quick pay action in detail */}
                {(detailFee.payment_status === 'pending' || detailFee.payment_status === 'overdue') && (
                  <>
                    <Separator />
                    <Button
                      className="w-full bg-green-600 hover:bg-green-700 gap-2"
                      onClick={() => {
                        setDetailDialogOpen(false);
                        setPayingFee(detailFee);
                        setPaymentDate(new Date().toISOString().split('T')[0]);
                        setPayDialogOpen(true);
                      }}
                    >
                      <CheckCircle2 className="h-4 w-4" />
                      Marcar como Pago
                    </Button>
                  </>
                )}
              </div>
            )}
            <DialogFooter>
              <Button variant="outline" onClick={() => setDetailDialogOpen(false)}>Fechar</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </TooltipProvider>
  );
}
