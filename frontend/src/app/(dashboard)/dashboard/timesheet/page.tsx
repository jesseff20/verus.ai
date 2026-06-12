'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { TimeEntry } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { AITextarea } from '@/components/ui/ai-textarea';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Clock, Plus, CheckCircle, DollarSign, TrendingUp, Calendar, Timer, BarChart3, Sparkles, Wand2, AlertCircle, ArrowRight } from 'lucide-react';
import { toast } from 'sonner';

interface TimesheetSuggestion {
  date: string;
  case_id: string;
  case_title: string;
  activity_type: string;
  activity_description: string;
  suggested_hours: number;
  suggested_description: string;
  confidence: number;
  metadata?: Record<string, any>;
}

interface UnloggedHours {
  date: string;
  activity_count: number;
  activity_types: string[];
  suggestion: string;
}

export default function TimesheetPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [showUnlogged, setShowUnlogged] = useState(false);
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);

  // Form state
  const [formData, setFormData] = useState({
    caso: '', date: new Date().toISOString().split('T')[0],
    hours: '', description: '', billing_type: 'billable', hourly_rate: '250',
  });

  // Copilot state
  const [selectedSuggestion, setSelectedSuggestion] = useState<TimesheetSuggestion | null>(null);
  const [isGeneratingDescription, setIsGeneratingDescription] = useState(false);

  // Queries
  const { data: entries = [], isLoading } = useQuery({
    queryKey: ['timesheet', year, month],
    queryFn: async () => {
      const res = await api.get('/api/v1/processos/timesheet/', { params: { year, month } });
      return (res.data?.results || res.data) as TimeEntry[];
    },
    staleTime: 2 * 60 * 1000,
  });

  const { data: report } = useQuery({
    queryKey: ['timesheet-report', year, month],
    queryFn: async () => {
      const res = await api.get('/api/v1/processos/timesheet/relatorio-mensal/', { params: { year, month } });
      return res.data;
    },
    staleTime: 2 * 60 * 1000,
  });

  const { data: cases = [] } = useQuery({
    queryKey: ['cases-list-simple'],
    queryFn: async () => {
      const res = await api.get('/api/v1/processos/', { params: { page_size: 100 } });
      return res.data?.results || res.data || [];
    },
  });

  // Copilot Queries
  const { data: suggestionsData } = useQuery({
    queryKey: ['timesheet-copilot-suggestions', month, year],
    queryFn: async () => {
      const res = await api.get('/api/v1/processos/timesheet/copilot/sugerir/', {
        params: { days_back: 7 },
      });
      return res.data;
    },
    enabled: showSuggestions,
    staleTime: 5 * 60 * 1000,
  });

  const { data: unloggedData } = useQuery({
    queryKey: ['timesheet-copilot-unlogged', month, year],
    queryFn: async () => {
      const start = new Date(year, month - 1, 1).toISOString().split('T')[0];
      const end = new Date(year, month, 0).toISOString().split('T')[0];
      const res = await api.get('/api/v1/processos/timesheet/copilot/detectar/', {
        params: { start, end },
      });
      return res.data;
    },
    enabled: showUnlogged,
    staleTime: 5 * 60 * 1000,
  });

  // Mutations
  const createEntry = useMutation({
    mutationFn: async (data: any) => {
      const res = await api.post('/api/v1/processos/timesheet/', data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timesheet'] });
      queryClient.invalidateQueries({ queryKey: ['timesheet-report'] });
      setShowForm(false);
      setSelectedSuggestion(null);
      setFormData({ caso: '', date: new Date().toISOString().split('T')[0], hours: '', description: '', billing_type: 'billable', hourly_rate: '250' });
      toast.success('Registro de horas criado');
    },
    onError: () => toast.error('Erro ao criar registro'),
  });

  const approveEntry = useMutation({
    mutationFn: async (id: string) => {
      const res = await api.post(`/api/v1/processos/timesheet/${id}/aprovar/`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timesheet'] });
      toast.success('Registro aprovado');
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || 'Erro ao processar');
    },
  });

  const generateDescription = useMutation({
    mutationFn: async (data: { activity_type: string; case_title: string; details?: any }) => {
      const res = await api.post('/api/v1/processos/timesheet/copilot/descricao/', data);
      return res.data;
    },
    onMutate: () => setIsGeneratingDescription(true),
    onSuccess: (data) => {
      setFormData(p => ({ ...p, description: data.description }));
      setIsGeneratingDescription(false);
      toast.success('Descrição gerada com IA');
    },
    onError: () => {
      setIsGeneratingDescription(false);
      toast.error('Erro ao gerar descrição');
    },
  });

  const summary = report?.summary || {};
  const totalHours = summary.total_hours || 0;
  const billableHours = summary.billable_hours || 0;
  const totalValue = summary.total_value || 0;
  const utilization = summary.utilization_rate || 0;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.caso || !formData.hours || !formData.description) {
      toast.error('Preencha todos os campos obrigatórios');
      return;
    }
    createEntry.mutate({
      ...formData,
      hours: parseFloat(formData.hours),
      hourly_rate: formData.hourly_rate ? parseFloat(formData.hourly_rate) : null,
    });
  };

  const handleSelectSuggestion = (suggestion: TimesheetSuggestion) => {
    setSelectedSuggestion(suggestion);
    setFormData({
      ...formData,
      caso: suggestion.case_id,
      date: suggestion.date,
      hours: String(suggestion.suggested_hours),
      description: suggestion.suggested_description,
    });
    setShowSuggestions(false);
    setShowForm(true);
  };

  const handleImproveDescription = () => {
    if (!formData.caso || !formData.description) {
      toast.error('Preencha o caso e uma descrição base primeiro');
      return;
    }
    const selectedCase = cases.find((c: any) => c.id === formData.caso);
    generateDescription.mutate({
      activity_type: 'atividade',
      case_title: selectedCase?.titulo || 'Caso',
      details: { current_description: formData.description },
    });
  };

  const monthNames = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];
  const suggestions = suggestionsData?.suggestions || [];
  const unloggedHours = unloggedData?.unlogged_hours || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2"><Clock className="h-6 w-6" /> Timesheet</h1>
          <p className="text-muted-foreground">Controle de horas trabalhadas por caso</p>
        </div>
        <div className="flex gap-2 items-center">
          <Select value={String(month)} onValueChange={(v) => setMonth(Number(v))}>
            <SelectTrigger className="w-[120px]"><SelectValue /></SelectTrigger>
            <SelectContent>{monthNames.map((m, i) => <SelectItem key={i} value={String(i+1)}>{m}</SelectItem>)}</SelectContent>
          </Select>
          <Select value={String(year)} onValueChange={(v) => setYear(Number(v))}>
            <SelectTrigger className="w-[100px]"><SelectValue /></SelectTrigger>
            <SelectContent>{[2024,2025,2026].map(y => <SelectItem key={y} value={String(y)}>{y}</SelectItem>)}</SelectContent>
          </Select>
          <Button variant="outline" onClick={() => setShowUnlogged(!showUnlogged)}>
            <AlertCircle className="h-4 w-4 mr-2" />
            Horas não lançadas
            {unloggedData?.count > 0 && (
              <Badge className="ml-2 bg-orange-500">{unloggedData.count}</Badge>
            )}
          </Button>
          <Button variant="outline" onClick={() => setShowSuggestions(!showSuggestions)}>
            <Sparkles className="h-4 w-4 mr-2" />
            Sugestões IA
            {suggestionsData?.count > 0 && (
              <Badge className="ml-2 bg-purple-500">{suggestionsData.count}</Badge>
            )}
          </Button>
          <Dialog open={showForm} onOpenChange={setShowForm}>
            <DialogTrigger asChild><Button><Plus className="h-4 w-4 mr-2" /> Registrar Horas</Button></DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>Novo Registro de Horas</DialogTitle>
                <DialogDescription>Registre as horas trabalhadas em um caso</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2">
                    <Label>Caso *</Label>
                    <Select value={formData.caso} onValueChange={(v) => setFormData(p => ({...p, caso: v}))}>
                      <SelectTrigger><SelectValue placeholder="Selecione o caso" /></SelectTrigger>
                      <SelectContent>{cases.map((c: any) => <SelectItem key={c.id} value={c.id}>{c.titulo}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                  <div><Label>Data *</Label><Input type="date" value={formData.date} onChange={e => setFormData(p => ({...p, date: e.target.value}))} /></div>
                  <div><Label>Horas *</Label><Input type="number" step="0.25" min="0.25" max="24" value={formData.hours} onChange={e => setFormData(p => ({...p, hours: e.target.value}))} placeholder="2.5" /></div>
                  <div>
                    <Label>Tipo</Label>
                    <Select value={formData.billing_type} onValueChange={(v) => setFormData(p => ({...p, billing_type: v}))}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="billable">Atividade Produtiva</SelectItem>
                        <SelectItem value="non_billable">Atividade Administrativa</SelectItem>
                        <SelectItem value="pro_bono">Capacitação / Formação</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div><Label>Valor/Hora (R$)</Label><Input type="number" step="10" value={formData.hourly_rate} onChange={e => setFormData(p => ({...p, hourly_rate: e.target.value}))} /></div>
                  <div className="col-span-2">
                    <div className="flex items-center justify-between">
                      <Label>Descrição *</Label>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={handleImproveDescription}
                        disabled={isGeneratingDescription || !formData.caso}
                        className="h-7 text-xs"
                      >
                        <Wand2 className={`h-3 w-3 mr-1 ${isGeneratingDescription ? 'animate-pulse' : ''}`} />
                        {isGeneratingDescription ? 'Gerando...' : 'Melhorar com IA'}
                      </Button>
                    </div>
                    <AITextarea
                      value={formData.description}
                      onChange={e => setFormData(p => ({...p, description: e.target.value}))}
                      setValue={(v) => setFormData(p => ({...p, description: v}))}
                      placeholder="Descreva a atividade realizada"
                      rows={3}
                      aiContext="Descrição de atividade jurídica registrada no timesheet de um procurador municipal"
                      aiObjective="Melhorar, detalhar ou corrigir a descrição da atividade com linguagem jurídica profissional"
                    />
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <Button type="button" variant="outline" onClick={() => setShowForm(false)}>Cancelar</Button>
                  <Button type="submit" disabled={createEntry.isPending}>{createEntry.isPending ? 'Salvando...' : 'Salvar'}</Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Unlogged Hours Alert */}
      {showUnlogged && unloggedHours.length > 0 && (
        <Alert className="bg-orange-50 border-orange-200">
          <AlertCircle className="h-4 w-4 text-orange-600" />
          <AlertDescription>
            <div className="mt-2 space-y-2">
              <p className="font-medium text-orange-800">
                {unloggedHours.length} período(s) com atividades não registradas:
              </p>
              <div className="grid gap-2">
                {unloggedHours.slice(0, 5).map((item: UnloggedHours, idx: number) => (
                  <div key={idx} className="flex items-center justify-between text-sm bg-orange-100/50 p-2 rounded">
                    <span>{new Date(item.date).toLocaleDateString('pt-BR')} - {item.activity_count} atividades</span>
                    <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={() => setShowForm(true)}>
                      Registrar <ArrowRight className="h-3 w-3 ml-1" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Suggestions Panel */}
      {showSuggestions && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-purple-500" />
              Sugestões de Preenchimento Automático
            </CardTitle>
            <CardDescription>
              {suggestions.length} sugestões baseadas em suas atividades recentes
            </CardDescription>
          </CardHeader>
          <CardContent>
            {suggestions.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">Nenhuma sugestão disponível no momento</p>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {suggestions.map((suggestion: TimesheetSuggestion, idx: number) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-3 border rounded-lg hover:bg-accent/50 cursor-pointer transition-colors"
                    onClick={() => handleSelectSuggestion(suggestion)}
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{suggestion.case_title}</span>
                        <Badge variant="outline" className="text-xs">
                          {suggestion.confidence}% confiança
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">{suggestion.activity_description}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {new Date(suggestion.date).toLocaleDateString('pt-BR')} • {suggestion.suggested_hours}h sugeridas
                      </p>
                    </div>
                    <Button size="sm" variant="outline">
                      Usar <ArrowRight className="h-3 w-3 ml-1" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Timer className="h-8 w-8 text-blue-500" /><div><p className="text-sm text-muted-foreground">Total de Horas</p><p className="text-2xl font-bold">{totalHours.toFixed(1)}h</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Clock className="h-8 w-8 text-green-500" /><div><p className="text-sm text-muted-foreground">Horas Produtivas</p><p className="text-2xl font-bold">{billableHours.toFixed(1)}h</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><DollarSign className="h-8 w-8 text-emerald-500" /><div><p className="text-sm text-muted-foreground">Valor Total</p><p className="text-2xl font-bold">R$ {totalValue.toLocaleString('pt-BR')}</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><TrendingUp className="h-8 w-8 text-[#8B5CF6]" /><div><p className="text-sm text-muted-foreground">Utilização</p><p className="text-2xl font-bold">{utilization}%</p></div></div></CardContent></Card>
      </div>

      {/* Entries Table */}
      <Card>
        <CardHeader><CardTitle>Registros do Mês</CardTitle><CardDescription>{entries.length} registros em {monthNames[month-1]} {year}</CardDescription></CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Carregando...</div>
          ) : entries.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Clock className="h-12 w-12 mx-auto mb-4 opacity-30" />
              <p>Nenhum registro de horas neste mês</p>
              <Button className="mt-4" onClick={() => setShowForm(true)}><Plus className="h-4 w-4 mr-2" /> Registrar Horas</Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Data</TableHead>
                  <TableHead>Caso</TableHead>
                  <TableHead>Descrição</TableHead>
                  <TableHead className="text-right">Horas</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead className="text-right">Valor</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {entries.map((entry: TimeEntry) => (
                  <TableRow key={entry.id}>
                    <TableCell className="font-mono text-sm">{new Date(entry.date).toLocaleDateString('pt-BR')}</TableCell>
                    <TableCell className="max-w-[200px] truncate">{entry.caso_titulo || '—'}</TableCell>
                    <TableCell className="max-w-[250px] truncate">{entry.description}</TableCell>
                    <TableCell className="text-right font-semibold">{Number(entry.hours).toFixed(1)}h</TableCell>
                    <TableCell>
                      <Badge variant={entry.billing_type === 'billable' ? 'default' : entry.billing_type === 'pro_bono' ? 'secondary' : 'outline'}>
                        {entry.billing_type_display || entry.billing_type}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">R$ {Number(entry.total_value || 0).toLocaleString('pt-BR')}</TableCell>
                    <TableCell>
                      {entry.is_approved ? <Badge className="bg-green-500"><CheckCircle className="h-3 w-3 mr-1" /> Aprovado</Badge> : <Badge variant="outline">Pendente</Badge>}
                    </TableCell>
                    <TableCell>
                      {!entry.is_approved && (
                        <Button size="sm" variant="ghost" onClick={() => approveEntry.mutate(entry.id)} aria-label="Aprovar registro">
                          <CheckCircle className="h-4 w-4" />
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
