'use client';

import { useState, useCallback, useRef, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useToast } from '@/hooks/use-toast';
import { useMinisterProfiles, useSimulationDetail } from '@/hooks/use-simulations';
import type { MinisterProfile } from '@/types';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Scale, ChevronLeft, ChevronRight, Loader2, CheckCircle2,
  FileDown, RotateCcw, Users, FileText, Landmark,
  AlertCircle, Send, MessageSquare, User, History,
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
import { cn } from '@/lib/utils';
import { Input } from '@/components/ui/input';
import { X } from 'lucide-react';
import { categorizeVote, countVotesByCategory, getDominantCategory, getSortedCategories, VOTE_CATEGORIES } from '@/lib/vote-utils';
// Multi-simulation already implemented natively in this page

// ─── Constants ───

const STEPS = [
  { title: 'Configuração', icon: Scale },
  { title: 'Ministros', icon: Users },
  { title: 'Julgamento', icon: Landmark },
  { title: 'Resultado', icon: FileText },
];

const ACTION_TYPES = [
  { value: 'RE', label: 'Recurso Extraordinário (RE)' },
  { value: 'ADI', label: 'Acao Direta de Inconstitucionalidade (ADI)' },
  { value: 'ADPF', label: 'Arguicao de Descumprimento de Preceito Fundamental (ADPF)' },
  { value: 'ADC', label: 'Acao Declaratoria de Constitucionalidade (ADC)' },
  { value: 'MI', label: 'Mandado de Injuncao (MI)' },
  { value: 'HC', label: 'Habeas Corpus (HC)' },
  { value: 'MS', label: 'Mandado de Seguranca (MS)' },
];

const COMPOSITIONS = [
  { value: 'plenario', label: 'Plenário (11 ministros)' },
  { value: '1a_turma', label: '1a Turma (5 ministros)' },
  { value: '2a_turma', label: '2a Turma (5 ministros)' },
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

// ─── Types ───

interface VoteResult {
  minister: string;
  vote: string;
  is_relator: boolean;
}

// ─── Component ───

export default function STFSimulationPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>}>
      <STFSimulationPageInner />
    </Suspense>
  );
}

function STFSimulationPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const historyId = searchParams.get('id');
  const { toast } = useToast();
  // Track whether we loaded from history
  const [loadedFromHistory, setLoadedFromHistory] = useState(false);

  // Step navigation
  const [currentStep, setCurrentStep] = useState(0);

  // Multi-simulation
  const [simulationCount, setSimulationCount] = useState(1);
  const [simInstances, setSimInstances] = useState<{ id: number; simulationId: string; status: 'running' | 'completed' | 'failed'; relatorioText: string; voteTexts: Record<string, string>; votes: VoteResult[]; proclamacaoText: string; strategicReport: string }[]>([]);
  const [activeSimTab, setActiveSimTab] = useState(0);
  const simAbortControllers = useRef<Record<number, AbortController>>({});

  // Step 1 config
  const [actionType, setActionType] = useState('');
  const [composition, setComposition] = useState('plenario');
  const [caseDescription, setCaseDescription] = useState('');

  // Step 2 ministers
  const { data: allMinisters } = useMinisterProfiles('STF');

  // Filtered ministers based on composition
  const filteredMinisters = (allMinisters || []).filter((m) => {
    if (composition === '1a_turma') return m.turma === '1a Turma' || m.turma === 'Presidente';
    if (composition === '2a_turma') return m.turma === '2a Turma' || m.turma === 'Vice-Presidente';
    return true;
  });

  // Step 3 simulation
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationId, setSimulationId] = useState<string | null>(null);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [analysisStage, setAnalysisStage] = useState('');
  const [currentPhaseDescription, setCurrentPhaseDescription] = useState('');
  const [currentPhase, setCurrentPhase] = useState<string | null>(null);

  // Streaming content
  const [relatorioText, setRelatorioText] = useState('');
  const [voteTexts, setVoteTexts] = useState<Record<string, string>>({});
  const [currentVoter, setCurrentVoter] = useState<string | null>(null);
  const [votes, setVotes] = useState<VoteResult[]>([]);
  const [proclamacaoText, setProclamacaoText] = useState('');
  const [strategicReport, setStrategicReport] = useState('');

  // Batching refs
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

  // ── Load from history when ?id= is present ──
  const { data: historySimulation } = useSimulationDetail(historyId);
  const historyLoadedRef = useRef(false);

  useEffect(() => {
    if (!historySimulation || historyLoadedRef.current) return;
    if (historySimulation.status !== 'completed') return;
    historyLoadedRef.current = true;

    const result = historySimulation.result || {};
    const config = historySimulation.config || {};

    // Populate state from saved simulation
    setSimulationId(historySimulation.id);
    setActionType(config.action_type || '');
    setComposition(config.composition || 'plenario');
    setCaseDescription(config.case_description || '');

    // Populate result data
    setRelatorioText(result.relatorio || '');
    setProclamacaoText(result.proclamacao || '');
    setStrategicReport(result.strategic_report || '');

    // Reconstruct votes from result
    if (result.votes && Array.isArray(result.votes)) {
      const reconstructedVotes: VoteResult[] = result.votes.map((v: any) => ({
        minister: v.minister || v.name || '',
        vote: v.vote || v.decision || '',
        is_relator: v.is_relator || (v.minister === result.relator),
      }));
      setVotes(reconstructedVotes);
    }

    // Jump to results step
    setCurrentStep(3);
    setLoadedFromHistory(true);

    toast({
      title: 'Simulação carregada do histórico',
      description: `"${historySimulation.title}" foi carregada com sucesso.`,
    });
  }, [historySimulation, toast]);

  // ─── Start simulation ───

  const startSimulation = useCallback(async () => {
    setIsSimulating(true);
    setAnalysisProgress(0);
    setAnalysisStage('Iniciando simulação...');
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

      // 1. Create simulation
      const createRes = await fetch('/api/v1/simulations/simulations/', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          simulation_type: 'stf',
          title: `Simulação STF - ${ACTION_TYPES.find(a => a.value === actionType)?.label || actionType}`,
          config: {
            action_type: actionType,
            composition,
            case_description: caseDescription,
          },
        }),
      });
      if (!createRes.ok) throw new Error(`Erro ao criar simulação: HTTP ${createRes.status}`);
      const simData = await createRes.json();
      const simId = simData.id;
      setSimulationId(simId);

      // 2. Start SSE
      const response = await fetch(`/api/v1/simulations/simulations/${simId}/stf/start/`, {
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
              setCurrentPhase(event.phase);
            } else if (eventType === 'ministers') {
              // Ministers list received
            } else if (eventType === 'phase') {
              setAnalysisStage(event.content || '');
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
                title: 'Simulação concluída',
                description: 'O julgamento do STF foi simulado com sucesso.',
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
  }, [actionType, composition, caseDescription, toast, scheduleStreamFlush, flushStreamBuffers]);

  // ─── Start ALL simultaneous STF simulations ───
  const startAllSimulations = useCallback(async () => {
    setIsSimulating(true);
    setCurrentStep(2);

    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };

    const instances: typeof simInstances = [];
    for (let i = 0; i < simulationCount; i++) {
      try {
        const createRes = await fetch('/api/v1/simulations/simulations/', {
          method: 'POST',
          headers,
          body: JSON.stringify({
            simulation_type: 'stf',
            title: `Simulação STF ${i + 1} - ${ACTION_TYPES.find((a) => a.value === actionType)?.label || actionType}`,
            config: { action_type: actionType, composition, case_description: caseDescription },
          }),
        });
        if (!createRes.ok) throw new Error(`HTTP ${createRes.status}`);
        const simData = await createRes.json();
        instances.push({
          id: i,
          simulationId: simData.id,
          status: 'running',
          relatorioText: '',
          voteTexts: {},
          votes: [],
          proclamacaoText: '',
          strategicReport: '',
        });
      } catch (error: any) {
        toast({ title: `Erro na simulação ${i + 1}`, description: error.message, variant: 'destructive' });
      }
    }

    setSimInstances(instances);
    setActiveSimTab(0);

    for (const inst of instances) {
      const controller = new AbortController();
      simAbortControllers.current[inst.id] = controller;
      (async () => {
        try {
          const response = await fetch(`/api/v1/simulations/simulations/${inst.simulationId}/stf/start/`, {
            method: 'POST',
            headers,
            body: JSON.stringify({}),
            signal: controller.signal,
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
                const idx = inst.id;
                if (eventType === 'relatorio') {
                  setSimInstances((prev) => prev.map((s, i) => i === idx ? { ...s, relatorioText: s.relatorioText + (event.content || '') } : s));
                } else if (eventType === 'vote_text') {
                  const minister = event.minister || '';
                  if (minister) {
                    setSimInstances((prev) => prev.map((s, i) => i === idx ? { ...s, voteTexts: { ...s.voteTexts, [minister]: (s.voteTexts[minister] || '') + (event.content || '') } } : s));
                  }
                } else if (eventType === 'vote_result') {
                  setSimInstances((prev) => prev.map((s, i) => i === idx ? { ...s, votes: [...s.votes, { minister: event.minister, vote: event.vote, is_relator: event.is_relator }] } : s));
                } else if (eventType === 'proclamacao') {
                  setSimInstances((prev) => prev.map((s, i) => i === idx ? { ...s, proclamacaoText: s.proclamacaoText + (event.content || '') } : s));
                } else if (eventType === 'relatorio_estrategico') {
                  setSimInstances((prev) => prev.map((s, i) => i === idx ? { ...s, strategicReport: s.strategicReport + (event.content || '') } : s));
                } else if (eventType === 'complete') {
                  setSimInstances((prev) => prev.map((s, i) => i === idx ? { ...s, status: 'completed' } : s));
                } else if (eventType === 'error') {
                  setSimInstances((prev) => prev.map((s, i) => i === idx ? { ...s, status: 'failed' } : s));
                }
              } catch { /* ignore */ }
            }
          }
          setSimInstances((prev) => prev.map((s, i) => i === inst.id ? { ...s, status: s.status === 'running' ? 'completed' : s.status } : s));
        } catch (error: any) {
          if (error.name === 'AbortError') return;
          setSimInstances((prev) => prev.map((s, i) => i === inst.id ? { ...s, status: 'failed' } : s));
        }
      })();
    }
  }, [actionType, composition, caseDescription, simulationCount, toast]);

  // ─── Question handler ───

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

  // ─── PDF Export ───

  const [isExportingPdf, setIsExportingPdf] = useState(false);

  const exportPdf = useCallback(async () => {
    if (!votes.length && !proclamacaoText && !strategicReport) {
      toast({ title: 'Nada para exportar', description: 'O julgamento ainda nao foi concluido.', variant: 'destructive' });
      return;
    }

    const title = `Simulação STF - ${ACTION_TYPES.find(a => a.value === actionType)?.label || actionType}`;
    const dateStr = new Date().toLocaleDateString('pt-BR');

    // Try backend PDF generation first
    if (simulationId) {
      setIsExportingPdf(true);
      try {
        const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
        const res = await fetch(`/api/v1/simulations/simulations/${simulationId}/generate-pdf/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
        });
        if (res.ok) {
          const blob = await res.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          const fileName = `simulação_stf_${new Date().toISOString().split('T')[0]}.pdf`;
          a.download = fileName;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
          toast({ title: 'PDF exportado', description: `Arquivo "${fileName}" baixado com sucesso.` });
          setIsExportingPdf(false);
          return;
        }
        console.warn('Backend PDF generation failed, falling back to client-side HTML.');
      } catch {
        console.warn('Backend PDF endpoint unavailable, falling back to client-side HTML.');
      }
      setIsExportingPdf(false);
    }

    // Fallback: client-side HTML blob download
    const markdownToHtml = (text: string) => {
      return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br/>');
    };

    const voteCounts = countVotesByCategory(votes);
    const provimento = voteCounts.provimento || 0;
    const desprovimento = voteCounts.desprovimento || 0;
    const parcial = voteCounts.parcial || 0;
    const resultado = provimento > desprovimento ? 'PROVIDO' : 'DESPROVIDO';

    const votesHtml = votes.map(v =>
      `<tr><td>${v.minister}${v.is_relator ? ' (Relator)' : ''}</td><td>${v.vote}</td></tr>`
    ).join('');

    const htmlContent = `
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>${title}</title>
  <style>
    @page { size: A4; margin: 2.5cm 2cm 2.5cm 3cm; }
    body { font-family: 'Times New Roman', Times, serif; font-size: 12pt; line-height: 1.5; color: #000; max-width: 210mm; margin: 0 auto; padding: 2.5cm 2cm 2.5cm 3cm; text-align: justify; }
    h1 { font-size: 16pt; font-weight: bold; text-align: center; margin-bottom: 24pt; }
    h2 { font-size: 14pt; font-weight: bold; margin-top: 24pt; margin-bottom: 12pt; border-bottom: 1px solid #ccc; padding-bottom: 6pt; }
    p { margin-bottom: 12pt; text-indent: 2cm; }
    p:first-of-type { text-indent: 0; }
    .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 16px; margin-bottom: 24px; }
    .resultado-badge { text-align: center; padding: 12px 24px; font-size: 14pt; font-weight: bold; border: 2px solid #333; display: inline-block; margin: 16px auto; }
    .footer { margin-top: 40px; padding-top: 16px; border-top: 1px solid #ccc; font-size: 9pt; color: #999; text-align: center; }
    table { width: 100%; border-collapse: collapse; margin: 12pt 0; font-size: 10pt; }
    th { background-color: #d3d3d3; padding: 8pt; text-align: left; font-weight: bold; border: 1px solid #000; }
    td { border: 1px solid #000; padding: 8pt; }
  </style>
</head>
<body>
  <div class="header">
    <h1>SIMULACAO DE JULGAMENTO - STF</h1>
    <p style="text-indent:0;font-size:11pt;color:#555;">${title}</p>
  </div>
  <p style="text-indent:0;"><strong>Data:</strong> ${dateStr} | <strong>Composicao:</strong> ${COMPOSITIONS.find(c => c.value === composition)?.label || composition}</p>
  <div style="text-align:center;margin:20px 0;"><span class="resultado-badge">${resultado}</span></div>
  <div style="text-align:center;margin-bottom:20px;"><strong>Provimento:</strong> ${provimento} x ${desprovimento} <strong>:Desprovimento</strong></div>
  <h2>Votos Individuais</h2>
  <table><thead><tr><th>Ministro</th><th>Voto</th></tr></thead><tbody>${votesHtml}</tbody></table>
  ${proclamacaoText ? `<h2>Proclamacao do Resultado</h2><div>${markdownToHtml(proclamacaoText)}</div>` : ''}
  ${strategicReport ? `<h2>Relatorio Estrategico</h2><div>${markdownToHtml(strategicReport)}</div>` : ''}
  <div class="footer">
    <p>Documento gerado automaticamente pelo Verus.AI - Simulação STF</p>
    <p>Este documento e uma simulação e não possui valor jurídico.</p>
  </div>
</body>
</html>`;

    const blob = new Blob([htmlContent], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const fileName = `simulação_stf_${new Date().toISOString().split('T')[0]}.pdf`;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast({ title: 'PDF exportado', description: `Arquivo "${fileName}" baixado com sucesso.` });
  }, [toast, votes, proclamacaoText, strategicReport, simulationId, actionType, composition]);

  // ─── Reset ───

  const resetSimulation = useCallback(() => {
    setSimulationCount(1);
    setCurrentStep(0);
    setActionType('');
    setComposition('plenario');
    setCaseDescription('');
    setSimulationId(null);
    setAnalysisProgress(0);
    setAnalysisStage('');
    setRelatorioText('');
    setVoteTexts({});
    setVotes([]);
    setProclamacaoText('');
    setStrategicReport('');
    setCurrentVoter(null);
    setQuestionText('');
    setQuestionAnswer('');
  }, []);

  // ─── Navigation ───

  const canAdvance = () => {
    if (currentStep === 0) return actionType !== '' && caseDescription.trim().length > 20;
    if (currentStep === 1) return filteredMinisters.length > 0;
    return true;
  };

  const nextStep = () => {
    if (currentStep < STEPS.length - 1) {
      if (currentStep === 1) {
        if (simulationCount > 1) {
          setTimeout(() => startAllSimulations(), 300);
        } else {
          setCurrentStep(2);
          setTimeout(() => startSimulation(), 300);
        }
      } else {
        setCurrentStep((s) => s + 1);
      }
    }
  };
  const prevStep = () => {
    if (currentStep > 0) setCurrentStep((s) => s - 1);
  };

  // ─── Stepper ───

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
              {isCompleted ? (
                <CheckCircle2 className="h-4 w-4" />
              ) : (
                <Icon className="h-4 w-4" />
              )}
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

  // ─── Step 0: Configuration ───

  const renderStep0 = () => (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <div className="flex items-center gap-3 mb-2">
          <Landmark className="h-8 w-8 text-primary" />
          <h2 className="text-2xl font-bold">Simulação do STF</h2>
        </div>
        <p className="text-muted-foreground">Configure o julgamento simulado no Supremo Tribunal Federal.</p>
      </div>

      <Card className="border-amber-200 bg-amber-50/50 dark:border-amber-900 dark:bg-amber-950/20">
        <CardContent className="flex gap-4 py-4">
          <AlertCircle className="h-6 w-6 text-amber-500 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-amber-800 dark:text-amber-200">
              Cada ministro vota individualmente com base em seu perfil real
            </p>
            <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
              A IA simula o voto de cada ministro do STF com base em sua filosofia judicial,
              posições anteriores e estilo de fundamentação. Quanto mais detalhado o caso,
              mais realista será a simulação.
            </p>
          </div>
        </CardContent>
      </Card>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label>Tipo de Ação *</Label>
          <Select value={actionType} onValueChange={setActionType}>
            <SelectTrigger>
              <SelectValue placeholder="Selecione o tipo de ação" />
            </SelectTrigger>
            <SelectContent>
              {ACTION_TYPES.map((at) => (
                <SelectItem key={at.value} value={at.value}>{at.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Composição *</Label>
          <Select value={composition} onValueChange={setComposition}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {COMPOSITIONS.map((c) => (
                <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Descrição do Caso *</Label>
          <p className="text-xs text-muted-foreground">
            Descreva o caso constitucional a ser julgado. Inclua fatos, questão jurídica,
            argumentos das partes e legislação envolvida.
          </p>
          <Textarea
            value={caseDescription}
            onChange={(e) => setCaseDescription(e.target.value)}
            placeholder="Ex: Recurso Extraordinário que discute a constitucionalidade do artigo X da Lei Y, que estabelece..."
            className="min-h-[200px]"
          />
          <p className="text-xs text-muted-foreground text-right">
            {caseDescription.length} caracteres (minimo 20)
          </p>
        </div>

        <div className="space-y-2">
          <Label>Quantidade de Simulações Simultâneas</Label>
          <p className="text-xs text-muted-foreground">
            Execute múltiplas simulações ao mesmo tempo e compare os resultados
          </p>
          <Select value={String(simulationCount)} onValueChange={(v) => setSimulationCount(Number(v))}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {[1, 2, 3, 4, 5].map((n) => (
                <SelectItem key={n} value={String(n)}>
                  {n} simulação{n > 1 ? 'ões' : ''}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  );

  // ─── Step 1: Ministers ───

  const renderStep1 = () => (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-1">Ministros do STF</h2>
        <p className="text-muted-foreground">
          {COMPOSITIONS.find(c => c.value === composition)?.label} - {filteredMinisters.length} ministros participarao do julgamento.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filteredMinisters.map((m) => {
          const hasVoted = votes.some(v => v.minister === m.name);
          const isVoting = currentVoter === m.name;
          const ministerVote = votes.find(v => v.minister === m.name);
          const isProvimento = ministerVote && categorizeVote(ministerVote.vote).id === 'provimento';
          return (
          <Card key={m.id} className={`transition-all duration-300 ${
            isVoting ? 'border-2 border-purple-500 speaker-active' :
            hasVoted ? 'minister-voted ' + (isProvimento ? 'bg-green-50/40 dark:bg-green-950/20' : 'bg-red-50/40 dark:bg-red-950/20') :
            'hover:border-primary/30'
          }`}>
            <CardHeader className="pb-3">
              <div className="flex items-center gap-3">
                <div className={`flex h-10 w-10 items-center justify-center rounded-full transition-colors ${
                  isVoting ? 'bg-purple-500/20 animate-pulse' :
                  hasVoted ? categorizeVote(ministerVote!.vote).iconClass :
                  'bg-primary/10'
                }`}>
                  {isVoting ? (
                    <Scale className="h-5 w-5 text-purple-600 gavel-thinking" />
                  ) : hasVoted ? (
                    <CheckCircle2 className={`h-5 w-5 ${isProvimento ? 'text-green-600' : 'text-red-600'}`} />
                  ) : (
                    <User className="h-5 w-5 text-primary" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <CardTitle className="text-sm truncate">Min. {m.name}</CardTitle>
                  <CardDescription className="text-xs">{m.turma}</CardDescription>
                </div>
                {hasVoted && ministerVote && (
                  <Badge className={`text-[10px] border-0 vote-reveal ${
                    categorizeVote(ministerVote.vote).badgeClass
                  }`}>
                    {ministerVote.vote}
                  </Badge>
                )}
                {isVoting && (
                  <div className="flex gap-1">
                    <div className="h-1.5 w-1.5 rounded-full bg-purple-500 thinking-dot" />
                    <div className="h-1.5 w-1.5 rounded-full bg-purple-500 thinking-dot" />
                    <div className="h-1.5 w-1.5 rounded-full bg-purple-500 thinking-dot" />
                  </div>
                )}
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

              <div>
                <p className="text-xs font-medium text-muted-foreground mb-1">Indicado por</p>
                <p className="text-xs">{m.appointed_by}</p>
              </div>
            </CardContent>
          </Card>
          );
        })}
      </div>

      {filteredMinisters.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Users className="h-12 w-12 text-muted-foreground/40 mb-4" />
            <p className="text-muted-foreground">Nenhum ministro encontrado para esta composição.</p>
            <p className="text-sm text-muted-foreground mt-1">
              Os perfis dos ministros estão sendo carregados. Aguarde alguns instantes e recarregue a página.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );

  // ─── Step 2: Simulation in progress ───

  const renderStep2 = () => {
    // Calculate vote scoreboard
    const voteCounts = countVotesByCategory(votes);
    const provimento = voteCounts.provimento || 0;
    const desprovimento = voteCounts.desprovimento || 0;
    const parcial = voteCounts.parcial || 0;

    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h2 className="text-2xl font-bold mb-1">Julgamento em Andamento</h2>
          <p className="text-muted-foreground">{analysisStage || 'Preparando julgamento...'}</p>
        </div>

        {/* Multi-simulation Tab Bar */}
        {simInstances.length > 1 && (
          <div className="flex gap-2 overflow-x-auto pb-1">
            {simInstances.map((sim, i) => (
              <button
                key={i}
                onClick={() => setActiveSimTab(i)}
                className={cn(
                  'flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all shrink-0 border sim-tab-active',
                  activeSimTab === i ? 'bg-primary text-primary-foreground border-primary' : 'bg-muted border-transparent',
                  sim.status === 'completed' && activeSimTab !== i && 'border-green-500 border-2',
                  sim.status === 'failed' && activeSimTab !== i && 'border-red-500 border-2'
                )}
              >
                Simulação {i + 1}
                {sim.status === 'completed' && <CheckCircle2 className="ml-1 h-3 w-3" />}
                {sim.status === 'running' && <Loader2 className="ml-1 h-3 w-3 animate-spin" />}
                {sim.status === 'failed' && <X className="ml-1 h-3 w-3" />}
              </button>
            ))}
          </div>
        )}

        {/* Active voter indicator with glow */}
        {isSimulating && currentVoter && (
          <div className="flex items-center gap-3 py-3 px-4 bg-muted/50 rounded-lg border-2 speaker-active">
            <div className="h-10 w-10 rounded-full bg-purple-500 flex items-center justify-center animate-pulse">
              <Scale className="h-5 w-5 text-white gavel-thinking" />
            </div>
            <div className="flex-1">
              <span className="text-sm font-medium">Min. {currentVoter}</span>
              <p className="text-xs text-muted-foreground">{currentPhaseDescription || 'Proferindo voto...'}</p>
            </div>
            <div className="flex gap-1 ml-auto">
              <div className="h-2 w-2 rounded-full bg-purple-500 thinking-dot" />
              <div className="h-2 w-2 rounded-full bg-purple-500 thinking-dot" />
              <div className="h-2 w-2 rounded-full bg-purple-500 thinking-dot" />
            </div>
          </div>
        )}

        {/* Minister status cards grid during voting */}
        {isSimulating && filteredMinisters.length > 0 && (
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2">
            {filteredMinisters.map((m) => {
              const hasVoted = votes.some(v => v.minister === m.name);
              const isVoting = currentVoter === m.name;
              const ministerVote = votes.find(v => v.minister === m.name);
              const isProvimento = ministerVote && categorizeVote(ministerVote.vote).id === 'provimento';
              return (
                <div
                  key={m.id}
                  className={`flex flex-col items-center p-2 rounded-lg border text-center transition-all duration-300 ${
                    isVoting ? 'border-2 border-purple-500 bg-purple-50 dark:bg-purple-950/20 speaker-active' :
                    hasVoted ? 'minister-voted ' + (isProvimento ? 'border-green-300 bg-green-50 dark:border-green-800 dark:bg-green-950/20' : 'border-red-300 bg-red-50 dark:border-red-800 dark:bg-red-950/20') :
                    'border-muted bg-muted/30'
                  }`}
                >
                  <div className={`h-8 w-8 rounded-full flex items-center justify-center mb-1 ${
                    isVoting ? 'bg-purple-500/20 animate-pulse' :
                    hasVoted ? categorizeVote(ministerVote!.vote).iconClass :
                    'bg-muted'
                  }`}>
                    {isVoting ? (
                      <Scale className="h-4 w-4 text-purple-600 gavel-thinking" />
                    ) : hasVoted ? (
                      <CheckCircle2 className={`h-4 w-4 ${isProvimento ? 'text-green-600' : 'text-red-600'}`} />
                    ) : (
                      <User className="h-4 w-4 text-muted-foreground" />
                    )}
                  </div>
                  <span className="text-[10px] font-medium truncate w-full">{m.name.split(' ').slice(-1)[0]}</span>
                  {hasVoted && ministerVote && (
                    <Badge className={`text-[8px] px-1 py-0 mt-0.5 border-0 vote-reveal ${
                      categorizeVote(ministerVote.vote).badgeClass
                    }`}>
                      {isProvimento ? 'Prov.' : 'Desp.'}
                    </Badge>
                  )}
                  {isVoting && (
                    <span className="text-[8px] text-purple-600 dark:text-purple-400 mt-0.5 font-medium">Votando...</span>
                  )}
                  {!hasVoted && !isVoting && (
                    <span className="text-[8px] text-muted-foreground mt-0.5">Pendente</span>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Progress */}
        <Card>
          <CardContent className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Progresso</span>
              <span className="text-sm text-muted-foreground">{analysisProgress}%</span>
            </div>
            <Progress value={analysisProgress} />
          </CardContent>
        </Card>

        {/* Vote scoreboard */}
        {votes.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Placar de Votação</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-center gap-6 mb-4">
                <div className="text-center">
                  <p className={`text-3xl font-bold ${VOTE_CATEGORIES[0].scoreClass} score-update`} key={`prov-${provimento}`}>{provimento}</p>
                  <p className="text-xs text-muted-foreground">Provimento</p>
                </div>
                {parcial > 0 && (
                  <>
                    <div className="text-center">
                      <p className={`text-3xl font-bold ${VOTE_CATEGORIES[2].scoreClass} score-update`} key={`parc-${parcial}`}>{parcial}</p>
                      <p className="text-xs text-muted-foreground">Parcial</p>
                    </div>
                  </>
                )}
                <div className="text-2xl text-muted-foreground font-bold">x</div>
                <div className="text-center">
                  <p className={`text-3xl font-bold ${VOTE_CATEGORIES[1].scoreClass} score-update`} key={`desp-${desprovimento}`}>{desprovimento}</p>
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
                      className={`text-xs border-0 vote-reveal ${
                        categorizeVote(v.vote).badgeClass
                      }`}
                    >
                      {v.vote}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Streaming content: current vote */}
        {currentVoter && voteTexts[currentVoter] && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Scale className="h-4 w-4" />
                Voto do Min. {currentVoter} {isSimulating && '(em andamento...)'}
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

  // ─── Step 3: Results ───

  const renderStep3 = () => {
    const voteCounts = countVotesByCategory(votes);
    const provimento = voteCounts.provimento || 0;
    const desprovimento = voteCounts.desprovimento || 0;
    const parcial = voteCounts.parcial || 0;
    const isVictory = provimento > desprovimento;
    const dominant = getDominantCategory(votes);
    const isUnanimous = Object.values(voteCounts).filter(c => c > 0).length <= 1;
    const catLabels: Record<string, string> = { provimento: 'PROVIDO', desprovimento: 'DESPROVIDO', parcial: 'PROVIMENTO PARCIAL', sem_merito: 'NÃO CONHECIDO', indeterminado: 'INDETERMINADO' };
    const resultado = catLabels[dominant.id] || 'INDETERMINADO';

    return (
      <div className="max-w-4xl mx-auto space-y-6">
        {loadedFromHistory && (
          <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-50 border border-blue-200 dark:bg-blue-950/20 dark:border-blue-900">
            <History className="h-4 w-4 text-blue-600 dark:text-blue-400" />
            <span className="text-sm text-blue-700 dark:text-blue-300">Carregado do histórico</span>
          </div>
        )}
        <div className="text-center">
          <h2 className="text-3xl font-bold mb-2">Resultado do Julgamento</h2>
          <Badge
            className={`text-lg px-6 py-2 border-0 ${
              isVictory ? VOTE_CATEGORIES[0].scoreClass : VOTE_CATEGORIES[1].scoreClass
            }`}
          >
            {resultado}
          </Badge>
        </div>

        {/* Scoreboard */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-center gap-6 mb-4">
              <div className="text-center">
                <p className={`text-4xl font-bold ${VOTE_CATEGORIES[0].scoreClass}`}>{provimento}</p>
                <p className="text-sm text-muted-foreground">Provimento</p>
              </div>
              {parcial > 0 && (
                <>
                  <div className="text-center">
                    <p className={`text-4xl font-bold ${VOTE_CATEGORIES[2].scoreClass}`}>{parcial}</p>
                    <p className="text-sm text-muted-foreground">Parcial</p>
                  </div>
                </>
              )}
              <div className="text-3xl text-muted-foreground font-bold">x</div>
              <div className="text-center">
                <p className={`text-4xl font-bold ${VOTE_CATEGORIES[1].scoreClass}`}>{desprovimento}</p>
                <p className="text-sm text-muted-foreground">Desprovimento</p>
              </div>
            </div>
            <p className="text-center text-sm text-muted-foreground">
              {isUnanimous ? 'Decisão unânime' : 'Decisão por maioria'} - {votes.length} votos
            </p>
          </CardContent>
        </Card>

        {/* Votes breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>Votos Individuais</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {votes.map((v, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors vote-reveal" style={{ animationDelay: `${i * 0.15}s`, animationFillMode: 'both' }}>
                <div className="flex items-center gap-3">
                  <div className={`h-8 w-8 rounded-full flex items-center justify-center ${
                    categorizeVote(v.vote).iconClass
                  }`}>
                    <User className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">Min. {v.minister}</p>
                    {v.is_relator && <p className="text-xs text-muted-foreground">Relator</p>}
                  </div>
                </div>
                <Badge
                  className={`border-0 vote-reveal ${
                    categorizeVote(v.vote).badgeClass
                  }`}
                >
                  {v.vote}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Proclamação */}
        {proclamacaoText && (
          <Card>
            <CardHeader>
              <CardTitle>Proclamação do Resultado</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[300px]">
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {proclamacaoText}
                  </ReactMarkdown>
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        )}

        {/* View individual votes */}
        {Object.keys(voteTexts).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Votos Completos</CardTitle>
              <CardDescription>Clique em um ministro para ler o voto integral</CardDescription>
            </CardHeader>
            <CardContent>
              <details className="space-y-4">
                <summary className="cursor-pointer text-sm font-medium text-primary hover:underline">
                  Expandir votos ({Object.keys(voteTexts).length} votos)
                </summary>
                <div className="space-y-4 mt-4">
                  {Object.entries(voteTexts).map(([name, text]) => (
                    <details key={name} className="border rounded-lg p-3">
                      <summary className="cursor-pointer text-sm font-medium">
                        Min. {name}
                      </summary>
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
          <Card className={`border-2 ${isVictory ? VOTE_CATEGORIES[0].borderClass : VOTE_CATEGORIES[1].borderClass}`}>
            <CardHeader>
              <CardTitle className={isVictory ? VOTE_CATEGORIES[0].scoreClass : VOTE_CATEGORIES[1].scoreClass}>
                Relatório Estratégico
              </CardTitle>
              <CardDescription>
                Análise do resultado e próximos passos
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {strategicReport}
                  </ReactMarkdown>
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
                  <CardDescription>Pergunte sobre o resultado ou votos individuais</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {[
                  'Por que o relator votou dessa forma?',
                  'Quais ministros podem mudar de voto em embargos?',
                  'Qual a tese fixada neste julgamento?',
                ].map((q, i) => (
                  <Button
                    key={i}
                    variant="outline"
                    size="sm"
                    onClick={() => setQuestionText(q)}
                    className="text-xs"
                  >
                    {q}
                  </Button>
                ))}
              </div>

              <div className="flex gap-2">
                <Textarea
                  value={questionText}
                  onChange={(e) => setQuestionText(e.target.value)}
                  placeholder="Sua pergunta sobre o julgamento..."
                  className="flex-1 min-h-[80px]"
                />
                <Button
                  onClick={handleQuestion}
                  disabled={isQuestioning || !questionText.trim()}
                  className="self-end"
                >
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
            {isExportingPdf ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <FileDown className="h-4 w-4 mr-2" />
            )}
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

  // ─── Main ───

  return (
    <div className="min-h-screen flex flex-col -mx-3 sm:-mx-6 -mb-6">
      {renderStepper()}

      <div className="flex-1 p-3 sm:p-6">
        {currentStep === 0 && renderStep0()}
        {currentStep === 1 && renderStep1()}
        {currentStep === 2 && renderStep2()}
        {currentStep === 3 && renderStep3()}
        <SimulationHistoryList type="stf" />
      </div>

      {/* Navigation */}
      {currentStep < 2 && (
        <div className="border-t p-3 sm:p-4 flex items-center justify-between max-w-3xl mx-auto w-full safe-area-bottom">
          <Button
            variant="outline"
            onClick={currentStep === 0 ? () => router.push('/dashboard/simulations') : prevStep}
          >
            <ChevronLeft className="h-4 w-4 mr-2" />
            {currentStep === 0 ? 'Voltar' : 'Anterior'}
          </Button>
          <Button onClick={nextStep} disabled={!canAdvance()}>
            {currentStep === 1 ? 'Iniciar Julgamento' : 'Próximo'}
            <ChevronRight className="h-4 w-4 ml-2" />
          </Button>
        </div>
      )}
    </div>
  );
}
