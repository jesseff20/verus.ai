'use client';

import { useState, memo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Paperclip, Bot, User, Pencil, Copy, Check, X, ExternalLink, FileText, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import type { CopilotMessage } from '@/hooks/use-copilot';
import Link from 'next/link';

interface MessageBubbleProps {
  message: CopilotMessage;
  messageIndex: number;
  onEdit?: (index: number, newText: string) => void;
  onDelete?: (index: number) => void;
  isStreaming?: boolean;
}

/**
 * Renders a markdown link.
 * - Internal routes (starting with /) use Next.js <Link> for SPA navigation.
 * - External URLs open in new tab.
 * - Special action buttons are rendered when the href starts with /dashboard.
 */
/**
 * Memoized Markdown renderer.
 * During streaming we skip full markdown parsing to avoid re-parsing the
 * entire growing message on every state update. Instead we show a lightweight
 * plain-text view and only render full markdown once streaming finishes.
 */
const FinalMarkdown = memo(function FinalMarkdown({
  content,
}: {
  content: string;
}) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        a: ({ href, children }) => (
          <MarkdownLink href={href}>{children}</MarkdownLink>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );
});

function MarkdownLink({ href, children }: { href?: string; children?: React.ReactNode }) {
  if (!href) return <span>{children}</span>;

  const isInternal = href.startsWith('/');
  const isDashboardAction = href.startsWith('/dashboard');

  if (isDashboardAction) {
    const isAssistantRoute = href.includes('/intelligent-assistant');
    return (
      <Link
        href={href}
        className="inline-flex items-center gap-1.5 rounded-md bg-primary/10 border border-primary/20 px-3 py-1.5 text-xs font-medium text-primary hover:bg-primary/20 transition-colors no-underline my-0.5"
      >
        {isAssistantRoute ? (
          <FileText className="h-3.5 w-3.5 shrink-0" />
        ) : (
          <ExternalLink className="h-3 w-3 shrink-0" />
        )}
        {children}
      </Link>
    );
  }

  if (isInternal) {
    return (
      <Link href={href} className="text-primary underline underline-offset-2 hover:opacity-80">
        {children}
      </Link>
    );
  }

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-primary underline underline-offset-2 hover:opacity-80 inline-flex items-center gap-1"
    >
      {children}
      <ExternalLink className="h-3 w-3 shrink-0" />
    </a>
  );
}

export function MessageBubble({ message, messageIndex, onEdit, onDelete, isStreaming }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(message.content);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleConfirmEdit = () => {
    if (!editText.trim()) return;
    onEdit?.(messageIndex, editText.trim());
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setEditText(message.content);
    setIsEditing(false);
  };

  return (
    <div className={cn('group flex gap-3', isUser ? 'flex-row-reverse' : 'flex-row')}>
      {/* Avatar */}
      <div
        className={cn(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
          isUser ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      {/* Coluna: bubble + ações - max-width 85% on mobile, 90% on desktop */}
      <div className={cn('flex max-w-[85%] sm:max-w-[90%] w-full flex-col gap-1', isUser ? 'items-end' : 'items-start')}>

        {/* Bubble */}
        <div
          className={cn(
            'rounded-2xl px-4 py-2.5 text-sm w-full',
            isUser
              ? 'bg-primary text-primary-foreground rounded-tr-sm'
              : 'bg-muted text-foreground rounded-tl-sm'
          )}
        >
          {message.hasAttachment && (
            <div className="mb-1.5 flex items-center gap-1.5 text-xs opacity-70">
              <Paperclip className="h-3 w-3" />
              {message.attachmentName || 'arquivo anexado'}
            </div>
          )}

          {/* Modo edição (apenas user) */}
          {isEditing ? (
            <div className="flex flex-col gap-2">
              <Textarea
                ref={(el) => {
                  if (el) {
                    el.style.height = 'auto';
                    el.style.height = Math.max(120, el.scrollHeight) + 'px';
                  }
                }}
                value={editText}
                onChange={(e) => {
                  setEditText(e.target.value);
                  const el = e.target;
                  el.style.height = 'auto';
                  el.style.height = Math.max(120, el.scrollHeight) + 'px';
                }}
                className="min-h-[120px] bg-primary/20 text-primary-foreground placeholder:text-primary-foreground/50 border-primary-foreground/30 resize-y text-sm overflow-hidden"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleConfirmEdit();
                  }
                  if (e.key === 'Escape') handleCancelEdit();
                }}
                autoFocus
              />
              <div className="flex justify-end gap-1.5">
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-7 px-2 text-xs text-primary-foreground/70 hover:bg-primary-foreground/10 hover:text-primary-foreground"
                  onClick={handleCancelEdit}
                >
                  <X className="h-3 w-3 mr-1" />
                  Cancelar
                </Button>
                <Button
                  size="sm"
                  className="h-7 px-2 text-xs bg-primary-foreground text-primary hover:bg-primary-foreground/90"
                  onClick={handleConfirmEdit}
                  disabled={!editText.trim()}
                >
                  <Check className="h-3 w-3 mr-1" />
                  Enviar
                </Button>
              </div>
            </div>
          ) : isUser ? (
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
          ) : message.isStreaming ? (
            /* During streaming: plain text — no markdown parsing overhead */
            <div className="prose prose-sm dark:prose-invert max-w-none break-words">
              <p className="whitespace-pre-wrap">{message.content || '\u2588'}</p>
            </div>
          ) : (
            /* After streaming: full markdown render (memoized) */
            <div className="prose prose-sm dark:prose-invert max-w-none break-words">
              <FinalMarkdown content={message.content} />
            </div>
          )}

          {!isEditing && (
            <p
              className={cn(
                'mt-1 text-right text-[10px] opacity-50',
                isUser ? 'text-primary-foreground' : 'text-muted-foreground'
              )}
            >
              {new Date(message.timestamp).toLocaleTimeString('pt-BR', {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </p>
          )}
        </div>

        {/* Ações abaixo do bubble - aparecem no hover */}
        {!isEditing && !message.isStreaming && (
          <div
            className={cn(
              'flex items-center gap-0.5 opacity-0 transition-opacity group-hover:opacity-100',
              isUser ? 'flex-row-reverse' : 'flex-row'
            )}
          >
            {/* Copiar */}
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 text-muted-foreground hover:text-foreground"
              onClick={handleCopy}
              title="Copiar"
            >
              {copied ? (
                <Check className="h-3.5 w-3.5 text-green-500" />
              ) : (
                <Copy className="h-3.5 w-3.5" />
              )}
            </Button>

            {/* Editar - apenas mensagens do usuário */}
            {isUser && onEdit && !isStreaming && (
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 text-muted-foreground hover:text-foreground"
                onClick={() => {
                  setEditText(message.content);
                  setIsEditing(true);
                }}
                title="Editar e regenerar"
              >
                <Pencil className="h-3.5 w-3.5" />
              </Button>
            )}

            {/* Excluir - apenas mensagens do usuário */}
            {isUser && onDelete && !isStreaming && (
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                onClick={() => onDelete?.(messageIndex)}
                title="Excluir mensagem"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
