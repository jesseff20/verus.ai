'use client';

import * as React from 'react';
import { useRef, useState, useCallback, useMemo, useEffect } from 'react';
import { Editor } from '@tinymce/tinymce-react';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import {
  AlertTriangle,
  CheckCircle2,
  FileText,
  ChevronLeft,
  ChevronRight,
  DiffIcon,
} from 'lucide-react';

// =============================================================================
// Types
// =============================================================================

export interface PlaceholderPattern {
  /** Regex para detectar o placeholder (incluindo colchetes) */
  regex: RegExp;
  /** Classe CSS aplicada ao span */
  className: string;
  /** Cor de fundo do highlight */
  backgroundColor: string;
  /** Rótulo descritivo */
  label: string;
}

export interface DocumentEditorProps {
  /** Conteúdo HTML do documento */
  content: string;
  /** Callback quando o conteúdo é alterado */
  onContentChange?: (content: string) => void;
  /** Modo somente leitura (desabilita edição) */
  readOnly?: boolean;
  /** Ativa modo de comparação entre versões */
  comparisonMode?: boolean;
  /** Conteúdo da versão anterior (para comparação) */
  previousContent?: string;
  /** Altura do editor em pixels */
  height?: number;
  /** Classes CSS adicionais */
  className?: string;
  /** Placeholders personalizados (usa defaults se vazio) */
  placeholderPatterns?: PlaceholderPattern[];
}

// =============================================================================
// Default Placeholder Patterns
// =============================================================================

export const DEFAULT_PLACEHOLDER_PATTERNS: PlaceholderPattern[] = [
  {
    regex: /\[PESQUISAR JURISPRUDÊNCIA:[^\]]*\]/gi,
    className: 'ph-jurisprudencia',
    backgroundColor: '#FFF3CD',
    label: 'Jurisprudência',
  },
  {
    regex: /\[INFORMAÇÃO NECESSÁRIA:[^\]]*\]/gi,
    className: 'ph-informacao',
    backgroundColor: '#F8D7DA',
    label: 'Informação',
  },
  {
    regex: /\[TESE CONTROVERTIDA:[^\]]*\]/gi,
    className: 'ph-tese',
    backgroundColor: '#D1ECF1',
    label: 'Tese',
  },
  {
    regex: /\[SUGESTÃO DA IA - VERIFICAR\]/gi,
    className: 'ph-sugestao',
    backgroundColor: '#D4EDDA',
    label: 'Sugestão IA',
  },
  {
    regex: /\[VERIFICAR BASE LEGAL:[^\]]*\]/gi,
    className: 'ph-legal',
    backgroundColor: '#FFF3E0',
    label: 'Base Legal',
  },
  {
    regex: /\[INSERIR DADO:[^\]]*\]/gi,
    className: 'ph-dado',
    backgroundColor: '#F0F0F0',
    label: 'Inserir Dado',
  },
];

// =============================================================================
// CSS para content_style do TinyMCE
// =============================================================================

function buildPlaceholderCSS(patterns: PlaceholderPattern[]): string {
  return patterns
    .map(
      (p) =>
        `.${p.className} { background-color: ${p.backgroundColor}; padding: 1px 4px; border-radius: 3px; font-weight: 500; cursor: help; border: 1px solid rgba(0,0,0,0.08); display: inline-block; }`
    )
    .join('\n');
}

const TINYMCE_BASE_CSS = `
body { font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 14px; line-height: 1.6; color: #1a1a1a; padding: 16px; }
h1 { font-size: 20px; font-weight: 700; margin-bottom: 8px; }
h2 { font-size: 17px; font-weight: 600; margin-bottom: 6px; }
p { margin-bottom: 8px; }
`;

// =============================================================================
// Utility: extrair texto puro do HTML
// =============================================================================

function htmlToPlainText(html: string): string {
  if (typeof document !== 'undefined') {
    const temp = document.createElement('div');
    temp.innerHTML = html;
    return temp.textContent || temp.innerText || '';
  }
  return html.replace(/<[^>]*>/g, '');
}

// =============================================================================
// Utility: contar placeholders no conteúdo HTML
// =============================================================================

export function countPlaceholders(
  html: string,
  patterns: PlaceholderPattern[] = DEFAULT_PLACEHOLDER_PATTERNS
): number {
  let total = 0;
  for (const pattern of patterns) {
    const matches = html.match(pattern.regex);
    if (matches) total += matches.length;
  }
  return total;
}

// =============================================================================
// Utility: agrupar placeholders por tipo
// =============================================================================

export function groupPlaceholders(
  html: string,
  patterns: PlaceholderPattern[] = DEFAULT_PLACEHOLDER_PATTERNS
): { pattern: PlaceholderPattern; count: number }[] {
  return patterns
    .map((p) => ({
      pattern: p,
      count: (html.match(p.regex) || []).length,
    }))
    .filter((g) => g.count > 0);
}

// =============================================================================
// Utility: pré-processar HTML para envolver placeholders em spans
// =============================================================================

export function preprocessPlaceholders(
  html: string,
  patterns: PlaceholderPattern[] = DEFAULT_PLACEHOLDER_PATTERNS
): string {
  let result = html;
  for (const pattern of patterns) {
    result = result.replace(
      pattern.regex,
      (match) => `<span class="${pattern.className}" data-placeholder="${pattern.label}">${match}</span>`
    );
  }
  return result;
}

// =============================================================================
// Utility: Diff visual simples (linha a linha) para modo comparação
// =============================================================================

interface DiffLine {
  type: 'same' | 'added' | 'removed';
  text: string;
  lineNum: number;
}

function simpleDiff(oldText: string, newText: string): DiffLine[] {
  const oldLines = oldText.split('\n');
  const newLines = newText.split('\n');
  const result: DiffLine[] = [];

  const maxLen = Math.max(oldLines.length, newLines.length);
  for (let i = 0; i < maxLen; i++) {
    const oldLine = oldLines[i] ?? '';
    const newLine = newLines[i] ?? '';

    if (oldLine === newLine) {
      if (oldLine !== '') {
        result.push({ type: 'same', text: oldLine, lineNum: i + 1 });
      }
    } else {
      if (oldLine !== '') {
        result.push({ type: 'removed', text: oldLine, lineNum: i + 1 });
      }
      if (newLine !== '') {
        result.push({ type: 'added', text: newLine, lineNum: i + 1 });
      }
    }
  }

  return result;
}

// =============================================================================
// Sub-component: Comparison View
// =============================================================================

function ComparisonView({
  previousContent,
  currentContent,
  patterns,
}: {
  previousContent: string;
  currentContent: string;
  patterns: PlaceholderPattern[];
}) {
  const prevPlain = htmlToPlainText(previousContent);
  const currPlain = htmlToPlainText(currentContent);
  const diffLines = simpleDiff(prevPlain, currPlain);

  return (
    <div className="border rounded-lg overflow-hidden">
      {/* Header */}
      <div className="grid grid-cols-2 border-b bg-muted/30">
        <div className="p-3 text-sm font-medium text-muted-foreground border-r flex items-center gap-2">
          <ChevronLeft className="h-4 w-4" />
          Versão Anterior
        </div>
        <div className="p-3 text-sm font-medium text-muted-foreground flex items-center gap-2">
          <ChevronRight className="h-4 w-4" />
          Versão Atual
        </div>
      </div>

      {/* Side-by-side content */}
      <div className="grid grid-cols-2 divide-x">
        {/* Previous version */}
        <div className="p-4 text-sm leading-relaxed max-h-[600px] overflow-y-auto bg-red-50/30">
          {diffLines
            .filter((l) => l.type !== 'added')
            .map((line, i) => (
              <div
                key={i}
                className={cn(
                  'py-0.5 px-1 rounded-sm',
                  line.type === 'removed' && 'bg-red-100 line-through text-red-700'
                )}
              >
                {line.text || '\u00A0'}
              </div>
            ))}
        </div>

        {/* Current version */}
        <div className="p-4 text-sm leading-relaxed max-h-[600px] overflow-y-auto bg-green-50/30">
          {diffLines
            .filter((l) => l.type !== 'removed')
            .map((line, i) => (
              <div
                key={i}
                className={cn(
                  'py-0.5 px-1 rounded-sm',
                  line.type === 'added' && 'bg-green-100 text-green-800'
                )}
              >
                {line.text || '\u00A0'}
              </div>
            ))}
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 p-2 border-t bg-muted/20 text-xs text-muted-foreground">
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 bg-red-100 border border-red-300 rounded" />
          Removido
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 bg-green-100 border border-green-300 rounded" />
          Adicionado
        </span>
        <span className="ml-auto flex items-center gap-1">
          <DiffIcon className="h-3 w-3" />
          Comparação linha a linha
        </span>
      </div>
    </div>
  );
}

// =============================================================================
// Sub-component: Placeholder Badge Counter
// =============================================================================

function PlaceholderBadge({ count }: { count: number }) {
  if (count === 0) {
    return (
      <Badge
        variant="outline"
        className="gap-1.5 text-green-600 border-green-300 bg-green-50"
      >
        <CheckCircle2 className="h-3.5 w-3.5" />
        Sem placeholders pendentes
      </Badge>
    );
  }

  return (
    <Badge
      variant="outline"
      className={cn(
        'gap-1.5',
        count > 5
          ? 'text-red-600 border-red-300 bg-red-50'
          : count > 2
          ? 'text-orange-600 border-orange-300 bg-orange-50'
          : 'text-yellow-600 border-yellow-300 bg-yellow-50'
      )}
    >
      <AlertTriangle className="h-3.5 w-3.5" />
      {count} placeholder{count !== 1 ? 's' : ''} não resolvido
      {count !== 1 ? 's' : ''}
    </Badge>
  );
}

// =============================================================================
// TinyMCE Custom Plugin - Placeholder Highlighting
// =============================================================================

function createPlaceholderPlugin(
  patterns: PlaceholderPattern[],
  onCountChange: (count: number) => void
) {
  return (editor: any) => {
    // Registrar formatos para cada tipo de placeholder
    patterns.forEach((p) => {
      editor.formatter.register(p.className, {
        inline: 'span',
        classes: [p.className],
        attributes: { 'data-placeholder': p.label },
        styles: {
          backgroundColor: p.backgroundColor,
          padding: '1px 4px',
          borderRadius: '3px',
          fontWeight: '500',
          cursor: 'help',
          border: '1px solid rgba(0,0,0,0.08)',
          display: 'inline-block',
        },
      });
    });

    // Função que percorre text nodes e envolve placeholders em spans
    const highlightPlaceholders = () => {
      const body = editor.getBody();
      if (!body) return;

      // Lista de nós de texto para processar (evita modificar durante walk)
      const textNodes: Text[] = [];
      const walker = document.createTreeWalker(
        body,
        NodeFilter.SHOW_TEXT,
        null
      );

      // Só processa nós que NÃO estão já dentro de um span de placeholder
      while (walker.nextNode()) {
        const node = walker.currentNode as Text;
        // Pula se já está dentro de um placeholder span
        let parent = node.parentElement;
        let skip = false;
        while (parent) {
          if (
            parent.tagName === 'SPAN' &&
            patterns.some((p) => parent?.classList.contains(p.className))
          ) {
            skip = true;
            break;
          }
          parent = parent.parentElement;
        }
        if (!skip) {
          textNodes.push(node);
        }
      }

      let madeChanges = false;

      // Processar cada nó de texto
      for (const node of textNodes) {
        const text = node.textContent || '';
        let matched = false;
        let matchPattern: PlaceholderPattern | null = null;

        for (const pattern of patterns) {
          pattern.regex.lastIndex = 0;
          if (pattern.regex.test(text)) {
            matched = true;
            matchPattern = pattern;
            break;
          }
        }

        if (matched && matchPattern) {
          madeChanges = true;
          const span = editor.dom.create('span', {
            class: matchPattern.className,
            'data-placeholder': matchPattern.label,
            style: `background-color: ${matchPattern.backgroundColor}; padding: 1px 4px; border-radius: 3px; font-weight: 500; cursor: help; border: 1px solid rgba(0,0,0,0.08); display: inline-block;`,
            contentEditable: 'false',
          });
          span.textContent = text;
          node.parentNode?.replaceChild(span, node);
        }
      }

      // Atualizar contagem se houver mudanças
      if (madeChanges) {
        const html = editor.getContent();
        const count = countPlaceholders(html, patterns);
        onCountChange(count);
      }
    };

    // Hook no SetContent (conteúdo carregado)
    editor.on('SetContent', () => {
      setTimeout(highlightPlaceholders, 0);
    });

    // Hook no NodeChange (digitação/edição)
    let debounceTimer: ReturnType<typeof setTimeout> | null = null;
    editor.on('NodeChange', () => {
      if (debounceTimer) clearTimeout(debounceTimer);
      debounceTimer = setTimeout(highlightPlaceholders, 300);
    });

    // Atualizar contagem também na inicialização
    editor.on('init', () => {
      setTimeout(() => {
        const html = editor.getContent();
        const count = countPlaceholders(html, patterns);
        onCountChange(count);
      }, 100);
    });
  };
}

// =============================================================================
// Configuração da Toolbar
// =============================================================================

const TOOLBAR_CONFIG = [
  'fontfamily fontsize',
  'bold italic underline forecolor',
  'alignleft aligncenter alignright alignjustify',
  'bullist numlist indent outdent',
  'link table code',
  'undo redo',
].join(' | ');

const FONT_SIZE_FORMATS =
  '8pt 9pt 10pt 11pt 12pt 14pt 16pt 18pt 20pt 22pt 24pt 26pt 28pt 36pt 42pt 48pt';

// =============================================================================
// Main Component: DocumentEditor
// =============================================================================

export function DocumentEditor({
  content,
  onContentChange,
  readOnly = false,
  comparisonMode = false,
  previousContent = '',
  height = 600,
  className,
  placeholderPatterns,
}: DocumentEditorProps) {
  const editorRef = useRef<any>(null);
  const [mounted, setMounted] = useState(false);
  const [placeholderCount, setPlaceholderCount] = useState(0);
  const [editorReady, setEditorReady] = useState(false);
  const [showComparisonPanel, setShowComparisonPanel] = useState(false);

  const patterns = placeholderPatterns ?? DEFAULT_PLACEHOLDER_PATTERNS;

  // Pre-processar conteúdo inicial para já vir com spans
  const initialContent = useMemo(
    () => preprocessPlaceholders(content, patterns),
    [] // só na montagem
  );

  // Contar placeholders iniciais
  useEffect(() => {
    setMounted(true);
    if (!comparisonMode) {
      const initialCount = countPlaceholders(initialContent, patterns);
      setPlaceholderCount(initialCount);
    }
  }, []);

  // Callback do plugin para atualizar contagem
  const handleCountChange = useCallback((count: number) => {
    setPlaceholderCount(count);
  }, []);

  // Config do editor TinyMCE
  const editorConfig = useMemo(() => {
    const apiKey =
      typeof window !== 'undefined'
        ? (window as any).NEXT_PUBLIC_TINYMCE_API_KEY
        : undefined;

    const config: Record<string, any> = {
      height,
      menubar: true,
      plugins: [
        'advlist',
        'autolink',
        'lists',
        'link',
        'image',
        'charmap',
        'preview',
        'anchor',
        'searchreplace',
        'visualblocks',
        'code',
        'fullscreen',
        'insertdatetime',
        'media',
        'table',
        'help',
        'wordcount',
      ],
      toolbar: readOnly ? false : TOOLBAR_CONFIG,
      font_size_formats: FONT_SIZE_FORMATS,
      content_style:
        buildPlaceholderCSS(patterns) + '\n' + TINYMCE_BASE_CSS,
      readonly: readOnly,
      license_key: 'gpl',
    branding: false,
      promotion: false,
      statusbar: true,
      resize: true,
      elementpath: true,
      contextmenu: 'link table',
      valid_elements: '*[*]',
      extended_valid_elements:
        'span[class|data-placeholder|style|contentEditable]',
      custom_elements: '~span[class|data-placeholder]',
      entity_encoding: 'raw',
      // Self-hosted: carregar tinymce do node_modules
      ...(apiKey
        ? { api_key: apiKey }
        : {
            // Modo self-hosted: usa o pacote npm tinymce
            external_plugins: {},
            skin_url: '/tinymce/skins/ui/oxide',
            content_css: '/tinymce/skins/content/default/content.css',
          }),
      // Plugin de highlighting inline no setup do editor
      setup: (editor: any) => {
        editorRef.current = editor;

        // Registrar plugin de highlighting
        const plugin = createPlaceholderPlugin(patterns, handleCountChange);
        plugin(editor);

        // Interceptar mudanças de conteúdo
        editor.on('Change', () => {
          const html = editor.getContent();
          onContentChange?.(html);
        });
      },
    };

    return config;
  }, [height, readOnly, patterns, handleCountChange, onContentChange]);

  // Alternar modo de comparação
  const toggleComparison = useCallback(() => {
    setShowComparisonPanel((prev) => !prev);
  }, []);

  // Se estiver em modo de comparação, renderizar visualização diff
  if (comparisonMode) {
    return (
      <div className={cn('space-y-3', className)}>
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <DiffIcon className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium text-muted-foreground">
              Modo Comparação
            </span>
          </div>
          <div className="flex items-center gap-2">
            <PlaceholderBadge count={placeholderCount} />
          </div>
        </div>

        <ComparisonView
          previousContent={previousContent}
          currentContent={content}
          patterns={patterns}
        />
      </div>
    );
  }

  // Modo de edição / visualização normal
  // Se não estiver montado (SSR), mostrar placeholder
  if (!mounted) {
    return (
      <div className={cn('space-y-3', className)}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium text-muted-foreground">
              Editor de Documento
            </span>
          </div>
          <PlaceholderBadge count={placeholderCount} />
        </div>
        <div
          className="border rounded-lg bg-muted/20 flex items-center justify-center text-muted-foreground"
          style={{ height }}
        >
          Carregando editor...
        </div>
      </div>
    );
  }

  return (
    <div className={cn('space-y-3', className)}>
      {/* Header with badges */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium text-muted-foreground">
            Editor de Documento
          </span>
          {readOnly && (
            <Badge variant="secondary" className="text-xs">
              Somente Leitura
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          <PlaceholderBadge count={placeholderCount} />

          {/* Botão toggle comparação */}
          {previousContent && previousContent !== content && (
            <button
              type="button"
              onClick={toggleComparison}
              className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground px-2 py-1 rounded border hover:bg-muted/50 transition-colors"
            >
              <DiffIcon className="h-3.5 w-3.5" />
              Comparar
            </button>
          )}
        </div>
      </div>

      {/* Painel de comparação (toggle) */}
      {showComparisonPanel && previousContent && previousContent !== content && (
        <Card className="p-0 overflow-hidden border-2 border-blue-200">
          <div className="flex items-center justify-between px-3 py-2 bg-blue-50 border-b border-blue-200">
            <span className="text-xs font-medium text-blue-700 flex items-center gap-1.5">
              <DiffIcon className="h-3.5 w-3.5" />
              Comparação rápida de versões
            </span>
            <button
              type="button"
              onClick={toggleComparison}
              className="text-xs text-blue-600 hover:text-blue-800 underline"
            >
              Fechar
            </button>
          </div>
          <div className="max-h-[300px] overflow-y-auto">
            <ComparisonView
              previousContent={previousContent}
              currentContent={content}
              patterns={patterns}
            />
          </div>
        </Card>
      )}

      {/* TinyMCE Editor */}
      <div className={readOnly ? 'pointer-events-none' : ''}>
        <Editor
          tinymceScriptSrc={
            // Self-hosted: carregar do node_modules
            '/tinymce/tinymce.min.js'
          }
          initialValue={initialContent}
          init={editorConfig}
          onInit={(_evt: any, editor: any) => {
            setEditorReady(true);
          }}
        />
      </div>

      {/* Footer com resumo */}

      {editorReady && (
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center gap-4">
            <span>
              {placeholderCount > 0
                ? `${placeholderCount} placeholder${
                    placeholderCount !== 1 ? 's' : ''
                  } pendente${placeholderCount !== 1 ? 's' : ''}`
                : 'Nenhum placeholder pendente'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {groupPlaceholders(content, patterns).map((g) => (
              <span
                key={g.pattern.className}
                className="inline-flex items-center gap-1"
              >
                <span
                  className="inline-block w-2.5 h-2.5 rounded-sm"
                  style={{
                    backgroundColor: g.pattern.backgroundColor,
                    border: '1px solid rgba(0,0,0,0.1)',
                  }}
                />
                <span>
                  {g.pattern.label}: {g.count}
                </span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Hook utilitário para gerenciar estado do editor
// =============================================================================

export function useDocumentEditor(initialContent: string = '') {
  const [content, setContent] = React.useState<string>(initialContent);
  const [isDirty, setIsDirty] = React.useState(false);
  const [version, setVersion] = React.useState(0);
  const [history, setHistory] = React.useState<string[]>([initialContent]);

  const handleContentChange = useCallback((newContent: string) => {
    setContent(newContent);
    setIsDirty(true);
  }, []);

  const saveVersion = useCallback(() => {
    setHistory((prev) => {
      if (prev[prev.length - 1] === content) return prev;
      return [...prev, content];
    });
    setVersion((prev) => prev + 1);
    setIsDirty(false);
  }, [content]);

  const previousVersion = useMemo(() => {
    if (version > 0 && history.length >= 2) {
      return history[history.length - 2];
    }
    return '';
  }, [version, history]);

  return {
    content,
    setContent,
    isDirty,
    version,
    history,
    previousVersion,
    handleContentChange,
    saveVersion,
  };
}

export default DocumentEditor;
