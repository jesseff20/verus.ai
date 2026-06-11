'use client';

import { useState, useCallback, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Lead, LeadStage, LeadPipelineData } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Switch } from '@/components/ui/switch';
import { Users, Plus, DollarSign, TrendingUp, Phone, Mail, ArrowRight, UserCheck, Flame, Snowflake, ThermometerSun, MoreHorizontal, MessageSquare, Calendar, Building2, Globe, AlertCircle, Zap, Sparkles, Loader2, Brain } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { toast } from 'sonner';

const tempIcons: Record<string, any> = { hot: Flame, warm: ThermometerSun, cold: Snowflake };
const tempColors: Record<string, string> = { hot: 'text-red-500', warm: 'text-amber-500', cold: 'text-blue-400' };

export default function CRMPipelinePage() {
  const queryClient = useQueryClient();
  const [showNewLead, setShowNewLead] = useState(false);
  const initialFormData = {
    name: '', email: '', phone: '', description: '', specialty: 'civel',
    source: 'indicacao', temperature: 'warm', estimated_value: '', stage: '',
    company: '', website: '', referral_source_detail: '',
    lead_channel: 'indicacao_cliente',
    urgency: false, complexity: 'medio',
    intake_form_data: {} as Record<string, string>,
  };
  const [formData, setFormData] = useState(initialFormData);

  // Copilot classification state
  const [isClassifying, setIsClassifying] = useState(false);
  const [classificationResult, setClassificationResult] = useState<{
    temperature: string;
    confidence: number;
    reasons: string[];
    suggested_approach: string;
  } | null>(null);
  const descriptionRef = useRef<HTMLTextAreaElement>(null);

  const { data: pipeline, isLoading } = useQuery({
    queryKey: ['crm-pipeline'],
    queryFn: async () => {
      const res = await api.get('/api/v1/processos/crm/pipeline/');
      return res.data as LeadPipelineData;
    },
    staleTime: 2 * 60 * 1000,
  });

  const [saveAndCreateAnother, setSaveAndCreateAnother] = useState(false);

  // Copilot classification mutation
  const classifyLead = useMutation({
    mutationFn: async () => {
      const intakeData = {
        ...formData.intake_form_data,
        ...(formData.company ? { company: formData.company } : {}),
        ...(formData.website ? { website: formData.website } : {}),
        ...(formData.referral_source_detail ? { referral_source_detail: formData.referral_source_detail } : {}),
      };
      const res = await api.post('/api/v1/processos/copilot/classificar-lead/', {
        description: formData.description,
        specialty: formData.specialty,
        urgency: formData.urgency,
        estimated_value: formData.estimated_value ? parseFloat(formData.estimated_value) : null,
        source: formData.source,
        intake_data: intakeData,
      });
      return res.data;
    },
    onSuccess: (data) => {
      setClassificationResult(data);
      // Auto-update temperature if confidence is high
      if (data.confidence >= 70) {
        setFormData(p => ({ ...p, temperature: data.temperature }));
        toast.success(`Temperatura classificada: ${data.temperature.toUpperCase()} (${data.confidence}% confiança)`);
      } else {
        toast.info('Classificação gerada - revise antes de aplicar');
      }
    },
    onError: () => {
      toast.error('Erro ao classificar lead com IA');
      setIsClassifying(false);
    },
  });

  // Follow-up generation mutation
  const generateFollowUp = useMutation({
    mutationFn: async (leadId: string) => {
      const res = await api.post('/api/v1/processos/copilot/followup-lead/', {
        lead_name: formData.name,
        temperature: formData.temperature,
        specialty: formData.specialty,
        stage_name: stages.find(s => s.id === formData.stage)?.name,
      });
      return res.data;
    },
    onSuccess: (data) => {
      navigator.clipboard.writeText(data.message);
      toast.success('Mensagem de follow-up copiada para a área de transferência!');
    },
    onError: () => {
      toast.error('Erro ao gerar follow-up');
    },
  });

  const handleClassifyLead = useCallback(() => {
    if (!formData.description && !formData.name) {
      toast.error('Preencha pelo menos o nome ou descrição para classificar');
      return;
    }
    setIsClassifying(true);
    setClassificationResult(null);
    // Delay pequeno para UX
    setTimeout(() => {
      classifyLead.mutate();
      setIsClassifying(false);
    }, 100);
  }, [formData, classifyLead]);

  const createLead = useMutation({
    mutationFn: async (data: any) => {
      const res = await api.post('/api/v1/processos/crm/leads/', data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm-pipeline'] });
      if (saveAndCreateAnother) {
        setFormData(initialFormData);
        toast.success('Lead criado! Formulário limpo para o próximo.');
      } else {
        setShowNewLead(false);
        setFormData(initialFormData);
        toast.success('Lead criado com sucesso');
      }
      setSaveAndCreateAnother(false);
    },
    onError: () => toast.error('Erro ao criar lead'),
  });

  const moveLead = useMutation({
    mutationFn: async ({ leadId, stageId }: { leadId: string; stageId: string }) => {
      const res = await api.patch(`/api/v1/processos/crm/leads/${leadId}/`, { stage: stageId });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm-pipeline'] });
      toast.success('Lead movido');
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || 'Erro ao processar');
    },
  });

  const convertLead = useMutation({
    mutationFn: async (leadId: string) => {
      const res = await api.post(`/api/v1/processos/crm/leads/${leadId}/converter/`);
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['crm-pipeline'] });
      toast.success(`Lead convertido! Cliente #${data.client_id?.slice(0,8)}`);
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || 'Erro ao processar');
    },
  });

  const stages = pipeline?.stages || [];
  const leadsByStage = pipeline?.leads_by_stage || {};
  const totalLeads = pipeline?.total_leads || 0;
  const totalValue = pipeline?.total_value || 0;
  const conversionRate = pipeline?.conversion_rate || 0;

  const handleSubmit = (e: React.FormEvent, createAnother = false) => {
    e.preventDefault();
    if (!formData.name) { toast.error('Nome é obrigatório'); return; }
    setSaveAndCreateAnother(createAnother);
    const intakeData = {
      ...formData.intake_form_data,
      ...(formData.company ? { company: formData.company } : {}),
      ...(formData.website ? { website: formData.website } : {}),
      ...(formData.referral_source_detail ? { referral_source_detail: formData.referral_source_detail } : {}),
      lead_channel: formData.lead_channel,
      urgency: formData.urgency,
      complexity: formData.complexity,
    };
    createLead.mutate({
      name: formData.name,
      email: formData.email,
      phone: formData.phone,
      description: formData.description,
      specialty: formData.specialty,
      source: formData.source,
      temperature: formData.temperature,
      estimated_value: formData.estimated_value ? parseFloat(formData.estimated_value) : null,
      stage: formData.stage || (stages[0]?.id || null),
      intake_form_data: intakeData,
    });
  };

  const intakeFieldsBySpecialty: Record<string, { key: string; label: string }[]> = {
    trabalhista: [
      { key: 'cargo', label: 'Cargo' },
      { key: 'tempo_empresa', label: 'Tempo de empresa' },
      { key: 'motivo_demissao', label: 'Motivo da demissão' },
    ],
    familia: [
      { key: 'tipo_acao', label: 'Tipo de ação (divórcio, guarda, etc.)' },
      { key: 'filhos', label: 'Quantidade de filhos' },
      { key: 'regime_bens', label: 'Regime de bens' },
    ],
    criminal: [
      { key: 'tipo_crime', label: 'Tipo de crime/infração' },
      { key: 'situacao_atual', label: 'Situação atual (preso, solto, etc.)' },
      { key: 'delegacia', label: 'Delegacia/Vara' },
    ],
    consumidor: [
      { key: 'empresa_reclamada', label: 'Empresa reclamada' },
      { key: 'produto_servico', label: 'Produto/serviço' },
      { key: 'valor_prejuizo', label: 'Valor do prejuízo' },
    ],
    previdenciario: [
      { key: 'tipo_beneficio', label: 'Tipo de benefício pretendido' },
      { key: 'tempo_contribuicao', label: 'Tempo de contribuição' },
      { key: 'inss_negou', label: 'INSS negou? Motivo' },
    ],
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2"><Users className="h-6 w-6" /> Pipeline de Leads</h1>
          <p className="text-muted-foreground">Funil de vendas do escritório</p>
        </div>
        <Dialog open={showNewLead} onOpenChange={setShowNewLead}>
          <DialogTrigger asChild><Button><Plus className="h-4 w-4 mr-2" /> Novo Lead</Button></DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto sm:max-w-2xl w-[calc(100vw-2rem)]">
            <DialogHeader>
              <DialogTitle>Novo Lead</DialogTitle>
              <DialogDescription>Cadastre uma nova oportunidade</DialogDescription>
            </DialogHeader>
            <form onSubmit={e => handleSubmit(e)} className="space-y-5">
              {/* Dados básicos */}
              <div>
                <p className="text-sm font-semibold mb-2">Dados do contato</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="sm:col-span-2"><Label>Nome *</Label><Input value={formData.name} onChange={e => setFormData(p => ({...p, name: e.target.value}))} placeholder="Nome completo" /></div>
                  <div><Label>E-mail</Label><Input type="email" value={formData.email} onChange={e => setFormData(p => ({...p, email: e.target.value}))} /></div>
                  <div><Label>Telefone</Label><Input value={formData.phone} onChange={e => setFormData(p => ({...p, phone: e.target.value}))} placeholder="(XX) XXXXX-XXXX" /></div>
                  <div><Label>Empresa (se PJ)</Label><Input value={formData.company} onChange={e => setFormData(p => ({...p, company: e.target.value}))} placeholder="Razão social ou nome fantasia" /></div>
                  <div><Label>Site / Rede Social</Label><Input value={formData.website} onChange={e => setFormData(p => ({...p, website: e.target.value}))} placeholder="https:// ou @perfil" /></div>
                </div>
              </div>

              <Separator />

              {/* Como o lead chegou */}
              <div>
                <p className="text-sm font-semibold mb-2">Como o lead chegou?</p>
                <RadioGroup value={formData.lead_channel} onValueChange={v => setFormData(p => ({...p, lead_channel: v, source: v === 'indicacao_cliente' || v === 'indicacao_parceiro' ? 'indicacao' : v === 'busca_organica' ? 'google' : v === 'anuncio_pago' ? 'google' : v === 'redes_sociais' ? 'instagram' : v === 'evento_palestra' ? 'evento' : 'outro'}))} className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {[
                    { value: 'indicacao_cliente', label: 'Indicação de cliente' },
                    { value: 'indicacao_parceiro', label: 'Indicação de parceiro' },
                    { value: 'busca_organica', label: 'Busca orgânica (Google)' },
                    { value: 'anuncio_pago', label: 'Anúncio pago' },
                    { value: 'redes_sociais', label: 'Redes sociais' },
                    { value: 'evento_palestra', label: 'Evento / palestra' },
                    { value: 'outros', label: 'Outros' },
                  ].map(opt => (
                    <div key={opt.value} className="flex items-center space-x-2 rounded-md border p-2">
                      <RadioGroupItem value={opt.value} id={`channel-${opt.value}`} />
                      <Label htmlFor={`channel-${opt.value}`} className="cursor-pointer text-sm font-normal">{opt.label}</Label>
                    </div>
                  ))}
                </RadioGroup>
                {(formData.lead_channel === 'indicacao_cliente' || formData.lead_channel === 'indicacao_parceiro') && (
                  <div className="mt-2">
                    <Label>Quem indicou?</Label>
                    <Input value={formData.referral_source_detail} onChange={e => setFormData(p => ({...p, referral_source_detail: e.target.value}))} placeholder="Nome de quem indicou" />
                  </div>
                )}
              </div>

              <Separator />

              {/* Classificação */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-semibold">Classificação</p>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleClassifyLead}
                    disabled={isClassifying || classifyLead.isPending}
                    className="gap-1.5 h-7 text-xs"
                  >
                    {isClassifying || classifyLead.isPending ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <Brain className="h-3 w-3 text-purple-500" />
                    )}
                    Classificar com IA
                  </Button>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <Label>Especialidade</Label>
                    <Select value={formData.specialty} onValueChange={v => setFormData(p => ({...p, specialty: v, intake_form_data: {}}))}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="civel">Cível</SelectItem><SelectItem value="criminal">Criminal</SelectItem>
                        <SelectItem value="trabalhista">Trabalhista</SelectItem><SelectItem value="tributario">Tributário</SelectItem>
                        <SelectItem value="administrativo">Administrativo</SelectItem><SelectItem value="previdenciario">Previdenciário</SelectItem>
                        <SelectItem value="familia">Família e Sucessões</SelectItem><SelectItem value="empresarial">Empresarial</SelectItem>
                        <SelectItem value="ambiental">Ambiental</SelectItem><SelectItem value="consumidor">Direito do Consumidor</SelectItem>
                        <SelectItem value="imobiliario">Imobiliário</SelectItem><SelectItem value="outros">Outros</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Temperatura</Label>
                    <Select value={formData.temperature} onValueChange={v => setFormData(p => ({...p, temperature: v}))}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="hot">Quente</SelectItem><SelectItem value="warm">Morno</SelectItem><SelectItem value="cold">Frio</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Complexidade estimada</Label>
                    <Select value={formData.complexity} onValueChange={v => setFormData(p => ({...p, complexity: v}))}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="simples">Simples</SelectItem>
                        <SelectItem value="medio">Médio</SelectItem>
                        <SelectItem value="complexo">Complexo</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div><Label>Valor Estimado (R$)</Label><Input type="number" value={formData.estimated_value} onChange={e => setFormData(p => ({...p, estimated_value: e.target.value}))} /></div>
                </div>
                <div className="flex items-center gap-3 mt-3 rounded-md border p-3">
                  <Switch checked={formData.urgency} onCheckedChange={v => setFormData(p => ({...p, urgency: v}))} id="urgency" />
                  <Label htmlFor="urgency" className="cursor-pointer flex items-center gap-2">
                    <Zap className="h-4 w-4 text-amber-500" /> Precisa de atendimento imediato?
                  </Label>
                  {formData.urgency && <Badge variant="destructive" className="ml-auto text-xs">URGENTE</Badge>}
                </div>

                {/* Resultado da classificação IA */}
                {classificationResult && (
                  <div className="mt-4 p-4 rounded-lg border bg-purple-50 dark:bg-purple-950/20 border-purple-200 dark:border-purple-800">
                    <div className="flex items-start gap-3">
                      <Brain className="h-5 w-5 text-purple-500 shrink-0 mt-0.5" />
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold">Classificação IA:</span>
                          <Badge className={
                            classificationResult.temperature === 'hot' ? 'bg-red-100 text-red-800' :
                            classificationResult.temperature === 'warm' ? 'bg-amber-100 text-amber-800' :
                            'bg-blue-100 text-blue-800'
                          }>
                            {classificationResult.temperature.toUpperCase()}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {classificationResult.confidence}% confiança
                          </span>
                        </div>
                        {classificationResult.reasons.length > 0 && (
                          <div className="text-xs space-y-1">
                            <p className="font-medium">Fatores considerados:</p>
                            <ul className="list-disc list-inside text-muted-foreground">
                              {classificationResult.reasons.map((reason, i) => (
                                <li key={i}>{reason}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {classificationResult.suggested_approach && (
                          <div className="text-xs">
                            <p className="font-medium mb-1">Abordagem sugerida:</p>
                            <p className="text-muted-foreground italic">{classificationResult.suggested_approach}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Intake dinâmico por especialidade */}
              {intakeFieldsBySpecialty[formData.specialty] && (
                <>
                  <Separator />
                  <div>
                    <p className="text-sm font-semibold mb-2">Informações específicas ({formData.specialty})</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {intakeFieldsBySpecialty[formData.specialty].map(field => (
                        <div key={field.key}>
                          <Label>{field.label}</Label>
                          <Input
                            value={formData.intake_form_data[field.key] || ''}
                            onChange={e => setFormData(p => ({...p, intake_form_data: {...p.intake_form_data, [field.key]: e.target.value}}))}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}

              <Separator />

              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label>Descrição do Caso</Label>
                  {formData.name && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => generateFollowUp.mutate('new')}
                      disabled={generateFollowUp.isPending}
                      className="h-7 text-xs gap-1"
                    >
                      {generateFollowUp.isPending ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      ) : (
                        <MessageSquare className="h-3 w-3" />
                      )}
                      Gerar Follow-up
                    </Button>
                  )}
                </div>
                <Textarea
                  ref={descriptionRef}
                  value={formData.description}
                  onChange={e => setFormData(p => ({...p, description: e.target.value}))}
                  rows={3}
                  placeholder="Descreva brevemente a situação do lead..."
                />
              </div>

              <div className="flex flex-col-reverse sm:flex-row justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setShowNewLead(false)}>Cancelar</Button>
                <Button type="button" variant="secondary" disabled={createLead.isPending} onClick={e => handleSubmit(e as any, true)}>
                  {createLead.isPending ? 'Salvando...' : 'Salvar e Criar Outro'}
                </Button>
                <Button type="submit" disabled={createLead.isPending}>{createLead.isPending ? 'Salvando...' : 'Criar Lead'}</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Users className="h-8 w-8 text-blue-500" /><div><p className="text-sm text-muted-foreground">Total de Leads</p><p className="text-2xl font-bold">{totalLeads}</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><DollarSign className="h-8 w-8 text-green-500" /><div><p className="text-sm text-muted-foreground">Valor Pipeline</p><p className="text-2xl font-bold">R$ {totalValue.toLocaleString('pt-BR')}</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><TrendingUp className="h-8 w-8 text-[#8B5CF6]" /><div><p className="text-sm text-muted-foreground">Taxa de Conversão</p><p className="text-2xl font-bold">{conversionRate}%</p></div></div></CardContent></Card>
      </div>

      {/* Kanban Board */}
      <div className="flex gap-4 overflow-x-auto pb-4">
        {isLoading ? (
          <div className="text-center py-12 w-full text-muted-foreground">Carregando pipeline...</div>
        ) : stages.length === 0 ? (
          <div className="text-center py-12 w-full text-muted-foreground">
            <Users className="h-12 w-12 mx-auto mb-4 opacity-30" />
            <p>Nenhuma etapa configurada. Configure o funil de vendas.</p>
          </div>
        ) : (
          stages.map((stage: LeadStage) => {
            const stageLeads = leadsByStage[stage.id] || [];
            return (
              <div key={stage.id} className="flex-shrink-0 w-[300px]">
                <div className="rounded-lg border bg-card">
                  <div className="p-3 border-b flex items-center justify-between" style={{ borderTopColor: stage.color, borderTopWidth: '3px', borderTopLeftRadius: '0.5rem', borderTopRightRadius: '0.5rem' }}>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm">{stage.name}</span>
                      <Badge variant="secondary" className="text-xs">{stageLeads.length}</Badge>
                    </div>
                  </div>
                  <ScrollArea className="h-[500px]">
                    <div className="p-2 space-y-2">
                      {stageLeads.map((lead: Lead) => {
                        const TempIcon = tempIcons[lead.temperature] || ThermometerSun;
                        return (
                          <Card key={lead.id} className="cursor-pointer hover:shadow-md transition-shadow">
                            <CardContent className="p-3 space-y-2">
                              <div className="flex items-start justify-between">
                                <div className="flex items-center gap-2">
                                  <Avatar className="h-8 w-8"><AvatarFallback className="text-xs">{lead.name.split(' ').map(n => n[0]).join('').slice(0,2)}</AvatarFallback></Avatar>
                                  <div><p className="font-medium text-sm">{lead.name}</p><p className="text-xs text-muted-foreground">{lead.source_display}</p></div>
                                </div>
                                <TempIcon className={`h-4 w-4 ${tempColors[lead.temperature]}`} />
                              </div>
                              {lead.description && <p className="text-xs text-muted-foreground line-clamp-2">{lead.description}</p>}
                              <div className="flex items-center justify-between text-xs">
                                {lead.estimated_value && <span className="font-semibold text-green-600">R$ {Number(lead.estimated_value).toLocaleString('pt-BR')}</span>}
                                <DropdownMenu>
                                  <DropdownMenuTrigger asChild><Button size="sm" variant="ghost" className="h-6 w-6 p-0" aria-label="Ações do lead"><MoreHorizontal className="h-3 w-3" /></Button></DropdownMenuTrigger>
                                  <DropdownMenuContent>
                                    {stages.filter(s => s.id !== stage.id).map(s => (
                                      <DropdownMenuItem key={s.id} onClick={() => moveLead.mutate({ leadId: lead.id, stageId: s.id })}>
                                        <ArrowRight className="h-3 w-3 mr-2" /> Mover para {s.name}
                                      </DropdownMenuItem>
                                    ))}
                                    <DropdownMenuItem onClick={() => convertLead.mutate(lead.id)} className="text-green-600">
                                      <UserCheck className="h-3 w-3 mr-2" /> Converter em Cliente
                                    </DropdownMenuItem>
                                  </DropdownMenuContent>
                                </DropdownMenu>
                              </div>
                              <div className="flex gap-1">
                                {lead.email && <Badge variant="outline" className="text-xs px-1"><Mail className="h-2.5 w-2.5" /></Badge>}
                                {lead.phone && <Badge variant="outline" className="text-xs px-1"><Phone className="h-2.5 w-2.5" /></Badge>}
                              </div>
                            </CardContent>
                          </Card>
                        );
                      })}
                      {stageLeads.length === 0 && (
                        <div className="text-center py-8 text-xs text-muted-foreground">Nenhum lead nesta etapa</div>
                      )}
                    </div>
                  </ScrollArea>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
