'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import type {
  DocumentBlueprint,
  BlueprintListResponse,
  BlueprintSectionsResponse,
  GenerateETPDynamicRequest,
  GenerateETPDynamicResponse,
} from '@/types';

// ========== Types para mutations ==========

interface CreateBlueprintData {
  name: string;
  description?: string;
  document_type: string;
  version?: string;
  is_active?: boolean;
  is_default?: boolean;
  legal_basis?: string;
  organization_name?: string;
  organization_acronym?: string;
  [key: string]: unknown;
}

interface UpdateBlueprintData {
  id: string;
  data: Partial<CreateBlueprintData>;
}

interface CreateSectionData {
  blueprintId: string;
  data: {
    section_name: string;
    section_key: string;
    section_number?: number;
    description?: string;
    instructions?: string;
    legal_reference?: string;
    is_required?: boolean;
    allow_skip?: boolean;
    is_active?: boolean;
    order?: number;
    [key: string]: unknown;
  };
}

interface UpdateSectionData {
  blueprintId: string;
  sectionId: string;
  data: Record<string, unknown>;
}

interface DeleteSectionData {
  blueprintId: string;
  sectionId: string;
}

interface CreateSubSectionData {
  sectionId: string;
  data: {
    sub_name: string;
    sub_key: string;
    sub_number?: string;
    description?: string;
    help_text?: string;
    default_text?: string;
    is_required?: boolean;
    is_active?: boolean;
    order?: number;
    [key: string]: unknown;
  };
}

interface UpdateSubSectionData {
  subSectionId: string;
  data: Record<string, unknown>;
}

interface ReorderSectionsData {
  blueprintId: string;
  section_order: Array<{ id: string; order: number }>;
}

/**
 * Hook para gerenciar blueprints de documentos jurídicos.
 *
 * Blueprints definem a estrutura de peças processuais (petições, recursos,
 * contratos, defesas, etc.) com seções, agentes de IA e base legal.
 */
export function useBlueprints(documentType?: string) {
  const queryClient = useQueryClient();

  // ── Queries ──

  // Listar blueprints disponiveis (apenas ativos)
  const {
    data: blueprintsData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['blueprints', documentType],
    queryFn: async () => {
      const params: Record<string, string> = { active_only: 'true' };
      if (documentType) {
        params.document_type = documentType;
      }

      const response = await api.get<BlueprintListResponse>(
        '/api/v1/intelligent-assistant/blueprints/',
        { params }
      );
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // blueprints raramente mudam — 5 min de cache
  });

  // Buscar detalhes de um blueprint especifico
  const useBlueprint = (id: string) => {
    return useQuery({
      queryKey: ['blueprint', id],
      queryFn: async () => {
        const response = await api.get<DocumentBlueprint>(
          `/api/v1/intelligent-assistant/blueprints/${id}/`
        );
        return response.data;
      },
      enabled: !!id,
    });
  };

  // Buscar blueprint por nome
  const useBlueprintByName = (name: string) => {
    return useQuery({
      queryKey: ['blueprint-by-name', name],
      queryFn: async () => {
        const response = await api.get<DocumentBlueprint>(
          `/api/v1/intelligent-assistant/blueprints/by-name/${encodeURIComponent(name)}/`
        );
        return response.data;
      },
      enabled: !!name,
    });
  };

  // Listar secoes de um blueprint
  const useBlueprintSections = (blueprintId: string) => {
    return useQuery({
      queryKey: ['blueprint-sections', blueprintId],
      queryFn: async () => {
        const response = await api.get<BlueprintSectionsResponse>(
          `/api/v1/intelligent-assistant/blueprints/${blueprintId}/sections/`
        );
        return response.data;
      },
      enabled: !!blueprintId,
    });
  };

  // ── Mutations: Document Generation ──

  const generateETPMutation = useMutation({
    mutationFn: async (data: GenerateETPDynamicRequest) => {
      const response = await api.post<GenerateETPDynamicResponse>(
        '/api/v1/intelligent-assistant/generate/',
        data,
        {
          timeout: 300000, // 5 minutos (mais secoes = mais tempo)
        }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['generation-sessions'] });
    },
  });

  // ── Mutations: Blueprint CRUD ──

  const createBlueprintMutation = useMutation({
    mutationFn: async (data: CreateBlueprintData) => {
      const response = await api.post<DocumentBlueprint>(
        '/api/v1/intelligent-assistant/blueprints/create/',
        data
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blueprints'] });
    },
  });

  const updateBlueprintMutation = useMutation({
    mutationFn: async ({ id, data }: UpdateBlueprintData) => {
      const response = await api.patch<DocumentBlueprint>(
        `/api/v1/intelligent-assistant/blueprints/${id}/update/`,
        data
      );
      return response.data;
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['blueprints'] });
      queryClient.invalidateQueries({ queryKey: ['blueprint', variables.id] });
    },
  });

  const deleteBlueprintMutation = useMutation({
    mutationFn: async (id: string) => {
      const response = await api.delete(
        `/api/v1/intelligent-assistant/blueprints/${id}/delete/`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blueprints'] });
    },
  });

  // ── Mutations: Section CRUD ──

  const createSectionMutation = useMutation({
    mutationFn: async ({ blueprintId, data }: CreateSectionData) => {
      const response = await api.post(
        `/api/v1/intelligent-assistant/blueprints/${blueprintId}/sections/create/`,
        data
      );
      return response.data;
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['blueprints'] });
      queryClient.invalidateQueries({ queryKey: ['blueprint', variables.blueprintId] });
      queryClient.invalidateQueries({ queryKey: ['blueprint-sections', variables.blueprintId] });
    },
  });

  const updateSectionMutation = useMutation({
    mutationFn: async ({ blueprintId, sectionId, data }: UpdateSectionData) => {
      const response = await api.patch(
        `/api/v1/intelligent-assistant/blueprints/${blueprintId}/sections/${sectionId}/`,
        data
      );
      return response.data;
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['blueprints'] });
      queryClient.invalidateQueries({ queryKey: ['blueprint', variables.blueprintId] });
      queryClient.invalidateQueries({ queryKey: ['blueprint-sections', variables.blueprintId] });
    },
  });

  const deleteSectionMutation = useMutation({
    mutationFn: async ({ blueprintId, sectionId }: DeleteSectionData) => {
      const response = await api.delete(
        `/api/v1/intelligent-assistant/blueprints/${blueprintId}/sections/${sectionId}/delete/`
      );
      return response.data;
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['blueprints'] });
      queryClient.invalidateQueries({ queryKey: ['blueprint', variables.blueprintId] });
      queryClient.invalidateQueries({ queryKey: ['blueprint-sections', variables.blueprintId] });
    },
  });

  // ── Mutations: SubSection CRUD ──

  const createSubSectionMutation = useMutation({
    mutationFn: async ({ sectionId, data }: CreateSubSectionData) => {
      const response = await api.post(
        `/api/v1/intelligent-assistant/sections/${sectionId}/sub-sections/`,
        data
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blueprints'] });
      queryClient.invalidateQueries({ queryKey: ['blueprint'] });
      queryClient.invalidateQueries({ queryKey: ['blueprint-sections'] });
    },
  });

  const updateSubSectionMutation = useMutation({
    mutationFn: async ({ subSectionId, data }: UpdateSubSectionData) => {
      const response = await api.patch(
        `/api/v1/intelligent-assistant/sub-sections/${subSectionId}/`,
        data
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blueprints'] });
      queryClient.invalidateQueries({ queryKey: ['blueprint'] });
      queryClient.invalidateQueries({ queryKey: ['blueprint-sections'] });
    },
  });

  const deleteSubSectionMutation = useMutation({
    mutationFn: async (subSectionId: string) => {
      const response = await api.delete(
        `/api/v1/intelligent-assistant/sub-sections/${subSectionId}/delete/`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blueprints'] });
      queryClient.invalidateQueries({ queryKey: ['blueprint'] });
      queryClient.invalidateQueries({ queryKey: ['blueprint-sections'] });
    },
  });

  // ── Mutations: Reorder Sections ──

  const reorderSectionsMutation = useMutation({
    mutationFn: async ({ blueprintId, section_order }: ReorderSectionsData) => {
      const response = await api.put(
        `/api/v1/intelligent-assistant/blueprints/${blueprintId}/sections/reorder/`,
        { section_order }
      );
      return response.data;
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['blueprints'] });
      queryClient.invalidateQueries({ queryKey: ['blueprint', variables.blueprintId] });
      queryClient.invalidateQueries({ queryKey: ['blueprint-sections', variables.blueprintId] });
    },
  });

  // Obter blueprint padrao (is_default = true)
  const defaultBlueprint = blueprintsData?.blueprints.find(b => b.is_default);

  return {
    // Data
    blueprints: blueprintsData?.blueprints || [],
    total: blueprintsData?.total || 0,
    defaultBlueprint,

    // States
    isLoading,
    error,

    // Queries
    useBlueprint,
    useBlueprintByName,
    useBlueprintSections,

    // Mutations: Document Generation
    generateETP: generateETPMutation.mutateAsync,
    generateETPWithCallbacks: generateETPMutation.mutate,
    isGenerating: generateETPMutation.isPending,

    // Mutations: Blueprint CRUD
    createBlueprint: createBlueprintMutation.mutateAsync,
    createBlueprintWithCallbacks: createBlueprintMutation.mutate,
    isCreatingBlueprint: createBlueprintMutation.isPending,

    updateBlueprint: updateBlueprintMutation.mutateAsync,
    updateBlueprintWithCallbacks: updateBlueprintMutation.mutate,
    isUpdatingBlueprint: updateBlueprintMutation.isPending,

    deleteBlueprint: deleteBlueprintMutation.mutateAsync,
    deleteBlueprintWithCallbacks: deleteBlueprintMutation.mutate,
    isDeletingBlueprint: deleteBlueprintMutation.isPending,

    // Mutations: Section CRUD
    createSection: createSectionMutation.mutateAsync,
    createSectionWithCallbacks: createSectionMutation.mutate,
    isCreatingSection: createSectionMutation.isPending,

    updateSection: updateSectionMutation.mutateAsync,
    updateSectionWithCallbacks: updateSectionMutation.mutate,
    isUpdatingSection: updateSectionMutation.isPending,

    deleteSection: deleteSectionMutation.mutateAsync,
    deleteSectionWithCallbacks: deleteSectionMutation.mutate,
    isDeletingSection: deleteSectionMutation.isPending,

    // Mutations: SubSection CRUD
    createSubSection: createSubSectionMutation.mutateAsync,
    createSubSectionWithCallbacks: createSubSectionMutation.mutate,
    isCreatingSubSection: createSubSectionMutation.isPending,

    updateSubSection: updateSubSectionMutation.mutateAsync,
    updateSubSectionWithCallbacks: updateSubSectionMutation.mutate,
    isUpdatingSubSection: updateSubSectionMutation.isPending,

    deleteSubSection: deleteSubSectionMutation.mutateAsync,
    deleteSubSectionWithCallbacks: deleteSubSectionMutation.mutate,
    isDeletingSubSection: deleteSubSectionMutation.isPending,

    // Mutations: Reorder
    reorderSections: reorderSectionsMutation.mutateAsync,
    reorderSectionsWithCallbacks: reorderSectionsMutation.mutate,
    isReorderingSections: reorderSectionsMutation.isPending,
  };
}

/**
 * Hook simplificado para selecionar blueprint em formularios.
 */
export function useBlueprintSelect() {
  const { blueprints, isLoading, defaultBlueprint } = useBlueprints('etp');

  return {
    options: blueprints.map(b => ({
      value: b.id,
      label: `${b.name} (${b.section_count} secoes)`,
      description: b.description,
      isDefault: b.is_default,
    })),
    isLoading,
    defaultValue: defaultBlueprint?.id,
  };
}

/**
 * Hook para gerenciamento de blueprints (admin).
 * Busca TODOS os blueprints, sem filtro de active_only.
 */
export function useBlueprintManagement(documentType?: string) {
  const queryClient = useQueryClient();

  const {
    data: blueprintsData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['blueprints-management', documentType],
    queryFn: async () => {
      const params: Record<string, string> = { active_only: 'false' };
      if (documentType) {
        params.document_type = documentType;
      }

      const response = await api.get<BlueprintListResponse>(
        '/api/v1/intelligent-assistant/blueprints/',
        { params }
      );
      return response.data;
    },
  });

  // Toggle is_active de um blueprint
  const toggleActiveMutation = useMutation({
    mutationFn: async ({ id, is_active }: { id: string; is_active: boolean }) => {
      const response = await api.patch<DocumentBlueprint>(
        `/api/v1/intelligent-assistant/blueprints/${id}/update/`,
        { is_active }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blueprints-management'] });
      queryClient.invalidateQueries({ queryKey: ['blueprints'] });
    },
  });

  const deleteBlueprintMutation = useMutation({
    mutationFn: async (id: string) => {
      const response = await api.delete(
        `/api/v1/intelligent-assistant/blueprints/${id}/delete/`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blueprints-management'] });
      queryClient.invalidateQueries({ queryKey: ['blueprints'] });
    },
  });

  const duplicateBlueprintMutation = useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<DocumentBlueprint>(
        `/api/v1/intelligent-assistant/blueprints/${id}/duplicate/`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blueprints-management'] });
      queryClient.invalidateQueries({ queryKey: ['blueprints'] });
    },
  });

  return {
    blueprints: blueprintsData?.blueprints || [],
    total: blueprintsData?.total || 0,
    isLoading,
    error,
    refetch,

    toggleActive: toggleActiveMutation.mutateAsync,
    toggleActiveWithCallbacks: toggleActiveMutation.mutate,
    isTogglingActive: toggleActiveMutation.isPending,

    deleteBlueprint: deleteBlueprintMutation.mutateAsync,
    deleteBlueprintWithCallbacks: deleteBlueprintMutation.mutate,
    isDeletingBlueprint: deleteBlueprintMutation.isPending,

    duplicateBlueprint: duplicateBlueprintMutation.mutateAsync,
    duplicateBlueprintWithCallbacks: duplicateBlueprintMutation.mutate,
    isDuplicatingBlueprint: duplicateBlueprintMutation.isPending,
  };
}
