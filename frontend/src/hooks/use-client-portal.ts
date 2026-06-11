'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

// ─── Types ──────────────────────────────────────────────────────────────────

export interface ClientProfile {
  id: string;
  name: string;
  client_type: string;
  client_type_display: string;
  cpf_cnpj: string;
  email: string;
  phone: string;
  address: string;
  city: string;
  state: string;
  zipcode: string;
  company_name: string;
  contact_person: string;
}

export interface ClientCase {
  id: string;
  numero_processo: string;
  titulo: string;
  especialidade: string;
  especialidade_display: string;
  status: string;
  status_display: string;
  fase: string;
  fase_display: string;
  cliente_nome: string;
  parte_contraria: string;
  tribunal: string;
  vara_juizo: string;
  comarca: string;
  data_distribuicao: string | null;
  created_at: string;
}

export interface ClientCaseDeadline {
  id: string;
  titulo: string;
  descricao: string;
  tipo: string;
  tipo_display: string;
  prioridade: string;
  prioridade_display: string;
  status: string;
  status_display: string;
  data_prazo: string;
  data_conclusao: string | null;
}

export interface ClientCasePhase {
  id: string;
  order: number;
  name: string;
  description: string;
  status: string;
  status_display: string;
  estimated_date: string | null;
  actual_date: string | null;
}

export interface ClientCaseDocument {
  id: string;
  titulo: string;
  tipo: string;
  tipo_display: string;
  descricao: string;
  data_documento: string | null;
  created_at: string;
}

export interface ClientCaseHearing {
  id: string;
  data_audiencia: string;
  hora_audiencia: string | null;
  tipo: string;
  tipo_display: string;
  local: string;
  observacoes: string;
  status: string;
  status_display: string;
}

export interface ClientCaseDetail extends ClientCase {
  descricao: string;
  prazos: ClientCaseDeadline[];
  phases: ClientCasePhase[];
  documentos: ClientCaseDocument[];
  audiencias?: ClientCaseHearing[];
  advogado_responsavel?: string;
  valor_causa?: string | null;
}

export interface ClientContract {
  id: string;
  titulo: string;
  tipo: string;
  tipo_display: string;
  status: string;
  status_display: string;
  content_html: string;
  created_at: string;
  signed_at: string | null;
  signature_hash: string | null;
}

export interface ClientMessage {
  id: string;
  case_id: string | null;
  case_titulo: string | null;
  sender_type: 'client' | 'lawyer';
  sender_name: string;
  content: string;
  created_at: string;
  read: boolean;
}

export interface ClientDocumentAll {
  id: string;
  titulo: string;
  tipo: string;
  tipo_display: string;
  descricao: string;
  data_documento: string | null;
  created_at: string;
  case_id: string;
  case_titulo: string;
  download_url: string | null;
}

export interface ClientConsent {
  id: string;
  title: string;
  version: string;
  content: string;
  accepted: boolean;
  accepted_at: string | null;
}

export interface ClientFinancial {
  id: string;
  descricao: string;
  tipo: string;
  tipo_display: string;
  valor: number;
  status: string;
  status_display: string;
  data_vencimento: string | null;
  data_pagamento: string | null;
  created_at: string;
  caso_id: string | null;
  caso_titulo: string | null;
}

export interface ClientNotification {
  id: string;
  titulo: string;
  mensagem: string;
  tipo: string;
  lida: boolean;
  created_at: string;
  link: string | null;
}

export interface ClientHearing {
  id: string;
  titulo: string;
  tipo: string;
  tipo_display: string;
  data_audiencia: string;
  local: string;
  status: string;
  status_display: string;
  observacoes: string;
  caso_id: string;
  caso_titulo: string;
}

// ─── API client for portal ──────────────────────────────────────────────────

const portalApi = axios.create({
  baseURL: '',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

portalApi.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('client_portal_access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// ─── Auth hook ──────────────────────────────────────────────────────────────

export function useClientPortalAuth() {
  const [error, setError] = useState<string | null>(null);
  const [loginLoading, setLoginLoading] = useState(false);
  const router = useRouter();
  const queryClient = useQueryClient();

  const {
    data: client,
    isLoading: loading,
  } = useQuery({
    queryKey: ['client-portal-me'],
    queryFn: async () => {
      const token = localStorage.getItem('client_portal_access_token');
      if (!token) return null;
      try {
        const res = await portalApi.get<ClientProfile>('/api/v1/auth/client-portal/me/');
        return res.data;
      } catch {
        return null;
      }
    },
    staleTime: 24 * 60 * 60 * 1000,
    retry: false,
    refetchOnWindowFocus: false,
  });

  const login = async (email: string, password: string) => {
    try {
      setError(null);
      setLoginLoading(true);
      const res = await portalApi.post('/api/v1/auth/client-portal/login/', { email, password });
      const { client: clientData, tokens } = res.data;
      localStorage.setItem('client_portal_access_token', tokens.access);
      localStorage.setItem('client_portal_refresh_token', tokens.refresh);
      queryClient.setQueryData(['client-portal-me'], clientData);
      router.push('/portal');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Erro ao fazer login. Tente novamente.';
      setError(msg);
    } finally {
      setLoginLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('client_portal_access_token');
    localStorage.removeItem('client_portal_refresh_token');
    queryClient.setQueryData(['client-portal-me'], null);
    queryClient.removeQueries({ queryKey: ['client-portal-cases'] });
    router.push('/portal/login');
  };

  return {
    client,
    loading,
    loginLoading,
    error,
    login,
    logout,
    isAuthenticated: !!client,
  };
}

// ─── Cases hook ─────────────────────────────────────────────────────────────

export function useClientPortalCases() {
  return useQuery({
    queryKey: ['client-portal-cases'],
    queryFn: async () => {
      const res = await portalApi.get<ClientCase[]>('/api/v1/auth/client-portal/cases/');
      return res.data;
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

export function useClientPortalCaseDetail(caseId: string) {
  return useQuery({
    queryKey: ['client-portal-case', caseId],
    queryFn: async () => {
      const res = await portalApi.get<ClientCaseDetail>(`/api/v1/auth/client-portal/cases/${caseId}/`);
      return res.data;
    },
    enabled: !!caseId,
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

// ─── Contracts hooks ───────────────────────────────────────────────────────

export function useClientPortalContracts() {
  return useQuery({
    queryKey: ['client-portal-contracts'],
    queryFn: async () => {
      const res = await portalApi.get<ClientContract[]>('/api/v1/auth/client-portal/contracts/');
      return res.data;
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

export function useClientPortalSignContract() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (contractId: string) => {
      const res = await portalApi.post(`/api/v1/auth/client-portal/contracts/${contractId}/sign/`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['client-portal-contracts'] });
    },
  });
}

// ─── Messages hooks ────────────────────────────────────────────────────────

export function useClientPortalMessages(caseId?: string) {
  return useQuery({
    queryKey: ['client-portal-messages', caseId || 'all'],
    queryFn: async () => {
      const params = caseId ? `?case_id=${caseId}` : '';
      const res = await portalApi.get<ClientMessage[]>(`/api/v1/auth/client-portal/messages/${params}`);
      return res.data;
    },
    staleTime: 30 * 1000,
    retry: false,
    refetchInterval: 30 * 1000,
  });
}

export function useClientPortalSendMessage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { content: string; case_id?: string }) => {
      const res = await portalApi.post('/api/v1/auth/client-portal/messages/', data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['client-portal-messages'] });
    },
  });
}

// ─── Documents hooks ───────────────────────────────────────────────────────

export function useClientPortalDocuments() {
  return useQuery({
    queryKey: ['client-portal-documents'],
    queryFn: async () => {
      const res = await portalApi.get<ClientDocumentAll[]>('/api/v1/auth/client-portal/documents/');
      return res.data;
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

export function useClientPortalUploadDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { file: File; case_id: string; titulo?: string }) => {
      const formData = new FormData();
      formData.append('file', data.file);
      formData.append('case_id', data.case_id);
      if (data.titulo) formData.append('titulo', data.titulo);
      const res = await portalApi.post('/api/v1/auth/client-portal/documents/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['client-portal-documents'] });
      queryClient.invalidateQueries({ queryKey: ['client-portal-case'] });
    },
  });
}

// ─── Consent hooks ──────────────────────────────────────────────────────────

export function useClientPortalPendingConsents() {
  return useQuery({
    queryKey: ['client-portal-consents-pending'],
    queryFn: async () => {
      const res = await portalApi.get<ClientConsent[]>('/api/v1/auth/client-portal/consents/pending/');
      return res.data;
    },
    staleTime: 2 * 60 * 1000,
    retry: false,
  });
}

export function useClientPortalAcceptConsent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (consentId: string) => {
      const res = await portalApi.post(`/api/v1/auth/client-portal/consents/${consentId}/accept/`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['client-portal-consents-pending'] });
      queryClient.invalidateQueries({ queryKey: ['client-portal-consents'] });
    },
  });
}

export function useClientPortalMyConsents() {
  return useQuery({
    queryKey: ['client-portal-consents'],
    queryFn: async () => {
      const res = await portalApi.get<ClientConsent[]>('/api/v1/auth/client-portal/consents/');
      return res.data;
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

// ─── Mark message as read ─────────────────────────────────────────────────

export function useClientPortalMarkRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (messageId: string) => {
      const res = await portalApi.post(`/api/v1/auth/client-portal/messages/${messageId}/read/`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['client-portal-messages'] });
    },
  });
}

// ─── Contract detail hook ─────────────────────────────────────────────────

export function useClientPortalContract(id: string) {
  return useQuery({
    queryKey: ['client-portal-contract', id],
    queryFn: async () => {
      const res = await portalApi.get<ClientContract>(`/api/v1/auth/client-portal/contracts/${id}/`);
      return res.data;
    },
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

// ─── Financial hooks ────────────────────────────────────────────────────────

export function useClientPortalFinancial() {
  return useQuery({
    queryKey: ['client-portal-financial'],
    queryFn: async () => {
      const res = await portalApi.get('/api/v1/auth/client-portal/financial/');
      return res.data as { total_pendente: string; total_pago: string; pendentes: ClientFinancial[]; historico: ClientFinancial[] };
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

// ─── Notification hooks ─────────────────────────────────────────────────────

export function useClientPortalNotifications() {
  return useQuery({
    queryKey: ['client-portal-notifications'],
    queryFn: async () => {
      const res = await portalApi.get<ClientNotification[]>('/api/v1/auth/client-portal/notifications/');
      return res.data;
    },
    staleTime: 2 * 60 * 1000,
    retry: false,
  });
}

// ─── Hearing hooks ──────────────────────────────────────────────────────────

export function useClientPortalHearings() {
  return useQuery({
    queryKey: ['client-portal-hearings'],
    queryFn: async () => {
      const res = await portalApi.get<ClientHearing[]>('/api/v1/auth/client-portal/hearings/');
      return res.data;
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

// ─── Profile hooks ──────────────────────────────────────────────────────────

export function useClientPortalUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<ClientProfile>) => {
      const res = await portalApi.patch('/api/v1/auth/client-portal/me/', data);
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['client-portal-me'], data);
    },
  });
}

export function useClientPortalChangePassword() {
  return useMutation({
    mutationFn: async (data: { current_password: string; new_password: string }) => {
      const res = await portalApi.post('/api/v1/auth/client-portal/change-password/', data);
      return res.data;
    },
  });
}

// ─── Copilot ───────────────────────────────────────────────────────────────

export interface CopilotSuggestion {
  icon: string;
  text: string;
  action: string;
  priority: string;
}

export function useClientPortalCopilot() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (message: string) => {
      const res = await portalApi.post('/api/v1/auth/client-portal/copilot/', { message });
      return res.data as { response: string; disclaimer: string };
    },
  });
}

export function useClientPortalCopilotSuggestions() {
  return useQuery({
    queryKey: ['client-copilot-suggestions'],
    queryFn: async () => {
      const res = await portalApi.get('/api/v1/auth/client-portal/copilot/sugestoes/');
      return res.data.suggestions as CopilotSuggestion[];
    },
    refetchInterval: 300000,
  });
}

// ─── Portal API export (for direct use) ────────────────────────────────────

export { portalApi };
