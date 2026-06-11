'use client';

import { useState, useMemo, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  AlertTriangle,
  Briefcase,
  TrendingUp,
  DollarSign,
  Clock,
  Users,
  Target,
  CalendarCheck,
  CalendarX,
  BarChart3,
  PieChart as PieChartIcon,
  Activity,
  Zap,
  Scale,
  Gavel,
  FileText,
  Award,
  Workflow,
  CheckCircle2,
  XCircle,
  Loader2,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

// ── Color palette ──

const COLORS = {
  primary: '#6366f1',
  secondary: '#8b5cf6',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#06b6d4',
  pink: '#ec4899',
  orange: '#f97316',
  lime: '#84cc16',
  blue: '#3b82f6',
};

const PIE_COLORS = [
  '#6366f1',
  '#8b5cf6',
  '#06b6d4',
  '#10b981',
  '#f59e0b',
  '#ef4444',
  '#ec4899',
  '#f97316',
  '#84cc16',
  '#3b82f6',
];

const STATUS_COLORS: Record<string, string> = {
  ativo: '#3b82f6',
  em_andamento: '#3b82f6',
  ganho: '#10b981',
  perdido: '#ef4444',
  acordo: '#f59e0b',
  arquivado: '#6b7280',
  encerrado: '#8b5cf6',
};

// ── Types ──

interface PortfolioData {
  total_cases: number;
  by_status: Record<string, number>;
  by_specialty: Record<string, number>;
  deadline_compliance: number;
  avg_duration_days: number;
  monthly_new_cases: Array<{ month: string; count: number }>;
}

interface KPIData {
  active_cases: number;
  deadline_compliance_pct: number;
  avg_resolution_days: number;
  new_cases_this_month?: number;
  new_cases_month?: number;
  overdue_deadlines?: number;
  deadlines_overdue?: number;
  upcoming_hearings?: number;
  cases_won?: number;
  cases_lost?: number;
  cases_settled?: number;
  deadlines_pending?: number;
  deadlines_completed?: number;
  total_deadlines?: number;
}

interface FinancialData {
  total_revenue: number;
  avg_honorarios: number;
  pending_payments: number;
  revenue_by_month: Array<{ month: string; revenue: number }>;
  revenue_by_type: Array<{ type: string; revenue: number }>;
}

interface StatsData {
  total: number;
  win_rate: number;
  avg_case_value: number;
  by_status: Record<string, number>;
  lawyers_hours: Array<{ name: string; hours: number }>;
  tasks_per_week: Array<{ week: string; completed: number }>;
  lawyer_performance: Array<{
    name: string;
    cases: number;
    deadlines: number;
    hours: number;
    docs: number;
    revenue: number;
  }>;
  deadlines_by_month: Array<{
    month: string;
    met: number;
    missed: number;
  }>;
  deadline_status: Record<string, number>;
}

// ── Fallback / sample data ──

const SAMPLE_PORTFOLIO: PortfolioData = {
  total_cases: 127,
  by_status: { ativo: 45, ganho: 38, perdido: 12, acordo: 22, arquivado: 10 },
  by_specialty: {
    Trabalhista: 35,
    Civil: 28,
    Criminal: 18,
    Tributario: 22,
    Empresarial: 14,
    Ambiental: 10,
  },
  deadline_compliance: 87,
  avg_duration_days: 245,
  monthly_new_cases: [
    { month: 'Jun', count: 8 },
    { month: 'Jul', count: 12 },
    { month: 'Ago', count: 9 },
    { month: 'Set', count: 15 },
    { month: 'Out', count: 11 },
    { month: 'Nov', count: 14 },
    { month: 'Dez', count: 7 },
    { month: 'Jan', count: 10 },
    { month: 'Fev', count: 13 },
    { month: 'Mar', count: 16 },
    { month: 'Abr', count: 11 },
    { month: 'Mai', count: 14 },
  ],
};

const SAMPLE_KPIS: KPIData = {
  active_cases: 45,
  deadline_compliance_pct: 87,
  avg_resolution_days: 180,
  new_cases_this_month: 14,
  overdue_deadlines: 3,
  upcoming_hearings: 8,
};

const SAMPLE_FINANCIAL: FinancialData = {
  total_revenue: 485000,
  avg_honorarios: 12500,
  pending_payments: 78000,
  revenue_by_month: [
    { month: 'Jun', revenue: 32000 },
    { month: 'Jul', revenue: 41000 },
    { month: 'Ago', revenue: 38000 },
    { month: 'Set', revenue: 45000 },
    { month: 'Out', revenue: 39000 },
    { month: 'Nov', revenue: 52000 },
    { month: 'Dez', revenue: 28000 },
    { month: 'Jan', revenue: 35000 },
    { month: 'Fev', revenue: 43000 },
    { month: 'Mar', revenue: 48000 },
    { month: 'Abr', revenue: 42000 },
    { month: 'Mai', revenue: 47000 },
  ],
  revenue_by_type: [
    { type: 'Trabalhista', revenue: 145000 },
    { type: 'Civil', revenue: 98000 },
    { type: 'Criminal', revenue: 72000 },
    { type: 'Tributario', revenue: 88000 },
    { type: 'Empresarial', revenue: 52000 },
    { type: 'Ambiental', revenue: 30000 },
  ],
};

const SAMPLE_STATS: Partial<StatsData> = {
  total: 127,
  win_rate: 76,
  avg_case_value: 38500,
  lawyers_hours: [
    { name: 'Dr. Silva', hours: 186 },
    { name: 'Dra. Santos', hours: 164 },
    { name: 'Dr. Oliveira', hours: 142 },
    { name: 'Dra. Costa', hours: 128 },
    { name: 'Dr. Pereira', hours: 98 },
  ],
  tasks_per_week: [
    { week: 'Sem 1', completed: 24 },
    { week: 'Sem 2', completed: 31 },
    { week: 'Sem 3', completed: 28 },
    { week: 'Sem 4', completed: 35 },
    { week: 'Sem 5', completed: 22 },
    { week: 'Sem 6', completed: 38 },
    { week: 'Sem 7', completed: 33 },
    { week: 'Sem 8', completed: 29 },
  ],
  lawyer_performance: [
    { name: 'Dr. Silva', cases: 90, deadlines: 95, hours: 85, docs: 80, revenue: 88 },
    { name: 'Dra. Santos', cases: 78, deadlines: 88, hours: 92, docs: 75, revenue: 82 },
    { name: 'Dr. Oliveira', cases: 85, deadlines: 72, hours: 78, docs: 90, revenue: 76 },
  ],
  deadlines_by_month: [
    { month: 'Jan', met: 18, missed: 2 },
    { month: 'Fev', met: 22, missed: 3 },
    { month: 'Mar', met: 25, missed: 1 },
    { month: 'Abr', met: 20, missed: 4 },
    { month: 'Mai', met: 28, missed: 2 },
    { month: 'Jun', met: 24, missed: 3 },
  ],
  deadline_status: {
    'No prazo': 68,
    Atrasado: 8,
    'Concluído': 42,
    Próximo: 12,
  },
};

// ── Utility ──

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat('pt-BR').format(value);
}

// ── Custom Tooltip ──

function CustomTooltip({
  active,
  payload,
  label,
  formatter,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
  formatter?: (v: number) => string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border bg-background/95 backdrop-blur-sm p-3 shadow-xl">
      {label && (
        <p className="text-sm font-medium text-foreground mb-1.5">{label}</p>
      )}
      {payload.map((entry, idx) => (
        <div key={idx} className="flex items-center gap-2 text-sm">
          <span
            className="w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-muted-foreground">{entry.name}:</span>
          <span className="font-semibold">
            {formatter ? formatter(entry.value) : formatNumber(entry.value)}
          </span>
        </div>
      ))}
    </div>
  );
}

// ── KPI Card ──

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: string;
  trendUp?: boolean;
  gradient: string;
}

function KPICard({
  title,
  value,
  subtitle,
  icon,
  trend,
  trendUp,
  gradient,
}: KPICardProps) {
  return (
    <Card className="relative overflow-hidden border-0 shadow-lg">
      <div
        className="absolute inset-0 opacity-10"
        style={{
          background: `linear-gradient(135deg, ${gradient.split(',')[0]} 0%, ${gradient.split(',')[1] || gradient.split(',')[0]} 100%)`,
        }}
      />
      <CardHeader className="flex flex-row items-center justify-between pb-2 relative">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <div
          className="h-10 w-10 rounded-xl flex items-center justify-center shadow-md"
          style={{
            background: `linear-gradient(135deg, ${gradient.split(',')[0]}, ${gradient.split(',')[1] || gradient.split(',')[0]})`,
          }}
        >
          {icon}
        </div>
      </CardHeader>
      <CardContent className="relative">
        <div className="text-3xl font-bold tracking-tight">{value}</div>
        {subtitle && (
          <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
        )}
        {trend && (
          <div
            className={`flex items-center gap-1 mt-2 text-xs font-medium ${trendUp ? 'text-emerald-600' : 'text-red-500'}`}
          >
            <TrendingUp
              className={`h-3 w-3 ${!trendUp ? 'rotate-180' : ''}`}
            />
            {trend}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Chart Card wrapper ──

function ChartCard({
  title,
  description,
  icon,
  children,
  className = '',
}: {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <Card
      className={`shadow-lg border-0 hover:shadow-xl transition-shadow duration-300 ${className}`}
    >
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          {icon}
          {title}
        </CardTitle>
        {description && (
          <CardDescription>{description}</CardDescription>
        )}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

// ── Loading skeleton for a chart card ──

function ChartSkeleton() {
  return (
    <Card className="shadow-lg border-0">
      <CardHeader className="pb-2">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="h-3 w-60 mt-1" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-[250px] w-full rounded-lg" />
      </CardContent>
    </Card>
  );
}

function KPISkeleton() {
  return (
    <Card className="shadow-lg border-0">
      <CardHeader className="pb-2">
        <Skeleton className="h-4 w-24" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-8 w-20" />
        <Skeleton className="h-3 w-32 mt-2" />
      </CardContent>
    </Card>
  );
}

// ── Calendar heatmap ──

function CalendarHeatmap({
  data,
}: {
  data: Array<{ date: string; value: number }>;
}) {
  const maxVal = Math.max(...data.map((d) => d.value), 1);

  function getColor(value: number) {
    if (value === 0) return 'bg-muted';
    const intensity = value / maxVal;
    if (intensity > 0.75) return 'bg-emerald-500';
    if (intensity > 0.5) return 'bg-emerald-400';
    if (intensity > 0.25) return 'bg-emerald-300';
    return 'bg-emerald-200';
  }

  // Generate 12 weeks x 7 days grid
  const weeks = 12;
  const days = 7;
  const dayLabels = ['Seg', '', 'Qua', '', 'Sex', '', 'Dom'];

  return (
    <div className="flex gap-1">
      <div className="flex flex-col gap-1 mr-1">
        {dayLabels.map((label, i) => (
          <div
            key={i}
            className="h-4 text-[10px] text-muted-foreground flex items-center"
          >
            {label}
          </div>
        ))}
      </div>
      {Array.from({ length: weeks }).map((_, weekIdx) => (
        <div key={weekIdx} className="flex flex-col gap-1">
          {Array.from({ length: days }).map((_, dayIdx) => {
            const dataIdx = weekIdx * days + dayIdx;
            const item = data[dataIdx];
            const value = item?.value ?? 0;
            return (
              <div
                key={dayIdx}
                className={`h-4 w-4 rounded-sm ${getColor(value)} transition-colors duration-200`}
                title={
                  item
                    ? `${item.date}: ${value} prazo(s)`
                    : 'Sem dados'
                }
              />
            );
          })}
        </div>
      ))}
    </div>
  );
}

// ── Generate sample heatmap data ──

function generateHeatmapData(): Array<{ date: string; value: number }> {
  const data: Array<{ date: string; value: number }> = [];
  const today = new Date();
  for (let i = 83; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    data.push({
      date: d.toISOString().slice(0, 10),
      value: Math.floor(Math.random() * 5),
    });
  }
  return data;
}

// ── Main Component ──

// ── Sample Data Warning Banner ──

function SampleDataBanner() {
  return (
    <Alert variant="default" className="mb-4 border-amber-300 bg-amber-50">
      <AlertTriangle className="h-4 w-4 text-amber-600" />
      <AlertTitle className="text-amber-800">Dados de Exemplo</AlertTitle>
      <AlertDescription className="text-amber-700">
        Os gráficos estão exibindo dados de demonstração. Execute os seeds de produção ou cadastre dados reais para visualizar métricas do seu escritório.
      </AlertDescription>
    </Alert>
  );
}

export default function RelatoriosPage() {
  const [activeTab, setActiveTab] = useState('portfolio');
  const [usingSampleData, setUsingSampleData] = useState(false);

  // Fetch data from all endpoints
  const { data: portfolioRaw, isLoading: loadingPortfolio } =
    useQuery<PortfolioData>({
      queryKey: ['reports', 'portfolio'],
      queryFn: async () => {
        const res = await api.get('/api/v1/processos/relatorios/portfolio/');
        return res.data;
      },
    });

  const { data: kpisRaw, isLoading: loadingKpis } = useQuery<KPIData>({
    queryKey: ['reports', 'kpis'],
    queryFn: async () => {
      const res = await api.get('/api/v1/processos/relatorios/kpis/');
      return res.data;
    },
  });

  const { data: financialRaw, isLoading: loadingFinancial } =
    useQuery<FinancialData>({
      queryKey: ['reports', 'financial'],
      queryFn: async () => {
        const res = await api.get(
          '/api/v1/processos/financeiro/dashboard/'
        );
        return res.data;
      },
    });

  const { data: statsRaw, isLoading: loadingStats } =
    useQuery<StatsData>({
      queryKey: ['reports', 'stats'],
      queryFn: async () => {
        const res = await api.get('/api/v1/processos/stats/');
        return res.data;
      },
    });

  // Detect sample data usage
  useEffect(() => {
    const isSample = !portfolioRaw || !kpisRaw || !financialRaw || !statsRaw;
    setUsingSampleData(isSample);
  }, [portfolioRaw, kpisRaw, financialRaw, statsRaw]);

  // Use real data or fallbacks
  const portfolio = portfolioRaw || SAMPLE_PORTFOLIO;
  const kpis = kpisRaw || SAMPLE_KPIS;
  const financial = financialRaw || SAMPLE_FINANCIAL;
  const stats = statsRaw || (SAMPLE_STATS as StatsData);

  // ── Derived chart data ──

  const specialtyPieData = useMemo(() => {
    const entries = Object.entries(portfolio.by_specialty || {});
    if (!entries.length) return Object.entries(SAMPLE_PORTFOLIO.by_specialty).map(([name, value]) => ({ name, value }));
    return entries.map(([name, value]) => ({ name, value }));
  }, [portfolio]);

  const statusBarData = useMemo(() => {
    const entries = Object.entries(portfolio.by_status || {});
    if (!entries.length) return Object.entries(SAMPLE_PORTFOLIO.by_status).map(([name, value]) => ({ name, value }));
    return entries.map(([name, value]) => ({ name, value }));
  }, [portfolio]);

  const monthlyLineData = useMemo(() => {
    const arr = portfolio.monthly_new_cases;
    if (!arr?.length) return SAMPLE_PORTFOLIO.monthly_new_cases;
    return arr;
  }, [portfolio]);

  const revenueAreaData = useMemo(() => {
    const arr = financial.revenue_by_month;
    if (!arr?.length) return SAMPLE_FINANCIAL.revenue_by_month;
    return arr;
  }, [financial]);

  const revenueByTypeData = useMemo(() => {
    const arr = financial.revenue_by_type;
    if (!arr?.length) return SAMPLE_FINANCIAL.revenue_by_type;
    return arr;
  }, [financial]);

  const lawyerHoursData = useMemo(() => {
    return stats.lawyers_hours?.length
      ? stats.lawyers_hours
      : SAMPLE_STATS.lawyers_hours!;
  }, [stats]);

  const tasksWeekData = useMemo(() => {
    return stats.tasks_per_week?.length
      ? stats.tasks_per_week
      : SAMPLE_STATS.tasks_per_week!;
  }, [stats]);

  const lawyerRadarData = useMemo(() => {
    return stats.lawyer_performance?.length
      ? stats.lawyer_performance
      : SAMPLE_STATS.lawyer_performance!;
  }, [stats]);

  const deadlinesByMonthData = useMemo(() => {
    return stats.deadlines_by_month?.length
      ? stats.deadlines_by_month
      : SAMPLE_STATS.deadlines_by_month!;
  }, [stats]);

  const deadlineStatusData = useMemo(() => {
    const raw = stats.deadline_status || SAMPLE_STATS.deadline_status!;
    return Object.entries(raw).map(([name, value]) => ({ name, value }));
  }, [stats]);

  const heatmapData = useMemo(() => generateHeatmapData(), []);

  // Radar data transform (subjects as rows)
  const radarSubjects = ['Casos', 'Prazos', 'Horas', 'Docs', 'Receita'];
  const radarChartData = useMemo(() => {
    return radarSubjects.map((subject, i) => {
      const keys = ['cases', 'deadlines', 'hours', 'docs', 'revenue'] as const;
      const row: Record<string, string | number> = { subject };
      lawyerRadarData.forEach((lawyer) => {
        row[lawyer.name] = lawyer[keys[i]];
      });
      return row;
    });
  }, [lawyerRadarData]);

  const isLoading =
    loadingPortfolio || loadingKpis || loadingFinancial || loadingStats;

  const winRate = stats.win_rate ?? SAMPLE_STATS.win_rate ?? 76;
  const avgCaseValue =
    stats.avg_case_value ?? SAMPLE_STATS.avg_case_value ?? 38500;
  const totalCases = portfolio.total_cases ?? SAMPLE_PORTFOLIO.total_cases;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          Relatórios
        </h1>
        <p className="text-muted-foreground mt-1">
          Painel completo com indicadores, financeiro, produtividade e prazos
        </p>
      </div>

      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="space-y-6"
      >
        <TabsList className="grid w-full grid-cols-5 lg:w-auto lg:inline-grid">
          <TabsTrigger value="portfolio" className="gap-1.5">
            <PieChartIcon className="h-4 w-4 hidden sm:block" />
            Portfolio
          </TabsTrigger>
          <TabsTrigger value="financeiro" className="gap-1.5">
            <DollarSign className="h-4 w-4 hidden sm:block" />
            Financeiro
          </TabsTrigger>
          <TabsTrigger value="produtividade" className="gap-1.5">
            <Activity className="h-4 w-4 hidden sm:block" />
            Produtividade
          </TabsTrigger>
          <TabsTrigger value="prazos" className="gap-1.5">
            <CalendarCheck className="h-4 w-4 hidden sm:block" />
            Prazos
          </TabsTrigger>
          <TabsTrigger value="fluxos" className="gap-1.5">
            <Workflow className="h-4 w-4 hidden sm:block" />
            Fluxos
          </TabsTrigger>
        </TabsList>

        {/* ════════════════════════════════════════════
            TAB 1: PORTFOLIO OVERVIEW
            ════════════════════════════════════════════ */}
        <TabsContent value="portfolio" className="space-y-6">
          {usingSampleData && !isLoading && <SampleDataBanner />}
          {/* KPI Cards */}
          {isLoading ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <KPISkeleton key={i} />
              ))}
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <KPICard
                title="Total de Casos"
                value={formatNumber(totalCases)}
                subtitle="processos cadastrados"
                icon={<Briefcase className="h-5 w-5 text-white" />}
                gradient="#6366f1,#8b5cf6"
              />
              <KPICard
                title="Taxa de Sucesso"
                value={`${winRate}%`}
                subtitle="casos ganhos ou acordo"
                icon={<Award className="h-5 w-5 text-white" />}
                trend="+3.2% vs mês anterior"
                trendUp
                gradient="#10b981,#06d6a0"
              />
              <KPICard
                title="Valor Médio"
                value={formatCurrency(avgCaseValue)}
                subtitle="por processo"
                icon={<Scale className="h-5 w-5 text-white" />}
                gradient="#f59e0b,#f97316"
              />
              <KPICard
                title="Casos Ativos"
                value={formatNumber(kpis.active_cases)}
                subtitle="em andamento"
                icon={<Gavel className="h-5 w-5 text-white" />}
                trend={`${kpis.new_cases_month ?? kpis.new_cases_this_month ?? 0} novos este mes`}
                trendUp
                gradient="#3b82f6,#06b6d4"
              />
            </div>
          )}

          {/* Charts row */}
          {isLoading ? (
            <div className="grid gap-6 lg:grid-cols-2">
              <ChartSkeleton />
              <ChartSkeleton />
            </div>
          ) : (
            <div className="grid gap-6 lg:grid-cols-2">
              {/* Pie: cases by specialty */}
              <ChartCard
                title="Casos por Especialidade"
                description="Distribuição do portfolio por área jurídica"
                icon={<PieChartIcon className="h-5 w-5 text-indigo-500" />}
              >
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={specialtyPieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        paddingAngle={4}
                        dataKey="value"
                        animationDuration={800}
                        stroke="none"
                      >
                        {specialtyPieData.map((_, idx) => (
                          <Cell
                            key={idx}
                            fill={PIE_COLORS[idx % PIE_COLORS.length]}
                          />
                        ))}
                      </Pie>
                      <Tooltip
                        content={({ active, payload }) => (
                          <CustomTooltip
                            active={active}
                            payload={payload?.map((p) => ({
                              name: String(p.name),
                              value: Number(p.value),
                              color: String(p.payload?.fill || '#666'),
                            }))}
                          />
                        )}
                      />
                      <Legend
                        verticalAlign="bottom"
                        height={36}
                        formatter={(value) => (
                          <span className="text-xs text-muted-foreground">
                            {value}
                          </span>
                        )}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </ChartCard>

              {/* Bar: cases by status */}
              <ChartCard
                title="Casos por Status"
                description="Situação atual dos processos"
                icon={<BarChart3 className="h-5 w-5 text-blue-500" />}
              >
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={statusBarData}
                      layout="vertical"
                      margin={{ left: 20 }}
                    >
                      <CartesianGrid
                        strokeDasharray="3 3"
                        horizontal={false}
                        stroke="hsl(var(--border))"
                      />
                      <XAxis type="number" tick={{ fontSize: 12 }} />
                      <YAxis
                        dataKey="name"
                        type="category"
                        width={90}
                        tick={{ fontSize: 12 }}
                      />
                      <Tooltip
                        content={({ active, payload, label }) => (
                          <CustomTooltip
                            active={active}
                            label={label}
                            payload={payload?.map((p) => ({
                              name: 'Casos',
                              value: Number(p.value),
                              color:
                                STATUS_COLORS[
                                  String(p.payload?.name || '')
                                ] || COLORS.primary,
                            }))}
                          />
                        )}
                      />
                      <Bar
                        dataKey="value"
                        radius={[0, 6, 6, 0]}
                        animationDuration={800}
                      >
                        {statusBarData.map((entry, idx) => (
                          <Cell
                            key={idx}
                            fill={
                              STATUS_COLORS[entry.name] ||
                              PIE_COLORS[idx % PIE_COLORS.length]
                            }
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </ChartCard>
            </div>
          )}

          {/* Line chart: new cases over 12 months */}
          {isLoading ? (
            <ChartSkeleton />
          ) : (
            <ChartCard
              title="Novos Casos - Últimos 12 Meses"
              description="Evolução mensal de novos processos"
              icon={<TrendingUp className="h-5 w-5 text-emerald-500" />}
            >
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={monthlyLineData}>
                    <defs>
                      <linearGradient
                        id="lineGradient"
                        x1="0"
                        y1="0"
                        x2="1"
                        y2="0"
                      >
                        <stop
                          offset="0%"
                          stopColor={COLORS.primary}
                          stopOpacity={1}
                        />
                        <stop
                          offset="100%"
                          stopColor={COLORS.info}
                          stopOpacity={1}
                        />
                      </linearGradient>
                    </defs>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="hsl(var(--border))"
                    />
                    <XAxis
                      dataKey="month"
                      tick={{ fontSize: 12 }}
                    />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip
                      content={({ active, payload, label }) => (
                        <CustomTooltip
                          active={active}
                          label={label}
                          payload={payload?.map((p) => ({
                            name: 'Novos casos',
                            value: Number(p.value),
                            color: COLORS.primary,
                          }))}
                        />
                      )}
                    />
                    <Line
                      type="monotone"
                      dataKey="count"
                      stroke="url(#lineGradient)"
                      strokeWidth={3}
                      dot={{
                        r: 5,
                        fill: COLORS.primary,
                        stroke: '#fff',
                        strokeWidth: 2,
                      }}
                      activeDot={{ r: 7 }}
                      animationDuration={800}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </ChartCard>
          )}
        </TabsContent>

        {/* ════════════════════════════════════════════
            TAB 2: FINANCIAL
            ════════════════════════════════════════════ */}
        <TabsContent value="financeiro" className="space-y-6">
          {usingSampleData && !isLoading && <SampleDataBanner />}
          {/* KPI Cards */}
          {isLoading ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <KPISkeleton key={i} />
              ))}
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <KPICard
                title="Receita Total"
                value={formatCurrency(financial.total_revenue)}
                subtitle="últimos 12 meses"
                icon={<DollarSign className="h-5 w-5 text-white" />}
                trend="+12.5% vs período anterior"
                trendUp
                gradient="#10b981,#06d6a0"
              />
              <KPICard
                title="Honorários Médio"
                value={formatCurrency(financial.avg_honorarios)}
                subtitle="por processo"
                icon={<FileText className="h-5 w-5 text-white" />}
                gradient="#6366f1,#8b5cf6"
              />
              <KPICard
                title="Pagamentos Pendentes"
                value={formatCurrency(financial.pending_payments)}
                subtitle="a receber"
                icon={<Clock className="h-5 w-5 text-white" />}
                gradient="#f59e0b,#f97316"
              />
            </div>
          )}

          {/* Area chart: revenue over months */}
          {isLoading ? (
            <ChartSkeleton />
          ) : (
            <ChartCard
              title="Receita Mensal"
              description="Evolução da receita nos últimos 12 meses"
              icon={<TrendingUp className="h-5 w-5 text-emerald-500" />}
            >
              <div className="h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={revenueAreaData}>
                    <defs>
                      <linearGradient
                        id="revenueGradient"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="5%"
                          stopColor={COLORS.success}
                          stopOpacity={0.3}
                        />
                        <stop
                          offset="95%"
                          stopColor={COLORS.success}
                          stopOpacity={0.02}
                        />
                      </linearGradient>
                    </defs>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="hsl(var(--border))"
                    />
                    <XAxis
                      dataKey="month"
                      tick={{ fontSize: 12 }}
                    />
                    <YAxis
                      tick={{ fontSize: 12 }}
                      tickFormatter={(v) =>
                        `${(v / 1000).toFixed(0)}k`
                      }
                    />
                    <Tooltip
                      content={({ active, payload, label }) => (
                        <CustomTooltip
                          active={active}
                          label={label}
                          payload={payload?.map((p) => ({
                            name: 'Receita',
                            value: Number(p.value),
                            color: COLORS.success,
                          }))}
                          formatter={formatCurrency}
                        />
                      )}
                    />
                    <Area
                      type="monotone"
                      dataKey="revenue"
                      stroke={COLORS.success}
                      strokeWidth={3}
                      fill="url(#revenueGradient)"
                      dot={{
                        r: 4,
                        fill: COLORS.success,
                        stroke: '#fff',
                        strokeWidth: 2,
                      }}
                      activeDot={{ r: 6 }}
                      animationDuration={800}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </ChartCard>
          )}

          {/* Bar chart: revenue by case type */}
          {isLoading ? (
            <ChartSkeleton />
          ) : (
            <ChartCard
              title="Receita por Tipo de Caso"
              description="Faturamento por área de atuação"
              icon={<BarChart3 className="h-5 w-5 text-indigo-500" />}
            >
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={revenueByTypeData}>
                    <defs>
                      <linearGradient
                        id="barGradient"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="0%"
                          stopColor={COLORS.primary}
                          stopOpacity={1}
                        />
                        <stop
                          offset="100%"
                          stopColor={COLORS.secondary}
                          stopOpacity={0.8}
                        />
                      </linearGradient>
                    </defs>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="hsl(var(--border))"
                    />
                    <XAxis
                      dataKey="type"
                      tick={{ fontSize: 11 }}
                    />
                    <YAxis
                      tick={{ fontSize: 12 }}
                      tickFormatter={(v) =>
                        `${(v / 1000).toFixed(0)}k`
                      }
                    />
                    <Tooltip
                      content={({ active, payload, label }) => (
                        <CustomTooltip
                          active={active}
                          label={label}
                          payload={payload?.map((p) => ({
                            name: 'Receita',
                            value: Number(p.value),
                            color: COLORS.primary,
                          }))}
                          formatter={formatCurrency}
                        />
                      )}
                    />
                    <Bar
                      dataKey="revenue"
                      fill="url(#barGradient)"
                      radius={[8, 8, 0, 0]}
                      animationDuration={800}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </ChartCard>
          )}
        </TabsContent>

        {/* ════════════════════════════════════════════
            TAB 3: PRODUCTIVITY
            ════════════════════════════════════════════ */}
        <TabsContent value="produtividade" className="space-y-6">
          {usingSampleData && !isLoading && <SampleDataBanner />}
          {isLoading ? (
            <>
              <div className="grid gap-6 lg:grid-cols-2">
                <ChartSkeleton />
                <ChartSkeleton />
              </div>
              <ChartSkeleton />
            </>
          ) : (
            <>
              <div className="grid gap-6 lg:grid-cols-2">
                {/* Bar: hours per lawyer */}
                <ChartCard
                  title="Horas por Advogado"
                  description="Total de horas registradas no periodo"
                  icon={<Users className="h-5 w-5 text-blue-500" />}
                >
                  <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={lawyerHoursData}
                        layout="vertical"
                        margin={{ left: 20 }}
                      >
                        <defs>
                          <linearGradient
                            id="hoursGradient"
                            x1="0"
                            y1="0"
                            x2="1"
                            y2="0"
                          >
                            <stop
                              offset="0%"
                              stopColor={COLORS.blue}
                              stopOpacity={1}
                            />
                            <stop
                              offset="100%"
                              stopColor={COLORS.info}
                              stopOpacity={0.8}
                            />
                          </linearGradient>
                        </defs>
                        <CartesianGrid
                          strokeDasharray="3 3"
                          horizontal={false}
                          stroke="hsl(var(--border))"
                        />
                        <XAxis
                          type="number"
                          tick={{ fontSize: 12 }}
                        />
                        <YAxis
                          dataKey="name"
                          type="category"
                          width={100}
                          tick={{ fontSize: 11 }}
                        />
                        <Tooltip
                          content={({ active, payload, label }) => (
                            <CustomTooltip
                              active={active}
                              label={label}
                              payload={payload?.map((p) => ({
                                name: 'Horas',
                                value: Number(p.value),
                                color: COLORS.blue,
                              }))}
                            />
                          )}
                        />
                        <Bar
                          dataKey="hours"
                          fill="url(#hoursGradient)"
                          radius={[0, 6, 6, 0]}
                          animationDuration={800}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>

                {/* Line: tasks completed per week */}
                <ChartCard
                  title="Tarefas Concluídas por Semana"
                  description="Produtividade semanal da equipe"
                  icon={<Zap className="h-5 w-5 text-amber-500" />}
                >
                  <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={tasksWeekData}>
                        <defs>
                          <linearGradient
                            id="taskGradient"
                            x1="0"
                            y1="0"
                            x2="0"
                            y2="1"
                          >
                            <stop
                              offset="5%"
                              stopColor={COLORS.warning}
                              stopOpacity={0.2}
                            />
                            <stop
                              offset="95%"
                              stopColor={COLORS.warning}
                              stopOpacity={0}
                            />
                          </linearGradient>
                        </defs>
                        <CartesianGrid
                          strokeDasharray="3 3"
                          stroke="hsl(var(--border))"
                        />
                        <XAxis
                          dataKey="week"
                          tick={{ fontSize: 12 }}
                        />
                        <YAxis tick={{ fontSize: 12 }} />
                        <Tooltip
                          content={({ active, payload, label }) => (
                            <CustomTooltip
                              active={active}
                              label={label}
                              payload={payload?.map((p) => ({
                                name: 'Tarefas',
                                value: Number(p.value),
                                color: COLORS.warning,
                              }))}
                            />
                          )}
                        />
                        <Line
                          type="monotone"
                          dataKey="completed"
                          stroke={COLORS.warning}
                          strokeWidth={3}
                          dot={{
                            r: 5,
                            fill: COLORS.warning,
                            stroke: '#fff',
                            strokeWidth: 2,
                          }}
                          activeDot={{ r: 7 }}
                          animationDuration={800}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>
              </div>

              {/* Radar: lawyer performance */}
              <ChartCard
                title="Performance dos Advogados"
                description="Comparativo multidimensional: casos, prazos, horas, documentos e receita"
                icon={<Target className="h-5 w-5 text-purple-500" />}
              >
                <div className="h-[400px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart
                      data={radarChartData}
                      cx="50%"
                      cy="50%"
                      outerRadius="70%"
                    >
                      <PolarGrid stroke="hsl(var(--border))" />
                      <PolarAngleAxis
                        dataKey="subject"
                        tick={{ fontSize: 12 }}
                      />
                      <PolarRadiusAxis
                        angle={90}
                        domain={[0, 100]}
                        tick={{ fontSize: 10 }}
                      />
                      {lawyerRadarData.map((lawyer, idx) => (
                        <Radar
                          key={lawyer.name}
                          name={lawyer.name}
                          dataKey={lawyer.name}
                          stroke={PIE_COLORS[idx % PIE_COLORS.length]}
                          fill={PIE_COLORS[idx % PIE_COLORS.length]}
                          fillOpacity={0.15}
                          strokeWidth={2}
                          animationDuration={800}
                        />
                      ))}
                      <Legend
                        formatter={(value) => (
                          <span className="text-xs text-muted-foreground">
                            {value}
                          </span>
                        )}
                      />
                      <Tooltip
                        content={({ active, payload, label }) => (
                          <CustomTooltip
                            active={active}
                            label={label}
                            payload={payload?.map((p) => ({
                              name: String(p.name),
                              value: Number(p.value),
                              color: String(p.color || '#666'),
                            }))}
                          />
                        )}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </ChartCard>
            </>
          )}
        </TabsContent>

        {/* ════════════════════════════════════════════
            TAB 4: DEADLINES
            ════════════════════════════════════════════ */}
        <TabsContent value="prazos" className="space-y-6">
          {usingSampleData && !isLoading && <SampleDataBanner />}
          {isLoading ? (
            <>
              <div className="grid gap-6 lg:grid-cols-2">
                <ChartSkeleton />
                <ChartSkeleton />
              </div>
              <ChartSkeleton />
            </>
          ) : (
            <>
              <div className="grid gap-6 lg:grid-cols-2">
                {/* Bar: deadlines met vs missed */}
                <ChartCard
                  title="Prazos Cumpridos vs Perdidos"
                  description="Comparativo mensal de cumprimento"
                  icon={
                    <CalendarCheck className="h-5 w-5 text-emerald-500" />
                  }
                >
                  <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={deadlinesByMonthData}>
                        <CartesianGrid
                          strokeDasharray="3 3"
                          stroke="hsl(var(--border))"
                        />
                        <XAxis
                          dataKey="month"
                          tick={{ fontSize: 12 }}
                        />
                        <YAxis tick={{ fontSize: 12 }} />
                        <Tooltip
                          content={({ active, payload, label }) => (
                            <CustomTooltip
                              active={active}
                              label={label}
                              payload={payload?.map((p) => ({
                                name: String(p.name) === 'met' ? 'Cumpridos' : 'Perdidos',
                                value: Number(p.value),
                                color: String(p.name) === 'met' ? COLORS.success : COLORS.danger,
                              }))}
                            />
                          )}
                        />
                        <Legend
                          formatter={(value) => (
                            <span className="text-xs text-muted-foreground">
                              {value === 'met'
                                ? 'Cumpridos'
                                : 'Perdidos'}
                            </span>
                          )}
                        />
                        <Bar
                          dataKey="met"
                          name="met"
                          fill={COLORS.success}
                          radius={[6, 6, 0, 0]}
                          animationDuration={800}
                        />
                        <Bar
                          dataKey="missed"
                          name="missed"
                          fill={COLORS.danger}
                          radius={[6, 6, 0, 0]}
                          animationDuration={800}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>

                {/* Donut: deadline status distribution */}
                <ChartCard
                  title="Distribuição de Prazos"
                  description="Status atual de todos os prazos"
                  icon={
                    <PieChartIcon className="h-5 w-5 text-violet-500" />
                  }
                >
                  <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={deadlineStatusData}
                          cx="50%"
                          cy="50%"
                          innerRadius={65}
                          outerRadius={95}
                          paddingAngle={4}
                          dataKey="value"
                          animationDuration={800}
                          stroke="none"
                        >
                          {deadlineStatusData.map((_, idx) => {
                            const colors = [
                              COLORS.success,
                              COLORS.danger,
                              COLORS.primary,
                              COLORS.warning,
                            ];
                            return (
                              <Cell
                                key={idx}
                                fill={
                                  colors[idx % colors.length]
                                }
                              />
                            );
                          })}
                        </Pie>
                        <Tooltip
                          content={({ active, payload }) => (
                            <CustomTooltip
                              active={active}
                              payload={payload?.map((p) => ({
                                name: String(p.name),
                                value: Number(p.value),
                                color: String(
                                  p.payload?.fill || '#666'
                                ),
                              }))}
                            />
                          )}
                        />
                        <Legend
                          verticalAlign="bottom"
                          height={36}
                          formatter={(value) => (
                            <span className="text-xs text-muted-foreground">
                              {value}
                            </span>
                          )}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>
              </div>

              {/* Calendar heatmap */}
              <ChartCard
                title="Mapa de Atividade de Prazos"
                description="Ultimas 12 semanas - intensidade de prazos por dia"
                icon={
                  <CalendarX className="h-5 w-5 text-teal-500" />
                }
              >
                <div className="flex flex-col items-center gap-4">
                  <CalendarHeatmap data={heatmapData} />
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span>Menos</span>
                    <div className="h-3 w-3 rounded-sm bg-muted" />
                    <div className="h-3 w-3 rounded-sm bg-emerald-200" />
                    <div className="h-3 w-3 rounded-sm bg-emerald-300" />
                    <div className="h-3 w-3 rounded-sm bg-emerald-400" />
                    <div className="h-3 w-3 rounded-sm bg-emerald-500" />
                    <span>Mais</span>
                  </div>
                </div>
              </ChartCard>
            </>
          )}
        </TabsContent>

        {/* ════════════════════════════════════════════
            TAB 5: FLUXOS DE TRABALHO (Fase 5)
            ════════════════════════════════════════════ */}
        <TabsContent value="fluxos" className="space-y-6">
          <FluxosTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// ── Fluxos Tab Component ────────────────────────────────────────

type FlowAnalyticsData = {
  summary: { total: number; running: number; completed: number; cancelled: number; completion_rate: number };
  by_template: { template_name_snapshot: string; total: number; completed: number }[];
  avg_completion_time: { template: string; avg_hours: number | null }[];
  tasks_by_role: { role_required: string; total: number; completed: number; pending: number }[];
  executions_over_time: { date: string; count: number }[];
  pending_by_user: { user_id: string; name: string; pending_tasks: number }[];
};

const ROLE_LABELS: Record<string, string> = {
  distribuidor: 'Distribuidor(a)', procurador: 'Procurador(a)',
  gerente: 'Gerente', assessor_gerencial: 'Assessor(a) Gerencial',
  assessor_gabinete: 'Assessor(a) de Gabinete', procurador_geral: 'Procurador(a)-Geral',
  subprocurador_geral: 'Subprocurador(a)-Geral', any: 'Qualquer papel',
};

function FluxosTab() {
  const [days, setDays] = useState(30);
  const { data, isLoading } = useQuery<FlowAnalyticsData>({
    queryKey: ['flow-analytics', days],
    queryFn: async () => {
      const res = await api.get(`/api/v1/workflow-execution/analytics/?days=${days}`);
      return res.data;
    },
  });

  if (isLoading) return <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin" /></div>;

  return (
    <div className="space-y-6">
      {/* Period filter */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">Período:</span>
        {[7, 30, 90].map((d) => (
          <button
            key={d}
            onClick={() => setDays(d)}
            className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
              days === d ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:bg-muted/80'
            }`}
          >
            {d} dias
          </button>
        ))}
      </div>

      {/* Summary */}
      {data && (
        <>
          <div className="grid gap-4 grid-cols-2 md:grid-cols-5">
            {[
              { label: 'Total', value: data.summary.total, icon: Workflow, color: 'text-violet-600' },
              { label: 'Em andamento', value: data.summary.running, icon: Activity, color: 'text-blue-600' },
              { label: 'Concluídos', value: data.summary.completed, icon: CheckCircle2, color: 'text-green-600' },
              { label: 'Cancelados', value: data.summary.cancelled, icon: XCircle, color: 'text-gray-500' },
              { label: 'Conclusão', value: `${data.summary.completion_rate}%`, icon: TrendingUp, color: 'text-emerald-600' },
            ].map(({ label, value, icon: Icon, color }) => (
              <Card key={label}>
                <CardContent className="flex items-center gap-3 py-4">
                  <Icon className={`h-8 w-8 ${color}`} />
                  <div>
                    <p className="text-2xl font-bold">{value}</p>
                    <p className="text-xs text-muted-foreground">{label}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            {/* By template */}
            <Card>
              <CardHeader><CardTitle className="text-sm">Execuções por template</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {data.by_template.length === 0 && <p className="text-sm text-muted-foreground">Sem dados.</p>}
                {data.by_template.map((t) => (
                  <div key={t.template_name_snapshot} className="flex items-center justify-between text-sm">
                    <span className="truncate max-w-[200px] text-muted-foreground">{t.template_name_snapshot}</span>
                    <span className="font-medium">{t.total}</span>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Tasks by role */}
            <Card>
              <CardHeader><CardTitle className="text-sm">Tarefas por papel</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {data.tasks_by_role.length === 0 && <p className="text-sm text-muted-foreground">Sem dados.</p>}
                {data.tasks_by_role.map((r) => (
                  <div key={r.role_required} className="flex items-center justify-between text-sm">
                    <span className="truncate max-w-[200px] text-muted-foreground">{ROLE_LABELS[r.role_required] ?? r.role_required}</span>
                    <div className="flex gap-3 text-xs">
                      <span className="text-green-600">{r.completed} ✓</span>
                      <span className="text-yellow-600">{r.pending} ⏳</span>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Avg completion time */}
            <Card>
              <CardHeader><CardTitle className="text-sm">Tempo médio de conclusão</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {data.avg_completion_time.length === 0 && <p className="text-sm text-muted-foreground">Nenhum fluxo concluído.</p>}
                {data.avg_completion_time.map((t) => (
                  <div key={t.template} className="flex items-center justify-between text-sm">
                    <span className="truncate max-w-[200px] text-muted-foreground">{t.template}</span>
                    <span className="font-mono text-xs">{t.avg_hours !== null ? `${t.avg_hours}h` : '—'}</span>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Pending by user */}
            <Card>
              <CardHeader><CardTitle className="text-sm">Tarefas pendentes por usuário</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {data.pending_by_user.length === 0 && <p className="text-sm text-muted-foreground">Nenhuma tarefa pendente atribuída.</p>}
                {data.pending_by_user.map((u) => (
                  <div key={u.user_id} className="flex items-center justify-between text-sm">
                    <span className="truncate max-w-[200px] text-muted-foreground">{u.name}</span>
                    <span className="font-medium text-yellow-600">{u.pending_tasks}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
