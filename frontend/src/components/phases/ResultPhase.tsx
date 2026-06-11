'use client';

import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  FileText,
  FileDown,
  FileOutput,
  ClipboardCopy,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Download,
  Printer,
  FileCode,
} from 'lucide-react';
import type { ApprovalStatus } from '@/types';
import { useMemo } from 'react';

interface ResultPhaseProps {
  generatedContent: Record<string, string>;
  sectionNames: Record<number, string>;
  approvalStatus: Record<number, ApprovalStatus>;
  generationMetadata: {
    total_tokens_used?: number;
    valid_sections?: number;
    average_score?: number;
    generation_time?: number | null;
    document_id?: string;
    generation_session_id?: string;
  } | null;
  documentTypeName: string;
  sessionObjective: string;
  pdfStatus: 'none' | 'generating' | 'ready' | 'failed';
  onGeneratePdf: () => Promise<void>;
  docxStatus: 'none' | 'generating' | 'ready' | 'failed';
  onGenerateDocx: () => Promise<void>;
  odtStatus: 'none' | 'generating' | 'ready' | 'failed';
  onGenerateOdt: () => Promise<void>;
  onCopyToClipboard: () => Promise<void>;
  sessionId: string | null;
  documentTypeCode?: string;
  className?: string;
}

export function ResultPhase({
  generatedContent,
  sectionNames,
  approvalStatus,
  generationMetadata,
  documentTypeName,
  sessionObjective,
  pdfStatus,
  onGeneratePdf,
  docxStatus,
  onGenerateDocx,
  odtStatus,
  onGenerateOdt,
  onCopyToClipboard,
  sessionId,
  documentTypeCode,
  className,
}: ResultPhaseProps) {
  // Section entries
  const sectionEntries = useMemo(() => {
    return Object.entries(generatedContent)
      .filter(([key]) => key.startsWith('section_'))
      .map(([key, content]) => {
        const num = parseInt(key.replace('section_', ''), 10);
        return { num, key, name: sectionNames[num] || `Seção ${num}`, content };
      })
      .sort((a, b) => a.num - b.num);
  }, [generatedContent, sectionNames]);

  const totalApproved = Object.values(approvalStatus).filter((s) => s === 'approved').length;
  const totalImproved = Object.values(approvalStatus).filter((s) => s === 'improved').length;

  const FormatButton = ({
    label,
    icon: Icon,
    status,
    onClick,
    color,
  }: {
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    status: string;
    onClick: () => void;
    color: string;
  }) => (
    <button
      onClick={onClick}
      disabled={status === 'generating'}
      className={cn(
        'flex flex-col items-center justify-center gap-2 p-6 rounded-lg border-2 transition-all',
        status === 'ready'
          ? `${color} border-green-500 bg-green-50 dark:bg-green-950`
          : status === 'failed'
          ? 'border-red-300 bg-red-50 dark:bg-red-950'
          : 'border-muted-foreground/20 hover:border-muted-foreground/50 hover:bg-muted/30'
      )}
    >
      {status === 'generating' ? (
        <Loader2 className={cn('h-8 w-8 animate-spin', color)} />
      ) : (
        <Icon className={cn('h-8 w-8', color)} />
      )}
      <span className="text-sm font-medium">
        {status === 'generating' ? 'Gerando...' : status === 'ready' ? 'Baixar' : label}
      </span>
      {status === 'ready' && (
        <Download className="h-4 w-4 text-green-600" />
      )}
    </button>
  );

  return (
    <div className={cn('space-y-6', className)}>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <FileCheck className="h-5 w-5 text-primary" />
            Documento Gerado
          </h2>
          <p className="text-sm text-muted-foreground">
            {documentTypeName} &mdash; {sessionObjective.slice(0, 80)}
            {sessionObjective.length > 80 && '...'}
          </p>
        </div>
      </div>

      {/* Document Summary */}
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{totalApproved}</div>
              <div className="text-xs text-muted-foreground">Aprovadas</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">{totalImproved}</div>
              <div className="text-xs text-muted-foreground">Melhoradas</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">{sectionEntries.length}</div>
              <div className="text-xs text-muted-foreground">Seções Totais</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {generationMetadata?.average_score || 0}%
              </div>
              <div className="text-xs text-muted-foreground">Score Geral</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Export Options */}
      <Card>
        <CardContent className="p-4">
          <h3 className="text-sm font-medium mb-4">Exportar Documento</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <FormatButton
              label="PDF"
              icon={FileDown}
              status={pdfStatus}
              onClick={onGeneratePdf}
              color="text-red-500"
            />
            <FormatButton
              label="DOCX"
              icon={FileOutput}
              status={docxStatus}
              onClick={onGenerateDocx}
              color="text-blue-500"
            />
            <FormatButton
              label="ODT"
              icon={FileCode}
              status={odtStatus}
              onClick={onGenerateOdt}
              color="text-purple-500"
            />
            <button
              onClick={onCopyToClipboard}
              className="flex flex-col items-center justify-center gap-2 p-6 rounded-lg border-2 border-muted-foreground/20 hover:border-muted-foreground/50 hover:bg-muted/30 transition-all"
            >
              <ClipboardCopy className="h-8 w-8 text-muted-foreground" />
              <span className="text-sm font-medium">Copiar</span>
              <Printer className="h-4 w-4 text-muted-foreground" />
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Document Preview */}
      <Card>
        <CardContent className="p-4">
          <h3 className="text-sm font-medium mb-3">Pré-visualização</h3>
          <ScrollArea className="h-[500px] rounded-md border">
            <div className="p-6 space-y-6">
              {sectionEntries.map(({ num, name, content }) => (
                <div key={num}>
                  <h4 className="text-base font-semibold mb-2">
                    {num}. {name}
                  </h4>
                  <div className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">
                    {content || 'Sem conteúdo.'}
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
