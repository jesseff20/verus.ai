'use client';

import { useQuery, useMutation } from '@tanstack/react-query';
import api from '@/lib/api';

// ── Types ──

export interface DataJudParte {
  nome: string;
  tipo: string;
  advogados: string[];
}

export interface DataJudMovimentacao {
  id: string;
  data: string;
  tipo: string;
  descricao: string;
  complemento: string;
}

export interface DataJudResult {
  numero: string;
  tribunal: string;
  vara: string;
  classe: string;
  assuntos: string[];
  partes: {
    autor: DataJudParte;
    reu: DataJudParte;
  };
  valor_causa: number;
  data_distribuicao: string;
  movimentacoes: DataJudMovimentacao[];
  status: string;
}

export interface DataJudSyncResult {
  success: boolean;
  updated_fields: string[];
  datajud_data: DataJudResult;
  message: string;
}

const BASE = '/api/v1/processos/datajud';

// ── Hooks ──

export function useDataJudSearch() {
  return useMutation({
    mutationFn: async (numero_processo: string) => {
      const res = await api.post<DataJudResult>(`${BASE}/buscar/`, { numero_processo });
      return res.data;
    },
  });
}

export function useDataJudSync() {
  return useMutation({
    mutationFn: async (caseId: string) => {
      const res = await api.post<DataJudSyncResult>(`${BASE}/sync/${caseId}/`);
      return res.data;
    },
  });
}

export function useDataJudMovimentacoes(numero_processo: string | undefined, limit?: number) {
  return useQuery({
    queryKey: ['datajud-movimentacoes', numero_processo, limit],
    queryFn: async () => {
      const params: Record<string, string> = { numero_processo: numero_processo! };
      if (limit) params.limit = String(limit);
      const res = await api.get<DataJudMovimentacao[]>(`${BASE}/movimentacoes/`, { params });
      return res.data;
    },
    enabled: !!numero_processo,
  });
}
