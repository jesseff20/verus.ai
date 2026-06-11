'use client';

import { use } from 'react';
import DOMPurify from 'isomorphic-dompurify';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Calendar,
  User,
  FileText,
  Scale,
  ScrollText,
  Users,
  Loader2,
} from 'lucide-react';
import {
  useContract,
  useMarkContractSigned,
  useUpdateContract,
} from '@/hooks/use-contracts';

// ── Helpers ──

const statusConfig: Record<string, { label: string; className: string }> = {
  draft: { label: 'Rascunho', className: 'bg-gray-100 text-gray-700 border-gray-200' },
  pending_signature: { label: 'Pendente de Assinatura', className: 'bg-yellow-100 text-yellow-800 border-yellow-200' },
  signed: { label: 'Assinado', className: 'bg-green-100 text-green-800 border-green-200' },
  cancelled: { label: 'Cancelado', className: 'bg-red-100 text-red-700 border-red-200' },
};

const typeConfig: Record<string, { label: string; icon: typeof Scale }> = {
  honorarios: { label: 'Contrato de Honorários', icon: Scale },
  procuracao: { label: 'Procuração', icon: ScrollText },
  substabelecimento: { label: 'Substabelecimento', icon: Users },
};

function formatDate(iso: string | null) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('pt-BR');
}

function formatCurrency(value: number | null) {
  if (value === null || value === undefined) return '—';
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

// ── Page ──

export default function ContratoDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: contract, isLoading, error } = useContract(id);
  const markSigned = useMarkContractSigned();
  const updateContract = useUpdateContract();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (error || !contract) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" asChild>
          <Link href="/dashboard/contratos">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Voltar
          </Link>
        </Button>
        <p className="text-red-600">Erro ao carregar contrato. Verifique se o contrato existe.</p>
      </div>
    );
  }

  const statusCfg = statusConfig[contract.status] ?? { label: contract.status, className: '' };
  const typeCfg = typeConfig[contract.contract_type] ?? { label: contract.contract_type_display, icon: FileText };
  const TypeIcon = typeCfg.icon;

  async function handleSign() {
    await markSigned.mutateAsync(contract!.id);
  }

  async function handleCancel() {
    await updateContract.mutateAsync({
      id: contract!.id,
      data: { status: 'cancelled' },
    });
  }

  return (
    <div className="space-y-6">
      {/* Back + Actions */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <Button variant="ghost" asChild>
          <Link href="/dashboard/contratos">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Voltar aos Contratos
          </Link>
        </Button>
        <div className="flex gap-2">
          {(contract.status === 'draft' || contract.status === 'pending_signature') && (
            <Button onClick={handleSign} disabled={markSigned.isPending}>
              {markSigned.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <CheckCircle2 className="mr-2 h-4 w-4" />
              )}
              Marcar como Assinado
            </Button>
          )}
          {contract.status !== 'cancelled' && contract.status !== 'signed' && (
            <Button variant="destructive" onClick={handleCancel} disabled={updateContract.isPending}>
              {updateContract.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <XCircle className="mr-2 h-4 w-4" />
              )}
              Cancelar Contrato
            </Button>
          )}
        </div>
      </div>

      {/* Metadata Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <TypeIcon className="h-6 w-6 text-muted-foreground" />
            <div>
              <CardTitle>{contract.title}</CardTitle>
              <CardDescription>{typeCfg.label}</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Status</p>
              <Badge variant="outline" className={statusCfg.className}>{statusCfg.label}</Badge>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground flex items-center gap-1">
                <User className="h-3 w-3" /> Cliente
              </p>
              <p className="text-sm font-medium">{contract.client_name}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Processo</p>
              <p className="text-sm font-medium">{contract.case_titulo ?? '—'}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Criado por</p>
              <p className="text-sm font-medium">{contract.created_by_name}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground flex items-center gap-1">
                <Calendar className="h-3 w-3" /> Criado em
              </p>
              <p className="text-sm font-medium">{formatDate(contract.created_at)}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Assinado em</p>
              <p className="text-sm font-medium">{formatDate(contract.signed_at)}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Expira em</p>
              <p className="text-sm font-medium">{formatDate(contract.expires_at)}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Type-specific Details */}
      {contract.honorarios_detail && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Scale className="h-5 w-5" />
              Detalhes dos Honorários
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Tipo de Honorário</p>
                <p className="text-sm font-medium capitalize">{contract.honorarios_detail.fee_type}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Valor Fixo</p>
                <p className="text-sm font-medium">{formatCurrency(contract.honorarios_detail.fixed_amount)}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Valor por Hora</p>
                <p className="text-sm font-medium">{formatCurrency(contract.honorarios_detail.hourly_rate)}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Percentual de Êxito</p>
                <p className="text-sm font-medium">
                  {contract.honorarios_detail.success_percentage != null
                    ? `${contract.honorarios_detail.success_percentage}%`
                    : '—'}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Parcelas</p>
                <p className="text-sm font-medium">{contract.honorarios_detail.installments}x</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Condições de Pagamento</p>
                <p className="text-sm font-medium">{contract.honorarios_detail.payment_terms || '—'}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {contract.procuracao_detail && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <ScrollText className="h-5 w-5" />
              Detalhes da Procuração
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Tipo de Poderes</p>
                <p className="text-sm font-medium capitalize">{contract.procuracao_detail.powers_type}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Abrangência do Foro</p>
                <p className="text-sm font-medium">{contract.procuracao_detail.court_scope || '—'}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Irrevogável</p>
                <p className="text-sm font-medium">{contract.procuracao_detail.is_irrevocable ? 'Sim' : 'Não'}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Válida até</p>
                <p className="text-sm font-medium">{formatDate(contract.procuracao_detail.valid_until)}</p>
              </div>
              {contract.procuracao_detail.special_powers && (
                <div className="space-y-1 sm:col-span-2">
                  <p className="text-sm text-muted-foreground">Poderes Especiais</p>
                  <p className="text-sm font-medium whitespace-pre-wrap">{contract.procuracao_detail.special_powers}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {contract.substabelecimento_detail && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Users className="h-5 w-5" />
              Detalhes do Substabelecimento
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Nome do Substabelecido</p>
                <p className="text-sm font-medium">{contract.substabelecimento_detail.substabelecido_name}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">OAB</p>
                <p className="text-sm font-medium">
                  {contract.substabelecimento_detail.substabelecido_oab}
                  {contract.substabelecimento_detail.substabelecido_oab_state && `/${contract.substabelecimento_detail.substabelecido_oab_state}`}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Com Reserva</p>
                <p className="text-sm font-medium">{contract.substabelecimento_detail.with_reserve ? 'Sim' : 'Não'}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Motivo</p>
                <p className="text-sm font-medium">{contract.substabelecimento_detail.reason || '—'}</p>
              </div>
              {contract.substabelecimento_detail.powers_transferred && (
                <div className="space-y-1 sm:col-span-2">
                  <p className="text-sm text-muted-foreground">Poderes Transferidos</p>
                  <p className="text-sm font-medium whitespace-pre-wrap">{contract.substabelecimento_detail.powers_transferred}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Contract Content */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Conteúdo do Contrato
          </CardTitle>
        </CardHeader>
        <Separator />
        <CardContent className="pt-6">
          {contract.content_html ? (
            <div
              className="prose prose-sm max-w-none"
              dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(contract.content_html) }}
            />
          ) : (
            <p className="text-muted-foreground text-center py-8">
              Nenhum conteúdo gerado para este contrato.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
