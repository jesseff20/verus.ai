'use client';

import { useState, useCallback, useRef, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useToast } from '@/hooks/use-toast';
import { useSimulationDetail } from '@/hooks/use-simulations';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Scale, ChevronLeft, ChevronRight, Loader2, CheckCircle2,
  FileDown, RotateCcw, FileText, Swords,
  AlertCircle, Send, MessageSquare, User, History, Shield,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import SimulationHistoryList from '@/components/SimulationHistoryList';
import SimulationCountSelector from '@/components/simulations/SimulationCountSelector';
import SimulationTabBar from '@/components/simulations/SimulationTabBar';
import { useMultiSimulation } from '@/hooks/use-multi-simulation';
import { categorizeVote, countVotesByCategory, VOTE_CATEGORIES } from '@/lib/vote-utils';

const STEPS = [
  { title: 'Configuração', icon: Swords },
  { title: 'Julgamento', icon: Shield },
  { title: 'Resultado', icon: FileText },
];

const FORCAS = [
  { value: 'Exercito', label: 'Exercito Brasileiro' },
  { value: 'Marinha', label: 'Marinha do Brasil' },
  { value: 'Aeronautica', label: 'Forca Aerea Brasileira' },
  { value: 'PM', label: 'Policia Militar' },
  { value: 'BM', label: 'Corpo de Bombeiros Militar' },
];

const CRIMES_MILITARES = [
  { value: 'desercao', label: 'Desercao (art. 187 CPM)' },
  { value: 'insubordinacao', label: 'Insubordinacao (art. 163 CPM)' },
  { value: 'abandono_posto', label: 'Abandono de Posto (art. 195 CPM)' },
  { value: 'furto', label: 'Furto (art. 240 CPM)' },
  { value: 'lesao_corporal', label: 'Lesao Corporal (art. 209 CPM)' },
  { value: 'estelionato', label: 'Estelionato (art. 251 CPM)' },
  { value: 'peculato', label: 'Peculato (art. 303 CPM)' },
  { value: 'embriaguez', label: 'Embriaguez em Servico (art. 202 CPM)' },
  { value: 'violencia_inferior', label: 'Violencia contra Inferior (art. 175 CPM)' },
  { value: 'outros', label: 'Outro crime militar' },
];

interface VoteResult {
  minister: string;
  vote: string;
  is_relator: boolean;
  role?: string;
}

interface SimInstanceState {
  simulationId: string | null;
  isSimulating: boolean;
  analysisProgress: number;
  analysisStage: string;
  currentPhaseDescription: string;
  relatorioText: string;
  interrogatorioText: string;
  debatesText: string;
  voteTexts: Record<string, string>;
  currentVoter: string | null;
  votes: VoteResult[];
  sentencaText: string;
  strategicReport: string;
  questionText: string;
  questionAnswer: string;
  isQuestioning: boolean;
  isExportingPdf: boolean;
}

function createEmptyInstance(): SimInstanceState {
  return {
    simulationId: null, isSimulating: false, analysisProgress: 0,
    analysisStage: '', currentPhaseDescription: '',
    relatorioText: '', interrogatorioText: '', debatesText: '',
    voteTexts: {}, currentVoter: null, votes: [],
    sentencaText: '', strategicReport: '',
    questionText: '', questionAnswer: '', isQuestioning: false, isExportingPdf: false,
  };
}

export default function MilitarSimulationPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>}>
      <MilitarSimulationPageInner />
    </Suspense>
  );
}

function MilitarSimulationPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const historyId = searchParams.get('id');
  const { toast } = useToast();

  const multiSim = useMultiSimulation();
  const [loadedFromHistory, setLoadedFromHistory] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);

  // Config
  const [forca, setForca] = useState('Exercito');
  const [crimeMilitar, setCrimeMilitar] = useState('');
  const [caseDescription, setCaseDescription] = useState('');

  // Multi-simulation instances state
  const [simInstances, setSimInstances] = useState<SimInstanceState[]>([createEmptyInstance()]);

  const updateInstance = useCallback((index: number, updates: Partial<SimInstanceState>) => {
    setSimInstances(prev => {
      const next = [...prev];
      if (next[index]) next[index] = { ...next[index], ...updates };
      return next;
    });
  }, []);

  const appendInstanceField = useCallback((index: number, field: keyof SimInstanceState, value: string) => {
    setSimInstances(prev => {
      const next = [...prev];
      if (next[index]) next[index] = { ...next[index], [field]: (next[index][field] as string) + value };
      return next;
    });
  }, []);

  const appendVoteText = useCallback((index: number, voter: string, text: string) => {
    setSimInstances(prev => {
      const next = [...prev];
      if (next[index]) {
        const voteTexts = { ...next[index].voteTexts };
        voteTexts[voter] = (voteTexts[voter] || '') + text;
        next[index] = { ...next[index], voteTexts };
      }
      return next;
    });
  }, []);

  const addVoteResult = useCallback((index: number, vote: VoteResult) => {
    setSimInstances(prev => {
      const next = [...prev];
      if (next[index]) next[index] = { ...next[index], votes: [...next[index].votes, vote] };
      return next;
    });
  }, []);

  // Active instance shortcut
  const activeInstance = simInstances[multiSim.activeSimIndex] || createEmptyInstance();

  // Batching refs per instance
  const pendingBuffersRef = useRef<Map<number, {
    relatorio: string; interrogatorio: string; debates: string;
    vote: string; sentenca: string; report: string;
    currentVoter: string | null;
  }>>(new Map());
  const streamFlushTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => { return () => { if (streamFlushTimerRef.current) clearTimeout(streamFlushTimerRef.current); }; }, []);

  const getBuffer = useCallback((idx: number) => {
    if (!pendingBuffersRef.current.has(idx)) {
      pendingBuffersRef.current.set(idx, { relatorio: '', interrogatorio: '', debates: '', vote: '', sentenca: '', report: '', currentVoter: null });
    }
    return pendingBuffersRef.current.get(idx)!;
  }, []);

  const flushAllBuffers = useCallback(() => {
    if (streamFlushTimerRef.current) { clearTimeout(streamFlushTimerRef.current); streamFlushTimerRef.current = null; }
    pendingBuffersRef.current.forEach((buf, idx) => {
      if (buf.relatorio) { appendInstanceField(idx, 'relatorioText', buf.relatorio); buf.relatorio = ''; }
      if (buf.interrogatorio) { appendInstanceField(idx, 'interrogatorioText', buf.interrogatorio); buf.interrogatorio = ''; }
      if (buf.debates) { appendInstanceField(idx, 'debatesText', buf.debates); buf.debates = ''; }
      if (buf.vote && buf.currentVoter) { appendVoteText(idx, buf.currentVoter, buf.vote); buf.vote = ''; }
      if (buf.sentenca) { appendInstanceField(idx, 'sentencaText', buf.sentenca); buf.sentenca = ''; }
      if (buf.report) { appendInstanceField(idx, 'strategicReport', buf.report); buf.report = ''; }
    });
  }, [appendInstanceField, appendVoteText]);

  const scheduleStreamFlush = useCallback(() => {
    if (!streamFlushTimerRef.current) {
      streamFlushTimerRef.current = setTimeout(() => {
        streamFlushTimerRef.current = null;
        flushAllBuffers();
      }, 50);
    }
  }, [flushAllBuffers]);

  // Load from history
  const { data: historySimulation } = useSimulationDetail(historyId);
  const historyLoadedRef = useRef(false);

  useEffect(() => {
    if (!historySimulation || historyLoadedRef.current) return;
    if (historySimulation.status !== 'completed') return;
    historyLoadedRef.current = true;
    const result = historySimulation.result || {};
    const config = historySimulation.config || {};
    const inst = createEmptyInstance();
    inst.simulationId = historySimulation.id;
    inst.relatorioText = result.relatorio || '';
    inst.interrogatorioText = result.interrogatorio || '';
    inst.debatesText = result.debates || '';
    inst.sentencaText = result.sentenca || '';
    inst.strategicReport = result.strategic_report || '';
    if (result.votes && Array.isArray(result.votes)) {
      inst.votes = result.votes.map((v: any) => ({ minister: v.minister || '', vote: v.vote || '', is_relator: v.is_relator || false, role: v.role || '' }));
    }
    setForca(config.forca || 'Exercito');
    setCrimeMilitar(config.crime_militar || '');
    setCaseDescription(config.case_description || '');
    setSimInstances([inst]);
    setCurrentStep(2);
    setLoadedFromHistory(true);
    toast({ title: 'Simulação carregada', description: `"${historySimulation.title}" carregada.` });
  }, [historySimulation, toast]);

  // --- Run a single simulation SSE for a given index ---
  const runSingleSimulation = useCallback(async (index: number) => {
    updateInstance(index, { isSimulating: true, analysisProgress: 0, analysisStage: 'Iniciando...' });
    multiSim.updateTabStatus(index, 'running');

    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      const headers = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

      const crimeLabel = CRIMES_MILITARES.find(c => c.value === crimeMilitar)?.label || crimeMilitar;
      const createRes = await fetch('/api/v1/simulations/simulations/', {
        method: 'POST', headers,
        body: JSON.stringify({
          simulation_type: 'militar',
          title: `Auditoria Militar - ${crimeLabel} (${forca})${multiSim.simulationCount > 1 ? ` [#${index + 1}]` : ''}`,
          config: { forca, crime_militar: crimeMilitar, case_description: caseDescription },
        }),
      });
      if (!createRes.ok) throw new Error(`HTTP ${createRes.status}`);
      const simData = await createRes.json();
      const simId = simData.id;
      updateInstance(index, { simulationId: simId });

      const response = await fetch(`/api/v1/simulations/simulations/${simId}/militar/start/`, { method: 'POST', headers, body: JSON.stringify({}) });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) throw new Error('No reader');

      const buf = getBuffer(index);
      let sseBuffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        sseBuffer += decoder.decode(value, { stream: true });
        const lines = sseBuffer.split('\n');
        sseBuffer = lines.pop() || '';
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const jsonStr = line.slice(6).trim();
          if (!jsonStr || jsonStr === '[DONE]') continue;
          try {
            const event = JSON.parse(jsonStr);
            const eventType = event.event || event.type;
            if (eventType === 'progress' && event.type === 'phase_change') {
              updateInstance(index, { analysisProgress: event.progress || 0, analysisStage: event.label || '', currentPhaseDescription: event.description || '' });
            } else if (eventType === 'phase') {
              updateInstance(index, { analysisStage: event.content || '' });
            } else if (eventType === 'relatorio') { buf.relatorio += (event.content || ''); scheduleStreamFlush(); }
            else if (eventType === 'interrogatorio') { buf.interrogatorio += (event.content || ''); scheduleStreamFlush(); }
            else if (eventType === 'debates') { buf.debates += (event.content || ''); scheduleStreamFlush(); }
            else if (eventType === 'vote_text') {
              const m = event.minister || '';
              if (m) { buf.currentVoter = m; updateInstance(index, { currentVoter: m }); buf.vote += (event.content || ''); scheduleStreamFlush(); }
            }
            else if (eventType === 'vote_result') { addVoteResult(index, { minister: event.minister, vote: event.vote, is_relator: event.is_relator, role: event.role }); }
            else if (eventType === 'sentenca') { buf.sentenca += (event.content || ''); scheduleStreamFlush(); }
            else if (eventType === 'relatorio_estrategico') { buf.report += (event.content || ''); scheduleStreamFlush(); }
            else if (eventType === 'complete') {
              flushAllBuffers();
              updateInstance(index, { analysisProgress: 100, isSimulating: false });
              multiSim.updateTabStatus(index, 'completed');
              // Move to results if this is the active tab or the first to complete
              setCurrentStep(2);
              if (index === multiSim.activeSimIndex) {
                toast({ title: 'Simulação concluida', description: `Simulação #${index + 1} concluida.` });
              }
            }
            else if (eventType === 'error') {
              updateInstance(index, { isSimulating: false });
              multiSim.updateTabStatus(index, 'error');
              toast({ title: 'Erro', description: event.content || 'Erro.', variant: 'destructive' });
            }
          } catch { /* ignore */ }
        }
      }
    } catch (error: any) {
      updateInstance(index, { isSimulating: false });
      multiSim.updateTabStatus(index, 'error');
      toast({ title: 'Erro', description: error.message || 'Falha ao conectar.', variant: 'destructive' });
    }
  }, [forca, crimeMilitar, caseDescription, toast, scheduleStreamFlush, flushAllBuffers, getBuffer, updateInstance, addVoteResult, multiSim]);

  // --- Start all simulations ---
  const startAllSimulations = useCallback(() => {
    const count = multiSim.simulationCount;
    const instances = Array.from({ length: count }, () => createEmptyInstance());
    setSimInstances(instances);
    multiSim.resetTabs(count);
    pendingBuffersRef.current.clear();
    setCurrentStep(1);

    // Launch all SSE connections in parallel
    for (let i = 0; i < count; i++) {
      setTimeout(() => runSingleSimulation(i), i * 200);
    }
  }, [multiSim, runSingleSimulation]);

  // --- Question handler ---
  const handleQuestion = useCallback(async () => {
    const inst = simInstances[multiSim.activeSimIndex];
    if (!inst?.questionText?.trim() || !inst?.simulationId) return;
    updateInstance(multiSim.activeSimIndex, { isQuestioning: true, questionAnswer: '' });
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      const res = await fetch(`/api/v1/simulations/simulations/${inst.simulationId}/question/`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({ question: inst.questionText }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      updateInstance(multiSim.activeSimIndex, { questionAnswer: data.answer || 'Sem resposta.', isQuestioning: false });
    } catch (error: any) {
      toast({ title: 'Erro', description: error.message, variant: 'destructive' });
      updateInstance(multiSim.activeSimIndex, { isQuestioning: false });
    }
  }, [simInstances, multiSim.activeSimIndex, updateInstance, toast]);

  // --- PDF Export ---
  const exportPdf = useCallback(async () => {
    const inst = simInstances[multiSim.activeSimIndex];
    if (!inst) return;
    if (!inst.sentencaText && !inst.strategicReport) {
      toast({ title: 'Nada para exportar', variant: 'destructive' }); return;
    }
    updateInstance(multiSim.activeSimIndex, { isExportingPdf: true });
    if (inst.simulationId) {
      try {
        const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
        const res = await fetch(`/api/v1/simulations/simulations/${inst.simulationId}/generate-pdf/`, {
          method: 'POST', headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        });
        if (res.ok) {
          const blob = await res.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a'); a.href = url;
          a.download = `simulação_militar_${multiSim.activeSimIndex + 1}_${new Date().toISOString().split('T')[0]}.pdf`;
          document.body.appendChild(a); a.click(); document.body.removeChild(a);
          setTimeout(() => URL.revokeObjectURL(url), 10000);
          toast({ title: 'PDF exportado' });
          updateInstance(multiSim.activeSimIndex, { isExportingPdf: false }); return;
        }
      } catch { /* fall through */ }
    }
    const htmlContent = `<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><title>Simulação Militar</title><style>body{font-family:'Times New Roman',serif;font-size:12pt;line-height:1.5;max-width:210mm;margin:0 auto;padding:2.5cm 2cm;text-align:justify;}h1{text-align:center;font-size:16pt;}h2{font-size:14pt;border-bottom:1px solid #ccc;padding-bottom:6pt;}.footer{margin-top:40px;border-top:1px solid #ccc;padding-top:12px;font-size:9pt;color:#999;text-align:center;}</style></head><body><h1>SIMULACAO AUDITORIA MILITAR</h1>${inst.sentencaText ? `<h2>Sentenca</h2><div>${inst.sentencaText.replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br/>')}</div>` : ''}${inst.strategicReport ? `<h2>Relatorio Estrategico</h2><div>${inst.strategicReport.replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br/>')}</div>` : ''}<div class="footer"><p>Documento gerado pelo Verus.AI.</p></div></body></html>`;
    const blob = new Blob([htmlContent], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob); const a = document.createElement('a');
    a.href = url; a.download = `simulação_militar_${multiSim.activeSimIndex + 1}_${new Date().toISOString().split('T')[0]}.pdf`;
    document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(url);
    toast({ title: 'PDF exportado' });
    updateInstance(multiSim.activeSimIndex, { isExportingPdf: false });
  }, [simInstances, multiSim.activeSimIndex, updateInstance, toast]);

  // --- Reset ---
  const resetSimulation = useCallback(() => {
    setCurrentStep(0); setForca('Exercito'); setCrimeMilitar(''); setCaseDescription('');
    setSimInstances([createEmptyInstance()]);
    multiSim.setSimulationCount(1);
    pendingBuffersRef.current.clear();
  }, [multiSim]);

  const canAdvance = () => currentStep === 0 && crimeMilitar !== '' && caseDescription.trim().length > 20;
  const nextStep = () => { if (currentStep === 0) { setTimeout(() => startAllSimulations(), 300); } };

  const renderStepper = () => (
    <div className="flex items-center justify-center gap-1 py-3 sm:py-4 px-2 sm:px-6 bg-card border-b overflow-x-auto">
      {STEPS.map((step, i) => {
        const Icon = step.icon; const isActive = i === currentStep; const isCompleted = i < currentStep;
        return (<div key={i} className="flex items-center shrink-0"><button onClick={() => i < currentStep && setCurrentStep(i)} disabled={i > currentStep} className={`flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-2 rounded-lg text-xs sm:text-sm font-medium transition-colors ${isActive ? 'bg-primary text-primary-foreground' : isCompleted ? 'bg-primary/10 text-primary cursor-pointer hover:bg-primary/20' : 'text-muted-foreground'}`}>{isCompleted ? <CheckCircle2 className="h-4 w-4" /> : <Icon className="h-4 w-4" />}<span className="hidden sm:inline">{step.title}</span></button>{i < STEPS.length - 1 && <ChevronRight className="h-4 w-4 text-muted-foreground mx-0.5 sm:mx-1 shrink-0" />}</div>);
      })}
    </div>
  );

  const renderStep0 = () => (
    <div className="max-w-3xl mx-auto space-y-6">
      <div><div className="flex items-center gap-3 mb-2"><Swords className="h-8 w-8 text-primary" /><h2 className="text-2xl font-bold">Auditoria de Justica Militar</h2></div><p className="text-muted-foreground">Simule um julgamento na Auditoria Militar com Conselho de Justica (1 Juiz Auditor + 4 Oficiais).</p></div>
      <Card className="border-amber-200 bg-amber-50/50 dark:border-amber-900 dark:bg-amber-950/20">
        <CardContent className="flex gap-4 py-4">
          <AlertCircle className="h-6 w-6 text-amber-500 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-amber-800 dark:text-amber-200">Composicao unica: 1 togado + 4 oficiais</p>
            <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">O Conselho de Justica e composto por 1 Juiz Auditor (togado) e 4 Oficiais Militares. Os oficiais NAO sao advogados -- trazem a perspectiva da caserna. Votacao secreta sobre culpa/inocencia.</p>
          </div>
        </CardContent>
      </Card>
      <div className="space-y-4">
        <div className="space-y-2">
          <Label>Forca Armada *</Label>
          <Select value={forca} onValueChange={setForca}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{FORCAS.map(f => (<SelectItem key={f.value} value={f.value}>{f.label}</SelectItem>))}</SelectContent></Select>
        </div>
        <div className="space-y-2">
          <Label>Crime Militar *</Label>
          <Select value={crimeMilitar} onValueChange={setCrimeMilitar}><SelectTrigger><SelectValue placeholder="Selecione o crime" /></SelectTrigger><SelectContent>{CRIMES_MILITARES.map(c => (<SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>))}</SelectContent></Select>
        </div>
        <div className="space-y-2">
          <Label>Descrição do Caso *</Label>
          <p className="text-xs text-muted-foreground">Inclua fatos do IPM, patente/unidade do acusado, provas e circunstancias.</p>
          <Textarea value={caseDescription} onChange={e => setCaseDescription(e.target.value)} placeholder="Ex: Soldado do 12o BI acusado de desercao apos ausentar-se da unidade por 15 dias sem autorizacao..." className="min-h-[200px]" />
          <p className="text-xs text-muted-foreground text-right">{caseDescription.length} caracteres (minimo 20)</p>
        </div>
        <Separator />
        <SimulationCountSelector value={multiSim.simulationCount} onChange={multiSim.setSimulationCount} />
      </div>
    </div>
  );

  const renderStep1 = () => {
    const inst = activeInstance;
    const voteCounts = countVotesByCategory(inst.votes);
    const condenacao = voteCounts.desprovimento || 0;
    const absolvicao = voteCounts.provimento || 0;
    const parcial = voteCounts.parcial || 0;
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <div><h2 className="text-2xl font-bold mb-1">Julgamento em Andamento</h2><p className="text-muted-foreground">{inst.analysisStage || 'Preparando...'}</p></div>
        {inst.isSimulating && inst.currentVoter && (<div className="flex items-center gap-3 py-3 px-4 bg-muted/50 rounded-lg border-2 speaker-active"><div className="h-10 w-10 rounded-full bg-primary flex items-center justify-center animate-pulse"><Shield className="h-5 w-5 text-white gavel-thinking" /></div><div className="flex-1"><span className="text-sm font-medium">{inst.currentVoter}</span><p className="text-xs text-muted-foreground">{inst.currentPhaseDescription || 'Votando...'}</p></div><div className="flex gap-1 ml-auto"><div className="h-2 w-2 rounded-full bg-primary thinking-dot" /><div className="h-2 w-2 rounded-full bg-primary thinking-dot" /><div className="h-2 w-2 rounded-full bg-primary thinking-dot" /></div></div>)}
        <Card><CardContent className="p-6 space-y-4"><div className="flex items-center justify-between"><span className="text-sm font-medium">Progresso</span><span className="text-sm text-muted-foreground">{inst.analysisProgress}%</span></div><Progress value={inst.analysisProgress} /></CardContent></Card>
        {inst.votes.length > 0 && (<Card><CardHeader className="pb-3"><CardTitle className="text-base">Placar do Conselho</CardTitle></CardHeader><CardContent><div className="flex items-center justify-center gap-6 sm:gap-8 mb-4"><div className="text-center"><p className="text-3xl font-bold text-red-600 score-update" key={`cond-${condenacao}`}>{condenacao}</p><p className="text-xs text-muted-foreground">Condenacao</p></div><div className="text-2xl text-muted-foreground font-bold">x</div>{parcial > 0 && (<><div className="text-center"><p className="text-3xl font-bold text-amber-600 score-update" key={`parc-${parcial}`}>{parcial}</p><p className="text-xs text-muted-foreground">Parcial</p></div><div className="text-2xl text-muted-foreground font-bold">x</div></>)}<div className="text-center"><p className="text-3xl font-bold text-green-600 score-update" key={`abs-${absolvicao}`}>{absolvicao}</p><p className="text-xs text-muted-foreground">Absolvicao</p></div></div><Separator className="mb-3" /><div className="space-y-2">{inst.votes.map((v, i) => (<div key={i} className="flex items-center justify-between py-1.5 px-3 rounded-lg bg-muted/50 vote-reveal" style={{ animationDelay: `${i * 0.1}s` }}><div className="flex items-center gap-2"><User className="h-4 w-4 text-muted-foreground" /><span className="text-sm font-medium">{v.minister}</span>{v.role && <Badge variant="outline" className="text-[10px]">{v.role}</Badge>}</div><Badge className={`text-xs border-0 vote-reveal ${categorizeVote(v.vote).badgeClass}`}>{v.vote}</Badge></div>))}</div></CardContent></Card>)}
        {inst.currentVoter && inst.voteTexts[inst.currentVoter] && (<Card><CardHeader className="pb-2"><CardTitle className="text-sm flex items-center gap-2"><Shield className="h-4 w-4" />Voto de {inst.currentVoter} {inst.isSimulating && '(em andamento...)'}</CardTitle></CardHeader><CardContent><ScrollArea className="h-[250px]"><div className="prose prose-sm max-w-none dark:prose-invert">{inst.isSimulating ? <p className="whitespace-pre-wrap">{inst.voteTexts[inst.currentVoter]}</p> : <ReactMarkdown remarkPlugins={[remarkGfm]}>{inst.voteTexts[inst.currentVoter]}</ReactMarkdown>}</div></ScrollArea></CardContent></Card>)}
      </div>
    );
  };

  const renderStep2 = () => {
    const inst = activeInstance;
    const voteCounts = countVotesByCategory(inst.votes);
    const condenacao = voteCounts.desprovimento || 0;
    const absolvicao = voteCounts.provimento || 0;
    const parcial = voteCounts.parcial || 0;
    const isAbsolvido = absolvicao > condenacao;
    const resultado = isAbsolvido ? 'ABSOLVIDO' : 'CONDENADO';
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        {loadedFromHistory && (<div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-50 border border-blue-200 dark:bg-blue-950/20 dark:border-blue-900"><History className="h-4 w-4 text-blue-600" /><span className="text-sm text-blue-700 dark:text-blue-300">Carregado do histórico</span></div>)}
        <div className="text-center"><h2 className="text-3xl font-bold mb-2">Resultado - Conselho de Justica</h2><Badge className={`text-lg px-6 py-2 border-0 ${isAbsolvido ? VOTE_CATEGORIES[0].badgeClass : VOTE_CATEGORIES[1].badgeClass}`}>{resultado}</Badge></div>
        <Card><CardContent className="p-6"><div className="flex items-center justify-center gap-6 sm:gap-8 mb-4"><div className="text-center"><p className="text-4xl font-bold text-red-600">{condenacao}</p><p className="text-sm text-muted-foreground">Condenacao</p></div><div className="text-3xl text-muted-foreground font-bold">x</div>{parcial > 0 && (<><div className="text-center"><p className="text-4xl font-bold text-amber-600">{parcial}</p><p className="text-sm text-muted-foreground">Parcial</p></div><div className="text-3xl text-muted-foreground font-bold">x</div></>)}<div className="text-center"><p className="text-4xl font-bold text-green-600">{absolvicao}</p><p className="text-sm text-muted-foreground">Absolvicao</p></div></div><p className="text-center text-sm text-muted-foreground">{inst.votes.length} votos no Conselho de Justica</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Votos do Conselho</CardTitle></CardHeader><CardContent className="space-y-2">{inst.votes.map((v, i) => (<div key={i} className="flex items-center justify-between p-3 rounded-lg bg-muted/50"><div className="flex items-center gap-3"><div className={`h-8 w-8 rounded-full flex items-center justify-center ${categorizeVote(v.vote).iconClass}`}><User className="h-4 w-4" /></div><div><p className="text-sm font-medium">{v.minister}</p>{v.role && <p className="text-xs text-muted-foreground">{v.role}</p>}</div></div><Badge className={`border-0 ${categorizeVote(v.vote).badgeClass}`}>{v.vote}</Badge></div>))}</CardContent></Card>
        {inst.interrogatorioText && (<Card><CardHeader><CardTitle>Interrogatorio</CardTitle></CardHeader><CardContent><ScrollArea className="h-[300px]"><div className="prose prose-sm max-w-none dark:prose-invert"><ReactMarkdown remarkPlugins={[remarkGfm]}>{inst.interrogatorioText}</ReactMarkdown></div></ScrollArea></CardContent></Card>)}
        {inst.debatesText && (<Card><CardHeader><CardTitle>Debates (Acusacao e Defesa)</CardTitle></CardHeader><CardContent><ScrollArea className="h-[300px]"><div className="prose prose-sm max-w-none dark:prose-invert"><ReactMarkdown remarkPlugins={[remarkGfm]}>{inst.debatesText}</ReactMarkdown></div></ScrollArea></CardContent></Card>)}
        {inst.sentencaText && (<Card><CardHeader><CardTitle>Sentenca</CardTitle></CardHeader><CardContent><ScrollArea className="h-[400px]"><div className="prose prose-sm max-w-none dark:prose-invert"><ReactMarkdown remarkPlugins={[remarkGfm]}>{inst.sentencaText}</ReactMarkdown></div></ScrollArea></CardContent></Card>)}
        {Object.keys(inst.voteTexts).length > 0 && (<Card><CardHeader><CardTitle>Votos Completos</CardTitle></CardHeader><CardContent><details className="space-y-4"><summary className="cursor-pointer text-sm font-medium text-primary hover:underline">Expandir votos ({Object.keys(inst.voteTexts).length})</summary><div className="space-y-4 mt-4">{Object.entries(inst.voteTexts).map(([name, text]) => (<details key={name} className="border rounded-lg p-3"><summary className="cursor-pointer text-sm font-medium">{name}</summary><div className="mt-3 prose prose-sm max-w-none dark:prose-invert"><ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown></div></details>))}</div></details></CardContent></Card>)}
        {inst.strategicReport && (<Card className={`border-2 ${isAbsolvido ? VOTE_CATEGORIES[0].borderClass : VOTE_CATEGORIES[1].borderClass}`}><CardHeader><CardTitle className={`${isAbsolvido ? VOTE_CATEGORIES[0].scoreClass : VOTE_CATEGORIES[1].scoreClass}`}>Relatorio Estrategico</CardTitle><CardDescription>Analise e proximos passos</CardDescription></CardHeader><CardContent><ScrollArea className="h-[400px]"><div className="prose prose-sm max-w-none dark:prose-invert"><ReactMarkdown remarkPlugins={[remarkGfm]}>{inst.strategicReport}</ReactMarkdown></div></ScrollArea></CardContent></Card>)}
        {inst.simulationId && (<Card><CardHeader><div className="flex items-center gap-3"><MessageSquare className="h-5 w-5 text-primary" /><div><CardTitle className="text-base">Questionar o Julgamento</CardTitle></div></div></CardHeader><CardContent className="space-y-4"><div className="flex flex-wrap gap-2">{['Cabe apelacao ao STM?', 'Quais atenuantes podem reduzir a pena?', 'Como funciona o recurso militar?'].map((q, i) => (<Button key={i} variant="outline" size="sm" onClick={() => updateInstance(multiSim.activeSimIndex, { questionText: q })} className="text-xs">{q}</Button>))}</div><div className="flex gap-2"><Textarea value={inst.questionText} onChange={e => updateInstance(multiSim.activeSimIndex, { questionText: e.target.value })} placeholder="Sua pergunta..." className="flex-1 min-h-[80px]" /><Button onClick={handleQuestion} disabled={inst.isQuestioning || !inst.questionText.trim()} className="self-end">{inst.isQuestioning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}</Button></div>{inst.questionAnswer && (<div className="mt-4 p-4 rounded-lg bg-muted/50 border"><div className="prose prose-sm max-w-none dark:prose-invert"><ReactMarkdown remarkPlugins={[remarkGfm]}>{inst.questionAnswer}</ReactMarkdown></div></div>)}</CardContent></Card>)}
        <div className="flex flex-col sm:flex-row gap-3"><Button onClick={exportPdf} className="flex-1" disabled={inst.isExportingPdf}>{inst.isExportingPdf ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <FileDown className="h-4 w-4 mr-2" />}{inst.isExportingPdf ? 'Gerando PDF...' : 'Exportar PDF'}</Button><Button variant="outline" onClick={resetSimulation} className="flex-1"><RotateCcw className="h-4 w-4 mr-2" />Nova Simulação</Button><Button variant="outline" onClick={() => router.push('/dashboard/simulations')} className="flex-1"><ChevronLeft className="h-4 w-4 mr-2" />Voltar</Button></div>
      </div>
    );
  };

  return (
    <div className="min-h-screen flex flex-col -mx-3 sm:-mx-6 -mb-6">
      {renderStepper()}
      {currentStep > 0 && multiSim.simulationCount > 1 && (
        <SimulationTabBar tabs={multiSim.tabs} activeIndex={multiSim.activeSimIndex} onTabChange={multiSim.setActiveSimIndex} />
      )}
      <div className="flex-1 p-3 sm:p-6">{currentStep === 0 && renderStep0()}{currentStep === 1 && renderStep1()}{currentStep === 2 && renderStep2()}</div>
      {currentStep === 0 && (<div className="border-t p-3 sm:p-4 flex items-center justify-between max-w-3xl mx-auto w-full safe-area-bottom"><Button variant="outline" onClick={() => router.push('/dashboard/simulations')}><ChevronLeft className="h-4 w-4 mr-2" />Voltar</Button><Button onClick={nextStep} disabled={!canAdvance()}>Iniciar Julgamento<ChevronRight className="h-4 w-4 ml-2" /></Button></div>)}
    </div>
  );
}
