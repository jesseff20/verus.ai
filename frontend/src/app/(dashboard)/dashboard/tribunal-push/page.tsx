'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Bell,
  Plus,
  RefreshCw,
  CheckCircle2,
  Trash2,
  Calendar,
  Gavel,
  Settings2,
  Sparkles,
  Brain,
  FileText,
  AlertCircle,
  X,
} from 'lucide-react';
import {
  useTribunalConfigs,
  useCreateTribunalConfig,
  useUpdateTribunalConfig,
  useDeleteTribunalConfig,
  useTribunalCheckNow,
  useTribunalEvents,
  useMarkEventProcessed,
  useCopilotAnalyzeMovement,
  useCopilotSuggestActions,
  useCopilotSummarize,
  useCopilotClassifyRelevance,
  CopilotSuggestion,
  CopilotRelevanceResult,
} from '@/hooks/use-protocol';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';

const COURT_SYSTEMS = [
  { value: 'pje', label: 'PJe' },
  { value: 'esaj', label: 'e-SAJ' },
  { value: 'projudi', label: 'PROJUDI' },
  { value: 'eproc', label: 'e-Proc' },
  { value: 'sei', label: 'SEI' },
];

const NOTIFICATION_TYPES = [
  { value: 'movimentacao', label: 'Movimentação processual' },
  { value: 'publicacao', label: 'Publicação no DJe' },
  { value: 'intimacao', label: 'Intimação' },
  { value: 'despacho', label: 'Despacho' },
  { value: 'sentenca', label: 'Sentença' },
  { value: 'audiencia', label: 'Audiência designada' },
];

const EVENT_TYPE_COLORS: Record<string, string> = {
  movimentacao: 'border-blue-500 text-blue-700 bg-blue-50',
  publicacao: 'border-purple-500 text-purple-700 bg-purple-50',
  intimacao: 'border-orange-500 text-orange-700 bg-orange-50',
  despacho: 'border-cyan-500 text-cyan-700 bg-cyan-50',
  sentenca: 'border-red-500 text-red-700 bg-red-50',
  audiencia: 'border-green-500 text-green-700 bg-green-50',
};

const DAYS_OPTIONS = [
  { value: '7', label: 'Últimos 7 dias' },
  { value: '15', label: 'Últimos 15 dias' },
  { value: '30', label: 'Últimos 30 dias' },
  { value: '90', label: 'Últimos 90 dias' },
];

const RELEVANCE_COLORS: Record<string, string> = {
  alta: 'bg-red-100 text-red-800 border-red-300',
  media: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  baixa: 'bg-green-100 text-green-800 border-green-300',
};

const URGENCY_COLORS: Record<string, string> = {
  alto: 'bg-red-100 text-red-800',
  medio: 'bg-yellow-100 text-yellow-800',
  baixo: 'bg-green-100 text-green-800',
};

export default function TribunalPushPage() {
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [eventCourtFilter, setEventCourtFilter] = useState<string>('all');
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('all');
  const [daysFilter, setDaysFilter] = useState<string>('30');

  // Form state for new config
  const [formCourtSystem, setFormCourtSystem] = useState('');
  const [formInterval, setFormInterval] = useState('24');
  const [formNotifTypes, setFormNotifTypes] = useState<string[]>([]);

  // Copilot state
  const [selectedEvent, setSelectedEvent] = useState<{ id: string; type: string; description: string } | null>(null);
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  const [summaryText, setSummaryText] = useState('');
  const [relevanceData, setRelevanceData] = useState<Record<string, CopilotRelevanceResult>>({});

  const { data: configs, isLoading: isLoadingConfigs } = useTribunalConfigs();
  const createConfig = useCreateTribunalConfig();
  const updateConfig = useUpdateTribunalConfig();
  const deleteConfig = useDeleteTribunalConfig();
  const checkNow = useTribunalCheckNow();

  const analyzeMovement = useCopilotAnalyzeMovement();
  const suggestActions = useCopilotSuggestActions();
  const summarize = useCopilotSummarize();
  const classifyRelevance = useCopilotClassifyRelevance();

  const eventFilters: Record<string, string> = {};
  if (eventCourtFilter !== 'all') eventFilters.court_system = eventCourtFilter;
  if (eventTypeFilter !== 'all') eventFilters.event_type = eventTypeFilter;
  if (daysFilter) eventFilters.days = daysFilter;

  const { data: events, isLoading: isLoadingEvents } = useTribunalEvents(
    Object.keys(eventFilters).length > 0 ? eventFilters : undefined
  );
  const markProcessed = useMarkEventProcessed();

  const handleCreateConfig = async () => {
    if (!formCourtSystem) return;
    await createConfig.mutateAsync({
      court_system: formCourtSystem,
      check_interval_hours: parseInt(formInterval, 10) || 24,
      notification_types: formNotifTypes,
    });
    setFormCourtSystem('');
    setFormInterval('24');
    setFormNotifTypes([]);
    setConfigDialogOpen(false);
  };

  const toggleNotifType = (type: string) => {
    setFormNotifTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  // Copilot handlers
  const handleAnalyzeMovement = async (event: { id: string; type: string; description: string }) => {
    setSelectedEvent(event);
    const result = await analyzeMovement.mutateAsync({ movement_text: event.description });
    setShowAnalysis(true);
  };

  const handleSuggestActions = async (eventType: string) => {
    const result = await suggestActions.mutateAsync({ movement_type: eventType });
    setShowSuggestions(true);
  };

  const handleSummarize = async (text: string) => {
    const result = await summarize.mutateAsync({ publication_text: text });
    setSummaryText(result.summary);
    setShowSummary(true);
  };

  const handleClassifyRelevance = async (event: { id: string; type: string; description: string }) => {
    const result = await classifyRelevance.mutateAsync({
      event_type: event.type,
      description: event.description,
    });
    setRelevanceData((prev) => ({ ...prev, [event.id]: result }));
  };

  // Classificar relevância automaticamente ao carregar eventos
  useEffect(() => {
    if (events && events.length > 0) {
      events.forEach((event) => {
        if (!relevanceData[event.id]) {
          handleClassifyRelevance({ id: event.id, type: event.event_type, description: event.description });
        }
      });
    }
  }, [events]);

  if (isLoadingConfigs) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Acompanhamento de Tribunal</h1>
          <p className="text-muted-foreground">Carregando dados...</p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-4 w-32" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold">Acompanhamento de Tribunal</h1>
          <p className="text-muted-foreground">
            Configure alertas e acompanhe eventos dos tribunais em tempo real
          </p>
        </div>
        <Badge variant="outline" className="flex items-center gap-2 h-8 w-fit">
          <Sparkles className="h-4 w-4 text-purple-500" />
          Copilot habilitado
        </Badge>
      </div>

      {/* Configs Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Settings2 className="h-5 w-5" />
            Configurações
          </h2>
          <Dialog open={configDialogOpen} onOpenChange={setConfigDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Nova Configuração
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Nova Configuração de Tribunal</DialogTitle>
                <DialogDescription className="sr-only">Formulário para configurar novo tribunal</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 pt-4">
                <div className="space-y-2">
                  <Label>Sistema do Tribunal</Label>
                  <Select value={formCourtSystem} onValueChange={setFormCourtSystem}>
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione o sistema" />
                    </SelectTrigger>
                    <SelectContent>
                      {COURT_SYSTEMS.map((cs) => (
                        <SelectItem key={cs.value} value={cs.value}>
                          {cs.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Intervalo de verificação (horas)</Label>
                  <Input
                    type="number"
                    min="1"
                    max="168"
                    value={formInterval}
                    onChange={(e) => setFormInterval(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Tipos de notificação</Label>
                  <div className="space-y-2 pt-1">
                    {NOTIFICATION_TYPES.map((nt) => (
                      <div key={nt.value} className="flex items-center gap-2">
                        <Checkbox
                          id={`notif-${nt.value}`}
                          checked={formNotifTypes.includes(nt.value)}
                          onCheckedChange={() => toggleNotifType(nt.value)}
                        />
                        <label htmlFor={`notif-${nt.value}`} className="text-sm cursor-pointer">
                          {nt.label}
                        </label>
                      </div>
                    ))}
                  </div>
                </div>
                <Button
                  className="w-full"
                  onClick={handleCreateConfig}
                  disabled={createConfig.isPending || !formCourtSystem}
                >
                  {createConfig.isPending ? 'Criando...' : 'Criar Configuração'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {(!configs || configs.length === 0) ? (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              Nenhuma configuração cadastrada. Crie uma para começar a receber eventos.
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {configs.map((config) => (
              <Card key={config.id}>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Gavel className="h-4 w-4" />
                    {config.court_system_display || config.court_system}
                  </CardTitle>
                  <Switch
                    checked={config.is_active}
                    onCheckedChange={(checked) =>
                      updateConfig.mutate({ id: config.id, data: { is_active: checked } })
                    }
                  />
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="text-sm text-muted-foreground space-y-1">
                    <div className="flex justify-between">
                      <span>Intervalo:</span>
                      <span>{config.check_interval_hours}h</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Eventos:</span>
                      <span>{config.events_count}</span>
                    </div>
                    {config.last_checked && (
                      <div className="flex justify-between">
                        <span>Última verificação:</span>
                        <span>{new Date(config.last_checked).toLocaleString('pt-BR')}</span>
                      </div>
                    )}
                  </div>
                  {config.notification_types.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {config.notification_types.map((nt) => (
                        <Badge key={nt} variant="outline" className="text-xs">
                          {nt}
                        </Badge>
                      ))}
                    </div>
                  )}
                  <div className="flex gap-2 pt-1">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => checkNow.mutate(config.id)}
                      disabled={checkNow.isPending}
                    >
                      <RefreshCw className="mr-1 h-3 w-3" />
                      Verificar Agora
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => deleteConfig.mutate(config.id)}
                      disabled={deleteConfig.isPending}
                      title="Excluir Configuração"
                    >
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Events Section */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <Bell className="h-5 w-5" />
          Eventos Recentes
        </h2>

        {/* Filters */}
        <div className="flex flex-col gap-4 sm:flex-row">
          <div className="w-full sm:w-48">
            <Select value={eventCourtFilter} onValueChange={setEventCourtFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Sistema" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos os Sistemas</SelectItem>
                {COURT_SYSTEMS.map((cs) => (
                  <SelectItem key={cs.value} value={cs.value}>
                    {cs.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="w-full sm:w-48">
            <Select value={eventTypeFilter} onValueChange={setEventTypeFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Tipo de evento" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos os Tipos</SelectItem>
                {NOTIFICATION_TYPES.map((nt) => (
                  <SelectItem key={nt.value} value={nt.value}>
                    {nt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="w-full sm:w-48">
            <Select value={daysFilter} onValueChange={setDaysFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Período" />
              </SelectTrigger>
              <SelectContent>
                {DAYS_OPTIONS.map((d) => (
                  <SelectItem key={d.value} value={d.value}>
                    {d.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Events List */}
        {isLoadingEvents ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Card key={i}>
                <CardContent className="py-4">
                  <Skeleton className="h-16 w-full" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (!events || events.length === 0) ? (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              Nenhum evento encontrado no período selecionado.
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {events.map((event) => {
              const relevance = relevanceData[event.id];
              return (
                <Card key={event.id} className={event.is_processed ? 'opacity-60' : ''}>
                  <CardContent className="py-4">
                    <div className="flex flex-col gap-3">
                      {/* Header row */}
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge
                          variant="outline"
                          className={EVENT_TYPE_COLORS[event.event_type] ?? ''}
                        >
                          {event.event_type}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          {event.config_court_system_display || event.config_court_system}
                        </Badge>
                        {relevance && (
                          <Badge
                            variant="outline"
                            className={`text-xs font-medium ${RELEVANCE_COLORS[relevance.relevance]}`}
                            title={`Confiança: ${relevance.confidence}%`}
                          >
                            <Brain className="mr-1 h-3 w-3" />
                            Relevância: {relevance.relevance}
                          </Badge>
                        )}
                        {event.is_processed && (
                          <Badge variant="secondary" className="text-xs">
                            <CheckCircle2 className="mr-1 h-3 w-3" />
                            Processado
                          </Badge>
                        )}
                      </div>

                      {/* Description */}
                      <p className="text-sm">{event.description}</p>

                      {/* Copilot Actions */}
                      <div className="flex flex-wrap gap-2 pt-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleAnalyzeMovement({
                            id: event.id,
                            type: event.event_type,
                            description: event.description,
                          })}
                          disabled={analyzeMovement.isPending}
                          className="h-8 text-xs"
                        >
                          <Brain className="mr-1 h-3 w-3" />
                          Analisar com IA
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleSuggestActions(event.event_type)}
                          disabled={suggestActions.isPending}
                          className="h-8 text-xs"
                        >
                          <Sparkles className="mr-1 h-3 w-3" />
                          Sugestões
                        </Button>
                        {(event.event_type === 'publicacao' || event.description.length > 200) && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleSummarize(event.description)}
                            disabled={summarize.isPending}
                            className="h-8 text-xs"
                          >
                            <FileText className="mr-1 h-3 w-3" />
                            Resumir
                          </Button>
                        )}
                      </div>

                      {/* Metadata */}
                      <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground pt-2">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {new Date(event.event_date).toLocaleDateString('pt-BR')}
                        </span>
                        {(event.case_titulo || event.case_numero_processo) && (
                          <span className="flex items-center gap-1">
                            <Gavel className="h-3 w-3" />
                            {event.case_titulo || event.case_numero_processo}
                          </span>
                        )}
                      </div>

                      {/* Action button */}
                      <div className="flex justify-end pt-2">
                        {!event.is_processed && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => markProcessed.mutate(event.id)}
                            disabled={markProcessed.isPending}
                          >
                            <CheckCircle2 className="mr-1 h-3 w-3" />
                            Marcar Processado
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* Analysis Dialog */}
      <Dialog open={showAnalysis} onOpenChange={(open) => { setShowAnalysis(open); if (!open) setSelectedEvent(null); }}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-purple-500" />
              Análise da Movimentação
            </DialogTitle>
            <DialogDescription>
              Interpretação jurídica gerada por IA
            </DialogDescription>
          </DialogHeader>
          {analyzeMovement.data && (
            <ScrollArea className="max-h-[60vh] pr-4">
              <div className="space-y-4">
                <Alert>
                  <AlertDescription className="text-sm">
                    <strong>Interpretação:</strong> {analyzeMovement.data.interpretation}
                  </AlertDescription>
                </Alert>

                <div>
                  <h4 className="font-semibold mb-2 flex items-center gap-2">
                    <AlertCircle className="h-4 w-4" />
                    Pontos-chave
                  </h4>
                  <ul className="list-disc list-inside space-y-1 text-sm">
                    {analyzeMovement.data.key_points.map((point, i) => (
                      <li key={i}>{point}</li>
                    ))}
                  </ul>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">Nível de urgência:</span>
                  <Badge className={URGENCY_COLORS[analyzeMovement.data.urgency_level]}>
                    {analyzeMovement.data.urgency_level}
                  </Badge>
                </div>

                <Separator />

                <div>
                  <h4 className="font-semibold mb-2">Ações Sugeridas</h4>
                  <ul className="list-disc list-inside space-y-1 text-sm">
                    {analyzeMovement.data.suggested_actions.map((action, i) => (
                      <li key={i}>{action}</li>
                    ))}
                  </ul>
                </div>

                <Separator />

                <div>
                  <h4 className="font-semibold mb-2">Implicações Jurídicas</h4>
                  <p className="text-sm text-muted-foreground">
                    {analyzeMovement.data.legal_implications}
                  </p>
                </div>
              </div>
            </ScrollArea>
          )}
        </DialogContent>
      </Dialog>

      {/* Suggestions Dialog */}
      <Dialog open={showSuggestions} onOpenChange={setShowSuggestions}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-purple-500" />
              Sugestões de Ações
            </DialogTitle>
            <DialogDescription>
              Ações práticas recomendadas pela IA
            </DialogDescription>
          </DialogHeader>
          {suggestActions.data?.suggestions && (
            <ScrollArea className="max-h-[50vh]">
              <div className="space-y-3">
                {suggestActions.data.suggestions.map((suggestion: CopilotSuggestion, i) => (
                  <Card key={i} className="p-3">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm font-medium">{suggestion.action}</p>
                      <Badge
                        variant="outline"
                        className={
                          suggestion.priority === 'alta'
                            ? 'bg-red-100 text-red-800'
                            : suggestion.priority === 'media'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-green-100 text-green-800'
                        }
                      >
                        {suggestion.priority}
                      </Badge>
                    </div>
                    <div className="flex gap-2 mt-2 text-xs text-muted-foreground">
                      <span>{suggestion.estimated_time}</span>
                      <span>•</span>
                      <span className="capitalize">{suggestion.category}</span>
                    </div>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          )}
        </DialogContent>
      </Dialog>

      {/* Summary Dialog */}
      <Dialog open={showSummary} onOpenChange={setShowSummary}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-purple-500" />
              Resumo da Publicação
            </DialogTitle>
            <DialogDescription>
              Versão concisa mantendo informações críticas
            </DialogDescription>
          </DialogHeader>
          <div className="max-h-[40vh] overflow-auto">
            <Card className="p-4">
              <p className="text-sm leading-relaxed">{summaryText}</p>
            </Card>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
