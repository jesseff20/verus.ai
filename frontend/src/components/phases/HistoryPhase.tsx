'use client';

import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  History,
  FileText,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Download,
  Trash2,
  Loader2,
  Eye,
} from 'lucide-react';
import { useMemo } from 'react';
import { formatDate, formatDateTime } from '@/lib/utils';

interface HistoryDocument {
  id: string;
  title: string;
  document_type: string;
  status: string;
  created_at: string;
  updated_at: string;
  pdf_url?: string;
  docx_url?: string;
  odt_url?: string;
}

interface HistoryPhaseProps {
  sessionDetail: {
    id: string;
    generated_documents?: HistoryDocument[];
    objective?: string;
    [key: string]: any;
  } | null;
  totalSections: number;
  onLoadDocument: (doc: any) => Promise<void>;
  onDeleteDocument: (documentId: string) => void;
  className?: string;
}

export function HistoryPhase({
  sessionDetail,
  totalSections,
  onLoadDocument,
  onDeleteDocument,
  className,
}: HistoryPhaseProps) {
  const documents = sessionDetail?.generated_documents || [];

  const sortedDocs = useMemo(() => {
    return [...documents].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
  }, [documents]);

  const StatusIcon = ({ status }: { status: string }) => {
    switch (status) {
      case 'completed':
      case 'ready':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'generating':
      case 'processing':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
    }
  };

  const StatusBadge = ({ status }: { status: string }) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning'> = {
      completed: 'success',
      ready: 'success',
      generating: 'secondary',
      processing: 'secondary',
      failed: 'destructive',
      draft: 'outline',
    };

    const labels: Record<string, string> = {
      completed: 'Concluído',
      ready: 'Pronto',
      generating: 'Gerando',
      processing: 'Processando',
      failed: 'Falhou',
      draft: 'Rascunho',
    };

    return (
      <Badge variant={variants[status] || 'outline'} className="text-[10px]">
        {labels[status] || status}
      </Badge>
    );
  };

  if (documents.length === 0) {
    return (
      <div className={cn('text-center py-12', className)}>
        <History className="h-12 w-12 mx-auto mb-3 text-muted-foreground" />
        <h3 className="text-lg font-medium mb-1">Nenhum Documento Gerado</h3>
        <p className="text-sm text-muted-foreground">
          Os documentos gerados nesta sessão aparecerão aqui.
        </p>
      </div>
    );
  }

  return (
    <div className={cn('space-y-4', className)}>
      <h2 className="text-lg font-semibold flex items-center gap-2">
        <History className="h-5 w-5 text-primary" />
        Histórico de Documentos
      </h2>

      <ScrollArea className="h-[calc(100vh-250px)]">
        <div className="space-y-3">
          {sortedDocs.map((doc) => (
            <Card key={doc.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-4">
                  {/* Document Info */}
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <FileText className="h-4 w-4 text-primary shrink-0" />
                      <h3 className="text-sm font-medium truncate">
                        {doc.title || 'Documento sem título'}
                      </h3>
                      <StatusBadge status={doc.status} />
                    </div>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatDateTime(doc.created_at)}
                      </span>
                      <span>Tipo: {doc.document_type}</span>
                      <span>
                        {totalSections} seções
                      </span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-1 shrink-0">
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-8 text-xs gap-1"
                      onClick={() => onLoadDocument(doc)}
                    >
                      <Eye className="h-3 w-3" />
                      Visualizar
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-8 w-8 text-muted-foreground hover:text-destructive"
                      onClick={() => onDeleteDocument(doc.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                {/* Download links */}
                {(doc.pdf_url || doc.docx_url || doc.odt_url) && (
                  <div className="flex items-center gap-2 mt-2 pt-2 border-t">
                    {doc.pdf_url && (
                      <a
                        href={doc.pdf_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-xs text-red-600 hover:underline"
                      >
                        <Download className="h-3 w-3" />
                        PDF
                      </a>
                    )}
                    {doc.docx_url && (
                      <a
                        href={doc.docx_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-xs text-blue-600 hover:underline"
                      >
                        <Download className="h-3 w-3" />
                        DOCX
                      </a>
                    )}
                    {doc.odt_url && (
                      <a
                        href={doc.odt_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-xs text-purple-600 hover:underline"
                      >
                        <Download className="h-3 w-3" />
                        ODT
                      </a>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
