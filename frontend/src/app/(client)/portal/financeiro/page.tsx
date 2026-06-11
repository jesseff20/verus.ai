'use client';

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
  Loader2,
  AlertTriangle,
  Wallet,
  CalendarClock,
  Receipt,
} from 'lucide-react';

// ─── Types ──────────────────────────────────────────────────────────────────

interface FinancialEntry {
  id: string;
  descricao: string;
  caso_titulo: string;
  valor: number;
  vencimento: string;
  status: 'pendente' | 'pago' | 'vencido';
}

interface FinancialSummary {
  total_devido: number;
  total_pago: number;
  proximo_vencimento: string | null;
  movimentacoes: FinancialEntry[];
}

// ─── API ────────────────────────────────────────────────────────────────────

const portalApi = axios.create({
  baseURL: '',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

portalApi.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('client_portal_access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// ─── Helpers ────────────────────────────────────────────────────────────────

const formatCurrency = (value: number) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);

const formatDate = (dateStr: string | null): string => {
  if (!dateStr) return '\u2014';
  return new Date(dateStr).toLocaleDateString('pt-BR');
};

const STATUS_BADGE: Record<string, string> = {
  pendente: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300',
  pago: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300',
  vencido: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300',
};

const STATUS_LABEL: Record<string, string> = {
  pendente: 'Pendente',
  pago: 'Pago',
  vencido: 'Vencido',
};

// ─── Component ──────────────────────────────────────────────────────────────

export default function FinanceiroPage() {
  const { data, isLoading, error } = useQuery<FinancialSummary>({
    queryKey: ['client-portal-financeiro'],
    queryFn: async () => {
      const res = await portalApi.get('/api/v1/auth/client-portal/financeiro/');
      return res.data;
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

  const summary = useMemo(() => {
    if (!data) return null;
    return {
      totalDevido: data.total_pendente || data.total_devido || '0',
      totalPago: data.total_pago || '0',
      proximoVencimento: data.proximo_vencimento || null,
      movimentacoes: data.pendentes || data.movimentacoes || [],
    };
  }, [data]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight flex items-center gap-2">
          <DollarSign className="h-7 w-7 sm:h-8 sm:w-8" />
          Financeiro
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Acompanhe suas movimentações financeiras
        </p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <div className="flex items-center justify-center py-16 text-destructive gap-2">
          <AlertTriangle className="h-5 w-5" />
          <span>Erro ao carregar dados financeiros</span>
        </div>
      ) : !summary ? (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground gap-3">
          <Receipt className="h-12 w-12 opacity-30" />
          <p className="text-sm">Nenhuma movimentação encontrada</p>
        </div>
      ) : (
        <>
          {/* Stats Cards */}
          <div className="grid gap-3 grid-cols-1 sm:grid-cols-3">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                  <Wallet className="h-3.5 w-3.5" />
                  Total Devido
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">
                  {formatCurrency(summary.totalDevido)}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                  <DollarSign className="h-3.5 w-3.5" />
                  Total Pago
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {formatCurrency(summary.totalPago)}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                  <CalendarClock className="h-3.5 w-3.5" />
                  Próximo Vencimento
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatDate(summary.proximoVencimento)}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Invoices Table */}
          {summary.movimentacoes.length > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Movimentações</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Descrição</TableHead>
                        <TableHead>Caso</TableHead>
                        <TableHead className="text-right">Valor (R$)</TableHead>
                        <TableHead>Vencimento</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {summary.movimentacoes.map((mov) => (
                        <TableRow key={mov.id}>
                          <TableCell className="font-medium text-sm">
                            {mov.descricao}
                          </TableCell>
                          <TableCell className="text-sm text-muted-foreground">
                            {mov.caso_titulo}
                          </TableCell>
                          <TableCell className="text-right text-sm font-mono">
                            {formatCurrency(mov.valor)}
                          </TableCell>
                          <TableCell className="text-sm">
                            {formatDate(mov.vencimento)}
                          </TableCell>
                          <TableCell>
                            <Badge className={`text-[10px] px-1.5 py-0 ${STATUS_BADGE[mov.status] || ''}`}>
                              {STATUS_LABEL[mov.status] || mov.status}
                            </Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground gap-3">
              <Receipt className="h-12 w-12 opacity-30" />
              <p className="text-sm">Nenhuma movimentação encontrada</p>
            </div>
          )}

          {/* Disclaimer */}
          <p className="text-xs text-muted-foreground text-center italic">
            Para dúvidas sobre valores, entre em contato com seu advogado.
          </p>
        </>
      )}
    </div>
  );
}
