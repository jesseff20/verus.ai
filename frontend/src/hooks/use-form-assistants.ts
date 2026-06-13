'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

export interface FormAssistant {
  id: string;
  name: string;
  description?: string;
  assistant_type: string;
  icon?: string;
  color?: string;
  display_order: number;
  llm_provider: 'openai' | 'anthropic' | 'watsonx';
  provider_display: string;
  model_name: string;
  temperature: number;
  max_tokens: number;
  variable_count: number;
  use_rag: boolean;
  rag_query_template?: string;
  is_active: boolean;
  is_default: boolean;
  created_by_name?: string;
  created_at: string;
  updated_at: string;
  system_prompt: string;
  user_prompt_template: string;
}

export interface FormAssistantStats {
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

interface CreateFormAssistantData {
  name: string;
  description?: string;
  assistant_type: string;
  icon?: string;
  color?: string;
  display_order?: number;
  system_prompt: string;
  user_prompt_template: string;
  llm_provider: 'openai' | 'anthropic' | 'watsonx';
  model_name: string;
  temperature: number;
  max_tokens: number;
  use_rag: boolean;
  rag_query_template?: string;
  is_active: boolean;
  is_default: boolean;
}

interface UpdateFormAssistantData {
  name?: string;
  description?: string;
  assistant_type?: string;
  icon?: string;
  color?: string;
  display_order?: number;
  system_prompt?: string;
  user_prompt_template?: string;
  llm_provider?: 'openai' | 'anthropic' | 'watsonx';
  model_name?: string;
  temperature?: number;
  max_tokens?: number;
  use_rag?: boolean;
  rag_query_template?: string;
  is_active?: boolean;
  is_default?: boolean;
}

interface UseFormAssistantsFilters {
  assistant_type?: string;
  llm_provider?: string;
  active_only?: boolean;
  ordering?: string;
}

export function useFormAssistants(page = 1, pageSize = 100, filters?: UseFormAssistantsFilters) {
  const queryClient = useQueryClient();

  // Listar Form Assistants
  const {
    data: assistantsData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['form-assistants', page, pageSize, filters],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<FormAssistant>>('/api/v1/forms/assistants/', {
        params: {
          page,
          page_size: pageSize,
          ...filters
        },
      });
      return response.data;
    },
  });

  // Buscar um Form Assistant específico
  const useFormAssistant = (id: string) => {
    return useQuery({
      queryKey: ['form-assistant', id],
      queryFn: async () => {
        const response = await api.get<FormAssistant>(`/api/v1/forms/assistants/${id}/`);
        return response.data;
      },
      enabled: !!id,
    });
  };

  // Criar novo Form Assistant
  const createMutation = useMutation({
    mutationFn: async (data: CreateFormAssistantData) => {
      const response = await api.post<FormAssistant>('/api/v1/forms/assistants/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['form-assistants'] });
      queryClient.invalidateQueries({ queryKey: ['form-assistants-stats'] });
    },
  });

  // Atualizar Form Assistant
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: UpdateFormAssistantData }) => {
      const response = await api.patch<FormAssistant>(`/api/v1/forms/assistants/${id}/`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['form-assistants'] });
      queryClient.invalidateQueries({ queryKey: ['form-assistant'] });
      queryClient.invalidateQueries({ queryKey: ['form-assistants-stats'] });
    },
  });

  // Deletar Form Assistant
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/forms/assistants/${id}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['form-assistants'] });
      queryClient.invalidateQueries({ queryKey: ['form-assistants-stats'] });
    },
  });

  // Duplicar Form Assistant
  const duplicateMutation = useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<FormAssistant>(`/api/v1/forms/assistants/${id}/duplicate/`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['form-assistants'] });
      queryClient.invalidateQueries({ queryKey: ['form-assistants-stats'] });
    },
  });

  // Hook para buscar estatísticas
  const useStats = () => {
    return useQuery({
      queryKey: ['form-assistants-stats'],
      queryFn: async () => {
        const response = await api.get<FormAssistantStats>('/api/v1/forms/assistants/stats/');
        return response.data;
      },
    });
  };

  return {
    // Data
    assistants: assistantsData?.results || [],
    count: assistantsData?.count || 0,
    next: assistantsData?.next,
    previous: assistantsData?.previous,

    // States
    isLoading,
    error,
    refetch,

    // Mutations
    createAssistant: createMutation.mutateAsync,
    isCreating: createMutation.isPending,
    updateAssistant: updateMutation.mutateAsync,
    isUpdating: updateMutation.isPending,
    deleteAssistant: deleteMutation.mutateAsync,
    isDeleting: deleteMutation.isPending,
    duplicateAssistant: duplicateMutation.mutateAsync,
    isDuplicating: duplicateMutation.isPending,

    // Hooks
    useFormAssistant,
    useStats,
  };
}
