'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import type { SectionAgent, BlueprintAgentsResponse } from '@/types';

export function useSectionAgents() {
  return useQuery({
    queryKey: ['section-agents'],
    queryFn: async () => {
      const response = await api.get<{
        agents: SectionAgent[];
        total: number;
      }>('/api/v1/intelligent-assistant/section-agents/');
      return response.data;
    },
  });
}

export function useBlueprintAgents(blueprintId: string) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ['blueprint-agents', blueprintId],
    queryFn: async () => {
      const response = await api.get<BlueprintAgentsResponse>(
        `/api/v1/intelligent-assistant/blueprints/${blueprintId}/agents/`
      );
      return response.data;
    },
    enabled: !!blueprintId,
  });

  const updateMutation = useMutation({
    mutationFn: async ({ agentId, data }: { agentId: string; data: Record<string, unknown> }) => {
      const response = await api.patch(
        `/api/v1/intelligent-assistant/agents/${agentId}/update/`,
        data
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blueprint-agents', blueprintId] });
    },
  });

  const createMutation = useMutation({
    mutationFn: async (data: Record<string, unknown>) => {
      const response = await api.post(
        '/api/v1/intelligent-assistant/agents/create/',
        data
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blueprint-agents', blueprintId] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (agentId: string) => {
      await api.delete(`/api/v1/intelligent-assistant/agents/${agentId}/delete/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blueprint-agents', blueprintId] });
    },
  });

  return {
    agents: query.data?.agents || [],
    total: query.data?.total || 0,
    isLoading: query.isLoading,
    refetch: query.refetch,
    updateAgent: updateMutation.mutateAsync,
    isUpdating: updateMutation.isPending,
    createAgent: createMutation.mutateAsync,
    isCreating: createMutation.isPending,
    deleteAgent: deleteMutation.mutateAsync,
    isDeleting: deleteMutation.isPending,
  };
}
