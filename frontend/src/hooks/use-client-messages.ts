'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

// ── Types ──

export interface ClientMessageItem {
  id: string;
  client: string;
  client_name: string | null;
  client_email: string | null;
  client_phone: string | null;
  case: string | null;
  case_titulo: string | null;
  sender_type: 'client' | 'lawyer';
  sender_name: string;
  content: string;
  is_read: boolean;
  created_at: string;
}

export interface ClientMessagesResponse {
  results: ClientMessageItem[];
  unread_count: number;
}

export interface ClientMessageReplyPayload {
  client: string;
  case?: string | null;
  content: string;
}

export interface MarkReadPayload {
  client: string;
  case?: string | null;
}

const BASE = '/api/v1/processos/mensagens-clientes';

// ── Hooks ──

export function useClientMessages(filters?: Record<string, string>) {
  return useQuery({
    queryKey: ['client-messages', filters],
    queryFn: async () => {
      const res = await api.get<ClientMessagesResponse>(`${BASE}/`, { params: filters });
      return res.data;
    },
    staleTime: 30 * 1000,
    refetchInterval: 30 * 1000,
  });
}

export function useClientMessageReply() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ClientMessageReplyPayload) => {
      const res = await api.post(`${BASE}/responder/`, data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['client-messages'] });
      queryClient.invalidateQueries({ queryKey: ['client-messages-unread'] });
    },
  });
}

export function useClientMessagesMarkRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: MarkReadPayload) => {
      const res = await api.post(`${BASE}/marcar-lidas/`, data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['client-messages'] });
      queryClient.invalidateQueries({ queryKey: ['client-messages-unread'] });
    },
  });
}

export function useClientMessagesUnread() {
  return useQuery({
    queryKey: ['client-messages-unread'],
    queryFn: async () => {
      const res = await api.get<{ unread_count: number }>(`${BASE}/nao-lidas/`);
      return res.data;
    },
    staleTime: 30 * 1000,
    refetchInterval: 60 * 1000,
  });
}
