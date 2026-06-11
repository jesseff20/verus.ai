'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

// ── Types ──

export interface ElectronicProtocol {
  id: string;
  case: string;
  document: string | null;
  protocol_number: string;
  court_system: string;
  court_system_display: string;
  status: string;
  status_display: string;
  petition_type: string;
  submitted_at: string | null;
  accepted_at: string | null;
  protocol_receipt: string;
  error_message: string;
  retry_count: number;
  created_by: string;
  created_by_name: string;
  case_titulo: string;
  case_numero_processo: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface TribunalPushConfig {
  id: string;
  user: string;
  court_system: string;
  court_system_display: string;
  is_active: boolean;
  check_interval_hours: number;
  last_checked: string | null;
  notification_types: string[];
  events_count: number;
  created_at: string;
  updated_at: string;
}

export interface TribunalPushEvent {
  id: string;
  config: string;
  case: string | null;
  event_type: string;
  event_date: string;
  description: string;
  raw_data: Record<string, unknown>;
  is_processed: boolean;
  notification_sent: boolean;
  config_court_system: string;
  config_court_system_display: string;
  case_titulo: string | null;
  case_numero_processo: string | null;
  created_at: string;
}

interface ProtocolStats {
  total: number;
  pending: number;
  accepted: number;
  rejected: number;
  submitted: number;
  draft: number;
  error: number;
}

const BASE = '/api/v1/processos/protocolos';
const TRIBUNAL_BASE = '/api/v1/processos/tribunal-push';

// ── Protocols ──

export function useProtocols(filters?: Record<string, string>) {
  return useQuery({
    queryKey: ['protocols', filters],
    queryFn: async () => {
      const res = await api.get(`${BASE}/`, { params: filters });
      const data = res.data;
      return (data.results || data) as ElectronicProtocol[];
    },
  });
}

export function useProtocol(id: string) {
  return useQuery({
    queryKey: ['protocols', id],
    queryFn: async () => {
      const res = await api.get<ElectronicProtocol>(`${BASE}/${id}/`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useCreateProtocol() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<ElectronicProtocol>) => {
      const res = await api.post(`${BASE}/`, data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['protocols'] });
      queryClient.invalidateQueries({ queryKey: ['protocol-stats'] });
    },
  });
}

export function useSubmitProtocol() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api.post(`${BASE}/${id}/submit/`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['protocols'] });
      queryClient.invalidateQueries({ queryKey: ['protocol-stats'] });
    },
  });
}

export function useCheckProtocolStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api.post(`${BASE}/${id}/check-status/`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['protocols'] });
      queryClient.invalidateQueries({ queryKey: ['protocol-stats'] });
    },
  });
}

export function useProtocolStats() {
  return useQuery({
    queryKey: ['protocol-stats'],
    queryFn: async () => {
      const res = await api.get<ProtocolStats>(`${BASE}/stats/`);
      return res.data;
    },
  });
}

// ── Tribunal Push Configs ──

export function useTribunalConfigs() {
  return useQuery({
    queryKey: ['tribunal-configs'],
    queryFn: async () => {
      const res = await api.get(`${TRIBUNAL_BASE}/configs/`);
      const data = res.data;
      return (data.results || data) as TribunalPushConfig[];
    },
  });
}

export function useCreateTribunalConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<TribunalPushConfig>) => {
      const res = await api.post(`${TRIBUNAL_BASE}/configs/`, data);
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tribunal-configs'] }),
  });
}

export function useUpdateTribunalConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<TribunalPushConfig> }) => {
      const res = await api.patch(`${TRIBUNAL_BASE}/configs/${id}/`, data);
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tribunal-configs'] }),
  });
}

export function useDeleteTribunalConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`${TRIBUNAL_BASE}/configs/${id}/`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tribunal-configs'] }),
  });
}

export function useTribunalCheckNow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api.post(`${TRIBUNAL_BASE}/configs/${id}/check-now/`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tribunal-configs'] });
      queryClient.invalidateQueries({ queryKey: ['tribunal-events'] });
    },
  });
}

// ── Tribunal Push Events ──

export function useTribunalEvents(filters?: Record<string, string>) {
  return useQuery({
    queryKey: ['tribunal-events', filters],
    queryFn: async () => {
      const res = await api.get(`${TRIBUNAL_BASE}/events/`, { params: filters });
      const data = res.data;
      return (data.results || data) as TribunalPushEvent[];
    },
  });
}

export function useMarkEventProcessed() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api.post(`${TRIBUNAL_BASE}/events/${id}/mark-processed/`);
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tribunal-events'] }),
  });
}

// ── Copilot Tribunal Push ──

export interface CopilotAnalysisResult {
  interpretation: string;
  key_points: string[];
  urgency_level: 'baixo' | 'medio' | 'alto';
  suggested_actions: string[];
  legal_implications: string;
}

export interface CopilotSuggestion {
  action: string;
  priority: 'alta' | 'media' | 'baixa';
  estimated_time: string;
  category: string;
}

export interface CopilotRelevanceResult {
  relevance: 'alta' | 'media' | 'baixa';
  confidence: number;
  reasons: string[];
  score: number;
}

const COPILOT_BASE = '/api/v1/processos/copilot/tribunal-push';

export function useCopilotAnalyzeMovement() {
  return useMutation({
    mutationFn: async (data: { movement_text: string; case_id?: string }) => {
      const res = await api.post<CopilotAnalysisResult>(`${COPILOT_BASE}/analisar/`, data);
      return res.data;
    },
  });
}

export function useCopilotSuggestActions() {
  return useMutation({
    mutationFn: async (data: { movement_type: string; case_id?: string }) => {
      const res = await api.post<{ suggestions: CopilotSuggestion[] }>(`${COPILOT_BASE}/sugerir-acoes/`, data);
      return res.data;
    },
  });
}

export function useCopilotSummarize() {
  return useMutation({
    mutationFn: async (data: { publication_text: string }) => {
      const res = await api.post<{ summary: string }>(`${COPILOT_BASE}/resumir/`, data);
      return res.data;
    },
  });
}

export function useCopilotClassifyRelevance() {
  return useMutation({
    mutationFn: async (data: { event_type: string; description: string; case_priority?: string }) => {
      const res = await api.post<CopilotRelevanceResult>(`${COPILOT_BASE}/classificar/`, data);
      return res.data;
    },
  });
}
