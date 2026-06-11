'use client';

import { useState, useCallback } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

export interface PrecedentAnalysis {
  id: string;
  tribunal: string;
  case_number: string;
  outcome: 'favorable' | 'unfavorable' | 'neutral' | 'mixed';
  weight: 'binding' | 'persuasive' | 'informative';
  relevance_score: number;
  summary: string;
  judgment_date: string | null;
  relator: string | null;
  organ: string | null;
  keywords: string[];
  citation: string;
}

export interface TribunalStatistics {
  tribunal: string;
  total_cases: number;
  favorable_count: number;
  unfavorable_count: number;
  success_rate: number;
  recent_trend: 'improving' | 'worsening' | 'stable';
}

export interface ThesisStatistics {
  thesis: string;
  total_cases: number;
  favorable_count: number;
  success_rate: number;
  tribunals: Record<string, number>;
  recent_judgments: PrecedentAnalysis[];
}

export interface RadarReport {
  query: string;
  total_analyzed: number;
  overall_success_rate: number;
  tribunal_stats: TribunalStatistics[];
  thesis_stats: ThesisStatistics[];
  timeline: Array<{
    date: string;
    count: number;
    favorable: number;
    avg_score: number;
  }>;
  key_precedents: PrecedentAnalysis[];
  recommendations: string[];
  generated_at: string;
}

export interface RadarAnalysisParams {
  query: string;
  specialty?: string;
  date_range?: [string, string];
  tribunals?: string[];
  include_timeline?: boolean;
  limit_precedents?: number;
}

/**
 * Hook para Radar de Precedentes
 *
 * @example
 * const {
 *   report,
 *   isLoading,
 *   analyze,
 *   tribunais,
 *   teses,
 * } = usePrecedentRadar();
 */
export function usePrecedentRadar() {
  const [report, setReport] = useState<RadarReport | null>(null);

  // Mutation para análise
  const analyzeMutation = useMutation({
    mutationFn: async (params: RadarAnalysisParams) => {
      const response = await api.post<RadarReport>(
        '/api/v1/jurisprudence/radar/analyze/',
        params
      );
      return response.data;
    },
    onSuccess: (data) => {
      setReport(data);
    },
  });

  // Query para tribunais
  const { data: tribunais = [], isLoading: loadingTribunais } = useQuery({
    queryKey: ['radar-tribunais'],
    queryFn: async () => {
      const response = await api.get('/api/v1/jurisprudence/radar/tribunais/');
      return response.data.tribunais || [];
    },
  });

  // Query para teses
  const { data: teses = [], isLoading: loadingTeses } = useQuery({
    queryKey: ['radar-teses'],
    queryFn: async () => {
      const response = await api.get('/api/v1/jurisprudence/radar/teses/');
      return response.data.theses || [];
    },
  });

  const analyze = useCallback((params: RadarAnalysisParams) => {
    analyzeMutation.mutate(params);
  }, [analyzeMutation]);

  return {
    // Estado
    report,
    isLoading: analyzeMutation.isPending,
    error: analyzeMutation.error,

    // Dados auxiliares
    tribunais,
    teses,
    loadingTribunais,
    loadingTeses,

    // Ações
    analyze,
    clearReport: () => setReport(null),
    refetchTribunais: analyzeMutation.reset,
  };
}

/**
 * Hook para detalhes de precedente individual
 */
export function usePrecedentDetail(precedentId: string | null) {
  return useQuery({
    queryKey: ['precedent-detail', precedentId],
    queryFn: async () => {
      if (!precedentId) return null;
      const response = await api.get(
        `/api/v1/jurisprudence/radar/precedents/${precedentId}/`
      );
      return response.data;
    },
    enabled: !!precedentId,
  });
}

/**
 * Utilitários para formatar dados do Radar
 */
export function formatSuccessRate(rate: number): string {
  return `${(rate * 100).toFixed(1)}%`;
}

export function getOutcomeColor(outcome: string): string {
  switch (outcome) {
    case 'favorable':
      return 'text-green-600 bg-green-50 border-green-200';
    case 'unfavorable':
      return 'text-red-600 bg-red-50 border-red-200';
    case 'mixed':
      return 'text-orange-600 bg-orange-50 border-orange-200';
    default:
      return 'text-gray-600 bg-gray-50 border-gray-200';
  }
}

export function getWeightBadge(weight: string): string {
  switch (weight) {
    case 'binding':
      return 'bg-purple-100 text-purple-700 border-purple-300';
    case 'persuasive':
      return 'bg-blue-100 text-blue-700 border-blue-300';
    case 'informative':
      return 'bg-gray-100 text-gray-700 border-gray-300';
    default:
      return 'bg-gray-100 text-gray-700 border-gray-300';
  }
}

export function getTrendIcon(trend: string): string {
  switch (trend) {
    case 'improving':
      return '↑';
    case 'worsening':
      return '↓';
    default:
      return '→';
  }
}

export function getTrendColor(trend: string): string {
  switch (trend) {
    case 'improving':
      return 'text-green-600';
    case 'worsening':
      return 'text-red-600';
    default:
      return 'text-gray-600';
  }
}
