'use client';

import { useState, useRef, useEffect, useCallback, KeyboardEvent } from 'react';
import DOMPurify from 'isomorphic-dompurify';
import {
  Bot,
  Send,
  AlertTriangle,
  Lightbulb,
  User,
  Loader2,
} from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  useClientPortalCopilot,
  useClientPortalCopilotSuggestions,
} from '@/hooks/use-client-portal';

// ─── Types ──────────────────────────────────────────────────────────────────

interface ChatMessage {
  id: string;
  role: 'user' | 'bot';
  content: string;
  disclaimer?: string;
}

// ─── Simple markdown renderer ───────────────────────────────────────────────

function renderMarkdown(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^[\s]*[-*]\s+(.+)/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/gs, '<ul class="list-disc pl-4 space-y-0.5">$1</ul>')
    .replace(/\n/g, '<br />');
}

// ─── Constants ──────────────────────────────────────────────────────────────

const WELCOME_MESSAGE: ChatMessage = {
  id: 'welcome',
  role: 'bot',
  content:
    'Olá! Sou o assistente virtual do Verus.AI. Posso ajudar com informações sobre seus processos, prazos e documentos. Para orientação jurídica, sempre consulte seu advogado. Como posso ajudá-lo?',
};

// ─── Component ──────────────────────────────────────────────────────────────

export default function ClientCopilotPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const copilotMutation = useClientPortalCopilot();
  const { data: suggestions } = useClientPortalCopilotSuggestions();

  // Auto-scroll to bottom
  useEffect(() => {
    const el = scrollRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages, copilotMutation.isPending]);

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || copilotMutation.isPending) return;

      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: trimmed,
      };
      setMessages((prev) => [...prev, userMsg]);
      setInput('');

      try {
        const result = await copilotMutation.mutateAsync(trimmed);
        const botMsg: ChatMessage = {
          id: `bot-${Date.now()}`,
          role: 'bot',
          content: result.response,
          disclaimer: result.disclaimer,
        };
        setMessages((prev) => [...prev, botMsg]);
      } catch {
        const errorMsg: ChatMessage = {
          id: `bot-error-${Date.now()}`,
          role: 'bot',
          content:
            'Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente em alguns instantes.',
        };
        setMessages((prev) => [...prev, errorMsg]);
      }
    },
    [copilotMutation],
  );

  const handleSuggestionClick = (action: string) => {
    sendMessage(action);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const priorityBorderColor = (priority: string) => {
    switch (priority) {
      case 'alta':
        return 'border-red-400 hover:border-red-500';
      case 'media':
        return 'border-yellow-400 hover:border-yellow-500';
      default:
        return 'border-gray-300 hover:border-gray-400';
    }
  };

  return (
    <div className="flex flex-col h-[calc(100dvh-8rem)] sm:h-[calc(100dvh-9rem)]">
      {/* ── Header ──────────────────────────────────────── */}
      <div className="mb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
            <Bot className="h-5 w-5 text-primary" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold">Assistente Virtual</h1>
              <Badge className="bg-primary/15 text-primary text-[10px] font-semibold px-1.5 py-0">
                IA
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              Tire dúvidas sobre seus processos
            </p>
          </div>
        </div>
      </div>

      {/* ── Chat area ───────────────────────────────────── */}
      <Card className="flex flex-1 flex-col overflow-hidden">
        {/* Disclaimer */}
        <div className="flex items-start gap-2 border-b bg-amber-50 dark:bg-amber-950/20 px-4 py-3">
          <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400 mt-0.5 shrink-0" />
          <p className="text-xs text-amber-700 dark:text-amber-300">
            Este assistente fornece informações gerais. Para orientação jurídica,
            consulte seu advogado.
          </p>
        </div>

        {/* Suggestions */}
        {suggestions && suggestions.length > 0 && (
          <div className="flex items-start gap-2 border-b px-4 py-3">
            <Lightbulb className="h-4 w-4 text-primary mt-0.5 shrink-0" />
            <div className="flex flex-wrap gap-2">
              {suggestions.map((s, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => handleSuggestionClick(s.action)}
                  disabled={copilotMutation.isPending}
                  className={`
                    inline-flex items-center gap-1.5 rounded-full border-2 px-3 py-1 text-xs
                    font-medium transition-colors bg-background
                    hover:bg-accent disabled:opacity-50
                    ${priorityBorderColor(s.priority)}
                  `}
                >
                  <span>{s.icon}</span>
                  <span>{s.text}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`
                  flex gap-2 max-w-[85%] sm:max-w-[75%]
                  ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}
                `}
              >
                {/* Avatar */}
                <div
                  className={`
                    flex h-7 w-7 shrink-0 items-center justify-center rounded-full mt-0.5
                    ${
                      msg.role === 'bot'
                        ? 'bg-primary/10 text-primary'
                        : 'bg-primary text-primary-foreground'
                    }
                  `}
                >
                  {msg.role === 'bot' ? (
                    <Bot className="h-3.5 w-3.5" />
                  ) : (
                    <User className="h-3.5 w-3.5" />
                  )}
                </div>

                {/* Bubble */}
                <div>
                  <div
                    className={`
                      rounded-2xl px-4 py-2.5 text-sm leading-relaxed
                      ${
                        msg.role === 'bot'
                          ? 'bg-violet-50 dark:bg-violet-950/30 text-foreground rounded-tl-sm'
                          : 'bg-primary text-primary-foreground rounded-tr-sm'
                      }
                    `}
                    dangerouslySetInnerHTML={{
                      __html: DOMPurify.sanitize(renderMarkdown(msg.content)),
                    }}
                  />
                  {msg.disclaimer && (
                    <p className="mt-1 text-[10px] text-muted-foreground px-2">
                      {msg.disclaimer}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {copilotMutation.isPending && (
            <div className="flex justify-start">
              <div className="flex gap-2">
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary mt-0.5">
                  <Bot className="h-3.5 w-3.5" />
                </div>
                <div className="rounded-2xl rounded-tl-sm bg-violet-50 dark:bg-violet-950/30 px-4 py-3">
                  <div className="flex gap-1">
                    <span className="h-2 w-2 rounded-full bg-primary/40 thinking-dot" />
                    <span className="h-2 w-2 rounded-full bg-primary/40 thinking-dot" />
                    <span className="h-2 w-2 rounded-full bg-primary/40 thinking-dot" />
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input area */}
        <div className="border-t p-3">
          <div className="flex items-end gap-2">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Digite sua mensagem..."
              disabled={copilotMutation.isPending}
              rows={1}
              className="flex-1 resize-none rounded-xl border bg-background px-4 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 disabled:opacity-50 max-h-32"
              style={{ minHeight: '2.5rem' }}
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement;
                target.style.height = 'auto';
                target.style.height = Math.min(target.scrollHeight, 128) + 'px';
              }}
            />
            <Button
              size="icon"
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || copilotMutation.isPending}
              className="h-10 w-10 rounded-xl shrink-0"
            >
              {copilotMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
