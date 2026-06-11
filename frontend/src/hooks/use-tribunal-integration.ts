'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

export interface TribunalIntegration {
  id: string;
  name: string;
  code: string;
  system_type: 'esaj' | 'pje' | 'eproc' | 'projudi' | 'outro';
  system_type_display?: string;
  api_endpoint: string;
  requires_certificate: boolean;
  is_active: boolean;
  connection_status: 'connected' | 'error' | 'testing' | 'unknown';
  connection_status_display?: string;
  last_connection_test?: string;
  created_at: string;
  updated_at: string;
}

export interface ProcessSync {
  id: string;
  tribunal: string;
  tribunal_name: string;
  tribunal_code: string;
  process_number: string;
  case_id?: string;
  status: 'pending' | 'syncing' | 'completed' | 'error';
  status_display?: string;
  last_sync_at?: string;
  next_sync_at?: string;
  sync_count: number;
  last_error?: string;
  last_error_at?: string;
  created_at: string;
  updated_at: string;
}

export interface ProcessMovement {
  id: string;
  process_sync: string;
  movement_date: string;
  movement_code: string;
  movement_description: string;
  complement: string;
  document_id?: string;
  source: string;
  created_at: string;
}

export interface PetitionProtocol {
  id: string;
  tribunal: string;
  tribunal_name: string;
  process_number: string;
  petition_type: 'inicial' | 'contestacao' | 'replica' | 'recurso' | 'pedido' | 'outro';
  petition_type_display?: string;
  petition_title: string;
  petition_content: string;
  attachments: string[];
  protocol_number?: string;
  protocol_date?: string;
  protocol_receipt?: string;
  status: 'draft' | 'sending' | 'sent' | 'confirmed' | 'rejected' | 'error';
  status_display?: string;
  last_error?: string;
  last_error_at?: string;
  created_by: number;
  created_by_name?: string;
  created_at: string;
  updated_at: string;
}

/**
 * Hook para Integração com Tribunais
 */
export function useTribunalIntegration() {
  const queryClient = useQueryClient();

  // Listar tribunais
  const { data: tribunais = [], isLoading: loadingTribunais } = useQuery<TribunalIntegration[]>({
    queryKey: ['tribunais'],
    queryFn: async () => {
      const response = await api.get('/api/v1/integration/tribunais/');
      return response.data.results || [];
    },
  });

  // Listar sincronizações
  const { data: syncs = [], isLoading: loadingSyncs } = useQuery<ProcessSync[]>({
    queryKey: ['process-syncs'],
    queryFn: async () => {
      const response = await api.get('/api/v1/integration/processes/');
      return response.data.results || [];
    },
  });

  // Listar petições
  const { data: petitions = [] } = useQuery<PetitionProtocol[]>({
    queryKey: ['petitions'],
    queryFn: async () => {
      const response = await api.get('/api/v1/integration/petitions/');
      return response.data.results || [];
    },
  });

  // Mutation para testar conexão
  const testConnectionMutation = useMutation({
    mutationFn: async (tribunalId: string) => {
      const response = await api.post(`/api/v1/integration/tribunais/${tribunalId}/test-connection/`);
      return response.data;
    },
  });

  // Mutation para criar tribunal
  const createTribunalMutation = useMutation({
    mutationFn: async (data: Partial<TribunalIntegration>) => {
      const response = await api.post('/api/v1/integration/tribunais/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tribunais'] });
    },
  });

  // Mutation para sincronizar processo
  const syncProcessMutation = useMutation({
    mutationFn: async (params: { tribunal_id: string; process_number: string; case_id?: string }) => {
      const response = await api.post('/api/v1/integration/processes/sync/', params);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['process-syncs'] });
    },
  });

  // Mutation para enviar petição
  const sendPetitionMutation = useMutation({
    mutationFn: async (petitionId: string) => {
      const response = await api.post(`/api/v1/integration/petitions/${petitionId}/send/`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['petitions'] });
    },
  });

  // Mutation para criar petição
  const createPetitionMutation = useMutation({
    mutationFn: async (data: Partial<PetitionProtocol>) => {
      const response = await api.post('/api/v1/integration/petitions/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['petitions'] });
    },
  });

  return {
    // Dados
    tribunais,
    syncs,
    petitions,

    // Loading
    loadingTribunais,
    loadingSyncs,
    isTestingConnection: testConnectionMutation.isPending,
    isSyncing: syncProcessMutation.isPending,
    isSending: sendPetitionMutation.isPending,

    // Ações
    testConnection: testConnectionMutation.mutate,
    createTribunal: createTribunalMutation.mutate,
    syncProcess: syncProcessMutation.mutate,
    sendPetition: sendPetitionMutation.mutate,
    createPetition: createPetitionMutation.mutate,
  };
}

/**
 * Hook para detalhes de sincronização
 */
export function useProcessSync(syncId: string | null) {
  return useQuery({
    queryKey: ['process-sync-detail', syncId],
    queryFn: async () => {
      if (!syncId) return null;
      const response = await api.get(`/api/v1/integration/processes/${syncId}/movements/`);
      return response.data;
    },
    enabled: !!syncId,
  });
}
