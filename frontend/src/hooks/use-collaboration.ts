'use client';

import { useState, useCallback, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

export interface CollaborationSession {
  id: string;
  document_id: string;
  document_type: 'legal' | 'contract' | 'petition' | 'brief';
  status: 'active' | 'paused' | 'completed' | 'abandoned';
  created_by: number;
  created_by_name?: string;
  allow_comments: boolean;
  allow_suggestions: boolean;
  max_collaborators: number;
  active_collaborators_count: number;
  created_at: string;
  updated_at: string;
  last_activity_at?: string;
  expires_at?: string;
}

export interface Collaborator {
  id: string;
  user: number;
  user_name: string;
  user_avatar: string;
  status: 'editing' | 'viewing' | 'commenting' | 'away';
  cursor_position: number;
  selected_section?: string;
  is_active: boolean;
  last_heartbeat: string;
  joined_at: string;
}

export interface Operation {
  id: string;
  user: number;
  user_name: string;
  operation_type: 'insert' | 'delete' | 'replace' | 'format' | 'move';
  section_id: string;
  position: number;
  length: number;
  content: string;
  version: number;
  parent_version: number;
  created_at: string;
}

export interface Comment {
  id: string;
  session: string;
  author: number;
  author_name: string;
  author_avatar: string;
  parent?: string;
  section_id?: string;
  position_start: number;
  position_end: number;
  quoted_text: string;
  content: string;
  is_resolved: boolean;
  replies_count: number;
  is_author: boolean;
  created_at: string;
  updated_at: string;
}

export interface Suggestion {
  id: string;
  session: string;
  section_id?: string;
  original_text: string;
  suggested_text: string;
  comment: string;
  status: 'pending' | 'accepted' | 'rejected' | 'modified';
  status_display: string;
  author: number;
  author_name: string;
  reviewed_by?: number;
  reviewer_name?: string;
  created_at: string;
  reviewed_at?: string;
}

export interface CreateSessionParams {
  document_id: string;
  document_type?: 'legal' | 'contract' | 'petition' | 'brief';
  allow_comments?: boolean;
  allow_suggestions?: boolean;
  max_collaborators?: number;
}

export interface CreateCommentParams {
  session_id: string;
  content: string;
  section_id?: string;
  position_start?: number;
  position_end?: number;
  quoted_text?: string;
  parent?: string;
}

export interface CreateSuggestionParams {
  session_id: string;
  original_text: string;
  suggested_text: string;
  comment?: string;
  section_id?: string;
}

/**
 * Hook para Colaboração em Tempo Real
 *
 * @example
 * const {
 *   session,
 *   collaborators,
 *   joinSession,
 *   sendOperation,
 *   comments,
 *   suggestions,
 * } = useCollaboration(sessionId);
 */
export function useCollaboration(sessionId: string | null) {
  const queryClient = useQueryClient();
  const [isConnected, setIsConnected] = useState(false);

  // Query para sessão
  const { data: session, isLoading: loadingSession } = useQuery<CollaborationSession>({
    queryKey: ['collaboration-session', sessionId],
    queryFn: async () => {
      if (!sessionId) throw new Error('Session ID required');
      const response = await api.get(`/api/v1/collaboration/sessions/${sessionId}/`);
      return response.data;
    },
    enabled: !!sessionId,
  });

  // Query para colaboradores
  const { data: collaborators = [], refetch: refetchCollaborators } = useQuery<Collaborator[]>({
    queryKey: ['collaboration-collaborators', sessionId],
    queryFn: async () => {
      if (!sessionId) return [];
      const response = await api.get(`/api/v1/collaboration/sessions/${sessionId}/collaborators/`);
      return response.data.collaborators || [];
    },
    enabled: !!sessionId,
    refetchInterval: 20_000, // Atualizar a cada 20s
  });

  // Query para operações
  const { data: operations = [] } = useQuery<Operation[]>({
    queryKey: ['collaboration-operations', sessionId],
    queryFn: async () => {
      if (!sessionId) return [];
      const response = await api.get(`/api/v1/collaboration/sessions/${sessionId}/operations/`);
      return response.data.operations || [];
    },
    enabled: !!sessionId,
  });

  // Query para comentários
  const { data: comments = [] } = useQuery<Comment[]>({
    queryKey: ['collaboration-comments', sessionId],
    queryFn: async () => {
      if (!sessionId) return [];
      const response = await api.get(`/api/v1/collaboration/comments/?session_id=${sessionId}`);
      return response.data.results || [];
    },
    enabled: !!sessionId,
  });

  // Query para sugestões
  const { data: suggestions = [] } = useQuery<Suggestion[]>({
    queryKey: ['collaboration-suggestions', sessionId],
    queryFn: async () => {
      if (!sessionId) return [];
      const response = await api.get(`/api/v1/collaboration/suggestions/?session_id=${sessionId}`);
      return response.data.results || [];
    },
    enabled: !!sessionId,
  });

  // Mutation para entrar na sessão
  const joinMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      const response = await api.post(`/api/v1/collaboration/sessions/${sessionId}/join/`);
      return response.data;
    },
    onSuccess: () => {
      setIsConnected(true);
      refetchCollaborators();
    },
  });

  // Mutation para sair da sessão
  const leaveMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      await api.post(`/api/v1/collaboration/sessions/${sessionId}/leave/`);
    },
    onSuccess: () => {
      setIsConnected(false);
      refetchCollaborators();
    },
  });

  // Mutation para heartbeat
  const heartbeatMutation = useMutation({
    mutationFn: async ({ sessionId, status, cursorPosition, selectedSection }: {
      sessionId: string;
      status?: string;
      cursorPosition?: number;
      selectedSection?: string;
    }) => {
      await api.post(`/api/v1/collaboration/sessions/${sessionId}/heartbeat/`, {
        status,
        cursor_position: cursorPosition,
        selected_section: selectedSection,
      });
    },
  });

  // Mutation para criar comentário
  const createCommentMutation = useMutation({
    mutationFn: async (params: CreateCommentParams) => {
      const response = await api.post(`/api/v1/collaboration/comments/?session_id=${params.session_id}`, params);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collaboration-comments', sessionId] });
    },
  });

  // Mutation para resolver comentário
  const resolveCommentMutation = useMutation({
    mutationFn: async (commentId: string) => {
      await api.post(`/api/v1/collaboration/comments/${commentId}/resolve/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collaboration-comments', sessionId] });
    },
  });

  // Mutation para criar sugestão
  const createSuggestionMutation = useMutation({
    mutationFn: async (params: CreateSuggestionParams) => {
      const response = await api.post(`/api/v1/collaboration/suggestions/?session_id=${params.session_id}`, params);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collaboration-suggestions', sessionId] });
    },
  });

  // Mutation para revisar sugestão
  const reviewSuggestionMutation = useMutation({
    mutationFn: async ({ suggestionId, status, comment }: { suggestionId: string; status: string; comment?: string }) => {
      await api.post(`/api/v1/collaboration/suggestions/${suggestionId}/review/`, { status, comment });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collaboration-suggestions', sessionId] });
    },
  });

  // Enviar heartbeat periódico
  useEffect(() => {
    if (!sessionId || !isConnected) return;

    const interval = setInterval(() => {
      heartbeatMutation.mutate({ sessionId });
    }, 15000); // Heartbeat a cada 15s

    return () => clearInterval(interval);
  }, [sessionId, isConnected, heartbeatMutation]);

  // Cleanup ao desmontar
  useEffect(() => {
    return () => {
      if (sessionId && isConnected) {
        leaveMutation.mutate(sessionId);
      }
    };
  }, [sessionId, isConnected, leaveMutation]);

  const joinSession = useCallback((sessionId: string) => {
    joinMutation.mutate(sessionId);
  }, [joinMutation]);

  const leaveSession = useCallback((sessionId: string) => {
    leaveMutation.mutate(sessionId);
  }, [leaveMutation]);

  const sendHeartbeat = useCallback((params: { status?: string; cursorPosition?: number; selectedSection?: string }) => {
    if (sessionId) {
      heartbeatMutation.mutate({ sessionId, ...params });
    }
  }, [sessionId, heartbeatMutation]);

  const sendOperation = useCallback(async (operation: Partial<Operation>) => {
    if (!sessionId) return;
    // Operação seria enviada via WebSocket em implementação real
    // Aqui usamos REST como fallback
    await api.post(`/api/v1/collaboration/sessions/${sessionId}/operations/`, operation);
  }, [sessionId]);

  const createComment = useCallback((params: Omit<CreateCommentParams, 'session_id'>) => {
    if (sessionId) {
      createCommentMutation.mutate({ ...params, session_id: sessionId });
    }
  }, [sessionId, createCommentMutation]);

  const resolveComment = useCallback((commentId: string) => {
    resolveCommentMutation.mutate(commentId);
  }, [resolveCommentMutation]);

  const createSuggestion = useCallback((params: Omit<CreateSuggestionParams, 'session_id'>) => {
    if (sessionId) {
      createSuggestionMutation.mutate({ ...params, session_id: sessionId });
    }
  }, [sessionId, createSuggestionMutation]);

  const reviewSuggestion = useCallback((params: { suggestionId: string; status: string; comment?: string }) => {
    reviewSuggestionMutation.mutate(params);
  }, [reviewSuggestionMutation]);

  return {
    // Estado
    session,
    collaborators,
    operations,
    comments,
    suggestions,
    isConnected,

    // Loading
    isLoading: loadingSession,

    // Ações
    joinSession,
    leaveSession,
    sendHeartbeat,
    sendOperation,
    createComment,
    resolveComment,
    createSuggestion,
    reviewSuggestion,
  };
}

/**
 * Hook para criar sessão de colaboração
 */
export function useCreateCollaborationSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params: CreateSessionParams) => {
      const response = await api.post(
        `/api/v1/collaboration/documents/${params.document_id}/start-session/`,
        {
          document_type: params.document_type,
          allow_comments: params.allow_comments,
          allow_suggestions: params.allow_suggestions,
          max_collaborators: params.max_collaborators,
        }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collaboration-sessions'] });
    },
  });
}
