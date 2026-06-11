'use client';

import { useState } from 'react';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  PenTool,
  CheckCircle2,
  XCircle,
  Shield,
  Search,
  FileSignature,
  Clock,
  Eye,
  ExternalLink,
  Settings,
  AlertCircle,
  Copy,
  Fingerprint,
  Lock,
  FileEdit,
  Landmark,
  Hash,
  Server,
  Key,
  QrCode,
  Award,
  ShieldCheck,
  Info,
  XOctagon,
  RefreshCw,
} from 'lucide-react';
import {
  useMySignatures,
  useSignDocument,
  useVerifySignature,
  type DigitalSignatureDto,
} from '@/hooks/useSignature';
import { AIInput } from '@/components/ui/ai-input';
import { AITextarea } from '@/components/ui/ai-textarea';

const DOCUMENT_TYPES = [
  { value: 'despacho', label: 'Despacho' },
  { value: 'parecer', label: 'Parecer' },
  { value: 'peticao', label: 'Petição' },
  { value: 'ata', label: 'Ata' },
  { value: 'contrato', label: 'Contrato' },
  { value: 'outro', label: 'Outro' },
];

const PROVIDERS_LIST = [
  { value: 'internal', label: 'Protocolo Verus.AI' },
  { value: 'd4sign', label: 'D4Sign (ICP-Brasil)' },
  { value: 'docusign', label: 'DocuSign' },
  { value: 'govbr', label: 'GOV.BR' },
];

const PROVIDERS = [
  {
    id: 'd4sign',
    name: 'D4Sign',
    description: 'Assinatura digital jurídica com validade legal no Brasil.',
    icon: <Lock className="h-6 w-6 text-blue-600" />,
    color: 'border-blue-200 bg-blue-50/30',
    activeColor: 'border-blue-500 bg-blue-50',
    features: ['Assinatura com certificado digital', 'API de integração', 'Envio via WhatsApp/Email'],
    setupSteps: [
      '1. Acesse d4sign.com.br e crie uma conta',
      '2. Obtenha o Token API e o CryptoKey no painel',
      '3. Configure em Configurações > Integrações > D4Sign',
      '4. Insira o Token API e a CryptoKey',
    ],
  },
  {
    id: 'docusign',
    name: 'DocuSign',
    description: 'Plataforma global de assinatura eletrônica e gestão de contratos.',
    icon: <FileEdit className="h-6 w-6 text-purple-600" />,
    color: 'border-purple-200 bg-purple-50/30',
    activeColor: 'border-purple-500 bg-purple-50',
    features: ['Reconhecimento internacional', 'Fluxos de aprovação', 'Templates de documentos'],
    setupSteps: [
      '1. Acesse docusign.com e crie uma conta developer',
      '2. Crie um aplicativo em Settings > Integrations',
      '3. Copie o Integration Key e o Secret Key',
      '4. Configure em Configurações > Integrações > DocuSign',
    ],
  },
  {
    id: 'govbr',
    name: 'GOV.BR',
    description: 'Assinatura digital governamental com certificado ICP-Brasil.',
    icon: <Landmark className="h-6 w-6 text-green-600" />,
    color: 'border-green-200 bg-green-50/30',
    activeColor: 'border-green-500 bg-green-50',
    features: ['Validade jurídica plena', 'Certificado ICP-Brasil', 'Integração gov.br'],
    setupSteps: [
      '1. Acesse assinador.iti.br com sua conta GOV.BR',
      '2. Obtenha certificado digital ICP-Brasil (e-CPF/e-CNPJ)',
      '3. Instale o certificado no navegador',
      '4. Configure em Configurações > Integrações > GOV.BR',
    ],
  },
];

const STATUS_CONFIG: Record<DigitalSignatureDto['status'], { label: string; variant: string; icon: React.ReactNode }> = {
  pending: { label: 'Pendente', variant: 'outline', icon: <Clock className="h-3 w-3" /> },
  signed: { label: 'Assinado', variant: 'success', icon: <CheckCircle2 className="h-3 w-3" /> },
  rejected: { label: 'Rejeitado', variant: 'destructive', icon: <XCircle className="h-3 w-3" /> },
  expired: { label: 'Expirado', variant: 'secondary', icon: <XOctagon className="h-3 w-3" /> },
  revoked: { label: 'Revogado', variant: 'destructive', icon: <XOctagon className="h-3 w-3" /> },
};

function ProviderCard({
  provider,
  isConfigured,
  onSetup,
}: {
  provider: typeof PROVIDERS[0];
  isConfigured: boolean;
  onSetup: () => void;
}) {
  return (
    <Card className={`transition-all ${isConfigured ? provider.activeColor : provider.color}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted/50">
              {provider.icon}
            </div>
            <div>
              <CardTitle className="text-base">{provider.name}</CardTitle>
              <CardDescription className="text-xs mt-0.5">{provider.description}</CardDescription>
            </div>
          </div>
          {isConfigured ? (
            <Badge variant="outline" className="border-green-500 text-green-700 bg-green-50 gap-1">
              <CheckCircle2 className="h-3 w-3" />
              Configurado
            </Badge>
          ) : (
            <Badge variant="outline" className="border-gray-300 text-gray-500 gap-1">
              <AlertCircle className="h-3 w-3" />
              Não configurado
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="flex flex-wrap gap-1.5 mb-3">
          {provider.features.map((feature) => (
            <Badge key={feature} variant="secondary" className="text-xs font-normal">
              {feature}
            </Badge>
          ))}
        </div>
        {!isConfigured && (
          <Button variant="outline" size="sm" onClick={onSetup} className="w-full gap-1">
            <Settings className="h-3.5 w-3.5" />
            Configurar {provider.name}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

function SignatureTimeline({ signature }: { signature: DigitalSignatureDto }) {
  const signedDate = signature.signed_at ? new Date(signature.signed_at) : new Date(signature.created_at);
  const isSigned = signature.status === 'signed';

  const steps = [
    {
      label: 'Solicitação criada',
      time: new Date(signature.created_at).toLocaleString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
      date: new Date(signature.created_at).toLocaleDateString('pt-BR'),
      completed: true,
      icon: <FileSignature className="h-3.5 w-3.5" />,
    },
    {
      label: isSigned ? 'Assinatura aplicada' : 'Assinatura pendente',
      time: signedDate.toLocaleString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
      date: signedDate.toLocaleDateString('pt-BR'),
      completed: isSigned,
      icon: <PenTool className="h-3.5 w-3.5" />,
    },
    {
      label: isSigned ? 'Verificação concluída' : STATUS_CONFIG[signature.status]?.label ?? signature.status,
      time: signedDate.toLocaleString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
      date: signedDate.toLocaleDateString('pt-BR'),
      completed: isSigned,
      icon: isSigned ? <CheckCircle2 className="h-3.5 w-3.5" /> : <XCircle className="h-3.5 w-3.5" />,
      status: isSigned ? 'success' : 'error',
    },
  ];

  return (
    <div className="space-y-0">
      {steps.map((step, i) => (
        <div key={i} className="flex gap-3">
          <div className="flex flex-col items-center">
            <div className={`flex h-7 w-7 items-center justify-center rounded-full border-2 ${
              step.status === 'error'
                ? 'border-red-500 bg-red-50 text-red-600'
                : step.status === 'success'
                  ? 'border-green-500 bg-green-50 text-green-600'
                  : step.completed
                    ? 'border-blue-500 bg-blue-50 text-blue-600'
                    : 'border-gray-300 bg-gray-50 text-gray-400'
            }`}>
              {step.icon}
            </div>
            {i < steps.length - 1 && (
              <div className={`w-0.5 h-6 ${step.completed ? 'bg-blue-300' : 'bg-gray-200'}`} />
            )}
          </div>
          <div className="pb-4 pt-0.5">
            <p className="text-sm font-medium">{step.label}</p>
            <p className="text-xs text-muted-foreground">{step.date} às {step.time}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function AssinaturaDigitalPage() {
  const { data: signatures, isLoading } = useMySignatures();
  const signDocument = useSignDocument();
  const verifyMutation = useVerifySignature();

  // Sign dialog state
  const [signDialogOpen, setSignDialogOpen] = useState(false);
  const [signDocumentRef, setSignDocumentRef] = useState('');
  const [signDocumentTitle, setSignDocumentTitle] = useState('');
  const [signDocType, setSignDocType] = useState('despacho');
  const [signContent, setSignContent] = useState('');
  const [signProvider, setSignProvider] = useState('internal');

  // Setup dialog state
  const [setupDialogOpen, setSetupDialogOpen] = useState(false);
  const [setupProvider, setSetupProvider] = useState<typeof PROVIDERS[0] | null>(null);

  // Timeline dialog state
  const [timelineDialogOpen, setTimelineDialogOpen] = useState(false);
  const [timelineSig, setTimelineSig] = useState<DigitalSignatureDto | null>(null);

  // Verify state
  const [verifyId, setVerifyId] = useState('');

  // For demo purposes, no providers are configured yet
  const configuredProviders: string[] = [];

  const pendingSignatures = signatures?.filter(s => s.status !== 'signed') ?? [];
  const validSignatures = signatures?.filter(s => s.status === 'signed') ?? [];

  const handleSign = () => {
    if (!signDocumentRef.trim() || !signContent.trim()) {
      toast.error('Preencha a referência do documento e o conteúdo.');
      return;
    }
    signDocument.mutate(
      {
        content: signContent.trim(),
        document_type: signDocType,
        document_ref: signDocumentRef.trim(),
        document_title: signDocumentTitle.trim() || undefined,
        provider: signProvider,
      },
      {
        onSuccess: () => {
          setSignDialogOpen(false);
          setSignDocumentRef('');
          setSignDocumentTitle('');
          setSignContent('');
          setSignDocType('despacho');
          setSignProvider('internal');
        },
      }
    );
  };

  const handleVerify = () => {
    if (!verifyId.trim()) {
      toast.error('Informe o ID da assinatura.');
      return;
    }
    verifyMutation.mutate(verifyId.trim());
  };

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold">Assinatura Digital</h1>
            <p className="text-muted-foreground">Gerencie e verifique assinaturas digitais de documentos</p>
          </div>
          <Button onClick={() => setSignDialogOpen(true)}>
            <PenTool className="mr-2 h-4 w-4" />
            Assinar Documento
          </Button>
        </div>

        {/* Provider Status Cards */}
        <div>
          <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Provedores de Assinatura
          </h2>
          <div className="grid gap-4 md:grid-cols-3">
            {PROVIDERS.map((provider) => (
              <ProviderCard
                key={provider.id}
                provider={provider}
                isConfigured={configuredProviders.includes(provider.id)}
                onSetup={() => {
                  setSetupProvider(provider);
                  setSetupDialogOpen(true);
                }}
              />
            ))}
          </div>
        </div>

        {/* Protocolo Verus.AI */}
        <Card className="border-indigo-200 bg-indigo-50/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-indigo-900">
              <ShieldCheck className="h-5 w-5 text-indigo-600" />
              Protocolo Verus.AI
            </CardTitle>
            <CardDescription>
              Protocolo interno de assinatura digital do Verus.AI. Funciona sem provedores externos, utilizando criptografia própria do sistema.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5 mb-6">
              <div className="flex items-start gap-3 rounded-lg border bg-background p-3">
                <Hash className="h-5 w-5 text-indigo-600 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm font-medium">Hash SHA-256</p>
                  <p className="text-xs text-muted-foreground">Hash criptográfico do documento para garantir integridade</p>
                </div>
              </div>
              <div className="flex items-start gap-3 rounded-lg border bg-background p-3">
                <Server className="h-5 w-5 text-indigo-600 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm font-medium">Timestamp do Servidor</p>
                  <p className="text-xs text-muted-foreground">Carimbo de tempo do servidor para prova temporal</p>
                </div>
              </div>
              <div className="flex items-start gap-3 rounded-lg border bg-background p-3">
                <Key className="h-5 w-5 text-indigo-600 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm font-medium">Chave do Usuário</p>
                  <p className="text-xs text-muted-foreground">Assinatura com chave criptográfica única do usuário</p>
                </div>
              </div>
              <div className="flex items-start gap-3 rounded-lg border bg-background p-3">
                <QrCode className="h-5 w-5 text-indigo-600 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm font-medium">QR Code de Verificação</p>
                  <p className="text-xs text-muted-foreground">QR Code para verificação rápida da autenticidade</p>
                </div>
              </div>
              <div className="flex items-start gap-3 rounded-lg border bg-background p-3">
                <Award className="h-5 w-5 text-indigo-600 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm font-medium">Certificado de Autenticidade</p>
                  <p className="text-xs text-muted-foreground">Certificado gerado pelo sistema com dados da assinatura</p>
                </div>
              </div>
            </div>

            <Separator className="my-4" />

            <div>
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <Info className="h-4 w-4 text-muted-foreground" />
                Protocolos de Assinatura Suportados
              </h3>
              <div className="grid gap-2 sm:grid-cols-2">
                <div className="flex items-start gap-3 rounded-lg border p-3">
                  <Lock className="h-4 w-4 text-blue-600 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium">ICP-Brasil (A1/A3)</p>
                    <p className="text-xs text-muted-foreground">Via D4Sign — Certificado digital ICP-Brasil para assinaturas qualificadas com validade jurídica plena.</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 rounded-lg border p-3">
                  <Landmark className="h-4 w-4 text-green-600 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium">Assinatura Eletrônica Avançada</p>
                    <p className="text-xs text-muted-foreground">Via GOV.BR — Autenticação governamental com nível avançado de segurança e certificado ICP-Brasil.</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 rounded-lg border p-3">
                  <FileEdit className="h-4 w-4 text-purple-600 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium">Assinatura Eletrônica Simples</p>
                    <p className="text-xs text-muted-foreground">Via DocuSign — Assinatura eletrônica com reconhecimento internacional para documentos de menor risco.</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 rounded-lg border border-indigo-200 bg-indigo-50/30 p-3">
                  <ShieldCheck className="h-4 w-4 text-indigo-600 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium">Protocolo Verus.AI</p>
                    <p className="text-xs text-muted-foreground">Interno — Hash SHA-256, timestamp, chave do usuário, QR Code e certificado de autenticidade gerado pelo sistema.</p>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Stats row */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Total Assinaturas</CardTitle>
              <Fingerprint className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{signatures?.length ?? 0}</div>
              <p className="text-xs text-muted-foreground mt-1">Documentos assinados</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Válidas</CardTitle>
              <CheckCircle2 className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-700">{validSignatures.length}</div>
              <p className="text-xs text-muted-foreground mt-1">Assinaturas verificadas</p>
            </CardContent>
          </Card>
          <Card className={pendingSignatures.length > 0 ? 'border-yellow-200 bg-yellow-50/30' : ''}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Pendentes/Inválidas</CardTitle>
              <Clock className="h-4 w-4 text-yellow-600" />
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${pendingSignatures.length > 0 ? 'text-yellow-700' : 'text-muted-foreground'}`}>
                {pendingSignatures.length}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {pendingSignatures.length > 0 ? 'Requerem atenção' : 'Nenhuma pendência'}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Pending signatures alert */}
        {pendingSignatures.length > 0 && (
          <Card className="border-yellow-300 bg-yellow-50/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2 text-yellow-800">
                <AlertCircle className="h-5 w-5" />
                Documentos com assinatura pendente ou inválida
              </CardTitle>
              <CardDescription>
                {pendingSignatures.length} documento(s) com assinatura pendente ou inválida
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-2">
                {pendingSignatures.slice(0, 5).map((sig) => (
                  <div key={sig.id} className="flex items-center justify-between rounded-lg border bg-background p-3">
                    <div className="flex items-center gap-3">
                      <XCircle className="h-4 w-4 text-red-500 flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium">{sig.document_title || sig.document_ref}</p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(sig.created_at).toLocaleDateString('pt-BR')} — {sig.provider_label}
                        </p>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1"
                      onClick={() => {
                        setTimelineSig(sig);
                        setTimelineDialogOpen(true);
                      }}
                    >
                      <Eye className="h-3 w-3" />
                      Ver
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* My Signatures Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileSignature className="h-5 w-5" />
              Minhas Assinaturas
            </CardTitle>
            <CardDescription>
              {signatures?.length ?? 0} documento(s) assinado(s) digitalmente
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : !signatures || signatures.length === 0 ? (
              <div className="text-center py-12">
                <FileSignature className="h-10 w-10 text-muted-foreground/40 mx-auto mb-3" />
                <p className="text-muted-foreground mb-1">Nenhuma assinatura digital registrada.</p>
                <p className="text-xs text-muted-foreground mb-4">Clique em &quot;Assinar Documento&quot; para começar.</p>
                <Button variant="outline" size="sm" onClick={() => setSignDialogOpen(true)}>
                  <PenTool className="mr-1 h-3 w-3" />
                  Assinar primeiro documento
                </Button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Documento</TableHead>
                      <TableHead>Provedor</TableHead>
                      <TableHead>Hash</TableHead>
                      <TableHead>Data</TableHead>
                      <TableHead className="text-center">Status</TableHead>
                      <TableHead className="text-right">Ações</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {signatures.map((sig) => {
                      const statusCfg = STATUS_CONFIG[sig.status];
                      return (
                        <TableRow key={sig.id}>
                          <TableCell className="font-medium max-w-[250px] truncate">
                            {sig.document_title || sig.document_ref}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className="font-normal">
                              {sig.provider_label}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {sig.content_hash ? (
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="font-mono text-xs h-7 px-2"
                                    onClick={() => {
                                      navigator.clipboard.writeText(sig.content_hash);
                                      toast.success('Hash copiado!');
                                    }}
                                  >
                                    <Copy className="h-3 w-3 mr-1" />
                                    {sig.content_hash.slice(0, 12)}...
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent className="font-mono text-xs max-w-[300px] break-all">
                                  {sig.content_hash}
                                </TooltipContent>
                              </Tooltip>
                            ) : (
                              <span className="text-muted-foreground text-xs">—</span>
                            )}
                          </TableCell>
                          <TableCell className="text-sm whitespace-nowrap">
                            {new Date(sig.created_at).toLocaleDateString('pt-BR', {
                              day: '2-digit',
                              month: '2-digit',
                              year: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </TableCell>
                          <TableCell className="text-center">
                            <Badge
                              variant="outline"
                              className={`gap-1 ${
                                sig.status === 'signed'
                                  ? 'border-green-500 text-green-700 bg-green-50'
                                  : sig.status === 'pending'
                                    ? 'border-yellow-500 text-yellow-700 bg-yellow-50'
                                    : 'border-red-500 text-red-700 bg-red-50'
                              }`}
                            >
                              {statusCfg?.icon}
                              {statusCfg?.label ?? sig.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => {
                                    setTimelineSig(sig);
                                    setTimelineDialogOpen(true);
                                  }}
                                >
                                  <Clock className="h-3.5 w-3.5" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>Ver linha do tempo</TooltipContent>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Verify Signature */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="h-5 w-5" />
              Verificar Assinatura
            </CardTitle>
            <CardDescription>Verifique a autenticidade de uma assinatura digital pelo ID</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="flex-1">
                <Input
                  placeholder="ID da assinatura (UUID)"
                  value={verifyId}
                  onChange={(e) => {
                    setVerifyId(e.target.value);
                    verifyMutation.reset();
                  }}
                />
              </div>
              <Button onClick={handleVerify} disabled={verifyMutation.isPending}>
                {verifyMutation.isPending ? (
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Search className="mr-2 h-4 w-4" />
                )}
                {verifyMutation.isPending ? 'Verificando...' : 'Verificar'}
              </Button>
            </div>

            {verifyMutation.data && (
              <div className={`mt-4 rounded-lg border-2 p-4 ${
                verifyMutation.data.valid
                  ? 'border-green-300 bg-green-50'
                  : 'border-red-300 bg-red-50'
              }`}>
                <div className="flex items-center gap-3 mb-3">
                  <div className={`rounded-full p-2 ${
                    verifyMutation.data.valid ? 'bg-green-100' : 'bg-red-100'
                  }`}>
                    {verifyMutation.data.valid ? (
                      <CheckCircle2 className="h-6 w-6 text-green-600" />
                    ) : (
                      <XCircle className="h-6 w-6 text-red-600" />
                    )}
                  </div>
                  <div>
                    <span className={`font-semibold text-lg ${
                      verifyMutation.data.valid ? 'text-green-700' : 'text-red-700'
                    }`}>
                      {verifyMutation.data.valid ? 'Assinatura Válida' : 'Assinatura Inválida'}
                    </span>
                    <p className="text-sm text-muted-foreground">{verifyMutation.data.reason}</p>
                  </div>
                </div>
                {verifyMutation.data.signature && (
                  <>
                    <Separator className="my-3" />
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <span className="text-muted-foreground">Assinante:</span>
                      <span className="font-medium">{verifyMutation.data.signature.signer_name}</span>
                      <span className="text-muted-foreground">Provedor:</span>
                      <Badge variant="outline" className="w-fit text-xs">{verifyMutation.data.signature.provider_label}</Badge>
                      <span className="text-muted-foreground">Data:</span>
                      <span>{verifyMutation.data.signature.created_at ? new Date(verifyMutation.data.signature.created_at).toLocaleString('pt-BR') : '—'}</span>
                    </div>
                  </>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Sign Document Dialog */}
        <Dialog open={signDialogOpen} onOpenChange={setSignDialogOpen}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Assinar Documento</DialogTitle>
              <DialogDescription>
                Preencha as informações do documento e selecione o provedor de assinatura.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>Tipo de Documento</Label>
                  <Select value={signDocType} onValueChange={setSignDocType}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {DOCUMENT_TYPES.map((t) => (
                        <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Provedor</Label>
                  <Select value={signProvider} onValueChange={setSignProvider}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {PROVIDERS_LIST.map((p) => (
                        <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Referência do Documento <span className="text-muted-foreground text-xs">(ID/UUID)</span></Label>
                <AIInput
                  placeholder="ex: uuid-do-despacho-ou-processo"
                  value={signDocumentRef}
                  onChange={(e) => setSignDocumentRef(e.target.value)}
                  setValue={setSignDocumentRef}
                  aiContext="referência/UUID do documento jurídico a ser assinado"
                  aiObjective="Formate o identificador do documento no padrão UUID ou referência adotada pelo sistema"
                />
              </div>
              <div className="space-y-2">
                <Label>Título <span className="text-muted-foreground text-xs">(opcional)</span></Label>
                <AIInput
                  placeholder="Breve descrição do documento..."
                  value={signDocumentTitle}
                  onChange={(e) => setSignDocumentTitle(e.target.value)}
                  setValue={setSignDocumentTitle}
                  aiContext="título do documento jurídico a ser assinado digitalmente"
                  aiObjective="Sugira um título claro e conciso para o documento jurídico"
                />
              </div>
              <div className="space-y-2">
                <Label>Conteúdo a Assinar</Label>
                <AITextarea
                  rows={5}
                  placeholder="Cole ou digite o conteúdo do documento que será assinado..."
                  value={signContent}
                  onChange={(e) => setSignContent(e.target.value)}
                  setValue={setSignContent}
                  aiContext="conteúdo de documento jurídico a ser assinado digitalmente"
                  aiObjective="Revise e melhore o texto jurídico: corrija erros de português, melhore a clareza e adeque ao padrão formal de documentos jurídicos brasileiros"
                  className="min-h-[100px]"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setSignDialogOpen(false)}>
                Cancelar
              </Button>
              <Button onClick={handleSign} disabled={signDocument.isPending}>
                <PenTool className="mr-2 h-4 w-4" />
                {signDocument.isPending ? 'Assinando...' : 'Assinar'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Setup Provider Dialog */}
        <Dialog open={setupDialogOpen} onOpenChange={setSetupDialogOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Configurar {setupProvider?.name}
              </DialogTitle>
              <DialogDescription>
                Siga os passos abaixo para configurar a integração com {setupProvider?.name}.
              </DialogDescription>
            </DialogHeader>
            {setupProvider && (
              <div className="space-y-4 pt-2">
                <div className="flex items-center gap-3 rounded-lg border bg-muted/30 p-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-muted/50">
                    {setupProvider.icon}
                  </div>
                  <div>
                    <p className="font-medium">{setupProvider.name}</p>
                    <p className="text-xs text-muted-foreground">{setupProvider.description}</p>
                  </div>
                </div>

                <Separator />

                <div>
                  <h4 className="text-sm font-semibold mb-3">Passos para configuração</h4>
                  <div className="space-y-2">
                    {setupProvider.setupSteps.map((step, i) => (
                      <div key={i} className="flex gap-3 text-sm">
                        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold flex-shrink-0">
                          {i + 1}
                        </div>
                        <p className="pt-0.5">{step.replace(/^\d+\.\s*/, '')}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <Separator />

                <div className="flex gap-2">
                  <Button variant="outline" className="flex-1" onClick={() => setSetupDialogOpen(false)}>
                    Fechar
                  </Button>
                  <Button className="flex-1 gap-1">
                    <ExternalLink className="h-3.5 w-3.5" />
                    Ir para Configurações
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Timeline Dialog */}
        <Dialog open={timelineDialogOpen} onOpenChange={setTimelineDialogOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Linha do Tempo da Assinatura</DialogTitle>
              <DialogDescription>
                Histórico completo do processo de assinatura digital.
              </DialogDescription>
            </DialogHeader>
            {timelineSig && (
              <div className="space-y-4 pt-2">
                <div className="rounded-lg border bg-muted/30 p-3">
                  <p className="text-sm font-medium">{timelineSig.document_title || timelineSig.document_ref}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="outline" className="text-xs">
                      {timelineSig.provider_label}
                    </Badge>
                    {timelineSig.status === 'signed' ? (
                      <Badge variant="outline" className="border-green-500 text-green-700 bg-green-50 text-xs gap-1">
                        <CheckCircle2 className="h-3 w-3" />
                        Válida
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="border-red-500 text-red-700 bg-red-50 text-xs gap-1">
                        <XCircle className="h-3 w-3" />
                        {STATUS_CONFIG[timelineSig.status]?.label ?? timelineSig.status}
                      </Badge>
                    )}
                  </div>
                </div>

                <SignatureTimeline signature={timelineSig} />

                {timelineSig.content_hash && (
                  <div className="rounded-lg border bg-muted/30 p-3">
                    <p className="text-xs text-muted-foreground mb-1">Hash do conteúdo</p>
                    <div className="flex items-center gap-2">
                      <code className="text-xs font-mono flex-1 break-all select-all bg-background rounded px-2 py-1 border">
                        {timelineSig.content_hash}
                      </code>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              navigator.clipboard.writeText(timelineSig.content_hash);
                              toast.success('Hash copiado!');
                            }}
                          >
                            <Copy className="h-3.5 w-3.5" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>Copiar hash</TooltipContent>
                      </Tooltip>
                    </div>
                  </div>
                )}
              </div>
            )}
            <DialogFooter>
              <Button variant="outline" onClick={() => setTimelineDialogOpen(false)}>Fechar</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </TooltipProvider>
  );
}
