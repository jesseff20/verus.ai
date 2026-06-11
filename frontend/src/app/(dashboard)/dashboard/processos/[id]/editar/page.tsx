'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  ArrowLeft,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Scale,
  Sparkles,
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
  const digits = value.replace(/\D/g, '').slice(0, 20);
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
    let r = '';
    for (let i = 0; i < Math.min(digits.length, 11); i++) {
      if (i === 3 || i === 6) r += '.';
      if (i === 9) r += '-';
      r += digits[i];
    }
    return r;
  }
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

const EMPTY_FORM: CaseFormData = {
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

export default function EditarCasoPage() {
  const router = useRouter();
  const params = useParams();
  const caseId = params.id as string;
  const { toast } = useToast();
  const [form, setForm] = useState<CaseFormData>(EMPTY_FORM);
  const [isAiFilling, setIsAiFilling] = useState(false);

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

  const { data: caso, isLoading, error } = useQuery({
    queryKey: ['caso', caseId],
    queryFn: async () => {
      const response = await api.get(`/api/v1/processos/${caseId}/`);
      return response.data;
    },
  });

  useEffect(() => {
    if (caso) {
      setForm({
        titulo: caso.titulo || '',
        numero_processo: caso.numero_processo || '',
        especialidade: caso.especialidade || 'civel',
        status: caso.status || 'ativo',
        fase: caso.fase || 'inicial',
        cliente_nome: caso.cliente_nome || '',
        cliente_cpf_cnpj: caso.cliente_cpf_cnpj || '',
        parte_contraria: caso.parte_contraria || '',
        parte_contraria_cpf_cnpj: caso.parte_contraria_cpf_cnpj || '',
        tribunal: caso.tribunal || '',
        vara_juizo: caso.vara_juizo || '',
        comarca: caso.comarca || '',
        valor_causa: caso.valor_causa ? String(caso.valor_causa) : '',
        data_distribuicao: caso.data_distribuicao || '',
        descricao: caso.descricao || '',
        observacoes: caso.observacoes || '',
      });
      // Setar estado para ativar cascata de dropdowns
      if (caso.estado) {
        setSelectedState(caso.estado);
      }
    }
  }, [caso]);

  const mutation = useMutation({
    mutationFn: async (data: CaseFormData) => {
      const payload = {
        ...data,
        valor_causa: data.valor_causa ? parseFloat(data.valor_causa.replace(',', '.')) : null,
        data_distribuicao: data.data_distribuicao || null,
      };
      const response = await api.put(`/api/v1/processos/${caseId}/`, payload);
      return response.data;
    },
    onSuccess: () => {
      toast({ title: 'Caso atualizado com sucesso!' });
      router.push(`/dashboard/processos/${caseId}`);
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

  // ─── AI Auto-fill ───

  const handleAiFill = useCallback(async () => {
    const text = form.descricao.trim();
    if (!text) {
      toast({
        title: 'Texto necessário',
        description: 'Cole o texto da petição inicial no campo "Descrição do Caso" antes de usar o preenchimento por IA.',
        variant: 'destructive',
      });
      return;
    }

    setIsAiFilling(true);
    try {
      const response = await api.post('/api/v1/processos/extract-case-data/', { text });
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
        description: error?.response?.data?.error || 'Tente novamente.',
        variant: 'destructive',
      });
    } finally {
      setIsAiFilling(false);
    }
  }, [form.descricao, toast]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !caso) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-4">
        <AlertCircle className="h-10 w-10 text-destructive" />
        <p className="text-muted-foreground">Caso nao encontrado</p>
        <Button asChild variant="outline">
          <Link href="/dashboard/processos"><ArrowLeft className="h-4 w-4 mr-2" />Voltar</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="icon" asChild>
          <Link href={`/dashboard/processos/${caseId}`}>
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Scale className="h-6 w-6" />
            Editar Caso
          </h1>
          <p className="text-muted-foreground text-sm">Atualize os dados do caso</p>
        </div>
      </div>

      {mutation.error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Erro ao salvar caso. Verifique os dados e tente novamente.
          </AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
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
                value={form.numero_processo}
                onChange={e => update('numero_processo', applyCNJMask(e.target.value))}
                onAIChange={(v) => update('numero_processo', applyCNJMask(v))}
                maxLength={25}
                aiContext="número do processo judicial no padrão CNJ"
                aiObjective="Formate o número do processo no padrão NNNNNNN-DD.AAAA.J.TT.OOOO"
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Especialidade *</Label>
                <Select value={form.especialidade} onValueChange={v => update('especialidade', v)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
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
                  <SelectTrigger><SelectValue /></SelectTrigger>
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
                  <SelectTrigger><SelectValue /></SelectTrigger>
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
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="cliente_nome">Cliente / Parte Representada *</Label>
                <AIInput
                  id="cliente_nome"
                  placeholder="Nome completo"
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
            <div className="grid grid-cols-2 gap-4">
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

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="tribunal">Tribunal</Label>
                {selectedState && tribunais.length > 0 ? (
                  <Select
                    value={form.tribunal}
                    onValueChange={handleTribunalChange}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione o tribunal" />
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

            <div className="grid grid-cols-2 gap-4">
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
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base">Descrição e Estratégia</CardTitle>
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleAiFill}
                disabled={isAiFilling || !form.descricao.trim()}
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
                placeholder="Resumo dos fatos, tese jurídica e estratégia processual..."
                className="min-h-[120px]"
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
                className="min-h-[80px]"
                value={form.observacoes}
                onChange={e => update('observacoes', e.target.value)}
                onAIChange={(text) => setForm(prev => ({ ...prev, observacoes: text }))}
                aiContext="observações internas de caso jurídico"
                aiObjective="Melhore a redação das observações internas do caso"
              />
            </div>
          </CardContent>
        </Card>

        <div className="flex gap-3 justify-end">
          <Button type="button" variant="outline" asChild>
            <Link href={`/dashboard/processos/${caseId}`}>Cancelar</Link>
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
              'Salvar Alterações'
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
