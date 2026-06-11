'use client';

import { useState, useEffect } from 'react';
import { useDashboardConfig, type WidgetConfig } from '@/hooks/use-dashboard-config';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from 'sonner';
import {
  Scale,
  Calendar,
  DollarSign,
  Activity,
  Clock,
  BarChart3,
  Settings,
  Save,
  ArrowLeft,
  Check,
} from 'lucide-react';
import Link from 'next/link';

const WIDGET_TYPES = [
  { type: 'cases_summary', label: 'Resumo de Casos', icon: Scale, description: 'Casos ativos e recentes' },
  { type: 'deadlines_upcoming', label: 'Próximos Prazos', icon: Calendar, description: 'Prazos a vencer' },
  { type: 'financial_summary', label: 'Resumo Financeiro', icon: DollarSign, description: 'Receitas, pendentes e vencidos' },
  { type: 'activity_feed', label: 'Feed de Atividades', icon: Activity, description: 'Últimas atividades no sistema' },
  { type: 'calendar_today', label: 'Calendário Hoje', icon: Clock, description: 'Eventos e prazos do dia' },
  { type: 'kpis', label: 'KPIs', icon: BarChart3, description: 'Indicadores de desempenho' },
];

const THEME_OPTIONS = [
  { value: 'default', label: 'Padrão', description: 'Layout equilibrado com cards médios' },
  { value: 'compact', label: 'Compacto', description: 'Informações condensadas, mais dados visíveis' },
  { value: 'detailed', label: 'Detalhado', description: 'Cards expandidos com mais informações' },
];

export default function DashboardConfigPage() {
  const { config, isLoading, updateConfig } = useDashboardConfig();

  const [selectedWidgets, setSelectedWidgets] = useState<string[]>([]);
  const [theme, setTheme] = useState('default');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(300);

  // Sincroniza com dados do backend
  useEffect(() => {
    if (config) {
      const widgetTypes = (config.layout || []).map((w: WidgetConfig) => w.type);
      setSelectedWidgets(widgetTypes);
      setTheme(config.theme || 'default');
      setAutoRefresh(config.auto_refresh ?? true);
      setRefreshInterval(config.refresh_interval || 300);
    }
  }, [config]);

  const toggleWidget = (type: string) => {
    setSelectedWidgets((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  const handleSave = () => {
    const layout: WidgetConfig[] = selectedWidgets.map((type, idx) => ({
      id: String(idx + 1),
      type,
      position: idx,
      size: 'medium',
      config: {},
    }));

    updateConfig.mutate(
      { layout, theme, auto_refresh: autoRefresh, refresh_interval: refreshInterval },
      {
        onSuccess: () => toast.success('Configuração salva com sucesso!'),
        onError: () => toast.error('Erro ao salvar configuração.'),
      }
    );
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid gap-4 grid-cols-1 lg:grid-cols-2">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-32" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Link href="/dashboard">
            <Button variant="outline" size="sm">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Voltar
            </Button>
          </Link>
          <div>
            <h1 className="text-lg sm:text-2xl md:text-3xl font-bold tracking-tight flex items-center gap-2">
              <Settings className="h-6 w-6 sm:h-8 sm:w-8" />
              Configurar Dashboard
            </h1>
            <p className="text-muted-foreground text-sm">
              Personalize os widgets e aparência do seu dashboard
            </p>
          </div>
        </div>
        <Button onClick={handleSave} disabled={updateConfig.isPending} className="self-start sm:self-auto">
          <Save className="mr-2 h-4 w-4" />
          {updateConfig.isPending ? 'Salvando...' : 'Salvar Configuração'}
        </Button>
      </div>

      {/* Widgets Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Widgets</CardTitle>
          <CardDescription>Selecione quais widgets deseja exibir no dashboard</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
            {WIDGET_TYPES.map((widget) => {
              const Icon = widget.icon;
              const isSelected = selectedWidgets.includes(widget.type);
              return (
                <button
                  key={widget.type}
                  onClick={() => toggleWidget(widget.type)}
                  className={`flex items-start gap-3 p-4 rounded-lg border-2 transition-colors text-left ${
                    isSelected
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-muted-foreground/30'
                  }`}
                >
                  <div className={`p-2 rounded-lg ${isSelected ? 'bg-primary/10' : 'bg-muted'}`}>
                    <Icon className={`h-5 w-5 ${isSelected ? 'text-primary' : 'text-muted-foreground'}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <p className="font-medium text-sm">{widget.label}</p>
                      {isSelected && <Check className="h-4 w-4 text-primary" />}
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5">{widget.description}</p>
                  </div>
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Layout Preview */}
      {selectedWidgets.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Preview do Layout</CardTitle>
            <CardDescription>{selectedWidgets.length} widget(s) selecionado(s)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 grid-cols-2 lg:grid-cols-3">
              {selectedWidgets.map((type, idx) => {
                const widget = WIDGET_TYPES.find((w) => w.type === type);
                if (!widget) return null;
                const Icon = widget.icon;
                return (
                  <div
                    key={type}
                    className="flex items-center gap-2 p-3 rounded-lg bg-muted/50 border border-dashed"
                  >
                    <span className="text-xs text-muted-foreground font-mono">{idx + 1}</span>
                    <Icon className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm truncate">{widget.label}</span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Theme Selector */}
      <Card>
        <CardHeader>
          <CardTitle>Tema</CardTitle>
          <CardDescription>Escolha o estilo de exibição dos widgets</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 grid-cols-1 sm:grid-cols-3">
            {THEME_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setTheme(opt.value)}
                className={`p-4 rounded-lg border-2 transition-colors text-left ${
                  theme === opt.value
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-muted-foreground/30'
                }`}
              >
                <div className="flex items-center justify-between">
                  <p className="font-medium text-sm">{opt.label}</p>
                  {theme === opt.value && <Check className="h-4 w-4 text-primary" />}
                </div>
                <p className="text-xs text-muted-foreground mt-1">{opt.description}</p>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Auto-refresh Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Atualização Automática</CardTitle>
          <CardDescription>Configure a atualização automática dos dados</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <Label htmlFor="auto-refresh" className="flex flex-col">
              <span>Auto-refresh</span>
              <span className="text-xs text-muted-foreground font-normal">
                Atualiza os dados automaticamente
              </span>
            </Label>
            <Switch
              id="auto-refresh"
              checked={autoRefresh}
              onCheckedChange={setAutoRefresh}
            />
          </div>
          {autoRefresh && (
            <div className="flex items-center gap-3">
              <Label htmlFor="refresh-interval">Intervalo (segundos)</Label>
              <Input
                id="refresh-interval"
                type="number"
                min={60}
                max={3600}
                className="w-32"
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(Number(e.target.value) || 300)}
              />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
