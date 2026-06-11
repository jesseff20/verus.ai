'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { Editor } from '@tinymce/tinymce-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import api from '@/lib/api';
import {
  X,
  Save,
  Download,
  Bot,
  Loader2,
  FileText,
  Maximize2,
  Minimize2,
} from 'lucide-react';

// =============================================================================
// Types
// =============================================================================

export interface FullDocumentEditorProps {
  /** HTML content to load into the editor */
  content: string;
  /** Document title (displayed in header) */
  title?: string;
  /** Document ID for backend save operations */
  documentId?: string;
  /** Callback when content changes */
  onContentChange?: (content: string) => void;
  /** Callback when user saves */
  onSave?: (content: string) => Promise<void>;
  /** Callback when user exports PDF */
  onExportPdf?: (content: string) => Promise<void>;
  /** Callback to close the editor */
  onClose?: () => void;
  /** Enable auto-save (default: false) */
  autoSave?: boolean;
  /** Auto-save interval in ms (default: 30000) */
  autoSaveInterval?: number;
}

// =============================================================================
// Copilot Actions
// =============================================================================

const COPILOT_ACTIONS = [
  {
    key: 'corrigir',
    label: 'Corrigir ortografia e gramática',
    instruction: 'Corrija erros de ortografia, gramática, pontuação e concordância no texto. Mantenha o significado original.',
  },
  {
    key: 'reformular',
    label: 'Reformular texto selecionado',
    instruction: 'Reformule o texto mantendo o mesmo significado, mas com melhor clareza e fluidez.',
  },
  {
    key: 'expandir',
    label: 'Expandir argumentação',
    instruction: 'Expanda a argumentação jurídica com mais detalhes, fundamentos e referências legais.',
  },
  {
    key: 'resumir',
    label: 'Resumir parágrafo',
    instruction: 'Resuma o texto de forma concisa, mantendo os pontos principais.',
  },
  {
    key: 'juridico',
    label: 'Melhorar fundamentação jurídica',
    instruction: 'Melhore a fundamentação jurídica, adicionando referências a leis, jurisprudências e doutrinas relevantes.',
  },
] as const;

// =============================================================================
// Component
// =============================================================================

export function FullDocumentEditor({
  content,
  title = 'Documento',
  documentId,
  onContentChange,
  onSave,
  onExportPdf,
  onClose,
  autoSave = false,
  autoSaveInterval = 30000,
}: FullDocumentEditorProps) {
  const editorRef = useRef<any>(null);
  const { toast } = useToast();

  // State
  const [editorContent, setEditorContent] = useState(content);
  const [isDirty, setIsDirty] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(true);
  const [showCopilotPanel, setShowCopilotPanel] = useState(false);
  const [copilotInput, setCopilotInput] = useState('');
  const [copilotLoading, setCopilotLoading] = useState(false);
  const [copilotResponse, setCopilotResponse] = useState('');

  // Auto-save
  useEffect(() => {
    if (!autoSave || !isDirty || !onSave) return;
    const timer = setTimeout(async () => {
      try {
        await onSave(editorContent);
        setIsDirty(false);
        toast({ title: 'Salvo automaticamente' });
      } catch {
        // Silent fail for auto-save
      }
    }, autoSaveInterval);
    return () => clearTimeout(timer);
  }, [autoSave, isDirty, editorContent, autoSaveInterval, onSave, toast]);

  // Handle editor content change
  const handleEditorChange = useCallback(
    (newContent: string) => {
      setEditorContent(newContent);
      setIsDirty(true);
      onContentChange?.(newContent);
    },
    [onContentChange]
  );

  // Save
  const handleSave = useCallback(async () => {
    if (!onSave) return;
    setIsSaving(true);
    try {
      const currentContent = editorRef.current?.getContent() || editorContent;
      await onSave(currentContent);
      setIsDirty(false);
      toast({ title: 'Documento salvo', description: 'Alterações salvas com sucesso.' });
    } catch (error: any) {
      toast({
        title: 'Erro ao salvar',
        description: error.message || 'Tente novamente.',
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  }, [onSave, editorContent, toast]);

  // Export PDF
  const handleExportPdf = useCallback(async () => {
    if (!onExportPdf) return;
    setIsExporting(true);
    try {
      const currentContent = editorRef.current?.getContent() || editorContent;
      await onExportPdf(currentContent);
    } catch (error: any) {
      toast({
        title: 'Erro ao exportar PDF',
        description: error.message || 'Tente novamente.',
        variant: 'destructive',
      });
    } finally {
      setIsExporting(false);
    }
  }, [onExportPdf, editorContent, toast]);

  // Get selected text from editor
  const getSelectedText = useCallback((): string => {
    if (!editorRef.current) return '';
    const selection = editorRef.current.selection.getContent({ format: 'text' });
    return selection || '';
  }, []);

  // Get selected HTML from editor
  const getSelectedHtml = useCallback((): string => {
    if (!editorRef.current) return '';
    return editorRef.current.selection.getContent({ format: 'html' }) || '';
  }, []);

  // Copilot action handler
  const handleCopilotAction = useCallback(
    async (actionKey: string) => {
      const action = COPILOT_ACTIONS.find((a) => a.key === actionKey);
      if (!action) return;

      const selectedText = getSelectedText();
      const textToProcess = selectedText || editorRef.current?.getContent({ format: 'text' }) || '';

      if (!textToProcess.trim()) {
        toast({
          title: 'Nenhum texto para processar',
          description: 'Selecione um texto no editor ou escreva algo primeiro.',
          variant: 'destructive',
        });
        return;
      }

      setCopilotLoading(true);
      setCopilotResponse('');

      try {
        const { data } = await api.post('/api/v1/intelligent-assistant/enhance-text/', {
          text: textToProcess,
          instruction: action.instruction,
          context: `Ação: ${action.label}. Documento jurídico em edição.`,
        });

        const enhancedText = data.enhanced_text || data.text || data.result || '';

        if (enhancedText) {
          if (selectedText) {
            // Replace selected text
            editorRef.current?.selection.setContent(enhancedText);
          } else {
            // Replace entire content
            editorRef.current?.setContent(enhancedText);
          }
          setIsDirty(true);
          setCopilotResponse('Texto atualizado com sucesso.');
          toast({ title: 'Texto atualizado', description: action.label });
        } else {
          setCopilotResponse('Não foi possível processar o texto.');
        }
      } catch (error: any) {
        const msg = error.response?.data?.error || error.message || 'Erro ao processar';
        setCopilotResponse(`Erro: ${msg}`);
        toast({ title: 'Erro no Copilot', description: msg, variant: 'destructive' });
      } finally {
        setCopilotLoading(false);
      }
    },
    [getSelectedText, toast]
  );

  // Copilot free-form chat
  const handleCopilotChat = useCallback(async () => {
    if (!copilotInput.trim()) return;

    const selectedText = getSelectedText();
    const textContext = selectedText || editorRef.current?.getContent({ format: 'text' })?.slice(0, 2000) || '';

    setCopilotLoading(true);
    setCopilotResponse('');

    try {
      const { data } = await api.post('/api/v1/intelligent-assistant/enhance-text/', {
        text: textContext,
        instruction: copilotInput,
        context: 'Pedido livre do usuário no editor de documentos jurídicos.',
      });

      const enhancedText = data.enhanced_text || data.text || data.result || '';

      if (enhancedText) {
        setCopilotResponse(enhancedText);
        // If user had text selected, offer to replace
        if (selectedText) {
          editorRef.current?.selection.setContent(enhancedText);
          setIsDirty(true);
          toast({ title: 'Texto atualizado' });
        }
      } else {
        setCopilotResponse('Não foi possível processar sua solicitação.');
      }
    } catch (error: any) {
      const msg = error.response?.data?.error || error.message || 'Erro ao processar';
      setCopilotResponse(`Erro: ${msg}`);
    } finally {
      setCopilotLoading(false);
      setCopilotInput('');
    }
  }, [copilotInput, getSelectedText, toast]);

  // Apply copilot response to editor
  const handleApplyResponse = useCallback(() => {
    if (!copilotResponse || !editorRef.current) return;
    const selectedHtml = getSelectedHtml();
    if (selectedHtml) {
      editorRef.current.selection.setContent(copilotResponse);
    } else {
      editorRef.current.setContent(copilotResponse);
    }
    setIsDirty(true);
    setCopilotResponse('');
    toast({ title: 'Texto aplicado ao documento' });
  }, [copilotResponse, getSelectedHtml, toast]);

  // TinyMCE config
  const editorConfig = {
    height: '100%',
    menubar: true,
    plugins: [
      'advlist', 'autolink', 'lists', 'link', 'image', 'charmap', 'preview',
      'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
      'insertdatetime', 'table', 'help', 'wordcount', 'pagebreak',
    ],
    toolbar: [
      'undo redo | blocks fontfamily fontsize',
      'bold italic underline strikethrough | forecolor backcolor',
      'alignleft aligncenter alignright alignjustify',
      'bullist numlist outdent indent',
      'table link image pagebreak | removeformat code',
    ].join(' | '),
    toolbar_mode: 'sliding' as const,
    font_size_formats: '8pt 9pt 10pt 11pt 12pt 14pt 16pt 18pt 20pt 24pt 28pt 36pt 48pt',
    content_style: `
      body {
        font-family: 'Times New Roman', Times, serif;
        font-size: 12pt;
        line-height: 1.5;
        color: #000;
        padding: 2.5cm 2cm 2.5cm 3cm;
        max-width: 210mm;
        margin: 0 auto;
        background: #fff;
        text-align: justify;
        -webkit-text-size-adjust: 100%;
      }
      @media (max-width: 640px) {
        body { padding: 0.5cm; }
      }
      h1 {
        font-size: 16pt;
        font-weight: bold;
        text-align: center;
        color: #000;
        text-transform: uppercase;
        margin-top: 0;
        margin-bottom: 24pt;
        padding-bottom: 12pt;
      }
      h2 {
        font-size: 14pt;
        font-weight: bold;
        color: #000;
        margin-top: 24pt;
        margin-bottom: 12pt;
        page-break-after: avoid;
      }
      h3 {
        font-size: 12pt;
        font-weight: bold;
        color: #000;
        margin-top: 18pt;
        margin-bottom: 6pt;
      }
      h4 {
        font-size: 12pt;
        font-weight: bold;
        color: #000;
        margin: 12pt 0 6pt 0;
      }
      p {
        margin-bottom: 12pt;
        text-align: justify;
        text-indent: 2cm;
        color: #000;
      }
      p:first-of-type { text-indent: 0; }
      strong { font-weight: bold; }
      blockquote {
        margin: 12pt 0;
        padding: 12pt;
        background-color: #f7fafc;
        border-left: 4px solid #333;
        font-style: italic;
      }
      ol, ul { margin-left: 1cm; margin-bottom: 12pt; }
      li { margin-bottom: 6pt; }
      em { font-style: italic; }
      table { border-collapse: collapse; width: 100%; margin: 12pt 0; font-size: 10pt; }
      td { border: 1px solid #000; padding: 8pt; color: #000; }
      th { background-color: #d3d3d3; color: #000; padding: 8pt; text-align: left; font-weight: bold; border: 1px solid #000; }
      hr { display: none; }
      code { font-family: 'Courier New', monospace; font-size: 10pt; background-color: #f7fafc; padding: 2pt 4pt; }
      pre { background-color: #f7fafc; padding: 12pt; overflow-x: auto; font-size: 10pt; }
    `,
    license_key: 'gpl',
    branding: false,
    promotion: false,
    statusbar: true,
    resize: false,
    elementpath: true,
    skin_url: '/tinymce/skins/ui/oxide',
    content_css: '/tinymce/skins/content/default/content.css',
    contextmenu: 'link table',
    pagebreak_separator: '<div style="page-break-after: always;"></div>',
    setup: (editor: any) => {
      editorRef.current = editor;
    },
  };

  return (
    <div
      className={`flex flex-col bg-background ${
        isFullscreen
          ? 'fixed inset-0 z-50'
          : 'relative w-full h-[calc(100vh-200px)] rounded-lg border'
      }`}
    >
      {/* ── Header Toolbar ── */}
      <div className="flex items-center justify-between px-2 sm:px-4 py-2 border-b bg-card shrink-0">
        <div className="flex items-center gap-2 sm:gap-3 min-w-0">
          <FileText className="h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground shrink-0" />
          <div className="min-w-0">
            <h3 className="font-semibold text-xs sm:text-sm leading-tight truncate">{title}</h3>
            {isDirty && (
              <span className="text-[10px] sm:text-xs text-amber-500 font-medium">Não salvo</span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-1 sm:gap-2">
          {/* Copilot toggle */}
          <Button
            variant={showCopilotPanel ? 'default' : 'outline'}
            size="sm"
            onClick={() => setShowCopilotPanel(!showCopilotPanel)}
            className="gap-1 sm:gap-1.5 h-8 px-2 sm:px-3 active:scale-95 touch-manipulation"
          >
            <Bot className="h-4 w-4" />
            <span className="hidden md:inline">Copilot</span>
          </Button>

          {/* Save */}
          {onSave && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleSave}
              disabled={isSaving || !isDirty}
              className="gap-1 sm:gap-1.5 h-8 px-2 sm:px-3 active:scale-95 touch-manipulation"
            >
              {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              <span className="hidden md:inline">Salvar</span>
            </Button>
          )}

          {/* Export PDF */}
          {onExportPdf && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleExportPdf}
              disabled={isExporting}
              className="gap-1 sm:gap-1.5 h-8 px-2 sm:px-3 active:scale-95 touch-manipulation"
            >
              {isExporting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Download className="h-4 w-4" />
              )}
              <span className="hidden md:inline">PDF</span>
            </Button>
          )}

          {/* Fullscreen toggle - hidden on mobile (always fullscreen) */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="hidden sm:inline-flex h-8 px-2"
          >
            {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </Button>

          {/* Close */}
          {onClose && (
            <Button variant="ghost" size="sm" onClick={onClose} className="h-8 px-2">
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {/* ── Main Content ── */}
      <div className="flex flex-1 min-h-0 overflow-hidden relative">
        {/* Editor area */}
        <div className={`flex-1 min-w-0 ${showCopilotPanel ? 'mr-0' : ''}`}>
          <Editor
            tinymceScriptSrc="/tinymce/tinymce.min.js"
            initialValue={content}
            init={editorConfig}
            onEditorChange={handleEditorChange}
            onInit={(_evt: any, editor: any) => {
              editorRef.current = editor;
            }}
          />
        </div>

        {/* ── Copilot Panel: full overlay on mobile, side panel on desktop ── */}
        {showCopilotPanel && (
          <>
            {/* Mobile backdrop */}
            <div
              className="fixed inset-0 bg-black/20 z-10 sm:hidden"
              onClick={() => setShowCopilotPanel(false)}
            />
            <div className="fixed inset-x-0 bottom-0 top-12 sm:static sm:inset-auto w-full sm:w-80 lg:w-96 border-l bg-card flex flex-col shrink-0 overflow-hidden z-20 sm:z-10 rounded-t-2xl sm:rounded-none shadow-xl sm:shadow-none">
              {/* Panel header */}
              <div className="p-3 sm:p-4 border-b flex justify-between items-center shrink-0">
                <h3 className="font-semibold text-sm flex items-center gap-2">
                  <Bot className="h-4 w-4 text-primary" />
                  <span className="sm:hidden">Copilot</span>
                  <span className="hidden sm:inline">Copilot - Assistente de Edição</span>
                </h3>
                <Button variant="ghost" size="sm" onClick={() => setShowCopilotPanel(false)} className="h-8 px-2">
                  <X className="h-4 w-4" />
                </Button>
              </div>

              {/* Quick actions */}
              <div className="p-3 space-y-1.5 border-b shrink-0">
                <p className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wider">
                  Ações rápidas
                </p>
                <div className="grid grid-cols-1 gap-1.5">
                  {COPILOT_ACTIONS.map((action) => (
                    <Button
                      key={action.key}
                      variant="outline"
                      size="sm"
                      className="w-full justify-start text-xs h-9 sm:h-8 active:scale-[0.98] touch-manipulation"
                      disabled={copilotLoading}
                      onClick={() => handleCopilotAction(action.key)}
                    >
                      {action.label}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Response area */}
              {(copilotResponse || copilotLoading) && (
                <div className="p-3 border-b shrink-0 max-h-48 overflow-y-auto overscroll-contain">
                  {copilotLoading ? (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground py-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Processando...
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <p className="text-xs text-muted-foreground font-medium">Resposta do Copilot:</p>
                      <div className="text-sm bg-muted/50 rounded-lg p-3 max-h-32 overflow-y-auto whitespace-pre-wrap">
                        {copilotResponse}
                      </div>
                      {!copilotResponse.startsWith('Erro:') &&
                        copilotResponse !== 'Texto atualizado com sucesso.' && (
                          <Button
                            size="sm"
                            variant="outline"
                            className="w-full text-xs active:scale-[0.98] touch-manipulation"
                            onClick={handleApplyResponse}
                          >
                            Aplicar ao documento
                          </Button>
                        )}
                    </div>
                  )}
                </div>
              )}

              {/* Free-form chat */}
              <div className="p-3 flex-1 flex flex-col min-h-0">
                <p className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wider">
                  Peça ajuda ao Copilot
                </p>
                <Textarea
                  placeholder="Ex: Melhore a introdução deste documento..."
                  value={copilotInput}
                  onChange={(e) => setCopilotInput(e.target.value)}
                  className="flex-1 min-h-[80px] resize-none text-sm"
                  style={{ fontSize: '16px' }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleCopilotChat();
                    }
                  }}
                />
                <Button
                  className="mt-2 w-full active:scale-[0.98] touch-manipulation"
                  size="sm"
                  onClick={handleCopilotChat}
                  disabled={copilotLoading || !copilotInput.trim()}
                >
                  {copilotLoading ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : null}
                  Enviar
                </Button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default FullDocumentEditor;
