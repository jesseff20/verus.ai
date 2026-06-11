'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

// ── Types ──

export interface HonorariosDetail {
  fee_type: string;
  fixed_amount: number | null;
  hourly_rate: number | null;
  success_percentage: number | null;
  estimated_hours: number | null;
  payment_terms: string;
  installments: number;
  includes_expenses: boolean;
}

export interface ProcuracaoDetail {
  powers_type: string;
  special_powers: string;
  court_scope: string;
  valid_until: string | null;
  is_irrevocable: boolean;
}

export interface SubstabelecimentoDetail {
  original_procuracao: string | null;
  substabelecido_name: string;
  substabelecido_oab: string;
  substabelecido_oab_state: string;
  with_reserve: boolean;
  powers_transferred: string;
  reason: string;
}

export interface LegalContract {
  id: string;
  case: string | null;
  client: string;
  contract_type: string;
  contract_type_display: string;
  title: string;
  status: string;
  status_display: string;
  content_html: string;
  signed_at: string | null;
  expires_at: string | null;
  created_by: string;
  created_by_name: string;
  client_name: string;
  case_titulo: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  honorarios_detail: HonorariosDetail | null;
  procuracao_detail: ProcuracaoDetail | null;
  substabelecimento_detail: SubstabelecimentoDetail | null;
}

export interface ContractStats {
  total: number;
  signed: number;
  pending: number;
  draft: number;
}

const BASE = '/api/v1/processos/contratos';

// ── Hooks ──

export function useContracts(filters?: Record<string, string>) {
  return useQuery({
    queryKey: ['contracts', filters],
    queryFn: async () => {
      const res = await api.get(`${BASE}/`, { params: filters });
      const data = res.data;
      return (data.results || data) as LegalContract[];
    },
  });
}

export function useContract(id: string | undefined) {
  return useQuery({
    queryKey: ['contracts', id],
    queryFn: async () => {
      const res = await api.get<LegalContract>(`${BASE}/${id}/`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useCreateContract() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<LegalContract>) => {
      const res = await api.post(`${BASE}/`, data);
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['contracts'] }),
  });
}

export function useGenerateContract() {
  return useMutation({
    mutationFn: async (data: Record<string, unknown>) => {
      const res = await api.post<{ content_html: string }>(`${BASE}/gerar/`, data);
      return res.data;
    },
  });
}

export function useUpdateContract() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<LegalContract> }) => {
      const res = await api.patch(`${BASE}/${id}/`, data);
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['contracts'] }),
  });
}

export function useMarkContractSigned() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api.post(`${BASE}/${id}/assinar/`);
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['contracts'] }),
  });
}

export function useContractStats() {
  return useQuery({
    queryKey: ['contracts', 'stats'],
    queryFn: async () => {
      const res = await api.get<ContractStats>(`${BASE}/stats/`);
      return res.data;
    },
  });
}

export function useUploadContract() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (formData: FormData) => {
      const res = await api.post(`${BASE}/upload-analyze/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['contracts'] }),
  });
}
