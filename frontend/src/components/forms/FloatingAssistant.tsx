'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import {
  MessageCircle,
  X,
  Send,
  Minimize2,
  Maximize2,
  Loader2,
  ThumbsUp,
  ThumbsDown,
  BookOpen
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import api from '@/lib/api';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';

interface KBSource {
  document_id: string;
  document_title: string;
  document_category: string;
  content: string;
  similarity: number;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  message_id?: string; // ID do backend (para feedback)
  kb_sources?: KBSource[]; // Fontes da Base de Conhecimento
  feedback?: 'positive' | 'negative'; // Feedback dado pelo usuário
}

interface FloatingAssistantProps {
  documentType?: string;
  documentId?: string;
  currentField?: string;
}

export function FloatingAssistant({ documentType, documentId, currentField }: FloatingAssistantProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Olá! Sou seu assistente de IA com acesso à Base de Conhecimento. Posso ajudar você com dúvidas sobre licitações, preenchimento de formulários e documentos. Como posso ajudar?',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  // Gerar session_id único ao montar componente
  useEffect(() => {
    const generateSessionId = () => {
      return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    };
    setSessionId(generateSessionId());
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await api.post('/api/v1/agents/chat/', {
        message: input,
        session_id: sessionId,
        conversation_id: conversationId,
        document_type: documentType,
        document_id: documentId,
        current_field: currentField,
      });

      // Salvar conversation_id para próximas mensagens
      if (response.data.conversation_id && !conversationId) {
        setConversationId(response.data.conversation_id);
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.response || response.data.message,
        timestamp: new Date(),
        message_id: response.data.message_id, // Para enviar feedback depois
        kb_sources: response.data.kb_sources || [],
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      toast({
        title: 'Erro',
        description: error.response?.data?.detail || 'Erro ao enviar mensagem.',
        variant: 'destructive',
      });

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFeedback = async (messageId: string, feedbackType: 'positive' | 'negative') => {
    try {
      await api.post('/api/v1/agents/feedback/', {
        message_id: messageId,
        feedback_type: feedbackType,
      });

      // Atualizar estado local para mostrar que feedback foi dado
      setMessages((prev) =>
        prev.map((msg) =>
          msg.message_id === messageId ? { ...msg, feedback: feedbackType } : msg
        )
      );

      toast({
        title: 'Feedback registrado',
        description: feedbackType === 'positive'
          ? 'Obrigado pelo feedback positivo!'
          : 'Obrigado! Vamos usar seu feedback para melhorar.',
      });
    } catch (error: any) {
      toast({
        title: 'Erro ao enviar feedback',
        description: error.response?.data?.detail || 'Tente novamente.',
        variant: 'destructive',
      });
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (!isOpen) {
    return (
      <div className="fixed bottom-6 right-6 z-50">
        <Button
          size="lg"
          className="rounded-full h-14 w-14 shadow-lg"
          onClick={() => setIsOpen(true)}
        >
          <MessageCircle className="h-6 w-6" />
        </Button>
      </div>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-50">
      <Card
        className={cn(
          'shadow-2xl transition-all duration-300',
          isMinimized ? 'w-80 h-16' : 'w-96 h-[600px]'
        )}
      >
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4 border-b">
          <CardTitle className="text-lg flex items-center gap-2">
            <MessageCircle className="h-5 w-5 text-primary" />
            Assistente IA
          </CardTitle>
          <div className="flex gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsMinimized(!isMinimized)}
            >
              {isMinimized ? (
                <Maximize2 className="h-4 w-4" />
              ) : (
                <Minimize2 className="h-4 w-4" />
              )}
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setIsOpen(false)}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>

        {!isMinimized && (
          <CardContent className="p-0 flex flex-col h-[calc(600px-73px)]">
            <ScrollArea className="flex-1 p-4" ref={scrollRef}>
              <div className="space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={cn(
                      'flex flex-col',
                      message.role === 'user' ? 'items-end' : 'items-start'
                    )}
                  >
                    <div
                      className={cn(
                        'max-w-[80%] rounded-lg p-3 text-sm',
                        message.role === 'user'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted'
                      )}
                    >
                      {/* Renderizar Markdown se for assistente, texto normal se for usuário */}
                      {message.role === 'assistant' ? (
                        <div className="text-sm">
                          <ReactMarkdown
                            rehypePlugins={[rehypeRaw]}
                            components={{
                              p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                              strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                              ul: ({ children }) => <ul className="list-disc ml-4 mb-2 space-y-1">{children}</ul>,
                              ol: ({ children }) => <ol className="list-decimal ml-4 mb-2 space-y-1">{children}</ol>,
                              li: ({ children }) => <li className="text-sm">{children}</li>,
                            }}
                          >
                            {message.content}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        <p className="whitespace-pre-wrap">{message.content}</p>
                      )}

                      {/* Fontes da Base de Conhecimento */}
                      {message.kb_sources && message.kb_sources.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-border/50">
                          <div className="flex items-center gap-1 text-xs font-medium mb-2">
                            <BookOpen className="h-3 w-3" />
                            <span>Fontes da Base de Conhecimento:</span>
                          </div>
                          <div className="space-y-1">
                            {message.kb_sources.map((source, idx) => (
                              <div key={idx} className="text-xs opacity-80">
                                <Badge variant="outline" className="text-xs">
                                  {source.document_title}
                                </Badge>
                                <span className="ml-1">
                                  ({Math.round(source.similarity * 100)}% relevante)
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <span className="text-xs opacity-70 mt-1 block">
                        {message.timestamp.toLocaleTimeString('pt-BR', {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </div>

                    {/* Botões de Feedback (apenas para mensagens do assistente) */}
                    {message.role === 'assistant' && message.message_id && (
                      <div className="flex gap-1 mt-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          className={cn(
                            'h-6 w-6 p-0',
                            message.feedback === 'positive' && 'bg-green-100 text-green-600'
                          )}
                          onClick={() => handleFeedback(message.message_id!, 'positive')}
                          disabled={!!message.feedback}
                        >
                          <ThumbsUp className="h-3 w-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className={cn(
                            'h-6 w-6 p-0',
                            message.feedback === 'negative' && 'bg-red-100 text-red-600'
                          )}
                          onClick={() => handleFeedback(message.message_id!, 'negative')}
                          disabled={!!message.feedback}
                        >
                          <ThumbsDown className="h-3 w-3" />
                        </Button>
                      </div>
                    )}
                  </div>
                ))}

                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-muted rounded-lg p-3">
                      <Loader2 className="h-4 w-4 animate-spin" />
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>

            <div className="border-t p-4">
              <div className="flex gap-2">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Digite sua mensagem..."
                  disabled={isLoading}
                />
                <Button
                  onClick={handleSendMessage}
                  disabled={isLoading || !input.trim()}
                  size="icon"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>

              {currentField && (
                <p className="text-xs text-muted-foreground mt-2">
                  Contexto: Preenchendo campo "{currentField}"
                </p>
              )}
            </div>
          </CardContent>
        )}
      </Card>
    </div>
  );
}
