'use client';

import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

// ── Types ──

export interface CaseProgressReport {
  case_info: Record<string, unknown>;
  phases: Array<Record<string, unknown>>;
  deadlines: Array<Record<string, unknown>>;
  documents: Array<Record<string, unknown>>;
  notifications: Array<Record<string, unknown>>;
  timeline: Array<Record<string, unknown>>;
}

export interface PortfolioReport {
  total_cases: number;
  by_status: Record<string, number>;
  by_specialty: Record<string, number>;
  deadline_compliance: number;
  avg_duration_days: number;
  monthly_new_cases: Array<{ month: string; count: number }>;
}

export interface KPIMetrics {
  active_cases: number;
  deadline_compliance_pct: number;
  avg_resolution_days: number;
  new_cases_this_month: number;
  overdue_deadlines: number;
  upcoming_hearings: number;
}

const BASE = '/api/v1/processos/relatorios';

// ── Hooks ──

export function useCaseProgressReport(caseId: string | null) {
  return useQuery({
    queryKey: ['reports', 'case-progress', caseId],
    queryFn: async () => {
      const res = await api.get<CaseProgressReport>(`${BASE}/caso/${caseId}/`);
      return res.data;
    },
    enabled: !!caseId,
  });
}

export function usePortfolioReport() {
  return useQuery({
    queryKey: ['reports', 'portfolio'],
    queryFn: async () => {
      const res = await api.get<PortfolioReport>(`${BASE}/portfolio/`);
      return res.data;
    },
  });
}

export function useKPIMetrics() {
  return useQuery({
    queryKey: ['reports', 'kpis'],
    queryFn: async () => {
      const res = await api.get<KPIMetrics>(`${BASE}/kpis/`);
      return res.data;
    },
  });
}
