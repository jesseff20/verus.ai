'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import type { AgentPrompt, PaginatedResponse, AgentStats, AgentsByCategory } from '@/types';

interface CreateAgentData {
  name: string;
  description?: string;
  agent_type: string;
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

interface UpdateAgentData {
  name?: string;
  description?: string;
  agent_type?: string;
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

interface ExecuteAgentData {
  id: string;
  variables: Record<string, any>;
  user_input?: string;
}

interface UseAgentsFilters {
  agent_type?: string;
  active_only?: boolean;
  ordering?: string;
}

export function useAgents(page = 1, pageSize = 20, filters?: UseAgentsFilters) {
  const queryClient = useQueryClient();

  // Listar Agentes
  const {
    data: agentsData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['agents', page, pageSize, filters],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<AgentPrompt>>('/api/v1/agents/', {
        params: {
          page,
          page_size: pageSize,
          ...filters
        },
      });
      return response.data;
    },
  });

  // Buscar um Agente específico
  const useAgent = (id: string) => {
    return useQuery({
      queryKey: ['agent', id],
      queryFn: async () => {
        const response = await api.get<AgentPrompt>(`/api/v1/agents/${id}/`);
        return response.data;
      },
      enabled: !!id,
    });
  };

  // Criar novo Agente
  const createMutation = useMutation({
    mutationFn: async (data: CreateAgentData) => {
      const response = await api.post<AgentPrompt>('/api/v1/agents/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });

  // Atualizar Agente
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: UpdateAgentData }) => {
      const response = await api.patch<AgentPrompt>(`/api/v1/agents/${id}/`, data);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      queryClient.invalidateQueries({ queryKey: ['agent', data.id] });
    },
  });

  // Deletar Agente
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/agents/${id}/`);
      return id;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });

  // Executar Agente (chamar LLM)
  const executeMutation = useMutation({
    mutationFn: async ({ id, variables, user_input }: ExecuteAgentData) => {
      const response = await api.post(`/api/v1/agents/${id}/execute/`, {
        variables,
        user_input,
      });
      return response.data;
    },
  });

  // Duplicar Agente
  const duplicateMutation = useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<AgentPrompt>(`/api/v1/agents/${id}/duplicate/`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });

  // Hook para buscar estatísticas
  const useStats = () => {
    return useQuery({
      queryKey: ['agent-stats'],
      queryFn: async () => {
        const response = await api.get<AgentStats>('/api/v1/agents/stats/');
        return response.data;
      },
    });
  };

  // Hook para buscar agentes por categoria
  const useByCategory = () => {
    return useQuery({
      queryKey: ['agents-by-category'],
      queryFn: async () => {
        const response = await api.get<AgentsByCategory>('/api/v1/agents/by_category/');
        return response.data;
      },
    });
  };

  return {
    // Data
    agents: agentsData?.results || [],
    count: agentsData?.count || 0,
    next: agentsData?.next,
    previous: agentsData?.previous,

    // States
    isLoading,
    error,
    refetch,

    // Mutations (async versions)
    createAgent: createMutation.mutateAsync,
    updateAgent: updateMutation.mutateAsync,
    deleteAgent: deleteMutation.mutateAsync,
    executeAgent: executeMutation.mutateAsync,
    duplicateAgent: duplicateMutation.mutateAsync,

    // Mutations (callback versions)
    createAgentWithCallbacks: createMutation.mutate,
    updateAgentWithCallbacks: updateMutation.mutate,
    deleteAgentWithCallbacks: deleteMutation.mutate,
    executeAgentWithCallbacks: executeMutation.mutate,
    duplicateAgentWithCallbacks: duplicateMutation.mutate,

    // Loading states
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
    isExecuting: executeMutation.isPending,
    isDuplicating: duplicateMutation.isPending,

    // Helpers
    useAgent,

    // Dashboard hooks
    useStats,
    useByCategory,
  };
}
