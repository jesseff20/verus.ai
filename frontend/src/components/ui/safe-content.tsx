'use client';

import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import DOMPurify from 'isomorphic-dompurify';
import { cn } from '@/lib/utils';

/**
 * Renderizador seguro de conteúdo gerado pelo agente IA.
 *
 * Detecta automaticamente se o conteúdo é HTML em bloco ou Markdown:
 * - HTML (começa com <div>, <h1-6>, <p>, <ul>, <table>, etc.):
 *   sanitiza com DOMPurify e renderiza via dangerouslySetInnerHTML.
 * - Markdown (qualquer outro caso): usa ReactMarkdown + rehypeRaw
 *   (que também aceita HTML inline misturado ao markdown).
 *
 * Em ambos os casos o output passa por DOMPurify antes de ir pro DOM.
 *
 * Uso:
 *   <SafeContent content={section.content} />
 *   <SafeContent content={...} className="prose-lg" />
 */
const HTML_BLOCK_REGEX =
  /^<\s*(div|h[1-6]|p|ul|ol|li|table|thead|tbody|tr|td|th|section|article|blockquote|pre|code|figure|nav|header|footer|main|aside)\b/i;

// Tabelas HTML quase sempre vêm com atributos legados (valign, bgcolor, cellpadding,
// cellspacing) que o ReactMarkdown + rehypeRaw repassam ao React causando warnings
// de "unrecognized DOM prop". Detectar tabela em QUALQUER lugar do conteúdo e
// rotear pro caminho HTML sanitizado (dangerouslySetInnerHTML + DOMPurify) evita
// esse problema.
const HAS_TABLE_REGEX = /<\s*(table|thead|tbody|tr|td|th)\b/i;

interface SafeContentProps {
  content: string;
  className?: string;
}

export function SafeContent({ content, className }: SafeContentProps) {
  const trimmed = (content || '').trim();
  if (!trimmed) return null;

  const isHtml = HTML_BLOCK_REGEX.test(trimmed) || HAS_TABLE_REGEX.test(trimmed);
  const baseClass = cn(
    'prose prose-sm max-w-none text-black [&_p]:text-justify [&_li]:text-justify',
    '[&_h1]:text-black [&_h2]:text-black [&_h3]:text-black [&_h4]:text-black [&_p]:text-black [&_li]:text-black [&_td]:text-black [&_th]:text-black [&_a]:text-black [&_strong]:text-black [&_blockquote]:text-black',
    className,
  );

  if (isHtml) {
    const sanitized = DOMPurify.sanitize(content);
    // text-justify: texto plain entre tags herda o alinhamento. Tabelas tem
    // text-align proprio nos <th>/<td>, nao sao afetadas.
    // whitespace-pre-line: faz o navegador respeitar \n como quebra de linha
    // em texto plain entre tags (ex: subsecoes 5.1, 5.2, 5.3 da §5 do ETP
    // que vem como texto puro separado por \n\n). Tabelas/listas/headings
    // tem white-space:normal por padrao (nao herda) - nao afetados.
    return (
      <div
        className={cn(baseClass, 'text-justify', 'whitespace-pre-line')}
        dangerouslySetInnerHTML={{ __html: sanitized }}
      />
    );
  }

  return (
    <div className={baseClass}>
      <ReactMarkdown rehypePlugins={[rehypeRaw]}>{content}</ReactMarkdown>
    </div>
  );
}
