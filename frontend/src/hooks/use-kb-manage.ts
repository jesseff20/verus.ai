'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import type { KBManageResponse, KBSource } from '@/types';

export function useKBManage() {
  const queryClient = useQueryClient();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['managed-kbs'],
    queryFn: async () => {
      const response = await api.get<KBManageResponse>(
        '/api/v1/intelligent-assistant/knowledge-bases/manage/'
      );
      return response.data;
    },
  });

  const createKB = useMutation({
    mutationFn: async (payload: {
      name: string;
      description?: string;
      kb_layer?: string;
      blueprint?: string;
      agent_config?: string;
    }) => {
      const response = await api.post(
        '/api/v1/intelligent-assistant/knowledge-bases/manage/',
        { kb_layer: 'blueprint', ...payload }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['managed-kbs'] });
    },
  });

  const uploadToKB = useMutation({
    mutationFn: async ({ kbId, formData }: { kbId: string; formData: FormData }) => {
      const response = await api.post(
        `/api/v1/intelligent-assistant/knowledge-bases/manage/${kbId}/upload/`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 120000,
        }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['managed-kbs'] });
      queryClient.invalidateQueries({ queryKey: ['kb-sources'] });
    },
  });

  const toggleKBActive = useMutation({
    mutationFn: async ({ kbId, isActive }: { kbId: string; isActive: boolean }) => {
      const response = await api.patch(
        `/api/v1/intelligent-assistant/knowledge-bases/manage/${kbId}/`,
        { is_active: isActive }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['managed-kbs'] });
    },
  });

  const deleteKB = useMutation({
    mutationFn: async (kbId: string) => {
      await api.delete(
        `/api/v1/intelligent-assistant/knowledge-bases/manage/${kbId}/`
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['managed-kbs'] });
    },
  });

  const deleteSource = useMutation({
    mutationFn: async ({ kbId, sourceName }: { kbId: string; sourceName: string }) => {
      const response = await api.delete(
        `/api/v1/intelligent-assistant/knowledge-bases/manage/${kbId}/sources/${encodeURIComponent(sourceName)}/`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['managed-kbs'] });
      queryClient.invalidateQueries({ queryKey: ['kb-sources'] });
    },
  });

  return {
    allKBs: data?.knowledge_bases || [],
    blueprintKBs: data?.blueprint_kbs || [],
    agentKBs: data?.agent_kbs || [],
    total: data?.total || 0,
    isLoading,
    error,
    refetch,
    createKB: createKB.mutate,
    createKBAsync: createKB.mutateAsync,
    isCreating: createKB.isPending,
    uploadToKB: uploadToKB.mutate,
    isUploading: uploadToKB.isPending,
    toggleKBActive: toggleKBActive.mutate,
    isToggling: toggleKBActive.isPending,
    deleteKB: deleteKB.mutate,
    isDeletingKB: deleteKB.isPending,
    deleteSource: deleteSource.mutate,
    isDeletingSource: deleteSource.isPending,
  };
}

export function useKBSources(kbId: string | null) {
  return useQuery({
    queryKey: ['kb-sources', kbId],
    queryFn: async () => {
      if (!kbId) return { sources: [], total_sources: 0 };
      const response = await api.get<{
        kb_id: string;
        kb_name: string;
        sources: KBSource[];
        total_sources: number;
      }>(`/api/v1/intelligent-assistant/knowledge-bases/manage/${kbId}/sources/`);
      return response.data;
    },
    enabled: !!kbId,
  });
}
