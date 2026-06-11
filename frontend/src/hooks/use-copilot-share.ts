'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

export interface CopilotShare {
  share_code: string;
  session_id: string;
  is_public: boolean;
  expires_at: string | null;
  access_count: number;
  created_at: string;
  shared_with_count: number;
}

export interface ShareData {
  session_id: string;
  created_by_email: string;
  created_at: string;
  is_public: boolean;
  access_count: number;
}

/**
 * Hook para compartilhamento de sessões do Copilot
 */
export function useCopilotShare() {
  const queryClient = useQueryClient();

  // Listar compartilhamentos
  const { data: shares = [], isLoading: loadingShares } = useQuery<CopilotShare[]>({
    queryKey: ['copilot-shares'],
    queryFn: async () => {
      const response = await api.get('/api/v1/copilot/share/list/');
      return response.data.shares || [];
    },
  });

  // Criar compartilhamento
  const createShareMutation = useMutation({
    mutationFn: async (params: {
      session_id: string;
      shared_with_emails?: string[];
      is_public?: boolean;
      expires_days?: number;
    }) => {
      const response = await api.post('/api/v1/copilot/share/create/', params);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['copilot-shares'] });
    },
  });

  // Obter compartilhamento
  const getShareMutation = useMutation({
    mutationFn: async (share_code: string) => {
      const response = await api.get(`/api/v1/copilot/share/${share_code}/`);
      return response.data as ShareData;
    },
  });

  // Excluir compartilhamento
  const deleteShareMutation = useMutation({
    mutationFn: async (share_code: string) => {
      await api.post(`/api/v1/copilot/share/${share_code}/delete/`);
      return share_code;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['copilot-shares'] });
    },
  });

  // Revogar acesso
  const revokeShareMutation = useMutation({
    mutationFn: async (params: { share_code: string; email: string }) => {
      await api.post(`/api/v1/copilot/share/${params.share_code}/revoke/`, {
        email: params.email,
      });
      return params.share_code;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['copilot-shares'] });
    },
  });

  const createShare = (params: {
    session_id: string;
    shared_with_emails?: string[];
    is_public?: boolean;
    expires_days?: number;
  }) => {
    createShareMutation.mutate(params);
  };

  const getShare = (share_code: string) => {
    getShareMutation.mutate(share_code);
  };

  const deleteShare = (share_code: string) => {
    deleteShareMutation.mutate(share_code);
  };

  const revokeShare = (params: { share_code: string; email: string }) => {
    revokeShareMutation.mutate(params);
  };

  return {
    // Dados
    shares,

    // Estado
    loadingShares,
    isCreating: createShareMutation.isPending,
    shareData: getShareMutation.data,
    isLoadingShare: getShareMutation.isPending,

    // Ações
    createShare,
    getShare,
    deleteShare,
    revokeShare,
  };
}
