'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

export interface DocumentGenerator {
  id: string;
  name: string;
  description?: string;
  document_type: string;
  specialty: string;
  specialty_display?: string;
  document_template_name?: string | null;
  icon?: string;
  color?: string;
  display_order: number;
  llm_provider: 'openai' | 'anthropic';
  provider_display: string;
  model_name: string;
  temperature: number;
  max_tokens: number;
  variable_count: number;
  use_rag: boolean;
  rag_query_template?: string;
  is_active: boolean;
  is_default: boolean;
  created_by_name?: string | null;
  created_at: string;
  updated_at: string;
  system_prompt: string;
  user_prompt_template: string;
  document_template?: string | null;
}

export interface DocumentGeneratorStats {
  total: number;
  active: number;
  by_provider: {
    openai: { name: string; count: number };
    anthropic: { name: string; count: number };
  };
}

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

interface CreateDocumentGeneratorData {
  name: string;
  description?: string;
  document_type: string;
  specialty?: string;
  document_template?: string | null;
  icon?: string;
  color?: string;
  display_order?: number;
  system_prompt: string;
  user_prompt_template: string;
  llm_provider: 'openai' | 'anthropic';
  model_name: string;
  temperature: number;
  max_tokens: number;
  use_rag: boolean;
  rag_query_template?: string;
  knowledge_bases?: string[];
  is_active: boolean;
  is_default: boolean;
}

interface UpdateDocumentGeneratorData {
  name?: string;
  description?: string;
  document_type?: string;
  specialty?: string;
  document_template?: string | null;
  icon?: string;
  color?: string;
  display_order?: number;
  system_prompt?: string;
  user_prompt_template?: string;
  llm_provider?: 'openai' | 'anthropic';
  model_name?: string;
  temperature?: number;
  max_tokens?: number;
  use_rag?: boolean;
  rag_query_template?: string;
  knowledge_bases?: string[];
  is_active?: boolean;
  is_default?: boolean;
}

interface UseDocumentGeneratorsFilters {
  document_type?: string;
  llm_provider?: string;
  active_only?: boolean;
  ordering?: string;
  specialty?: string;
}

export function useDocumentGenerators(page = 1, pageSize = 100, filters?: UseDocumentGeneratorsFilters) {
  const queryClient = useQueryClient();

  // Listar Document Generators
  const {
    data: generatorsData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['document-generators', page, pageSize, filters],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<DocumentGenerator>>('/api/v1/documents/generators/', {
        params: {
          page,
          page_size: pageSize,
          ...filters
        },
      });
      return response.data;
    },
  });

  // Buscar um Document Generator específico
  const useDocumentGenerator = (id: string) => {
    return useQuery({
      queryKey: ['document-generator', id],
      queryFn: async () => {
        const response = await api.get<DocumentGenerator>(`/api/v1/documents/generators/${id}/`);
        return response.data;
      },
      enabled: !!id,
    });
  };

  // Criar novo Document Generator
  const createMutation = useMutation({
    mutationFn: async (data: CreateDocumentGeneratorData) => {
      const response = await api.post<DocumentGenerator>('/api/v1/documents/generators/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document-generators'] });
      queryClient.invalidateQueries({ queryKey: ['document-generators-stats'] });
    },
  });

  // Atualizar Document Generator
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: UpdateDocumentGeneratorData }) => {
      const response = await api.patch<DocumentGenerator>(`/api/v1/documents/generators/${id}/`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document-generators'] });
      queryClient.invalidateQueries({ queryKey: ['document-generator'] });
      queryClient.invalidateQueries({ queryKey: ['document-generators-stats'] });
    },
  });

  // Deletar Document Generator
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/documents/generators/${id}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document-generators'] });
      queryClient.invalidateQueries({ queryKey: ['document-generators-stats'] });
    },
  });

  // Duplicar Document Generator
  const duplicateMutation = useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<DocumentGenerator>(`/api/v1/documents/generators/${id}/duplicate/`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document-generators'] });
      queryClient.invalidateQueries({ queryKey: ['document-generators-stats'] });
    },
  });

  // Hook para buscar estatísticas
  const useStats = () => {
    return useQuery({
      queryKey: ['document-generators-stats'],
      queryFn: async () => {
        const response = await api.get<DocumentGeneratorStats>('/api/v1/documents/generators/stats/');
        return response.data;
      },
    });
  };

  return {
    // Data
    generators: generatorsData?.results || [],
    count: generatorsData?.count || 0,
    next: generatorsData?.next,
    previous: generatorsData?.previous,

    // States
    isLoading,
    error,
    refetch,

    // Mutations
    createGenerator: createMutation.mutateAsync,
    isCreating: createMutation.isPending,
    updateGenerator: updateMutation.mutateAsync,
    isUpdating: updateMutation.isPending,
    deleteGenerator: deleteMutation.mutateAsync,
    isDeleting: deleteMutation.isPending,
    duplicateGenerator: duplicateMutation.mutateAsync,
    isDuplicating: duplicateMutation.isPending,

    // Hooks
    useDocumentGenerator,
    useStats,
  };
}
