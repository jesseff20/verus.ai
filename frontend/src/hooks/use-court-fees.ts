'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

// ── Types ──

export interface CourtFeeGuide {
  id: string;
  case: string;
  case_titulo: string;
  fee_type: string;
  fee_type_display: string;
  court: string;
  state: string;
  calculated_amount: number;
  case_value: number | null;
  calculation_formula: string;
  due_date: string;
  payment_status: string;
  payment_status_display: string;
  payment_date: string | null;
  barcode: string;
  notes: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface CourtFeeCalculation {
  calculated_amount: number;
  calculation_formula: string;
}

export interface CourtFeeSummary {
  total_pending: number;
  total_paid: number;
  total_overdue: number;
  overdue_count: number;
}

const BASE = '/api/v1/processos/custas';

// ── Hooks ──

export function useCourtFees(filters?: Record<string, string>) {
  return useQuery({
    queryKey: ['court-fees', filters],
    queryFn: async () => {
      const res = await api.get(`${BASE}/`, { params: filters });
      const data = res.data;
      return (data.results || data) as CourtFeeGuide[];
    },
  });
}

export function useCourtFeeDetail(id: string | undefined) {
  return useQuery({
    queryKey: ['court-fees', id],
    queryFn: async () => {
      const res = await api.get<CourtFeeGuide>(`${BASE}/${id}/`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useCreateCourtFee() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: Partial<CourtFeeGuide>) => {
      const res = await api.post<CourtFeeGuide>(`${BASE}/`, data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['court-fees'] });
    },
  });
}

export function useCalculateCourtFee() {
  return useMutation({
    mutationFn: async (data: { court: string; state: string; fee_type: string; case_value: number }) => {
      const res = await api.post<CourtFeeCalculation>(`${BASE}/calcular/`, data);
      return res.data;
    },
  });
}

export function useMarkFeePaid() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, payment_date }: { id: string; payment_date: string }) => {
      const res = await api.post(`${BASE}/${id}/pagar/`, { payment_date });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['court-fees'] });
    },
  });
}

export function useCourtFeeSummary() {
  return useQuery({
    queryKey: ['court-fees', 'summary'],
    queryFn: async () => {
      const res = await api.get<CourtFeeSummary>(`${BASE}/resumo/`);
      return res.data;
    },
  });
}
