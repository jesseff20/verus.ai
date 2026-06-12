import React, { memo, useState, useCallback } from 'react';
import { motion } from 'motion/react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { SafeContent } from '@/components/ui/safe-content';
import {
  Download,
  Copy,
  Loader2,
  FileText,
  PenLine,
  Link as LinkIcon,
  CheckCircle2,
  Briefcase,
  ChevronDown,
} from 'lucide-react';
import { marked } from 'marked';
import { useQuery } from '@tanstack/react-query';
import type { ApprovalStatus } from '../../types';
import { AttachmentsList } from '../AttachmentsList';
import api from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/hooks/use-auth';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

// Codes que podem ser PAI de anexos (nao sao anexos eles mesmos).
// Quando o documento atual e um destes, exibe a secao "Anexos vinculados".
const PARENT_DOCUMENT_CODES = new Set(['etp', 'termo_referencia']);

type ExportStatus = 'none' | 'generating' | 'ready' | 'failed';

interface ResultPhaseProps {
  generatedContent: Record<string, string>;
  sectionNames: Record<number, string>;
  approvalStatus: Record<number, ApprovalStatus>;
  generationMetadata: any;
  documentTypeName: string;
  sessionObjective: string;
  pdfStatus: ExportStatus;
  onGeneratePdf: () => void;
  docxStatus: ExportStatus;
  onGenerateDocx: () => void;
  odtStatus: ExportStatus;
  onGenerateOdt: () => void;
  onCopyToClipboard: () => void;
  /** UUID da sessao atual - usado pra listar anexos vinculados quando o
   *  documento atual e ETP ou TR (PARENT_DOCUMENT_CODES). */
  sessionId?: string | null;
  /** Tipo do documento atual (etp, termo_referencia, ordem_servico, etc). */
  documentTypeCode?: string | null;
  /** Callback when content is updated from the editor */
  onContentUpdated?: (updatedContent: Record<string, string>) => void;
}

function ExportButton({
  label,
  status,
  onGenerate,
  primary = false,
}: {
  label: string;
  status: ExportStatus;
  onGenerate: () => void;
  primary?: boolean;
}) {
  if (status === 'generating') {
    return (
      <Button disabled className="w-full rounded-xl justify-between">
        <Loader2 className="h-4 w-4 animate-spin" />
        Gerando {label}...
      </Button>
    );
  }

  return (
    <Button
      variant={primary ? 'default' : 'outline'}
      onClick={onGenerate}
      className={cn('w-full rounded-xl justify-between', primary ? 'dark:bg-slate-900 dark:hover:bg-black' : '')}
    >
      Gerar {label}
      <Download size={16} />
    </Button>
  );
}

/** Build the OAB line text from user profile data */
function buildOabText(oabState?: string, oabNumber?: string): string {
  if (oabState && oabNumber) {
    return `OAB/${oabState} n\u00ba ${oabNumber}`;
  }
  return 'OAB/___ n\u00ba ___________';
}

/** Build the signature name line */
function buildSignatureNameText(signatureName?: string): string {
  return signatureName || '____________________________';
}

/** Vincular ao Caso — dropdown + button */
function LinkToCaseSection({
  sessionId,
  documentId,
}: {
  sessionId?: string | null;
  documentId?: string | null;
}) {
  const { toast } = useToast();
  const [selectedCaseId, setSelectedCaseId] = useState('');
  const [isLinking, setIsLinking] = useState(false);
  const [linkedCase, setLinkedCase] = useState<{ id: string; titulo: string } | null>(null);

  const { data: userCases } = useQuery({
    queryKey: ['user-cases-for-link'],
    queryFn: async () => {
      const res = await api.get('/api/v1/processos/', { params: { page_size: 100, status: 'ativo' } });
      return res.data.results || res.data;
    },
  });

  const handleLink = useCallback(async () => {
    if (!selectedCaseId || !sessionId) return;
    setIsLinking(true);
    try {
      const res = await api.post('/api/v1/processos/link-document/', {
        case_id: selectedCaseId,
        session_id: sessionId,
        document_id: documentId || undefined,
      });
      setLinkedCase({ id: res.data.case_id, titulo: res.data.case_titulo });
      toast({ title: 'Vinculado com sucesso!', description: `Documento vinculado ao caso: ${res.data.case_titulo}` });
    } catch (err: any) {
      toast({
        title: 'Erro ao vincular',
        description: err?.response?.data?.error || 'Tente novamente.',
        variant: 'destructive',
      });
    } finally {
      setIsLinking(false);
    }
  }, [selectedCaseId, sessionId, documentId, toast]);

  if (!sessionId) return null;

  return (
    <div className="mt-6 pt-4 border-t border-slate-100 space-y-3">
      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
        Vincular ao Caso
      </p>

      {linkedCase ? (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-green-50 border border-green-200">
          <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0" />
          <div className="min-w-0">
            <p className="text-xs font-medium text-green-800 truncate">{linkedCase.titulo}</p>
            <p className="text-[10px] text-green-600">Documento vinculado</p>
          </div>
        </div>
      ) : (
        <>
          <Select value={selectedCaseId} onValueChange={setSelectedCaseId}>
            <SelectTrigger className="rounded-xl text-sm">
              <SelectValue placeholder="Selecionar caso..." />
            </SelectTrigger>
            <SelectContent>
              {(userCases || []).map((c: any) => (
                <SelectItem key={c.id} value={c.id}>
                  <span className="flex items-center gap-2">
                    <Briefcase className="h-3 w-3 text-muted-foreground" />
                    <span className="truncate max-w-[200px]">{c.titulo}</span>
                  </span>
                </SelectItem>
              ))}
              {(!userCases || userCases.length === 0) && (
                <SelectItem value="_none" disabled>
                  Nenhum caso ativo
                </SelectItem>
              )}
            </SelectContent>
          </Select>

          <Button
            variant="outline"
            className="w-full rounded-xl justify-between"
            onClick={handleLink}
            disabled={!selectedCaseId || isLinking}
          >
            {isLinking ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Vinculando...
              </>
            ) : (
              <>
                Vincular ao Caso
                <LinkIcon size={16} />
              </>
            )}
          </Button>
        </>
      )}
    </div>
  );
}

function ResultPhaseComponent({
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
  onContentUpdated,
}: ResultPhaseProps) {
  const { toast } = useToast();
  const { user } = useAuth();

  // Build full HTML from sections for the editor — matching preview/PDF visual identity
  const buildFullHtml = useCallback(() => {
    const entries = Object.entries(generatedContent)
      .filter(([key]) => {
        const num = parseInt(key.replace('section_', ''));
        const status = approvalStatus[num];
        return status !== 'rejected';
      })
      .sort(([a], [b]) => {
        const numA = parseInt(a.replace('section_', ''));
        const numB = parseInt(b.replace('section_', ''));
        return numA - numB;
      });

    // Convert each section content: detect markdown vs HTML and convert accordingly
    const HTML_BLOCK_RE = /^<\s*(div|h[1-6]|p|ul|ol|li|table|thead|tbody|tr|td|th|section|article|blockquote|pre|code)\b/i;
    const sectionsHtml = entries
      .map(([key, content]) => {
        const num = parseInt(key.replace('section_', ''));
        const name = sectionNames[num] || `Seção ${num}`;
        const trimmed = (content || '').trim();
        // If content is already HTML, use as-is; otherwise convert markdown → HTML
        const htmlContent = HTML_BLOCK_RE.test(trimmed) ? trimmed : marked.parse(trimmed, { async: false }) as string;
        return `<h2 style="font-family:'Times New Roman',Times,serif;font-size:14pt;font-weight:bold;color:#000;margin-top:24pt;margin-bottom:12pt;">${num}. ${name}</h2>\n${htmlContent}`;
      })
      .join('\n');

    const oabText = buildOabText(user?.oab_state, user?.oab_number);
    const sigName = buildSignatureNameText(user?.signature_name);
    const signatureImgHtml = user?.signature_image
      ? `<img src="${user.signature_image}" alt="Assinatura" style="max-height:80px;max-width:280px;margin:0 auto 8px auto;display:block;" />`
      : '';

    // Formal legal document — no branding, judiciary-ready (matches PDF exactly)
    return `
<div style="text-align:center;margin-bottom:24pt;">
  <h1 style="font-family:'Times New Roman',Times,serif;font-size:16pt;font-weight:bold;color:#000;text-transform:uppercase;margin-top:0;margin-bottom:24pt;padding-bottom:12pt;">${documentTypeName}</h1>
</div>
${sectionsHtml}
<div style="margin-top:60px;text-align:center;">
  <p style="text-align:right;margin-bottom:40px;font-family:'Times New Roman',Times,serif;font-size:12pt;">_________________, ___ de _____________ de ____.</p>
  <div style="width:300px;margin:0 auto;">
    ${signatureImgHtml}
    <div style="border-top:1px solid #000;padding-top:8px;">
      <p style="font-weight:bold;margin:0;font-family:'Times New Roman',Times,serif;font-size:12pt;">${sigName}</p>
      <p style="margin:4px 0 0 0;font-size:10pt;font-family:'Times New Roman',Times,serif;">${oabText}</p>
    </div>
  </div>
</div>`;
  }, [generatedContent, sectionNames, approvalStatus, documentTypeName, user]);

  // Open editor in a new page/tab
  const handleOpenEditor = useCallback(() => {
    sessionStorage.setItem('verus_editor_content', buildFullHtml());
    sessionStorage.setItem('verus_editor_title', documentTypeName);
    sessionStorage.setItem('verus_editor_docId', generationMetadata?.document_id || '');
    window.open(
      `/dashboard/intelligent-assistant/editor?doc=${generationMetadata?.document_id || ''}`,
      '_blank'
    );
  }, [buildFullHtml, documentTypeName, generationMetadata]);

  const isParentDocument =
    !!sessionId && !!documentTypeCode && PARENT_DOCUMENT_CODES.has(documentTypeCode);
  const approvedEntries = Object.entries(generatedContent)
    .filter(([key]) => {
      const num = parseInt(key.replace('section_', ''));
      const status = approvalStatus[num];
      return status === 'approved' || status === undefined || status === 'pending';
    })
    .sort(([a], [b]) => {
      const numA = parseInt(a.replace('section_', ''));
      const numB = parseInt(b.replace('section_', ''));
      return numA - numB;
    });

  const visibleEntries = approvedEntries.filter(([key]) => {
    const num = parseInt(key.replace('section_', ''));
    return approvalStatus[num] !== 'rejected';
  });

  const oabText = buildOabText(user?.oab_state, user?.oab_number);
  const sigName = buildSignatureNameText(user?.signature_name);

  return (
    <motion.div
      key="result"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex flex-col lg:flex-row gap-4 sm:gap-8 pb-20 sm:pb-0"
    >
      {/* Document preview (shown first on mobile, second on desktop via order) */}
      <div className="order-1 lg:order-2 lg:flex-1 min-w-0">
        {visibleEntries.length === 0 ? (
          <div className="bg-white rounded-2xl sm:rounded-[2rem] border border-slate-200 shadow-xl p-8 sm:p-16 text-center">
            <FileText className="h-12 w-12 sm:h-16 sm:w-16 mx-auto mb-4 text-slate-300" />
            <h3 className="text-base sm:text-lg font-semibold text-slate-600 mb-2">Nenhum documento gerado</h3>
            <p className="text-sm text-slate-400">Volte ao passo anterior para gerar o documento.</p>
          </div>
        ) : (
          <div className="bg-white rounded-2xl sm:rounded-[2rem] border border-slate-200 shadow-xl min-h-[400px] sm:min-h-[800px] p-4 sm:p-12 lg:p-16 max-w-[900px] mx-auto">
            {/* Document header */}
            <div className="text-center mb-8 sm:mb-14">
              <h1 className="text-base sm:text-xl font-bold text-black uppercase tracking-tight" style={{ fontFamily: "'Times New Roman', Times, serif" }}>
                {documentTypeName}
              </h1>
            </div>

            {/* Sections */}
            <div className="space-y-6 sm:space-y-10">
              {visibleEntries.map(([key, content]) => {
                const num = parseInt(key.replace('section_', ''));
                return (
                  <div key={key} id={`result-section-${num}`} className="scroll-mt-24">
                    <h2 className="text-base sm:text-lg font-bold text-black mb-3 sm:mb-5 flex items-center gap-2 sm:gap-3">
                      <span className="text-black/30 text-lg sm:text-xl">
                        {String(num).padStart(2, '0')}
                      </span>
                      {sectionNames[num] || `Seção ${num}`}
                    </h2>
                    <SafeContent
                      content={content}
                      className="text-black leading-relaxed prose-p:text-sm prose-li:text-sm prose-headings:text-base break-words overflow-wrap-anywhere"
                    />
                  </div>
                );
              })}
            </div>

            {/* Signature block - scales on mobile */}
            <div className="mt-10 sm:mt-16 text-center" style={{ fontFamily: "'Times New Roman', Times, serif" }}>
              <p className="text-right mb-6 sm:mb-10 text-xs sm:text-sm text-black">
                _________________, ___ de _____________ de ____.
              </p>
              <div className="mx-auto w-[220px] sm:w-[300px]">
                {user?.signature_image && (
                  <img
                    src={user.signature_image}
                    alt="Assinatura"
                    className="mx-auto mb-2"
                    style={{ maxHeight: 60, maxWidth: 200, objectFit: 'contain' }}
                  />
                )}
                <div className="border-t border-black pt-2">
                  <p className="font-bold text-xs sm:text-sm text-black m-0">{sigName}</p>
                  <p className="text-[10px] sm:text-xs text-black mt-1">{oabText}</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Sidebar: Index + Export (below preview on mobile, left on desktop) */}
      <div className="order-2 lg:order-1 lg:w-72 xl:w-80 space-y-4 sm:space-y-6 shrink-0">
        <div className="bg-white rounded-2xl sm:rounded-3xl border border-slate-200 p-4 sm:p-6 shadow-sm lg:sticky lg:top-16">
          {/* Index - collapsible on mobile */}
          <details className="group" open>
            <summary className="font-bold text-slate-800 mb-3 sm:mb-4 cursor-pointer sm:cursor-default list-none flex items-center justify-between">
              Índice do Documento
              <ChevronDown size={16} className="sm:hidden group-open:rotate-180 transition-transform text-slate-400" />
            </summary>
            <div className="space-y-1 max-h-[40vh] sm:max-h-none overflow-y-auto overscroll-contain">
              {visibleEntries.map(([key]) => {
                const num = parseInt(key.replace('section_', ''));
                return (
                  <a
                    key={key}
                    href={`#result-section-${num}`}
                    className="block px-3 py-2 rounded-lg text-sm text-slate-600 hover:bg-slate-50 hover:text-primary transition-all active:bg-slate-50"
                  >
                    {num}. {sectionNames[num] || `Seção ${num}`}
                  </a>
                );
              })}
            </div>
          </details>

          <div className="mt-6 sm:mt-8 pt-4 sm:pt-6 border-t border-slate-100 space-y-3">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
              Exportar Documento
            </p>

            {/* Open in Editor */}
            <Button
              variant="default"
              onClick={handleOpenEditor}
              className="w-full rounded-xl justify-between bg-primary hover:bg-primary/90 active:scale-[0.98] touch-manipulation"
            >
              Abrir no Editor
              <PenLine size={16} />
            </Button>

            <div className="grid grid-cols-2 gap-2">
              <ExportButton
                label="PDF"
                status={pdfStatus}
                onGenerate={onGeneratePdf}
              />

              <ExportButton
                label="DOCX"
                status={docxStatus}
                onGenerate={onGenerateDocx}
              />

              <ExportButton
                label="ODT"
                status={odtStatus}
                onGenerate={onGenerateOdt}
              />

              <button
                type="button"
                onClick={onCopyToClipboard}
                className="w-full flex items-center justify-center gap-2 text-slate-400 hover:text-primary active:text-primary transition-all text-xs font-bold uppercase tracking-widest pt-2 touch-manipulation"
              >
                <Copy size={14} />
                Copiar
              </button>
            </div>
          </div>

          {/* Vincular ao Caso */}
          <LinkToCaseSection
            sessionId={sessionId}
            documentId={generationMetadata?.document_id}
          />

          {/* Anexos vinculados */}
          {isParentDocument && (
            <div className="mt-4">
              <AttachmentsList
                sessionId={sessionId}
                parentDocumentType={documentTypeCode}
              />
            </div>
          )}
        </div>
      </div>

      {/* Mobile: Fixed bottom export bar */}
      <div className="fixed bottom-0 left-0 right-0 sm:hidden z-40 bg-white/95 backdrop-blur-sm border-t border-slate-200 px-4 py-3 safe-area-bottom order-last">
        <div className="flex items-center gap-2">
          <Button
            variant="default"
            onClick={handleOpenEditor}
            className="flex-1 rounded-xl gap-2 text-[16px] py-3 active:scale-[0.98] touch-manipulation"
          >
            <PenLine size={16} />
            Editor
          </Button>
          <Button
            variant="outline"
            onClick={onGeneratePdf}
            disabled={pdfStatus === 'generating'}
            className="rounded-xl gap-2 py-3 active:scale-[0.98] touch-manipulation"
          >
            {pdfStatus === 'generating' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download size={16} />}
            PDF
          </Button>
        </div>
      </div>
    </motion.div>
  );
}

export const ResultPhase = memo(ResultPhaseComponent);
