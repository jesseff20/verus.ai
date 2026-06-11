'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Table,
  TableHeader,
  TableRow,
  TableHead,
  TableBody,
  TableCell,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  FileText,
  Plus,
  Send,
  RefreshCw,
  Eye,
  CheckCircle2,
  Clock,
  XCircle,
  AlertTriangle,
  ArrowRight,
  ExternalLink,
  RotateCcw,
} from 'lucide-react';
import {
  useProtocols,
  useProtocolStats,
  useCreateProtocol,
  useSubmitProtocol,
  useCheckProtocolStatus,
} from '@/hooks/use-protocol';

const STATUS_BADGE: Record<string, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; className?: string; label: string; icon: React.ReactNode }> = {
  draft: { variant: 'secondary', label: 'Rascunho', icon: <FileText className="h-3 w-3" /> },
  pending: { variant: 'outline', className: 'border-yellow-500 text-yellow-700 bg-yellow-50', label: 'Pendente', icon: <Clock className="h-3 w-3" /> },
  submitted: { variant: 'outline', className: 'border-blue-500 text-blue-700 bg-blue-50', label: 'Submetido', icon: <Send className="h-3 w-3" /> },
  accepted: { variant: 'outline', className: 'border-green-500 text-green-700 bg-green-50', label: 'Aceito', icon: <CheckCircle2 className="h-3 w-3" /> },
  rejected: { variant: 'destructive', label: 'Rejeitado', icon: <XCircle className="h-3 w-3" /> },
  error: { variant: 'destructive', label: 'Erro', icon: <AlertTriangle className="h-3 w-3" /> },
};

const COURT_SYSTEMS = [
  { value: 'pje', label: 'PJe' },
  { value: 'esaj', label: 'e-SAJ' },
  { value: 'projudi', label: 'PROJUDI' },
  { value: 'eproc', label: 'e-Proc' },
  { value: 'sei', label: 'SEI' },
];

const PETITION_TYPES = [
  { value: 'inicial', label: 'Petição Inicial' },
  { value: 'contestacao', label: 'Contestação' },
  { value: 'recurso', label: 'Recurso' },
  { value: 'manifestacao', label: 'Manifestação' },
  { value: 'outros', label: 'Outros' },
];

const PETITION_TYPE_LABELS: Record<string, string> = {
  inicial: 'Petição Inicial',
  contestacao: 'Contestação',
  recurso: 'Recurso',
  manifestacao: 'Manifestação',
  outros: 'Outros',
};

function WorkflowSteps({ status }: { status: string }) {
  const steps = [
    { key: 'draft', label: 'Rascunho', icon: FileText },
    { key: 'submitted', label: 'Submetido', icon: Send },
    { key: 'accepted', label: 'Aceito', icon: CheckCircle2 },
  ];

  const statusOrder: Record<string, number> = {
    draft: 0,
    pending: 1,
    submitted: 1,
    accepted: 2,
    rejected: 2,
    error: -1,
  };

  const currentStep = statusOrder[status] ?? -1;
  const isRejected = status === 'rejected';
  const isError = status === 'error';

  return (
    <div className="flex items-center gap-1">
      {steps.map((step, i) => {
        const StepIcon = step.icon;
        const isCompleted = currentStep > i;
        const isCurrent = currentStep === i;
        const isFailed = isCurrent && (isRejected || isError);

        return (
          <div key={step.key} className="flex items-center gap-1">
            <div
              className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium transition-colors ${
                isFailed
                  ? 'bg-red-100 text-red-700 ring-1 ring-red-300'
                  : isCompleted
                    ? 'bg-green-100 text-green-700'
                    : isCurrent
                      ? 'bg-blue-100 text-blue-700 ring-1 ring-blue-300'
                      : 'bg-muted text-muted-foreground'
              }`}
            >
              <StepIcon className="h-3 w-3" />
              <span className="hidden sm:inline">{step.label}</span>
            </div>
            {i < steps.length - 1 && (
              <ArrowRight className={`h-3 w-3 ${isCompleted ? 'text-green-500' : 'text-muted-foreground/40'}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}

export default function ProtocoloPage() {
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [courtFilter, setCourtFilter] = useState<string>('all');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [detailId, setDetailId] = useState<string | null>(null);

  // Form state
  const [formCase, setFormCase] = useState('');
  const [formPetitionType, setFormPetitionType] = useState('');
  const [formCourtSystem, setFormCourtSystem] = useState('');

  const filters: Record<string, string> = {};
  if (statusFilter !== 'all') filters.status = statusFilter;
  if (courtFilter !== 'all') filters.court_system = courtFilter;

  const { data: protocols, isLoading } = useProtocols(Object.keys(filters).length > 0 ? filters : undefined);
  const { data: stats, isLoading: isLoadingStats } = useProtocolStats();
  const createProtocol = useCreateProtocol();
  const submitProtocol = useSubmitProtocol();
  const checkStatus = useCheckProtocolStatus();

  const handleCreate = async () => {
    if (!formCase || !formPetitionType || !formCourtSystem) return;
    await createProtocol.mutateAsync({
      case: formCase,
      petition_type: formPetitionType,
      court_system: formCourtSystem,
    });
    setFormCase('');
    setFormPetitionType('');
    setFormCourtSystem('');
    setDialogOpen(false);
  };

  const detailProtocol = detailId ? protocols?.find((p) => p.id === detailId) : null;

  // Calculate acceptance rate
  const total = stats?.total ?? 0;
  const accepted = stats?.accepted ?? 0;
  const acceptanceRate = total > 0 ? Math.round((accepted / total) * 100) : 0;

  if (isLoading || isLoadingStats) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Protocolo Eletrônico</h1>
          <p className="text-muted-foreground">Carregando dados...</p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-32" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold">Protocolo Eletrônico</h1>
            <p className="text-muted-foreground">
              Gerencie protocolos eletrônicos de peticoes nos tribunais
            </p>
          </div>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Novo Protocolo
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Novo Protocolo Eletrônico</DialogTitle>
                <DialogDescription>Preencha os dados para criar um novo protocolo de petição eletrônica.</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 pt-4">
                <div className="space-y-2">
                  <Label>Caso (ID)</Label>
                  <Input
                    placeholder="ID do caso"
                    value={formCase}
                    onChange={(e) => setFormCase(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Tipo de Petição</Label>
                  <Select value={formPetitionType} onValueChange={setFormPetitionType}>
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione o tipo" />
                    </SelectTrigger>
                    <SelectContent>
                      {PETITION_TYPES.map((pt) => (
                        <SelectItem key={pt.value} value={pt.value}>
                          {pt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Sistema do Tribunal</Label>
                  <Select value={formCourtSystem} onValueChange={setFormCourtSystem}>
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione o sistema" />
                    </SelectTrigger>
                    <SelectContent>
                      {COURT_SYSTEMS.map((cs) => (
                        <SelectItem key={cs.value} value={cs.value}>
                          {cs.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button
                  className="w-full"
                  onClick={handleCreate}
                  disabled={createProtocol.isPending || !formCase || !formPetitionType || !formCourtSystem}
                >
                  {createProtocol.isPending ? 'Criando...' : 'Criar Protocolo'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {/* Stats Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Total Protocolos</CardTitle>
              <FileText className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.total ?? 0}</div>
              <p className="text-xs text-muted-foreground mt-1">Todos os registros</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Pendentes</CardTitle>
              <Clock className="h-4 w-4 text-yellow-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-700">{stats?.pending ?? 0}</div>
              <p className="text-xs text-muted-foreground mt-1">Aguardando resposta</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Submetidos</CardTitle>
              <Send className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-700">{stats?.submitted ?? 0}</div>
              <p className="text-xs text-muted-foreground mt-1">Enviados ao tribunal</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Aceitos</CardTitle>
              <CheckCircle2 className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-700">{stats?.accepted ?? 0}</div>
              <p className="text-xs text-muted-foreground mt-1">Protocolados com sucesso</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Rejeitados</CardTitle>
              <XCircle className="h-4 w-4 text-red-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-700">{stats?.rejected ?? 0}</div>
              <p className="text-xs text-muted-foreground mt-1">Necessitam revisao</p>
            </CardContent>
          </Card>
        </div>

        {/* Acceptance Rate */}
        {total > 0 && (
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Taxa de aceitacao</span>
                <span className="text-sm font-bold">{acceptanceRate}%</span>
              </div>
              <Progress value={acceptanceRate} className="h-2" />
              <p className="text-xs text-muted-foreground mt-2">
                {accepted} de {total} protocolos aceitos
              </p>
            </CardContent>
          </Card>
        )}

        {/* Filters */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
              <div className="space-y-1.5 w-full sm:w-48">
                <Label className="text-xs font-medium text-muted-foreground">Status</Label>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="Filtrar por status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos os Status</SelectItem>
                    <SelectItem value="draft">Rascunho</SelectItem>
                    <SelectItem value="pending">Pendente</SelectItem>
                    <SelectItem value="submitted">Submetido</SelectItem>
                    <SelectItem value="accepted">Aceito</SelectItem>
                    <SelectItem value="rejected">Rejeitado</SelectItem>
                    <SelectItem value="error">Erro</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5 w-full sm:w-48">
                <Label className="text-xs font-medium text-muted-foreground">Sistema do Tribunal</Label>
                <Select value={courtFilter} onValueChange={setCourtFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="Filtrar por sistema" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos os Sistemas</SelectItem>
                    {COURT_SYSTEMS.map((cs) => (
                      <SelectItem key={cs.value} value={cs.value}>
                        {cs.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {(statusFilter !== 'all' || courtFilter !== 'all') && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setStatusFilter('all');
                    setCourtFilter('all');
                  }}
                  className="text-muted-foreground"
                >
                  <RotateCcw className="mr-1 h-3 w-3" />
                  Limpar filtros
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Protocols Table */}
        <Card>
          <CardHeader>
            <CardTitle>Protocolos</CardTitle>
            <CardDescription>
              {protocols?.length ?? 0} protocolo(s) encontrado(s)
              {statusFilter !== 'all' || courtFilter !== 'all' ? ' com os filtros aplicados' : ''}
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>N. Protocolo</TableHead>
                    <TableHead>Caso</TableHead>
                    <TableHead>Tipo Petição</TableHead>
                    <TableHead>Sistema</TableHead>
                    <TableHead>Progresso</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Criado em</TableHead>
                    <TableHead>Última atualização</TableHead>
                    <TableHead className="text-right">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(!protocols || protocols.length === 0) ? (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center text-muted-foreground py-12">
                        <div className="flex flex-col items-center gap-2">
                          <FileText className="h-8 w-8 text-muted-foreground/50" />
                          <span>Nenhum protocolo encontrado.</span>
                          <Button variant="outline" size="sm" onClick={() => setDialogOpen(true)}>
                            <Plus className="mr-1 h-3 w-3" />
                            Criar primeiro protocolo
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : (
                    protocols.map((protocol) => {
                      const badge = STATUS_BADGE[protocol.status] ?? { variant: 'secondary' as const, label: protocol.status_display || protocol.status, icon: null };
                      return (
                        <TableRow key={protocol.id} className="group">
                          <TableCell className="font-mono text-sm">
                            {protocol.protocol_number ? (
                              <span className="bg-muted px-2 py-0.5 rounded text-xs">
                                {protocol.protocol_number}
                              </span>
                            ) : (
                              <span className="text-muted-foreground">---</span>
                            )}
                          </TableCell>
                          <TableCell>
                            <div className="max-w-[200px]">
                              <div className="font-medium truncate">
                                {protocol.case_titulo || '-'}
                              </div>
                              {protocol.case_numero_processo && (
                                <div className="text-xs text-muted-foreground truncate flex items-center gap-1">
                                  <ExternalLink className="h-3 w-3 flex-shrink-0" />
                                  {protocol.case_numero_processo}
                                </div>
                              )}
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className="font-normal">
                              {PETITION_TYPE_LABELS[protocol.petition_type] || protocol.petition_type}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge variant="secondary" className="font-mono text-xs">
                              {protocol.court_system_display || protocol.court_system?.toUpperCase()}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <WorkflowSteps status={protocol.status} />
                          </TableCell>
                          <TableCell>
                            <Badge variant={badge.variant} className={`${badge.className ?? ''} gap-1`}>
                              {badge.icon}
                              {badge.label}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-sm text-muted-foreground whitespace-nowrap">
                            {new Date(protocol.created_at).toLocaleDateString('pt-BR', {
                              day: '2-digit',
                              month: '2-digit',
                              year: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </TableCell>
                          <TableCell className="text-sm text-muted-foreground whitespace-nowrap">
                            {protocol.submitted_at
                              ? new Date(protocol.submitted_at).toLocaleDateString('pt-BR', {
                                  day: '2-digit',
                                  month: '2-digit',
                                  year: 'numeric',
                                  hour: '2-digit',
                                  minute: '2-digit',
                                })
                              : '-'}
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex items-center justify-end gap-1">
                              {protocol.status === 'draft' && (
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={() => submitProtocol.mutate(protocol.id)}
                                      disabled={submitProtocol.isPending}
                                      className="gap-1"
                                    >
                                      <Send className="h-3.5 w-3.5" />
                                      <span className="hidden lg:inline">Submeter</span>
                                    </Button>
                                  </TooltipTrigger>
                                  <TooltipContent>Submeter protocolo ao tribunal</TooltipContent>
                                </Tooltip>
                              )}
                              {['submitted', 'pending'].includes(protocol.status) && (
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={() => checkStatus.mutate(protocol.id)}
                                      disabled={checkStatus.isPending}
                                      className="gap-1"
                                    >
                                      <RefreshCw className={`h-3.5 w-3.5 ${checkStatus.isPending ? 'animate-spin' : ''}`} />
                                      <span className="hidden lg:inline">Verificar Status</span>
                                    </Button>
                                  </TooltipTrigger>
                                  <TooltipContent>Verificar status no tribunal</TooltipContent>
                                </Tooltip>
                              )}
                              {(protocol.status === 'rejected' || protocol.status === 'error') && (
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={() => submitProtocol.mutate(protocol.id)}
                                      disabled={submitProtocol.isPending}
                                      className="gap-1 border-orange-300 text-orange-700 hover:bg-orange-50"
                                    >
                                      <RotateCcw className="h-3.5 w-3.5" />
                                      <span className="hidden lg:inline">Reenviar</span>
                                    </Button>
                                  </TooltipTrigger>
                                  <TooltipContent>Reenviar protocolo ao tribunal</TooltipContent>
                                </Tooltip>
                              )}
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setDetailId(protocol.id)}
                                  >
                                    <Eye className="h-3.5 w-3.5" />
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent>Ver detalhes</TooltipContent>
                              </Tooltip>
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {/* Detail Dialog */}
        <Dialog open={!!detailId} onOpenChange={(open) => !open && setDetailId(null)}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Detalhes do Protocolo</DialogTitle>
              <DialogDescription>Informações detalhadas do protocolo eletrônico.</DialogDescription>
            </DialogHeader>
            {detailProtocol && (
              <div className="space-y-4 pt-2">
                {/* Workflow visualization in detail */}
                <div>
                  <Label className="text-xs text-muted-foreground">Progresso do protocolo</Label>
                  <div className="mt-2">
                    <WorkflowSteps status={detailProtocol.status} />
                  </div>
                </div>

                <Separator />

                <div className="space-y-3 text-sm">
                  <div className="grid grid-cols-2 gap-2">
                    <span className="text-muted-foreground">N. Protocolo:</span>
                    <span className="font-mono">
                      {detailProtocol.protocol_number ? (
                        <Badge variant="outline" className="font-mono">{detailProtocol.protocol_number}</Badge>
                      ) : (
                        <span className="text-muted-foreground">---</span>
                      )}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <span className="text-muted-foreground">Caso:</span>
                    <div>
                      <span className="font-medium">{detailProtocol.case_titulo || '-'}</span>
                      {detailProtocol.case_numero_processo && (
                        <div className="text-xs text-muted-foreground">{detailProtocol.case_numero_processo}</div>
                      )}
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <span className="text-muted-foreground">Tipo Petição:</span>
                    <span>{PETITION_TYPE_LABELS[detailProtocol.petition_type] || detailProtocol.petition_type}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <span className="text-muted-foreground">Sistema:</span>
                    <Badge variant="secondary" className="w-fit font-mono text-xs">
                      {detailProtocol.court_system_display || detailProtocol.court_system}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <span className="text-muted-foreground">Status:</span>
                    <Badge
                      variant={STATUS_BADGE[detailProtocol.status]?.variant ?? 'secondary'}
                      className={`${STATUS_BADGE[detailProtocol.status]?.className ?? ''} w-fit gap-1`}
                    >
                      {STATUS_BADGE[detailProtocol.status]?.icon}
                      {STATUS_BADGE[detailProtocol.status]?.label ?? detailProtocol.status_display}
                    </Badge>
                  </div>

                  <Separator />

                  <div className="grid grid-cols-2 gap-2">
                    <span className="text-muted-foreground">Criado por:</span>
                    <span>{detailProtocol.created_by_name || '-'}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <span className="text-muted-foreground">Criado em:</span>
                    <span>{new Date(detailProtocol.created_at).toLocaleString('pt-BR')}</span>
                  </div>
                  {detailProtocol.submitted_at && (
                    <div className="grid grid-cols-2 gap-2">
                      <span className="text-muted-foreground">Submetido em:</span>
                      <span>{new Date(detailProtocol.submitted_at).toLocaleString('pt-BR')}</span>
                    </div>
                  )}
                  {detailProtocol.accepted_at && (
                    <div className="grid grid-cols-2 gap-2">
                      <span className="text-muted-foreground">Aceito em:</span>
                      <span className="text-green-700 font-medium">{new Date(detailProtocol.accepted_at).toLocaleString('pt-BR')}</span>
                    </div>
                  )}
                  {detailProtocol.protocol_receipt && (
                    <div className="grid grid-cols-2 gap-2">
                      <span className="text-muted-foreground">Recibo:</span>
                      <span className="font-mono text-xs break-all bg-muted p-1.5 rounded">{detailProtocol.protocol_receipt}</span>
                    </div>
                  )}
                  {detailProtocol.error_message && (
                    <div className="rounded-md bg-red-50 border border-red-200 p-3 text-red-700 text-sm">
                      <div className="flex items-center gap-2 mb-1">
                        <AlertTriangle className="h-4 w-4" />
                        <span className="font-medium">Erro</span>
                      </div>
                      {detailProtocol.error_message}
                    </div>
                  )}
                  {detailProtocol.retry_count > 0 && (
                    <div className="grid grid-cols-2 gap-2">
                      <span className="text-muted-foreground">Tentativas:</span>
                      <Badge variant="outline" className="w-fit">{detailProtocol.retry_count}</Badge>
                    </div>
                  )}
                </div>

                {/* Quick actions in detail dialog */}
                {(detailProtocol.status === 'draft' || detailProtocol.status === 'rejected' || detailProtocol.status === 'error' || detailProtocol.status === 'submitted' || detailProtocol.status === 'pending') && (
                  <>
                    <Separator />
                    <div className="flex gap-2">
                      {detailProtocol.status === 'draft' && (
                        <Button
                          size="sm"
                          onClick={() => {
                            submitProtocol.mutate(detailProtocol.id);
                            setDetailId(null);
                          }}
                          disabled={submitProtocol.isPending}
                          className="gap-1"
                        >
                          <Send className="h-3.5 w-3.5" />
                          Submeter Protocolo
                        </Button>
                      )}
                      {['submitted', 'pending'].includes(detailProtocol.status) && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => checkStatus.mutate(detailProtocol.id)}
                          disabled={checkStatus.isPending}
                          className="gap-1"
                        >
                          <RefreshCw className={`h-3.5 w-3.5 ${checkStatus.isPending ? 'animate-spin' : ''}`} />
                          Verificar Status
                        </Button>
                      )}
                      {(detailProtocol.status === 'rejected' || detailProtocol.status === 'error') && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            submitProtocol.mutate(detailProtocol.id);
                            setDetailId(null);
                          }}
                          disabled={submitProtocol.isPending}
                          className="gap-1 border-orange-300 text-orange-700 hover:bg-orange-50"
                        >
                          <RotateCcw className="h-3.5 w-3.5" />
                          Reenviar
                        </Button>
                      )}
                    </div>
                  </>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </TooltipProvider>
  );
}
