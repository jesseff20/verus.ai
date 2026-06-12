'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import {
  Scale,
  Plus,
  Search,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  Clock,
  FolderOpen,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import api from '@/lib/api';

interface LegalCase {
  id: string;
  numero_processo: string;
  titulo: string;
  especialidade: string;
  especialidade_display: string;
  status: string;
  status_display: string;
  fase_display: string;
  cliente_nome: string;
  parte_contraria: string;
  tribunal: string;
  vara_juizo: string;
  valor_causa: string | null;
  advogado_nome: string | null;
  data_distribuicao: string | null;
  total_prazos_pendentes: number;
  total_tarefas_pendentes: number;
  created_at: string;
  updated_at: string;
  // Fase 4
  active_flow_id: string | null;
  active_flow_status: string | null;
}

interface PaginatedResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: LegalCase[];
}

const statusConfig: Record<string, { label: string; color: string }> = {
  ativo: { label: 'Em Curso', color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' },
  aguardando: { label: 'Aguardando', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' },
  suspenso: { label: 'Suspenso', color: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200' },
  encerrado: { label: 'Encerrado', color: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200' },
  arquivado: { label: 'Arquivado', color: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400' },
  ganho: { label: 'Procedente', color: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200' },
  perdido: { label: 'Improcedente', color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' },
  acordo: { label: 'Acordo / Transação', color: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200' },
};

const especialidadeConfig: Record<string, string> = {
  administrativo: 'Administrativo',
  tributario: 'Tributário Municipal',
  divida_ativa: 'Dívida Ativa',
  civel: 'Cível',
  ambiental: 'Ambiental',
  urbanismo: 'Urbanismo e Uso do Solo',
  licitacoes: 'Licitações e Contratos',
  previdenciario: 'Previdenciário',
  constitucional: 'Constitucional',
  outros: 'Outros',
};

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('pt-BR');
}

function formatCurrency(value: string | null): string {
  if (!value) return '—';
  const num = parseFloat(value);
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(num);
}

export default function ProcessosPage() {
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [especialidadeFilter, setEspecialidadeFilter] = useState<string>('all');

  // Debounce search: só dispara API após 400ms de inatividade
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(searchInput);
    }, 400);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const { data, isLoading, error } = useQuery({
    queryKey: ['casos', search, statusFilter, especialidadeFilter],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      if (statusFilter && statusFilter !== 'all') params.status = statusFilter;
      if (especialidadeFilter && especialidadeFilter !== 'all') params.especialidade = especialidadeFilter;

      const response = await api.get<PaginatedResponse>('/api/v1/processos/', { params });
      return response.data;
    },
  });

  const { data: statsData } = useQuery({
    queryKey: ['casos-stats'],
    queryFn: async () => {
      const response = await api.get('/api/v1/processos/stats/');
      return response.data;
    },
  });

  const casos = data?.results || [];

  return (
    <div className="space-y-6 pb-20 sm:pb-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight flex items-center gap-2">
            <Scale className="h-7 w-7 sm:h-8 sm:w-8" />
            Processos Jurídicos
          </h1>
          <p className="text-muted-foreground text-sm sm:text-base">
            Gerencie os processos da procuradoria e acompanhe o andamento processual
          </p>
        </div>
        <Button asChild className="hidden sm:inline-flex">
          <Link href="/dashboard/processos/novo">
            <Plus className="h-4 w-4 mr-2" />
            Novo Processo
          </Link>
        </Button>
      </div>

      {/* Stats Cards */}
      {statsData && (
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total de Processos</CardTitle>
              <FolderOpen className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statsData.total_casos}</div>
              <p className="text-xs text-muted-foreground">{statsData.casos_ativos} em curso</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Prazos Pendentes</CardTitle>
              <Clock className="h-4 w-4 text-yellow-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statsData.prazos_pendentes}</div>
              <p className="text-xs text-muted-foreground">{statsData.prazos_proximos_7_dias} nos próximos 7 dias</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Prazos Atrasados</CardTitle>
              <AlertTriangle className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{statsData.prazos_atrasados}</div>
              <p className="text-xs text-muted-foreground">Requerem atenção imediata</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Processos Encerrados</CardTitle>
              <CheckCircle2 className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {statsData.casos_encerrados ?? 0}
              </div>
              <p className="text-xs text-muted-foreground">Encerrados / ganhos / perdidos</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filtros */}
      <Card>
        <CardHeader>
          <CardTitle>Processos</CardTitle>
          <CardDescription>{data?.count ?? 0} processos encontrados</CardDescription>
        </CardHeader>
        <CardContent>
          {/* Search bar - sticky on mobile */}
          <div className="sticky top-0 z-10 bg-card pb-3 -mt-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar por número, parte, título..."
                className="pl-9 text-[16px] sm:text-sm"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
              />
            </div>
          </div>

          {/* Filter chips - horizontal scroll on mobile */}
          <div className="flex gap-2 mb-4 overflow-x-auto pb-2 -mx-1 px-1 scrollbar-hide">
            {[
              { value: 'all', label: 'Todos' },
              { value: 'ativo', label: 'Em Curso' },
              { value: 'aguardando', label: 'Aguardando' },
              { value: 'suspenso', label: 'Suspenso' },
              { value: 'encerrado', label: 'Encerrado' },
              { value: 'ganho', label: 'Procedente' },
              { value: 'perdido', label: 'Improcedente' },
              { value: 'acordo', label: 'Acordo / Transação' },
              { value: 'arquivado', label: 'Arquivado' },
            ].map((item) => (
              <button
                key={item.value}
                type="button"
                onClick={() => setStatusFilter(item.value)}
                className={`inline-flex items-center whitespace-nowrap rounded-full px-3 py-1.5 text-xs font-medium transition-colors shrink-0 min-h-[36px] ${
                  statusFilter === item.value
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          {/* Specialty filter - hidden on mobile, dropdown on desktop */}
          <div className="hidden sm:flex gap-3 mb-4">
            <Select value={especialidadeFilter} onValueChange={setEspecialidadeFilter}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Especialidade" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas</SelectItem>
                {Object.entries(especialidadeConfig).map(([value, label]) => (
                  <SelectItem key={value} value={value}>{label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Specialty chips on mobile */}
          <div className="sm:hidden flex gap-2 mb-4 overflow-x-auto pb-2 -mx-1 px-1 scrollbar-hide">
            {[{ value: 'all', label: 'Todas' }, ...Object.entries(especialidadeConfig).map(([value, label]) => ({ value, label }))].map((item) => (
              <button
                key={item.value}
                type="button"
                onClick={() => setEspecialidadeFilter(item.value)}
                className={`inline-flex items-center whitespace-nowrap rounded-full px-3 py-1.5 text-xs font-medium transition-colors shrink-0 min-h-[36px] ${
                  especialidadeFilter === item.value
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : error ? (
            <div className="flex items-center justify-center py-12 text-destructive gap-2">
              <AlertTriangle className="h-5 w-5" />
              <span>Erro ao carregar processos</span>
            </div>
          ) : casos.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground gap-3">
              <Scale className="h-12 w-12 opacity-30" />
              <p className="text-sm">Nenhum processo encontrado</p>
              <Button asChild size="sm" variant="outline">
                <Link href="/dashboard/processos/novo">
                  <Plus className="h-4 w-4 mr-2" />
                  Cadastrar primeiro processo
                </Link>
              </Button>
            </div>
          ) : (
            <>
              {/* Mobile card view */}
              <div className="sm:hidden space-y-3">
                {casos.map((caso) => {
                  const statusCfg = statusConfig[caso.status] || { label: caso.status_display, color: 'bg-gray-100 text-gray-800' };
                  return (
                    <Link
                      key={caso.id}
                      href={`/dashboard/processos/${caso.id}`}
                      className="block border rounded-lg p-4 hover:bg-accent/50 active:bg-accent/70 transition-colors touch-manipulation"
                    >
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <p className="font-medium text-sm leading-snug flex-1 min-w-0">{caso.titulo}</p>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium shrink-0 ${statusCfg.color}`}>
                          {statusCfg.label}
                        </span>
                      </div>

                      <p className="text-xs text-muted-foreground mb-2">{caso.cliente_nome}</p>

                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant="outline" className="text-[10px]">
                          {caso.especialidade_display}
                        </Badge>
                        {caso.total_prazos_pendentes > 0 && (
                          <Badge className="bg-yellow-100 text-yellow-800 text-[10px]">
                            {caso.total_prazos_pendentes} prazo{caso.total_prazos_pendentes !== 1 ? 's' : ''}
                          </Badge>
                        )}
                        {caso.numero_processo && (
                          <span className="text-[10px] text-muted-foreground font-mono">{caso.numero_processo}</span>
                        )}
                      </div>
                    </Link>
                  );
                })}
              </div>

              {/* Desktop table view */}
              <div className="hidden sm:block overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Caso</TableHead>
                      <TableHead>Parte / Ente</TableHead>
                      <TableHead>Especialidade</TableHead>
                      <TableHead>Tribunal / Vara</TableHead>
                      <TableHead>Prazos</TableHead>
                      <TableHead>Fluxo</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Distribuído em</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {casos.map((caso) => {
                      const statusCfg = statusConfig[caso.status] || { label: caso.status_display, color: 'bg-gray-100 text-gray-800' };
                      return (
                        <TableRow key={caso.id} className="cursor-pointer hover:bg-accent/50">
                          <TableCell>
                            <Link href={`/dashboard/processos/${caso.id}`} className="block">
                              <p className="font-medium text-sm">{caso.titulo}</p>
                              {caso.numero_processo && (
                                <p className="text-xs text-muted-foreground font-mono">{caso.numero_processo}</p>
                              )}
                            </Link>
                          </TableCell>
                          <TableCell>
                            <p className="text-sm">{caso.cliente_nome}</p>
                            {caso.parte_contraria && (
                              <p className="text-xs text-muted-foreground">x {caso.parte_contraria}</p>
                            )}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className="text-xs">
                              {caso.especialidade_display}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <p className="text-xs">{caso.tribunal || '—'}</p>
                            {caso.vara_juizo && (
                              <p className="text-xs text-muted-foreground truncate max-w-[150px]">{caso.vara_juizo}</p>
                            )}
                          </TableCell>
                          <TableCell>
                            {caso.total_prazos_pendentes > 0 ? (
                              <Badge className="bg-yellow-100 text-yellow-800 text-xs">
                                {caso.total_prazos_pendentes} prazo{caso.total_prazos_pendentes !== 1 ? 's' : ''}
                              </Badge>
                            ) : (
                              <span className="text-xs text-muted-foreground">—</span>
                            )}
                          </TableCell>
                          <TableCell>
                            {caso.active_flow_status === 'running' ? (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                                <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                                Em fluxo
                              </span>
                            ) : caso.active_flow_status === 'completed' ? (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                                Concluído
                              </span>
                            ) : (
                              <span className="text-xs text-muted-foreground">—</span>
                            )}
                          </TableCell>
                          <TableCell>
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${statusCfg.color}`}>
                              {statusCfg.label}
                            </span>
                          </TableCell>
                          <TableCell className="text-xs text-muted-foreground">
                            {formatDate(caso.data_distribuicao)}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* FAB - Floating Action Button for mobile */}
      <Link
        href="/dashboard/processos/novo"
        className="sm:hidden fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg hover:bg-primary/90 active:scale-95 transition-transform touch-manipulation"
      >
        <Plus className="h-6 w-6" />
      </Link>
    </div>
  );
}
