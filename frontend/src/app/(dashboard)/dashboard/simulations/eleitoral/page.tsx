'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useToast } from '@/hooks/use-toast';
import { useMinisterProfiles } from '@/hooks/use-simulations';
import type { MinisterProfile } from '@/types';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Scale, ChevronLeft, ChevronRight, Loader2, CheckCircle2,
  FileDown, RotateCcw, Users, FileText, Vote,
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
import { categorizeVote, countVotesByCategory, getDominantCategory, VOTE_CATEGORIES } from '@/lib/vote-utils';

// --- Constants ---

const STEPS = [
  { title: 'Configuração', icon: Scale },
  { title: 'Membros', icon: Users },
  { title: 'Julgamento', icon: Vote },
  { title: 'Resultado', icon: FileText },
];

const COURT_TYPES = [
  { value: 'eleitoral', label: 'Juiz Eleitoral (1a Instancia)' },
  { value: 'tre', label: 'TRE - Tribunal Regional Eleitoral (7 membros)' },
  { value: 'tse', label: 'TSE - Tribunal Superior Eleitoral (7 ministros)' },
];

const CASE_TYPES = [
  { value: 'propaganda_irregular', label: 'Propaganda Eleitoral Irregular' },
  { value: 'registro_candidatura', label: 'Registro de Candidatura' },
  { value: 'prestacao_contas', label: 'Prestacao de Contas' },
  { value: 'cassacao', label: 'Cassacao de Mandato' },
  { value: 'abuso_poder', label: 'Abuso de Poder Economico/Politico' },
  { value: 'outros', label: 'Outros' },
];

const ACTION_TYPES_TRE = [
  { value: 'recurso_eleitoral', label: 'Recurso Eleitoral' },
  { value: 'aime', label: 'AIME - Acao de Impugnacao de Mandato Eletivo' },
  { value: 'aije', label: 'AIJE - Acao de Investigacao Judicial Eleitoral' },
  { value: 'representacao', label: 'Representacao Eleitoral' },
  { value: 'registro_candidatura', label: 'Registro de Candidatura (recurso)' },
];

const ACTION_TYPES_TSE = [
  { value: 'recurso_especial_eleitoral', label: 'Recurso Especial Eleitoral' },
  { value: 'recurso_ordinario', label: 'Recurso Ordinario' },
  { value: 'consulta', label: 'Consulta' },
  { value: 'representacao', label: 'Representacao' },
  { value: 'aime_originaria', label: 'AIME (Competencia Originaria)' },
];

const PHILOSOPHY_COLORS: Record<string, string> = {
  progressista: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  conservador: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  centrista: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
  pragmatico: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
};

const PHILOSOPHY_LABELS: Record<string, string> = {
  progressista: 'Progressista',
  conservador: 'Conservador',
  centrista: 'Centrista',
  pragmatico: 'Pragmatico',
};

// --- Types ---

interface VoteResult {
  minister: string;
  vote: string;
  is_relator: boolean;
}

// --- Component ---

export default function EleitoralSimulationPage() {
  const router = useRouter();
  const { toast } = useToast();
  const multiSim = useMultiSimulation();
  // Step navigation
  const [currentStep, setCurrentStep] = useState(0);

  // Step 1 config
  const [courtType, setCourtType] = useState<string>('eleitoral');
  const [caseType, setCaseType] = useState('');
  const [actionType, setActionType] = useState('');
  const [caseDescription, setCaseDescription] = useState('');

  const isColegiado = courtType === 'tre' || courtType === 'tse';

  // Step 2 members (only for TRE/TSE)
  const memberCourtType = courtType === 'tse' ? 'TSE' : courtType === 'tre' ? 'TRE' : undefined;
  const { data: allMembers } = useMinisterProfiles(memberCourtType as any);

  // Step 3 simulation
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationId, setSimulationId] = useState<string | null>(null);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [analysisStage, setAnalysisStage] = useState('');
  const [currentPhaseDescription, setCurrentPhaseDescription] = useState('');

  // Streaming content
  const [sentencaText, setSentencaText] = useState('');
  const [relatorioText, setRelatorioText] = useState('');
  const [voteTexts, setVoteTexts] = useState<Record<string, string>>({});
  const [currentVoter, setCurrentVoter] = useState<string | null>(null);
  const [votes, setVotes] = useState<VoteResult[]>([]);
  const [proclamacaoText, setProclamacaoText] = useState('');
  const [strategicReport, setStrategicReport] = useState('');

  // Batching refs
  const pendingSentencaRef = useRef('');
  const pendingRelatorioRef = useRef('');
  const pendingVoteRef = useRef('');
  const pendingProclamacaoRef = useRef('');
  const pendingReportRef = useRef('');
  const currentVoterRef = useRef<string | null>(null);
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
        if (pendingSentencaRef.current) {
          const t = pendingSentencaRef.current;
          pendingSentencaRef.current = '';
          setSentencaText((p) => p + t);
        }
        if (pendingRelatorioRef.current) {
          const t = pendingRelatorioRef.current;
          pendingRelatorioRef.current = '';
          setRelatorioText((p) => p + t);
        }
        if (pendingVoteRef.current && currentVoterRef.current) {
          const t = pendingVoteRef.current;
          const voter = currentVoterRef.current;
          pendingVoteRef.current = '';
          setVoteTexts((p) => ({ ...p, [voter]: (p[voter] || '') + t }));
        }
        if (pendingProclamacaoRef.current) {
          const t = pendingProclamacaoRef.current;
          pendingProclamacaoRef.current = '';
          setProclamacaoText((p) => p + t);
        }
        if (pendingReportRef.current) {
          const t = pendingReportRef.current;
          pendingReportRef.current = '';
          setStrategicReport((p) => p + t);
        }
      }, 50);
    }
  }, []);

  const flushStreamBuffers = useCallback(() => {
    if (streamFlushTimerRef.current) {
      clearTimeout(streamFlushTimerRef.current);
      streamFlushTimerRef.current = null;
    }
    if (pendingSentencaRef.current) {
      const t = pendingSentencaRef.current;
      pendingSentencaRef.current = '';
      setSentencaText((p) => p + t);
    }
    if (pendingRelatorioRef.current) {
      const t = pendingRelatorioRef.current;
      pendingRelatorioRef.current = '';
      setRelatorioText((p) => p + t);
    }
    if (pendingVoteRef.current && currentVoterRef.current) {
      const t = pendingVoteRef.current;
      const voter = currentVoterRef.current;
      pendingVoteRef.current = '';
      setVoteTexts((p) => ({ ...p, [voter]: (p[voter] || '') + t }));
    }
    if (pendingProclamacaoRef.current) {
      const t = pendingProclamacaoRef.current;
      pendingProclamacaoRef.current = '';
      setProclamacaoText((p) => p + t);
    }
    if (pendingReportRef.current) {
      const t = pendingReportRef.current;
      pendingReportRef.current = '';
      setStrategicReport((p) => p + t);
    }
  }, []);

  // Question
  const [questionText, setQuestionText] = useState('');
  const [questionAnswer, setQuestionAnswer] = useState('');
  const [isQuestioning, setIsQuestioning] = useState(false);
  const [isExportingPdf, setIsExportingPdf] = useState(false);

  // --- Start simulation ---

  const startSimulation = useCallback(async () => {
    setIsSimulating(true);
    setAnalysisProgress(0);
    setAnalysisStage('Iniciando simulação...');
    setSentencaText('');
    setRelatorioText('');
    setVoteTexts({});
    setVotes([]);
    setProclamacaoText('');
    setStrategicReport('');
    setCurrentVoter(null);

    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      const headers = {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      };

      const courtLabel = COURT_TYPES.find(c => c.value === courtType)?.label || courtType;

      // 1. Create simulation
      const createRes = await fetch('/api/v1/simulations/simulations/', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          simulation_type: courtType,
          title: `Simulação ${courtLabel} - ${CASE_TYPES.find(c => c.value === caseType)?.label || caseType}`,
          config: {
            case_type: caseType,
            action_type: actionType,
            case_description: caseDescription,
          },
        }),
      });
      if (!createRes.ok) throw new Error(`Erro ao criar simulação: HTTP ${createRes.status}`);
      const simData = await createRes.json();
      const simId = simData.id;
      setSimulationId(simId);

      // 2. Start SSE
      const sseEndpoint = courtType === 'tse'
        ? `tse/start/`
        : courtType === 'tre'
        ? `tre/start/`
        : `eleitoral/start/`;

      const response = await fetch(`/api/v1/simulations/simulations/${simId}/${sseEndpoint}`, {
        method: 'POST',
        headers,
        body: JSON.stringify({}),
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
              setCurrentPhaseDescription(event.description || '');
            } else if (eventType === 'ministers') {
              // Members list received
            } else if (eventType === 'phase') {
              setAnalysisStage(event.content || '');
            } else if (eventType === 'sentenca') {
              pendingSentencaRef.current += (event.content || '');
              scheduleStreamFlush();
            } else if (eventType === 'relatorio') {
              pendingRelatorioRef.current += (event.content || '');
              scheduleStreamFlush();
            } else if (eventType === 'vote_text') {
              const minister = event.minister || '';
              if (minister) {
                currentVoterRef.current = minister;
                setCurrentVoter(minister);
                pendingVoteRef.current += (event.content || '');
                scheduleStreamFlush();
              }
            } else if (eventType === 'vote_result') {
              const newVote: VoteResult = {
                minister: event.minister,
                vote: event.vote,
                is_relator: event.is_relator,
              };
              setVotes(prev => [...prev, newVote]);
            } else if (eventType === 'proclamacao') {
              pendingProclamacaoRef.current += (event.content || '');
              scheduleStreamFlush();
            } else if (eventType === 'relatorio_estrategico') {
              pendingReportRef.current += (event.content || '');
              scheduleStreamFlush();
            } else if (eventType === 'complete') {
              flushStreamBuffers();
              setAnalysisProgress(100);
              setCurrentStep(3);
              toast({
                title: 'Simulação concluida',
                description: `A simulação da Justica Eleitoral foi concluida com sucesso.`,
              });
            } else if (eventType === 'error') {
              toast({
                title: 'Erro na simulação',
                description: event.content || 'Erro desconhecido.',
                variant: 'destructive',
              });
              setIsSimulating(false);
            }
          } catch {
            // ignore parse errors
          }
        }
      }
    } catch (error: any) {
      toast({
        title: 'Erro',
        description: error.message || 'Falha ao conectar com o servidor.',
        variant: 'destructive',
      });
    } finally {
      setIsSimulating(false);
    }
  }, [courtType, caseType, actionType, caseDescription, toast, scheduleStreamFlush, flushStreamBuffers]);

  // --- Question handler ---

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
      setQuestionAnswer(data.answer || 'Sem resposta disponivel.');
    } catch (error: any) {
      toast({
        title: 'Erro',
        description: error.message || 'Falha ao enviar a pergunta.',
        variant: 'destructive',
      });
    } finally {
      setIsQuestioning(false);
    }
  }, [questionText, simulationId, toast]);

  // --- PDF Export ---

  const exportPdf = useCallback(async () => {
    if (!sentencaText && !proclamacaoText && !strategicReport) {
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
          a.download = `simulação_eleitoral_${new Date().toISOString().split('T')[0]}.pdf`;
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
    const htmlContent = `<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><title>Simulação Eleitoral</title><style>body{font-family:'Times New Roman',serif;font-size:12pt;line-height:1.5;max-width:210mm;margin:0 auto;padding:2.5cm 2cm;text-align:justify;}h1{text-align:center;font-size:16pt;}h2{font-size:14pt;border-bottom:1px solid #ccc;padding-bottom:6pt;}.footer{margin-top:40px;border-top:1px solid #ccc;padding-top:12px;font-size:9pt;color:#999;text-align:center;}</style></head><body><h1>SIMULAÇÃO JUSTIÇA ELEITORAL</h1><p><strong>Data:</strong> ${new Date().toLocaleDateString('pt-BR')}</p>${sentencaText ? `<h2>Sentença</h2><div>${sentencaText.replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br/>')}</div>` : ''}${proclamacaoText ? `<h2>Proclamação</h2><div>${proclamacaoText.replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br/>')}</div>` : ''}${strategicReport ? `<h2>Relatório Estratégico</h2><div>${strategicReport.replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br/>')}</div>` : ''}<div class="footer"><p>Documento gerado pelo Verus.AI. Este documento não possui valor jurídico.</p></div></body></html>`;
    const blob = new Blob([htmlContent], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `simulação_eleitoral_${new Date().toISOString().split('T')[0]}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast({ title: 'PDF exportado', description: 'Arquivo baixado com sucesso.' });
    setIsExportingPdf(false);
  }, [sentencaText, proclamacaoText, strategicReport, simulationId, toast]);

  // --- Reset ---

  const resetSimulation = useCallback(() => {
    multiSim.setSimulationCount(1);
    setCurrentStep(0);
    setCourtType('eleitoral');
    setCaseType('');
    setActionType('');
    setCaseDescription('');
    setSimulationId(null);
    setAnalysisProgress(0);
    setAnalysisStage('');
    setSentencaText('');
    setRelatorioText('');
    setVoteTexts({});
    setVotes([]);
    setProclamacaoText('');
    setStrategicReport('');
    setCurrentVoter(null);
    setQuestionText('');
    setQuestionAnswer('');
  }, []);

  // --- Navigation ---

  const canAdvance = () => {
    if (currentStep === 0) return caseType !== '' && caseDescription.trim().length > 20;
    return true;
  };

  const nextStep = () => {
    if (currentStep < STEPS.length - 1) {
      if (isColegiado && currentStep === 1) {
        setCurrentStep(2);
        (() => { multiSim.resetTabs(multiSim.simulationCount); for (let i = 0; i < multiSim.simulationCount; i++) { setTimeout(() => { multiSim.updateTabStatus(i, 'running'); startSimulation().then(() => multiSim.updateTabStatus(i, 'completed')).catch(() => multiSim.updateTabStatus(i, 'error')); }, i * 200); } })();
      } else if (!isColegiado && currentStep === 0) {
        // Skip members step for simple judge
        setCurrentStep(2);
        (() => { multiSim.resetTabs(multiSim.simulationCount); for (let i = 0; i < multiSim.simulationCount; i++) { setTimeout(() => { multiSim.updateTabStatus(i, 'running'); startSimulation().then(() => multiSim.updateTabStatus(i, 'completed')).catch(() => multiSim.updateTabStatus(i, 'error')); }, i * 200); } })();
      } else {
        setCurrentStep((s) => s + 1);
      }
    }
  };
  const prevStep = () => {
    if (currentStep > 0) setCurrentStep((s) => s - 1);
  };

  // --- Stepper ---

  const stepsToShow = isColegiado ? STEPS : [STEPS[0], STEPS[2], STEPS[3]];

  const renderStepper = () => (
    <div className="flex items-center justify-center gap-1 py-3 sm:py-4 px-2 sm:px-6 bg-card border-b overflow-x-auto">
      {stepsToShow.map((step, i) => {
        const Icon = step.icon;
        const stepIndex = isColegiado ? i : (i === 0 ? 0 : i + 1);
        const isActive = stepIndex === currentStep;
        const isCompleted = stepIndex < currentStep;
        return (
          <div key={i} className="flex items-center shrink-0">
            <button
              onClick={() => stepIndex < currentStep && setCurrentStep(stepIndex)}
              disabled={stepIndex > currentStep}
              className={`flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-2 rounded-lg text-xs sm:text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : isCompleted
                  ? 'bg-primary/10 text-primary cursor-pointer hover:bg-primary/20'
                  : 'text-muted-foreground'
              }`}
            >
              {isCompleted ? (
                <CheckCircle2 className="h-4 w-4" />
              ) : (
                <Icon className="h-4 w-4" />
              )}
              <span className="hidden sm:inline">{step.title}</span>
            </button>
            {i < stepsToShow.length - 1 && (
              <ChevronRight className="h-4 w-4 text-muted-foreground mx-0.5 sm:mx-1 shrink-0" />
            )}
          </div>
        );
      })}
    </div>
  );

  // --- Step 0: Configuration ---

  const renderStep0 = () => (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <div className="flex items-center gap-3 mb-2">
          <Vote className="h-8 w-8 text-purple-600" />
          <h2 className="text-2xl font-bold">Justica Eleitoral</h2>
        </div>
        <p className="text-muted-foreground">Configure a simulação de julgamento na Justica Eleitoral.</p>
      </div>

      <Card className="border-purple-200 bg-purple-50/50 dark:border-purple-900 dark:bg-purple-950/20">
        <CardContent className="flex gap-4 py-4">
          <AlertCircle className="h-6 w-6 text-purple-500 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-purple-800 dark:text-purple-200">
              Estrutura da Justica Eleitoral
            </p>
            <p className="text-sm text-purple-700 dark:text-purple-300 mt-1">
              <strong>Juiz Eleitoral:</strong> sentenca de 1a instancia. <br />
              <strong>TRE:</strong> 7 membros (2 desembargadores TJ, 2 juizes de direito, 1 juiz federal, 2 advogados). <br />
              <strong>TSE:</strong> 7 ministros (3 do STF, 2 do STJ, 2 advogados nomeados pelo Presidente).
            </p>
          </div>
        </CardContent>
      </Card>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label>Instancia / Tribunal *</Label>
          <Select value={courtType} onValueChange={(v) => { setCourtType(v); setActionType(''); }}>
            <SelectTrigger>
              <SelectValue placeholder="Selecione a instancia" />
            </SelectTrigger>
            <SelectContent>
              {COURT_TYPES.map((ct) => (
                <SelectItem key={ct.value} value={ct.value}>{ct.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Tipo de Acao Eleitoral *</Label>
          <Select value={caseType} onValueChange={setCaseType}>
            <SelectTrigger>
              <SelectValue placeholder="Selecione o tipo de acao" />
            </SelectTrigger>
            <SelectContent>
              {CASE_TYPES.map((ct) => (
                <SelectItem key={ct.value} value={ct.value}>{ct.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {isColegiado && (
          <div className="space-y-2">
            <Label>Tipo de Recurso *</Label>
            <Select value={actionType} onValueChange={setActionType}>
              <SelectTrigger>
                <SelectValue placeholder="Selecione o tipo de recurso" />
              </SelectTrigger>
              <SelectContent>
                {(courtType === 'tse' ? ACTION_TYPES_TSE : ACTION_TYPES_TRE).map((at) => (
                  <SelectItem key={at.value} value={at.value}>{at.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        <div className="space-y-2">
          <Label>Descrição do Caso *</Label>
          <p className="text-xs text-muted-foreground">
            Descreva o caso eleitoral. Inclua fatos, partes, legislacao violada e pedidos.
          </p>
          <Textarea
            value={caseDescription}
            onChange={(e) => setCaseDescription(e.target.value)}
            placeholder="Ex: Representacao por propaganda eleitoral irregular na qual o candidato X utilizou recursos publicos para..."
            className="min-h-[200px]"
          />
          <p className="text-xs text-muted-foreground text-right">
            {caseDescription.length} caracteres (minimo 20)
          </p>
        
        <div className="pt-4 border-t mt-4">
          <SimulationCountSelector value={multiSim.simulationCount} onChange={multiSim.setSimulationCount} />
        </div>
      </div>
      </div>
    </div>
  );

  // --- Step 1: Members (TRE/TSE only) ---

  const renderStep1 = () => (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-1">Membros do {courtType === 'tse' ? 'TSE' : 'TRE'}</h2>
        <p className="text-muted-foreground">
          {courtType === 'tse' ? '7 ministros: 3 STF + 2 STJ + 2 advogados' : '7 membros: 2 desembargadores + 2 juizes + 1 juiz federal + 2 advogados'}
          {' '}- {(allMembers || []).length > 0 ? `${(allMembers || []).length} membros cadastrados` : 'Perfis genericos serao utilizados'}.
        </p>
      </div>

      {(allMembers || []).length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {(allMembers || []).map((m) => (
            <Card key={m.id} className="hover:border-primary/30 transition-colors">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-purple-500/10">
                    <User className="h-5 w-5 text-purple-600" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <CardTitle className="text-sm truncate">{m.name}</CardTitle>
                    <CardDescription className="text-xs">{(m.profile_data as any)?.court_origin || (m.profile_data as any)?.role_origin || m.turma}</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3 pt-0">
                <Badge className={`text-xs border-0 ${PHILOSOPHY_COLORS[m.judicial_philosophy] || ''}`}>
                  {PHILOSOPHY_LABELS[m.judicial_philosophy] || m.judicial_philosophy}
                </Badge>
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-1">Especialidades</p>
                  <div className="flex flex-wrap gap-1">
                    {(m.specialty_areas || []).slice(0, 3).map((s, i) => (
                      <Badge key={i} variant="outline" className="text-[10px] px-1.5 py-0">{s}</Badge>
                    ))}
                  </div>
                </div>
                {m.appointed_by && (
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-1">Origem</p>
                    <p className="text-xs">{m.appointed_by}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="border-purple-200 bg-purple-50/50 dark:border-purple-900 dark:bg-purple-950/20">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Users className="h-12 w-12 text-purple-500/40 mb-4" />
            <p className="text-purple-800 dark:text-purple-200 font-medium">Perfis genericos serao utilizados</p>
            <p className="text-sm text-purple-700 dark:text-purple-300 mt-1 text-center">
              7 membros com perfis variados serao criados automaticamente.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );

  // --- Step 2: Simulation in progress ---

  const renderStep2 = () => {
    const categoryCounts = countVotesByCategory(votes);
    const provimento = categoryCounts.provimento || 0;
    const desprovimento = categoryCounts.desprovimento || 0;
    const parcial = categoryCounts.parcial || 0;

    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h2 className="text-2xl font-bold mb-1">
            {isColegiado ? 'Julgamento em Andamento' : 'Sentenca em Andamento'}
          </h2>
          <p className="text-muted-foreground">{analysisStage || 'Preparando...'}</p>
        </div>

        {isSimulating && isColegiado && currentVoter && (
          <div className="flex items-center gap-3 py-3 px-4 bg-muted/50 rounded-lg border-2 speaker-active">
            <div className="h-10 w-10 rounded-full bg-purple-500 flex items-center justify-center animate-pulse">
              <Scale className="h-5 w-5 text-white gavel-thinking" />
            </div>
            <div className="flex-1">
              <span className="text-sm font-medium">{currentVoter}</span>
              <p className="text-xs text-muted-foreground">{currentPhaseDescription || 'Proferindo voto...'}</p>
            </div>
            <div className="flex gap-1 ml-auto">
              <div className="h-2 w-2 rounded-full bg-purple-500 thinking-dot" />
              <div className="h-2 w-2 rounded-full bg-purple-500 thinking-dot" />
              <div className="h-2 w-2 rounded-full bg-purple-500 thinking-dot" />
            </div>
          </div>
        )}

        <Card>
          <CardContent className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Progresso</span>
              <span className="text-sm text-muted-foreground">{analysisProgress}%</span>
            </div>
            <Progress value={analysisProgress} />
          </CardContent>
        </Card>

        {/* Sentenca text for juiz eleitoral */}
        {!isColegiado && sentencaText && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Scale className="h-4 w-4" />
                Sentenca Eleitoral {isSimulating && '(em andamento...)'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[350px]">
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  {isSimulating ? (
                    <p className="whitespace-pre-wrap">{sentencaText}</p>
                  ) : (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{sentencaText}</ReactMarkdown>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        )}

        {/* Votes for TRE/TSE */}
        {isColegiado && votes.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Placar de Votacao</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-center gap-8 mb-4">
                <div className="text-center">
                  <p className="text-3xl font-bold text-green-600 score-update" key={`prov-${provimento}`}>{provimento}</p>
                  <p className="text-xs text-muted-foreground">Provimento</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-amber-600 score-update" key={`parc-${parcial}`}>{parcial}</p>
                  <p className="text-xs text-muted-foreground">Parcial</p>
                </div>
                <div className="text-2xl text-muted-foreground font-bold">x</div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-red-600 score-update" key={`desp-${desprovimento}`}>{desprovimento}</p>
                  <p className="text-xs text-muted-foreground">Desprovimento</p>
                </div>
              </div>
              <Separator className="mb-3" />
              <div className="space-y-2">
                {votes.map((v, i) => (
                  <div key={i} className="flex items-center justify-between py-1.5 px-3 rounded-lg bg-muted/50 vote-reveal" style={{ animationDelay: `${i * 0.1}s` }}>
                    <div className="flex items-center gap-2">
                      <User className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">{v.minister}</span>
                      {v.is_relator && (
                        <Badge variant="outline" className="text-[10px]">Relator</Badge>
                      )}
                    </div>
                    <Badge
                      className={`text-xs border-0 vote-reveal ${categorizeVote(v.vote).badgeClass}`}
                    >
                      {v.vote}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {isColegiado && currentVoter && voteTexts[currentVoter] && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Scale className="h-4 w-4" />
                Voto de {currentVoter} {isSimulating && '(em andamento...)'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[250px]">
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  {isSimulating ? (
                    <p className="whitespace-pre-wrap">{voteTexts[currentVoter]}</p>
                  ) : (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {voteTexts[currentVoter]}
                    </ReactMarkdown>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  // --- Step 3: Results ---

  const renderStep3 = () => {
    const categoryCounts = countVotesByCategory(votes);
    const provimento = categoryCounts.provimento || 0;
    const desprovimento = categoryCounts.desprovimento || 0;
    const parcial = categoryCounts.parcial || 0;
    const dominant = isColegiado ? getDominantCategory(votes) : null;
    const isVictory = dominant?.id === 'provimento';
    const resultado = isColegiado
      ? (dominant?.id === 'provimento' ? 'PROVIDO' : dominant?.id === 'parcial' ? 'PARCIALMENTE PROVIDO' : 'DESPROVIDO')
      : '';
    const isUnanimous = votes.length > 0 && Math.max(provimento, desprovimento, parcial) === votes.length;

    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="text-center">
          <h2 className="text-3xl font-bold mb-2">
            {isColegiado ? 'Resultado do Julgamento' : 'Sentenca Eleitoral'}
          </h2>
          {isColegiado && (
            <Badge
              className={`text-lg px-6 py-2 border-0 ${
                isVictory
                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                  : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
              }`}
            >
              {resultado}
            </Badge>
          )}
        </div>

        {/* Scoreboard for TRE/TSE */}
        {isColegiado && (
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-center gap-8 mb-4">
                <div className="text-center">
                  <p className="text-4xl font-bold text-green-600">{provimento}</p>
                  <p className="text-sm text-muted-foreground">Provimento</p>
                </div>
                <div className="text-center">
                  <p className="text-4xl font-bold text-amber-600">{parcial}</p>
                  <p className="text-sm text-muted-foreground">Parcial</p>
                </div>
                <div className="text-3xl text-muted-foreground font-bold">x</div>
                <div className="text-center">
                  <p className="text-4xl font-bold text-red-600">{desprovimento}</p>
                  <p className="text-sm text-muted-foreground">Desprovimento</p>
                </div>
              </div>
              <p className="text-center text-sm text-muted-foreground">
                {isUnanimous ? 'Decisao unanime' : 'Decisao por maioria'} - {votes.length} votos
              </p>
            </CardContent>
          </Card>
        )}

        {/* Votes breakdown */}
        {isColegiado && votes.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Votos Individuais</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {votes.map((v, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors">
                  <div className="flex items-center gap-3">
                    <div className={`h-8 w-8 rounded-full flex items-center justify-center ${categorizeVote(v.vote).iconClass}`}>
                      <User className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-sm font-medium">{v.minister}</p>
                      {v.is_relator && <p className="text-xs text-muted-foreground">Relator</p>}
                    </div>
                  </div>
                  <Badge
                    className={`border-0 ${categorizeVote(v.vote).badgeClass}`}
                  >
                    {v.vote}
                  </Badge>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Sentenca for juiz eleitoral */}
        {!isColegiado && sentencaText && (
          <Card>
            <CardHeader>
              <CardTitle>Sentenca Eleitoral</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{sentencaText}</ReactMarkdown>
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        )}

        {/* Proclamacao */}
        {proclamacaoText && (
          <Card>
            <CardHeader>
              <CardTitle>Proclamacao do Resultado</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[300px]">
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{proclamacaoText}</ReactMarkdown>
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        )}

        {/* Vote texts */}
        {Object.keys(voteTexts).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Votos Completos</CardTitle>
              <CardDescription>Clique em um membro para ler o voto integral</CardDescription>
            </CardHeader>
            <CardContent>
              <details className="space-y-4">
                <summary className="cursor-pointer text-sm font-medium text-primary hover:underline">
                  Expandir votos ({Object.keys(voteTexts).length} votos)
                </summary>
                <div className="space-y-4 mt-4">
                  {Object.entries(voteTexts).map(([name, text]) => (
                    <details key={name} className="border rounded-lg p-3">
                      <summary className="cursor-pointer text-sm font-medium">{name}</summary>
                      <div className="mt-3 prose prose-sm max-w-none dark:prose-invert">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
                      </div>
                    </details>
                  ))}
                </div>
              </details>
            </CardContent>
          </Card>
        )}

        {/* Strategic Report */}
        {strategicReport && (
          <Card className={`border-2 ${
            !isColegiado
              ? 'border-green-200 bg-green-50/50 dark:border-green-900 dark:bg-green-950/20'
              : dominant && VOTE_CATEGORIES.find(c => c.id === dominant.id)?.borderClass
              || 'border-green-200 bg-green-50/50 dark:border-green-900 dark:bg-green-950/20'
          }`}>
            <CardHeader>
              <CardTitle className={
                !isColegiado
                  ? 'text-green-700 dark:text-green-400'
                  : dominant?.id === 'provimento'
                  ? 'text-green-700 dark:text-green-400'
                  : dominant?.id === 'parcial'
                  ? 'text-amber-700 dark:text-amber-400'
                  : 'text-red-700 dark:text-red-400'
              }>
                Relatorio Estrategico
              </CardTitle>
              <CardDescription>Analise do resultado e proximos passos</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{strategicReport}</ReactMarkdown>
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        )}

        {/* Question */}
        {simulationId && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <MessageSquare className="h-5 w-5 text-primary" />
                <div>
                  <CardTitle className="text-base">Questionar o Julgamento</CardTitle>
                  <CardDescription>Pergunte sobre o resultado, legislacao eleitoral ou recursos</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {[
                  'Cabe recurso ao TSE/STF?',
                  'Qual o prazo para recurso eleitoral?',
                  'Ha risco de inelegibilidade?',
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
                  placeholder="Sua pergunta sobre o julgamento eleitoral..."
                  className="flex-1 min-h-[80px]"
                />
                <Button onClick={handleQuestion} disabled={isQuestioning || !questionText.trim()} className="self-end">
                  {isQuestioning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                </Button>
              </div>

              {questionAnswer && (
                <div className="mt-4 p-4 rounded-lg bg-muted/50 border">
                  <div className="flex items-center gap-2 mb-3">
                    <Scale className="h-4 w-4 text-primary" />
                    <span className="text-sm font-semibold">Resposta</span>
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
          <Button variant="outline" onClick={resetSimulation} className="flex-1">
            <RotateCcw className="h-4 w-4 mr-2" />
            Nova Simulação
          </Button>
          <Button variant="outline" onClick={() => router.push('/dashboard/simulations')} className="flex-1">
            <ChevronLeft className="h-4 w-4 mr-2" />
            Voltar ao Histórico
          </Button>
        </div>
      </div>
    );
  };

  // --- Main ---

  const showNavFooter = isColegiado ? currentStep < 2 : currentStep === 0;

  return (
    <div className="min-h-screen flex flex-col -mx-3 sm:-mx-6 -mb-6">
      {renderStepper()}
      {currentStep > 0 && multiSim.simulationCount > 1 && (
        <SimulationTabBar tabs={multiSim.tabs} activeIndex={multiSim.activeSimIndex} onTabChange={multiSim.setActiveSimIndex} />
      )}

      <div className="flex-1 p-3 sm:p-6">
        {currentStep === 0 && renderStep0()}
        {currentStep === 1 && isColegiado && renderStep1()}
        {currentStep === 2 && renderStep2()}
        {currentStep === 3 && renderStep3()}
      </div>

      {showNavFooter && (
        <div className="border-t p-3 sm:p-4 flex items-center justify-between max-w-3xl mx-auto w-full safe-area-bottom">
          <Button
            variant="outline"
            onClick={currentStep === 0 ? () => router.push('/dashboard/simulations') : prevStep}
          >
            <ChevronLeft className="h-4 w-4 mr-2" />
            {currentStep === 0 ? 'Voltar' : 'Anterior'}
          </Button>
          <Button onClick={nextStep} disabled={!canAdvance()}>
            {(isColegiado && currentStep === 1) || (!isColegiado && currentStep === 0) ? 'Iniciar Julgamento' : 'Próximo'}
            <ChevronRight className="h-4 w-4 ml-2" />
          </Button>
        </div>
      )}
    </div>
  );
}
