'use client';

import { useQuery, useMutation } from '@tanstack/react-query';
import api from '@/lib/api';

// ── Types ──

export interface PrazoPriorizado {
  id: string;
  titulo: string;
  risco: 'alto' | 'medio' | 'baixo';
  motivo: string;
  acao_sugerida: string;
}

export interface DeadlineAnalysis {
  analise: string;
  prazos_analisados: number;
  prazos_priorizados: PrazoPriorizado[];
  recomendacoes: string[];
  error?: string;
}

export interface DeadlineSuggestion {
  acao: string;
  urgencia: 'alta' | 'media' | 'baixa';
  prazo_sugerido: string;
}

export interface DeadlineSuggestResult {
  deadline_id: string;
  titulo: string;
  sugestoes: DeadlineSuggestion[];
  observacoes: string;
  error?: string;
}

export interface CaseRiskPrediction {
  case_id: string;
  titulo: string;
  nivel_risco: 'alto' | 'medio' | 'baixo';
  score: number;
  explicacao: string;
  fatores_risco: string[];
  recomendacoes: string[];
  estatisticas: {
    total_prazos: number;
    pendentes: number;
    atrasados: number;
    concluidos: number;
  };
  error?: string;
}

const BASE = '/api/v1/processos/prazos/inteligente';

// ── Hooks ──

export function useSmartDeadlineAnalysis() {
  return useMutation({
    mutationFn: async () => {
      const res = await api.get<DeadlineAnalysis>(`${BASE}/analise/`);
      return res.data;
    },
  });
}

export function useSmartDeadlineSuggest() {
  return useMutation({
    mutationFn: async (deadlineId: string) => {
      const res = await api.get<DeadlineSuggestResult>(`${BASE}/${deadlineId}/sugestoes/`);
      return res.data;
    },
  });
}

export function useSmartDeadlineRisk() {
  return useMutation({
    mutationFn: async (caseId: string) => {
      const res = await api.get<CaseRiskPrediction>(`${BASE}/${caseId}/risco/`);
      return res.data;
    },
  });
}
