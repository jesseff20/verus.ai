'use client';

import { useState, useCallback, useRef, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useToast } from '@/hooks/use-toast';
import { useSimulationDetail } from '@/hooks/use-simulations';
import {
  Gavel, ChevronLeft, ChevronRight, Loader2,
  CheckCircle2, FileDown, RotateCcw, FileText,
  Search, AlertCircle, Shield, Send, MessageSquare,
  CheckSquare, Square, History, Scale,
  BarChart3, BookOpen, Handshake, AlertTriangle,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Progress } from '@/components/ui/progress';
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

// ─── Constants ───

const JECRIM_CRIME_TYPES = [
  'Lesão corporal leve (art. 129, caput, CP)',
  'Ameaça (art. 147, CP)',
  'Injúria (art. 140, CP)',
  'Calúnia (art. 138, CP)',
  'Difamação (art. 139, CP)',
  'Dano simples (art. 163, CP)',
  'Perturbação do sossego (art. 42, LCP)',
  'Vias de fato (art. 21, LCP)',
  'Desacato (art. 331, CP)',
  'Desobediência (art. 330, CP)',
  'Exercício arbitrário das próprias razões (art. 345, CP)',
  'Outros (pena máxima < 2 anos)',
];

const STEPS = [
  { title: 'Dados do Crime', icon: FileText },
  { title: 'Simulação', icon: Search },
  { title: 'Resultado', icon: Gavel },
];

const JECRIM_PHASES = [
  { key: 'preliminar', label: 'Audiência Preliminar', icon: Handshake, description: 'Realizando audiência preliminar obrigatória...' },
  { key: 'transacao', label: 'Transação Penal (art. 76)', icon: Scale, description: 'MP elaborando proposta de transação penal...' },
  { key: 'analise_transacao', label: 'Análise da Transação', icon: Search, description: 'Analisando aceitação ou rejeição da proposta...' },
  { key: 'suspensao', label: 'Suspensão Condicional (art. 89)', icon: AlertTriangle, description: 'Avaliando suspensão condicional do processo...' },
  { key: 'instrucao', label: 'Instrução Criminal', icon: BookOpen, description: 'Realizando instrução criminal simplificada...' },
  { key: 'sentenca', label: 'Sentença Criminal', icon: Gavel, description: 'Redigindo sentença criminal simplificada...' },
  { key: 'relatorio', label: 'Relatório Estratégico', icon: BarChart3, description: 'Gerando análise e recomendações...' },
];

// ─── Component ───

export default function JECRIMSimulationPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>}>
      <JECRIMSimulationPageInner />
    </Suspense>
  );
}

function JECRIMSimulationPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const historyId = searchParams.get('id');
  const { toast } = useToast();
  const multiSim = useMultiSimulation();
  const [loadedFromHistory, setLoadedFromHistory] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);

  // Step 1 - Config
  const [crimeType, setCrimeType] = useState('');
  const [facts, setFacts] = useState('');

  // Step 2 - Simulation
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [analysisStage, setAnalysisStage] = useState('');
  const [completedPhases, setCompletedPhases] = useState<string[]>([]);
  const [currentPhase, setCurrentPhase] = useState<string | null>(null);
  const [currentPhaseDescription, setCurrentPhaseDescription] = useState('');
  const [sentenceContent, setSentenceContent] = useState('');

  // Step 3 - Results
  const [dispositivo, setDispositivo] = useState<string | null>(null);
  const [strategicReport, setStrategicReport] = useState('');
  const [isVictory, setIsVictory] = useState(false);
  const [simulationId, setSimulationId] = useState<string | null>(null);
  const [transacaoAceita, setTransacaoAceita] = useState(false);

  // Question
  const [questionText, setQuestionText] = useState('');
  const [questionAnswer, setQuestionAnswer] = useState('');
  const [isQuestioning, setIsQuestioning] = useState(false);

  // PDF export
  const [isExportingPdf, setIsExportingPdf] = useState(false);

  // Checklist
  const [checkedItems, setCheckedItems] = useState<Record<number, boolean>>({});

  // Streaming batching
  const pendingSentenceRef = useRef('');
  const pendingReportRef = useRef('');
  const streamFlushTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (streamFlushTimerRef.current) clearTimeout(streamFlushTimerRef.current);
    };
  }, []);

  const scheduleStreamFlush = useCallback(() => {
    if (!streamFlushTimerRef.current) {
      streamFlushTimerRef.current = setTimeout(() => {
        streamFlushTimerRef.current = null;
        if (pendingSentenceRef.current) {
          const text = pendingSentenceRef.current;
          pendingSentenceRef.current = '';
          setSentenceContent((prev) => prev + text);
        }
        if (pendingReportRef.current) {
          const text = pendingReportRef.current;
          pendingReportRef.current = '';
          setStrategicReport((prev) => prev + text);
        }
      }, 50);
    }
  }, []);

  const flushStreamBuffers = useCallback(() => {
    if (streamFlushTimerRef.current) {
      clearTimeout(streamFlushTimerRef.current);
      streamFlushTimerRef.current = null;
    }
    if (pendingSentenceRef.current) {
      const text = pendingSentenceRef.current;
      pendingSentenceRef.current = '';
      setSentenceContent((prev) => prev + text);
    }
    if (pendingReportRef.current) {
      const text = pendingReportRef.current;
      pendingReportRef.current = '';
      setStrategicReport((prev) => prev + text);
    }
  }, []);

  // ── Load from history ──
  const { data: historySimulation } = useSimulationDetail(historyId);
  const historyLoadedRef = useRef(false);

  useEffect(() => {
    if (!historySimulation || historyLoadedRef.current) return;
    if (historySimulation.status !== 'completed') return;
    historyLoadedRef.current = true;

    const result = historySimulation.result || {};
    const config = historySimulation.config || {};

    setSimulationId(historySimulation.id);
    setSentenceContent(result.sentence || '');
    setStrategicReport(result.strategic_report || '');
    setDispositivo(result.dispositivo || null);
    setTransacaoAceita(result.transacao_aceita || false);
    setIsVictory(['absolvicao', 'transacao_aceita', 'suspensao_aceita'].includes(result.dispositivo));
    setCrimeType(config.crime_type || result.crime_type || '');
    setFacts(config.facts || result.facts || '');

    setCurrentStep(2);
    setLoadedFromHistory(true);

    toast({
      title: 'Simulação carregada do histórico',
      description: `"${historySimulation.title}" foi carregada com sucesso.`,
    });
  }, [historySimulation, toast]);

  // ── Start analysis ──

  const startAnalysis = useCallback(async () => {
    setIsAnalyzing(true);
    setAnalysisProgress(0);
    setAnalysisStage('Iniciando simulação JECRIM...');
    setSentenceContent('');
    setStrategicReport('');
    setCompletedPhases([]);
    setCurrentPhase(null);

    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      const headers = {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      };

      const config = {
        crime_type: crimeType,
        facts,
        case_description: facts,
      };

      // Create simulation
      const createRes = await fetch('/api/v1/simulations/simulations/', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          simulation_type: 'jecrim',
          title: `JECRIM - ${crimeType || 'Simulação'}`,
          config,
        }),
      });
      if (!createRes.ok) throw new Error(`Erro ao criar simulação: HTTP ${createRes.status}`);
      const simData = await createRes.json();
      const simId = simData.id;
      setSimulationId(simId);

      // Start SSE
      const response = await fetch(`/api/v1/simulations/simulations/${simId}/jecrim/start/`, {
        method: 'POST',
        headers,
        body: JSON.stringify(config),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) throw new Error('No reader');

      let buffer = '';
      let lastPhase: string | null = null;
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
              setCurrentPhaseDescription(event.description || '');
              if (lastPhase && lastPhase !== event.phase) {
                const prev = lastPhase;
                setCompletedPhases((arr) => arr.includes(prev) ? arr : [...arr, prev]);
              }
              lastPhase = event.phase;
              setCurrentPhase(event.phase);
            } else if (eventType === 'analise_transacao' && event.aceita !== undefined) {
              setTransacaoAceita(event.aceita);
              pendingSentenceRef.current += (event.content || '');
              scheduleStreamFlush();
            } else if (eventType === 'suspensao' && event.aceita !== undefined) {
              pendingSentenceRef.current += (event.content || '');
              scheduleStreamFlush();
            } else if (eventType === 'sentence' || eventType === 'sentence_chunk') {
              pendingSentenceRef.current += (event.content || '');
              scheduleStreamFlush();
            } else if (eventType === 'relatorio') {
              pendingReportRef.current += (event.content || '');
              scheduleStreamFlush();
              if (event.dispositivo) {
                setDispositivo(event.dispositivo);
                setIsVictory(!!event.is_victory);
              }
            } else if (eventType === 'complete') {
              flushStreamBuffers();
              if (lastPhase) {
                const prev = lastPhase;
                setCompletedPhases((arr) => arr.includes(prev) ? arr : [...arr, prev]);
              }
              setCurrentPhase(null);
              setAnalysisProgress(100);
              setCurrentStep(2);
              toast({
                title: 'Simulação salva no histórico',
                description: 'Você pode revisitar esta simulação a qualquer momento.',
              });
            } else if (eventType === 'error') {
              toast({
                title: 'Erro na simulação',
                description: event.content || 'Erro desconhecido.',
                variant: 'destructive',
              });
              setIsAnalyzing(false);
            } else if (['preliminar', 'transacao', 'instrucao', 'triagem'].includes(eventType)) {
              pendingSentenceRef.current += (event.content || '');
              scheduleStreamFlush();
            }
          } catch {
            // ignore parse errors
          }
        }
      }
    } catch (error: any) {
      toast({
        title: 'Erro na análise',
        description: error.message || 'Falha ao conectar com o servidor.',
        variant: 'destructive',
      });
    } finally {
      setIsAnalyzing(false);
    }
  }, [crimeType, facts, toast, scheduleStreamFlush, flushStreamBuffers]);

  // ── Handlers ──

  const resetSimulation = useCallback(() => {
    multiSim.setSimulationCount(1);
    setCurrentStep(0);
    setCrimeType('');
    setFacts('');
    setSentenceContent('');
    setStrategicReport('');
    setDispositivo(null);
    setIsVictory(false);
    setTransacaoAceita(false);
    setSimulationId(null);
    setCheckedItems({});
    setQuestionText('');
    setQuestionAnswer('');
    setCompletedPhases([]);
    setCurrentPhase(null);
    setAnalysisProgress(0);
  }, []);

  const handleQuestion = useCallback(async () => {
    if (!questionText.trim() || !simulationId) return;
    setIsQuestioning(true);
    setQuestionAnswer('');

    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      const res = await fetch(`/api/v1/simulations/simulations/${simulationId}/question/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ question: questionText }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setQuestionAnswer(data.answer || 'Sem resposta disponível.');
    } catch (error: any) {
      toast({
        title: 'Erro ao questionar',
        description: error.message || 'Falha ao enviar a pergunta.',
        variant: 'destructive',
      });
    } finally {
      setIsQuestioning(false);
    }
  }, [questionText, simulationId, toast]);

  const exportPdf = useCallback(async () => {
    if (!sentenceContent && !strategicReport) {
      toast({ title: 'Nada para exportar', description: 'A decisão ainda não foi gerada.', variant: 'destructive' });
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
          a.download = `simulação_jecrim_${new Date().toISOString().split('T')[0]}.pdf`;
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
    const htmlContent = `<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><title>Simulação JECRIM</title><style>body{font-family:'Times New Roman',serif;font-size:12pt;line-height:1.5;max-width:210mm;margin:0 auto;padding:2.5cm 2cm;text-align:justify;}h1{text-align:center;font-size:16pt;}h2{font-size:14pt;border-bottom:1px solid #ccc;padding-bottom:6pt;}.footer{margin-top:40px;border-top:1px solid #ccc;padding-top:12px;font-size:9pt;color:#999;text-align:center;}</style></head><body><h1>SIMULAÇÃO JECRIM</h1><p><strong>Data:</strong> ${new Date().toLocaleDateString('pt-BR')} | <strong>Crime:</strong> ${crimeType || 'N/A'}</p>${sentenceContent ? `<h2>Decisão</h2><div>${sentenceContent.replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br/>')}</div>` : ''}${strategicReport ? `<h2>Relatório Estratégico</h2><div>${strategicReport.replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br/>')}</div>` : ''}<div class="footer"><p>Documento gerado pelo Verus.AI - Simulação JECRIM. Este documento não possui valor jurídico.</p></div></body></html>`;
    const blob = new Blob([htmlContent], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `simulação_jecrim_${new Date().toISOString().split('T')[0]}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast({ title: 'PDF exportado', description: 'Arquivo baixado com sucesso.' });
    setIsExportingPdf(false);
  }, [sentenceContent, strategicReport, simulationId, toast, crimeType]);

  const toggleCheckItem = useCallback((index: number) => {
    setCheckedItems((prev) => ({ ...prev, [index]: !prev[index] }));
  }, []);

  // ── Navigation ──

  const canAdvance = () => {
    if (currentStep === 0) return crimeType !== '' && facts.trim() !== '';
    return true;
  };

  const nextStep = () => {
    if (currentStep === 0) {
      setCurrentStep(1);
      multiSim.resetTabs(multiSim.simulationCount);
      for (let i = 0; i < multiSim.simulationCount; i++) {
        setTimeout(() => {
          multiSim.updateTabStatus(i, 'running');
          startAnalysis().then(() => multiSim.updateTabStatus(i, 'completed')).catch(() => multiSim.updateTabStatus(i, 'error'));
        }, i * 200);
      }
    }
  };

  // ── Render Stepper ──

  const renderStepper = () => (
    <div className="flex items-center justify-center gap-1 py-3 sm:py-4 px-2 sm:px-6 bg-card border-b overflow-x-auto">
      {STEPS.map((step, i) => {
        const Icon = step.icon;
        const isActive = i === currentStep;
        const isCompleted = i < currentStep;
        return (
          <div key={i} className="flex items-center shrink-0">
            <button
              onClick={() => i < currentStep && setCurrentStep(i)}
              disabled={i > currentStep}
              className={`flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-2 rounded-lg text-xs sm:text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : isCompleted
                  ? 'bg-primary/10 text-primary cursor-pointer hover:bg-primary/20'
                  : 'text-muted-foreground'
              }`}
            >
              {isCompleted ? <CheckCircle2 className="h-4 w-4" /> : <Icon className="h-4 w-4" />}
              <span className="hidden sm:inline">{step.title}</span>
            </button>
            {i < STEPS.length - 1 && (
              <ChevronRight className="h-4 w-4 text-muted-foreground mx-0.5 sm:mx-1 shrink-0" />
            )}
          </div>
        );
      })}
    </div>
  );

  // ── Render Step 0: Config ──

  const renderStep0 = () => (
    <div className="max-w-3xl mx-auto space-y-4 sm:space-y-6">
      <div>
        <h2 className="text-xl sm:text-2xl font-bold mb-1">Dados do Crime - JECRIM</h2>
        <p className="text-muted-foreground">Configure os dados para o Juizado Especial Criminal (Lei 9.099/95).</p>
      </div>

      <div className="flex gap-3 p-4 rounded-lg border border-amber-200 bg-amber-50/50 dark:border-amber-900 dark:bg-amber-950/20">
        <AlertCircle className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" />
        <div className="text-sm">
          <p className="font-medium text-amber-800 dark:text-amber-200">
            Competência do JECRIM: infrações de menor potencial ofensivo
          </p>
          <p className="text-amber-700 dark:text-amber-300 mt-1">
            Contravenções penais e crimes com pena máxima não superior a 2 anos, cumulada ou não com multa
            (art. 61, Lei 9.099/95). A simulação inclui transação penal (art. 76) e suspensão condicional (art. 89).
          </p>
        </div>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label>Tipo de Crime / Infração *</Label>
          <Select value={crimeType} onValueChange={setCrimeType}>
            <SelectTrigger>
              <SelectValue placeholder="Selecione o tipo de crime" />
            </SelectTrigger>
            <SelectContent>
              {JECRIM_CRIME_TYPES.map((ct) => (
                <SelectItem key={ct} value={ct}>{ct}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Descrição dos Fatos *</Label>
          <Textarea
            value={facts}
            onChange={(e) => setFacts(e.target.value)}
            placeholder="Descreva os fatos: o que aconteceu, quando, onde, quem são as partes envolvidas, circunstâncias relevantes, provas disponíveis..."
            className="min-h-[200px]"
          />
        </div>

        <div className="pt-4 border-t mt-4">
          <SimulationCountSelector value={multiSim.simulationCount} onChange={multiSim.setSimulationCount} />
        </div>
      </div>
    </div>
  );

  // ── Render Step 1: Simulation ──

  const renderStep1 = () => (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-1">Simulação em Andamento</h2>
        <p className="text-muted-foreground">{analysisStage || 'Preparando simulação...'}</p>
      </div>

      {isAnalyzing && analysisStage && (
        <div className="flex items-center gap-3 py-3 px-4 bg-muted/50 rounded-lg border-2 speaker-active">
          <div className="h-10 w-10 rounded-full bg-rose-500 flex items-center justify-center">
            <Gavel className="h-5 w-5 text-white gavel-thinking" />
          </div>
          <div className="flex-1">
            <span className="text-sm font-medium">Juizado Especial Criminal</span>
            <p className="text-xs text-muted-foreground">{currentPhaseDescription || analysisStage}</p>
          </div>
          <div className="flex gap-1 ml-auto">
            <div className="h-2 w-2 rounded-full bg-rose-500 thinking-dot" />
            <div className="h-2 w-2 rounded-full bg-rose-500 thinking-dot" />
            <div className="h-2 w-2 rounded-full bg-rose-500 thinking-dot" />
          </div>
        </div>
      )}

      <Card>
        <CardContent className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Progresso Geral</span>
            <span className="text-sm text-muted-foreground">
              Fase {Math.min(completedPhases.length + 1, JECRIM_PHASES.length)} de {JECRIM_PHASES.length}
            </span>
          </div>
          <Progress value={analysisProgress} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Etapas do Procedimento</CardTitle>
        </CardHeader>
        <CardContent className="space-y-1">
          {JECRIM_PHASES.map((phase) => {
            const PhaseIcon = phase.icon;
            const isCompleted = completedPhases.includes(phase.key);
            const isCurrent = currentPhase === phase.key;

            return (
              <div
                key={phase.key}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                  isCurrent
                    ? 'bg-primary/5 border border-primary/20'
                    : isCompleted
                    ? 'bg-green-50 dark:bg-green-950/10'
                    : 'opacity-50'
                }`}
              >
                <div
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                    isCompleted ? 'bg-green-100 dark:bg-green-900' : isCurrent ? 'bg-primary/10' : 'bg-muted'
                  }`}
                >
                  {isCompleted ? (
                    <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400" />
                  ) : isCurrent ? (
                    <Loader2 className="h-4 w-4 text-primary animate-spin" />
                  ) : (
                    <PhaseIcon className="h-4 w-4 text-muted-foreground" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-medium ${isCompleted ? 'text-green-700 dark:text-green-400' : isCurrent ? 'text-foreground' : 'text-muted-foreground'}`}>
                    {phase.label}
                  </p>
                  {(isCurrent || isCompleted) && (
                    <p className="text-xs text-muted-foreground truncate">{phase.description}</p>
                  )}
                </div>
                {isCurrent && (
                  <div className="flex gap-0.5 shrink-0">
                    <div className="h-1.5 w-1.5 rounded-full bg-primary thinking-dot" />
                    <div className="h-1.5 w-1.5 rounded-full bg-primary thinking-dot" />
                    <div className="h-1.5 w-1.5 rounded-full bg-primary thinking-dot" />
                  </div>
                )}
                {isCompleted && (
                  <Badge variant="outline" className="text-xs text-green-600 border-green-200 dark:text-green-400 dark:border-green-800 shrink-0">
                    Concluída
                  </Badge>
                )}
              </div>
            );
          })}
        </CardContent>
      </Card>

      {sentenceContent && (
        <Card className="mt-4">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <FileText className="h-4 w-4" />
              {isAnalyzing ? 'Procedimento (em andamento...)' : 'Procedimento'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px]">
              <div className="prose prose-sm max-w-none dark:prose-invert">
                {isAnalyzing ? (
                  <p className="whitespace-pre-wrap">{sentenceContent}</p>
                ) : (
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{sentenceContent}</ReactMarkdown>
                )}
              </div>
            </ScrollArea>
            {isAnalyzing && (
              <div className="flex items-center gap-1 mt-2 text-xs text-muted-foreground">
                <Loader2 className="h-3 w-3 animate-spin" />
                Processando...
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );

  // ── Render Step 2: Results ──

  const renderStep2 = () => {
    const victoryColor = isVictory ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400';
    const victoryBg = isVictory ? 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-900' : 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900';

    const checklistItems: string[] = [];
    if (strategicReport) {
      const lines = strategicReport.split('\n');
      for (const line of lines) {
        const match = line.match(/\[[ x]\]\s*(.+)/i);
        if (match) checklistItems.push(match[1].trim());
      }
    }

    const dispositivoLabel = dispositivo === 'condenacao'
      ? 'CONDENADO'
      : dispositivo === 'absolvicao'
      ? 'ABSOLVIDO'
      : dispositivo === 'transacao_aceita'
      ? 'TRANSAÇÃO PENAL ACEITA'
      : dispositivo === 'suspensao_aceita'
      ? 'SUSPENSÃO CONDICIONAL ACEITA'
      : '';

    return (
      <div className="max-w-4xl mx-auto space-y-4 sm:space-y-6">
        {loadedFromHistory && (
          <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-50 border border-blue-200 dark:bg-blue-950/20 dark:border-blue-900">
            <History className="h-4 w-4 text-blue-600 dark:text-blue-400" />
            <span className="text-sm text-blue-700 dark:text-blue-300">Carregado do histórico</span>
          </div>
        )}

        <div className="text-center">
          <h2 className="text-2xl sm:text-3xl font-bold mb-2">Resultado - JECRIM</h2>
          {dispositivo && (
            <Badge
              variant={isVictory ? 'default' : 'destructive'}
              className="text-base sm:text-lg px-4 py-1.5"
            >
              {dispositivoLabel}
            </Badge>
          )}
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
          <Card>
            <CardContent className="text-center p-4">
              <p className="text-lg font-bold text-primary">{crimeType}</p>
              <p className="text-xs text-muted-foreground">Tipo de Crime</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="text-center p-4">
              <p className="text-3xl font-bold">{transacaoAceita ? 'Sim' : 'Não'}</p>
              <p className="text-xs text-muted-foreground">Transação Aceita</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="text-center p-4">
              <p className="text-3xl font-bold">{dispositivoLabel || 'N/A'}</p>
              <p className="text-xs text-muted-foreground">Resultado</p>
            </CardContent>
          </Card>
        </div>

        {/* Sentence / Decision text */}
        <Card>
          <CardHeader>
            <CardTitle>
              {dispositivo === 'transacao_aceita'
                ? 'Termo de Transação Penal'
                : dispositivo === 'suspensao_aceita'
                ? 'Termo de Suspensão Condicional'
                : 'Sentença Criminal'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[500px]">
              <div className="prose prose-sm max-w-none dark:prose-invert">
                {sentenceContent ? (
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{sentenceContent}</ReactMarkdown>
                ) : (
                  'Conteúdo não disponível.'
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Strategic Report */}
        {strategicReport && (
          <Card className={`border-2 ${victoryBg}`}>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${isVictory ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
                  <Shield className={`h-6 w-6 ${victoryColor}`} />
                </div>
                <div className="flex-1">
                  <CardTitle className={victoryColor}>Relatório Estratégico</CardTitle>
                  <CardDescription>Análise completa com recomendações práticas</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px]">
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{strategicReport}</ReactMarkdown>
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        )}

        {/* Checklist */}
        {checklistItems.length > 0 && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <CheckSquare className="h-5 w-5 text-primary" />
                <CardTitle className="text-base">Checklist de Providências</CardTitle>
                <Badge variant="outline" className="ml-auto">
                  {Object.values(checkedItems).filter(Boolean).length}/{checklistItems.length}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {checklistItems.map((item, idx) => {
                  const cleanItem = item.replace(/\*\*(.*?)\*\*/g, '$1');
                  const isChecked = !!checkedItems[idx];
                  return (
                    <div key={idx} className={`rounded-lg transition-colors ${isChecked ? 'bg-green-50 dark:bg-green-950/20' : 'bg-muted/50 hover:bg-muted'}`}>
                      <button onClick={() => toggleCheckItem(idx)} className="flex items-center gap-3 w-full text-left px-3 py-3 sm:py-2 min-h-[44px]">
                        {isChecked ? <CheckSquare className="h-4 w-4 text-green-600 shrink-0" /> : <Square className="h-4 w-4 text-muted-foreground shrink-0" />}
                        <span className={`text-sm flex-1 ${isChecked ? 'line-through text-muted-foreground' : ''}`}>{cleanItem}</span>
                      </button>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Question */}
        {(simulationId || sentenceContent) && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <MessageSquare className="h-5 w-5 text-primary" />
                <div>
                  <CardTitle className="text-base">Questionar o Resultado</CardTitle>
                  <CardDescription>Pergunte sobre a decisão e receba análises</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {[
                  'Quais são as chances de recurso?',
                  'A transação penal gera antecedentes?',
                  'Cabe recurso à Turma Recursal?',
                ].map((q, i) => (
                  <Button key={i} variant="outline" size="sm" onClick={() => setQuestionText(q)} className="text-xs">
                    {q}
                  </Button>
                ))}
              </div>
              <div className="flex gap-2">
                <Textarea
                  value={questionText}
                  onChange={(e) => setQuestionText(e.target.value)}
                  placeholder="Ex: Quais são as chances de recurso? A transação penal gera antecedentes?"
                  className="flex-1 min-h-[80px]"
                />
                <Button onClick={handleQuestion} disabled={isQuestioning || !questionText.trim() || !simulationId} className="self-end">
                  {isQuestioning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                </Button>
              </div>
              {questionAnswer && (
                <div className="mt-4 p-4 rounded-lg bg-muted/50 border">
                  <div className="flex items-center gap-2 mb-3">
                    <Gavel className="h-4 w-4 text-primary" />
                    <span className="text-sm font-semibold">Resposta do Consultor</span>
                  </div>
                  <div className="prose prose-sm max-w-none dark:prose-invert">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{questionAnswer}</ReactMarkdown>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3">
          <Button onClick={exportPdf} className="flex-1" disabled={isExportingPdf}>
            {isExportingPdf ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <FileDown className="h-4 w-4 mr-2" />}
            {isExportingPdf ? 'Gerando PDF...' : 'Exportar PDF'}
          </Button>
          <Button variant="outline" onClick={resetSimulation}>
            <RotateCcw className="h-4 w-4 mr-2" />
            Nova Simulação
          </Button>
        </div>
      </div>
    );
  };

  // ── Main Render ──

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
          <Button variant="outline" onClick={() => router.push('/dashboard/simulations')}>
            <ChevronLeft className="h-4 w-4 mr-2" />
            Voltar
          </Button>
          <Button onClick={nextStep} disabled={!canAdvance()}>
            Iniciar Simulação
            <ChevronRight className="h-4 w-4 ml-2" />
          </Button>
        </div>
      )}
    </div>
  );
}
