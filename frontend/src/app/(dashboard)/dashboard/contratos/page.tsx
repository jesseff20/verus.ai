'use client';

import { useState, useMemo, useEffect } from 'react';
import DOMPurify from 'isomorphic-dompurify';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { AIInput } from '@/components/ui/ai-input';
import { AITextarea } from '@/components/ui/ai-textarea';
import { Switch } from '@/components/ui/switch';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  FileText,
  CheckCircle2,
  Clock,
  FilePlus,
  Eye,
  PenLine,
  Sparkles,
  ArrowRight,
  ArrowLeft,
  Loader2,
  Scale,
  ScrollText,
  Users,
  Briefcase,
  ShieldCheck,
  Handshake,
  FileSignature,
  Building2,
  Home,
  ShoppingCart,
  UserCheck,
} from 'lucide-react';
import {
  useContracts,
  useContractStats,
  useCreateContract,
  useGenerateContract,
  useUploadContract,
  type LegalContract,
} from '@/hooks/use-contracts';

// ── Helpers ──

const statusConfig: Record<string, { label: string; className: string }> = {
  draft: { label: 'Rascunho', className: 'bg-gray-100 text-gray-700 border-gray-200' },
  pending_signature: { label: 'Pendente', className: 'bg-yellow-100 text-yellow-800 border-yellow-200' },
  signed: { label: 'Assinado', className: 'bg-green-100 text-green-800 border-green-200' },
  cancelled: { label: 'Cancelado', className: 'bg-red-100 text-red-700 border-red-200' },
};

const typeConfig: Record<string, { label: string; className: string }> = {
  honorarios: { label: 'Termo de Referência', className: 'bg-blue-100 text-blue-800 border-blue-200' },
  procuracao: { label: 'Procuração', className: 'bg-purple-100 text-purple-800 border-purple-200' },
  substabelecimento: { label: 'Substabelecimento', className: 'bg-amber-100 text-amber-800 border-amber-200' },
  prestacao_servicos: { label: 'Prestação de Serviços', className: 'bg-teal-100 text-teal-800 border-teal-200' },
  consultoria: { label: 'Consultoria', className: 'bg-cyan-100 text-cyan-800 border-cyan-200' },
  confidencialidade: { label: 'NDA', className: 'bg-rose-100 text-rose-800 border-rose-200' },
  parceria: { label: 'Parceria', className: 'bg-indigo-100 text-indigo-800 border-indigo-200' },
  cessao_credito: { label: 'Cessão de Crédito', className: 'bg-orange-100 text-orange-800 border-orange-200' },
  acordo_extrajudicial: { label: 'Acordo Extrajudicial', className: 'bg-lime-100 text-lime-800 border-lime-200' },
  distrato: { label: 'Distrato', className: 'bg-red-100 text-red-700 border-red-200' },
  compromisso_arbitragem: { label: 'Arbitragem', className: 'bg-violet-100 text-violet-800 border-violet-200' },
  acordo_acionistas: { label: 'Acordo Acionistas', className: 'bg-fuchsia-100 text-fuchsia-800 border-fuchsia-200' },
  contrato_social: { label: 'Contrato Social', className: 'bg-emerald-100 text-emerald-800 border-emerald-200' },
  termos_uso: { label: 'Termos de Uso', className: 'bg-sky-100 text-sky-800 border-sky-200' },
  contrato_locacao: { label: 'Locação', className: 'bg-yellow-100 text-yellow-800 border-yellow-200' },
  compra_venda: { label: 'Compra e Venda', className: 'bg-green-100 text-green-800 border-green-200' },
  contrato_trabalho: { label: 'Trabalho', className: 'bg-blue-100 text-blue-700 border-blue-200' },
};

const TYPE_LABELS: Record<string, string> = {
  honorarios: 'Termo de Referência',
  procuracao: 'Procuração',
  substabelecimento: 'Substabelecimento',
  prestacao_servicos: 'Contrato de Prestação de Serviços Juridicos',
  consultoria: 'Contrato de Consultoria Jurídica',
  confidencialidade: 'Acordo de Confidencialidade / NDA',
  parceria: 'Contrato de Parceria',
  cessao_credito: 'Contrato de Cessão de Crédito',
  acordo_extrajudicial: 'Acordo Extrajudicial',
  distrato: 'Distrato / Rescisão Contratual',
  compromisso_arbitragem: 'Compromisso Arbitral',
  acordo_acionistas: 'Acordo de Acionistas',
  contrato_social: 'Contrato Social',
  termos_uso: 'Termos de Uso',
  contrato_locacao: 'Contrato de Locação',
  compra_venda: 'Contrato de Compra e Venda',
  contrato_trabalho: 'Contrato de Trabalho',
};

const PAYMENT_SUGGESTIONS = [
  { value: 'a_vista', label: 'A vista - pagamento integral no ato da assinatura' },
  { value: 'parcelado', label: 'Parcelado - em parcelas mensais iguais e consecutivas' },
  { value: 'exito', label: 'Exito - percentual sobre o valor obtido na acao' },
  { value: 'misto', label: 'Misto - entrada fixa + percentual de exito' },
  { value: 'mensal', label: 'Mensal - retainer fixo mensal (assessoria)' },
  { value: 'por_ato', label: 'Por ato - cobrado por cada ato processual praticado' },
];

function StatusBadge({ status }: { status: string }) {
  const cfg = statusConfig[status] ?? { label: status, className: '' };
  return <Badge variant="outline" className={cfg.className}>{cfg.label}</Badge>;
}

function TypeBadge({ type }: { type: string }) {
  const cfg = typeConfig[type] ?? { label: type, className: '' };
  return <Badge variant="outline" className={cfg.className}>{cfg.label}</Badge>;
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('pt-BR');
}

// ── Contract Type Cards ──

const CONTRACT_TYPES = [
  { value: 'contrato_administrativo', title: 'Contrato Administrativo', description: 'Contrato de obras, serviços ou fornecimento celebrado pela municipalidade.', icon: Briefcase },
  { value: 'convenio', title: 'Convênio', description: 'Instrumento de cooperação entre entes públicos ou entidades sem fins lucrativos.', icon: Handshake },
  { value: 'tac', title: 'TAC / Ajustamento de Conduta', description: 'Termo de Ajustamento de Conduta para adequação a obrigações legais.', icon: Scale },
  { value: 'acordo_colaboracao', title: 'Acordo de Colaboração', description: 'Parceria com OSC conforme Lei 13.019/2014 (Marco Regulatório das OSCs).', icon: Users },
  { value: 'procuracao', title: 'Procuração', description: 'Instrumento de mandato em representação do Município.', icon: ScrollText },
  { value: 'concessao', title: 'Concessão / Permissão', description: 'Concessão ou permissão de serviço público ou uso de bem municipal.', icon: Building2 },
  { value: 'acordo_extrajudicial', title: 'Acordo Extrajudicial', description: 'Acordo firmado extrajudicialmente pela Fazenda Pública.', icon: Handshake },
  { value: 'contrato_gestao', title: 'Contrato de Gestão', description: 'Contrato com organização social para gestão de serviço público.', icon: FileSignature },
  { value: 'cessao_uso', title: 'Cessão de Uso', description: 'Cessão de uso de bem público a terceiros.', icon: FileText },
  { value: 'cooperacao_tecnica', title: 'Cooperação Técnica', description: 'Acordo de cooperação técnica entre entidades públicas.', icon: Briefcase },
  { value: 'adesao_ata', title: 'Adesão a Ata de Registro', description: 'Adesão a ata de registro de preços de outro ente (carona).', icon: FileText },
  { value: 'distrato', title: 'Distrato / Rescisão', description: 'Rescisão de contrato administrativo.', icon: FileText },
] as const;

// ── New Contract Dialog ──

function NewContractDialog() {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(1);
  const [contractType, setContractType] = useState('');
  const [clientId, setClientId] = useState('');
  const [caseId, setCaseId] = useState('');
  const [title, setTitle] = useState('');
  const [previewHtml, setPreviewHtml] = useState('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  // Honorários fields
  const [feeType, setFeeType] = useState('fixed');
  const [fixedAmount, setFixedAmount] = useState('');
  const [hourlyRate, setHourlyRate] = useState('');
  const [installments, setInstallments] = useState('1');
  const [paymentTerms, setPaymentTerms] = useState('');
  const [selectedPaymentSuggestion, setSelectedPaymentSuggestion] = useState('');

  // Procuração fields
  const [powersType, setPowersType] = useState('general');
  const [specialPowers, setSpecialPowers] = useState('');
  const [courtScope, setCourtScope] = useState('');
  const [isIrrevocable, setIsIrrevocable] = useState(false);

  // Substabelecimento fields
  const [substabelecidoName, setSubstabelecidoName] = useState('');
  const [substabelecidoOab, setSubstabelecidoOab] = useState('');
  const [withReserve, setWithReserve] = useState(true);
  const [powersTransferred, setPowersTransferred] = useState('');

  const generateContract = useGenerateContract();
  const createContract = useCreateContract();

  // Fetch clients from API
  const { data: clients = [] } = useQuery({
    queryKey: ['clients-list-simple'],
    queryFn: async () => {
      const res = await api.get('/api/v1/clientes/', { params: { page_size: 200 } });
      return res.data?.results || res.data || [];
    },
  });

  // Fetch cases from API
  const { data: casesList = [] } = useQuery({
    queryKey: ['cases-list-simple'],
    queryFn: async () => {
      const res = await api.get('/api/v1/processos/', { params: { page_size: 200 } });
      return res.data?.results || res.data || [];
    },
  });

  // Filter cases by selected client
  const filteredCases = useMemo(() => {
    if (!clientId) return casesList;
    return casesList.filter((c: any) => c.client === clientId);
  }, [casesList, clientId]);

  // Auto-generate title when client, case, or type changes
  useEffect(() => {
    const clientObj = clients.find((c: any) => String(c.id) === clientId);
    const caseObj = casesList.find((c: any) => String(c.id) === caseId);
    const typeLabel = TYPE_LABELS[contractType] || '';

    if (typeLabel) {
      const parts = [typeLabel];
      if (clientObj) parts.push(clientObj.name || clientObj.nome || '');
      if (caseObj) parts.push(caseObj.titulo || '');
      setTitle(parts.filter(Boolean).join(' - '));
    }
  }, [clientId, caseId, contractType, clients, casesList]);

  // Apply payment suggestion
  useEffect(() => {
    if (selectedPaymentSuggestion) {
      const suggestion = PAYMENT_SUGGESTIONS.find(s => s.value === selectedPaymentSuggestion);
      if (suggestion) {
        setPaymentTerms(suggestion.label);
      }
    }
  }, [selectedPaymentSuggestion]);

  function resetForm() {
    setStep(1);
    setContractType('');
    setClientId('');
    setCaseId('');
    setTitle('');
    setPreviewHtml('');
    setFeeType('fixed');
    setFixedAmount('');
    setHourlyRate('');
    setInstallments('1');
    setPaymentTerms('');
    setSelectedPaymentSuggestion('');
    setPowersType('general');
    setSpecialPowers('');
    setCourtScope('');
    setIsIrrevocable(false);
    setSubstabelecidoName('');
    setSubstabelecidoOab('');
    setWithReserve(true);
    setPowersTransferred('');
    setUploadedFile(null);
    setIsUploading(false);
  }

  const uploadContract = useUploadContract();

  async function handleFileUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadedFile(file);

    const formData = new FormData();
    formData.append('file', file);
    if (contractType) {
      formData.append('contract_type', contractType);
    }

    try {
      const result = await uploadContract.mutateAsync(formData);
      // Preencher dados extraídos
      const extracted = result.extracted_data;
      if (extracted.client_name && !clientId) {
        // Tentar encontrar cliente nos dados retornados
        console.log('Dados extraídos:', extracted);
      }
      setPreviewHtml(result.contract.content_html);
      setStep(5);
    } catch (error) {
      console.error('Erro no upload:', error);
    } finally {
      setIsUploading(false);
    }
  }

  function buildPayload() {
    const base: Record<string, unknown> = {
      contract_type: contractType,
      client: clientId,
      title,
    };
    if (caseId) base.case = caseId;

    if (contractType === 'honorarios') {
      base.honorarios_detail = {
        fee_type: feeType,
        fixed_amount: fixedAmount ? parseFloat(fixedAmount) : null,
        hourly_rate: hourlyRate ? parseFloat(hourlyRate) : null,
        installments: parseInt(installments) || 1,
        payment_terms: paymentTerms,
      };
    } else if (contractType === 'procuracao') {
      base.procuracao_detail = {
        powers_type: powersType,
        special_powers: specialPowers,
        court_scope: courtScope,
        is_irrevocable: isIrrevocable,
      };
    } else if (contractType === 'substabelecimento') {
      base.substabelecimento_detail = {
        substabelecido_name: substabelecidoName,
        substabelecido_oab: substabelecidoOab,
        with_reserve: withReserve,
        powers_transferred: powersTransferred,
      };
    }
    return base;
  }

  async function handleGenerate() {
    const payload = buildPayload();
    const result = await generateContract.mutateAsync(payload);
    setPreviewHtml(result.content_html);
    setStep(5);
  }

  async function handleSave() {
    const payload = buildPayload();
    payload.content_html = previewHtml;
    await createContract.mutateAsync(payload as Partial<LegalContract>);
    setOpen(false);
    resetForm();
  }

  const needsDetailStep = ['honorarios', 'procuracao', 'substabelecimento'].includes(contractType);

  return (
    <Dialog open={open} onOpenChange={(v) => { setOpen(v); if (!v) resetForm(); }}>
      <DialogTrigger asChild>
        <Button>
          <FilePlus className="mr-2 h-4 w-4" />
          Novo Contrato
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {step === 1 && 'Selecione o tipo de contrato'}
            {step === 2 && 'Selecione a parte / ente e caso'}
            {step === 3 && 'Preencha os detalhes'}
            {step === 4 && 'Gerando contrato com IA...'}
            {step === 5 && 'Pré-visualização do contrato'}
          </DialogTitle>
          <DialogDescription className="sr-only">Assistente para criação de contrato</DialogDescription>
        </DialogHeader>

        {/* Step 1: Select type or upload */}
        {step === 1 && (
          <div className="space-y-6">
            <div className="text-center p-6 border-2 border-dashed rounded-lg bg-muted/30">
              <Sparkles className="h-10 w-10 mx-auto mb-3 text-primary" />
              <h3 className="font-semibold mb-1">Upload Inteligente de Contrato</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Carregue um contrato existente (PDF/DOCX) e a IA irá extrair automaticamente todos os dados.
              </p>
              <label className="inline-flex items-center gap-2 cursor-pointer">
                <Button asChild variant="outline">
                  <span>
                    <input
                      type="file"
                      accept=".pdf,.docx"
                      className="hidden"
                      onChange={handleFileUpload}
                      disabled={isUploading}
                    />
                    {isUploading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Analisando...
                      </>
                    ) : (
                      <>
                        <FileText className="h-4 w-4 mr-2" />
                        Selecionar Arquivo
                      </>
                    )}
                  </span>
                </Button>
              </label>
            </div>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">Ou crie do zero</span>
              </div>
            </div>

            <div>
              <p className="text-sm font-semibold mb-3 text-center">Selecione o tipo de contrato</p>
              <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-4">
                {CONTRACT_TYPES.map((ct) => {
                  const Icon = ct.icon;
                  return (
                    <button
                      key={ct.value}
                      onClick={() => { setContractType(ct.value); setStep(2); }}
                      className={`flex flex-col items-center gap-2 rounded-lg border-2 p-3 text-center transition-colors hover:border-primary hover:bg-muted/50 ${
                        contractType === ct.value ? 'border-primary bg-muted/50' : 'border-muted'
                      }`}
                    >
                      <Icon className="h-6 w-6 text-muted-foreground" />
                      <span className="font-semibold text-xs">{ct.title}</span>
                      <span className="text-[10px] text-muted-foreground line-clamp-2">{ct.description}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Client + Case */}
        {step === 2 && (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Parte *</Label>
              <Select value={clientId} onValueChange={(v) => { setClientId(v); setCaseId(''); }}>
                <SelectTrigger><SelectValue placeholder="Selecione a parte / ente" /></SelectTrigger>
                <SelectContent>
                  {clients.map((c: any) => (
                    <SelectItem key={c.id} value={String(c.id)}>
                      {c.name} {c.cpf_cnpj ? `(${c.cpf_cnpj})` : ''}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Processo vinculado (opcional)</Label>
              <Select value={caseId || 'none'} onValueChange={(v) => setCaseId(v === 'none' ? '' : v)}>
                <SelectTrigger><SelectValue placeholder="Selecione o processo" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Nenhum</SelectItem>
                  {filteredCases.map((c: any) => (
                    <SelectItem key={c.id} value={String(c.id)}>
                      {c.titulo} {c.numero_processo ? `(${c.numero_processo})` : ''}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Título do contrato</Label>
              <AIInput
                placeholder="Título gerado automaticamente..."
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                setValue={setTitle}
                aiContext="título de contrato jurídico"
                aiObjective="Sugira um título claro e formal para o contrato, incluindo o tipo de contrato e as partes envolvidas"
              />
              <p className="text-xs text-muted-foreground">Título gerado automaticamente com base no tipo, parte e processo selecionados.</p>
            </div>
            <div className="flex justify-between">
              <Button variant="outline" onClick={() => setStep(1)}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Voltar
              </Button>
              {needsDetailStep ? (
                <Button onClick={() => setStep(3)} disabled={!clientId || !title}>
                  Próximo
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              ) : (
                <Button onClick={handleGenerate} disabled={!clientId || !title || generateContract.isPending}>
                  {generateContract.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Sparkles className="mr-2 h-4 w-4" />
                  )}
                  Gerar com IA
                </Button>
              )}
            </div>
          </div>
        )}

        {/* Step 3: Type-specific fields */}
        {step === 3 && (
          <div className="space-y-4">
            {contractType === 'honorarios' && (
              <>
                <div className="space-y-2">
                  <Label>Tipo de Honorário</Label>
                  <Select value={feeType} onValueChange={setFeeType}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="fixed">Fixo</SelectItem>
                      <SelectItem value="hourly">Por hora</SelectItem>
                      <SelectItem value="success">Exito</SelectItem>
                      <SelectItem value="mixed">Misto</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                {(feeType === 'fixed' || feeType === 'mixed') && (
                  <div className="space-y-2">
                    <Label>Valor Fixo (R$)</Label>
                    <Input type="number" placeholder="0,00" value={fixedAmount} onChange={(e) => setFixedAmount(e.target.value)} />
                  </div>
                )}
                {(feeType === 'hourly' || feeType === 'mixed') && (
                  <div className="space-y-2">
                    <Label>Valor por Hora (R$)</Label>
                    <Input type="number" placeholder="0,00" value={hourlyRate} onChange={(e) => setHourlyRate(e.target.value)} />
                  </div>
                )}
                <div className="space-y-2">
                  <Label>Parcelas</Label>
                  <Input type="number" min="1" value={installments} onChange={(e) => setInstallments(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label>Sugestão de Condição de Pagamento</Label>
                  <Select value={selectedPaymentSuggestion} onValueChange={setSelectedPaymentSuggestion}>
                    <SelectTrigger><SelectValue placeholder="Selecione uma sugestão..." /></SelectTrigger>
                    <SelectContent>
                      {PAYMENT_SUGGESTIONS.map((s) => (
                        <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Condições de Pagamento</Label>
                  <Textarea placeholder="Descreva as condições de pagamento..." value={paymentTerms} onChange={(e) => setPaymentTerms(e.target.value)} rows={3} />
                </div>
              </>
            )}

            {contractType === 'procuracao' && (
              <>
                <div className="space-y-2">
                  <Label>Tipo de Poderes</Label>
                  <Select value={powersType} onValueChange={setPowersType}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="general">Gerais</SelectItem>
                      <SelectItem value="special">Especiais</SelectItem>
                      <SelectItem value="both">Gerais e Especiais</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Poderes Especiais</Label>
                  <AITextarea placeholder="Descreva os poderes especiais..." value={specialPowers} onChange={(e) => setSpecialPowers(e.target.value)} setValue={setSpecialPowers} aiContext="poderes especiais de procuração jurídica" aiObjective="Redija os poderes especiais com linguagem jurídica precisa e adequada ao tipo de processo" />
                </div>
                <div className="space-y-2">
                  <Label>Abrangência do Foro</Label>
                  <AIInput placeholder="Ex: Foro da Comarca de São Paulo" value={courtScope} onChange={(e) => setCourtScope(e.target.value)} setValue={setCourtScope} aiContext="abrangência do foro na procuração jurídica" aiObjective="Sugira a abrangência de foro adequada para a procuração, por exemplo: Foro da Comarca de [Cidade], Justiça Federal ou Tribunal específico" />
                </div>
                <div className="flex items-center gap-3">
                  <Switch checked={isIrrevocable} onCheckedChange={setIsIrrevocable} />
                  <Label>Procuração Irrevogavel</Label>
                </div>
              </>
            )}

            {contractType === 'substabelecimento' && (
              <>
                <div className="space-y-2">
                  <Label>Nome do Substabelecido</Label>
                  <AIInput placeholder="Nome completo do procurador" value={substabelecidoName} onChange={(e) => setSubstabelecidoName(e.target.value)} setValue={setSubstabelecidoName} aiContext="nome do procurador substabelecido na procuração municipal" aiObjective="Formate o nome completo do procurador em letras maiúsculas e com ordem direta, conforme padrão jurídico" />
                </div>
                <div className="space-y-2">
                  <Label>OAB do Substabelecido</Label>
                  <Input placeholder="Ex: 123456/SP" value={substabelecidoOab} onChange={(e) => setSubstabelecidoOab(e.target.value)} />
                </div>
                <div className="flex items-center gap-3">
                  <Switch checked={withReserve} onCheckedChange={setWithReserve} />
                  <Label>Com Reserva de Poderes</Label>
                </div>
                <div className="space-y-2">
                  <Label>Poderes Transferidos</Label>
                  <AITextarea placeholder="Descreva os poderes a serem transferidos..." value={powersTransferred} onChange={(e) => setPowersTransferred(e.target.value)} setValue={setPowersTransferred} aiContext="poderes transferidos no substabelecimento de procuração" aiObjective="Redija os poderes a serem transferidos com linguagem jurídica formal e adequada ao substabelecimento" />
                </div>
              </>
            )}

            <div className="flex justify-between">
              <Button variant="outline" onClick={() => setStep(2)}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Voltar
              </Button>
              <Button onClick={handleGenerate} disabled={generateContract.isPending}>
                {generateContract.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="mr-2 h-4 w-4" />
                )}
                Gerar com IA
              </Button>
            </div>
          </div>
        )}

        {/* Step 4: Loading */}
        {step === 4 && (
          <div className="flex flex-col items-center justify-center py-12 gap-4">
            <Loader2 className="h-10 w-10 animate-spin text-primary" />
            <p className="text-muted-foreground">Gerando contrato com inteligência artificial...</p>
          </div>
        )}

        {/* Step 5: Preview + Save */}
        {step === 5 && (
          <div className="space-y-4">
            <div
              className="rounded-lg border p-4 prose prose-sm max-w-none max-h-96 overflow-y-auto"
              dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(previewHtml) }}
            />
            <div className="flex justify-between">
              <Button variant="outline" onClick={() => setStep(needsDetailStep ? 3 : 2)}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Editar Dados
              </Button>
              <Button onClick={handleSave} disabled={createContract.isPending}>
                {createContract.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <CheckCircle2 className="mr-2 h-4 w-4" />
                )}
                Salvar Contrato
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

// ── Contracts Table ──

function ContractsTable({ contracts, isLoading }: { contracts: LegalContract[]; isLoading: boolean }) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (contracts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <FileText className="h-12 w-12 text-muted-foreground mb-4" />
        <p className="text-muted-foreground">Nenhum contrato encontrado.</p>
      </div>
    );
  }

  return (
    <div className="rounded-md border overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Titulo</TableHead>
            <TableHead>Tipo</TableHead>
            <TableHead>Parte</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Data</TableHead>
            <TableHead className="text-right">Ações</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {contracts.map((contract) => (
            <TableRow key={contract.id}>
              <TableCell className="font-medium max-w-[200px] truncate">
                {contract.title}
              </TableCell>
              <TableCell>
                <TypeBadge type={contract.contract_type} />
              </TableCell>
              <TableCell className="max-w-[150px] truncate">
                {contract.client_name}
              </TableCell>
              <TableCell>
                <StatusBadge status={contract.status} />
              </TableCell>
              <TableCell className="text-muted-foreground text-sm">
                {formatDate(contract.created_at)}
              </TableCell>
              <TableCell className="text-right">
                <div className="flex items-center justify-end gap-1">
                  <Button variant="ghost" size="sm" asChild>
                    <Link href={`/dashboard/contratos/${contract.id}`}>
                      <Eye className="h-4 w-4" />
                    </Link>
                  </Button>
                  {contract.status === 'pending_signature' && (
                    <Button variant="ghost" size="sm" asChild>
                      <Link href={`/dashboard/contratos/${contract.id}`}>
                        <PenLine className="h-4 w-4" />
                      </Link>
                    </Button>
                  )}
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

// ── Main Page ──

export default function ContratosPage() {
  const [activeTab, setActiveTab] = useState('all');
  const { data: contracts = [], isLoading } = useContracts();
  const { data: stats } = useContractStats();

  const filtered = useMemo(() => {
    if (activeTab === 'all') return contracts;
    return contracts.filter((c) => c.contract_type === activeTab);
  }, [contracts, activeTab]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold">Contratos Administrativos</h1>
          <p className="text-muted-foreground">
            Gerencie contratos, convênios e instrumentos jurídicos da procuradoria.
          </p>
        </div>
        <NewContractDialog />
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Assinados</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-700">{stats?.signed ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Pendentes</CardTitle>
            <Clock className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-700">{stats?.pending ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Rascunhos</CardTitle>
            <FileText className="h-4 w-4 text-gray-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-600">{stats?.draft ?? 0}</div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs + Table */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="flex-wrap h-auto gap-1">
          <TabsTrigger value="all">Todos</TabsTrigger>
          <TabsTrigger value="honorarios">Termos</TabsTrigger>
          <TabsTrigger value="procuracao">Procurações</TabsTrigger>
          <TabsTrigger value="substabelecimento">Substabelecimentos</TabsTrigger>
          <TabsTrigger value="prestacao_servicos">Serviços</TabsTrigger>
          <TabsTrigger value="consultoria">Consultoria</TabsTrigger>
          <TabsTrigger value="confidencialidade">NDA</TabsTrigger>
          <TabsTrigger value="acordo_extrajudicial">Acordos</TabsTrigger>
        </TabsList>
        <TabsContent value={activeTab}>
          <ContractsTable contracts={filtered} isLoading={isLoading} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
