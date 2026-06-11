'use client';

import { useState, useEffect, useRef } from 'react';
import {
  useClientPortalMessages,
  useClientPortalSendMessage,
  useClientPortalCases,
} from '@/hooks/use-client-portal';
import type { ClientMessage } from '@/hooks/use-client-portal';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  MessageSquare,
  Loader2,
  AlertTriangle,
  Send,
  Circle,
} from 'lucide-react';

// ─── Helpers ────────────────────────────────────────────────────────────────

function formatMessageTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) {
    return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  }
  if (diffDays === 1) return 'Ontem';
  if (diffDays < 7) return `${diffDays} dias atrás`;
  return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
}

// ─── Component ──────────────────────────────────────────────────────────────

export default function MensagensPage() {
  const [caseFilter, setCaseFilter] = useState<string>('all');
  const [messageText, setMessageText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const activeCaseId = caseFilter === 'all' ? undefined : caseFilter;
  const { data: messages, isLoading, error } = useClientPortalMessages(activeCaseId);
  const { data: cases } = useClientPortalCases();
  const sendMutation = useClientPortalSendMessage();

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    const trimmed = messageText.trim();
    if (!trimmed) return;
    try {
      await sendMutation.mutateAsync({
        content: trimmed,
        case_id: activeCaseId,
      });
      setMessageText('');
    } catch {
      // error handled by mutation
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight flex items-center gap-2">
          <MessageSquare className="h-7 w-7 sm:h-8 sm:w-8" />
          Mensagens
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Comunique-se com seu advogado
        </p>
      </div>

      {/* Case filter */}
      {cases && cases.length > 0 && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Filtrar por caso:</span>
          <Select value={caseFilter} onValueChange={setCaseFilter}>
            <SelectTrigger className="w-[260px]">
              <SelectValue placeholder="Todos os casos" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos os casos</SelectItem>
              {cases.map((c) => (
                <SelectItem key={c.id} value={c.id}>
                  {c.titulo}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Messages area */}
      <Card className="flex flex-col" style={{ minHeight: '400px' }}>
        <CardContent className="flex-1 p-4 overflow-y-auto max-h-[60vh]">
          {isLoading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : error ? (
            <div className="flex items-center justify-center py-16 text-destructive gap-2">
              <AlertTriangle className="h-5 w-5" />
              <span>Erro ao carregar mensagens</span>
            </div>
          ) : !messages || messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-muted-foreground gap-3">
              <MessageSquare className="h-12 w-12 opacity-30" />
              <p className="text-sm">Nenhuma mensagem ainda</p>
              <p className="text-xs">Envie uma mensagem para iniciar a conversa</p>
            </div>
          ) : (
            <div className="space-y-3">
              {messages.map((msg: ClientMessage) => {
                const isClient = msg.sender_type === 'client';
                return (
                  <div
                    key={msg.id}
                    className={`flex ${isClient ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] sm:max-w-[70%] rounded-lg p-3 ${
                        isClient
                          ? 'bg-purple-600 text-white'
                          : 'bg-muted text-foreground'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`text-[11px] font-medium ${
                          isClient ? 'text-purple-200' : 'text-muted-foreground'
                        }`}>
                          {msg.sender_name}
                        </span>
                        {msg.case_titulo && (
                          <span className={`text-[10px] ${
                            isClient ? 'text-purple-300' : 'text-muted-foreground'
                          }`}>
                            | {msg.case_titulo}
                          </span>
                        )}
                      </div>
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                      <div className={`flex items-center justify-end gap-1.5 mt-1 ${
                        isClient ? 'text-purple-200' : 'text-muted-foreground'
                      }`}>
                        <span className="text-[10px]">{formatMessageTime(msg.created_at)}</span>
                        {!isClient && !msg.read && (
                          <Circle className="h-2 w-2 fill-blue-500 text-blue-500" />
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
              <div ref={messagesEndRef} />
            </div>
          )}
        </CardContent>

        {/* Input area */}
        <div className="border-t p-3">
          <div className="flex gap-2">
            <Textarea
              value={messageText}
              onChange={(e) => setMessageText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Digite sua mensagem..."
              className="min-h-[44px] max-h-[120px] resize-none"
              rows={1}
            />
            <Button
              onClick={handleSend}
              disabled={!messageText.trim() || sendMutation.isPending}
              className="shrink-0 self-end"
            >
              {sendMutation.isPending ? (
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
