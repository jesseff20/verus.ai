'use client';

import { useState } from 'react';
import DOMPurify from 'isomorphic-dompurify';
import {
  useClientPortalContracts,
  useClientPortalSignContract,
} from '@/hooks/use-client-portal';
import type { ClientContract } from '@/hooks/use-client-portal';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  FileText,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  PenLine,
} from 'lucide-react';

// ─── Helpers ────────────────────────────────────────────────────────────────

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '\u2014';
  return new Date(dateStr).toLocaleDateString('pt-BR');
}

const TYPE_COLORS: Record<string, string> = {
  honorarios: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300',
  procuracao: 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300',
  substabelecimento: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300',
};

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-600 dark:bg-gray-800/40 dark:text-gray-400',
  pending_signature: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300',
  signed: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300',
};

const STATUS_LABELS: Record<string, string> = {
  draft: 'Rascunho',
  pending_signature: 'Aguardando Assinatura',
  signed: 'Assinado',
};

// ─── Component ──────────────────────────────────────────────────────────────

export default function ContratosPage() {
  const { data: contracts, isLoading, error } = useClientPortalContracts();
  const signMutation = useClientPortalSignContract();

  const [signDialogOpen, setSignDialogOpen] = useState(false);
  const [selectedContract, setSelectedContract] = useState<ClientContract | null>(null);
  const [agreed, setAgreed] = useState(false);
  const [signSuccess, setSignSuccess] = useState<{ hash: string } | null>(null);

  const handleOpenSign = (contract: ClientContract) => {
    setSelectedContract(contract);
    setAgreed(false);
    setSignSuccess(null);
    setSignDialogOpen(true);
  };

  const handleSign = async () => {
    if (!selectedContract || !agreed) return;
    try {
      const result = await signMutation.mutateAsync(selectedContract.id);
      setSignSuccess({ hash: result.signature_hash || 'assinatura-registrada' });
    } catch {
      // error handled by mutation
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight flex items-center gap-2">
          <FileText className="h-7 w-7 sm:h-8 sm:w-8" />
          Meus Contratos
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Visualize e assine seus contratos
        </p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <div className="flex items-center justify-center py-16 text-destructive gap-2">
          <AlertTriangle className="h-5 w-5" />
          <span>Erro ao carregar contratos</span>
        </div>
      ) : !contracts || contracts.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground gap-3">
          <FileText className="h-12 w-12 opacity-30" />
          <p className="text-sm">Nenhum contrato encontrado</p>
        </div>
      ) : (
        <div className="space-y-3">
          {contracts.map((contract) => (
            <Collapsible key={contract.id}>
              <Card>
                <CollapsibleTrigger asChild>
                  <CardHeader className="cursor-pointer hover:bg-accent/30 transition-colors">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <CardTitle className="text-base">{contract.titulo}</CardTitle>
                        <div className="flex items-center gap-2 mt-2 flex-wrap">
                          <Badge className={`text-[10px] ${TYPE_COLORS[contract.tipo] || 'bg-gray-100 text-gray-800'}`}>
                            {contract.tipo_display}
                          </Badge>
                          <Badge className={`text-[10px] ${STATUS_COLORS[contract.status] || STATUS_COLORS.draft}`}>
                            {STATUS_LABELS[contract.status] || contract.status_display}
                          </Badge>
                          <span className="text-[11px] text-muted-foreground">
                            Criado em {formatDate(contract.created_at)}
                          </span>
                        </div>
                      </div>
                      <ChevronDown className="h-5 w-5 text-muted-foreground shrink-0 mt-1" />
                    </div>
                  </CardHeader>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <CardContent className="pt-0">
                    {/* Rendered HTML content */}
                    {contract.content_html && (
                      <div
                        className="prose prose-sm dark:prose-invert max-w-none border rounded-lg p-4 bg-muted/30 mb-4"
                        dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(contract.content_html) }}
                      />
                    )}

                    {/* Signature action */}
                    {contract.status === 'pending_signature' && (
                      <Button onClick={() => handleOpenSign(contract)}>
                        <PenLine className="h-4 w-4 mr-1" />
                        Assinar Digitalmente
                      </Button>
                    )}

                    {contract.status === 'signed' && (
                      <div className="flex items-center gap-2 text-sm text-green-600">
                        <CheckCircle2 className="h-4 w-4" />
                        <span>Assinado em {formatDate(contract.signed_at)}</span>
                        {contract.signature_hash && (
                          <span className="text-xs font-mono text-muted-foreground ml-2">
                            Hash: {contract.signature_hash.slice(0, 16)}...
                          </span>
                        )}
                      </div>
                    )}
                  </CardContent>
                </CollapsibleContent>
              </Card>
            </Collapsible>
          ))}
        </div>
      )}

      {/* Sign Dialog */}
      <Dialog open={signDialogOpen} onOpenChange={setSignDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Assinar Contrato</DialogTitle>
            <DialogDescription>
              Ao assinar, você confirma que leu e concorda com os termos deste contrato.
            </DialogDescription>
          </DialogHeader>

          {signSuccess ? (
            <div className="space-y-4 py-4">
              <div className="flex flex-col items-center gap-3 text-center">
                <CheckCircle2 className="h-12 w-12 text-green-600" />
                <h3 className="font-semibold text-lg">Contrato Assinado com Sucesso</h3>
                <p className="text-sm text-muted-foreground">
                  Hash da assinatura:
                </p>
                <code className="text-xs font-mono bg-muted p-2 rounded break-all">
                  {signSuccess.hash}
                </code>
              </div>
              <DialogFooter>
                <Button onClick={() => setSignDialogOpen(false)}>Fechar</Button>
              </DialogFooter>
            </div>
          ) : (
            <div className="space-y-4">
              {selectedContract && (
                <p className="text-sm">
                  <strong>Contrato:</strong> {selectedContract.titulo}
                </p>
              )}
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="agree-terms"
                  checked={agreed}
                  onCheckedChange={(checked) => setAgreed(checked === true)}
                />
                <label htmlFor="agree-terms" className="text-sm cursor-pointer">
                  Li e concordo com todos os termos
                </label>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setSignDialogOpen(false)}>
                  Cancelar
                </Button>
                <Button
                  onClick={handleSign}
                  disabled={!agreed || signMutation.isPending}
                >
                  {signMutation.isPending && <Loader2 className="h-4 w-4 mr-1 animate-spin" />}
                  Assinar
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
