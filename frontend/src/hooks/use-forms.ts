'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import type { FormTemplate, PaginatedResponse } from '@/types';

export function useForms(page = 1) {
  const queryClient = useQueryClient();

  const { data: formsData, isLoading, error, refetch } = useQuery({
    queryKey: ['forms', page],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<FormTemplate>>('/api/v1/forms/templates/', {
        params: { page },
      });
      return response.data;
    },
  });

  const useForm = (id: string, enabled = true) => {
    return useQuery({
      queryKey: ['form', id],
      queryFn: async () => {
        const response = await api.get<FormTemplate>(`/api/v1/forms/templates/${id}/`);
        return response.data;
      },
      enabled: !!id && enabled,
    });
  };

  const createForm = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post('/api/v1/forms/templates/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['forms'] });
    },
  });

  const updateForm = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: any }) => {
      const response = await api.patch(`/api/v1/forms/templates/${id}/`, data);
      return response.data;
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['forms'] });
      queryClient.invalidateQueries({ queryKey: ['form', variables.id] });
    },
  });

  const deleteForm = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/forms/templates/${id}/`);
    },
    onSuccess: (data, id) => {
      queryClient.invalidateQueries({ queryKey: ['forms'] });
      queryClient.removeQueries({ queryKey: ['form', id] });
    },
  });

  const duplicateForm = useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<FormTemplate>(`/api/v1/forms/templates/${id}/duplicate/`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['forms'] });
    },
  });

  return {
    forms: formsData?.results || [],
    count: formsData?.count || 0,
    isLoading,
    error,
    refetch,
    useForm,
    createForm: createForm.mutateAsync,
    updateForm: updateForm.mutateAsync,
    deleteForm: deleteForm.mutateAsync,
    duplicateForm: duplicateForm.mutateAsync,
    isCreating: createForm.isPending,
    isUpdating: updateForm.isPending,
    isDeleting: deleteForm.isPending,
    isDuplicating: duplicateForm.isPending,
  };
}
