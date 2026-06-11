'use client';

import { useState, useCallback } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

export interface LegalArgument {
  id: string;
  title: string;
  content: string;
  summary: string;
  category: 'preliminar' | 'merito' | 'pedido' | 'fundamentacao' | 'recurso' | 'contrarrazoes';
  category_display?: string;
  specialty: 'CIV' | 'PEN' | 'TRB' | 'FAM' | 'PRE' | 'ADM' | 'TRI' | 'EMP';
  specialty_display?: string;
  subcategories: string[];
  tribunal: string;
  effectiveness_score: number;
  usage_count: number;
  success_count: number;
  related_precedents: string[];
  created_by: number;
  created_by_name?: string;
  status: 'draft' | 'review' | 'approved' | 'archived';
  created_at: string;
  updated_at: string;
  last_used_at?: string;
}

export interface ArgumentCollection {
  id: string;
  name: string;
  description: string;
  arguments_count: number;
  arguments_list: LegalArgument[];
  created_by: number;
  created_by_name?: string;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface ArgumentStats {
  total: number;
  approved: number;
  draft: number;
  by_specialty: Array<{
    specialty: string;
    count: number;
    avg_effectiveness: number;
  }>;
  top_used: LegalArgument[];
  top_effective: LegalArgument[];
}

export interface CreateArgumentParams {
  title: string;
  content: string;
  summary?: string;
  category: string;
  specialty: string;
  subcategories?: string[];
  tribunal?: string;
  related_precedents?: string[];
}

export interface SearchParams {
  query?: string;
  specialty?: string;
  category?: string;
  tribunal?: string;
  status?: string;
  sort?: string;
  limit?: number;
}

/**
 * Hook para Biblioteca Viva de Argumentos
 *
 * @example
 * const {
 *   arguments,
 *   isLoading,
 *   createArgument,
 *   suggestArguments,
 * } = useLegalLibrary();
 */
export function useLegalLibrary() {
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useState<SearchParams>({});

  // Query para listar argumentos
  const { data: legalArguments = [], isLoading, refetch } = useQuery({
    queryKey: ['legal-arguments', searchParams],
    queryFn: async () => {
      const params = new URLSearchParams();
      Object.entries(searchParams).forEach(([key, value]) => {
        if (value) params.append(key, value.toString());
      });
      const response = await api.get(`/api/v1/legal-library/arguments/?${params}`);
      return response.data.results || [];
    },
  });

  // Query para estatísticas
  const { data: stats } = useQuery<ArgumentStats>({
    queryKey: ['legal-arguments-stats'],
    queryFn: async () => {
      const response = await api.get('/api/v1/legal-library/arguments/stats/');
      return response.data;
    },
  });

  // Query para coleções
  const { data: collections = [] } = useQuery({
    queryKey: ['argument-collections'],
    queryFn: async () => {
      const response = await api.get('/api/v1/legal-library/collections/');
      return response.data.results || [];
    },
  });

  // Mutation para criar argumento
  const createMutation = useMutation({
    mutationFn: async (params: CreateArgumentParams) => {
      const response = await api.post('/api/v1/legal-library/arguments/', params);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['legal-arguments'] });
      queryClient.invalidateQueries({ queryKey: ['legal-arguments-stats'] });
    },
  });

  // Mutation para atualizar argumento
  const updateMutation = useMutation({
    mutationFn: async ({ id, ...params }: CreateArgumentParams & { id: string }) => {
      const response = await api.patch(`/api/v1/legal-library/arguments/${id}/`, params);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['legal-arguments'] });
    },
  });

  // Mutation para deletar argumento
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/legal-library/arguments/${id}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['legal-arguments'] });
    },
  });

  // Mutation para registrar uso
  const useMutationHook = useMutation({
    mutationFn: async ({ argumentId, ...params }: { argumentId: string; document_id?: string; case_id?: string; section_title?: string }) => {
      const response = await api.post(`/api/v1/legal-library/arguments/${argumentId}/use/`, params);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['legal-arguments'] });
    },
  });

  // Mutation para registrar sucesso
  const successMutation = useMutation({
    mutationFn: async ({ argumentId, usage_id }: { argumentId: string; usage_id?: string }) => {
      const response = await api.post(`/api/v1/legal-library/arguments/${argumentId}/success/`, { usage_id });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['legal-arguments'] });
    },
  });

  // Sugerir argumentos
  const suggest = useCallback(async (params: SearchParams) => {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value) queryParams.append(key, value.toString());
    });
    const response = await api.get(`/api/v1/legal-library/arguments/suggest/?${queryParams}`);
    return response.data.suggestions || [];
  }, []);

  const createArgument = useCallback((params: CreateArgumentParams) => {
    createMutation.mutate(params);
  }, [createMutation]);

  const updateArgument = useCallback((id: string, params: Partial<CreateArgumentParams>) => {
    updateMutation.mutate({ id, ...params } as any);
  }, [updateMutation]);

  const deleteArgument = useCallback((id: string) => {
    deleteMutation.mutate(id);
  }, [deleteMutation]);

  const registerUsage = useCallback((params: { argumentId: string; document_id?: string; case_id?: string; section_title?: string }) => {
    useMutationHook.mutate(params);
  }, [useMutationHook]);

  const registerSuccess = useCallback((params: { argumentId: string; usage_id?: string }) => {
    successMutation.mutate(params);
  }, [successMutation]);

  return {
    // Estado
    arguments: legalArguments,
    collections,
    stats,

    // Loading
    isLoading,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,

    // Ações
    createArgument,
    updateArgument,
    deleteArgument,
    registerUsage,
    registerSuccess,
    suggest,
    setSearchParams,
    refetch,
  };
}

/**
 * Utilitários para formatar dados
 */
export function getCategoryColor(category: string): string {
  const colors: Record<string, string> = {
    preliminar: 'bg-yellow-100 text-yellow-700 border-yellow-300',
    merito: 'bg-blue-100 text-blue-700 border-blue-300',
    pedido: 'bg-green-100 text-green-700 border-green-300',
    fundamentacao: 'bg-purple-100 text-purple-700 border-purple-300',
    recurso: 'bg-red-100 text-red-700 border-red-300',
    contrarrazoes: 'bg-orange-100 text-orange-700 border-orange-300',
  };
  return colors[category] || 'bg-gray-100 text-gray-700 border-gray-300';
}

export function getSpecialtyIcon(specialty: string): string {
  const icons: Record<string, string> = {
    CIV: '⚖️',
    PEN: '🔒',
    TRB: '💼',
    FAM: '👨‍👩‍👧',
    PRE: '🏥',
    ADM: '🏛️',
    TRI: '💰',
    EMP: '🏢',
  };
  return icons[specialty] || '📄';
}

export function getEffectivenessLabel(score: number): string {
  if (score >= 0.8) return 'Alta';
  if (score >= 0.5) return 'Média';
  if (score > 0) return 'Baixa';
  return 'Sem dados';
}

export function getEffectivenessColor(score: number): string {
  if (score >= 0.8) return 'text-green-600';
  if (score >= 0.5) return 'text-yellow-600';
  if (score > 0) return 'text-red-600';
  return 'text-gray-400';
}
