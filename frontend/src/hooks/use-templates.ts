'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import type { DocumentTemplate, PaginatedResponse } from '@/types';

export function useTemplates(page = 1) {
  const queryClient = useQueryClient();

  const { data: templatesData, isLoading, error, refetch } = useQuery({
    queryKey: ['templates', page],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<DocumentTemplate>>('/api/v1/templates/', {
        params: { page },
      });
      return response.data;
    },
  });

  const useTemplate = (id: string, enabled = true) => {
    return useQuery({
      queryKey: ['template', id],
      queryFn: async () => {
        const response = await api.get<DocumentTemplate>(`/api/v1/templates/${id}/`);
        return response.data;
      },
      enabled: !!id && enabled,
    });
  };

  // Buscar templates associados a um blueprint específico
  const useTemplatesByBlueprint = (blueprintId: string, enabled = true) => {
    return useQuery({
      queryKey: ['templates', 'by-blueprint', blueprintId],
      queryFn: async () => {
        const response = await api.get<PaginatedResponse<DocumentTemplate>>('/api/v1/templates/', {
          params: { blueprint: blueprintId },
        });
        return response.data.results || [];
      },
      enabled: !!blueprintId && enabled,
    });
  };

  const createTemplate = useMutation({
    mutationFn: async (data: any) => {
      // Se data contém File, usar FormData
      const hasFile = Object.values(data).some(value => value instanceof File);

      if (hasFile) {
        const formData = new FormData();
        Object.entries(data).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            formData.append(key, value as any);
          }
        });
        const response = await api.post('/api/v1/templates/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
      }

      const response = await api.post('/api/v1/templates/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
  });

  const updateTemplate = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: any }) => {
      // Se data contém File, usar FormData
      const hasFile = Object.values(data).some(value => value instanceof File);

      if (hasFile) {
        const formData = new FormData();
        Object.entries(data).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            formData.append(key, value as any);
          }
        });
        const response = await api.patch(`/api/v1/templates/${id}/`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
      }

      const response = await api.patch(`/api/v1/templates/${id}/`, data);
      return response.data;
    },
    onSuccess: (data, variables) => {
      // Invalida a lista de templates
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      // Invalida o template específico que foi atualizado
      queryClient.invalidateQueries({ queryKey: ['template', variables.id] });
    },
  });

  const deleteTemplate = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/templates/${id}/`);
    },
    onSuccess: (data, id) => {
      // Invalida a lista de templates
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      // Remove o template específico do cache
      queryClient.removeQueries({ queryKey: ['template', id] });
    },
  });

  const duplicateTemplate = useMutation({
    mutationFn: async ({ id, name }: { id: string; name?: string }) => {
      const response = await api.post(`/api/v1/templates/${id}/duplicate/`, { name });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
  });

  const previewTemplate = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Record<string, any> }) => {
      const response = await api.post(`/api/v1/templates/${id}/preview/`, { data });
      return response.data;
    },
  });

  const checkCompatibility = async (id: string) => {
    const response = await api.get(`/api/v1/templates/${id}/check-compatibility/`);
    return response.data;
  };

  const extractPlaceholders = async (id: string) => {
    const response = await api.get(`/api/v1/templates/${id}/placeholders/`);
    return response.data;
  };

  const activateTemplate = useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post(`/api/v1/templates/${id}/activate/`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
  });

  const deactivateTemplate = useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post(`/api/v1/templates/${id}/deactivate/`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
  });

  return {
    templates: templatesData?.results || [],
    count: templatesData?.count || 0,
    isLoading,
    error,
    refetch,
    useTemplate,
    useTemplatesByBlueprint,
    createTemplate: createTemplate.mutateAsync,
    updateTemplate: updateTemplate.mutateAsync,
    deleteTemplate: deleteTemplate.mutateAsync,
    duplicateTemplate: duplicateTemplate.mutateAsync,
    previewTemplate: previewTemplate.mutateAsync,
    checkCompatibility,
    extractPlaceholders,
    activateTemplate: activateTemplate.mutateAsync,
    deactivateTemplate: deactivateTemplate.mutateAsync,
    isCreating: createTemplate.isPending,
    isUpdating: updateTemplate.isPending,
    isDeleting: deleteTemplate.isPending,
  };
}
