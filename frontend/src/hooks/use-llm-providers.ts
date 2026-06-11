'use client';

import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

/**
 * Modelo LLM retornado pela API.
 */
export interface LLMModel {
  id: string;
  model_id: string;
  display_name: string;
  description: string;
  max_tokens_limit: number;
  default_temperature: number;
  display_order: number;
  is_active: boolean;
}

/**
 * Provider LLM retornado pela API (com modelos aninhados).
 */
export interface LLMProvider {
  id: string;
  code: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  has_api_key: boolean;
  display_order: number;
  is_active: boolean;
  models: LLMModel[];
}

/**
 * Hook para buscar provedores LLM e seus modelos da API.
 *
 * Substitui as listas hardcoded nos dialogs de agentes.
 * Providers e modelos são gerenciados via admin (Core > Provedores LLM).
 */
export function useLLMProviders() {
  const {
    data: providers,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['llm-providers'],
    queryFn: async () => {
      const response = await api.get<LLMProvider[]>(
        '/api/v1/core/llm-providers/with_models/'
      );
      return response.data;
    },
    staleTime: 1000 * 60 * 15, // 15 minutos
  });

  /**
   * Retorna os modelos ativos de um provider específico.
   */
  const getModelsForProvider = (providerCode: string): LLMModel[] => {
    const provider = providers?.find(p => p.code === providerCode);
    return provider?.models || [];
  };

  /**
   * Retorna um provider pelo código.
   */
  const getProvider = (providerCode: string): LLMProvider | undefined => {
    return providers?.find(p => p.code === providerCode);
  };

  /**
   * Verifica se um model_id é válido para um provider.
   */
  const isModelValid = (providerCode: string, modelId: string): boolean => {
    const models = getModelsForProvider(providerCode);
    return models.some(m => m.model_id === modelId);
  };

  return {
    providers: providers || [],
    isLoading,
    error,
    getModelsForProvider,
    getProvider,
    isModelValid,
  };
}
