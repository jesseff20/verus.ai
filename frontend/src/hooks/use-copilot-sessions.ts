'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { useState, useCallback } from 'react';

export interface CopilotSession {
  id: string;
  created_at: string;
  last_message_at: string;
  message_count: number;
  preview: string;
}

export interface CopilotMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  hasAttachment?: boolean;
  attachmentName?: string;
}

/**
 * Hook para gerenciar histórico de sessões do Copilot
 */
export function useCopilotSessions() {
  const queryClient = useQueryClient();
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<CopilotMessage[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  // Listar sessões (com busca opcional)
  const { data: sessions = [], isLoading: loading } = useQuery<CopilotSession[]>({
    queryKey: ['copilot-sessions', searchQuery],
    queryFn: async () => {
      const params = searchQuery ? { search: searchQuery } : {};
      const response = await api.get('/api/v1/copilot/sessions/', { params });
      return response.data.sessions || [];
    },
  });

  // Criar sessão
  const createSessionMutation = useMutation({
    mutationFn: async () => {
      const response = await api.get('/api/v1/copilot/session/');
      return response.data.session_id as string;
    },
    onSuccess: (sessionId) => {
      setCurrentSessionId(sessionId);
      setMessages([]);
      queryClient.invalidateQueries({ queryKey: ['copilot-sessions'] });
    },
  });

  // Carregar sessão
  const loadSessionMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      const response = await api.get(`/api/v1/copilot/session/${sessionId}/`);
      return response.data.messages as CopilotMessage[];
    },
    onSuccess: (loadedMessages, sessionId) => {
      setCurrentSessionId(sessionId);
      setMessages(loadedMessages);
      queryClient.invalidateQueries({ queryKey: ['copilot-sessions'] });
    },
  });

  // Excluir sessão
  const deleteSessionMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      await api.delete(`/api/v1/copilot/session/${sessionId}/`);
      return sessionId;
    },
    onSuccess: (deletedId) => {
      if (deletedId === currentSessionId) {
        setCurrentSessionId(null);
        setMessages([]);
      }
      queryClient.invalidateQueries({ queryKey: ['copilot-sessions'] });
    },
  });

  // Limpar sessão atual
  const clearCurrentSession = useCallback(() => {
    if (currentSessionId) {
      setMessages([]);
      queryClient.invalidateQueries({ queryKey: ['copilot-sessions'] });
    }
  }, [currentSessionId, queryClient]);

  // Adicionar mensagem ao estado local
  const addMessage = useCallback((message: CopilotMessage) => {
    setMessages((prev) => [...prev, message]);
  }, []);

  // Atualizar mensagem (para streaming)
  const updateMessage = useCallback((messageId: string, content: string) => {
    setMessages((prev) =>
      prev.map((m) => (m.id === messageId ? { ...m, content } : m))
    );
  }, []);

  const createSession = useCallback(() => {
    createSessionMutation.mutate();
  }, [createSessionMutation]);

  const loadSession = useCallback(
    (sessionId: string) => {
      loadSessionMutation.mutate(sessionId);
    },
    [loadSessionMutation]
  );

  const deleteSession = useCallback(
    (sessionId: string) => {
      deleteSessionMutation.mutate(sessionId);
    },
    [deleteSessionMutation]
  );

  return {
    // Dados
    sessions,
    currentSessionId,
    messages,

    // Estado
    loading,
    isCreating: createSessionMutation.isPending,
    searchQuery,

    // Ações
    createSession,
    loadSession,
    deleteSession,
    clearCurrentSession,
    addMessage,
    updateMessage,
    setMessages,
    setSearchQuery,
  };
}
