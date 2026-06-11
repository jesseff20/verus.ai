'use client';

import { useState, useCallback, useRef, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { useToast } from '@/hooks/use-toast';
import { useCourts, useJudgeProfiles, useSimulationDetail } from '@/hooks/use-simulations';
import api from '@/lib/api';
import Link from 'next/link';
import {
  Scale, ChevronLeft, ChevronRight, Upload, Loader2,
  CheckCircle2, X, FileDown, RotateCcw, User, Building2,
  MapPin, FileText, Search, TrendingUp, AlertCircle,
  Shield, AlertTriangle, Send, MessageSquare, CheckSquare, Square,
  Briefcase, BookOpen, BarChart3, ListTodo, Bot, FileEdit, Link2,
  History,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import SimulationHistoryList from '@/components/SimulationHistoryList';
import { cn } from '@/lib/utils';
// Multi-simulation already implemented natively in this page

// ─── Constants ───

const BRAZILIAN_STATES = [
  'AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
  'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN',
  'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO',
];

const PROCESS_TYPES = [
  'Cível',
  'Criminal',
  'Trabalhista',
  'Previdenciário',
  'Tributário',
  'Administrativo',
  'Ambiental',
  'Consumerista',
  'Empresarial',
  'Família e Sucessões',
];

const STEPS = [
  { title: 'Seleção do Juiz', icon: User },
  { title: 'Documentos do Processo', icon: FileText },
  { title: 'Análise', icon: Search },
  { title: 'Sentença Simulada', icon: Scale },
];

const JUDGE_ANALYSIS_PHASES = [
  { key: 'profile', label: 'Analisando perfil do juiz', icon: User, description: 'Consultando histórico de decisões e padrões de julgamento...' },
  { key: 'documents', label: 'Analisando documentos', icon: FileText, description: 'Lendo petição inicial, contestação e provas anexadas...' },
  { key: 'jurisprudence', label: 'Consultando jurisprudência', icon: Search, description: 'Buscando precedentes e súmulas aplicáveis ao caso...' },
  { key: 'fundamentacao', label: 'Elaborando fundamentação', icon: BookOpen, description: 'Construindo a fundamentação jurídica da sentença...' },
  { key: 'sentence', label: 'Redigindo sentença', icon: Scale, description: 'Redigindo o relatório, fundamentação e dispositivo...' },
  { key: 'report', label: 'Gerando relatório estratégico', icon: BarChart3, description: 'Analisando pontos fortes, fracos e recomendações...' },
];

// ─── Types ───

interface JudgeAnalysis {
  profile: {
    name: string;
    court: string;
    comarca: string;
    total_decisions: number;
    tendencies: string[];
    approval_rate: number;
    avg_sentence_length: string;
    common_fundamentations: string[];
  };
  confidence: number;
}

// ─── Component ───

export default function JudgeSimulationPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>}>
      <JudgeSimulationPageInner />
    </Suspense>
  );
}

function JudgeSimulationPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const historyId = searchParams.get('id');
  const { toast } = useToast();

  // Track whether we loaded from history
  const [loadedFromHistory, setLoadedFromHistory] = useState(false);

  // Step navigation
  const [currentStep, setCurrentStep] = useState(0);

  // Step 1 - Seleção do Juiz
  const [selectedState, setSelectedState] = useState('');
  const [selectedTribunal, setSelectedTribunal] = useState('');
  const [selectedComarca, setSelectedComarca] = useState('');
  const [selectedJudgeId, setSelectedJudgeId] = useState('');
  const [useGenericJudge, setUseGenericJudge] = useState(false);
  const [selectedCaseId, setSelectedCaseId] = useState('');

  // Multi-simulation
  const [simulationCount, setSimulationCount] = useState(1);
  const [simInstances, setSimInstances] = useState<{ id: number; simulationId: string; status: 'running' | 'completed' | 'failed'; sentenceContent: string; strategicReport: string; dispositivo: string | null; isVictory: boolean; judgeAnalysis: JudgeAnalysis | null }[]>([]);
  const [activeSimTab, setActiveSimTab] = useState(0);
  const simAbortControllers = useRef<Record<number, AbortController>>({});

  // Step 2 - Documentos
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [processType, setProcessType] = useState('');
  const [caseValue, setCaseValue] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Step 3 - Análise
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [analysisStage, setAnalysisStage] = useState('');
  const [judgeAnalysis, setJudgeAnalysis] = useState<JudgeAnalysis | null>(null);
  const [sentenceContent, setSentenceContent] = useState('');
  const [completedPhases, setCompletedPhases] = useState<string[]>([]);
  const [currentPhase, setCurrentPhase] = useState<string | null>(null);
  const [currentPhaseDescription, setCurrentPhaseDescription] = useState('');

  // Step 4 - Sentença
  const [dispositivo, setDispositivo] = useState<'procedente' | 'improcedente' | 'parcialmente_procedente' | null>(null);
  const [fundamentacao, setFundamentacao] = useState('');
  const [confidence, setConfidence] = useState(0);

  // Strategic Report
  const [strategicReport, setStrategicReport] = useState('');
  const [isVictory, setIsVictory] = useState(false);

  // Question simulation
  const [questionText, setQuestionText] = useState('');
  const [questionAnswer, setQuestionAnswer] = useState('');
  const [isQuestioning, setIsQuestioning] = useState(false);
  const [simulationId, setSimulationId] = useState<string | null>(null);

  // ── Batching refs for streaming content ──
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

  // Checklist state
  const [checkedItems, setCheckedItems] = useState<Record<number, boolean>>({});

  // Hooks
  const { data: courts } = useCourts(selectedState || undefined);
  const { data: judges } = useJudgeProfiles({
    state: selectedState || undefined,
    court: selectedTribunal || undefined,
    comarca: selectedComarca || undefined,
  });

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
    setSentenceContent(result.sentence || '');
    setStrategicReport(result.strategic_report || '');
    setDispositivo(result.dispositivo || null);
    setFundamentacao(result.fundamentacao || '');
    setConfidence(result.confidence || 0);
    setIsVictory(result.dispositivo === 'procedente' || result.dispositivo === 'parcialmente_procedente');
    setSelectedState(config.state || '');
    setSelectedComarca(config.comarca || '');
    setProcessType(config.process_type || result.process_type || '');
    setCaseValue(config.case_value || result.case_value || '');

    // Jump to results step
    setCurrentStep(3);
    setLoadedFromHistory(true);

    toast({
      title: 'Simulação carregada do histórico',
      description: `"${historySimulation.title}" foi carregada com sucesso.`,
    });
  }, [historySimulation, toast]);

  // Buscar casos existentes do usuário
  const { data: userCases } = useQuery({
    queryKey: ['user-cases'],
    queryFn: async () => {
      const response = await api.get('/api/v1/processos/');
      return response.data.results || response.data;
    },
  });

  // Derived
  const tribunais = courts?.map((c) => c.name) || [];
  const comarcas = courts?.find((c) => c.name === selectedTribunal)?.comarcas || [];

  // ─── Handlers: Step 1 ───

  const handleStateChange = useCallback((state: string) => {
    setSelectedState(state);
    setSelectedTribunal('');
    setSelectedComarca('');
    setSelectedJudgeId('');
  }, []);

  const handleTribunalChange = useCallback((tribunal: string) => {
    setSelectedTribunal(tribunal);
    setSelectedComarca('');
    setSelectedJudgeId('');
  }, []);

  const handleComarcaChange = useCallback((comarca: string) => {
    setSelectedComarca(comarca);
    setSelectedJudgeId('');
  }, []);

  const handleSelectCase = useCallback((caseId: string) => {
    setSelectedCaseId(caseId);
    const selectedCase = userCases?.find((c: any) => c.id === caseId);
    if (selectedCase) {
      // Step 1 - Preencher tribunal e comarca
      if (selectedCase.tribunal) {
        setSelectedTribunal(selectedCase.tribunal);
      }
      if (selectedCase.comarca) {
        setSelectedComarca(selectedCase.comarca);
      }
      // Step 2 - Preencher tipo de processo e valor da causa
      if (selectedCase.especialidade) {
        const especialidadeMap: Record<string, string> = {
          civel: 'Cível',
          criminal: 'Criminal',
          trabalhista: 'Trabalhista',
          tributario: 'Tributário',
          administrativo: 'Administrativo',
          previdenciario: 'Previdenciário',
          familia: 'Família e Sucessões',
          empresarial: 'Empresarial',
          ambiental: 'Ambiental',
          consumidor: 'Consumerista',
          imobiliario: 'Cível',
          outros: 'Cível',
        };
        setProcessType(especialidadeMap[selectedCase.especialidade] || 'Cível');
      }
      if (selectedCase.valor_causa) {
        setCaseValue(`R$ ${Number(selectedCase.valor_causa).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`);
      }
      toast({
        title: 'Caso importado',
        description: `Dados de "${selectedCase.titulo}" preenchidos automaticamente.`,
      });
    }
  }, [userCases, toast]);

  // ─── Handlers: Step 2 ───

  const handleFileUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setUploadedFiles((prev) => [...prev, ...Array.from(e.target.files!)]);
    }
  }, []);

  const removeFile = useCallback((index: number) => {
    setUploadedFiles((prev) => prev.filter((_, i) => i !== index));
  }, []);

  // ─── Handlers: Step 3 - Análise SSE ───

  const startAnalysis = useCallback(async () => {
    setIsAnalyzing(true);
    setAnalysisProgress(0);
    setAnalysisStage('Iniciando análise...');
    setJudgeAnalysis(null);
    setSentenceContent('');
    setCompletedPhases([]);
    setCurrentPhase(null);
    setCurrentPhaseDescription('');

    try {
      const payload = {
        state: selectedState,
        tribunal: selectedTribunal,
        comarca: selectedComarca,
        judge_id: useGenericJudge ? null : selectedJudgeId,
        use_generic: useGenericJudge,
        process_type: processType,
        case_value: caseValue,
      };

      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      const headers = {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      };

      // 1. Criar simulação no backend
      const createRes = await fetch('/api/v1/simulations/simulations/', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          simulation_type: 'judge',
          title: `Simulação de Sentença - ${selectedComarca}/${selectedState}`,
          ...(selectedCaseId ? { case: selectedCaseId } : {}),
          config: {
            ...payload,
          },
        }),
      });
      if (!createRes.ok) throw new Error(`Erro ao criar simulação: HTTP ${createRes.status}`);
      const simData = await createRes.json();
      const simId = simData.id;
      setSimulationId(simId);

      // 2. Iniciar streaming SSE
      const response = await fetch(`/api/v1/simulations/simulations/${simId}/judge/start/`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
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
              // Phase change progress event
              setAnalysisProgress(event.progress || 0);
              setAnalysisStage(event.label || '');
              setCurrentPhaseDescription(event.description || '');
              if (lastPhase && lastPhase !== event.phase) {
                const prev = lastPhase;
                setCompletedPhases((arr) =>
                  arr.includes(prev) ? arr : [...arr, prev]
                );
              }
              lastPhase = event.phase;
              setCurrentPhase(event.phase);
            } else if (eventType === 'progress') {
              setAnalysisProgress(event.progress || 0);
              setAnalysisStage(event.stage || event.content || '');
            } else if (eventType === 'profile') {
              // Judge profile info from backend
              setAnalysisStage('Perfil do juiz carregado');
            } else if (eventType === 'judge_profile') {
              setJudgeAnalysis(event.data);
            } else if (eventType === 'sentence' || eventType === 'sentence_chunk') {
              // Batched: accumulate in ref, flush every 50ms
              pendingSentenceRef.current += (event.content || '');
              scheduleStreamFlush();
            } else if (eventType === 'relatorio') {
              // Batched: accumulate in ref, flush every 50ms
              pendingReportRef.current += (event.content || '');
              scheduleStreamFlush();
              if (event.dispositivo) {
                setDispositivo(event.dispositivo);
                setIsVictory(!!event.is_victory);
              }
            } else if (eventType === 'strategic_report') {
              pendingReportRef.current += (event.content || '');
              scheduleStreamFlush();
              if (event.dispositivo) {
                setDispositivo(event.dispositivo);
                setIsVictory(!!event.is_victory);
              }
            } else if (eventType === 'simulation_id') {
              if (event.simulation_id) setSimulationId(event.simulation_id);
            } else if (eventType === 'complete') {
              // Flush remaining buffered content
              flushStreamBuffers();
              // Mark the last phase as completed
              if (lastPhase) {
                const prev = lastPhase;
                setCompletedPhases((arr) =>
                  arr.includes(prev) ? arr : [...arr, prev]
                );
              }
              setCurrentPhase(null);
              setAnalysisProgress(100);
              setCurrentStep(3);
              toast({
                title: 'Simulação salva no histórico',
                description: 'Você pode revisitar esta simulação a qualquer momento na página de histórico.',
              });
            } else if (eventType === 'result') {
              setDispositivo(event.dispositivo);
              setFundamentacao(event.fundamentacao || '');
              setConfidence(event.confidence || 0);
              if (event.simulation_id) setSimulationId(event.simulation_id);
              setCurrentStep(3);
            } else if (eventType === 'error' || eventType === 'erro') {
              toast({
                title: 'Erro na simulação',
                description: event.content || 'Erro desconhecido no servidor.',
                variant: 'destructive',
              });
              setIsAnalyzing(false);
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
  }, [selectedState, selectedTribunal, selectedComarca, selectedJudgeId, useGenericJudge, processType, caseValue, toast]);

  // ─── Start ALL simultaneous judge analyses ───
  const startAllAnalyses = useCallback(async () => {
    setIsAnalyzing(true);
    setCurrentStep(2);

    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };

    const payload = {
      state: selectedState,
      tribunal: selectedTribunal,
      comarca: selectedComarca,
      judge_id: useGenericJudge ? null : selectedJudgeId,
      use_generic: useGenericJudge,
      process_type: processType,
      case_value: caseValue,
    };

    const instances: typeof simInstances = [];
    for (let i = 0; i < simulationCount; i++) {
      try {
        const createRes = await fetch('/api/v1/simulations/simulations/', {
          method: 'POST',
          headers,
          body: JSON.stringify({
            simulation_type: 'judge',
            title: `Simulação de Sentença ${i + 1} - ${selectedComarca}/${selectedState}`,
            config: payload,
          }),
        });
        if (!createRes.ok) throw new Error(`HTTP ${createRes.status}`);
        const simData = await createRes.json();

        instances.push({
          id: i,
          simulationId: simData.id,
          status: 'running',
          sentenceContent: '',
          strategicReport: '',
          dispositivo: null,
          isVictory: false,
          judgeAnalysis: null,
        });
      } catch (error: any) {
        toast({ title: `Erro na simulação ${i + 1}`, description: error.message, variant: 'destructive' });
      }
    }

    setSimInstances(instances);
    setActiveSimTab(0);

    // Start all SSE connections simultaneously
    for (const inst of instances) {
      const controller = new AbortController();
      simAbortControllers.current[inst.id] = controller;
      (async () => {
        try {
          const response = await fetch(`/api/v1/simulations/simulations/${inst.simulationId}/judge/start/`, {
            method: 'POST',
            headers,
            body: JSON.stringify(payload),
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
                if (eventType === 'sentence' || eventType === 'sentence_chunk') {
                  setSimInstances((prev) => prev.map((s, i) => i === idx ? { ...s, sentenceContent: s.sentenceContent + (event.content || '') } : s));
                } else if (eventType === 'relatorio' || eventType === 'strategic_report') {
                  setSimInstances((prev) => prev.map((s, i) => i === idx ? {
                    ...s,
                    strategicReport: s.strategicReport + (event.content || ''),
                    ...(event.dispositivo ? { dispositivo: event.dispositivo, isVictory: !!event.is_victory } : {}),
                  } : s));
                } else if (eventType === 'judge_profile') {
                  setSimInstances((prev) => prev.map((s, i) => i === idx ? { ...s, judgeAnalysis: event.data } : s));
                } else if (eventType === 'complete') {
                  setSimInstances((prev) => prev.map((s, i) => i === idx ? { ...s, status: 'completed' } : s));
                } else if (eventType === 'error' || eventType === 'erro') {
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
  }, [selectedState, selectedTribunal, selectedComarca, selectedJudgeId, useGenericJudge, processType, caseValue, simulationCount, toast]);

  // ─── Handlers: Step 4 ───

  const [isExportingPdf, setIsExportingPdf] = useState(false);

  const exportDocument = useCallback(async (format: 'pdf' | 'docx') => {
    if (!sentenceContent && !strategicReport) {
      toast({ title: 'Nada para exportar', description: 'A sentença ainda não foi gerada.', variant: 'destructive' });
      return;
    }

    const title = `Simulação de Sentença - ${selectedComarca || 'Comarca'}/${selectedState || 'UF'}`;
    const dateStr = new Date().toLocaleDateString('pt-BR');

    const dispositivoLabel =
      dispositivo === 'procedente'
        ? 'PROCEDENTE'
        : dispositivo === 'improcedente'
        ? 'IMPROCEDENTE'
        : dispositivo === 'parcialmente_procedente'
        ? 'PARCIALMENTE PROCEDENTE'
        : '';

    // Convert markdown-style formatting to simple HTML for export
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

    if (format === 'pdf') {
      // Try backend PDF generation first (WeasyPrint), fall back to HTML blob download
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
            const fileName = `sentenca_simulada_${(selectedComarca || 'comarca').replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.pdf`;
            a.download = fileName;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            toast({ title: 'PDF exportado', description: `Arquivo "${fileName}" baixado com sucesso.` });
            setIsExportingPdf(false);
            return;
          }
          // Backend PDF failed, fall through to client-side generation
          console.warn('Backend PDF generation failed, falling back to client-side HTML.');
        } catch {
          console.warn('Backend PDF endpoint unavailable, falling back to client-side HTML.');
        }
        setIsExportingPdf(false);
      }

      // Fallback: generate styled HTML blob download (looks like a PDF when opened in browser)
      const htmlContent = `
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>${title}</title>
  <style>
    @page { size: A4; margin: 2.5cm 2cm 2.5cm 3cm; }
    @media print {
      body { margin: 0; padding: 0; }
      .no-print { display: none !important; }
    }
    body {
      font-family: 'Times New Roman', Times, serif;
      font-size: 12pt;
      line-height: 1.5;
      color: #000;
      max-width: 210mm;
      margin: 0 auto;
      padding: 2.5cm 2cm 2.5cm 3cm;
      text-align: justify;
    }
    h1 { font-size: 16pt; font-weight: bold; text-align: center; margin-top: 0; margin-bottom: 24pt; padding-bottom: 12pt; }
    h2 { font-size: 14pt; font-weight: bold; margin-top: 24pt; margin-bottom: 12pt; page-break-after: avoid; border-bottom: 1px solid #ccc; padding-bottom: 6pt; }
    h3 { font-size: 12pt; font-weight: bold; margin-top: 18pt; margin-bottom: 6pt; }
    p { margin-bottom: 12pt; text-indent: 2cm; }
    p:first-of-type { text-indent: 0; }
    .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 16px; margin-bottom: 24px; }
    .header h1 { font-size: 18pt; margin: 0 0 8px 0; padding-bottom: 0; border-bottom: none; }
    .header .subtitle { font-size: 11pt; color: #555; }
    .meta { display: flex; justify-content: space-between; font-size: 10pt; color: #666; margin-bottom: 24px; padding: 8px 0; border-bottom: 1px solid #ddd; }
    .dispositivo-badge { text-align: center; padding: 12px 24px; margin: 16px 0; font-size: 14pt; font-weight: bold; border: 2px solid #333; display: inline-block; }
    .section { margin-bottom: 24px; }
    .section-content { text-align: justify; }
    .footer { margin-top: 40px; padding-top: 16px; border-top: 1px solid #ccc; font-size: 9pt; color: #999; text-align: center; }
    ul, ol { margin-left: 1cm; margin-bottom: 12pt; }
    li { margin-bottom: 6pt; }
    table { width: 100%; border-collapse: collapse; margin: 12pt 0; font-size: 10pt; }
    th { background-color: #d3d3d3; padding: 8pt; text-align: left; font-weight: bold; border: 1px solid #000; }
    td { border: 1px solid #000; padding: 8pt; }
    blockquote { margin: 12pt 0; padding: 12pt; background-color: #f7fafc; border-left: 4px solid #333; font-style: italic; }
    strong { font-weight: bold; }
    em { font-style: italic; }
  </style>
</head>
<body>
  <div class="header">
    <h1>SENTENCA SIMULADA</h1>
    <div class="subtitle">${title}</div>
  </div>
  <div class="meta">
    <span>Data: ${dateStr}</span>
    <span>Tipo: ${processType || 'N/A'}</span>
    ${caseValue ? `<span>Valor: ${caseValue}</span>` : ''}
  </div>
  ${dispositivoLabel ? `<div style="text-align:center; margin: 20px 0;"><span class="dispositivo-badge">${dispositivoLabel}</span></div>` : ''}
  ${confidence ? `<div class="section"><h2>Grau de Confiança</h2><p style="text-indent:0">${confidence}%</p></div>` : ''}
  ${sentenceContent ? `<div class="section"><h2>Texto da Sentença</h2><div class="section-content">${markdownToHtml(sentenceContent)}</div></div>` : ''}
  ${fundamentacao ? `<div class="section"><h2>Fundamentação</h2><div class="section-content">${markdownToHtml(fundamentacao)}</div></div>` : ''}
  ${strategicReport ? `<div class="section"><h2>Relatório Estratégico</h2><div class="section-content">${markdownToHtml(strategicReport)}</div></div>` : ''}
  <div class="footer">
    <p>Documento gerado automaticamente pelo Verus.AI - Simulação de Sentença</p>
    <p>Este documento é uma simulação e não possui valor jurídico.</p>
  </div>
</body>
</html>`;

      const blob = new Blob([htmlContent], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const fileName = `sentenca_simulada_${(selectedComarca || 'comarca').replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.pdf`;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast({ title: 'PDF exportado', description: `Arquivo "${fileName}" baixado com sucesso.` });
    } else {
      // DOCX export: use HTML blob with Word-compatible MIME type
      const docContent = `
<html xmlns:o="urn:schemas-microsoft-com:office:office"
      xmlns:w="urn:schemas-microsoft-com:office:word"
      xmlns="http://www.w3.org/TR/REC-html40">
<head>
  <meta charset="UTF-8">
  <meta name="ProgId" content="Word.Document">
  <meta name="Generator" content="Verus.AI">
  <!--[if gte mso 9]>
  <xml>
    <w:WordDocument>
      <w:View>Print</w:View>
    </w:WordDocument>
  </xml>
  <![endif]-->
  <style>
    body {
      font-family: 'Times New Roman', Times, serif;
      font-size: 13pt;
      line-height: 1.6;
      color: #1a1a1a;
    }
    .header {
      text-align: center;
      border-bottom: 2pt solid #333;
      padding-bottom: 12pt;
      margin-bottom: 18pt;
    }
    .header h1 { font-size: 18pt; margin: 0 0 6pt 0; }
    .header .subtitle { font-size: 11pt; color: #555; }
    .section { margin-bottom: 18pt; }
    .section h2 {
      font-size: 14pt;
      border-bottom: 1pt solid #ccc;
      padding-bottom: 4pt;
      margin-bottom: 8pt;
    }
    .dispositivo-badge {
      text-align: center;
      padding: 8pt 18pt;
      font-size: 14pt;
      font-weight: bold;
      border: 2pt solid #333;
    }
    .footer {
      margin-top: 36pt;
      padding-top: 12pt;
      border-top: 1pt solid #ccc;
      font-size: 9pt;
      color: #999;
      text-align: center;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>SENTENÇA SIMULADA</h1>
    <div class="subtitle">${title}</div>
  </div>

  <p><strong>Data:</strong> ${dateStr} | <strong>Tipo:</strong> ${processType || 'N/A'}${caseValue ? ` | <strong>Valor:</strong> ${caseValue}` : ''}</p>

  ${dispositivoLabel ? `<p style="text-align:center;"><span class="dispositivo-badge">${dispositivoLabel}</span></p>` : ''}

  ${confidence ? `<div class="section"><h2>Grau de Confiança</h2><p>${confidence}%</p></div>` : ''}

  ${sentenceContent ? `<div class="section"><h2>Texto da Sentença</h2><div>${markdownToHtml(sentenceContent)}</div></div>` : ''}

  ${fundamentacao ? `<div class="section"><h2>Fundamentação</h2><div>${markdownToHtml(fundamentacao)}</div></div>` : ''}

  ${strategicReport ? `<div class="section"><h2>Relatório Estratégico</h2><div>${markdownToHtml(strategicReport)}</div></div>` : ''}

  <div class="footer">
    <p>Documento gerado automaticamente pelo Verus.AI - Simulação de Sentença</p>
    <p>Este documento é uma simulação e não possui valor jurídico.</p>
  </div>
</body>
</html>`;

      const blob = new Blob(['\ufeff' + docContent], { type: 'application/msword' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const fileName = `sentenca_simulada_${(selectedComarca || 'comarca').replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.doc`;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast({ title: 'DOCX exportado', description: `Arquivo "${fileName}" baixado com sucesso.` });
    }
  }, [toast, sentenceContent, strategicReport, fundamentacao, dispositivo, confidence, selectedComarca, selectedState, processType, caseValue, simulationId]);

  const resetSimulation = useCallback(() => {
    setSimulationCount(1);
    setCurrentStep(0);
    setSelectedState('');
    setSelectedTribunal('');
    setSelectedComarca('');
    setSelectedJudgeId('');
    setUseGenericJudge(false);
    setUploadedFiles([]);
    setProcessType('');
    setCaseValue('');
    setAnalysisProgress(0);
    setJudgeAnalysis(null);
    setSentenceContent('');
    setCompletedPhases([]);
    setCurrentPhase(null);
    setCurrentPhaseDescription('');
    setDispositivo(null);
    setFundamentacao('');
    setConfidence(0);
    setStrategicReport('');
    setIsVictory(false);
    setQuestionText('');
    setQuestionAnswer('');
    setSimulationId(null);
    setCheckedItems({});
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

  const toggleCheckItem = useCallback((index: number) => {
    setCheckedItems((prev) => ({ ...prev, [index]: !prev[index] }));
  }, []);

  // ─── Navigation ───

  const canAdvance = () => {
    if (currentStep === 0) return selectedState !== '' && (selectedJudgeId !== '' || useGenericJudge);
    if (currentStep === 1) return processType !== '';
    return true;
  };

  const nextStep = () => {
    if (currentStep < STEPS.length - 1) {
      if (currentStep === 1) {
        // Go to step 2 (analysis) and auto-start
        if (simulationCount > 1) {
          setTimeout(() => startAllAnalyses(), 300);
        } else {
          setCurrentStep(2);
          setTimeout(() => startAnalysis(), 300);
        }
      } else {
        setCurrentStep((s) => s + 1);
      }
    }
  };
  const prevStep = () => {
    if (currentStep > 0) setCurrentStep((s) => s - 1);
  };

  // ─── Render Stepper ───

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

  // ─── Render Steps ───

  const renderStep0 = () => (
    <div className="max-w-3xl mx-auto space-y-4 sm:space-y-6">
      <div>
        <h2 className="text-xl sm:text-2xl font-bold mb-1">Seleção do Juiz</h2>
        <p className="text-muted-foreground">Selecione o juiz que deseja simular.</p>
      </div>

      {/* Aviso sobre qualidade dos dados */}
      <div className="flex gap-3 p-4 rounded-lg border border-amber-200 bg-amber-50/50 dark:border-amber-900 dark:bg-amber-950/20">
        <AlertCircle className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" />
        <div className="text-sm">
          <p className="font-medium text-amber-800 dark:text-amber-200">
            A precisão da simulação depende da qualidade dos dados
          </p>
          <p className="text-amber-700 dark:text-amber-300 mt-1">
            Forneça o máximo de detalhes possível: petição inicial completa, contestação, provas documentais,
            laudos e depoimentos. Quanto mais contexto, mais realista será a sentença simulada e mais próxima
            do estilo de decisão do juiz selecionado.
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {/* Importar de caso existente */}
        <Card className="border-dashed border-2 border-muted-foreground/20">
          <CardContent className="py-4">
            <div className="flex items-center gap-3 mb-3">
              <Briefcase className="h-5 w-5 text-primary" />
              <div>
                <h3 className="text-sm font-semibold">Importar de Caso Existente</h3>
                <p className="text-xs text-muted-foreground">Selecione um caso para preencher automaticamente</p>
              </div>
            </div>

            <Select value={selectedCaseId} onValueChange={handleSelectCase}>
              <SelectTrigger>
                <SelectValue placeholder="Selecione um caso ou digite manualmente abaixo" />
              </SelectTrigger>
              <SelectContent>
                {userCases?.map((c: any) => (
                  <SelectItem key={c.id} value={c.id}>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{c.titulo}</span>
                      {c.numero_processo && <span className="text-xs text-muted-foreground">({c.numero_processo})</span>}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Separator className="my-3" />
            <p className="text-xs text-muted-foreground text-center">ou preencha manualmente abaixo</p>
          </CardContent>
        </Card>

        <div className="space-y-2">
          <Label>Estado *</Label>
          <Select value={selectedState} onValueChange={handleStateChange}>
            <SelectTrigger>
              <SelectValue placeholder="Selecione o estado" />
            </SelectTrigger>
            <SelectContent>
              {BRAZILIAN_STATES.map((uf) => (
                <SelectItem key={uf} value={uf}>{uf}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Tribunal</Label>
          <Select
            value={selectedTribunal}
            onValueChange={handleTribunalChange}
            disabled={!selectedState}
          >
            <SelectTrigger>
              <SelectValue placeholder={selectedState ? 'Selecione o tribunal' : 'Selecione o estado primeiro'} />
            </SelectTrigger>
            <SelectContent>
              {tribunais.map((t) => (
                <SelectItem key={t} value={t}>{t}</SelectItem>
              ))}
              {tribunais.length === 0 && selectedState && (
                <SelectItem value="__generic" disabled>
                  Nenhum tribunal encontrado
                </SelectItem>
              )}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Comarca</Label>
          <Select
            value={selectedComarca}
            onValueChange={handleComarcaChange}
            disabled={!selectedTribunal}
          >
            <SelectTrigger>
              <SelectValue placeholder={selectedTribunal ? 'Selecione a comarca' : 'Selecione o tribunal primeiro'} />
            </SelectTrigger>
            <SelectContent>
              {comarcas.map((c) => (
                <SelectItem key={c} value={c}>{c}</SelectItem>
              ))}
              {comarcas.length === 0 && selectedTribunal && (
                <SelectItem value="__generic" disabled>
                  Nenhuma comarca encontrada
                </SelectItem>
              )}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Juiz</Label>
          <Select
            value={selectedJudgeId}
            onValueChange={setSelectedJudgeId}
            disabled={useGenericJudge || !selectedComarca}
          >
            <SelectTrigger>
              <SelectValue placeholder="Selecione o juiz" />
            </SelectTrigger>
            <SelectContent>
              {judges?.map((j) => (
                <SelectItem key={j.id} value={j.id}>{j.name}</SelectItem>
              )) || []}
              {(!judges || judges.length === 0) && (
                <SelectItem value="__none" disabled>
                  Nenhum juiz encontrado
                </SelectItem>
              )}
            </SelectContent>
          </Select>
        </div>

        <Card className="bg-muted/30">
          <CardContent className="flex items-center gap-3 p-4">
            <input
              type="checkbox"
              id="generic-judge"
              checked={useGenericJudge}
              onChange={(e) => {
                setUseGenericJudge(e.target.checked);
                if (e.target.checked) setSelectedJudgeId('');
              }}
              className="h-4 w-4 rounded border-gray-300"
            />
            <Label htmlFor="generic-judge" className="text-sm font-normal cursor-pointer">
              Usar juiz genérico da comarca (perfil baseado em padrões gerais)
            </Label>
          </CardContent>
        </Card>

      </div>
    </div>
  );

  const renderStep1 = () => (
    <div className="max-w-3xl mx-auto space-y-4 sm:space-y-6">
      <div>
        <h2 className="text-xl sm:text-2xl font-bold mb-1">Documentos do Processo</h2>
        <p className="text-muted-foreground">Envie os documentos relevantes para análise.</p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label>Tipo de Processo *</Label>
          <Select value={processType} onValueChange={setProcessType}>
            <SelectTrigger>
              <SelectValue placeholder="Selecione o tipo de processo" />
            </SelectTrigger>
            <SelectContent>
              {PROCESS_TYPES.map((pt) => (
                <SelectItem key={pt} value={pt}>{pt}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Valor da Causa (se aplicável)</Label>
          <Input
            value={caseValue}
            onChange={(e) => setCaseValue(e.target.value)}
            placeholder="R$ 0,00"
          />
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

        <div className="space-y-2">
          <Label>Documentos</Label>
          <p className="text-xs text-muted-foreground">
            Petição inicial, contestação, provas, etc. (PDF, DOCX, TXT)
          </p>
          <div
            className="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer hover:border-primary/50 transition-colors"
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
            <p className="text-sm text-muted-foreground">Clique para enviar documentos</p>
            <p className="text-xs text-muted-foreground mt-1">PDF, DOCX, TXT, ODT</p>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx,.txt,.odt"
              className="hidden"
              onChange={handleFileUpload}
            />
          </div>
          {uploadedFiles.length > 0 && (
            <div className="space-y-2 mt-3">
              {uploadedFiles.map((f, i) => (
                <div key={i} className="flex items-center justify-between bg-muted rounded-lg px-3 py-2">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm truncate">{f.name}</span>
                    <span className="text-xs text-muted-foreground">
                      ({(f.size / 1024).toFixed(1)} KB)
                    </span>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => removeFile(i)}>
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const selectedJudgeName = judges?.find((j) => j.id === selectedJudgeId)?.name || null;

  const renderStep2 = () => {
    const completedCount = completedPhases.length;

    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h2 className="text-2xl font-bold mb-1">Análise em Andamento</h2>
          <p className="text-muted-foreground">{analysisStage || 'Preparando análise...'}</p>
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

        {/* Who is working indicator with gavel animation */}
        {isAnalyzing && analysisStage && (
          <div className="flex items-center gap-3 py-3 px-4 bg-muted/50 rounded-lg speaker-active border-2">
            <div className="h-10 w-10 rounded-full bg-amber-500 flex items-center justify-center">
              <Scale className="h-5 w-5 text-white gavel-thinking" />
            </div>
            <div className="flex-1">
              <span className="text-sm font-medium">Juiz {selectedJudgeName || 'Titular'}</span>
              <p className="text-xs text-muted-foreground">{currentPhaseDescription || analysisStage}</p>
            </div>
            <div className="flex gap-1 ml-auto">
              <div className="h-2 w-2 rounded-full bg-primary thinking-dot" />
              <div className="h-2 w-2 rounded-full bg-primary thinking-dot" />
              <div className="h-2 w-2 rounded-full bg-primary thinking-dot" />
            </div>
          </div>
        )}

        {/* Overall progress bar */}
        <Card>
          <CardContent className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Progresso Geral</span>
              <span className="text-sm text-muted-foreground">
                Fase {Math.min(completedCount + 1, JUDGE_ANALYSIS_PHASES.length)} de {JUDGE_ANALYSIS_PHASES.length}
              </span>
            </div>
            <Progress value={analysisProgress} />
          </CardContent>
        </Card>

        {/* Phase-by-phase panel */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Etapas da Análise</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            {JUDGE_ANALYSIS_PHASES.map((phase, index) => {
              const PhaseIcon = phase.icon;
              const isCompleted = completedPhases.includes(phase.key);
              const isCurrent = currentPhase === phase.key;
              const isPending = !isCompleted && !isCurrent;

              return (
                <div
                  key={phase.key}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-300 ${
                    isCurrent
                      ? 'bg-primary/5 border-2 border-primary/30 speaker-active phase-step-enter'
                      : isCompleted
                      ? 'bg-green-50 dark:bg-green-950/10 minister-voted'
                      : 'opacity-50'
                  }`}
                >
                  {/* Status icon */}
                  <div
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                      isCompleted
                        ? 'bg-green-100 dark:bg-green-900'
                        : isCurrent
                        ? 'bg-primary/10'
                        : 'bg-muted'
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

                  {/* Phase info */}
                  <div className="flex-1 min-w-0">
                    <p
                      className={`text-sm font-medium ${
                        isCompleted
                          ? 'text-green-700 dark:text-green-400'
                          : isCurrent
                          ? 'text-foreground'
                          : 'text-muted-foreground'
                      }`}
                    >
                      {phase.label}
                    </p>
                    {(isCurrent || isCompleted) && (
                      <p className="text-xs text-muted-foreground truncate">
                        {phase.description}
                      </p>
                    )}
                  </div>

                  {/* Status badge */}
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

        {/* Perfil do Juiz */}
        {judgeAnalysis && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-amber-500/10">
                  <User className="h-6 w-6 text-amber-600" />
                </div>
                <div>
                  <CardTitle>Perfil do Juiz</CardTitle>
                  <CardDescription>{judgeAnalysis.profile.name}</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-4">
                <div className="text-center p-3 bg-muted rounded-lg">
                  <p className="text-2xl font-bold">{judgeAnalysis.profile.total_decisions}</p>
                  <p className="text-xs text-muted-foreground">Decisões</p>
                </div>
                <div className="text-center p-3 bg-muted rounded-lg">
                  <p className="text-2xl font-bold">{judgeAnalysis.profile.approval_rate}%</p>
                  <p className="text-xs text-muted-foreground">Taxa de Procedência</p>
                </div>
                <div className="text-center p-3 bg-muted rounded-lg">
                  <p className="text-2xl font-bold">{judgeAnalysis.profile.avg_sentence_length}</p>
                  <p className="text-xs text-muted-foreground">Extensão Média</p>
                </div>
                <div className="text-center p-3 bg-muted rounded-lg">
                  <p className="text-2xl font-bold">{judgeAnalysis.confidence}%</p>
                  <p className="text-xs text-muted-foreground">Confiança</p>
                </div>
              </div>

              <div>
                <Label className="text-sm font-semibold">Tendências Identificadas</Label>
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {judgeAnalysis.profile.tendencies.map((t, i) => (
                    <Badge key={i} variant="outline">{t}</Badge>
                  ))}
                </div>
              </div>

              <div>
                <Label className="text-sm font-semibold">Fundamentações Comuns</Label>
                <ul className="mt-2 space-y-1">
                  {judgeAnalysis.profile.common_fundamentations.map((f, i) => (
                    <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                      <TrendingUp className="h-4 w-4 mt-0.5 shrink-0 text-primary" />
                      {f}
                    </li>
                  ))}
                </ul>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Sentença em streaming */}
        {sentenceContent && (
          <Card className="mt-4">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <FileText className="h-4 w-4" />
                {isAnalyzing ? 'Sentença (em elaboração...)' : 'Sentença'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[300px]">
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  {isAnalyzing ? (
                    /* During streaming: plain text — no markdown parsing overhead */
                    <p className="whitespace-pre-wrap">{sentenceContent}</p>
                  ) : (
                    /* After streaming: full markdown render */
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {sentenceContent}
                    </ReactMarkdown>
                  )}
                </div>
              </ScrollArea>
              {isAnalyzing && (
                <div className="flex items-center gap-1 mt-2 text-xs text-muted-foreground">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  Redigindo...
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  const renderStep3 = () => {
    const victoryColor = isVictory ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400';
    const victoryBg = isVictory ? 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-900' : 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900';
    const victoryBadgeBg = isVictory ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';

    // Extract checklist items from strategic report
    const checklistItems: string[] = [];
    if (strategicReport) {
      const lines = strategicReport.split('\n');
      for (const line of lines) {
        const match = line.match(/\[[ x]\]\s*(.+)/i);
        if (match) checklistItems.push(match[1].trim());
      }
    }

    return (
      <div className="max-w-4xl mx-auto space-y-4 sm:space-y-6">
        {loadedFromHistory && (
          <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-50 border border-blue-200 dark:bg-blue-950/20 dark:border-blue-900">
            <History className="h-4 w-4 text-blue-600 dark:text-blue-400" />
            <span className="text-sm text-blue-700 dark:text-blue-300">Carregado do histórico</span>
          </div>
        )}
        <div className="text-center">
          <h2 className="text-2xl sm:text-3xl font-bold mb-2">Sentença Simulada</h2>
          {dispositivo && (
            <Badge
              variant={
                dispositivo === 'procedente'
                  ? 'default'
                  : dispositivo === 'improcedente'
                  ? 'destructive'
                  : 'secondary'
              }
              className="text-base sm:text-lg px-4 py-1.5"
            >
              {dispositivo === 'procedente'
                ? 'PROCEDENTE'
                : dispositivo === 'improcedente'
                ? 'IMPROCEDENTE'
                : 'PARCIALMENTE PROCEDENTE'}
            </Badge>
          )}
        </div>

        {/* Metricas */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
          <Card className="vote-reveal">
            <CardContent className="text-center p-4">
              <p className="text-3xl font-bold text-primary">{confidence}%</p>
              <div className="w-full h-2 bg-muted rounded-full mt-2 overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full confidence-fill"
                  style={{ width: `${confidence}%` }}
                />
              </div>
              <p className="text-xs text-muted-foreground mt-1">Grau de Confiança</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="text-center p-4">
              <p className="text-3xl font-bold">
                {dispositivo === 'procedente'
                  ? 'Sim'
                  : dispositivo === 'improcedente'
                  ? 'Nao'
                  : 'Parcial'}
              </p>
              <p className="text-xs text-muted-foreground">Dispositivo</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="text-center p-4">
              <p className="text-3xl font-bold">{processType}</p>
              <p className="text-xs text-muted-foreground">Tipo</p>
            </CardContent>
          </Card>
        </div>

        {/* Sentença completa */}
        <Card>
          <CardHeader>
            <CardTitle>Texto da Sentença</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[500px]">
              <div className="prose prose-sm max-w-none dark:prose-invert">
                {sentenceContent ? (
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {sentenceContent}
                  </ReactMarkdown>
                ) : (
                  'Sentença não disponível.'
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Fundamentação */}
        {fundamentacao && (
          <Card>
            <CardHeader>
              <CardTitle>Fundamentação</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm max-w-none dark:prose-invert">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {fundamentacao}
                </ReactMarkdown>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Strategic Report */}
        {strategicReport && (
          <Card className={`border-2 ${victoryBg}`}>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${isVictory ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
                  <Shield className={`h-6 w-6 ${victoryColor}`} />
                </div>
                <div className="flex-1">
                  <CardTitle className={victoryColor}>
                    Relatório Estratégico
                  </CardTitle>
                  <CardDescription>
                    Análise completa da sentença com recomendações práticas
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  {isVictory ? (
                    <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 border-0">
                      Vitória
                    </Badge>
                  ) : (
                    <Badge className="bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 border-0">
                      Derrota
                    </Badge>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px]">
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  {isAnalyzing ? (
                    <p className="whitespace-pre-wrap">{strategicReport}</p>
                  ) : (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {strategicReport}
                    </ReactMarkdown>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        )}

        {/* Interactive Checklist */}
        {checklistItems.length > 0 && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <CheckSquare className="h-5 w-5 text-primary" />
                <CardTitle className="text-base">Checklist de Providências Imediatas</CardTitle>
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
                    <div
                      key={idx}
                      className={`rounded-lg transition-colors ${
                        isChecked
                          ? 'bg-green-50 dark:bg-green-950/20'
                          : 'bg-muted/50 hover:bg-muted'
                      }`}
                    >
                      <button
                        onClick={() => toggleCheckItem(idx)}
                        className="flex items-center gap-3 w-full text-left px-3 py-3 sm:py-2 min-h-[44px]"
                      >
                        {isChecked ? (
                          <CheckSquare className="h-4 w-4 text-green-600 shrink-0" />
                        ) : (
                          <Square className="h-4 w-4 text-muted-foreground shrink-0" />
                        )}
                        <span className={`text-sm flex-1 ${isChecked ? 'line-through text-muted-foreground' : ''}`}>
                          {cleanItem}
                        </span>
                        {isChecked ? (
                          <Badge variant="outline" className="text-xs shrink-0 text-green-600 border-green-200 dark:text-green-400 dark:border-green-800">
                            Concluído
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-xs shrink-0">
                            Pendente
                          </Badge>
                        )}
                      </button>
                      {/* Action buttons for unchecked items */}
                      {!isChecked && (
                        <div className="flex flex-wrap gap-1.5 px-3 pb-3 pt-0">
                          <Link
                            href={`/dashboard/copilot?prompt=${encodeURIComponent(
                              `Crie uma tarefa jurídica para: "${cleanItem}". Inclua título, descrição detalhada, prazo sugerido e prioridade.`
                            )}`}
                          >
                            <Button variant="outline" size="sm" className="h-7 text-xs gap-1">
                              <ListTodo className="h-3 w-3" />
                              Criar Tarefa
                            </Button>
                          </Link>
                          <Link href="/dashboard/copilot?prompt=Preciso+gerar+um+documento+jurídico">
                            <Button variant="outline" size="sm" className="h-7 text-xs gap-1">
                              <FileEdit className="h-3 w-3" />
                              Gerar Documento
                            </Button>
                          </Link>
                          <Link
                            href={`/dashboard/copilot?prompt=${encodeURIComponent(
                              `Analise esta providência da simulação de sentença e me oriente sobre como proceder: "${cleanItem}"`
                            )}`}
                          >
                            <Button variant="outline" size="sm" className="h-7 text-xs gap-1">
                              <Bot className="h-3 w-3" />
                              Consultar Copilot
                            </Button>
                          </Link>
                          {selectedCaseId && (
                            <Link
                              href={`/dashboard/processos/${selectedCaseId}`}
                            >
                              <Button variant="outline" size="sm" className="h-7 text-xs gap-1">
                                <Link2 className="h-3 w-3" />
                                Vincular ao Caso
                              </Button>
                            </Link>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Question the Decision */}
        {(simulationId || sentenceContent) && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <MessageSquare className="h-5 w-5 text-primary" />
                <div>
                  <CardTitle className="text-base">Questionar a Decisão</CardTitle>
                  <CardDescription>
                    Pergunte sobre a sentença e receba análises detalhadas
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Quick questions - horizontal scroll on mobile */}
              <div className="chips-scroll sm:flex-wrap sm:overflow-visible">
                {[
                  'O que eu poderia ter feito diferente?',
                  'Quais argumentos fortaleceriam minha posição?',
                  'Qual a chance de reverter em recurso?',
                ].map((q, i) => (
                  <Button
                    key={i}
                    variant="outline"
                    size="sm"
                    onClick={() => setQuestionText(q)}
                    className="text-xs whitespace-nowrap shrink-0"
                  >
                    {q}
                  </Button>
                ))}
              </div>

              <div className="flex gap-2">
                <Textarea
                  value={questionText}
                  onChange={(e) => setQuestionText(e.target.value)}
                  placeholder="Ex: Quais argumentos fortaleceriam minha posição?"
                  className="flex-1 min-h-[80px]"
                />
                <Button
                  onClick={handleQuestion}
                  disabled={isQuestioning || !questionText.trim() || !simulationId}
                  className="self-end"
                >
                  {isQuestioning ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>

              {/* Answer */}
              {questionAnswer && (
                <div className="mt-4 p-4 rounded-lg bg-muted/50 border">
                  <div className="flex items-center gap-2 mb-3">
                    <Scale className="h-4 w-4 text-primary" />
                    <span className="text-sm font-semibold">Resposta do Consultor</span>
                  </div>
                  <div className="prose prose-sm max-w-none dark:prose-invert">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {questionAnswer}
                    </ReactMarkdown>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3">
          <Button onClick={() => exportDocument('pdf')} className="flex-1" disabled={isExportingPdf}>
            {isExportingPdf ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <FileDown className="h-4 w-4 mr-2" />
            )}
            {isExportingPdf ? 'Gerando PDF...' : 'Exportar PDF'}
          </Button>
          <Button variant="outline" onClick={() => exportDocument('docx')} className="flex-1">
            <FileDown className="h-4 w-4 mr-2" />
            Exportar DOCX
          </Button>
          <Button variant="outline" onClick={resetSimulation}>
            <RotateCcw className="h-4 w-4 mr-2" />
            Nova Simulação
          </Button>
        </div>
      </div>
    );
  };

  // ─── Main Render ───

  return (
    <div className="min-h-screen flex flex-col -mx-3 sm:-mx-6 -mb-6">
      {renderStepper()}

      <div className="flex-1 p-3 sm:p-6">
        {currentStep === 0 && renderStep0()}
        {currentStep === 1 && renderStep1()}
        {currentStep === 2 && renderStep2()}
        {currentStep === 3 && renderStep3()}
        <SimulationHistoryList type="judge" />
      </div>

      {/* Navigation buttons */}
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
            {currentStep === 1 ? 'Iniciar Análise' : 'Próximo'}
            <ChevronRight className="h-4 w-4 ml-2" />
          </Button>
        </div>
      )}
    </div>
  );
}
