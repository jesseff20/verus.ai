'use client';

import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import type {
  AssistantAnalytics,
  AnalyticsSummaryResponse,
  WordCloudData,
  PaginatedResponse
} from '@/types';

export function useAnalytics() {
  // Buscar resumo dos últimos 30 dias
  const {
    data: summaryData,
    isLoading: isSummaryLoading,
    error: summaryError,
    refetch: refetchSummary,
  } = useQuery({
    queryKey: ['analytics-summary'],
    queryFn: async () => {
      const response = await api.get<AnalyticsSummaryResponse>(
        '/api/v1/agents/analytics/summary/'
      );
      return response.data;
    },
  });

  // Buscar dados de word cloud
  const {
    data: wordCloudData,
    isLoading: isWordCloudLoading,
    error: wordCloudError,
    refetch: refetchWordCloud,
  } = useQuery({
    queryKey: ['analytics-wordcloud'],
    queryFn: async () => {
      const response = await api.get<WordCloudData>(
        '/api/v1/agents/analytics/wordcloud/'
      );
      return response.data;
    },
  });

  // Listar todos os analytics (com paginação)
  const useAnalyticsList = (page = 1, pageSize = 30) => {
    return useQuery({
      queryKey: ['analytics-list', page, pageSize],
      queryFn: async () => {
        const response = await api.get<PaginatedResponse<AssistantAnalytics>>(
          '/api/v1/agents/analytics/',
          {
            params: { page, page_size: pageSize },
          }
        );
        return response.data;
      },
    });
  };

  // Buscar analytics de um dia específico
  const useAnalyticsByDate = (date: string) => {
    return useQuery({
      queryKey: ['analytics-date', date],
      queryFn: async () => {
        const response = await api.get<AssistantAnalytics>(
          `/api/v1/agents/analytics/${date}/`
        );
        return response.data;
      },
      enabled: !!date,
    });
  };

  return {
    // Summary data (30 dias)
    summary: summaryData?.summary,
    chartData: summaryData?.chart_data || [],
    feedbackTimeline: summaryData?.feedback_timeline || [],
    period: summaryData?.period,

    // Word cloud data
    wordCloudData,
    isWordCloudLoading,
    wordCloudError,

    // States
    isSummaryLoading,
    summaryError,
    refetchSummary,
    refetchWordCloud,

    // Helpers
    useAnalyticsList,
    useAnalyticsByDate,
  };
}
