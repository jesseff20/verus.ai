'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useToast } from '@/hooks/use-toast';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Scale, ChevronLeft, ChevronRight, Loader2, CheckCircle2,
  FileDown, RotateCcw, Users, FileText, Landmark,
  AlertCircle, Send, MessageSquare, User,
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
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import SimulationCountSelector from '@/components/simulations/SimulationCountSelector';
import SimulationTabBar from '@/components/simulations/SimulationTabBar';
import { useMultiSimulation } from '@/hooks/use-multi-simulation';
import { categorizeVote, countVotesByCategory, getDominantCategory, VOTE_CATEGORIES } from '@/lib/vote-utils';

const STEPS = [
  { title: 'Configuração', icon: Scale },
  { title: 'Julgamento', icon: Landmark },
  { title: 'Resultado', icon: FileText },
];

const RECURSO_TYPES = [
  { value: 'Recurso Ordinário', label: 'Recurso Ordinário (RO)' },
  { value: 'Agravo de Petição', label: 'Agravo de Petição' },
  { value: 'Mandado de Segurança', label: 'Mandado de Segurança' },
  { value: 'Dissídio Coletivo', label: 'Dissídio Coletivo' },
  { value: 'Acao Rescisoria', label: 'Acao Rescisoria' },
];

const TRT_LIST = [
  'TRT-1 (RJ)', 'TRT-2 (SP)', 'TRT-3 (MG)', 'TRT-4 (RS)', 'TRT-5 (BA)',
  'TRT-6 (PE)', 'TRT-7 (CE)', 'TRT-8 (PA/AP)', 'TRT-9 (PR)', 'TRT-10 (DF/TO)',
  'TRT-11 (AM/RR)', 'TRT-12 (SC)', 'TRT-13 (PB)', 'TRT-14 (RO/AC)', 'TRT-15 (Campinas)',
  'TRT-16 (MA)', 'TRT-17 (ES)', 'TRT-18 (GO)', 'TRT-19 (AL)', 'TRT-20 (SE)',
  'TRT-21 (RN)', 'TRT-22 (PI)', 'TRT-23 (MT)', 'TRT-24 (MS)',
];

interface VoteResult {
  minister: string;
  vote: string;
  is_relator: boolean;
  role?: string;
}

export default function TRTSimulationPage() {
  const router = useRouter();
  const { toast } = useToast();
  const multiSim = useMultiSimulation();
  const [currentStep, setCurrentStep] = useState(0);

  // Config
  const [recursoType, setRecursoType] = useState('Recurso Ordinario');
  const [tribunal, setTribunal] = useState('TRT-2 (SP)');
  const [caseDescription, setCaseDescription] = useState('');

  // Simulation
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationId, setSimulationId] = useState<string | null>(null);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [analysisStage, setAnalysisStage] = useState('');

  // Streaming content
  const [relatorioText, setRelatorioText] = useState('');
  const [voteTexts, setVoteTexts] = useState<Record<string, string>>({});
  const [currentVoter, setCurrentVoter] = useState<string | null>(null);
  const [votes, setVotes] = useState<VoteResult[]>([]);
  const [proclamacaoText, setProclamacaoText] = useState('');
  const [ementaText, setEmentaText] = useState('');
  const [strategicReport, setStrategicReport] = useState('');

  // Batching
  const pendingRelatorioRef = useRef('');
  const pendingVoteRef = useRef('');
  const pendingProclamacaoRef = useRef('');
  const pendingEmentaRef = useRef('');
  const pendingReportRef = useRef('');
  const currentVoterRef = useRef<string | null>(null);
  const streamFlushTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => { return () => { if (streamFlushTimerRef.current) clearTimeout(streamFlushTimerRef.current); }; }, []);

  const scheduleStreamFlush = useCallback(() => {
    if (!streamFlushTimerRef.current) {
      streamFlushTimerRef.current = setTimeout(() => {
        streamFlushTimerRef.current = null;
        if (pendingRelatorioRef.current) { const t = pendingRelatorioRef.current; pendingRelatorioRef.current = ''; setRelatorioText((p) => p + t); }
        if (pendingVoteRef.current && currentVoterRef.current) { const t = pendingVoteRef.current; const v = currentVoterRef.current; pendingVoteRef.current = ''; setVoteTexts((p) => ({ ...p, [v]: (p[v] || '') + t })); }
        if (pendingProclamacaoRef.current) { const t = pendingProclamacaoRef.current; pendingProclamacaoRef.current = ''; setProclamacaoText((p) => p + t); }
        if (pendingEmentaRef.current) { const t = pendingEmentaRef.current; pendingEmentaRef.current = ''; setEmentaText((p) => p + t); }
        if (pendingReportRef.current) { const t = pendingReportRef.current; pendingReportRef.current = ''; setStrategicReport((p) => p + t); }
      }, 50);
    }
  }, []);

  const flushStreamBuffers = useCallback(() => {
    if (streamFlushTimerRef.current) { clearTimeout(streamFlushTimerRef.current); streamFlushTimerRef.current = null; }
    if (pendingRelatorioRef.current) { const t = pendingRelatorioRef.current; pendingRelatorioRef.current = ''; setRelatorioText((p) => p + t); }
    if (pendingVoteRef.current && currentVoterRef.current) { const t = pendingVoteRef.current; const v = currentVoterRef.current; pendingVoteRef.current = ''; setVoteTexts((p) => ({ ...p, [v]: (p[v] || '') + t })); }
    if (pendingProclamacaoRef.current) { const t = pendingProclamacaoRef.current; pendingProclamacaoRef.current = ''; setProclamacaoText((p) => p + t); }
    if (pendingEmentaRef.current) { const t = pendingEmentaRef.current; pendingEmentaRef.current = ''; setEmentaText((p) => p + t); }
    if (pendingReportRef.current) { const t = pendingReportRef.current; pendingReportRef.current = ''; setStrategicReport((p) => p + t); }
  }, []);

  const [questionText, setQuestionText] = useState('');
  const [questionAnswer, setQuestionAnswer] = useState('');
  const [isQuestioning, setIsQuestioning] = useState(false);
  const [isExportingPdf, setIsExportingPdf] = useState(false);

  const startSimulation = useCallback(async () => {
    setIsSimulating(true); setAnalysisProgress(0); setAnalysisStage('Iniciando simulação...');
    setRelatorioText(''); setVoteTexts({}); setVotes([]); setProclamacaoText('');
    setEmentaText(''); setStrategicReport(''); setCurrentVoter(null);

    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      const headers = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

      const createRes = await fetch('/api/v1/simulations/simulations/', {
        method: 'POST', headers,
        body: JSON.stringify({
          simulation_type: 'trt',
          title: `TRT - ${recursoType} - ${tribunal}`,
          config: { recurso_type: recursoType, tribunal, case_description: caseDescription },
        }),
      });
      if (!createRes.ok) throw new Error(`HTTP ${createRes.status}`);
      const simData = await createRes.json();
      const simId = simData.id;
      setSimulationId(simId);

      const response = await fetch(`/api/v1/simulations/simulations/${simId}/trt/start/`, {
        method: 'POST', headers, body: JSON.stringify({}),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) throw new Error('No reader');

      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const jsonStr = line.slice(6).trim();
          if (!jsonStr || jsonStr === '[DONE]') continue;
          try {
            const event = JSON.parse(jsonStr);
            const eventType = event.event || event.type;
            if (eventType === 'progress' && event.type === 'phase_change') {
              setAnalysisProgress(event.progress || 0);
              setAnalysisStage(event.label || '');
            } else if (eventType === 'phase') {
              setAnalysisStage(event.content || '');
            } else if (eventType === 'relatorio') {
              pendingRelatorioRef.current += (event.content || ''); scheduleStreamFlush();
            } else if (eventType === 'vote_text') {
              const minister = event.minister || '';
              if (minister) { currentVoterRef.current = minister; setCurrentVoter(minister); pendingVoteRef.current += (event.content || ''); scheduleStreamFlush(); }
            } else if (eventType === 'vote_result') {
              setVotes(prev => [...prev, { minister: event.minister, vote: event.vote, is_relator: event.is_relator, role: event.role }]);
            } else if (eventType === 'proclamacao') {
              pendingProclamacaoRef.current += (event.content || ''); scheduleStreamFlush();
            } else if (eventType === 'ementa') {
              pendingEmentaRef.current += (event.content || ''); scheduleStreamFlush();
            } else if (eventType === 'relatorio_estrategico') {
              pendingReportRef.current += (event.content || ''); scheduleStreamFlush();
            } else if (eventType === 'complete') {
              flushStreamBuffers(); setAnalysisProgress(100); setCurrentStep(2);
              toast({ title: 'Simulação concluida', description: 'Julgamento do TRT simulado com sucesso.' });
            } else if (eventType === 'error') {
              toast({ title: 'Erro', description: event.content || 'Erro desconhecido.', variant: 'destructive' });
              setIsSimulating(false);
            }
          } catch { /* ignore */ }
        }
      }
    } catch (error: any) {
      toast({ title: 'Erro', description: error.message || 'Falha.', variant: 'destructive' });
    } finally { setIsSimulating(false); }
  }, [recursoType, tribunal, caseDescription, toast, scheduleStreamFlush, flushStreamBuffers]);

  const handleQuestion = useCallback(async () => {
    if (!questionText.trim() || !simulationId) return;
    setIsQuestioning(true); setQuestionAnswer('');
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      const res = await fetch(`/api/v1/simulations/simulations/${simulationId}/question/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({ question: questionText }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setQuestionAnswer(data.answer || 'Sem resposta.');
    } catch (error: any) {
      toast({ title: 'Erro', description: error.message, variant: 'destructive' });
    } finally { setIsQuestioning(false); }
  }, [questionText, simulationId, toast]);

  const exportPdf = useCallback(async () => {
    if (!proclamacaoText && !strategicReport && !ementaText) {
      toast({ title: 'Nada para exportar', description: 'O resultado ainda não foi gerado.', variant: 'destructive' });
      return;
    }
    setIsExportingPdf(true);
    if (simulationId) {
      try {
        const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
        const res = await fetch(`/api/v1/simulations/simulations/${simulationId}/generate-pdf/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        });
        if (res.ok) {
          const blob = await res.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `simulação_trt_${new Date().toISOString().split('T')[0]}.pdf`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          setTimeout(() => URL.revokeObjectURL(url), 10000);
          toast({ title: 'PDF exportado', description: 'Arquivo baixado com sucesso.' });
          setIsExportingPdf(false);
          return;
        }
      } catch { /* fall through */ }
    }
    const htmlContent = `<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><title>Simulação TRT</title><style>body{font-family:'Times New Roman',serif;font-size:12pt;line-height:1.5;max-width:210mm;margin:0 auto;padding:2.5cm 2cm;text-align:justify;}h1{text-align:center;font-size:16pt;}h2{font-size:14pt;border-bottom:1px solid #ccc;padding-bottom:6pt;}.footer{margin-top:40px;border-top:1px solid #ccc;padding-top:12px;font-size:9pt;color:#999;text-align:center;}</style></head><body><h1>SIMULAÇÃO TRT</h1><p><strong>Data:</strong> ${new Date().toLocaleDateString('pt-BR')} | <strong>Tribunal:</strong> ${tribunal}</p>${ementaText ? `<h2>Ementa</h2><div>${ementaText.replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br/>')}</div>` : ''}${proclamacaoText ? `<h2>Proclamação</h2><div>${proclamacaoText.replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br/>')}</div>` : ''}${strategicReport ? `<h2>Relatório Estratégico</h2><div>${strategicReport.replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br/>')}</div>` : ''}<div class="footer"><p>Documento gerado pelo Verus.AI. Este documento não possui valor jurídico.</p></div></body></html>`;
    const blob = new Blob([htmlContent], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `simulação_trt_${new Date().toISOString().split('T')[0]}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast({ title: 'PDF exportado', description: 'Arquivo baixado com sucesso.' });
    setIsExportingPdf(false);
  }, [proclamacaoText, ementaText, strategicReport, simulationId, toast, tribunal]);

  const resetSimulation = useCallback(() => {
    multiSim.setSimulationCount(1);
    setCurrentStep(0); setRecursoType('Recurso Ordinario'); setTribunal('TRT-2 (SP)');
    setCaseDescription(''); setSimulationId(null); setAnalysisProgress(0); setAnalysisStage('');
    setRelatorioText(''); setVoteTexts({}); setVotes([]); setProclamacaoText('');
    setEmentaText(''); setStrategicReport(''); setCurrentVoter(null);
    setQuestionText(''); setQuestionAnswer('');
  }, []);

  const canAdvance = () => currentStep === 0 ? caseDescription.trim().length > 20 : true;

  const nextStep = () => {
    if (currentStep === 0) { setCurrentStep(1); (() => { multiSim.resetTabs(multiSim.simulationCount); for (let i = 0; i < multiSim.simulationCount; i++) { setTimeout(() => { multiSim.updateTabStatus(i, 'running'); startSimulation().then(() => multiSim.updateTabStatus(i, 'completed')).catch(() => multiSim.updateTabStatus(i, 'error')); }, i * 200); } })(); }
    else if (currentStep < STEPS.length - 1) setCurrentStep((s) => s + 1);
  };

  const renderStepper = () => (
    <div className="flex items-center justify-center gap-1 py-3 sm:py-4 px-2 sm:px-6 bg-card border-b overflow-x-auto">
      {STEPS.map((step, i) => {
        const Icon = step.icon;
        const isActive = i === currentStep;
        const isCompleted = i < currentStep;
        return (
          <div key={i} className="flex items-center shrink-0">
            <button onClick={() => i < currentStep && setCurrentStep(i)} disabled={i > currentStep}
              className={`flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-2 rounded-lg text-xs sm:text-sm font-medium transition-colors ${isActive ? 'bg-primary text-primary-foreground' : isCompleted ? 'bg-primary/10 text-primary cursor-pointer hover:bg-primary/20' : 'text-muted-foreground'}`}>
              {isCompleted ? <CheckCircle2 className="h-4 w-4" /> : <Icon className="h-4 w-4" />}
              <span className="hidden sm:inline">{step.title}</span>
            </button>
            {i < STEPS.length - 1 && <ChevronRight className="h-4 w-4 text-muted-foreground mx-0.5 sm:mx-1 shrink-0" />}
          </div>
        );
      })}
    </div>
  );

  const renderStep0 = () => (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <div className="flex items-center gap-3 mb-2">
          <Landmark className="h-8 w-8 text-orange-600" />
          <h2 className="text-2xl font-bold">TRT - Tribunal Regional do Trabalho</h2>
        </div>
        <p className="text-muted-foreground">Simule um acordao de 2a instancia trabalhista com 3 desembargadores.</p>
      </div>
      <Card className="border-orange-200 bg-orange-50/50 dark:border-orange-900 dark:bg-orange-950/20">
        <CardContent className="flex gap-4 py-4">
          <AlertCircle className="h-6 w-6 text-orange-500 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-orange-800 dark:text-orange-200">Recurso contra sentenca trabalhista</p>
            <p className="text-sm text-orange-700 dark:text-orange-300 mt-1">
              O TRT julga recursos ordinarios contra sentencas das Varas do Trabalho.
              3 desembargadores (Relator, Revisor, Vogal) votam individualmente.
            </p>
          </div>
        </CardContent>
      </Card>
      <div className="space-y-4">
        <div className="space-y-2">
          <Label>Tipo de Recurso *</Label>
          <Select value={recursoType} onValueChange={setRecursoType}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              {RECURSO_TYPES.map((r) => <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Tribunal *</Label>
          <Select value={tribunal} onValueChange={setTribunal}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              {TRT_LIST.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Descrição do Caso *</Label>
          <Textarea value={caseDescription} onChange={(e) => setCaseDescription(e.target.value)}
            placeholder="Descreva o caso trabalhista que será julgado pelo TRT, incluindo a sentenca de 1a instancia e os motivos do recurso..."
            className="min-h-[200px]" />
          <p className="text-xs text-muted-foreground text-right">{caseDescription.length} caracteres (minimo 20)</p>
        
        <div className="pt-4 border-t mt-4">
          <SimulationCountSelector value={multiSim.simulationCount} onChange={multiSim.setSimulationCount} />
        </div>
      </div>
      </div>
    </div>
  );

  const renderStep1 = () => {
    const voteCounts = countVotesByCategory(votes);
    const provimento = voteCounts.provimento || 0;
    const desprovimento = voteCounts.desprovimento || 0;
    const parcial = voteCounts.parcial || 0;
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <div><h2 className="text-2xl font-bold mb-1">Julgamento em Andamento</h2><p className="text-muted-foreground">{analysisStage || 'Preparando julgamento...'}</p></div>
        {isSimulating && currentVoter && (
          <div className="flex items-center gap-3 py-3 px-4 bg-muted/50 rounded-lg border-2 speaker-active">
            <div className="h-10 w-10 rounded-full bg-orange-500 flex items-center justify-center animate-pulse"><Scale className="h-5 w-5 text-white gavel-thinking" /></div>
            <div className="flex-1"><span className="text-sm font-medium">{currentVoter}</span><p className="text-xs text-muted-foreground">Proferindo voto...</p></div>
            <div className="flex gap-1 ml-auto"><div className="h-2 w-2 rounded-full bg-orange-500 thinking-dot" /><div className="h-2 w-2 rounded-full bg-orange-500 thinking-dot" /><div className="h-2 w-2 rounded-full bg-orange-500 thinking-dot" /></div>
          </div>
        )}
        <Card><CardContent className="p-6 space-y-4"><div className="flex items-center justify-between"><span className="text-sm font-medium">Progresso</span><span className="text-sm text-muted-foreground">{analysisProgress}%</span></div><Progress value={analysisProgress} /></CardContent></Card>
        {votes.length > 0 && (
          <Card>
            <CardHeader className="pb-3"><CardTitle className="text-base">Placar</CardTitle></CardHeader>
            <CardContent>
              <div className="flex items-center justify-center gap-6 sm:gap-8 mb-4">
                <div className="text-center"><p className="text-3xl font-bold text-green-600 score-update" key={`prov-${provimento}`}>{provimento}</p><p className="text-xs text-muted-foreground">Provimento</p></div>
                <div className="text-2xl text-muted-foreground font-bold">x</div>
                {parcial > 0 && (<><div className="text-center"><p className="text-3xl font-bold text-amber-600 score-update" key={`parc-${parcial}`}>{parcial}</p><p className="text-xs text-muted-foreground">Parcial</p></div><div className="text-2xl text-muted-foreground font-bold">x</div></>)}
                <div className="text-center"><p className="text-3xl font-bold text-red-600 score-update" key={`desp-${desprovimento}`}>{desprovimento}</p><p className="text-xs text-muted-foreground">Desprovimento</p></div>
              </div>
              <Separator className="mb-3" />
              <div className="space-y-2">
                {votes.map((v, i) => (
                  <div key={i} className="flex items-center justify-between py-1.5 px-3 rounded-lg bg-muted/50 vote-reveal" style={{ animationDelay: `${i * 0.1}s` }}>
                    <div className="flex items-center gap-2"><User className="h-4 w-4 text-muted-foreground" /><span className="text-sm font-medium">{v.minister}</span>{v.role && <Badge variant="outline" className="text-[10px]">{v.role}</Badge>}</div>
                    <Badge className={`text-xs border-0 vote-reveal ${categorizeVote(v.vote).badgeClass}`}>{v.vote}</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
        {currentVoter && voteTexts[currentVoter] && (
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm flex items-center gap-2"><Scale className="h-4 w-4" />Voto do {currentVoter}</CardTitle></CardHeader>
            <CardContent><ScrollArea className="h-[250px]"><div className="prose prose-sm max-w-none dark:prose-invert"><p className="whitespace-pre-wrap">{voteTexts[currentVoter]}</p></div></ScrollArea></CardContent>
          </Card>
        )}
      </div>
    );
  };

  const renderStep2 = () => {
    const voteCounts = countVotesByCategory(votes);
    const provimento = voteCounts.provimento || 0;
    const desprovimento = voteCounts.desprovimento || 0;
    const parcial = voteCounts.parcial || 0;
    const dominant = getDominantCategory(votes);
    const isVictory = dominant.id === 'provimento';
    const resultado = dominant.id === 'provimento' ? 'PROVIDO' : dominant.id === 'desprovimento' ? 'DESPROVIDO' : 'PARCIAL';
    const isUnanimous = votes.length > 0 && (dominant.count === votes.length);

    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="text-center">
          <h2 className="text-3xl font-bold mb-2">Resultado do Julgamento - TRT</h2>
          <Badge className={`text-lg px-6 py-2 border-0 ${VOTE_CATEGORIES.find(c => c.id === dominant.id)?.badgeClass || 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'}`}>{resultado}</Badge>
        </div>

        <Card><CardContent className="p-6">
          <div className="flex items-center justify-center gap-6 sm:gap-8 mb-4">
            <div className="text-center"><p className="text-4xl font-bold text-green-600">{provimento}</p><p className="text-sm text-muted-foreground">Provimento</p></div>
            <div className="text-3xl text-muted-foreground font-bold">x</div>
            {parcial > 0 && (<><div className="text-center"><p className="text-4xl font-bold text-amber-600">{parcial}</p><p className="text-sm text-muted-foreground">Parcial</p></div><div className="text-3xl text-muted-foreground font-bold">x</div></>)}
            <div className="text-center"><p className="text-4xl font-bold text-red-600">{desprovimento}</p><p className="text-sm text-muted-foreground">Desprovimento</p></div>
          </div>
          <p className="text-center text-sm text-muted-foreground">{isUnanimous ? 'Decisao unanime' : 'Decisao por maioria'} - {votes.length} votos</p>
        </CardContent></Card>

        <Card><CardHeader><CardTitle>Votos Individuais</CardTitle></CardHeader><CardContent className="space-y-2">
          {votes.map((v, i) => (
            <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
              <div className="flex items-center gap-3">
                <div className={`h-8 w-8 rounded-full flex items-center justify-center ${categorizeVote(v.vote).iconClass}`}><User className="h-4 w-4" /></div>
                <div><p className="text-sm font-medium">{v.minister}</p>{v.role && <p className="text-xs text-muted-foreground">{v.role}</p>}</div>
              </div>
              <Badge className={`border-0 ${categorizeVote(v.vote).badgeClass}`}>{v.vote}</Badge>
            </div>
          ))}
        </CardContent></Card>

        {ementaText && (<Card><CardHeader><CardTitle>Ementa do Acordao</CardTitle></CardHeader><CardContent><ScrollArea className="h-[250px]"><div className="prose prose-sm max-w-none dark:prose-invert"><ReactMarkdown remarkPlugins={[remarkGfm]}>{ementaText}</ReactMarkdown></div></ScrollArea></CardContent></Card>)}

        {proclamacaoText && (<Card><CardHeader><CardTitle>Proclamacao</CardTitle></CardHeader><CardContent><ScrollArea className="h-[250px]"><div className="prose prose-sm max-w-none dark:prose-invert"><ReactMarkdown remarkPlugins={[remarkGfm]}>{proclamacaoText}</ReactMarkdown></div></ScrollArea></CardContent></Card>)}

        {Object.keys(voteTexts).length > 0 && (
          <Card><CardHeader><CardTitle>Votos Completos</CardTitle></CardHeader><CardContent>
            <details><summary className="cursor-pointer text-sm font-medium text-primary hover:underline">Expandir votos ({Object.keys(voteTexts).length})</summary>
              <div className="space-y-4 mt-4">{Object.entries(voteTexts).map(([name, text]) => (<details key={name} className="border rounded-lg p-3"><summary className="cursor-pointer text-sm font-medium">{name}</summary><div className="mt-3 prose prose-sm max-w-none dark:prose-invert"><ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown></div></details>))}</div>
            </details>
          </CardContent></Card>
        )}

        {strategicReport && (
          <Card className={`border-2 ${VOTE_CATEGORIES.find(c => c.id === dominant.id)?.borderClass || 'border-green-200 bg-green-50/50 dark:border-green-900 dark:bg-green-950/20'}`}>
            <CardHeader><CardTitle className={`${VOTE_CATEGORIES.find(c => c.id === dominant.id)?.scoreClass || 'text-green-700 dark:text-green-400'}`}>Relatorio Estrategico</CardTitle></CardHeader>
            <CardContent><ScrollArea className="h-[400px]"><div className="prose prose-sm max-w-none dark:prose-invert"><ReactMarkdown remarkPlugins={[remarkGfm]}>{strategicReport}</ReactMarkdown></div></ScrollArea></CardContent>
          </Card>
        )}

        {simulationId && (
          <Card><CardHeader><div className="flex items-center gap-3"><MessageSquare className="h-5 w-5 text-primary" /><div><CardTitle className="text-base">Questionar o Julgamento</CardTitle></div></div></CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {['Cabe Recurso de Revista ao TST?', 'Quais requisitos do art. 896 CLT?', 'Cabe embargos de declaracao?'].map((q, i) => (
                  <Button key={i} variant="outline" size="sm" onClick={() => setQuestionText(q)} className="text-xs">{q}</Button>
                ))}
              </div>
              <div className="flex gap-2">
                <Textarea value={questionText} onChange={(e) => setQuestionText(e.target.value)} placeholder="Sua pergunta..." className="flex-1 min-h-[80px]" />
                <Button onClick={handleQuestion} disabled={isQuestioning || !questionText.trim()} className="self-end">
                  {isQuestioning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                </Button>
              </div>
              {questionAnswer && (<div className="mt-4 p-4 rounded-lg bg-muted/50 border"><div className="prose prose-sm max-w-none dark:prose-invert"><ReactMarkdown remarkPlugins={[remarkGfm]}>{questionAnswer}</ReactMarkdown></div></div>)}
            </CardContent>
          </Card>
        )}

        <div className="flex flex-col sm:flex-row gap-3">
          <Button onClick={exportPdf} className="flex-1" disabled={isExportingPdf}>{isExportingPdf ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <FileDown className="h-4 w-4 mr-2" />}{isExportingPdf ? 'Gerando PDF...' : 'Exportar PDF'}</Button>
          <Button variant="outline" onClick={resetSimulation} className="flex-1"><RotateCcw className="h-4 w-4 mr-2" />Nova Simulação</Button>
          <Button variant="outline" onClick={() => router.push('/dashboard/simulations')} className="flex-1"><ChevronLeft className="h-4 w-4 mr-2" />Voltar ao Histórico</Button>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen flex flex-col -mx-3 sm:-mx-6 -mb-6">
      {renderStepper()}
      {currentStep > 0 && multiSim.simulationCount > 1 && (
        <SimulationTabBar tabs={multiSim.tabs} activeIndex={multiSim.activeSimIndex} onTabChange={multiSim.setActiveSimIndex} />
      )}
      <div className="flex-1 p-3 sm:p-6">
        {currentStep === 0 && renderStep0()}
        {currentStep === 1 && renderStep1()}
        {currentStep === 2 && renderStep2()}
      </div>
      {currentStep === 0 && (
        <div className="border-t p-3 sm:p-4 flex items-center justify-between max-w-3xl mx-auto w-full safe-area-bottom">
          <Button variant="outline" onClick={() => router.push('/dashboard/simulations')}><ChevronLeft className="h-4 w-4 mr-2" />Voltar</Button>
          <Button onClick={nextStep} disabled={!canAdvance()}>Iniciar Julgamento<ChevronRight className="h-4 w-4 ml-2" /></Button>
        </div>
      )}
    </div>
  );
}
