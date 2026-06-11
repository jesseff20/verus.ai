'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import type { AgentKnowledgeBaseLink } from '@/types';

export function useAgentKBLinks(kbId: string | null) {
  const queryClient = useQueryClient();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['agent-kb-links', kbId],
    queryFn: async () => {
      if (!kbId) return { links: [], total: 0 };
      const response = await api.get<{
        kb_id: string;
        kb_name: string;
        links: AgentKnowledgeBaseLink[];
        total: number;
      }>(`/api/v1/intelligent-assistant/knowledge-bases/manage/${kbId}/agent-links/`);
      return response.data;
    },
    enabled: !!kbId,
  });

  const createLink = useMutation({
    mutationFn: async (payload: {
      agent: string;
      priority?: number;
      purpose?: string;
      instruction?: string;
      top_k?: number;
      min_similarity?: number;
      include_summary?: boolean;
    }) => {
      const response = await api.post(
        `/api/v1/intelligent-assistant/knowledge-bases/manage/${kbId}/agent-links/`,
        payload
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-kb-links', kbId] });
      queryClient.invalidateQueries({ queryKey: ['managed-kbs'] });
    },
  });

  const updateLink = useMutation({
    mutationFn: async ({ linkId, ...payload }: {
      linkId: string;
      priority?: number;
      purpose?: string;
      instruction?: string;
      top_k?: number;
      min_similarity?: number;
      include_summary?: boolean;
    }) => {
      const response = await api.patch(
        `/api/v1/intelligent-assistant/knowledge-bases/manage/${kbId}/agent-links/${linkId}/`,
        payload
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-kb-links', kbId] });
    },
  });

  const deleteLink = useMutation({
    mutationFn: async (linkId: string) => {
      await api.delete(
        `/api/v1/intelligent-assistant/knowledge-bases/manage/${kbId}/agent-links/${linkId}/`
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-kb-links', kbId] });
      queryClient.invalidateQueries({ queryKey: ['managed-kbs'] });
    },
  });

  return {
    links: data?.links || [],
    total: data?.total || 0,
    isLoading,
    error,
    refetch,
    createLink: createLink.mutate,
    createLinkAsync: createLink.mutateAsync,
    isCreatingLink: createLink.isPending,
    updateLink: updateLink.mutate,
    isUpdatingLink: updateLink.isPending,
    deleteLink: deleteLink.mutate,
    isDeletingLink: deleteLink.isPending,
  };
}
