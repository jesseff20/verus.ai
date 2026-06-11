'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useMutation } from '@tanstack/react-query';
import {
  ArrowLeft,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Scale,
  Sparkles,
  Upload,
  FileUp,
  Clock,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AIInput } from '@/components/ui/ai-input';
import { AITextarea } from '@/components/ui/ai-textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import { useCourts, useJudgeProfiles } from '@/hooks/use-simulations';
import api from '@/lib/api';

// ─── Constants ───

const BRAZILIAN_STATES = [
  'AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
  'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN',
  'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO',
];

// ─── CNJ Mask ───

function applyCNJMask(value: string): string {
  // Remove tudo que não é dígito
  const digits = value.replace(/\D/g, '').slice(0, 20);
  // Formato: NNNNNNN-DD.AAAA.J.TT.OOOO
  let result = '';
  for (let i = 0; i < digits.length; i++) {
    if (i === 7) result += '-';
    if (i === 9) result += '.';
    if (i === 13) result += '.';
    if (i === 14) result += '.';
    if (i === 16) result += '.';
    result += digits[i];
  }
  return result;
}

// ─── CPF/CNPJ Mask ───

function applyCpfCnpjMask(value: string): string {
  const digits = value.replace(/\D/g, '');
  if (digits.length <= 11) {
    // CPF: 000.000.000-00
    let r = '';
    for (let i = 0; i < Math.min(digits.length, 11); i++) {
      if (i === 3 || i === 6) r += '.';
      if (i === 9) r += '-';
      r += digits[i];
    }
    return r;
  }
  // CNPJ: 00.000.000/0000-00
  const d = digits.slice(0, 14);
  let r = '';
  for (let i = 0; i < d.length; i++) {
    if (i === 2) r += '.';
    if (i === 5) r += '.';
    if (i === 8) r += '/';
    if (i === 12) r += '-';
    r += d[i];
  }
  return r;
}

// ─── Types ───

interface CaseFormData {
  titulo: string;
  numero_processo: string;
  especialidade: string;
  status: string;
  fase: string;
  cliente_nome: string;
  cliente_cpf_cnpj: string;
  parte_contraria: string;
  parte_contraria_cpf_cnpj: string;
  tribunal: string;
  vara_juizo: string;
  comarca: string;
  valor_causa: string;
  data_distribuicao: string;
  descricao: string;
  observacoes: string;
}

const INITIAL_FORM: CaseFormData = {
  titulo: '',
  numero_processo: '',
  especialidade: 'civel',
  status: 'ativo',
  fase: 'inicial',
  cliente_nome: '',
  cliente_cpf_cnpj: '',
  parte_contraria: '',
  parte_contraria_cpf_cnpj: '',
  tribunal: '',
  vara_juizo: '',
  comarca: '',
  valor_causa: '',
  data_distribuicao: '',
  descricao: '',
  observacoes: '',
};

export default function NovoCasoPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();
  const [form, setForm] = useState<CaseFormData>(INITIAL_FORM);
  const [isAiFilling, setIsAiFilling] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);

  // Pre-fill client name from query params (e.g. coming from client detail)
  useEffect(() => {
    const clientName = searchParams.get('client_name');
    if (clientName) {
      setForm(prev => ({ ...prev, cliente_nome: clientName }));
    }
  }, [searchParams]);
  const [extractedPrazos, setExtractedPrazos] = useState<any[]>([]);
  const [prazosIdentificados, setPrazosIdentificados] = useState<any[]>([]);
  const docInputRef = useRef<HTMLInputElement>(null);

  // ─── Cascaded location selects ───
  const [selectedState, setSelectedState] = useState('');
  const { data: courts } = useCourts(selectedState || undefined);
  const tribunais = courts?.map((c) => c.name) || [];
  const selectedCourtObj = courts?.find((c) => c.name === form.tribunal);
  const comarcas = selectedCourtObj?.comarcas || [];

  const { data: judges } = useJudgeProfiles({
    state: selectedState || undefined,
    court: form.tribunal || undefined,
    comarca: form.comarca || undefined,
  });

  const mutation = useMutation({
    mutationFn: async (data: CaseFormData) => {
      const payload: Record<string, any> = {
        ...data,
        valor_causa: data.valor_causa ? parseFloat(data.valor_causa.replace(',', '.')) : null,
        data_distribuicao: data.data_distribuicao || null,
      };
      // Incluir prazos identificados pela IA para criação automática
      if (prazosIdentificados.length > 0) {
        payload.prazos_identificados = prazosIdentificados;
      }
      const response = await api.post('/api/v1/processos/', payload);
      return response.data;
    },
    onSuccess: (data) => {
      router.push(`/dashboard/processos/${data.id}`);
    },
    onError: (err: any) => {
      toast({ title: err?.response?.data?.error || err?.response?.data?.detail || 'Erro ao processar solicitação', variant: 'destructive' });
    },
  });

  function update(field: keyof CaseFormData, value: string) {
    setForm(prev => ({ ...prev, [field]: value }));
  }

  const handleStateChange = useCallback((state: string) => {
    setSelectedState(state);
    setForm(prev => ({ ...prev, tribunal: '', comarca: '', vara_juizo: '' }));
  }, []);

  const handleTribunalChange = useCallback((tribunal: string) => {
    setForm(prev => ({ ...prev, tribunal, comarca: '', vara_juizo: '' }));
  }, []);

  const handleComarcaChange = useCallback((comarca: string) => {
    setForm(prev => ({ ...prev, comarca, vara_juizo: '' }));
  }, []);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.titulo.trim() || !form.cliente_nome.trim()) return;
    mutation.mutate(form);
  }

  // ─── AI Auto-fill from uploaded document ───

  const handleDocUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsExtracting(true);
    setExtractedPrazos([]);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post('/api/v1/processos/extract-from-document/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const extracted = response.data;

      let filledCount = 0;

      setForm(prev => {
        const updated = { ...prev };
        if (extracted.titulo) { updated.titulo = extracted.titulo; filledCount++; }
        if (extracted.numero_processo) { updated.numero_processo = applyCNJMask(extracted.numero_processo); filledCount++; }
        if (extracted.especialidade) { updated.especialidade = extracted.especialidade; filledCount++; }
        if (extracted.cliente_nome) { updated.cliente_nome = extracted.cliente_nome; filledCount++; }
        if (extracted.cliente_documento) { updated.cliente_cpf_cnpj = applyCpfCnpjMask(extracted.cliente_documento); filledCount++; }
        if (extracted.parte_contraria) { updated.parte_contraria = extracted.parte_contraria; filledCount++; }
        if (extracted.parte_contraria_documento) { updated.parte_contraria_cpf_cnpj = applyCpfCnpjMask(extracted.parte_contraria_documento); filledCount++; }
        if (extracted.tribunal) { updated.tribunal = extracted.tribunal; filledCount++; }
        if (extracted.comarca) { updated.comarca = extracted.comarca; filledCount++; }
        if (extracted.vara_juizo) { updated.vara_juizo = extracted.vara_juizo; filledCount++; }
        if (extracted.valor_causa) { updated.valor_causa = String(extracted.valor_causa); filledCount++; }
        if (extracted.data_distribuicao) { updated.data_distribuicao = extracted.data_distribuicao; filledCount++; }
        if (extracted.descricao) { updated.descricao = extracted.descricao; filledCount++; }
        if (extracted.observacoes) { updated.observacoes = extracted.observacoes; filledCount++; }
        return updated;
      });

      // Estado (para dropdown cascateado)
      if (extracted.estado) {
        setSelectedState(extracted.estado);
      }

      // Prazos identificados
      const prazos = extracted.prazos_identificados || [];
      if (prazos.length > 0) {
        setExtractedPrazos(prazos);
        setPrazosIdentificados(prazos);
      }

      toast({
        title: 'Documento processado com sucesso!',
        description: `${filledCount} campo(s) preenchido(s) automaticamente.${prazos.length > 0 ? ` ${prazos.length} prazo(s) identificado(s).` : ''}`,
      });
    } catch (error: any) {
      toast({
        title: 'Erro ao processar documento',
        description: error?.response?.data?.error || 'Não foi possível extrair dados do documento. Tente novamente.',
        variant: 'destructive',
      });
    } finally {
      setIsExtracting(false);
      // Limpar input para permitir reenviar o mesmo arquivo
      if (docInputRef.current) docInputRef.current.value = '';
    }
  }, [toast]);

  // ─── AI Auto-fill from document text ───

  const handleAiFill = useCallback(async () => {
    const text = form.descricao.trim();
    if (!text) {
      toast({
        title: 'Texto necessário',
        description: 'Cole o texto da petição inicial ou documento no campo "Descrição do Caso" antes de usar o preenchimento por IA.',
        variant: 'destructive',
      });
      return;
    }

    setIsAiFilling(true);
    try {
      const response = await api.post('/api/v1/processos/extract-case-data/', {
        text,
      });
      const extracted = response.data;

      setForm(prev => ({
        ...prev,
        titulo: extracted.titulo || prev.titulo,
        numero_processo: extracted.numero_processo ? applyCNJMask(extracted.numero_processo) : prev.numero_processo,
        especialidade: extracted.especialidade || prev.especialidade,
        cliente_nome: extracted.cliente_nome || prev.cliente_nome,
        parte_contraria: extracted.parte_contraria || prev.parte_contraria,
        tribunal: extracted.tribunal || prev.tribunal,
        comarca: extracted.comarca || prev.comarca,
        vara_juizo: extracted.vara_juizo || prev.vara_juizo,
        valor_causa: extracted.valor_causa || prev.valor_causa,
      }));

      // Se o backend retornou estado, setar no dropdown cascateado
      if (extracted.estado) {
        setSelectedState(extracted.estado);
      }

      toast({
        title: 'Dados extraidos com sucesso!',
        description: 'Revise os campos preenchidos pela IA antes de salvar.',
      });
    } catch (error: any) {
      toast({
        title: 'Erro ao extrair dados',
        description: error?.response?.data?.error || 'Não foi possível extrair dados do texto. Tente novamente.',
        variant: 'destructive',
      });
    } finally {
      setIsAiFilling(false);
    }
  }, [form.descricao, toast]);

  return (
    <div className="max-w-3xl mx-auto space-y-6 px-0 sm:px-0 pb-24 sm:pb-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="icon" asChild className="shrink-0">
          <Link href="/dashboard/processos">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight flex items-center gap-2">
            <Scale className="h-5 w-5 sm:h-6 sm:w-6" />
            Novo Caso Jurídico
          </h1>
          <p className="text-muted-foreground text-sm">Preencha os dados do caso</p>
        </div>
      </div>

      {mutation.error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Erro ao criar caso. Verifique os dados e tente novamente.
          </AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Upload de documento para preenchimento automatico */}
        <Card className="border-primary/20 bg-primary/5">
          <CardContent className="flex flex-col sm:flex-row items-start sm:items-center gap-4 py-4">
            <FileUp className="h-8 w-8 text-primary flex-shrink-0 hidden sm:block" />
            <div className="flex-1">
              <h3 className="font-semibold flex items-center gap-2">
                <FileUp className="h-5 w-5 text-primary sm:hidden" />
                Preenchimento Automático
              </h3>
              <p className="text-sm text-muted-foreground">
                Anexe uma petição inicial, citação ou intimação e a IA preencherá todos os campos automaticamente.
              </p>
            </div>
            <input
              type="file"
              ref={docInputRef}
              className="hidden"
              accept=".pdf,.docx,.doc,.odt,.txt"
              onChange={handleDocUpload}
            />
            <Button
              type="button"
              onClick={() => docInputRef.current?.click()}
              disabled={isExtracting}
              className="w-full sm:w-auto"
            >
              {isExtracting ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <Upload className="h-4 w-4 mr-2" />
              )}
              {isExtracting ? 'Extraindo dados...' : 'Anexar Documento'}
            </Button>
          </CardContent>
        </Card>

        {/* Preview de prazos identificados */}
        {extractedPrazos.length > 0 && (
          <Card className="border-amber-500/20 bg-amber-50 dark:bg-amber-950/20">
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Clock className="h-4 w-4 text-amber-600" />
                Prazos Identificados ({extractedPrazos.length})
              </CardTitle>
              <CardDescription>
                Estes prazos serao criados automaticamente ao salvar o caso
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {extractedPrazos.map((prazo, idx) => (
                  <div key={idx} className="flex flex-col sm:flex-row sm:items-center justify-between text-sm p-2 rounded bg-background/80 gap-1">
                    <div>
                      <span className="font-medium">{prazo.tipo}</span>
                      {prazo.descricao && (
                        <span className="text-muted-foreground ml-2">— {prazo.descricao}</span>
                      )}
                    </div>
                    <div className="text-muted-foreground flex-shrink-0 sm:ml-4">
                      {prazo.prazo_dias} dia(s)
                      {prazo.data_inicio && ` a partir de ${prazo.data_inicio}`}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Identificação */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Identificação do Caso</CardTitle>
            <CardDescription>Informações básicas de identificação</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="titulo">Título / Assunto *</Label>
              <AIInput
                id="titulo"
                placeholder="Ex: Ação de Indenização - João Silva x Empresa XYZ"
                className="text-[16px] sm:text-sm"
                value={form.titulo}
                onChange={e => update('titulo', e.target.value)}
                onAIChange={(v) => update('titulo', v)}
                required
                aiContext="título do caso jurídico"
                aiObjective="Sugira um título claro identificando as partes e o tipo de ação"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="numero_processo">Número do Processo (CNJ)</Label>
              <AIInput
                id="numero_processo"
                placeholder="0000000-00.0000.0.00.0000"
                className="text-[16px] sm:text-sm"
                value={form.numero_processo}
                onChange={e => update('numero_processo', applyCNJMask(e.target.value))}
                onAIChange={(v) => update('numero_processo', applyCNJMask(v))}
                maxLength={25}
                aiContext="número do processo judicial no padrão CNJ"
                aiObjective="Formate o número do processo no padrão NNNNNNN-DD.AAAA.J.TT.OOOO"
              />
              <p className="text-xs text-muted-foreground">Formato: NNNNNNN-DD.AAAA.J.TT.OOOO</p>
            </div>

            <div className="grid grid-cols-1 gap-4">
              <div className="space-y-2">
                <Label>Especialidade *</Label>
                <Select value={form.especialidade} onValueChange={v => update('especialidade', v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="civel">Civel</SelectItem>
                    <SelectItem value="criminal">Criminal</SelectItem>
                    <SelectItem value="trabalhista">Trabalhista</SelectItem>
                    <SelectItem value="tributario">Tributario</SelectItem>
                    <SelectItem value="administrativo">Administrativo</SelectItem>
                    <SelectItem value="previdenciario">Previdenciario</SelectItem>
                    <SelectItem value="familia">Familia e Sucessoes</SelectItem>
                    <SelectItem value="empresarial">Empresarial</SelectItem>
                    <SelectItem value="ambiental">Ambiental</SelectItem>
                    <SelectItem value="consumidor">Consumidor</SelectItem>
                    <SelectItem value="imobiliario">Imobiliario</SelectItem>
                    <SelectItem value="outros">Outros</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Status</Label>
                <Select value={form.status} onValueChange={v => update('status', v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ativo">Ativo</SelectItem>
                    <SelectItem value="aguardando">Aguardando</SelectItem>
                    <SelectItem value="suspenso">Suspenso</SelectItem>
                    <SelectItem value="encerrado">Encerrado</SelectItem>
                    <SelectItem value="ganho">Ganho</SelectItem>
                    <SelectItem value="perdido">Perdido</SelectItem>
                    <SelectItem value="acordo">Acordo</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Fase</Label>
                <Select value={form.fase} onValueChange={v => update('fase', v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="inicial">Fase Inicial</SelectItem>
                    <SelectItem value="instrucao">Instrução</SelectItem>
                    <SelectItem value="julgamento">Julgamento</SelectItem>
                    <SelectItem value="recursal">Recursal</SelectItem>
                    <SelectItem value="execução">Execução</SelectItem>
                    <SelectItem value="transitado">Transitado em Julgado</SelectItem>
                    <SelectItem value="extrajudicial">Extrajudicial</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Partes */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Partes do Processo</CardTitle>
            <CardDescription>Identificação das partes envolvidas</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="cliente_nome">Cliente / Parte Representada *</Label>
                <AIInput
                  id="cliente_nome"
                  placeholder="Nome completo"
                  className="text-[16px] sm:text-sm"
                  value={form.cliente_nome}
                  onChange={e => update('cliente_nome', e.target.value)}
                  onAIChange={(v) => update('cliente_nome', v)}
                  required
                  aiContext="nome do cliente ou parte representada no processo"
                  aiObjective="Formate o nome completo da parte representada"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="cliente_cpf_cnpj">CPF/CNPJ do Cliente</Label>
                <AIInput
                  id="cliente_cpf_cnpj"
                  placeholder="000.000.000-00 ou 00.000.000/0000-00"
                  value={form.cliente_cpf_cnpj}
                  onChange={e => update('cliente_cpf_cnpj', applyCpfCnpjMask(e.target.value))}
                  onAIChange={(v) => update('cliente_cpf_cnpj', applyCpfCnpjMask(v))}
                  maxLength={18}
                  aiContext="CPF ou CNPJ do cliente"
                  aiObjective="Formate o CPF ou CNPJ do cliente corretamente"
                />
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="parte_contraria">Parte Contrária</Label>
                <AIInput
                  id="parte_contraria"
                  placeholder="Nome completo"
                  value={form.parte_contraria}
                  onChange={e => update('parte_contraria', e.target.value)}
                  onAIChange={(v) => update('parte_contraria', v)}
                  aiContext="nome da parte contrária no processo judicial"
                  aiObjective="Formate o nome completo da parte contrária"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="parte_contraria_cpf_cnpj">CPF/CNPJ da Parte Contrária</Label>
                <AIInput
                  id="parte_contraria_cpf_cnpj"
                  placeholder="000.000.000-00 ou 00.000.000/0000-00"
                  value={form.parte_contraria_cpf_cnpj}
                  onChange={e => update('parte_contraria_cpf_cnpj', applyCpfCnpjMask(e.target.value))}
                  onAIChange={(v) => update('parte_contraria_cpf_cnpj', applyCpfCnpjMask(v))}
                  maxLength={18}
                  aiContext="CPF ou CNPJ da parte contrária"
                  aiObjective="Formate o CPF ou CNPJ da parte contrária corretamente"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Localização Processual — Cascaded Dropdowns */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Localização Processual</CardTitle>
            <CardDescription>Selecione a localização ou digite manualmente</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Estado (drives the cascade) */}
            <div className="space-y-2">
              <Label>Estado</Label>
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

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Tribunal — dropdown from courts API */}
              <div className="space-y-2">
                <Label htmlFor="tribunal">Tribunal</Label>
                {selectedState && tribunais.length > 0 ? (
                  <Select
                    value={form.tribunal}
                    onValueChange={handleTribunalChange}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder={selectedState ? 'Selecione o tribunal' : 'Selecione o estado primeiro'} />
                    </SelectTrigger>
                    <SelectContent>
                      {tribunais.map((t) => (
                        <SelectItem key={t} value={t}>{t}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <AIInput
                    id="tribunal"
                    placeholder={selectedState ? 'Ex: TJRJ, TRT-1, STJ' : 'Selecione o estado primeiro'}
                    value={form.tribunal}
                    onChange={e => update('tribunal', e.target.value)}
                    onAIChange={(v) => update('tribunal', v)}
                    disabled={!selectedState}
                    aiContext="tribunal competente do processo judicial"
                    aiObjective="Identifique o tribunal correto para o processo"
                  />
                )}
              </div>
              {/* Comarca — dropdown from court comarcas */}
              <div className="space-y-2">
                <Label htmlFor="comarca">Comarca / Seção Judiciária</Label>
                {form.tribunal && comarcas.length > 0 ? (
                  <Select
                    value={form.comarca}
                    onValueChange={handleComarcaChange}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione a comarca" />
                    </SelectTrigger>
                    <SelectContent>
                      {comarcas.map((c) => (
                        <SelectItem key={c} value={c}>{c}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <AIInput
                    id="comarca"
                    placeholder={form.tribunal ? 'Ex: Rio de Janeiro' : 'Selecione o tribunal primeiro'}
                    value={form.comarca}
                    onChange={e => update('comarca', e.target.value)}
                    onAIChange={(v) => update('comarca', v)}
                    disabled={!form.tribunal}
                    aiContext="comarca ou seção judiciária do processo"
                    aiObjective="Identifique a comarca correta para o processo"
                  />
                )}
              </div>
            </div>

            {/* Vara — still free text, optionally show judge suggestions */}
            <div className="space-y-2">
              <Label htmlFor="vara_juizo">Vara / Juizo</Label>
              <AIInput
                id="vara_juizo"
                placeholder="Ex: 3a Vara Civel da Comarca do Rio de Janeiro"
                value={form.vara_juizo}
                onChange={e => update('vara_juizo', e.target.value)}
                onAIChange={(v) => update('vara_juizo', v)}
                aiContext="vara ou juízo do processo judicial"
                aiObjective="Identifique a vara ou juízo competente para o processo"
              />
              {judges && judges.length > 0 && (
                <p className="text-xs text-muted-foreground">
                  {judges.length} juiz(es) cadastrado(s) nesta comarca/tribunal
                </p>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="valor_causa">Valor da Causa (R$)</Label>
                <Input
                  id="valor_causa"
                  type="number"
                  placeholder="0,00"
                  value={form.valor_causa}
                  onChange={e => update('valor_causa', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="data_distribuicao">Data de Distribuição</Label>
                <Input
                  id="data_distribuicao"
                  type="date"
                  value={form.data_distribuicao}
                  onChange={e => update('data_distribuicao', e.target.value)}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Descrição */}
        <Card>
          <CardHeader>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <CardTitle className="text-base">Descrição e Estratégia</CardTitle>
                <CardDescription>Cole o texto de uma petição inicial para preencher automaticamente</CardDescription>
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleAiFill}
                disabled={isAiFilling || !form.descricao.trim()}
                className="w-full sm:w-auto"
              >
                {isAiFilling ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Sparkles className="h-4 w-4 mr-2" />
                )}
                Preencher com IA
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="descrição">Descrição do Caso</Label>
              <AITextarea
                id="descrição"
                placeholder="Cole aqui o texto da petição inicial ou descreva os fatos do caso. Use o botão 'Preencher com IA' para extrair dados automaticamente..."
                className="min-h-[120px] text-[16px] sm:text-sm"
                value={form.descricao}
                onChange={e => update('descricao', e.target.value)}
                onAIChange={(text) => setForm(prev => ({ ...prev, descricao: text }))}
                aiContext="descrição de caso jurídico"
                aiObjective="Melhore a redação da descrição do caso, mantendo os fatos e tese jurídica"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="observacoes">Observações Internas</Label>
              <AITextarea
                id="observacoes"
                placeholder="Notas internas, informações de contato, histórico..."
                className="min-h-[80px] text-[16px] sm:text-sm"
                value={form.observacoes}
                onChange={e => update('observacoes', e.target.value)}
                onAIChange={(text) => setForm(prev => ({ ...prev, observacoes: text }))}
                aiContext="observações internas de caso jurídico"
                aiObjective="Melhore a redação das observações internas do caso"
              />
            </div>
          </CardContent>
        </Card>

        {/* Desktop submit buttons */}
        <div className="hidden sm:flex gap-3 justify-end">
          <Button type="button" variant="outline" asChild>
            <Link href="/dashboard/processos">Cancelar</Link>
          </Button>
          <Button type="submit" disabled={mutation.isPending || !form.titulo.trim() || !form.cliente_nome.trim()}>
            {mutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Salvando...
              </>
            ) : mutation.isSuccess ? (
              <>
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Salvo!
              </>
            ) : (
              'Criar Caso'
            )}
          </Button>
        </div>

        {/* Mobile sticky submit bar */}
        <div className="sm:hidden fixed bottom-0 left-0 right-0 z-40 bg-background/95 backdrop-blur-sm border-t px-4 py-3 flex gap-3">
          <Button type="button" variant="outline" asChild className="flex-1 min-h-[48px]">
            <Link href="/dashboard/processos">Cancelar</Link>
          </Button>
          <Button type="submit" disabled={mutation.isPending || !form.titulo.trim() || !form.cliente_nome.trim()} className="flex-1 min-h-[48px]">
            {mutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Salvando...
              </>
            ) : mutation.isSuccess ? (
              <>
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Salvo!
              </>
            ) : (
              'Criar Caso'
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
