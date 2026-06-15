'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { SafeContent } from '@/components/ui/safe-content';
import {
  FileText,
  FileDown,
  Loader2,
  AlertCircle,
  Edit3,
  Calendar,
} from 'lucide-react';
import { useAttachmentPreview } from '@/hooks/use-attachment-preview';
import api from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface AttachmentPreviewModalProps {
  /** UUID da sessao do anexo a visualizar. Quando null, modal nao renderiza. */
  sessionId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type DownloadKind = 'pdf' | 'docx' | 'odt';

const DOWNLOAD_LABELS: Record<DownloadKind, string> = {
  pdf: 'PDF',
  docx: 'DOCX',
  odt: 'ODT',
};

const DOWNLOAD_MIME: Record<DownloadKind, string> = {
  pdf: 'application/pdf',
  docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  odt: 'application/vnd.oasis.opendocument.text',
};

/**
 * Modal de visualização de um anexo a partir do preview do ETP/TR.
 *
 * Le sections + URLs do R2 do backend (`GET /sessions/<id>/preview/`).
 * Cada secao vem com HTML formatado (`SectionGeneration.content`) - mesma
 * fonte do ResultPhase, garantindo render identico.
 *
 * Downloads PDF/DOCX/ODT usam POST + blob URL, porque os endpoints
 * `/documents/<id>/generate-<kind>/` exigem POST (regeram on-the-fly se
 * o R2 ainda nao tem o arquivo).
 */
export function AttachmentPreviewModal({
  sessionId,
  open,
  onOpenChange,
}: AttachmentPreviewModalProps) {
  const router = useRouter();
  const { toast } = useToast();
  const { preview, isLoading, error } = useAttachmentPreview(sessionId, open);
  const [downloadingKind, setDownloadingKind] = useState<DownloadKind | null>(null);

  const handleGoToEdit = () => {
    if (!sessionId) return;
    onOpenChange(false);
    router.push(`/dashboard/intelligent-assistant/anexos?session=${sessionId}`);
  };

  const handleDownload = async (kind: DownloadKind) => {
    if (!preview?.generated_doc_id) return;
    setDownloadingKind(kind);
    try {
      const response = await api.post(
        `/api/v1/intelligent-assistant/documents/${preview.generated_doc_id}/generate-${kind}/`,
        {},
        { responseType: 'blob' },
      );
      const blob = new Blob([response.data], { type: DOWNLOAD_MIME[kind] });
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = `${preview.document_type || 'documento'}.${kind}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(blobUrl);
    } catch (err: any) {
      toast({
        title: `Erro ao baixar ${DOWNLOAD_LABELS[kind]}`,
        description: err?.response?.data?.error || err?.message || 'Tente novamente.',
        variant: 'destructive',
      });
    } finally {
      setDownloadingKind(null);
    }
  };

  // Para PDF/DOCX: se ja temos URL R2 publica, link direto resolve. Senao,
  // POST + blob download via handleDownload(kind).
  const renderDownloadButton = (kind: DownloadKind) => {
    if (!preview?.generated_doc_id) return null;

    const isLoadingThis = downloadingKind === kind;
    const directUrl =
      (kind === 'pdf' && preview.pdf_url) ||
      (kind === 'docx' && preview.docx_url) ||
      null;

    if (directUrl) {
      return (
        <Button asChild variant="outline" size="sm" className="rounded-xl" key={kind}>
          <a href={directUrl} target="_blank" rel="noopener noreferrer">
            <FileDown className="h-4 w-4 mr-1" />
            {DOWNLOAD_LABELS[kind]}
          </a>
        </Button>
      );
    }

    return (
      <Button
        key={kind}
        variant="outline"
        size="sm"
        className="rounded-xl"
        disabled={isLoadingThis}
        onClick={() => handleDownload(kind)}
      >
        {isLoadingThis ? (
          <Loader2 className="h-4 w-4 mr-1 animate-spin" />
        ) : (
          <FileDown className="h-4 w-4 mr-1" />
        )}
        {DOWNLOAD_LABELS[kind]}
      </Button>
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-lg">
            <FileText className="h-5 w-5 text-slate-500" />
            {preview?.document_type_display || 'Anexo'}
          </DialogTitle>
          <DialogDescription className="sr-only">Visualizar prévia do documento anexo</DialogDescription>
          {/* DialogDescription e <p>; nao pode conter <div> (Badge). Usa div manual. */}
          <div className="text-sm text-muted-foreground flex items-center gap-2 flex-wrap mt-1">
            {preview?.status && (
              <Badge variant="outline" className="text-[10px]">
                {preview.status}
              </Badge>
            )}
            {preview?.generated_at && (
              <span className="flex items-center gap-1 text-xs">
                <Calendar className="h-3 w-3" />
                {new Date(preview.generated_at).toLocaleDateString('pt-BR')}
              </span>
            )}
            {preview?.objective && (
              <span className="text-xs text-muted-foreground truncate max-w-md">
                · {preview.objective.slice(0, 100)}
                {preview.objective.length > 100 ? '…' : ''}
              </span>
            )}
          </div>
        </DialogHeader>

        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
            <span className="ml-2 text-sm text-muted-foreground">
              Carregando preview…
            </span>
          </div>
        )}

        {!!error && !isLoading && (
          <div className="flex flex-col items-center justify-center py-12 gap-2">
            <AlertCircle className="h-8 w-8 text-red-400" />
            <p className="text-sm text-muted-foreground">
              Erro ao carregar preview do anexo.
            </p>
          </div>
        )}

        {!isLoading && !error && preview && !preview.has_generated_doc && (
          <div className="flex flex-col items-center justify-center py-12 gap-3 text-center">
            <FileText className="h-12 w-12 text-slate-300" />
            <p className="text-sm text-slate-600 font-medium">
              Documento ainda não foi gerado
            </p>
            <p className="text-xs text-muted-foreground max-w-md">
              Este anexo está em rascunho. Continue a edição para fazer upload
              de documentos de referência e gerar o conteúdo.
            </p>
            <Button onClick={handleGoToEdit} className="mt-2">
              <Edit3 className="h-4 w-4 mr-1.5" />
              Ir para edição
            </Button>
          </div>
        )}

        {!isLoading && !error && preview?.has_generated_doc && (
          <>
            <div className="flex items-center gap-2 flex-wrap pb-3 border-b border-slate-100">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                Baixar
              </span>
              {renderDownloadButton('pdf')}
              {renderDownloadButton('docx')}
              {renderDownloadButton('odt')}
            </div>

            <div className="flex-1 overflow-y-auto pt-3 space-y-6">
              {preview.sections.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">
                  Nenhuma seção com conteúdo gerado.
                </p>
              ) : (
                preview.sections.map((s) => (
                  <div key={s.section_number} className="scroll-mt-4">
                    <h3 className="text-base font-bold text-foreground mb-3 flex items-center gap-2">
                      <span className="text-foreground/30">
                        {String(s.section_number).padStart(2, '0')}
                      </span>
                      {s.section_name}
                    </h3>
                    <SafeContent
                      content={s.content}
                      className="text-foreground leading-relaxed prose-p:text-sm prose-li:text-sm prose-headings:text-base"
                    />
                  </div>
                ))
              )}
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}

export default AttachmentPreviewModal;
