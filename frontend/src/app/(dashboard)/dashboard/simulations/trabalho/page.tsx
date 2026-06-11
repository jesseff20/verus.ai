'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useToast } from '@/hooks/use-toast';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Scale, ChevronLeft, ChevronRight, Loader2, CheckCircle2,
  FileDown, RotateCcw, FileText, AlertCircle, Send, MessageSquare,
  Plus, X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import SimulationCountSelector from '@/components/simulations/SimulationCountSelector';
import SimulationTabBar from '@/components/simulations/SimulationTabBar';
import { useMultiSimulation } from '@/hooks/use-multi-simulation';

const STEPS = [
  { title: 'Configuração', icon: Scale },
  { title: 'Simulação', icon: FileText },
  { title: 'Resultado', icon: CheckCircle2 },
];

const CLAIMS_SUGGESTIONS = [
  'Verbas rescisorias (saldo de salario, aviso previo, 13o, ferias + 1/3)',
  'Horas extras e reflexos',
  'FGTS + multa de 40%',
  'Adicional de insalubridade',
  'Adicional de periculosidade',
  'Dano moral trabalhista',
  'Adicional noturno',
  'Desvio/acumulo de funcao',
  'Intervalo intrajornada',
  'Reconhecimento de vinculo empregaticio',
];

export default function TrabalhoSimulationPage() {
  const router = useRouter();
  const { toast } = useToast();
  const multiSim = useMultiSimulation();
  const [currentStep, setCurrentStep] = useState(0);

  // Config
  const [caseDescription, setCaseDescription] = useState('');
  const [caseValue, setCaseValue] = useState('');
  const [claims, setClaims] = useState<string[]>([]);
  const [newClaim, setNewClaim] = useState('');

  // Simulation
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationId, setSimulationId] = useState<string | null>(null);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [analysisStage, setAnalysisStage] = useState('');

  // Streaming content
  const [conciliacaoText, setConciliacaoText] = useState('');
  const [instrucaoText, setInstruçãoText] = useState('');
  const [razoesText, setRazoesText] = useState('');
  const [sentencaText, setSentencaText] = useState('');
  const [strategicReport, setStrategicReport] = useState('');
  const [dispositivo, setDispositivo] = useState('');

  // Batching
  const pendingConciliacaoRef = useRef('');
  const pendingInstruçãoRef = useRef('');
  const pendingRazoesRef = useRef('');
  const pendingSentencaRef = useRef('');
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
        if (pendingConciliacaoRef.current) {
          const t = pendingConciliacaoRef.current; pendingConciliacaoRef.current = '';
          setConciliacaoText((p) => p + t);
        }
        if (pendingInstruçãoRef.current) {
          const t = pendingInstruçãoRef.current; pendingInstruçãoRef.current = '';
          setInstruçãoText((p) => p + t);
        }
        if (pendingRazoesRef.current) {
          const t = pendingRazoesRef.current; pendingRazoesRef.current = '';
          setRazoesText((p) => p + t);
        }
        if (pendingSentencaRef.current) {
          const t = pendingSentencaRef.current; pendingSentencaRef.current = '';
          setSentencaText((p) => p + t);
        }
        if (pendingReportRef.current) {
          const t = pendingReportRef.current; pendingReportRef.current = '';
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
    if (pendingConciliacaoRef.current) { const t = pendingConciliacaoRef.current; pendingConciliacaoRef.current = ''; setConciliacaoText((p) => p + t); }
    if (pendingInstruçãoRef.current) { const t = pendingInstruçãoRef.current; pendingInstruçãoRef.current = ''; setInstruçãoText((p) => p + t); }
    if (pendingRazoesRef.current) { const t = pendingRazoesRef.current; pendingRazoesRef.current = ''; setRazoesText((p) => p + t); }
    if (pendingSentencaRef.current) { const t = pendingSentencaRef.current; pendingSentencaRef.current = ''; setSentencaText((p) => p + t); }
    if (pendingReportRef.current) { const t = pendingReportRef.current; pendingReportRef.current = ''; setStrategicReport((p) => p + t); }
  }, []);

  // Question
  const [questionText, setQuestionText] = useState('');
  const [questionAnswer, setQuestionAnswer] = useState('');
  const [isQuestioning, setIsQuestioning] = useState(false);
  const [isExportingPdf, setIsExportingPdf] = useState(false);

  const addClaim = useCallback(() => {
    if (newClaim.trim() && !claims.includes(newClaim.trim())) {
      setClaims(prev => [...prev, newClaim.trim()]);
      setNewClaim('');
    }
  }, [newClaim, claims]);

  const removeClaim = useCallback((idx: number) => {
    setClaims(prev => prev.filter((_, i) => i !== idx));
  }, []);

  const startSimulation = useCallback(async () => {
    setIsSimulating(true);
    setAnalysisProgress(0);
    setAnalysisStage('Iniciando simulação...');
    setConciliacaoText(''); setInstruçãoText(''); setRazoesText('');
    setSentencaText(''); setStrategicReport(''); setDispositivo('');

    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      const headers = {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      };

      const createRes = await fetch('/api/v1/simulations/simulations/', {
        method: 'POST', headers,
        body: JSON.stringify({
          simulation_type: 'trabalho',
          title: `Vara do Trabalho - ${new Date().toLocaleDateString('pt-BR')}`,
          config: {
            case_description: caseDescription,
            case_value: caseValue,
            claims,
          },
        }),
      });
      if (!createRes.ok) throw new Error(`HTTP ${createRes.status}`);
      const simData = await createRes.json();
      const simId = simData.id;
      setSimulationId(simId);

      const response = await fetch(`/api/v1/simulations/simulations/${simId}/trabalho/start/`, {
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
            } else if (eventType === 'conciliacao') {
              pendingConciliacaoRef.current += (event.content || '');
              scheduleStreamFlush();
            } else if (eventType === 'instrucao') {
              pendingInstruçãoRef.current += (event.content || '');
              scheduleStreamFlush();
            } else if (eventType === 'razoes_finais') {
              pendingRazoesRef.current += (event.content || '');
              scheduleStreamFlush();
            } else if (eventType === 'sentence') {
              pendingSentencaRef.current += (event.content || '');
              scheduleStreamFlush();
            } else if (eventType === 'relatorio_estrategico') {
              pendingReportRef.current += (event.content || '');
              scheduleStreamFlush();
              if (event.dispositivo) setDispositivo(event.dispositivo);
            } else if (eventType === 'complete') {
              flushStreamBuffers();
              setAnalysisProgress(100);
              setCurrentStep(2);
              toast({ title: 'Simulação concluida', description: 'Sentenca da Vara do Trabalho simulada com sucesso.' });
            } else if (eventType === 'error') {
              toast({ title: 'Erro', description: event.content || 'Erro desconhecido.', variant: 'destructive' });
              setIsSimulating(false);
            }
          } catch { /* ignore parse errors */ }
        }
      }
    } catch (error: any) {
      toast({ title: 'Erro', description: error.message || 'Falha ao conectar.', variant: 'destructive' });
    } finally {
      setIsSimulating(false);
    }
  }, [caseDescription, caseValue, claims, toast, scheduleStreamFlush, flushStreamBuffers]);

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
    if (!sentencaText && !strategicReport) {
      toast({ title: 'Nada para exportar', description: 'A sentença ainda não foi gerada.', variant: 'destructive' });
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
          a.download = `simulação_trabalho_${new Date().toISOString().split('T')[0]}.pdf`;
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
    const htmlContent = `<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><title>Simulação Vara do Trabalho</title><style>body{font-family:'Times New Roman',serif;font-size:12pt;line-height:1.5;max-width:210mm;margin:0 auto;padding:2.5cm 2cm;text-align:justify;}h1{text-align:center;font-size:16pt;}h2{font-size:14pt;border-bottom:1px solid #ccc;padding-bottom:6pt;}.footer{margin-top:40px;border-top:1px solid #ccc;padding-top:12px;font-size:9pt;color:#999;text-align:center;}</style></head><body><h1>SENTENÇA TRABALHISTA</h1><p><strong>Data:</strong> ${new Date().toLocaleDateString('pt-BR')}</p>${sentencaText ? `<h2>Sentença</h2><div>${sentencaText.replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br/>')}</div>` : ''}${strategicReport ? `<h2>Relatório Estratégico</h2><div>${strategicReport.replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br/>')}</div>` : ''}<div class="footer"><p>Documento gerado pelo Verus.AI. Este documento não possui valor jurídico.</p></div></body></html>`;
    const blob = new Blob([htmlContent], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `simulação_trabalho_${new Date().toISOString().split('T')[0]}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast({ title: 'PDF exportado', description: 'Arquivo baixado com sucesso.' });
    setIsExportingPdf(false);
  }, [sentencaText, strategicReport, simulationId, toast]);

  const resetSimulation = useCallback(() => {
    multiSim.setSimulationCount(1);
    setCurrentStep(0); setCaseDescription(''); setCaseValue(''); setClaims([]);
    setSimulationId(null); setAnalysisProgress(0); setAnalysisStage('');
    setConciliacaoText(''); setInstruçãoText(''); setRazoesText('');
    setSentencaText(''); setStrategicReport(''); setDispositivo('');
    setQuestionText(''); setQuestionAnswer('');
  }, []);

  const canAdvance = () => {
    if (currentStep === 0) return caseDescription.trim().length > 20 && claims.length > 0;
    return true;
  };

  const nextStep = () => {
    if (currentStep === 0) {
      setCurrentStep(1);
      (() => { multiSim.resetTabs(multiSim.simulationCount); for (let i = 0; i < multiSim.simulationCount; i++) { setTimeout(() => { multiSim.updateTabStatus(i, 'running'); startSimulation().then(() => multiSim.updateTabStatus(i, 'completed')).catch(() => multiSim.updateTabStatus(i, 'error')); }, i * 200); } })();
    } else if (currentStep < STEPS.length - 1) {
      setCurrentStep((s) => s + 1);
    }
  };

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
                isActive ? 'bg-primary text-primary-foreground'
                : isCompleted ? 'bg-primary/10 text-primary cursor-pointer hover:bg-primary/20'
                : 'text-muted-foreground'
              }`}
            >
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
          <Scale className="h-8 w-8 text-orange-600" />
          <h2 className="text-2xl font-bold">Vara do Trabalho</h2>
        </div>
        <p className="text-muted-foreground">Simule uma sentenca da Vara do Trabalho (1a instancia trabalhista).</p>
      </div>

      <Card className="border-orange-200 bg-orange-50/50 dark:border-orange-900 dark:bg-orange-950/20">
        <CardContent className="flex gap-4 py-4">
          <AlertCircle className="h-6 w-6 text-orange-500 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-orange-800 dark:text-orange-200">Conciliacao obrigatoria (CLT art. 846)</p>
            <p className="text-sm text-orange-700 dark:text-orange-300 mt-1">
              A simulação inclui audiencia de conciliacao obrigatoria, instrucao, analise
              individual de cada pedido e sentenca com calculos trabalhistas.
            </p>
          </div>
        </CardContent>
      </Card>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label>Descrição do Caso *</Label>
          <p className="text-xs text-muted-foreground">
            Descreva os fatos da reclamacao trabalhista. Inclua dados do empregador,
            funcao, periodo trabalhado, motivo da rescisao e circunstancias relevantes.
          </p>
          <Textarea
            value={caseDescription}
            onChange={(e) => setCaseDescription(e.target.value)}
            placeholder="Ex: Reclamante trabalhou como vendedor na empresa X de 01/2020 a 12/2023, sendo dispensado sem justa causa. Alega nao ter recebido..."
            className="min-h-[200px]"
          />
          <p className="text-xs text-muted-foreground text-right">{caseDescription.length} caracteres (minimo 20)</p>
        </div>

        <div className="space-y-2">
          <Label>Valor da Causa</Label>
          <Input value={caseValue} onChange={(e) => setCaseValue(e.target.value)} placeholder="Ex: R$ 50.000,00" />
        </div>

        <div className="space-y-2">
          <Label>Pedidos do Reclamante * (minimo 1)</Label>
          <div className="flex gap-2">
            <Input value={newClaim} onChange={(e) => setNewClaim(e.target.value)}
              placeholder="Digite um pedido e pressione Adicionar"
              onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addClaim())}
            />
            <Button onClick={addClaim} size="sm"><Plus className="h-4 w-4" /></Button>
          </div>
          <div className="flex flex-wrap gap-1 mt-2">
            {CLAIMS_SUGGESTIONS.filter(s => !claims.includes(s)).slice(0, 5).map((s, i) => (
              <Button key={i} variant="outline" size="sm" className="text-xs h-7"
                onClick={() => setClaims(prev => [...prev, s])}>{s.slice(0, 40)}...</Button>
            ))}
          </div>
          {claims.length > 0 && (
            <div className="space-y-1 mt-3">
              {claims.map((c, i) => (
                <div key={i} className="flex items-center gap-2 p-2 rounded bg-muted/50">
                  <span className="text-sm flex-1">{c}</span>
                  <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => removeClaim(i)}>
                    <X className="h-3 w-3" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        
        <div className="pt-4 border-t mt-4">
          <SimulationCountSelector value={multiSim.simulationCount} onChange={multiSim.setSimulationCount} />
        </div>
      </div>
      </div>
    </div>
  );

  const renderStep1 = () => (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-1">Simulação em Andamento</h2>
        <p className="text-muted-foreground">{analysisStage || 'Preparando simulação...'}</p>
      </div>
      {isSimulating && (
        <div className="flex items-center gap-3 py-3 px-4 bg-muted/50 rounded-lg border-2 speaker-active">
          <div className="h-10 w-10 rounded-full bg-orange-500 flex items-center justify-center">
            <Scale className="h-5 w-5 text-white gavel-thinking" />
          </div>
          <div className="flex-1">
            <span className="text-sm font-medium">Juiz do Trabalho</span>
            <p className="text-xs text-muted-foreground">{analysisStage || 'Analisando reclamacao...'}</p>
          </div>
          <div className="flex gap-1 ml-auto">
            <div className="h-2 w-2 rounded-full bg-orange-500 thinking-dot" />
            <div className="h-2 w-2 rounded-full bg-orange-500 thinking-dot" />
            <div className="h-2 w-2 rounded-full bg-orange-500 thinking-dot" />
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
      {sentencaText && (
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Sentenca (em andamento...)</CardTitle></CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px]">
              <div className="prose prose-sm max-w-none dark:prose-invert">
                <p className="whitespace-pre-wrap">{sentencaText}</p>
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderStep2 = () => {
    const isVictory = dispositivo === 'procedente' || dispositivo === 'parcialmente_procedente';
    const dispositivoLabel = {
      procedente: 'PROCEDENTE',
      improcedente: 'IMPROCEDENTE',
      parcialmente_procedente: 'PARCIALMENTE PROCEDENTE',
      indeterminado: 'INDETERMINADO',
    }[dispositivo] || dispositivo;

    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="text-center">
          <h2 className="text-3xl font-bold mb-2">Sentenca da Vara do Trabalho</h2>
          <Badge className={`text-lg px-6 py-2 border-0 ${
            isVictory ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
            : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
          }`}>{dispositivoLabel}</Badge>
        </div>

        {conciliacaoText && (
          <Card>
            <CardHeader><CardTitle>Audiência de Conciliacao</CardTitle><CardDescription>CLT art. 846 - Tentativa obrigatoria</CardDescription></CardHeader>
            <CardContent>
              <ScrollArea className="h-[250px]">
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{conciliacaoText}</ReactMarkdown>
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        )}

        {instrucaoText && (
          <details className="border rounded-lg">
            <summary className="cursor-pointer p-4 text-sm font-medium">Audiência de Instrução</summary>
            <div className="px-4 pb-4">
              <ScrollArea className="h-[250px]">
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{instrucaoText}</ReactMarkdown>
                </div>
              </ScrollArea>
            </div>
          </details>
        )}

        {sentencaText && (
          <Card>
            <CardHeader><CardTitle>Sentenca Trabalhista</CardTitle></CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{sentencaText}</ReactMarkdown>
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        )}

        {strategicReport && (
          <Card className={`border-2 ${isVictory ? 'border-green-200 bg-green-50/50 dark:border-green-900 dark:bg-green-950/20' : 'border-red-200 bg-red-50/50 dark:border-red-900 dark:bg-red-950/20'}`}>
            <CardHeader>
              <CardTitle className={isVictory ? 'text-green-700 dark:text-green-400' : 'text-red-700 dark:text-red-400'}>
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

        {simulationId && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <MessageSquare className="h-5 w-5 text-primary" />
                <div>
                  <CardTitle className="text-base">Questionar a Sentenca</CardTitle>
                  <CardDescription>Pergunte sobre o resultado ou pedidos individuais</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {['Cabe Recurso Ordinario ao TRT?', 'Como calcular as verbas deferidas?', 'Quais pedidos podem ser revertidos em recurso?'].map((q, i) => (
                  <Button key={i} variant="outline" size="sm" onClick={() => setQuestionText(q)} className="text-xs">{q}</Button>
                ))}
              </div>
              <div className="flex gap-2">
                <Textarea value={questionText} onChange={(e) => setQuestionText(e.target.value)}
                  placeholder="Sua pergunta sobre a sentenca..." className="flex-1 min-h-[80px]" />
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

        <div className="flex flex-col sm:flex-row gap-3">
          <Button onClick={exportPdf} className="flex-1" disabled={isExportingPdf}>
            {isExportingPdf ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <FileDown className="h-4 w-4 mr-2" />}
            {isExportingPdf ? 'Gerando PDF...' : 'Exportar PDF'}
          </Button>
          <Button variant="outline" onClick={resetSimulation} className="flex-1">
            <RotateCcw className="h-4 w-4 mr-2" />Nova Simulação
          </Button>
          <Button variant="outline" onClick={() => router.push('/dashboard/simulations')} className="flex-1">
            <ChevronLeft className="h-4 w-4 mr-2" />Voltar ao Histórico
          </Button>
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
          <Button variant="outline" onClick={() => router.push('/dashboard/simulations')}>
            <ChevronLeft className="h-4 w-4 mr-2" />Voltar
          </Button>
          <Button onClick={nextStep} disabled={!canAdvance()}>
            Iniciar Simulação<ChevronRight className="h-4 w-4 ml-2" />
          </Button>
        </div>
      )}
    </div>
  );
}
