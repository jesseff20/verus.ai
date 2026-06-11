"use client";

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api, { publicApi } from '@/lib/api';
import { BrandSettings, UpdateBrandSettingsData } from '@/types';
import { toast } from 'sonner';

/**
 * Hook para gerenciar configurações de marca
 */
export function useBrandSettings() {
  const queryClient = useQueryClient();

  // Query: Buscar configurações (usa publicApi pois é endpoint público)
  const { data, isLoading, error } = useQuery({
    queryKey: ['brand-settings'],
    queryFn: async () => {
      const response = await publicApi.get<BrandSettings>('/api/v1/auth/brand-settings/');

      // Normaliza URLs para evitar qualquer "http://" legado vindo do backend/DB
      const normalizeUrl = (url?: string | null) => {
        if (!url) return url;
        // Se vier absoluta com http, força https
        if (url.startsWith('http://')) {
          return url.replace(/^http:\/\//i, 'https://');
        }
        // Se vier relativa (/media/...), mantém - o browser vai usar o mesmo esquema da página (https)
        return url;
      };

      const raw = response.data;

      return {
        ...raw,
        logo: normalizeUrl(raw.logo),
        logo_dark: normalizeUrl(raw.logo_dark),
        favicon: normalizeUrl(raw.favicon),
      };
    },
    staleTime: 5 * 60 * 1000, // 5 minutos
    refetchOnWindowFocus: false,
    // Não retenta em erros de servidor (5xx) — evita retry storm quando o backend
    // está em warm-up. Retenta 1x apenas para erros de rede transitórios (sem status).
    retry: (failureCount: number, error: any) => {
      const status = error?.response?.status
      if (status && status >= 400) return false // nunca retenta em erros HTTP
      return failureCount < 1 // 1 retry apenas para erros de rede
    },
  });

  // Mutation: Atualizar configurações
  const updateMutation = useMutation({
    mutationFn: async (data: UpdateBrandSettingsData) => {
      const formData = new FormData();

      // Adicionar campos de texto
      if (data.system_name !== undefined) formData.append('system_name', data.system_name);
      if (data.system_tagline !== undefined) formData.append('system_tagline', data.system_tagline);
      if (data.primary_color !== undefined) formData.append('primary_color', data.primary_color);
      if (data.secondary_color !== undefined) formData.append('secondary_color', data.secondary_color);
      if (data.accent_color !== undefined) formData.append('accent_color', data.accent_color);

      // Adicionar arquivos (logo, logo_dark, favicon)
      if (data.logo instanceof File) {
        formData.append('logo', data.logo);
      } else if (data.logo === null) {
        formData.append('logo', '');
      }

      if (data.logo_dark instanceof File) {
        formData.append('logo_dark', data.logo_dark);
      } else if (data.logo_dark === null) {
        formData.append('logo_dark', '');
      }

      if (data.favicon instanceof File) {
        formData.append('favicon', data.favicon);
      } else if (data.favicon === null) {
        formData.append('favicon', '');
      }

      const response = await api.patch<BrandSettings>(
        '/api/v1/auth/brand-settings/1/',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['brand-settings'] });
      toast.success('Configurações atualizadas com sucesso!');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Erro ao atualizar configurações';
      toast.error(message);
    },
  });

  // Mutation: Resetar configurações
  const resetMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post<BrandSettings>('/api/v1/auth/brand-settings/reset/');
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['brand-settings'] });
      toast.success('Configurações resetadas para padrão!');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Erro ao resetar configurações';
      toast.error(message);
    },
  });

  return {
    // Data
    brandSettings: data,
    isLoading,
    error,

    // Mutations
    updateBrandSettings: updateMutation.mutateAsync,
    isUpdating: updateMutation.isPending,
    resetBrandSettings: resetMutation.mutateAsync,
    isResetting: resetMutation.isPending,
  };
}
