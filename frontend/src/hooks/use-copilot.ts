'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import api from '@/lib/api';

// ========== TYPES ==========

export interface CopilotMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  hasAttachment?: boolean;
  attachmentName?: string;
  isStreaming?: boolean;
}

export interface CopilotState {
  messages: CopilotMessage[];
  isStreaming: boolean;
  sessionId: string | null;
  attachedFile: File | null;
  error: string | null;
}

// ========== HOOK ==========

export function useCopilot() {
  const [messages, setMessages] = useState<CopilotMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  // ── Batching refs for fast streaming ────────────────────────────────────
  // Instead of calling setMessages on every SSE token (which triggers a
  // React re-render + ReactMarkdown reparse per token), we accumulate
  // incoming text in a ref and flush to React state at ~20 fps.
  const pendingContentRef = useRef('');
  const flushTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const streamingMsgIdRef = useRef<string | null>(null);

  // Clean up flush timer on unmount
  useEffect(() => {
    return () => {
      if (flushTimerRef.current) clearTimeout(flushTimerRef.current);
    };
  }, []);

  /** Append text to the pending buffer and schedule a batched state flush. */
  const appendStreamChunk = useCallback((text: string) => {
    pendingContentRef.current += text;
    if (!flushTimerRef.current) {
      flushTimerRef.current = setTimeout(() => {
        const msgId = streamingMsgIdRef.current;
        const pending = pendingContentRef.current;
        if (msgId && pending) {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === msgId ? { ...m, content: m.content + pending } : m
            )
          );
          pendingContentRef.current = '';
        }
        flushTimerRef.current = null;
      }, 50); // flush every 50ms = 20 fps, very smooth
    }
  }, []);

  /** Force-flush any remaining pending content (call at stream end). */
  const flushPendingContent = useCallback((msgId: string) => {
    if (flushTimerRef.current) {
      clearTimeout(flushTimerRef.current);
      flushTimerRef.current = null;
    }
    const pending = pendingContentRef.current;
    if (pending) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === msgId ? { ...m, content: m.content + pending } : m
        )
      );
      pendingContentRef.current = '';
    }
    streamingMsgIdRef.current = null;
  }, []);

  // ── Inicializar sessão ──────────────────────────────────────────────────

  const initSession = useCallback(async (): Promise<string> => {
    const response = await api.get('/api/v1/copilot/session/');
    const id: string = response.data.session_id;
    setSessionId(id);
    return id;
  }, []);

  const ensureSession = useCallback(async (): Promise<string> => {
    if (sessionId) return sessionId;
    return initSession();
  }, [sessionId, initSession]);

  // ── Enviar mensagem ─────────────────────────────────────────────────────

  const sendMessage = useCallback(
    async (text: string) => {
      if (isStreaming) return;
      if (!text.trim() && !attachedFile) return;

      setError(null);

      const sid = await ensureSession();

      const userMsg: CopilotMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content: text,
        timestamp: new Date().toISOString(),
        hasAttachment: !!attachedFile,
        attachmentName: attachedFile?.name,
      };

      setMessages((prev) => [...prev, userMsg]);

      const assistantMsgId = crypto.randomUUID();
      streamingMsgIdRef.current = assistantMsgId;
      pendingContentRef.current = '';
      setMessages((prev) => [
        ...prev,
        {
          id: assistantMsgId,
          role: 'assistant',
          content: '',
          timestamp: new Date().toISOString(),
          isStreaming: true,
        },
      ]);

      setIsStreaming(true);
      const fileToSend = attachedFile;
      setAttachedFile(null);

      try {
        const baseUrl = (/^https?:\/\//.test(process.env.NEXT_PUBLIC_API_URL || '')) ? process.env.NEXT_PUBLIC_API_URL! : '';
        // Força axios a validar/renovar token antes de usar fetch nativo (que não passa pelo interceptor)
        await api.get('/api/v1/auth/users/me/');
        const token =
          typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;

        const formData = new FormData();
        formData.append('session_id', sid);
        formData.append('message', text);
        if (fileToSend) {
          formData.append('file', fileToSend);
        }

        const abortController = new AbortController();
        abortControllerRef.current = abortController;

        const response = await fetch(`${baseUrl}/api/v1/copilot/chat/stream/`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            Accept: 'text/event-stream',
          },
          body: formData,
          signal: abortController.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) throw new Error('No reader available');

        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            try {
              const data = JSON.parse(line.slice(6));

              if (data.event === 'token' && data.text) {
                appendStreamChunk(data.text);
              } else if (data.event === 'completed') {
                flushPendingContent(assistantMsgId);
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMsgId
                      ? { ...m, content: data.full_text || m.content, isStreaming: false }
                      : m
                  )
                );
              } else if (data.event === 'error') {
                throw new Error(data.message || 'Erro desconhecido');
              }
            } catch (parseErr) {
              // Linha mal-formada - ignorar
            }
          }
        }

        // Stream ended without explicit 'completed' event — flush remaining
        flushPendingContent(assistantMsgId);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId ? { ...m, isStreaming: false } : m
          )
        );
      } catch (err: any) {
        if (err.name === 'AbortError') return;

        flushPendingContent(assistantMsgId);
        const msg = err.message || 'Erro ao conectar com o servidor';
        setError(msg);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  content: `Erro: ${msg}`,
                  isStreaming: false,
                }
              : m
          )
        );
      } finally {
        setIsStreaming(false);
        abortControllerRef.current = null;
      }
    },
    [isStreaming, attachedFile, ensureSession, appendStreamChunk, flushPendingContent]
  );

  // ── Limpar conversa ─────────────────────────────────────────────────────

  const clearConversation = useCallback(async () => {
    if (sessionId) {
      try {
        await api.post('/api/v1/copilot/session/clear/', { session_id: sessionId });
      } catch {
        // Silenciar -pode estar expirada
      }
    }
    setMessages([]);
    setSessionId(null);
    setAttachedFile(null);
    setError(null);
  }, [sessionId]);

  // ── Exportar conversa ───────────────────────────────────────────────────

  const exportConversation = useCallback(
    async (format: 'docx' | 'pdf' | 'odt', title = 'Conversa Copilot') => {
      const assistantMessages = messages.filter((m) => m.role === 'assistant');
      if (assistantMessages.length === 0) return;

      const text = messages
        .map((m) => (m.role === 'user' ? `**Usuário:** ${m.content}` : `**Copilot:** ${m.content}`))
        .join('\n\n---\n\n');

      const response = await api.post(
        '/api/v1/copilot/export/',
        { text, format, title },
        { responseType: 'blob' }
      );

      const extMap: Record<string, string> = { docx: 'docx', pdf: 'pdf', odt: 'odt' };
      const url = window.URL.createObjectURL(response.data);
      const link = document.createElement('a');
      link.href = url;
      link.download = `copilot_${title.replace(/\s+/g, '_')}.${extMap[format]}`;
      link.click();
      window.URL.revokeObjectURL(url);
    },
    [messages]
  );

  // ── Arquivo ──────────────────────────────────────────────────────────────

  const attachFile = useCallback((file: File | null) => {
    setAttachedFile(file);
  }, []);

  const stopGeneration = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsStreaming(false);
  }, []);

  // ── Deletar mensagem ────────────────────────────────────────────────────
  // Remove uma mensagem específica e sincroniza com o backend.

  const deleteMessage = useCallback(
    async (messageIndex: number) => {
      if (!sessionId) return;

      // Criar novo histórico sem a mensagem deletada
      const newMessages = messages.filter((_, idx) => idx !== messageIndex);

      // Sincronizar com backend
      const historyForBackend = newMessages.map((m) => ({
        role: m.role,
        content: m.content,
        timestamp: m.timestamp,
      }));

      try {
        await api.post('/api/v1/copilot/session/sync/', {
          session_id: sessionId,
          messages: historyForBackend,
        });
      } catch {
        // Se falhar, continua mesmo assim
      }

      // Atualizar estado local
      setMessages(newMessages);
    },
    [sessionId, messages]
  );

  // ── Editar mensagem e regenerar ─────────────────────────────────────────
  // Trunca o histórico até o índice da mensagem editada, sincroniza com
  // o Redis via /session/sync/ e reenvia com o texto novo.

  const editAndRegenerate = useCallback(
    async (messageIndex: number, newText: string) => {
      if (isStreaming) return;
      if (!newText.trim()) return;

      const sid = sessionId;
      if (!sid) return;

      // Fatia o array: mantém só as mensagens ANTES da editada
      const priorMessages = messages.slice(0, messageIndex);

      // Sincroniza Redis com o histórico truncado
      // (converte CopilotMessage → formato do backend)
      const historyForBackend = priorMessages.map((m) => ({
        role: m.role,
        content: m.content,
        timestamp: m.timestamp,
      }));

      try {
        await api.post('/api/v1/copilot/session/sync/', {
          session_id: sid,
          messages: historyForBackend,
        });
      } catch {
        // Se falhar, continua mesmo assim -o pior caso é o contexto ficar
        // levemente desincronizado, mas a resposta ainda será gerada
      }

      // Atualiza estado local com histórico truncado
      setMessages(priorMessages);
      setError(null);

      // Dispara o envio da mensagem editada
      // Precisa aguardar o setState propagar -usa versão interna sem guard isStreaming
      const assistantMsgId = crypto.randomUUID();
      streamingMsgIdRef.current = assistantMsgId;
      pendingContentRef.current = '';

      const userMsg: CopilotMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content: newText,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [
        ...prev,
        userMsg,
        {
          id: assistantMsgId,
          role: 'assistant',
          content: '',
          timestamp: new Date().toISOString(),
          isStreaming: true,
        },
      ]);

      setIsStreaming(true);

      try {
        const baseUrl = (/^https?:\/\//.test(process.env.NEXT_PUBLIC_API_URL || '')) ? process.env.NEXT_PUBLIC_API_URL! : '';
        // Força axios a validar/renovar token antes de usar fetch nativo (que não passa pelo interceptor)
        await api.get('/api/v1/auth/users/me/');
        const token =
          typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;

        const formData = new FormData();
        formData.append('session_id', sid);
        formData.append('message', newText);

        const abortController = new AbortController();
        abortControllerRef.current = abortController;

        const response = await fetch(`${baseUrl}/api/v1/copilot/chat/stream/`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}`, Accept: 'text/event-stream' },
          body: formData,
          signal: abortController.signal,
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        if (!reader) throw new Error('No reader available');

        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            try {
              const data = JSON.parse(line.slice(6));
              if (data.event === 'token' && data.text) {
                appendStreamChunk(data.text);
              } else if (data.event === 'completed') {
                flushPendingContent(assistantMsgId);
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMsgId
                      ? { ...m, content: data.full_text || m.content, isStreaming: false }
                      : m
                  )
                );
              } else if (data.event === 'error') {
                throw new Error(data.message || 'Erro desconhecido');
              }
            } catch {
              // linha mal-formada
            }
          }
        }

        // Stream ended without explicit 'completed' event — flush remaining
        flushPendingContent(assistantMsgId);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId ? { ...m, isStreaming: false } : m
          )
        );
      } catch (err: any) {
        if (err.name === 'AbortError') return;
        flushPendingContent(assistantMsgId);
        const msg = err.message || 'Erro ao conectar com o servidor';
        setError(msg);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId ? { ...m, content: `Erro: ${msg}`, isStreaming: false } : m
          )
        );
      } finally {
        setIsStreaming(false);
        abortControllerRef.current = null;
      }
    },
    [isStreaming, sessionId, messages, appendStreamChunk, flushPendingContent]
  );

  // ── Iniciar nova sessão (limpa tudo e cria sessão nova) ──────────────────

  const startNewSession = useCallback(async () => {
    setMessages([]);
    setSessionId(null);
    setAttachedFile(null);
    setError(null);
    // Pre-create session so it appears in history immediately
    try {
      await initSession();
    } catch {
      // Will be created lazily on first message
    }
  }, [initSession]);

  // ── Carregar sessão existente ──────────────────────────────────────────

  const loadSession = useCallback(
    async (sid: string, loadedMessages: CopilotMessage[]) => {
      setSessionId(sid);
      setMessages(loadedMessages);
      setAttachedFile(null);
      setError(null);
    },
    []
  );

  return {
    messages,
    isStreaming,
    sessionId,
    attachedFile,
    error,
    sendMessage,
    clearConversation,
    exportConversation,
    attachFile,
    stopGeneration,
    editAndRegenerate,
    deleteMessage,
    startNewSession,
    loadSession,
  };
}
