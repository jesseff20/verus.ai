'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Paperclip,
  Eye,
  Loader2,
  ChevronLeft,
  ChevronRight,
  PlusCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useSessionAttachments } from '@/hooks/use-session-attachments';
import { AttachmentPreviewModal } from './AttachmentPreviewModal';

// Codes de anexo de cada categoria - espelha as whitelists do backend e
// do SessionSidebar. Usado pra colorir tag "Pre-contratacao" vs
// "Em contratacao".
const ATTACHMENT_CODES_ETP = new Set([
  'especificacoes_tecnicas',
  'poc',
  'catalogo_servicos',
  'mapa_riscos',
]);
const ATTACHMENT_CODES_TR = new Set([
  'ordem_servico',
  'recebimento_provisorio',
  'recebimento_definitivo',
  'confidencialidade',
  'composicao_lances',
]);

interface AttachmentsListProps {
  /** UUID da sessao pai. Sem ela, o componente nao renderiza. */
  sessionId: string | null | undefined;
  /** Tipo da sessao pai. Decide o CTA de "criar". */
  parentDocumentType?: string | null;
}

/**
 * Lista visual de anexos vinculados a uma sessao pai.
 *
 * Renderiza no `ResultPhase` (ou em qualquer preview onde o user veja
 * o documento gerado). Mostra tag de fase do anexo, status, data, e
 * botao "Abrir" que navega pra /anexos?session=<id>.
 *
 * Lista vem paginada do backend (10 por pagina por padrao).
 * Estado vazio inclui CTA pra criar primeiro anexo.
 */
export function AttachmentsList({ sessionId, parentDocumentType }: AttachmentsListProps) {
  const router = useRouter();
  const [page, setPage] = useState(1);
  const [previewSessionId, setPreviewSessionId] = useState<string | null>(null);

  const {
    attachments,
    total,
    totalPages,
    hasNext,
    hasPrevious,
    isLoading,
  } = useSessionAttachments(sessionId, page, 10);

  if (!sessionId) return null;

  const handleOpenAttachment = (id: string) => {
    // Em vez de navegar pra outra rota com 4 query params (session/phase/doc/
    // generation_session), abre modal inline que le markdown + URLs do R2
    // direto do banco. Mais simples, sem coreografia de URL.
    setPreviewSessionId(id);
  };

  const handleCreateAttachment = () => {
    // /anexos lista todos os anexos - wizard genérico funciona para qualquer tipo.
    // Bug anterior mandava TR pra /tr (mesma rota onde o user ja estava) e o
    // Next.js ignorava a navegacao.
    router.push('/dashboard/intelligent-assistant/anexos');
  };

  return (
    <>
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Paperclip className="h-5 w-5 text-slate-500" />
          Anexos vinculados {total > 0 && <span className="text-slate-400 font-normal">({total})</span>}
        </CardTitle>
        <CardDescription>
          Documentos auxiliares deste documento.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Carregando…
          </div>
        ) : attachments.length === 0 ? (
          <div className="text-center py-8 space-y-3">
            <p className="text-sm text-slate-500">Nenhum anexo vinculado.</p>
            <Button
              variant="outline"
              size="sm"
              onClick={handleCreateAttachment}
              className="mx-auto"
            >
              <PlusCircle className="h-4 w-4 mr-1.5" />
              Criar anexo
            </Button>
          </div>
        ) : (
          <>
            <ul className="space-y-2">
              {attachments.map((att) => {
                const isEtpAttach = ATTACHMENT_CODES_ETP.has(att.document_type);
                const isTrAttach = ATTACHMENT_CODES_TR.has(att.document_type);
                const date = new Date(att.created_at).toLocaleDateString('pt-BR');
                return (
                  <li
                    key={att.id}
                    className={cn(
                      'flex items-center gap-3 p-3 rounded-xl border transition-colors',
                      isEtpAttach && 'bg-blue-50/40 border-blue-100 hover:bg-blue-50/70',
                      isTrAttach && 'bg-orange-50/40 border-orange-100 hover:bg-orange-50/70',
                      !isEtpAttach && !isTrAttach && 'bg-slate-50 border-slate-100 hover:bg-slate-100',
                    )}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium text-sm text-slate-800 truncate">
                          {att.document_type_display}
                        </span>
                        {isEtpAttach && (
                          <Badge className="text-[10px] bg-blue-100 text-blue-700 border-blue-200 border hover:bg-blue-200">
                            Pré-contratação
                          </Badge>
                        )}
                        {isTrAttach && (
                          <Badge className="text-[10px] bg-orange-100 text-orange-700 border-orange-200 border hover:bg-orange-200">
                            Em contratação
                          </Badge>
                        )}
                        <Badge variant="outline" className="text-[10px]">
                          {att.status}
                        </Badge>
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5 truncate">
                        {date} · {att.objective_preview || 'Sem objetivo'}
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleOpenAttachment(att.id)}
                      className="flex-shrink-0"
                    >
                      <Eye className="h-3.5 w-3.5 mr-1" />
                      Visualizar
                    </Button>
                  </li>
                );
              })}
            </ul>

            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-100">
                <p className="text-xs text-slate-500">
                  Página {page} de {totalPages}
                </p>
                <div className="flex items-center gap-1">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!hasPrevious}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!hasNext}
                    onClick={() => setPage((p) => p + 1)}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>

    <AttachmentPreviewModal
      sessionId={previewSessionId}
      open={!!previewSessionId}
      onOpenChange={(open) => {
        if (!open) setPreviewSessionId(null);
      }}
    />
    </>
  );
}

export default AttachmentsList;
