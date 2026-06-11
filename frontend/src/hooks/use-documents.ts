'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import type { ETP, PaginatedResponse, GenerateETPDynamicResponse } from '@/types';

// ========================================
// TIPOS PARA DOCUMENTOS UNIFICADOS
// ========================================

export interface UnifiedDocument {
  id: string;
  title: string;
  numero_processo: string | null;
  user_id: number | null;
  user_name: string;
  source: 'manual' | 'generator' | 'assistant';
  source_display: string;
  status: string;
  status_display: string;
  system: 'documents' | 'intelligent_assistant';
  system_display: string;
  form_template_name: string | null;
  document_generator_name: string | null;
  blueprint_name?: string | null;
  document_type?: string | null;
  progress: number;
  version: number;
  created_at: string;
  updated_at: string;
  has_generated_content: boolean;
  pdf_url: string | null;
  preview_url: string | null;
  detail_url: string;
}

export interface UnifiedDocumentsResponse {
  count: number;
  results: UnifiedDocument[];
  filters_applied: {
    status: string | null;
    source: string | null;
    user_id: string | null;
    search: string | null;
    system: string | null;
  };
}

export interface UnifiedDocumentsFilters {
  status?: string;
  source?: 'manual' | 'generator' | 'assistant';
  user_id?: string;
  search?: string;
  system?: 'documents' | 'intelligent_assistant';
}

// ========================================
// TIPOS PARA DOCUMENTS TRADICIONAIS
// ========================================

interface CreateDocumentData {
  title: string;
  numero_processo?: string;
  form_template: string;
  document_template?: string;
  data: Record<string, any>;
}

interface UpdateDocumentData {
  title?: string;
  numero_processo?: string;
  document_template?: string;
  data?: Record<string, any>;
  status?: 'rascunho' | 'em_analise' | 'aprovado' | 'rejeitado' | 'finalizado';
}

export function useDocuments(page = 1, pageSize = 20) {
  const queryClient = useQueryClient();

  // Listar Documents
  const {
    data: DocumentsData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['documents', page, pageSize],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<ETP>>('/api/v1/documents/items/', {
        params: { page, page_size: pageSize },
      });
      return response.data;
    },
  });

  // Buscar um documento específico
  const useDocument = (id: string) => {
    return useQuery({
      queryKey: ['document', id],
      queryFn: async () => {
        const response = await api.get<ETP>(`/api/v1/documents/items/${id}/`);
        return response.data;
      },
      enabled: !!id,
    });
  };

  // Criar novo documento
  const createMutation = useMutation({
    mutationFn: async (data: CreateDocumentData) => {
      const response = await api.post<ETP>('/api/v1/documents/items/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  // Atualizar documento
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: UpdateDocumentData }) => {
      const response = await api.patch<ETP>(`/api/v1/documents/items/${id}/`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  // Deletar documento
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/documents/items/${id}/`);
      return id;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  // Gerar documento HTML (sistema antigo)
  const generateMutation = useMutation({
    mutationFn: async (id: string) => {
      // Aumentar timeout para 2 minutos (120 segundos) pois IA pode demorar
      const response = await api.post(`/api/v1/documents/items/${id}/generate/`, {}, {
        timeout: 120000, // 2 minutos
      });
      return response.data;
    },
    onSuccess: async (data, id) => {
      await queryClient.invalidateQueries({ queryKey: ['document', id] });
    },
  });

  // Gerar documento com Blueprint Dinâmico (novo sistema)
  const generateDynamicMutation = useMutation({
    mutationFn: async ({
      blueprintId,
      blueprintName,
      objective,
      collectionName,
    }: {
      blueprintId?: string;
      blueprintName?: string;
      objective: string;
      collectionName?: string;
    }) => {
      const response = await api.post<GenerateETPDynamicResponse>(
        '/api/v1/intelligent-assistant/generate/',
        {
          blueprint_id: blueprintId,
          blueprint_name: blueprintName,
          objective,
          collection_name: collectionName,
        },
        {
          timeout: 300000, // 5 minutos (mais seções = mais tempo)
        }
      );
      return response.data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['documents'] });
      await queryClient.invalidateQueries({ queryKey: ['generation-sessions'] });
    },
  });

  // Completar documento
  const completeMutation = useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post(`/api/v1/documents/items/${id}/complete/`);
      return response.data;
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['document', id] });
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  // Criar nova versão
  const createVersionMutation = useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<ETP>(`/api/v1/documents/items/${id}/create_version/`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  return {
    // Data
    Documents: DocumentsData?.results || [],
    count: DocumentsData?.count || 0,
    next: DocumentsData?.next,
    previous: DocumentsData?.previous,

    // States
    isLoading,
    error,

    // Mutations (async versions)
    createDocument: createMutation.mutateAsync,
    updateDocument: updateMutation.mutateAsync,
    deleteDocument: deleteMutation.mutateAsync,
    generateDocument: generateMutation.mutateAsync,
    generateDocumentDynamic: generateDynamicMutation.mutateAsync,
    completeDocument: completeMutation.mutateAsync,
    createVersion: createVersionMutation.mutateAsync,
    // Aliases legados - manter compatibilidade
    createETP: createMutation.mutateAsync,
    updateETP: updateMutation.mutateAsync,
    deleteETP: deleteMutation.mutateAsync,
    completeETP: completeMutation.mutateAsync,

    // Mutations (callback versions)
    createDocumentWithCallbacks: createMutation.mutate,
    updateDocumentWithCallbacks: updateMutation.mutate,
    deleteDocumentWithCallbacks: deleteMutation.mutate,
    generateDocumentWithCallbacks: generateMutation.mutate,
    generateDocumentDynamicWithCallbacks: generateDynamicMutation.mutate,
    completeDocumentWithCallbacks: completeMutation.mutate,
    createVersionWithCallbacks: createVersionMutation.mutate,
    // Aliases legados - manter compatibilidade
    createETPWithCallbacks: createMutation.mutate,
    updateETPWithCallbacks: updateMutation.mutate,
    deleteETPWithCallbacks: deleteMutation.mutate,
    completeETPWithCallbacks: completeMutation.mutate,

    // Loading states
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
    isGenerating: generateMutation.isPending,
    isGeneratingDynamic: generateDynamicMutation.isPending,
    isCompleting: completeMutation.isPending,
    isCreatingVersion: createVersionMutation.isPending,

    // Helpers
    useDocument,
    // Alias legado - manter compatibilidade
    useETP: useDocument,
  };
}

// ========================================
// HOOK PARA DOCUMENTOS UNIFICADOS
// ========================================

/**
 * Hook para buscar documentos de ambos os sistemas combinados:
 * - Document (sistema tradicional de geradores)
 * - GeneratedDocument (assistente inteligente)
 *
 * Suporta filtros por:
 * - status: draft, in_review, completed, archived
 * - source: manual, generator, assistant
 * - user_id: Filtrar por usuário (Manager+ apenas)
 * - search: Buscar por título ou processo
 * - system: documents, intelligent_assistant
 */
export function useUnifiedDocuments(filters?: UnifiedDocumentsFilters) {
  const queryClient = useQueryClient();

  const {
    data,
    isLoading,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['unified-documents', filters],
    queryFn: async () => {
      const params = new URLSearchParams();

      if (filters?.status) params.append('status', filters.status);
      if (filters?.source) params.append('source', filters.source);
      if (filters?.user_id) params.append('user_id', filters.user_id);
      if (filters?.search) params.append('search', filters.search);
      if (filters?.system) params.append('system', filters.system);

      const response = await api.get<UnifiedDocumentsResponse>(
        `/api/v1/documents/items/unified/?${params.toString()}`
      );
      return response.data;
    },
  });

  // Função para invalidar cache e refetch
  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['unified-documents'] });
  };

  return {
    // Data
    documents: data?.results || [],
    count: data?.count || 0,
    filtersApplied: data?.filters_applied,

    // States
    isLoading,
    isFetching,
    error,

    // Actions
    refetch,
    invalidate,
  };
}
