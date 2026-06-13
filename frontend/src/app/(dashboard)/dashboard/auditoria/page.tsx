'use client';

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { useAuditLogs, useAuditStats, useAuditUserActivity, type AuditFilters, type AuditLogEntry } from '@/hooks/use-audit';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Eye,
  Shield,
  Activity,
  Users,
  Clock,
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  Bot,
  User,
  Plug,
  AlertTriangle,
  Lock,
  LogIn,
  LogOut,
  FileText,
  Briefcase,
  Calendar,
  Brain,
  Cpu,
  Zap,
  ChevronDown,
  ChevronUp,
  ShieldAlert,
  MonitorSmartphone,
  KeyRound,
  TrendingUp,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';

// ─── Constants ───────────────────────────────────────────────────────────────

const actionBadgeConfig: Record<string, { className: string; label: string }> = {
  create: { className: 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300', label: 'Criação' },
  update: { className: 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300', label: 'Atualização' },
  delete: { className: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300', label: 'Exclusão' },
  read: { className: 'bg-gray-100 text-gray-800 dark:bg-gray-950 dark:text-gray-300', label: 'Leitura' },
  login: { className: 'bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300', label: 'Login' },
  logout: { className: 'bg-purple-100 text-purple-600 dark:bg-purple-950 dark:text-purple-400', label: 'Logout' },
  login_failed: { className: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300', label: 'Falha Login' },
  submit: { className: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-950 dark:text-yellow-300', label: 'Submissão' },
  approve: { className: 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300', label: 'Aprovação' },
  reject: { className: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300', label: 'Rejeição' },
  generate: { className: 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300', label: 'Geração' },
  download: { className: 'bg-gray-100 text-gray-800 dark:bg-gray-950 dark:text-gray-300', label: 'Download' },
  sign: { className: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300', label: 'Assinatura' },
  password_change: { className: 'bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-300', label: 'Senha' },
  config_change: { className: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-950 dark:text-yellow-300', label: 'Config' },
};

const ACTION_OPTIONS = [
  { value: 'create', label: 'Criação' },
  { value: 'read', label: 'Leitura' },
  { value: 'update', label: 'Atualização' },
  { value: 'delete', label: 'Exclusão' },
  { value: 'login', label: 'Login' },
  { value: 'logout', label: 'Logout' },
  { value: 'login_failed', label: 'Falha Login' },
  { value: 'submit', label: 'Submissão' },
  { value: 'approve', label: 'Aprovação' },
  { value: 'generate', label: 'Geração' },
  { value: 'download', label: 'Download' },
  { value: 'sign', label: 'Assinatura' },
];

const METHOD_OPTIONS = [
  { value: 'GET', label: 'GET' },
  { value: 'POST', label: 'POST' },
  { value: 'PUT', label: 'PUT' },
  { value: 'PATCH', label: 'PATCH' },
  { value: 'DELETE', label: 'DELETE' },
];

const CHART_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];

// ─── Helpers ─────────────────────────────────────────────────────────────────

const formatDateTime = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const formatNumber = (n: number) => n.toLocaleString('pt-BR');

function detectUserType(entry: AuditLogEntry): 'human' | 'ai' | 'api' {
  const email = entry.user_email?.toLowerCase() || '';
  if (email.includes('agent') || email.includes('bot') || email.includes('ia') || email.includes('sistema')) return 'ai';
  if (email.includes('api') || email.includes('integracao') || email.includes('webhook')) return 'api';
  return 'human';
}

function getMethodFromAction(action: string): string {
  switch (action) {
    case 'create': case 'login': case 'submit': case 'generate': case 'sign': return 'POST';
    case 'update': case 'approve': case 'reject': return 'PUT';
    case 'delete': return 'DELETE';
    default: return 'GET';
  }
}

function getEndpointFromEntry(entry: AuditLogEntry): string {
  const type = entry.entity_type?.toLowerCase() || 'unknown';
  const action = entry.action;
  if (action === 'login' || action === 'logout' || action === 'login_failed') return '/api/v1/auth/token/';
  return `/api/v1/${type}/`;
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function ActionBadge({ action }: { action: string }) {
  const config = actionBadgeConfig[action] || {
    className: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300',
    label: action,
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${config.className}`}>
      {config.label}
    </span>
  );
}

function UserTypeBadge({ type }: { type: 'human' | 'ai' | 'api' }) {
  const cfg = {
    human: { icon: User, label: 'Humano', className: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-800' },
    ai: { icon: Bot, label: 'Agente IA', className: 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950 dark:text-purple-300 dark:border-purple-800' },
    api: { icon: Plug, label: 'API', className: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-800' },
  }[type];
  const Icon = cfg.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium border ${cfg.className}`}>
      <Icon className="h-3 w-3" />
      {cfg.label}
    </span>
  );
}

function MethodBadge({ method }: { method: string }) {
  const colors: Record<string, string> = {
    GET: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300',
    POST: 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300',
    PUT: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300',
    PATCH: 'bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-300',
    DELETE: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300',
  };
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${colors[method] || colors.GET}`}>
      {method}
    </span>
  );
}

function SeverityBadge({ severity }: { severity: 'high' | 'medium' | 'low' }) {
  const cfg = {
    high: { label: 'Alto', className: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300' },
    medium: { label: 'Médio', className: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300' },
    low: { label: 'Baixo', className: 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300' },
  }[severity];
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${cfg.className}`}>
      {cfg.label}
    </span>
  );
}

function TokenTypeBadge({ type }: { type: string }) {
  const cfg: Record<string, { label: string; className: string }> = {
    'copilot': { label: 'Copilot', className: 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300' },
    'agent': { label: 'Agente', className: 'bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300' },
    'document_gen': { label: 'Doc Gen', className: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300' },
    'user_request': { label: 'Usuario', className: 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300' },
    'analysis': { label: 'Análise', className: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-950 dark:text-cyan-300' },
    'other': { label: 'Outro', className: 'bg-gray-100 text-gray-800 dark:bg-gray-950 dark:text-gray-300' },
  };
  const c = cfg[type] || cfg['other'];
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium ${c.className}`}>
      {c.label}
    </span>
  );
}

function EmptyState({ icon: Icon, title, description }: { icon: React.ElementType; title: string; description: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <Icon className="h-12 w-12 text-muted-foreground/40 mb-4" />
      <h3 className="text-lg font-medium text-muted-foreground">{title}</h3>
      <p className="text-sm text-muted-foreground/70 mt-1 max-w-md">{description}</p>
    </div>
  );
}

function TimelineEventIcon({ type }: { type: string }) {
  const icons: Record<string, { icon: React.ElementType; className: string }> = {
    document: { icon: FileText, className: 'bg-blue-100 text-blue-600 dark:bg-blue-950 dark:text-blue-400' },
    case: { icon: Briefcase, className: 'bg-green-100 text-green-600 dark:bg-green-950 dark:text-green-400' },
    deadline: { icon: Calendar, className: 'bg-amber-100 text-amber-600 dark:bg-amber-950 dark:text-amber-400' },
    login: { icon: LogIn, className: 'bg-purple-100 text-purple-600 dark:bg-purple-950 dark:text-purple-400' },
    logout: { icon: LogOut, className: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400' },
    create: { icon: FileText, className: 'bg-green-100 text-green-600 dark:bg-green-950 dark:text-green-400' },
    update: { icon: FileText, className: 'bg-blue-100 text-blue-600 dark:bg-blue-950 dark:text-blue-400' },
    delete: { icon: FileText, className: 'bg-red-100 text-red-600 dark:bg-red-950 dark:text-red-400' },
    generate: { icon: Brain, className: 'bg-purple-100 text-purple-600 dark:bg-purple-950 dark:text-purple-400' },
  };
  const cfg = icons[type] || icons.document;
  const Icon = cfg.icon;
  return (
    <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${cfg.className}`}>
      <Icon className="h-4 w-4" />
    </div>
  );
}

// ─── Helper: map action to timeline type ────────────────────────────────────

function actionToTimelineType(action: string): string {
  if (action === 'login' || action === 'login_failed') return 'login';
  if (action === 'logout') return 'logout';
  if (action === 'generate') return 'generate';
  if (action === 'create') return 'create';
  if (action === 'update') return 'update';
  if (action === 'delete') return 'delete';
  return 'document';
}

// ─── Tab: Access Logs ────────────────────────────────────────────────────────

function AccessLogsTab() {
  const [filters, setFilters] = useState<AuditFilters>({ page: 1, page_size: 20 });
  const [methodFilter, setMethodFilter] = useState<string>('');
  const [userTypeFilter, setUserTypeFilter] = useState<string>('');

  const { data: logsData, isLoading } = useAuditLogs(filters);
  const totalPages = logsData ? Math.ceil(logsData.count / (filters.page_size || 20)) : 0;

  const filteredResults = useMemo(() => {
    let results = logsData?.results || [];
    if (methodFilter) {
      results = results.filter((e) => getMethodFromAction(e.action) === methodFilter);
    }
    if (userTypeFilter) {
      results = results.filter((e) => detectUserType(e) === userTypeFilter);
    }
    return results;
  }, [logsData?.results, methodFilter, userTypeFilter]);

  return (
    <div className="space-y-4">
      {/* Filters */}
      <Card>
        <CardContent className="p-3 sm:p-4">
          <div className="flex flex-wrap gap-3">
            <Select
              value={filters.action || ''}
              onValueChange={(v) => setFilters((f) => ({ ...f, action: v === 'all' ? undefined : v || undefined, page: 1 }))}
            >
              <SelectTrigger className="w-full sm:w-[160px]">
                <SelectValue placeholder="Tipo de ação" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas as ações</SelectItem>
                {ACTION_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select
              value={methodFilter}
              onValueChange={(v) => setMethodFilter(v === 'all' ? '' : v)}
            >
              <SelectTrigger className="w-full sm:w-[130px]">
                <SelectValue placeholder="Método HTTP" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos</SelectItem>
                {METHOD_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select
              value={userTypeFilter}
              onValueChange={(v) => setUserTypeFilter(v === 'all' ? '' : v)}
            >
              <SelectTrigger className="w-full sm:w-[150px]">
                <SelectValue placeholder="Tipo usuário" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos</SelectItem>
                <SelectItem value="human">Humano</SelectItem>
                <SelectItem value="ai">Agente IA</SelectItem>
                <SelectItem value="api">API</SelectItem>
              </SelectContent>
            </Select>

            <Input
              type="date"
              className="w-full sm:w-[150px]"
              value={filters.date_from || ''}
              onChange={(e) => setFilters((f) => ({ ...f, date_from: e.target.value || undefined, page: 1 }))}
            />
            <Input
              type="date"
              className="w-full sm:w-[150px]"
              value={filters.date_to || ''}
              onChange={(e) => setFilters((f) => ({ ...f, date_to: e.target.value || undefined, page: 1 }))}
            />
            <Input
              placeholder="Buscar..."
              className="w-full sm:w-[180px]"
              value={filters.search || ''}
              onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value || undefined, page: 1 }))}
            />
            <Button
              variant="outline"
              size="sm"
              onClick={() => { setFilters({ page: 1, page_size: 20 }); setMethodFilter(''); setUserTypeFilter(''); }}
            >
              Limpar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-4 space-y-3">
              {[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-12 w-full" />)}
            </div>
          ) : filteredResults.length === 0 ? (
            <EmptyState icon={Eye} title="Nenhum registro encontrado" description="Ajuste os filtros para ver os logs de acesso." />
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Usuario</TableHead>
                      <TableHead>Tipo</TableHead>
                      <TableHead>Ação</TableHead>
                      <TableHead>Método</TableHead>
                      <TableHead className="hidden md:table-cell">Endpoint</TableHead>
                      <TableHead className="hidden lg:table-cell">IP</TableHead>
                      <TableHead className="hidden xl:table-cell">User-Agent</TableHead>
                      <TableHead>Data/Hora</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredResults.map((entry) => {
                      const userType = detectUserType(entry);
                      const method = getMethodFromAction(entry.action);
                      const endpoint = getEndpointFromEntry(entry);
                      return (
                        <TableRow key={entry.id}>
                          <TableCell>
                            <div className="flex flex-col gap-1">
                              <span className="text-sm font-medium">{entry.user_email || 'Anônimo'}</span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <UserTypeBadge type={userType} />
                          </TableCell>
                          <TableCell>
                            <ActionBadge action={entry.action} />
                          </TableCell>
                          <TableCell>
                            <MethodBadge method={method} />
                          </TableCell>
                          <TableCell className="hidden md:table-cell">
                            <span className="text-xs font-mono text-muted-foreground">{endpoint}</span>
                          </TableCell>
                          <TableCell className="hidden lg:table-cell">
                            <span className="text-xs font-mono">{entry.ip_address || '-'}</span>
                          </TableCell>
                          <TableCell className="hidden xl:table-cell">
                            <span className="text-xs text-muted-foreground truncate max-w-[200px] block">
                              {(entry.metadata as Record<string, string>)?.user_agent || 'N/D'}
                            </span>
                          </TableCell>
                          <TableCell>
                            <span className="text-xs whitespace-nowrap">{formatDateTime(entry.created_at)}</span>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>

              {totalPages > 1 && (
                <div className="flex items-center justify-between px-4 py-3 border-t">
                  <span className="text-sm text-muted-foreground">{logsData?.count ?? 0} registros</span>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" disabled={(filters.page || 1) <= 1}
                      onClick={() => setFilters((f) => ({ ...f, page: (f.page || 1) - 1 }))} aria-label="Página anterior">
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <span className="text-sm">{filters.page || 1} / {totalPages}</span>
                    <Button variant="outline" size="sm" disabled={(filters.page || 1) >= totalPages}
                      onClick={() => setFilters((f) => ({ ...f, page: (f.page || 1) + 1 }))} aria-label="Próxima página">
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ─── Tab: Token Usage ────────────────────────────────────────────────────────

interface TokenUsageStats {
  today: { total_tokens: number; total_cost: number; count: number; total_input: number; total_output: number };
  week: { total_tokens: number; total_cost: number; count: number; total_input: number; total_output: number };
  month: { total_tokens: number; total_cost: number; count: number; total_input: number; total_output: number };
  all_time: { total_tokens: number; total_cost: number; count: number; total_input: number; total_output: number };
  by_provider: Array<{ model_provider: string; total_tokens: number; total_cost: number; count: number }>;
  by_usage_type: Array<{ usage_type: string; total_tokens: number; total_cost: number; count: number }>;
  by_user: Array<{ user__email: string; total_tokens: number; total_cost: number; count: number }>;
  timeline: Array<{ date: string; total_tokens: number; total_cost: number; count: number }>;
}

interface TokenUsageEntry {
  id: string;
  user?: string;
  user_email?: string;
  model_provider: string;
  provider_display?: string;
  model_name: string;
  usage_type: string;
  usage_type_display?: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost_estimate: string;
  description: string;
  created_at: string;
}

function TokenUsageTab() {
  const [modelFilter, setModelFilter] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');

  const { data: tokenStats, isLoading: isLoadingStats } = useQuery<TokenUsageStats>({
    queryKey: ['token-usage-stats'],
    queryFn: async () => {
      const res = await api.get('/api/v1/core/token-usage/stats/');
      return res.data;
    },
  });

  const { data: tokenListRaw, isLoading: isLoadingList } = useQuery<TokenUsageEntry[]>({
    queryKey: ['token-usage-list'],
    queryFn: async () => {
      const res = await api.get('/api/v1/core/token-usage/', { params: { page_size: 50 } });
      return res.data?.results || res.data || [];
    },
  });

  const tokenList = tokenListRaw || [];

  const todayTokens = tokenStats?.today?.total_tokens || 0;
  const weekTokens = tokenStats?.week?.total_tokens || 0;
  const monthTokens = tokenStats?.month?.total_tokens || 0;

  const dailyData = useMemo(() => {
    return (tokenStats?.timeline || []).map((entry) => ({
      date: entry.date ? new Date(entry.date).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }) : '',
      tokens: entry.total_tokens || 0,
    }));
  }, [tokenStats?.timeline]);

  const userTokens = useMemo(() => {
    return (tokenStats?.by_user || []).map((entry, index) => ({
      name: entry.user__email || 'Sem usuário',
      tokens: entry.total_tokens || 0,
      color: CHART_COLORS[index % CHART_COLORS.length],
    }));
  }, [tokenStats?.by_user]);

  const filteredUsage = useMemo(() => {
    let data = tokenList;
    if (modelFilter) data = data.filter((d) => d.model_provider === modelFilter);
    if (typeFilter) data = data.filter((d) => d.usage_type === typeFilter);
    return data;
  }, [tokenList, modelFilter, typeFilter]);

  const isLoading = isLoadingStats || isLoadingList;

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2 p-4">
            <CardTitle className="text-sm font-medium">Tokens Hoje</CardTitle>
            <Zap className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent className="p-4 pt-0">
            {isLoadingStats ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <>
                <div className="text-2xl font-bold">{formatNumber(todayTokens)}</div>
                <p className="text-xs text-muted-foreground">~R$ {(todayTokens * 0.000003).toFixed(2)} estimado</p>
              </>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2 p-4">
            <CardTitle className="text-sm font-medium">Tokens Semana</CardTitle>
            <TrendingUp className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent className="p-4 pt-0">
            {isLoadingStats ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <>
                <div className="text-2xl font-bold">{formatNumber(weekTokens)}</div>
                <p className="text-xs text-muted-foreground">~R$ {(weekTokens * 0.000003).toFixed(2)} estimado</p>
              </>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2 p-4">
            <CardTitle className="text-sm font-medium">Tokens Mes</CardTitle>
            <Brain className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent className="p-4 pt-0">
            {isLoadingStats ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <>
                <div className="text-2xl font-bold">{formatNumber(monthTokens)}</div>
                <p className="text-xs text-muted-foreground">~R$ {(monthTokens * 0.000003).toFixed(2)} estimado</p>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-4 grid-cols-1 lg:grid-cols-3">
        {/* Bar Chart - Tokens by Day */}
        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Tokens por Dia (ultimos 30 dias)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[280px]">
              {dailyData.length === 0 ? (
                <EmptyState icon={Cpu} title="Nenhum dado disponível" description="Dados de uso de tokens aparecerão aqui quando houver chamadas de IA." />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={dailyData}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis dataKey="date" tick={{ fontSize: 10 }} interval={4} />
                    <YAxis tick={{ fontSize: 10 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                    <Tooltip
                      contentStyle={{ fontSize: 12, borderRadius: 8 }}
                      formatter={(value: number) => [formatNumber(value), 'Tokens']}
                    />
                    <Bar dataKey="tokens" fill="#3b82f6" radius={[2, 2, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Pie Chart - Tokens by User */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Tokens por Usuario</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[280px]">
              {userTokens.length === 0 ? (
                <EmptyState icon={Users} title="Nenhum dado disponível" description="Dados de uso por usuário aparecerão aqui." />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={userTokens}
                      dataKey="tokens"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      innerRadius={40}
                      paddingAngle={2}
                      label={({ name, percent }) => `${(name as string).split('@')[0]} ${(percent * 100).toFixed(0)}%`}
                      labelLine={false}
                    >
                      {userTokens.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: number) => [formatNumber(value), 'Tokens']} />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Table */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <CardTitle className="text-sm font-medium">Uso Detalhado por Requisição</CardTitle>
            <div className="flex gap-2">
              <Select value={modelFilter} onValueChange={(v) => setModelFilter(v === 'all' ? '' : v)}>
                <SelectTrigger className="w-[160px] h-8 text-xs">
                  <SelectValue placeholder="Modelo" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos modelos</SelectItem>
                  <SelectItem value="openai">OpenAI</SelectItem>
                  <SelectItem value="watsonx">IBM WatsonX</SelectItem>
                  <SelectItem value="watsonx">WatsonX</SelectItem>
                </SelectContent>
              </Select>
              <Select value={typeFilter} onValueChange={(v) => setTypeFilter(v === 'all' ? '' : v)}>
                <SelectTrigger className="w-[150px] h-8 text-xs">
                  <SelectValue placeholder="Tipo" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos tipos</SelectItem>
                  <SelectItem value="copilot">Copilot</SelectItem>
                  <SelectItem value="agent">Agente</SelectItem>
                  <SelectItem value="document_gen">Doc Gen</SelectItem>
                  <SelectItem value="user_request">Usuario</SelectItem>
                  <SelectItem value="analysis">Análise</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoadingList ? (
            <div className="p-4 space-y-3">
              {[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-12 w-full" />)}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Usuario</TableHead>
                    <TableHead>Modelo</TableHead>
                    <TableHead>Tipo</TableHead>
                    <TableHead className="text-right">Input</TableHead>
                    <TableHead className="text-right">Output</TableHead>
                    <TableHead className="text-right">Custo Est.</TableHead>
                    <TableHead className="hidden md:table-cell">Descrição</TableHead>
                    <TableHead>Data/Hora</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredUsage.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                        Nenhum dado disponível
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredUsage.map((row) => (
                      <TableRow key={row.id}>
                        <TableCell className="text-sm font-medium">{row.user_email || 'Sistema'}</TableCell>
                        <TableCell>
                          <span className="text-xs font-mono bg-muted px-1.5 py-0.5 rounded">
                            {row.model_provider}/{row.model_name}
                          </span>
                        </TableCell>
                        <TableCell><TokenTypeBadge type={row.usage_type} /></TableCell>
                        <TableCell className="text-right text-xs font-mono">{formatNumber(row.input_tokens)}</TableCell>
                        <TableCell className="text-right text-xs font-mono">{formatNumber(row.output_tokens)}</TableCell>
                        <TableCell className="text-right text-xs font-mono text-amber-600 dark:text-amber-400">
                          R$ {Number(row.cost_estimate || 0).toFixed(4)}
                        </TableCell>
                        <TableCell className="hidden md:table-cell">
                          <span className="text-xs text-muted-foreground truncate max-w-[200px] block">{row.description}</span>
                        </TableCell>
                        <TableCell>
                          <span className="text-xs whitespace-nowrap">{formatDateTime(row.created_at)}</span>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ─── Tab: Activity Timeline ──────────────────────────────────────────────────

interface TimelineDay {
  date: string;
  label: string;
  events: Array<{
    id: string;
    time: string;
    type: string;
    title: string;
    detail: string;
    user: string;
  }>;
}

function ActivityTimelineTab() {
  const { data: timelineRaw, isLoading } = useQuery<AuditLogEntry[]>({
    queryKey: ['audit-timeline'],
    queryFn: async () => {
      const res = await api.get('/api/v1/core/auditoria/', { params: { page_size: 50 } });
      return res.data?.results || res.data || [];
    },
  });

  const timelineData = useMemo<TimelineDay[]>(() => {
    if (!timelineRaw || timelineRaw.length === 0) return [];

    const grouped: Record<string, TimelineDay> = {};
    const today = new Date().toISOString().split('T')[0];
    const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0];

    for (const entry of timelineRaw) {
      const dateStr = entry.created_at.split('T')[0];
      if (!grouped[dateStr]) {
        let label = dateStr;
        if (dateStr === today) label = 'Hoje';
        else if (dateStr === yesterday) label = 'Ontem';
        else {
          const d = new Date(dateStr + 'T00:00:00');
          label = d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
        }
        grouped[dateStr] = { date: dateStr, label, events: [] };
      }

      const time = new Date(entry.created_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
      const actionLabel = actionBadgeConfig[entry.action]?.label || entry.action_display || entry.action;

      grouped[dateStr].events.push({
        id: entry.id,
        time,
        type: actionToTimelineType(entry.action),
        title: `${actionLabel}: ${entry.entity_name || entry.entity_type || ''}`.trim(),
        detail: entry.description || `${entry.entity_type || ''} - ${entry.action_display || entry.action}`,
        user: entry.user_email || 'Anônimo',
      });
    }

    return Object.values(grouped).sort((a, b) => b.date.localeCompare(a.date));
  }, [timelineRaw]);

  const [expandedDays, setExpandedDays] = useState<Set<string>>(new Set());

  // Auto-expand first two days on data load
  useMemo(() => {
    if (timelineData.length > 0 && expandedDays.size === 0) {
      const first = timelineData.slice(0, 2).map((d) => d.date);
      setExpandedDays(new Set(first));
    }
  }, [timelineData]);

  const toggleDay = (date: string) => {
    setExpandedDays((prev) => {
      const next = new Set(prev);
      if (next.has(date)) next.delete(date);
      else next.add(date);
      return next;
    });
  };

  const [expandedEvent, setExpandedEvent] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => <Skeleton key={i} className="h-24 w-full" />)}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {timelineData.map((day) => {
        const isExpanded = expandedDays.has(day.date);
        return (
          <Card key={day.date}>
            <button
              className="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors rounded-t-lg"
              onClick={() => toggleDay(day.date)}
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                  <Calendar className="h-5 w-5 text-primary" />
                </div>
                <div className="text-left">
                  <h3 className="font-semibold text-sm">{day.label}</h3>
                  <p className="text-xs text-muted-foreground">{day.events.length} atividades</p>
                </div>
              </div>
              {isExpanded ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
            </button>

            {isExpanded && (
              <CardContent className="pt-0 pb-4 px-4">
                <div className="relative ml-5 border-l-2 border-muted pl-6 space-y-4">
                  {day.events.map((event) => {
                    const isEventExpanded = expandedEvent === event.id;
                    return (
                      <div key={event.id} className="relative">
                        {/* Timeline dot */}
                        <div className="absolute -left-[31px] top-1 w-3 h-3 rounded-full bg-background border-2 border-primary" />

                        <button
                          className="w-full text-left group"
                          onClick={() => setExpandedEvent(isEventExpanded ? null : event.id)}
                        >
                          <div className="flex items-start gap-3 p-2 rounded-lg hover:bg-muted/50 transition-colors">
                            <TimelineEventIcon type={event.type} />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-sm font-medium">{event.title}</span>
                                <span className="text-[10px] text-muted-foreground">{event.time}</span>
                              </div>
                              <p className="text-xs text-muted-foreground mt-0.5">{event.detail}</p>
                              {isEventExpanded && (
                                <div className="mt-2 p-2 bg-muted/50 rounded text-xs space-y-1">
                                  <p><span className="font-medium">Usuario:</span> {event.user}</p>
                                  <p><span className="font-medium">Tipo:</span> {event.type}</p>
                                  <p><span className="font-medium">Horario:</span> {event.time}</p>
                                </div>
                              )}
                            </div>
                            <span className="text-xs text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">
                              {event.user}
                            </span>
                          </div>
                        </button>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            )}
          </Card>
        );
      })}

      {timelineData.length === 0 && (
        <EmptyState icon={Activity} title="Nenhuma atividade registrada" description="As atividades do sistema aparecerao aqui quando houver interações." />
      )}
    </div>
  );
}

// ─── Tab: Security ───────────────────────────────────────────────────────────

function SecurityTab() {
  const { data: securityLogs, isLoading } = useQuery<AuditLogEntry[]>({
    queryKey: ['audit-security'],
    queryFn: async () => {
      const res = await api.get('/api/v1/core/auditoria/', { params: { page_size: 100 } });
      return res.data?.results || res.data || [];
    },
  });

  const securityData = useMemo(() => {
    const logs = securityLogs || [];

    // Failed logins: entries with action login_failed
    const failedLogins = logs
      .filter((e) => e.action === 'login_failed')
      .map((e) => ({
        id: e.id,
        user: e.user_email || 'desconhecido',
        ip: e.ip_address || 'N/D',
        timestamp: e.created_at,
        attempts: 1,
        blocked: false,
        userAgent: (e.metadata as Record<string, string>)?.user_agent || 'N/D',
      }));

    // Suspicious activity: derive from patterns
    const suspiciousActivity: Array<{
      id: string;
      type: string;
      severity: 'high' | 'medium' | 'low';
      description: string;
      user: string;
      ip: string;
      timestamp: string;
    }> = [];

    // Multiple failed logins
    if (failedLogins.length >= 3) {
      suspiciousActivity.push({
        id: 'sa-failed-logins',
        type: 'multiple_failed_logins',
        severity: 'high',
        description: `${failedLogins.length} tentativas de login falhadas detectadas`,
        user: failedLogins[0]?.user || 'N/D',
        ip: failedLogins[0]?.ip || 'N/D',
        timestamp: failedLogins[0]?.timestamp || new Date().toISOString(),
      });
    }

    // Unusual hours (access between 00:00-06:00)
    const unusualHours = logs.filter((e) => {
      const hour = new Date(e.created_at).getHours();
      return hour >= 0 && hour < 6 && (e.action === 'login' || e.action === 'create' || e.action === 'update');
    });
    for (const e of unusualHours.slice(0, 3)) {
      suspiciousActivity.push({
        id: `sa-hours-${e.id}`,
        type: 'unusual_hours',
        severity: 'medium',
        description: `Acesso em horario incomum (${new Date(e.created_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })})`,
        user: e.user_email || 'N/D',
        ip: e.ip_address || 'N/D',
        timestamp: e.created_at,
      });
    }

    // Mass downloads
    const downloads = logs.filter((e) => e.action === 'download');
    if (downloads.length >= 10) {
      suspiciousActivity.push({
        id: 'sa-mass-download',
        type: 'mass_download',
        severity: 'medium',
        description: `${downloads.length} downloads detectados no periodo`,
        user: downloads[0]?.user_email || 'N/D',
        ip: downloads[0]?.ip_address || 'N/D',
        timestamp: downloads[0]?.created_at || new Date().toISOString(),
      });
    }

    // Active sessions: recent logins without logout
    const loginUsers = new Map<string, AuditLogEntry>();
    const loggedOut = new Set<string>();
    for (const e of logs) {
      if (e.action === 'logout') loggedOut.add(e.user_email || '');
      if (e.action === 'login' && !loggedOut.has(e.user_email || '')) {
        if (!loginUsers.has(e.user_email || '')) loginUsers.set(e.user_email || '', e);
      }
    }
    const activeSessions = Array.from(loginUsers.values()).map((e) => ({
      id: e.id,
      user: e.user_email?.split('@')[0] || 'N/D',
      email: e.user_email || 'N/D',
      ip: e.ip_address || 'N/D',
      device: (e.metadata as Record<string, string>)?.user_agent || 'N/D',
      loginAt: e.created_at,
      lastActivity: e.created_at,
    }));

    // Permission changes
    const permissionChanges = logs
      .filter((e) => e.action === 'config_change' || e.action === 'password_change' || (e.entity_type || '').toLowerCase().includes('permission'))
      .map((e) => ({
        id: e.id,
        admin: e.user_email || 'Sistema',
        target: e.entity_name || 'N/D',
        change: e.description || `${e.action_display || e.action}`,
        timestamp: e.created_at,
      }));

    return { failedLogins, suspiciousActivity, activeSessions, permissionChanges };
  }, [securityLogs]);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardHeader className="pb-2 p-4"><Skeleton className="h-4 w-24" /></CardHeader>
              <CardContent className="p-4 pt-0"><Skeleton className="h-8 w-16" /></CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2 p-4">
            <CardTitle className="text-xs sm:text-sm font-medium">Falhas de Login</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold text-red-600 dark:text-red-400">{securityData.failedLogins.length}</div>
            <p className="text-xs text-muted-foreground">no periodo</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2 p-4">
            <CardTitle className="text-xs sm:text-sm font-medium">Alertas Suspeitos</CardTitle>
            <ShieldAlert className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold text-amber-600 dark:text-amber-400">{securityData.suspiciousActivity.length}</div>
            <p className="text-xs text-muted-foreground">requer atenção</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2 p-4">
            <CardTitle className="text-xs sm:text-sm font-medium">Sessões Ativas</CardTitle>
            <MonitorSmartphone className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">{securityData.activeSessions.length}</div>
            <p className="text-xs text-muted-foreground">usuarios conectados</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2 p-4">
            <CardTitle className="text-xs sm:text-sm font-medium">Mudanças de Permissão</CardTitle>
            <KeyRound className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold">{securityData.permissionChanges.length}</div>
            <p className="text-xs text-muted-foreground">no periodo</p>
          </CardContent>
        </Card>
      </div>

      {/* Suspicious Activity */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 text-amber-500" />
            Atividade Suspeita
          </CardTitle>
          <CardDescription>Alertas automaticos baseados em padroes anomalos</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {securityData.suspiciousActivity.length === 0 ? (
            <EmptyState icon={Shield} title="Nenhuma atividade suspeita" description="Nenhum padrao anomalo detectado no periodo." />
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Severidade</TableHead>
                    <TableHead>Descrição</TableHead>
                    <TableHead>Usuario</TableHead>
                    <TableHead className="hidden md:table-cell">IP</TableHead>
                    <TableHead>Data/Hora</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {securityData.suspiciousActivity.map((alert) => (
                    <TableRow key={alert.id}>
                      <TableCell><SeverityBadge severity={alert.severity} /></TableCell>
                      <TableCell className="text-sm">{alert.description}</TableCell>
                      <TableCell className="text-sm font-mono">{alert.user}</TableCell>
                      <TableCell className="hidden md:table-cell text-xs font-mono">{alert.ip}</TableCell>
                      <TableCell className="text-xs whitespace-nowrap">{formatDateTime(alert.timestamp)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Failed Logins */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Lock className="h-4 w-4 text-red-500" />
            Tentativas de Login Falhadas
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {securityData.failedLogins.length === 0 ? (
            <EmptyState icon={Lock} title="Nenhuma falha de login" description="Nenhuma tentativa de login falhada detectada." />
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Email</TableHead>
                    <TableHead>IP</TableHead>
                    <TableHead>Tentativas</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="hidden md:table-cell">User-Agent</TableHead>
                    <TableHead>Data/Hora</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {securityData.failedLogins.map((fl) => (
                    <TableRow key={fl.id}>
                      <TableCell className="text-sm font-mono">{fl.user}</TableCell>
                      <TableCell className="text-xs font-mono">{fl.ip}</TableCell>
                      <TableCell>
                        <span className={`text-sm font-bold ${fl.attempts >= 5 ? 'text-red-600 dark:text-red-400' : 'text-amber-600 dark:text-amber-400'}`}>
                          {fl.attempts}
                        </span>
                      </TableCell>
                      <TableCell>
                        {fl.blocked ? (
                          <Badge variant="destructive" className="text-[10px]">Bloqueado</Badge>
                        ) : (
                          <Badge variant="outline" className="text-[10px]">Ativo</Badge>
                        )}
                      </TableCell>
                      <TableCell className="hidden md:table-cell">
                        <span className="text-xs text-muted-foreground truncate max-w-[200px] block">{fl.userAgent}</span>
                      </TableCell>
                      <TableCell className="text-xs whitespace-nowrap">{formatDateTime(fl.timestamp)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Active Sessions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <MonitorSmartphone className="h-4 w-4 text-green-500" />
            Sessões Ativas
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {securityData.activeSessions.length === 0 ? (
            <EmptyState icon={MonitorSmartphone} title="Nenhuma sessão ativa" description="Nenhuma sessão ativa detectada." />
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Usuario</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>IP</TableHead>
                    <TableHead className="hidden md:table-cell">Dispositivo</TableHead>
                    <TableHead>Login</TableHead>
                    <TableHead>Ultima Atividade</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {securityData.activeSessions.map((session) => (
                    <TableRow key={session.id}>
                      <TableCell className="text-sm font-medium">{session.user}</TableCell>
                      <TableCell className="text-xs font-mono">{session.email}</TableCell>
                      <TableCell className="text-xs font-mono">{session.ip}</TableCell>
                      <TableCell className="hidden md:table-cell text-xs">{session.device}</TableCell>
                      <TableCell className="text-xs whitespace-nowrap">{formatDateTime(session.loginAt)}</TableCell>
                      <TableCell className="text-xs whitespace-nowrap">{formatDateTime(session.lastActivity)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Permission Changes */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <KeyRound className="h-4 w-4 text-blue-500" />
            Alterações de Permissão
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {securityData.permissionChanges.length === 0 ? (
            <EmptyState icon={KeyRound} title="Nenhuma alteração" description="Nenhuma alteração de permissão detectada no período." />
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Administrador</TableHead>
                    <TableHead>Usuário Alvo</TableHead>
                    <TableHead>Alteração</TableHead>
                    <TableHead>Data/Hora</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {securityData.permissionChanges.map((pc) => (
                    <TableRow key={pc.id}>
                      <TableCell className="text-sm font-medium">{pc.admin}</TableCell>
                      <TableCell className="text-sm">{pc.target}</TableCell>
                      <TableCell className="text-xs">{pc.change}</TableCell>
                      <TableCell className="text-xs whitespace-nowrap">{formatDateTime(pc.timestamp)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function AuditoriaPage() {
  const [activeTab, setActiveTab] = useState('access-logs');
  const { data: stats, isLoading: isLoadingStats } = useAuditStats();

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-lg sm:text-2xl md:text-3xl font-bold tracking-tight flex items-center gap-2">
          <Eye className="h-6 w-6 sm:h-8 sm:w-8" />
          Auditoria
        </h1>
        <p className="text-muted-foreground text-sm sm:text-base">
          Monitoramento completo de acessos, uso de IA, atividades e segurança
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        {isLoadingStats ? (
          [1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardHeader className="pb-2 p-3 sm:p-6"><Skeleton className="h-4 w-24" /></CardHeader>
              <CardContent className="p-3 sm:p-6 pt-0"><Skeleton className="h-8 w-16" /></CardContent>
            </Card>
          ))
        ) : (
          <>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2 p-3 sm:p-6">
                <CardTitle className="text-xs sm:text-sm font-medium">Total Registros</CardTitle>
                <Shield className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent className="p-3 sm:p-6 pt-0">
                <div className="text-xl sm:text-2xl font-bold">{stats?.total ?? 0}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2 p-3 sm:p-6">
                <CardTitle className="text-xs sm:text-sm font-medium">Ações Hoje</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent className="p-3 sm:p-6 pt-0">
                <div className="text-xl sm:text-2xl font-bold">{stats?.today ?? 0}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2 p-3 sm:p-6">
                <CardTitle className="text-xs sm:text-sm font-medium">Usuarios Ativos</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent className="p-3 sm:p-6 pt-0">
                <div className="text-xl sm:text-2xl font-bold">{stats?.active_users ?? 0}</div>
                <p className="text-[10px] sm:text-xs text-muted-foreground">ultimos 7 dias</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2 p-3 sm:p-6">
                <CardTitle className="text-xs sm:text-sm font-medium">Ultimas 24h</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent className="p-3 sm:p-6 pt-0">
                <div className="text-xl sm:text-2xl font-bold">{stats?.last_24h ?? 0}</div>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* Tabbed Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="access-logs" className="text-xs sm:text-sm gap-1">
            <Eye className="h-3.5 w-3.5 hidden sm:inline" />
            Acessos
          </TabsTrigger>
          <TabsTrigger value="token-usage" className="text-xs sm:text-sm gap-1">
            <Cpu className="h-3.5 w-3.5 hidden sm:inline" />
            Tokens IA
          </TabsTrigger>
          <TabsTrigger value="timeline" className="text-xs sm:text-sm gap-1">
            <Activity className="h-3.5 w-3.5 hidden sm:inline" />
            Timeline
          </TabsTrigger>
          <TabsTrigger value="security" className="text-xs sm:text-sm gap-1">
            <Shield className="h-3.5 w-3.5 hidden sm:inline" />
            Segurança
          </TabsTrigger>
        </TabsList>

        <TabsContent value="access-logs">
          <AccessLogsTab />
        </TabsContent>

        <TabsContent value="token-usage">
          <TokenUsageTab />
        </TabsContent>

        <TabsContent value="timeline">
          <ActivityTimelineTab />
        </TabsContent>

        <TabsContent value="security">
          <SecurityTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
