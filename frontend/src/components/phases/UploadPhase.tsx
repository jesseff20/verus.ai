'use client';

import { useRef, useCallback, useState } from 'react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Upload, FileText, Trash2, Loader2, Download } from 'lucide-react';

interface UploadedDoc {
  id: string;
  filename: string;
  document_type?: string;
  size?: number;
  uploaded_at: string;
  status: string;
}

interface UploadPhaseProps {
  sessionDetail: {
    id: string;
    uploaded_documents?: UploadedDoc[];
    [key: string]: any;
  } | null;
  isUploadingDocuments: boolean;
  dragActive: boolean;
  onDrag: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent) => Promise<void>;
  onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => Promise<void>;
  onDeleteDocument: (documentId: string) => void;
  onAdvance: () => void;
  formatFileSize: (bytes: number) => string;
  className?: string;
}

export function UploadPhase({
  sessionDetail,
  isUploadingDocuments,
  dragActive,
  onDrag,
  onDrop,
  onFileSelect,
  onDeleteDocument,
  onAdvance,
  formatFileSize,
  className,
}: UploadPhaseProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const documents = sessionDetail?.uploaded_documents || [];
  const hasDocuments = documents.length > 0;

  return (
    <div className={cn('space-y-6', className)}>
      <Card>
        <CardContent className="p-6">
          <div
            onDragEnter={onDrag}
            onDragLeave={onDrag}
            onDragOver={onDrag}
            onDrop={onDrop}
            className={cn(
              'border-2 border-dashed rounded-lg p-10 text-center transition-colors',
              dragActive
                ? 'border-primary bg-primary/5'
                : 'border-muted-foreground/25 hover:border-muted-foreground/50',
              isUploadingDocuments && 'pointer-events-none opacity-50'
            )}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx,.txt,.odt"
              onChange={onFileSelect}
              className="hidden"
            />
            <Upload className="h-10 w-10 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-medium mb-2">
              {isUploadingDocuments ? 'Enviando documentos...' : 'Arraste arquivos ou clique para enviar'}
            </h3>
            <p className="text-sm text-muted-foreground mb-4">
              PDF, DOCX, TXT ou ODT — múltiplos arquivos suportados
            </p>
            <Button
              variant="outline"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploadingDocuments}
            >
              {isUploadingDocuments ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <Upload className="h-4 w-4 mr-2" />
              )}
              Selecionar Arquivos
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Documents List */}
      {hasDocuments && (
        <Card>
          <CardContent className="p-4">
            <h3 className="text-sm font-medium mb-3">
              Documentos Enviados ({documents.length})
            </h3>
            <div className="space-y-2">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-muted/30 transition-colors"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <FileText className="h-5 w-5 text-primary shrink-0" />
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">{doc.filename}</p>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        {doc.size && <span>{formatFileSize(doc.size)}</span>}
                        <Badge variant="outline" className="text-[10px] px-1.5 py-0">
                          {doc.status}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  <Button
                    size="icon"
                    variant="ghost"
                    className="h-8 w-8 shrink-0 text-muted-foreground hover:text-destructive"
                    onClick={() => onDeleteDocument(doc.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action */}
      {hasDocuments && (
        <div className="flex justify-end">
          <Button onClick={onAdvance} className="gap-2">
            Avançar para Geração
            <Download className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
