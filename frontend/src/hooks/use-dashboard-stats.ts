'use client';

import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

// ========================================
// TIPOS
// ========================================

export interface DashboardStats {
  documents: {
    total: number;
    traditional: number;
    assistant: number;
    by_status: {
      draft: number;
      in_review: number;
      completed: number;
      archived: number;
    };
  };
  knowledge_base: {
    total: number;
  };
  notifications: {
    pending_review: number;
  };
  recent_documents: RecentDocument[];
}

export interface RecentDocument {
  id: string;
  title: string;
  status: string;
  status_display: string;
  source: 'manual' | 'generator' | 'assistant';
  source_display: string;
  system: 'documents' | 'intelligent_assistant';
  created_at: string;
  user_name: string;
}

// ========================================
// HOOK
// ========================================

/**
 * Hook para buscar estatísticas do dashboard
 *
 * Retorna:
 * - Total de documentos (ambos sistemas)
 * - Documentos por status
 * - Total de documentos na Knowledge Base
 * - Notificações pendentes
 * - Documentos recentes (últimos 5)
 */
export function useDashboardStats() {
  const {
    data,
    isLoading,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await api.get<DashboardStats>(
        '/api/v1/documents/items/dashboard_stats/'
      );
      return response.data;
    },
    staleTime: 60000, // 1 minuto de cache
    refetchOnWindowFocus: true,
  });

  return {
    // Data
    stats: data,
    documents: data?.documents,
    knowledgeBase: data?.knowledge_base,
    notifications: data?.notifications,
    recentDocuments: data?.recent_documents || [],

    // States
    isLoading,
    isFetching,
    error,

    // Actions
    refetch,
  };
}
